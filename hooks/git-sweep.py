#!/usr/bin/env python3
"""SessionStart hook: compute live repo state fresh, every session.

WHY THIS EXISTS
---------------
It replaces a hand-maintained "current git state" section in a memory note. That
section rotted. By the time anyone checked it, it was wrong on two of three repos --
an agent reading it would have branched defensively around a clean repo while
treating 177 uncommitted files as "no commits yet".

**Volatile facts belong in a hook that recomputes them, not in a note someone has to
remember to bump.** That is the whole idea, and it generalises well past git.

FIVE TRAPS THIS HANDLES
-----------------------
Each one produced a confident, false finding before it was handled here.

  1. Repos nest one level down. A project folder is very often not the repo; the
     repo is one directory inside it. A single-level scan reports these unversioned.
  2. Worktrees live outside the project tree. Some agent tooling keeps them under
     ~/.config/, some uses an in-repo .worktrees/. No directory walk finds them --
     ask git.
  3. A missing upstream is not a missing remote. A branch can diverge from a remote
     that holds most of the history. `git remote -v` before concluding anything is
     unbacked.
  4. Stashes are invisible to `git status`, and a stash is exactly what someone makes
     deliberately before a destructive step. A cleanup pass that cannot see one reads
     it as debris.
  5. A branch can hold commits that exist on no remote while `git status` on the
     current branch reads perfectly clean. `git status` reports ahead/behind for the
     CURRENT branch only.

Traps 4 and 5 are the ones people miss. A clean `git status` is not evidence that
nothing is in flight.

CONFIGURE
---------
    AGENT_PROJECTS   Root directory to sweep. Required.
                     e.g. export AGENT_PROJECTS="$HOME/code"
    CLAUDE_HOOKS_SKIP    Standard opt-out for nested/headless runs.

Pause files honoured: ~/.claude/automation.paused, ~/.claude/automation-gitsweep.paused

BEHAVIOUR
---------
  - Always writes ~/.claude/hook_state/git-sweep.json (the full picture).
  - Prints to stdout ONLY when something needs attention. SessionStart stdout is
    injected into the session context, so silence is the correct output for a healthy
    tree. A hook that speaks every session trains the reader to skim it.
  - Always exits 0. A fault here must never block a session.

PERFORMANCE NOTE, because it is counter-intuitive
-------------------------------------------------
`status --porcelain=v2 --branch` answers five questions in ONE call: branch name,
upstream, ahead/behind, dirty count, and whether HEAD exists yet. This used to be five
separate invocations.

That matters more than it looks. Each `git` costs roughly 83ms of process spawn on
Windows, and this sweep makes well over a hundred of them. **Call count is the thing to
optimise, not concurrency** -- Windows serialises process creation enough that threading
the repos out barely helped on its own. Consolidating the calls took one real setup from
7.6s to 2.8s per session start.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

_root = os.environ.get("AGENT_PROJECTS", "").strip()
PROJECTS = Path(_root) if _root else None
STATE_DIR = Path.home() / ".claude" / "hook_state"
STATE_FILE = STATE_DIR / "git-sweep.json"
SKIP_DIRS = {".git", ".worktrees", "node_modules", "dist", "build", "tmp",
             ".next", ".venv", "venv", "__pycache__", "target", "vendor"}

# Folders whose lack of version control is a RECORDED DECISION, not a finding.
# Add names here once you have decided a folder stays unversioned on purpose.
#
# This list exists because a sweep that re-raises a settled question every session
# trains the reader to skim past it -- which is exactly how a real signal gets missed.
# Write the decision down somewhere too; this set is the enforcement, not the record.
DELIBERATELY_UNVERSIONED = set()

TIMEOUT = 8
PAUSE_FILES = (
    Path.home() / ".claude" / "automation.paused",
    Path.home() / ".claude" / "automation-gitsweep.paused",
)


def git(repo, *args):
    try:
        p = subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return p.returncode, p.stdout.strip()
    except Exception:
        return 1, ""


def find_repos(root, depth=2):
    """Every repo at or below root, to `depth`. See trap 1."""
    out = []
    if not root.exists():
        return out
    if (root / ".git").exists():
        out.append(root)
        return out          # don't descend into a repo's own subdirs
    if depth > 0:
        try:
            kids = sorted(p for p in root.iterdir() if p.is_dir())
        except OSError:
            return out
        for k in kids:
            if k.name in SKIP_DIRS:
                continue
            out.extend(find_repos(k, depth - 1))
    return out


def inspect(repo):
    branch = None
    upstream = None
    ahead = behind = None
    dirty = 0
    has_commits = True
    _, sv2 = git(repo, "status", "--porcelain=v2", "--branch")
    for line in sv2.splitlines():
        if not line.strip():
            continue
        if not line.startswith("# "):
            dirty += 1
            continue
        if line.startswith("# branch.head "):
            branch = line[len("# branch.head "):].strip()
        elif line.startswith("# branch.upstream "):
            upstream = line[len("# branch.upstream "):].strip()
        elif line.startswith("# branch.oid "):
            has_commits = "(initial)" not in line
        elif line.startswith("# branch.ab "):
            try:
                a_tok, b_tok = line[len("# branch.ab "):].split()
                ahead, behind = int(a_tok.lstrip("+")), int(b_tok.lstrip("-"))
            except ValueError:
                pass
    if branch in (None, "(detached)"):
        branch = branch or ""

    # Trap 3: ask for remotes directly. Never infer them from upstream tracking.
    _, remotes_raw = git(repo, "remote", "-v")
    remotes = sorted({l.split()[1] for l in remotes_raw.splitlines() if len(l.split()) > 1})

    # Trap 2: enumerate, never scan.
    _, wt_raw = git(repo, "worktree", "list")
    worktrees = [l for l in wt_raw.splitlines() if l.strip()]

    # Trap 4: stashes.
    _, stash_raw = git(repo, "stash", "list")
    stashes = [l for l in stash_raw.splitlines() if l.strip()]

    # Trap 5: branches holding work that is BOTH unmerged and on no remote.
    #
    # Both halves are load-bearing. `--not --remotes` alone answers "have these commits
    # left the machine", which once described an already-merged branch as 3 outstanding
    # commits and nearly shaped a push decision. Asking --no-merged first is also much
    # cheaper: most branches are merged, so this costs one call plus one per genuinely
    # unmerged branch, rather than two calls per branch.
    unpushed_branches = []
    if remotes:
        _, unmerged_raw = git(repo, "branch", "--no-merged", "HEAD",
                              "--format=%(refname:short)")
        for name in (l.strip() for l in unmerged_raw.splitlines()):
            if not name:
                continue
            rc, uniq = git(repo, "rev-list", "--count", name, "--not", "--remotes")
            if rc == 0 and uniq.isdigit() and int(uniq) > 0:
                unpushed_branches.append({"branch": name, "unique_commits": int(uniq)})

    return {
        "path": str(repo),
        "name": repo.name,
        "branch": branch or "(detached or empty)",
        "remotes": remotes,
        "upstream": upstream,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "has_commits": has_commits,
        "worktrees": worktrees,
        "stashes": stashes,
        "unpushed_branches": unpushed_branches,
    }


def flags(r):
    """Things worth surfacing. Deliberately conservative: a dirty tree is normal
    working state, not an alarm. Only structural oddities are called out."""
    out = []
    if not r["has_commits"]:
        out.append("EMPTY REPO (initialised, nothing committed)")
    if not r["remotes"]:
        out.append("NO REMOTE (nothing has left this machine)")
    if r["behind"]:
        out.append("branch is %d behind its remote (possible divergence)" % r["behind"])
    if r["remotes"] and not r["upstream"]:
        out.append("has a remote but no upstream tracking on this branch")
    if r["ahead"]:
        out.append("%d unpushed commit(s)" % r["ahead"])
    if r.get("stashes"):
        out.append("%d stash(es) - do not drop without asking" % len(r["stashes"]))
    for b in r.get("unpushed_branches", []):
        out.append("branch %s holds %d unmerged commit(s) on no remote"
                   % (b["branch"], b["unique_commits"]))
    return out


def main():
    if os.environ.get("CLAUDE_HOOKS_SKIP"):
        return 0
    if any(p.exists() for p in PAUSE_FILES):
        return 0
    if PROJECTS is None:
        return 0          # unconfigured is not an error; just do nothing
    try:
        found = find_repos(PROJECTS)
        # Every call is read-only and the repos are independent, so fanning out is
        # safe. Order is restored afterwards so printed output stays stable.
        with ThreadPoolExecutor(max_workers=8) as pool:
            repos = list(pool.map(inspect, found))
        repos.sort(key=lambda r: r["path"])

        unversioned = []
        if PROJECTS.exists():
            repo_roots = {r["path"] for r in repos}
            for d in sorted(p for p in PROJECTS.iterdir() if p.is_dir()):
                if d.name in SKIP_DIRS or d.name in DELIBERATELY_UNVERSIONED:
                    continue
                if not any(rp.startswith(str(d)) for rp in repo_roots):
                    unversioned.append(d.name)

        state = {
            "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "projects_root": str(PROJECTS),
            "repos": repos,
            "unversioned_folders": unversioned,
        }
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

        noteworthy = [(r, f) for r, f in ((r, flags(r)) for r in repos) if f]
        if noteworthy or unversioned:
            print("GIT SWEEP (computed fresh at session start; "
                  "full state in ~/.claude/hook_state/git-sweep.json)")
            for r, f in noteworthy:
                print("- %s [%s]: %s" % (r["name"], r["branch"], "; ".join(f)))
            if unversioned:
                print("- not under version control: %s" % ", ".join(unversioned))
            print("Verify before acting on any of this; do not copy it into a note.")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

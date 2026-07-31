#!/usr/bin/env python3
"""
git_status_capture.py  -  capture clean Git state snapshot for session-close notes.

Usage:
    python git_status_capture.py "<project-folder>"
    python git_status_capture.py "<project-folder>" --markdown   # markdown formatted (default)
    python git_status_capture.py "<project-folder>" --json       # JSON output

Output drops directly into the "Git State After Work" section of the
session-close template. Designed to be human-readable and template-paste-ready.

Covers all four places work hides where `git status` shows nothing: unpushed
branches, out-of-tree worktrees, in-repo worktrees, and stashes. Empty results are
printed rather than omitted, so a checked absence is distinguishable from a check
that never ran.

Exits non-zero if the path isn't a git repo (with a clear message  -  non-git
folders still need handling, just not via this script).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return out.returncode, out.stdout.strip(), out.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git not found"


def find_repos(folder: Path, max_depth: int = 2):
    """Every git repo at or below `folder`, to max_depth.

    Project folders very often nest the repo one level down: the folder you
    think of as "the project" is a container, and the repo is one directory
    inside it. A depth-0 check reports "not a git repo" for every one of those,
    which is how one audit briefly concluded 9 of 12 projects were unversioned.
    They were not.
    """
    found = []
    if not folder.exists():
        return found
    if (folder / ".git").exists():
        found.append(folder)
    if max_depth > 0:
        try:
            children = sorted(p for p in folder.iterdir() if p.is_dir())
        except OSError:
            children = []
        for child in children:
            if child.name in {".git", "node_modules", ".godot", "dist", "build", "tmp"}:
                continue
            found.extend(find_repos(child, max_depth - 1))
    return found


def capture(folder: Path):
    if not folder.exists():
        return None, f"folder not found: {folder}"
    if not (folder / ".git").exists():
        nested = find_repos(folder)
        if nested:
            rel = ", ".join(str(x.relative_to(folder)) for x in nested)
            return None, (f"not a git repo itself, but contains {len(nested)} nested repo(s): "
                          f"{rel}. Re-run against the nested path, not the parent.")
        return None, f"not a git repo, and none nested within it: {folder}"

    code, branch, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], folder)
    if code != 0:
        return None, "failed to read branch"

    # A missing upstream does NOT mean a missing remote. A branch can be divergent
    # from a remote holding most of the history. One repo here had a local main of
    # 1 commit while origin/main had 27. Report them separately, or a reader concludes
    # work has never left the machine when it has.
    _, remotes_raw, _ = run(["git", "remote", "-v"], folder)
    remotes = sorted({ln.split()[1] for ln in (remotes_raw or "").splitlines() if len(ln.split()) > 1})

    # Worktrees can live entirely outside the project tree (some agent tooling
    # keeps them under ~/.config/, others use an in-repo .worktrees/), so a directory
    # scan cannot see them. Ask git.
    _, worktrees_raw, _ = run(["git", "worktree", "list"], folder)
    worktrees = [ln for ln in (worktrees_raw or "").splitlines() if ln.strip()]

    # Work hides in four places and `git status` shows none of them: unpushed
    # branches, out-of-tree worktrees, in-repo worktrees, and stashes. All four were
    # once found populated in one repo while every `git status` read perfectly clean.
    # Worktrees are covered above; the two below close the rest.
    #
    # Stashes are the most dangerous omission, because a stash is what someone makes
    # deliberately before a destructive step, and a cleanup pass that cannot see it
    # will read it as debris and drop it.
    _, stash_raw, _ = run(["git", "stash", "list"], folder)
    stashes = [ln for ln in (stash_raw or "").splitlines() if ln.strip()]

    # EVERY local branch, measured against every remote-tracking ref. The current
    # branch's ahead/behind (below) says nothing about the other branches in the repo.
    #
    # Do NOT filter to "branches with no upstream". That filter was tried here first
    # and it hid the branch that actually mattered: a branch can have an upstream
    # configured and still carry commits that exist on no remote. Having an upstream
    # says nothing about whether a branch's commits ever left the machine. The only
    # question worth asking is "do these commits exist anywhere but this disk", which
    # is `--not --remotes`.
    #
    # But that is only HALF the question, and reporting it alone misleads. This script
    # once described a branch as "3 commits on no remote" - true, and it read as
    # unfinished work needing a decision. The branch had already been merged into main;
    # `git rev-list --count HEAD..<branch>` was 0. Those commits had not left the machine
    # because MAIN had not been pushed, not because the branch was pending. That framing
    # shaped a push decision before it was caught.
    #
    # So ask both: "have these commits left the machine" AND "are they already in HEAD".
    # A merged branch is a cleanup candidate; an unmerged one is a decision.
    _, local_raw, _ = run(
        ["git", "for-each-ref", "--format=%(refname:short)%09%(upstream:short)", "refs/heads"],
        folder,
    )
    unpushed = []
    for ln in (local_raw or "").splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t")
        name = parts[0]
        tracks = parts[1].strip() if len(parts) > 1 else ""
        _, cnt, _ = run(["git", "rev-list", "--count", name, "--not", "--remotes"], folder)
        try:
            unique = int(cnt)
        except (TypeError, ValueError):
            unique = -1
        # Commits on this branch that HEAD does not already contain. 0 means merged
        # (or an ancestor); the branch holds no work the current branch is missing.
        code_m, ahead_of_head, _ = run(["git", "rev-list", "--count", f"HEAD..{name}"], folder)
        try:
            unmerged = int(ahead_of_head) if code_m == 0 else -1
        except (TypeError, ValueError):
            unmerged = -1
        unpushed.append(
            {
                "branch": name,
                "unique_commits": unique,
                "unmerged_commits": unmerged,
                "tracks": tracks,
            }
        )
    # Loudest first: branches carrying commits that exist nowhere else.
    unpushed.sort(key=lambda b: (-b["unique_commits"], b["branch"]))

    _, upstream, _ = run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], folder)
    upstream = upstream or "(no upstream tracking for this branch)"

    _, ahead_behind, _ = run(["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"], folder)
    ahead = behind = 0
    if ahead_behind:
        try:
            a, b = ahead_behind.split()
            ahead, behind = int(a), int(b)
        except ValueError:
            pass

    _, status, _ = run(["git", "status", "--porcelain"], folder)
    modified, staged, untracked, deleted = [], [], [], []
    for line in (status or "").splitlines():
        if not line:
            continue
        x, y = line[0], line[1]
        path = line[3:]
        if x == "?" and y == "?":
            untracked.append(path)
        elif x == "D" or y == "D":
            deleted.append(path)
        elif x != " " and x != "?":
            staged.append(path)
            if y != " " and y != "?":
                modified.append(path)
        elif y != " ":
            modified.append(path)

    _, last_commits, _ = run(["git", "log", "--oneline", "-5"], folder)

    return {
        "folder": str(folder),
        "branch": branch,
        "upstream": upstream,
        "remotes": remotes,
        "worktrees": worktrees,
        "stashes": stashes,
        "unpushed_branches": unpushed,
        "ahead": ahead,
        "behind": behind,
        "modified": modified,
        "staged": staged,
        "deleted": deleted,
        "untracked": untracked,
        "last_5_commits": last_commits.splitlines() if last_commits else [],
    }, None


def to_markdown(state: dict) -> str:
    lines = []
    lines.append(f"- Branch: `{state['branch']}`")
    if state.get("remotes"):
        lines.append(f"- Remotes: {', '.join('`'+r+'`' for r in state['remotes'])}")
    else:
        lines.append("- Remotes: **NONE CONFIGURED** (nothing has left this machine)")
    lines.append(f"- Remote tracking: `{state['upstream']}`")
    if state["ahead"] or state["behind"]:
        lines.append(f"- Ahead/behind upstream: {state['ahead']} ahead, {state['behind']} behind")
        if state["behind"]:
            lines.append(f"  - **{state['behind']} commit(s) on the remote are not in this branch.** Check for divergence before building on it.")
    if len(state.get("worktrees", [])) > 1:
        lines.append(f"- Worktrees ({len(state['worktrees'])}, some may sit outside the project tree):")
        for w in state["worktrees"]:
            lines.append(f"  - `{w}`")
    # Report these even when empty. "0 stashes" is a checked absence; a silent
    # section is indistinguishable from a check that was never run, and that
    # ambiguity is what let four hiding places stay invisible behind a clean status.
    stashes = state.get("stashes", [])
    if stashes:
        lines.append(f"- **Stashes: {len(stashes)}  -  do not drop without asking.**")
        for s in stashes:
            lines.append(f"  - `{s}`")
    else:
        lines.append("- Stashes: none")

    # The current branch already has its own ahead/behind line above; repeating it here
    # as "merged into HEAD" is both noisy and confusingly worded (it is HEAD).
    unpushed = [b for b in state.get("unpushed_branches", []) if b["branch"] != state["branch"]]
    carrying = [b for b in unpushed if b["unique_commits"] > 0]
    unreadable = [b for b in unpushed if b["unique_commits"] < 0]
    safe = [b for b in unpushed if b["unique_commits"] == 0]
    # A repo with no remotes at all has every commit "on no remote" by definition, so
    # flagging each branch is noise, not a finding  -  and four repos on this host are
    # deliberately remoteless. Say it once instead. Recurring false signal is precisely
    # what versioning those folders was meant to stop.
    if not state.get("remotes"):
        # Count every branch including HEAD here. This line is about the repo as a
        # whole, not about work hiding elsewhere, so excluding the current branch
        # made a single-branch repo report "0 local branches".
        total = len(state.get("unpushed_branches", []))
        lines.append(
            f"- Local branches: {total} "
            "(no remotes configured, so nothing here has left the machine  -  by design "
            "for local-only repos; confirm that is the intent for this one)"
        )
    elif carrying:
        # Split by the question that actually decides what to do. Commits absent from
        # HEAD are work you could still lose; commits already merged into HEAD are on
        # this disk only because HEAD itself has not been pushed.
        decisions = [b for b in carrying if b["unmerged_commits"] != 0]
        merged = [b for b in carrying if b["unmerged_commits"] == 0]
        if decisions:
            lines.append(
                f"- **Branches holding unmerged work that exists on no remote: {len(decisions)}**"
            )
            for b in decisions:
                tracks = f", tracks `{b['tracks']}`" if b["tracks"] else ", no upstream"
                n = b["unmerged_commits"]
                extent = f"{n} not in HEAD" if n > 0 else "merge status unreadable"
                lines.append(
                    f"  - **`{b['branch']}`  -  {b['unique_commits']} commit(s) on no remote, "
                    f"{extent}{tracks}.**"
                )
            lines.append(
                "  - A clean `git status` cannot show you these, and they are the ones that "
                "need a real decision: push, merge, or drop deliberately  -  never as cleanup. "
                "An upstream being set does not mean the commits ever left this machine."
            )
        if merged:
            lines.append(
                f"- {len(merged)} branch(es) already merged into HEAD, unpushed only because "
                "HEAD is: "
                + ", ".join(f"`{b['branch']}`" for b in merged)
            )
            lines.append(
                "  - Not outstanding work. Pushing the current branch publishes their commits; "
                "the refs are cleanup candidates, not decisions."
            )
    else:
        lines.append("- Local branches holding commits that exist on no remote: none")
    if unreadable and state.get("remotes"):
        lines.append(
            f"  - ! {len(unreadable)} branch(es) whose unique-commit count could not be read: "
            + ", ".join(f"`{b['branch']}`" for b in unreadable)
            + "  -  treat as unverified, not as clean."
        )
    if safe and state.get("remotes"):
        lines.append(
            f"  - {len(safe)} other local branch(es), all fully present on a remote: "
            + ", ".join(f"`{b['branch']}`" for b in safe)
        )

    counts = []
    if state["modified"]:
        counts.append(f"{len(state['modified'])} modified")
    if state["staged"]:
        counts.append(f"{len(state['staged'])} staged")
    if state["deleted"]:
        counts.append(f"{len(state['deleted'])} deleted")
    lines.append(f"- Dirty files: {', '.join(counts) if counts else 'none'}")
    lines.append(f"- Untracked files: {len(state['untracked'])}")

    if state["modified"]:
        lines.append("")
        lines.append("**Modified:**")
        for f in state["modified"]:
            lines.append(f"- `{f}`")
    if state["staged"]:
        lines.append("")
        lines.append("**Staged:**")
        for f in state["staged"]:
            lines.append(f"- `{f}`")
    if state["untracked"]:
        lines.append("")
        lines.append("**Untracked:**")
        for f in state["untracked"]:
            lines.append(f"- `{f}`")
    if state["last_5_commits"]:
        lines.append("")
        lines.append("**Last 5 commits:**")
        for c in state["last_5_commits"]:
            lines.append(f"- `{c}`")
    return "\n".join(lines)


def main(argv):
    p = argparse.ArgumentParser(description="Capture git state for session-close notes")
    p.add_argument("folder", type=Path)
    fmt = p.add_mutually_exclusive_group()
    fmt.add_argument("--markdown", action="store_true", default=True)
    fmt.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    state, err = capture(args.folder)
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(to_markdown(state))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""SessionStart(matcher="compact") hook: re-orient after context compaction.

A working replacement for `hooks/post-compact.sh`.

WHY THIS IS A SessionStart HOOK AND NOT PostCompact
---------------------------------------------------
`PostCompact` exists and fires after compaction, but per the hooks documentation it
**cannot inject text into the model's context** -- it has no `additionalContext`, and is
described as being for side effects such as logging. A reorientation notice printed from
that event runs and changes nothing.

`SessionStart` with `matcher: "compact"` fires when the session resumes after auto or
manual compaction, and SessionStart stdout IS injected. That is the working mechanism.
Verified against the hooks documentation on 2026-07-26 (Windows, Python 3, Claude Code).

Register it like this in your settings merge, alongside the normal session-start entries:

    "SessionStart": [
        ("",        [sh("git-session-baseline.sh")]),
        ("",        [sh("learning-loop-start.sh")]),
        ("compact", [py("post-compact-reorient.py")]),
    ],

WHAT IT DOES BEYOND THE ORIGINAL
--------------------------------
Compaction summarises the conversation. What survives is the gist; what tends not to
survive is the set of small binding facts agreed mid-session -- which path was declared
canonical, that one push was approved and another was not, that a route was already tried
and closed. Those are exactly the facts whose loss causes an agent to redo settled work
or redo a destructive step.

So this prints named anchors, not only advice: the last few user messages verbatim, and
any commits already made today in a repo you point it at. A generic reminder is easy to
skim past; a named constraint is not.

Portable: no personal data, no absolute paths. Configure via environment variables.

    REORIENT_REPO       Optional. Path to a repo whose commits-since-midnight are worth
                        surfacing (your memory store, if it is under git). Unset = skip.
    CLAUDE_HOOKS_SKIP   Standard opt-out for nested/headless runs.

Pause files honoured: ~/.claude/automation.paused and ~/.claude/automation-reorient.paused

Windows note: prints ASCII only, on purpose. See policies/windows-scripting.md.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PAUSE_FILES = (
    Path.home() / ".claude" / "automation.paused",
    Path.home() / ".claude" / "automation-reorient.paused",
)
REPO = os.environ.get("REORIENT_REPO", "").strip()
MAX_USER_MSGS = 4
MAX_CHARS = 220


def read_messages(path):
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def is_tool_result(content):
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


def recent_user_messages(messages):
    found = []
    for msg in reversed(messages):
        if msg.get("type") != "user":
            continue
        content = msg.get("message", {}).get("content", "")
        if is_tool_result(content):
            continue
        raw = text_of(content)
        raw = re.sub(r"<system-reminder>.*?</system-reminder>", "", raw, flags=re.DOTALL)
        raw = " ".join(raw.split())
        if not raw:
            continue
        found.append(raw[:MAX_CHARS])
        if len(found) >= MAX_USER_MSGS:
            break
    return list(reversed(found))


def commits_today():
    """Cheap, factual record of what this session already decided. Recall is what
    compaction damaged; the git log is not."""
    if not REPO or not (Path(REPO) / ".git").exists():
        return []
    try:
        p = subprocess.run(
            ["git", "-C", REPO, "log", "--since=midnight", "--format=%h %s"],
            capture_output=True, text=True, timeout=8,
        )
    except Exception:
        return []
    if p.returncode != 0:
        return []
    return [l for l in p.stdout.strip().splitlines() if l.strip()][:8]


def main():
    if os.environ.get("CLAUDE_HOOKS_SKIP"):
        return 0
    if any(p.exists() for p in PAUSE_FILES):
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    messages = read_messages(payload.get("transcript_path") or "")
    users = recent_user_messages(messages)
    commits = commits_today()

    # Unlike a status hook, silence is NOT the right output here. The whole point is to
    # fire when context was just lost.
    print("CONTEXT WAS COMPACTED - re-orient before the next action.")
    print("")
    print("The summary kept the gist. What it most likely dropped is the small print:")
    print("which path was declared canonical, what was approved versus merely discussed,")
    print("and which approaches were already tried and ruled out.")
    print("")
    print("Before doing anything further:")
    print("1. Re-state the current task and the step you are on.")
    print("2. Re-state any constraint agreed mid-session - especially anything about")
    print("   pushing, deleting, overwriting, or which surface is canonical.")
    print("3. Treat every approval as spent. Approval to push once is not approval to")
    print("   push again; re-ask rather than inferring it from the summary.")
    print("4. Re-verify volatile facts rather than trusting the summary's version of")
    print("   them: branch state, file counts, what is installed where.")
    print("5. If lessons or rules were loaded into context this session, reload them.")
    print("   Loaded memory did not survive compaction.")

    if users:
        print("")
        print("Most recent user messages verbatim (the summary paraphrased these):")
        for u in users:
            print(f"  - {u}")

    if commits:
        print("")
        print("Commits already made today - work that is DONE, do not redo:")
        for c in commits:
            print(f"  - {c}")

    print("")
    print("If anything above conflicts with the compacted summary, the summary is the")
    print("less reliable source. Check the file or the repo, then continue.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A reorientation hook must never be the reason a resumed session fails.
        sys.exit(0)

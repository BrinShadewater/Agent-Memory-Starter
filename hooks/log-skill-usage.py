#!/usr/bin/env python3
"""PostToolUse hook (matcher: Skill)  -  append skill invocations to a JSONL log.

Gives any skill-audit process real usage data. Judgements about which skills
earn their keep otherwise rest on impression, because nothing records which
skills actually fire.

One line per Skill call:
    {"skill": "<name>", "ts": "<ISO8601>", "session": "<id>"}

Local only, no network. Always exits 0 and swallows every error: telemetry must
never block a skill from running.

Reporting note, and it is the important part: do not report dormancy
until the log covers the dormancy window. A skill that looks unused because the
log is three days old is a false positive, and a confident wrong number is worse
than no number.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "hook_state" / "skill-usage.jsonl"


MAX_BYTES = 2 * 1024 * 1024   # rotate at 2 MB; an append-only log is a runaway in waiting
PAUSE_FILES = (
    Path.home() / ".claude" / "automation.paused",
    Path.home() / ".claude" / "automation-telemetry.paused",
)


def rotate_if_needed():
    try:
        if LOG.exists() and LOG.stat().st_size > MAX_BYTES:
            prev = LOG.with_suffix(".jsonl.1")
            if prev.exists():
                prev.unlink()
            LOG.rename(prev)   # keep exactly one previous generation
    except Exception:
        pass


def main():
    if os.environ.get("CLAUDE_HOOKS_SKIP"):
        return 0
    if any(p.exists() for p in PAUSE_FILES):
        return 0
    try:
        rotate_if_needed()
        payload = json.load(sys.stdin)
        skill = (payload.get("tool_input") or {}).get("skill")
        if not skill:
            return 0
        LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "skill": skill,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "session": payload.get("session_id", ""),
        }
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

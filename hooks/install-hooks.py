#!/usr/bin/env python3
"""Install this kit's hooks into ~/.claude/settings.json.

Installer discipline, because an installer that mangles a settings file it did not
write is a worse outcome than no installer:

  1. Timestamped backup FIRST. Never touch the file until the copy exists.
  2. Merge ADDITIVELY. Never replace a hooks block you did not author.
  3. Dedupe by script basename, so re-running is safe and does not stack duplicates.
  4. Refuse to wire a script that is not on disk. A registered path that does not
     exist is a hook that fails silently on every session.
  5. Print every path chosen, so the user can see exactly what changed and undo it.

Usage:
    python install-hooks.py [--apply]

Dry-run by default. Nothing is written without --apply, per the blast-radius contract
in vault/40_Knowledge/policies/automation-safety.md.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
SETTINGS = HOME / ".claude" / "settings.json"
HOOKS_DIR = HOME / ".claude" / "hooks"
HERE = Path(__file__).resolve().parent

# (event, matcher, script filename)
#
# NOTE the matcher on post-compact-reorient. It is "compact" under SessionStart, NOT
# a PostCompact registration. PostCompact fires after compaction but cannot inject
# text into the model's context -- a reorientation notice printed there runs and
# changes nothing. SessionStart(matcher="compact") fires on resume after compaction
# and its stdout IS injected. This distinction is the difference between the hook
# working and the hook being decorative.
PLAN = [
    ("SessionStart", "",        "git-sweep.py"),
    ("SessionStart", "compact", "post-compact-reorient.py"),
    ("SessionStart", "",        "task-health.py"),
    ("PostToolUse",  "Skill",   "log-skill-usage.py"),
]


def cmd_for(script_path):
    return f'python "{script_path}"'


def already_registered(entries, basename):
    """True if any hook command in `entries` references this script basename."""
    for entry in entries:
        for h in entry.get("hooks", []):
            if basename in str(h.get("command", "")):
                return True
    return False


def main():
    apply = "--apply" in sys.argv
    print(f"Kit hooks:      {HERE}")
    print(f"Install target: {HOOKS_DIR}")
    print(f"Settings file:  {SETTINGS}")
    print(f"Mode:           {'APPLY' if apply else 'DRY RUN (pass --apply to write)'}")
    print("")

    # Guard 4: refuse to wire anything that is not on disk.
    missing = [s for _, _, s in PLAN if not (HERE / s).exists()]
    if missing:
        print("ERROR: these scripts are missing from the kit, refusing to continue:")
        for m in missing:
            print(f"  - {m}")
        return 1

    settings = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: {SETTINGS} is not valid JSON ({e}). Fix it first; "
                  f"this installer will not overwrite a file it cannot parse.")
            return 1

    hooks = settings.setdefault("hooks", {})
    planned_copies, planned_regs, skipped = [], [], []

    for event, matcher, script in PLAN:
        target = HOOKS_DIR / script
        planned_copies.append((HERE / script, target))
        entries = hooks.setdefault(event, [])
        if already_registered(entries, script):
            skipped.append(f"{event}[{matcher or '*'}] -> {script} (already registered)")
            continue
        entries.append({
            "matcher": matcher,
            "hooks": [{"type": "command", "command": cmd_for(target)}],
        })
        planned_regs.append(f"{event}[{matcher or '*'}] -> {target}")

    print("Files to copy:")
    for src, dst in planned_copies:
        print(f"  {src.name}  ->  {dst}")
    print("")
    print("Registrations to add:" if planned_regs else "Registrations to add: none")
    for r in planned_regs:
        print(f"  + {r}")
    if skipped:
        print("")
        print("Skipped (dedupe by script basename, so re-running is safe):")
        for s in skipped:
            print(f"  = {s}")

    if not apply:
        print("")
        print("Dry run only. Nothing written. Re-run with --apply to install.")
        return 0

    # Guard 1: backup before touching anything.
    if SETTINGS.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = SETTINGS.with_name(f"settings.json.pre-kit-{stamp}")
        shutil.copy2(SETTINGS, backup)
        print("")
        print(f"Backup written: {backup}")

    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in planned_copies:
        shutil.copy2(src, dst)
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {len(planned_copies)} script(s), "
          f"added {len(planned_regs)} registration(s).")
    print("")
    print("NEXT STEPS, and the first one is not optional:")
    print("  1. Set AGENT_PROJECTS to the root directory you want swept, or the")
    print("     git sweep will do nothing. Set AGENT_VAULT to your vault root.")
    print("     Set AGENT_TASK_FILTER to a regex matching your scheduled tasks, or")
    print("     task-health.py stays inert. Windows only; it reads Task Scheduler.")
    print("  2. Start a FRESH session. A running session's hooks are fixed at start,")
    print("     so this session will not show the change no matter what you do.")
    print("  3. Confirm the sweep ran:  ~/.claude/hook_state/git-sweep.json")
    print("     Registration is not evidence. Check the artifact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

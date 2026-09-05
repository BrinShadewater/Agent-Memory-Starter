#!/usr/bin/env python3
"""SessionStart hook: surface unattended jobs that failed or went stale.

WHY THIS EXISTS
---------------
A daily briefing job's staleness alarm once worked exactly as designed: its upstream feed
was unreachable, the job detected a zero fetch, wrote a STALE log line and exited 2. Task
Scheduler recorded `LastTaskResult 2`.

Nobody looked. It was found a day later, by accident, while auditing something else.

**An alarm nobody reads is the same shape as the problem it was built to catch.** The
2026-07-25 review of automation-safety.md concluded that a job needs a way to prove it
worked and a way to be stopped. It needs a third thing: a way to be *heard*.

Every other control in that policy is about the job. This is about the gap between the job
failing and a human finding out.

WHAT IT CHECKS
--------------
  1. Non-zero LastTaskResult on the scheduled tasks you select.
  2. Tasks that have not run within their expected window (a job that stops firing
     reports nothing at all -- the 2026-07-06..07-15 backup gap was ten silent days).

Both are read-only queries against Task Scheduler.

BEHAVIOUR
---------
  - Silent when everything is healthy. SessionStart stdout enters the context window, and
    a hook that speaks every session trains the reader to skim it.
  - Never blocks, always exits 0. A health reporter must never be why a session fails.
  - Honours CLAUDE_HOOKS_SKIP and the automation.paused kill switch.

CONFIGURE
---------
    AGENT_TASK_FILTER   Regex selecting your scheduled tasks, e.g. "Backup|Sync".
                        Unset means the hook does nothing at all.

WINDOWS ONLY. It queries Task Scheduler via PowerShell. The IDEA is portable -- the
Linux equivalent is `systemctl list-timers` plus each unit's last exit status -- but
this implementation is not.

Exit-code semantics per job are deliberately NOT hardcoded beyond "non-zero is worth
mentioning". The point is to surface, not to diagnose -- diagnosis needs the job's own log,
and this hook names it rather than guessing.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PAUSE_FILES = (
    Path.home() / ".claude" / "automation.paused",
    Path.home() / ".claude" / "automation-taskhealth.paused",
)
STATE_FILE = Path.home() / ".claude" / "hook_state" / "task-health.json"

# Task name pattern -> how many hours between runs before it counts as overdue.
# Generous on purpose: the machine is a desktop and is legitimately off overnight or for
# a weekend. A false "overdue" every Monday is exactly the noise this hook must not make.
# ========================== EDIT THIS FOR YOUR SETUP ==========================
# TASK_FILTER is a regex matched against scheduled-task names. Set it to something
# that selects YOUR jobs and nothing else, or this reports on Windows' own
# maintenance tasks and becomes noise on day one.
TASK_FILTER = os.environ.get("AGENT_TASK_FILTER", "").strip()

# Task name -> hours between runs before it counts as overdue. Generous on purpose:
# a desktop is legitimately off overnight and for whole weekends. The uptime logic
# further down is the real defence against Monday false alarms.
WATCHED = {
    # "My Nightly Backup": 48,
}

# Where a failing job's evidence actually lives, so the report points somewhere useful
# rather than saying "check the logs".
LOG_HINTS = {
    # "My Nightly Backup": r"C:\path\to\its\log.txt",
}
# ==============================================================================

PS = r"C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe"


def query_tasks():
    """Read task state as JSON. Returns [] on any failure -- this hook is best-effort.

    Also returns system uptime, because 'overdue' is meaningless without it: a desktop
    that was switched off cannot be blamed for a task that did not fire.
    """
    script = (
        "$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime; "
        "$t = Get-ScheduledTask | Where-Object {$_.TaskName -match '" + TASK_FILTER.replace("'", "''") + "'} | "
        "ForEach-Object { $i = $_ | Get-ScheduledTaskInfo; "
        "[pscustomobject]@{ Name=$_.TaskName; State=[string]$_.State; "
        "Result=$i.LastTaskResult; "
        "CatchesUp=[bool]$_.Settings.StartWhenAvailable; "
        "Last=$(if($i.LastRunTime){$i.LastRunTime.ToString('o')}else{''}) } }; "
        "[pscustomobject]@{ Boot=$boot.ToString('o'); Tasks=@($t) } | "
        "ConvertTo-Json -Compress -Depth 4"
    )
    try:
        p = subprocess.run(
            [PS, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=25,
        )
    except Exception:
        return [], None          # must match the tuple signature; a bare [] fails to unpack
    if p.returncode != 0 or not p.stdout.strip():
        return [], None
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        return [], None
    tasks = data.get("Tasks") or []
    if isinstance(tasks, dict):
        tasks = [tasks]
    boot = None
    try:
        boot = datetime.fromisoformat(data["Boot"])
        if boot.tzinfo is None:
            boot = boot.replace(tzinfo=timezone.utc)
    except (KeyError, ValueError, TypeError):
        pass
    return tasks, boot


CACHE_MINUTES = 30


def report(problems, stale_minutes=None):
    if not problems:
        return
    when = ("computed fresh at session start" if stale_minutes is None
            else "from the check %d min ago; the next fresh one is within %d" % (stale_minutes, CACHE_MINUTES))
    print("UNATTENDED JOB HEALTH (%s)" % when)
    for name, detail in problems:
        print("- %s: %s" % (name, detail))
    print("An exit code is not evidence either way - read the job's own output "
          "before concluding it is fine.")


def main():
    if os.environ.get("CLAUDE_HOOKS_SKIP"):
        return 0
    if any(p.exists() for p in PAUSE_FILES):
        return 0

    # A state file fresher than CACHE_MINUTES means the scheduler query (about 2.5 s of
    # PowerShell, the slowest hook at every session start) would only repeat itself.
    # Reuse it: a clean prior result stays quiet, and a prior problem is reprinted so a
    # session that starts inside the window still hears it.
    try:
        prior = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        checked = datetime.fromisoformat(prior["checked_at"])
        if datetime.now(timezone.utc) - checked < timedelta(minutes=CACHE_MINUTES):
            report([(p["task"], p["detail"]) for p in prior.get("problems", [])],
                   stale_minutes=int((datetime.now(timezone.utc) - checked).total_seconds() // 60))
            return 0
    except (OSError, ValueError, KeyError, TypeError):
        pass

    if not TASK_FILTER:
        return 0          # unconfigured is not an error; do nothing rather than guess

    tasks, boot = query_tasks()
    if not tasks:
        return 0          # cannot query is not the same as unhealthy; stay quiet

    now = datetime.now(timezone.utc)
    uptime_h = (now - boot).total_seconds() / 3600 if boot else None
    problems = []

    for t in tasks:
        name = t.get("Name") or ""
        result = t.get("Result")
        last_raw = t.get("Last") or ""

        # Task Scheduler reports states through LastTaskResult too, and they are
        # non-zero without being failures: 0x41301 running right now, 0x41302
        # disabled, 0x41303 never run, 0x41304 no more runs, 0x41305 not yet started.
        # A job that happens to be mid-run at session start is not a broken job.
        informational = {0x41301, 0x41302, 0x41303, 0x41304, 0x41305}
        if isinstance(result, int) and result != 0 and result not in informational:
            hint = LOG_HINTS.get(name, "")
            msg = "exited %d on its last run" % result
            if hint:
                msg += " - evidence: %s" % hint
            problems.append((name, msg))

        window = WATCHED.get(name)
        if window and last_raw:
            try:
                last = datetime.fromisoformat(last_raw)
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                age_h = (now - last).total_seconds() / 3600
            except ValueError:
                continue

            if age_h <= window:
                continue

            # "Overdue" is meaningless without knowing whether the machine was ON.
            # This is a desktop: it is legitimately off overnight and for whole weekends.
            # A weekend off puts every daily job ~76 hours behind, and reporting that as a
            # fault every Monday is exactly how a health check trains its reader to skim.
            #
            # So compare the overdue span against uptime. If the machine has been up for
            # LESS time than the job is overdue, it was off for part of that window and the
            # miss is explained. Report it, but say so -- suppressing it entirely would
            # hide a job that is failing AND happens to follow a reboot.
            if uptime_h is not None and uptime_h < age_h:
                catches_up = t.get("CatchesUp")
                note = ("%d h overdue, but the machine has only been up %d h - most likely "
                        "downtime rather than failure" % (age_h, uptime_h))
                if catches_up is False:
                    note += (". NOTE: this task has StartWhenAvailable=False, so it does "
                             "NOT catch up a missed run - that day is simply skipped")
                problems.append((name, note))
            else:
                problems.append((
                    name,
                    "has not run for %d hours (expected within %d) and the machine has "
                    "been up throughout - it had the opportunity and did not take it"
                    % (age_h, window),
                ))

    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({
            "checked_at": now.isoformat(timespec="seconds"),
            "uptime_hours": round(uptime_h, 1) if uptime_h is not None else None,
            "tasks": tasks,
            "problems": [{"task": n, "detail": d} for n, d in problems],
        }, indent=2), encoding="utf-8")
    except OSError:
        pass

    report(problems)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)

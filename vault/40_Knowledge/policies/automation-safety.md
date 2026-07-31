---
title: Automation Safety
aliases:
  - blast radius contract
  - kill switch for scheduled jobs
  - unattended job rules
status: active
created: 2026-07-27
updated: 2026-07-28
privacy: working
applies_when: >
  Writing, scheduling, or modifying anything that runs unattended: a scheduled
  task, a hook, a cron entry, or a script another job invokes.
verify: >
  List your scheduled tasks and read the hooks block in your settings file.
  Confirm every entry appears in the inventory table below.
---

# Automation Safety

Unattended code is the only code that can do damage while nobody is watching. Everything
here is cheap to add up front and expensive to retrofit after an incident.

## The kill switch

**One file stops every unattended job:**

```
~/.claude/automation.paused
```

Create it to pause, delete it to resume. No service restart, no scheduler surgery, no
editing scripts under pressure. Per-job variant: `~/.claude/automation-<jobname>.paused`.

Every hook and every scheduled script checks for it. Two lines each.

**Check the coverage, do not assert it.** This section originally claimed universal
coverage. When actually read against the machine it was 4 of 5 jobs — and the uncovered job
was the one missing from the inventory table below. **An inventory that omits a job cannot
audit it, and a claim of completeness over an incomplete list reads as verification.**

## Two tiers

A ten-control checklist applied to a job that appends one log line is theatre, and theatre
gets skipped, which is how real controls go missing. **Decide the tier first, from what the
job deletes or overwrites — not from how important it feels.**

**Tier 1 — mutating.** Deletes, overwrites, or moves anything, or writes outside its own
working directory. Gets the full contract below.

**Tier 2 — contained.** Appends or rewrites only files it owns, and deletes nothing. Needs
four things and no more: **a kill switch**, **bounded growth** on anything append-only,
**exit-code honesty**, and **a row in the inventory**.

Anything unattended that **mutates the memory store** is Tier 1 by definition, whatever else
it does. The store is the record everything else gets reconstructed from.

Tier 2 is a smaller list, not a waiver.

## The contract

Tier 1 jobs get all of these before being scheduled. Where a control does not apply, it
should be *stated* as not applying, not silently skipped.

| Control | Why |
|---|---|
| **Kill switch** | Stop it without editing anything under pressure. |
| **Dry-run default** | Destructive capability is opt-in via `--apply`, never the default. |
| **Resource floor** | Abort if free disk is below a threshold. A job that fills the disk takes the machine with it. |
| **Runaway guard** | Abort if the thing it manages has grown implausibly. |
| **Action cap** | A bounded number of mutations per run, logged when the cap is hit. |
| **Rollback snapshot** | Written *before* the first mutation. If the snapshot cannot be written, the run aborts. |
| **Verify the artifact** | Check what was produced. An exit code is not evidence. |
| **Never hard-delete** | Move to an archive location. Deletion is a separate, deliberate, human step. |
| **Report retention** | Keep a bounded history of run reports so a silent failure leaves a trace. |
| **Bounded growth** | Any append-only log needs rotation, or it becomes the runaway. |

## The inventory

Keep a table of every unattended job: name, trigger, what it mutates, blast radius, controls
present. **A job that is not in this table is not governed by anything above. Adding the row
is the control; the rest is detail.**

This is the section that goes stale first. Mine went stale within hours of the warning being
written — two of five rows wrong on a same-day re-read, with nothing having changed on the
machine.

## An alarm nobody reads is not an alarm

Every control above is about the **job**. There is a third thing a job needs, alongside a
way to prove it worked and a way to be stopped: **a way to be heard.**

This was learned the expensive way. A staleness alarm fired exactly as designed — detected
a zero fetch, wrote a `STALE` log line, exited 2, and Task Scheduler recorded the non-zero
result. **Nobody looked.** It was found a day later, by accident, while auditing something
else.

`hooks/task-health.py` in this kit closes that gap. It surfaces two things at session
start and diagnoses neither:

1. **A non-zero last result** on any task you're watching, with that job's log path named
   — at 3am the difference between "job X failed" and "job X failed, its log is *here*" is
   most of the value.
2. **A task that has not run inside its window.** A job that stops firing reports nothing
   at all, which is how a ten-day backup gap once passed unnoticed.

### "Overdue" is meaningless without knowing whether the machine was on

The naive version of check 2 reports every daily job as overdue each Monday, because a
desktop is legitimately off for a weekend — roughly 76 hours. **A check that cries wolf
every Monday trains its reader to skim, and then the real finding is skimmed too.**

So compare the overdue span against **system uptime**. If the machine has been up for less
time than the job is overdue, it was off for part of that window and the miss is explained.
Report it — but say so. Suppressing it entirely would hide a job that is genuinely failing
*and* happens to follow a reboot.

Two distinct messages, and the distinction is the whole point:

- *"76 h overdue, but the machine has only been up 2 h — most likely downtime"*
- *"76 h overdue and the machine has been up throughout — it had the opportunity and did
  not take it"*

### Check whether your tasks even catch up

Windows tasks have a `StartWhenAvailable` setting. With it **off**, a task missed while the
machine was asleep is simply skipped — that day never happens. With it on, it runs late.

Worth auditing: in the setup this came from, two jobs caught up and a third silently did
not, and nothing surfaced the asymmetry until this hook started reporting it.

## Exit code 0 is not evidence

A daily pipeline here **served frozen data for 21 days while reporting success every
morning.** Its source was unreachable; it rendered from a persisted store rather than from
the fetch, so the output directory kept getting fresh timestamps and a plausible file full
of three-week-old content. Every run exited 0.

1. **Verify the artifact.** Check the thing you meant to produce, and check a content
   property of it — a count, a newest-record date — not just that it exists.
2. **Fresh output timestamps are not evidence either.** A file rewritten daily from stale
   inputs looks *healthier* than one that stopped being written. **The absence of failure is
   not the presence of success.**
3. **A job needs a staleness alarm, not just a kill switch.** Parse your own pipeline's
   count line; when it is zero **or the line is absent at all**, exit non-zero and say why.

And: **fixing the failure you found does not mean you found the only failure.** Restoring
the unreachable service here was not enough — the source itself had stopped polling and
served its own stale cache. Two failures were stacked, and a non-zero count looked healthy
in that state.

## Hooks specifically

Hooks run on **every** session or tool call, so their failure modes differ from scheduled
jobs:

- **Always exit 0.** A hook that errors must never block a session or a tool. Swallow
  exceptions.
- **Respect an opt-out env var** (`CLAUDE_HOOKS_SKIP`). Nested and headless runs must be
  able to opt out, or a hook's output gets captured as a subprocess's answer.
- **Timeout every external command.** A hung `git` call hangs session start.
- **Be quiet when there is nothing to say.** SessionStart stdout enters the context window.
  Silence is the correct output for a healthy state — with one exception: a
  post-compaction re-orientation hook *should* always speak, because the whole point is
  that context was just lost.
- **Watch cumulative cost.** Consolidating five `git` calls into one
  `status --porcelain=v2 --branch` took one hook from 7.6s to 2.8s per session start.
- **Hooks on the same event run in registration order and share stdout.** A second hook on
  an event must be silent when healthy, must not depend on the first having run, and must be
  checked for cumulative time cost.

## Schedule nothing you have not run end to end

Two latent bugs were found in a backup script that had run nightly for months, both in a
code path the schedule never invoked. Neither was a bad decision. Both were **untested code
paths**.

Registration is not evidence. Run it once, manually, against real data, and read the output.

## A safety document is unattended code too

Every claim on this page was checked against the machine a second time on the day it was
written. Two of five inventory rows were wrong and the kill switch covered 4 of 5 jobs
rather than all of them. Nothing had changed in between — the note was simply written from
what was believed rather than read.

**It runs in the head of whoever reads it next, and it fails the same way: silently, in a
path nobody exercised.** The fix is the same as for the scripts — run it end to end. For a
note, that means re-deriving each claim from the machine, not re-reading the prose and
finding it plausible.

## Search Anchors

- what is the kill switch for scheduled jobs
- how do I pause automation
- what rules apply to writing a hook
- how do I know if a scheduled job failed
- what surfaces a failed task
- why does my health check fire every monday
- which tier does a new unattended job belong to
- why did a job report success with stale data
- what should I check before scheduling something

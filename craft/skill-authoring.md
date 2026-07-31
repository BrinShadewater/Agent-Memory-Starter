# Skill and procedure craft

Everything here is about **skills** — packaged procedures an agent triggers on its own.
It is separate from the vault because it applies whether or not you run a memory system.

Most of it was learned by writing skills that misfired, so the failures are named.

---

## Triggering

### `TRIGGER` and `SKIP`, and `SKIP` must name the alternative

A skill's description is the only thing deciding whether it fires. Write both halves.

```
TRIGGER when the user says X, Y, Z; or before doing W.
SKIP for A (use skill-a), for B (use skill-b). This skill owns C.
```

**A bare `SKIP` is half a rule.** "Not for image work" leaves the agent with nowhere to
go, so it either fires anyway or does the work unguided. "Not for image work (use
`image-pipeline`)" routes it. Every skip case should name where the work actually goes.

The closing "this skill owns C" line is worth writing too — it settles boundary
disputes between overlapping skills in one clause.

### Name skills for a class of work, never a task

`fix-the-footer-flicker` is a task. `visual-regression-pass` is a class. Task-named
skills accumulate, never fire twice, and quietly become the reason the skill list is
unreadable.

### Watch for collisions

Three skills that all plausibly answer "run my morning brief", with no routing between
them, is a real state a skill library reaches. **The fix is a `SKIP` clause on each one
naming the canonical one**, plus retiring the losers. The gap is usually execution, not
detection — the collision is normally already known and simply never resolved.

---

## Procedure design

### A completion contract

State what "done" means, in the skill, explicitly:

> Complete when every applicable check has a recorded status, all writes are verified,
> failures are reported, and the report is delivered.

Without it, "done" drifts to mean "stopped".

### Invocation modes must disclose what they skipped

A `quick` mode is fine. **A quick mode that does not say what it skipped is not** — the
user reads a clean report and assumes full coverage. Any abbreviated run states its own
omissions in the report.

### A preflight that classifies, never aborts

Check dependencies up front and sort them into **available / unavailable / not
applicable**. Then proceed with what is available.

The failure this prevents: one missing optional dependency aborting an entire run that
could have completed 90% of its work. Degradation should be **declared and documented**,
not discovered.

### Bounded retry

One attempt, then record and move on. **An unbounded retry loop inside a procedure is
indistinguishable from a hang**, and the caller cannot tell which it is.

### Failure messages carry the recovery procedure

An error that says what broke is half a message. Say what to do about it — and **gate
the fallback with "then and only then"**, or the degraded path quietly becomes the
default path.

### Truncated output must announce itself

If a step prints the first 20 of 400 results, say so and name the command for the full
list. Silent truncation is how a partial answer gets treated as complete.

---

## Reporting

### The seven-state vocabulary

These are genuinely distinct, and collapsing them destroys information:

`completed` · `nothing found` · `not applicable` · `skipped` · `failed` ·
`could not verify` · `awaiting approval`

**The dangerous collapse is "could not verify" into "nothing found."** One means the
thing is absent; the other means you did not look successfully. A pipeline reporting
"no problems found" when it means "the check did not run" is worse than a pipeline that
crashes.

### Lists, not counts

"3 notes updated" is unauditable. The three filenames are. Counts are a summary of
evidence; give the evidence.

### Per-category answers, with the literal word "Nothing"

Do not consolidate absences into prose. If a category had no findings, say
`Nothing`. A category silently omitted is indistinguishable from a category that was
never checked.

### Report before asking

Deliver what you have, *then* ask your question. A procedure that stops to ask before
reporting throws away work the user could have acted on.

### Never report a metric the data cannot support

"Skill X is dormant" is not supportable when the usage log is three days old and
dormancy is defined over a month. **Say so and skip the metric.** A confident wrong
number is worse than no number.

---

## Modifying skills safely

### The self-modification guard

**Never let a procedure patch itself mid-run.** The version on disk changes underneath
the version executing, and the result is neither.

### The patch protocol

1. Patch narrowly.
2. Re-read the file.
3. Validate frontmatter and structure.
4. Show the diff.
5. **Auto-revert if validation fails.**

Step 5 is the one that gets left out and the one that matters.

### `name:` must never change

Installation overwrites by frontmatter name. **A changed `name:` silently creates a
second skill instead of replacing the first**, and now two versions fire on overlapping
triggers with no indication of which one ran.

### Edit source, package, install — never edit the installed copy

Installed skills are typically a managed cache. Edits there get reverted, or worse,
survive locally and diverge from the source nobody realises is now stale. Keep sources
somewhere you control and treat the installed copy as an artifact.

### Verification requires a fresh session

**A running session's skill list is fixed at start.** No amount of re-checking inside
the current session proves an install worked. Start a new one.

---

## Auditing a skill library

### Usage telemetry, or you are guessing

`hooks/log-skill-usage.py` in this kit appends one JSONL line per skill invocation. Any
judgement about which skills earn their keep rests on impression until something records
what actually fires.

**And do not report dormancy until the log covers the dormancy window** — a skill that
looks unused because the log is three days old is a false positive.

### Word-boundary matching, not substring

A scan for skills making runtime claims matched `mount` inside `paramount` and
`blend_amount`. Two false alarms against skills making no runtime claim at all. Use
word boundaries in any automated scan over prose.

### A locator is not a health metric

A scan that finds which files mention a pattern tells you where to look. It does not
tell you whether anything is wrong. Label such tools as locators, or their output gets
read as a score.

### The over-capture tripwire

If a skill is firing constantly on things it should not, that is a trigger problem, not
a user problem. And **repeated reject-and-re-add of the same lesson means the domain is
unstable** — surface that as a signal rather than continuing to arbitrate individual
cases.

---

## Orientation files (`CLAUDE.md`, `AGENTS.md`)

### Load path first

An orientation file only loads from the working directory upward. **A file nothing puts
in front of an agent is reachable only by an agent that already knows to look — which is
the one case where it is not needed.**

Map your coverage honestly: for each directory a session realistically starts in, list
what actually loads. The gaps are usually the busiest directories.

### Keep it a signpost, not the rules

The orientation file should point at where the rules live and carry only the hard
prohibitions inline. Everything duplicated between it and the vault will drift, and then
you have two answers.

### Per-agent files drift

`AGENTS.md` and `CLAUDE.md` are different files. When a durable project rule changes,
**update both** — or one agent operates a rule the other has never heard of.

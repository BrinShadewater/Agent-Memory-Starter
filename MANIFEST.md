# Manifest

What is in the kit, and — the more useful half — what was deliberately left out.

## Contents

### `vault/` — the memory structure, shipped empty

| File | What it is |
|---|---|
| `schema.md` | The frontmatter contract. `applies_when:` and `verify:` do most of the work. |
| `00_WakeUp/CURRENT_CONTEXT.md` | Paths and host context. Documents what deliberately is *not* in it. |
| `00_WakeUp/NEXT_ACTIONS.md` | The ranked list of what is left. First read of every session. |
| `10_Rules/operating-rules.md` | The rules, plus the destination ladder. **Edit these.** |
| `10_Rules/verification-discipline.md` | An absence is a claim about the whole search space. Eight false alarms tabled. |
| `40_Knowledge/policies/memory-write-guards.md` | What never goes in, and what looks like a lesson but poisons the store. |
| `40_Knowledge/policies/git-safety.md` | Before editing, before cleaning, and the four places work hides. |
| `40_Knowledge/policies/automation-safety.md` | Two-tier blast-radius contract, kill switch, the exit-code-0 incident. |
| `40_Knowledge/policies/windows-scripting.md` | cp1252, robocopy, exit-code bitmasks. Silent-failure traps. |
| `40_Knowledge/policies/multi-agent-handoff.md` | Only relevant if more than one agent works in your setup. |
| `templates/` | session-close, decision-record, project-home. |
| Folder `README.md`s | What belongs in each numbered folder, and its characteristic failure mode. |

### `hooks/`

| File | Notes |
|---|---|
| `git-sweep.py` | `SessionStart`. Needs `AGENT_PROJECTS`. Silent when healthy. |
| `post-compact-reorient.py` | `SessionStart(matcher: "compact")` — **not** `PostCompact`. |
| `log-skill-usage.py` | `PostToolUse(matcher: "Skill")`. Rotates at 2 MB. |
| `task-health.py` | `SessionStart`. Windows Task Scheduler only; skips silently elsewhere. Select which tasks it watches — it ships watching none. |
| `install-hooks.py` | Dry-run by default. Backup, additive merge, dedupe, refuse-missing. |

### `skills/project-memory/`

`SKILL.md` plus three scripts: `git_status_capture.py` (355 lines, covers all four
hiding places), `lint_frontmatter.py` (211 lines), `scaffold_journal.py` (235 lines).

### `skills/skill-maintenance/`

`SKILL.md` plus four tools: `build_skill.py` (the validate-before-install gate),
`check_scoped.py` (single-runtime claims), `scan_skills.py` (**a locator, not a health
metric**), `show_hits.py` (triage). The three scanners carry pattern lists marked
**EDIT THIS FOR YOUR SETUP** - they are worthless until they describe your paths.

### `skills/site-scaffold/`

`SKILL.md`, `references/stack.md`, `scripts/init_site.py`. **The stack is a choice, not a
recommendation** - the transferable part is having one standard, a verify gate from day
one, and a scaffold that refuses to clobber.

### `tools/README.md`

Two adjacent tools pointed at rather than copied in, with the reasoning. Read it before
redistributing any skill package.

### `craft/skill-authoring.md`

Skill and procedure craft. Independent of the memory system — useful even if you throw
the vault away.

---

## Deliberately not included

### Anything personal

The user model (`working-with-<you>.md`) ships as a concept described in the close-out
flow, **not as a file**. A user model is the single least portable artifact in any memory
system, and shipping someone else's is worse than shipping none.

Same for the private-material boundary: the policy says *keep a private location outside
the vault, and keep it out of every index and agent read path*. Where that lives is
yours.

### Project-specific skills

The setup this came from runs about a dozen skills. Most are not here, on purpose:

- **Content-pipeline skills** for one specific book project. Useless to anyone else.
- **A deploy skill** naming specific repos, hosts, and build traps.
- **A prose/voice skill** encoding one person's writing voice. Actively harmful to
  anyone else — it would make your writing sound like them.

The pattern worth taking from all of them is in `craft/skill-authoring.md`, which is why
that file exists. The site scaffold *was* generalised and is included, with its stack
clearly labelled as one choice among many rather than a recommendation.

### Two adjacent tools, for provenance reasons

**An SEO audit skill** - not mine to give. It is third-party MIT code by other authors,
already public and maintained upstream. Pointed at in `tools/README.md`.

**An image pipeline** - the tool is good; the package is 3.2 MB of which most is brand
assets, marketing PDFs, render scratch, and two commercial strategy documents. Stripping
it to the tool is real work, not a copy. It is the worked example of the
"never ship your author's debris" rule.

Both decisions are the same judgement: **check what a package actually contains before
redistributing it.** A `.skill` is a zip, and the file listing tells you things the
description does not.

### Ideas evaluated and rejected

Recorded so they are not re-proposed. These are design options weighed for *this* setup —
a rejection here means "wrong for a three-agent markdown vault", not "bad idea". Several
of them are load-bearing in systems that made different trade-offs, and made them for
good reasons.

- **A vector store for memory.** Rejected for this shape of setup: single-agent by
  design, opaque to grep and diff, and it brings its own maintenance surface. Markdown
  plus aliases and search anchors has been competitive. **If you add retrieval, scope it
  to retrieval, never storage.**
- **An `N/5` confirmation counter** for promoting lessons from hypothesis to rule. The
  lifecycle is sound; the arithmetic is theatre. Most rules never reach 5/5 organically,
  promotion is a judgement call anyway, and the number ends up set by hand as a status
  marker. Dated evidence lines do all the real work. Kept the ladder, dropped the count.
- **A mandatory session-start domain ceremony.** A confirmation round trip before
  answering anything taxes every trivial session.
- **A knowledge graph** over the notes. Git answers the same temporal questions without
  needing dangling-reference validation.
- **Per-thread continuity notes** surfaced at session start. *Rejected, then adopted —
  the reversal is more useful than the original call.* The rejection was that it
  duplicates `NEXT_ACTIONS.md`, and that two handoff mechanisms mean two places to look
  and guaranteed drift.

  What that missed: the two answer different questions. `NEXT_ACTIONS.md` is **one ranked
  list for the whole setup** — what should be worked on next. A continuity note is
  **per work thread** — where *this* piece of work stopped and what its next single step
  is. Parallel threads were the case that broke the original reasoning: with one file, the
  last session to close overwrites the context of every other thread in flight, and the
  loss is silent.

  The shape that works, if you add it: one small file per thread, keyed by a slug, injected
  at session start when it is newer than some cutoff. Keep it a **pointer, not a
  transcript** — where things stand, the single next action, and the path to the note
  holding the detail. Never record volatile state (branch names, dirty files) as fact in
  it; say "verify before acting" and let the sweep hook answer. Delete a thread's note when
  the thread finishes rather than letting it go stale.

  **The drift warning still stands** and is the thing to design against: the two mechanisms
  only coexist because their scopes genuinely differ. If you cannot state in one sentence
  which question each answers, you have two of the same thing and should keep one.

  Not shipped as a hook here — it is a handful of lines and its behaviour depends on where
  your agent stores per-session state, so it is written up rather than automated.
- **A correction nudge** — a Stop hook forcing a one-line "notable moment or nothing".
  Held rather than rejected. It is the mechanism that converts "you should record
  decisions" into "answer this now", and it is the real fix for an empty decisions
  folder. It is also the most intrusive thing on this list. **Consider it if your
  corrections keep going unrecorded**; diligence is not a mechanism.

---

## Provenance of the war stories

Every incident cited is real and happened in one working setup. The load-bearing ones:

- A "current git state" note wrong on two of three repos after eleven weeks unchecked.
- Eight consecutive false findings in one audit, all scoping artifacts, six caught by a
  human pushing back rather than by any check.
- A daily job serving 21-day-old data while exiting 0 every morning, with fresh output
  timestamps the whole time.
- A memory vault silently unretrievable for eight weeks while every sync reported
  success.
- A backup whose project-file path had never once been executed, carrying two latent
  bugs — including a default of one million retries at 30 seconds each.
- A safety document that was wrong about the machine one day after being written,
  because it was written from belief rather than read from the machine.

That last one is the reason for the closing note in `automation-safety.md`: **a safety
document is unattended code too.** It runs in the head of whoever reads it next, and it
fails the same way — silently, in a path nobody exercised.

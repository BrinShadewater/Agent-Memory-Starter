---
name: project-memory
description: >
  Operate inside a markdown memory vault: orient at session start, write durable
  notes correctly, and close a session out so context carries forward. Encodes
  the read-before-write protocol, frontmatter rules, journal naming, git safety
  rails and evidence-first session close.
  TRIGGER when the user says "wake up", "calibrate", "start session", "what's the
  state", "log this", "save this decision", "remember this", "wrap up", "close
  out", "end session"; when they reference the vault; or before editing any file
  under a tracked project.
  SKIP for one-off factual questions that need no durable record, for building or
  deploying (use the project's own deploy procedure), and for authoring or
  auditing skills themselves (use skill-authoring craft notes). This skill owns
  the vault.
---

# Project Memory

**The vault is the data. This skill is the discipline.**

The vault is usually fine. The failure mode is agent discipline in using it — context
gets dropped at session close, volatile facts get recalled instead of checked, and the
next session burns time relearning what should already be known.

Set `AGENT_VAULT` to your vault root. Three flows; pick the one that matches.

---

## Flow 1: WAKE UP (orient at session start)

**Trigger when:** the user says "wake up" / "calibrate" / "what's the state" / "let's
work on X"; they name a project you have no context on; you are about to touch a tracked
project file; or you are in a fresh conversation and the workspace is the vault.

1. **Read `00_WakeUp/NEXT_ACTIONS.md` first.** The ranked list of what is actually
   outstanding. Read it **before proposing work and before quoting any planning
   document** — plans go stale in both directions, and **proposing already-finished work
   is the specific failure this prevents.**

2. **Read `00_WakeUp/CURRENT_CONTEXT.md`.** Paths and host context. It deliberately
   does **not** record live git state; that is computed fresh.

3. **Read `10_Rules/operating-rules.md`.** If a later instruction contradicts one of
   these, the rule wins — say so and ask.

4. **Read `10_Rules/verification-discipline.md`** if you are about to audit, sweep, or
   report on the state of anything.

5. **If touching a project, read its home note** in `50_Projects/`. Path, stack, status,
   conventions, open questions, safe next actions. **Read this before asking the user
   anything — most answers are already here.**

6. **Read the policy that matches the work:** code edits → `git-safety.md`; anything
   unattended → `automation-safety.md`; scripting on Windows → `windows-scripting.md`;
   more than one agent → `multi-agent-handoff.md`.

7. **Skim the last one to three journal entries** in `90_Journal/` (filenames sort by
   date). They tell you what was actually done recently, which often differs from what a
   project note's `updated:` field suggests.

8. **Verify, do not trust.** Memory is a snapshot. Before acting on a recalled fact —
   branch state, file paths, what is installed — check it. **Recall is a starting point,
   not ground truth.**

9. **Summarise back.** "I'm oriented on X. Here's what's open, here's what I'd suggest
   next. Want me to verify state first?" Then ask only for what is genuinely missing.

### Four git traps that give confident wrong answers

Use `scripts/git_status_capture.py`, which handles all four, rather than improvising:

- **Repos nest one level down.** A project folder is often not the repo. Scanning one
  level reports it unversioned.
- **Worktrees live outside the project tree.** No directory scan finds them.
  `git worktree list`.
- **No upstream does not mean no remote.** A branch can diverge from a remote holding
  most of the history. `git remote -v`.
- **A configured upstream does not mean the commits were pushed.** `git status` reports
  ahead/behind for the *current branch only*. Ask
  `git rev-list --count <branch> --not --remotes` per branch, and `git stash list` for
  the fourth hiding place.

**Before reporting that anything is missing, establish that you searched everywhere it
could be.** An absence is a claim about the whole search space.

---

## Flow 2: WRITE (create or update notes)

**Trigger when:** the user says "log this" / "save this decision" / "remember this"; a
durable decision was made; meaningful work was done; or a project's state shifted.

**Pick the destination first.** Getting this right is what makes the vault searchable
later.

| Note type | Lives in | When |
|---|---|---|
| Journal entry | `90_Journal/YYYY-MM-DD-topic.md` | session work, audits, activity |
| Decision record | `30_Decisions/` (`templates/decision-record.md`) | choices affecting architecture, stack, hosting, money, public messaging, security |
| Project home update | `50_Projects/{Project}.md` | durable state change, not micro-experiments |
| New project home | `50_Projects/{New}.md` (`templates/project-home.md`) | starting on something new |
| Inbox dump | `20_Inbox/` | raw fragments to triage; promote upward later |
| Knowledge / policy | `40_Knowledge/` | durable knowledge that is not a decision |

**But check the destination ladder first** (`10_Rules/operating-rules.md`). If a *skill*
governed the work and the lesson is procedural, **the lesson belongs in that skill, not
in a note.** A skill fires automatically next time; a note has to be found first.

**Frontmatter is load-bearing.** Schema in `schema.md`. Required: `title`, `created`,
`updated`, `privacy`. Required when the note asserts anything volatile: `verify`.

- Validate before saving: `python scripts/lint_frontmatter.py <note>`
- Scaffold journal entries: `python scripts/scaffold_journal.py --topic "slug" --project "Name" --agent claude`

**Write guards** (full list in `40_Knowledge/policies/memory-write-guards.md`):

- Never store credentials. Ever.
- Never record a negative capability claim — "X is broken" hardens into a false refusal
  months after X is fixed. **Capture the fix, never the failure.**
- Never record environment-dependent failures or transient errors that resolved.
- Brainstorming goes to `20_Inbox/` and only gets promoted once the user confirms.
- Mark uncertain claims `confidence: low`.
- Ask before saving anything personal, financial, legal, medical, or safety-affecting.
  Default no.

**If you run a retrieval index, refresh it after writing — and verify the refresh.** A
sync that reports success is not proof a note is retrievable. One setup here was
silently unretrievable for eight weeks while every sync reported fine: the collection
had never been registered, and nothing ever checked. **Check the index's own listing,
not the sync's exit code.**

---

## Flow 3: CLOSE OUT (end a meaningful session)

**Trigger when:** the user says "wrap up" / "close out" / "we're done"; meaningful work
finished; you are about to lose context; or a commit, deploy, audit or decision happened.

**This flow is evidence-first. Read state before writing anything, never from recall.**

1. **Capture git state.** `python scripts/git_status_capture.py <project>`. Paste the
   output. Do not type it from memory — that is the entire point of the step.

2. **Create the journal entry** from `templates/session-close.md`, or scaffold it.

3. **Fill in every section.** What changed, files touched, git state, decisions, open
   questions, safe next actions, search anchors. **An empty section should say
   "Nothing", explicitly** — a blank is indistinguishable from a step that was skipped.

4. **Update the project home note.** Bump `updated:`, add a `### YYYY-MM-DD - topic`
   work-log entry, refresh open questions and next actions. **The project note is what
   gets searched first**; durable changes belong there, not only in the journal.

5. **If a decision was made, write the decision record.** Do it now. This is the step
   that never happens later, and an empty decisions folder is the normal outcome of
   intending to do it later.

6. **If the session revealed something about how the user works, refresh the user
   model.** Not every session does — most produce project facts, not user facts. But
   when they correct your *approach* rather than your output, override a recommendation,
   or react to how work was handed back, that is user-model signal and nothing else
   captures it.

   **Rewrite that section, never append**, so it stays a current picture rather than a
   log of every small preference. And keep the confidence honest: a handful of sessions
   is a small sample.

7. **If the project keeps a `WORK-LOG.md`, append to it.**

8. **Report what you saved.** "Closed out — wrote `90_Journal/X.md`, updated
   `50_Projects/Y.md`. Open questions: [...]. Safe next actions: [...]."

---

## Report vocabulary

When reporting on a multi-step run, these seven states are distinct and collapsing them
loses real information. **"Could not verify" and "nothing found" sharing a bucket is the
dangerous one.**

`completed` · `nothing found` · `not applicable` · `skipped` · `failed` ·
`could not verify` · `awaiting approval`

Give **lists, not counts** — "3 notes updated" is unauditable, the three filenames are
not. Answer **per category**, using the literal word "Nothing" rather than consolidating
absences into prose. **Report before asking**: deliver what you have, then ask your
question.

## Hard rails

1. **Never push without explicit approval**, per push. Not "the change is small", not
   "they approved one yesterday".
2. **Never edit directly on the default branch** when the repo tracks a remote.
3. **Never overwrite, reset, revert, or delete uncommitted work.** Ask.
4. **Never store secrets in the vault.** Not even temporarily.
5. **Never promote brainstorming to strategy** without confirmation.
6. **Never propagate stale memory.** If memory and current state disagree, trust
   current state and fix the memory.

## When in doubt

Read more of the vault before acting. One extra file read costs far less than
overwriting someone's work, dropping context, or storing a secret. If the answer is
genuinely not in the vault, ask — do not guess at hard rails.

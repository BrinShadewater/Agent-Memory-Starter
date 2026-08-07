---
title: Verification Discipline
aliases:
  - how to avoid false alarms
  - absence is a claim about the search space
  - scoping errors
  - do not infer a mechanism from one observation
  - check the level you are counting at
status: active
created: 2026-07-27
updated: 2026-08-06
privacy: working
applies_when: >
  About to report that something is missing, broken, unversioned, unbacked,
  impossible, or unavailable. Also before stating how a system behaves based on
  one observation of it.
verify: >
  Re-run the check at a different scope (wider path, different level, second
  method) and confirm the finding survives.
---

# Verification Discipline

Every false alarm raised during one systems audit was a **scoping artifact**. Not one was a
real problem. Each dissolved the moment the search widened. Eight for eight is consistent
enough to be worth a standing rule.

## The rule

**An absence is a claim about the entire search space, and it is only as good as the space
you actually covered.**

Before reporting that something is missing, broken, or impossible:

1. Name the space you searched.
2. Name at least one place the thing could be that you did **not** search.
3. Search it.
4. Only then report.

And separately: **do not infer a mechanism from a single observation.** One disappearance is
not a policy. One empty directory is not a capability limit. Watch it twice, or find the
thing that documents it, before building on the theory.

## The lexical trigger

**Any sentence containing an absolute — "nothing", "zero", "none", "no rows", "clean",
"empty", "missing", "doesn't exist" — must state its coverage in the same breath:** what
was searched, from which inventory, before the result stands.

Why this exists as a separate trigger when the rule above already covers it: **the rule
fires only when an agent notices it is making an absence claim, and that noticing is the
step that fails.** One agent's logged record showed three recurrences across three
different tools where this discipline was fully loaded and still did not fire, because
each query looked ordinary. The fix that held: key the trigger off the *shape of the
claim* (a string-matchable absolute word), not the shape of the operation. A lexical
trigger needs no judgement call and therefore no meta-audit. Recognition, not rigour, is
the binding constraint — most rows in the incident log below were caught by the user
pushing back, not by the discipline firing.

## The incident log

Each row is a confident claim that turned out to be false, and the check that would have
caught it. Keep your own version of this table — the specific traps are what make the rule
stick.

| Claim made | Reality | Scope that was too narrow | The check that fixes it |
|---|---|---|---|
| "9 of 12 projects are not git repos" | 6 repos exist | scanned at depth 1 | recurse 2 levels |
| "This repo has no remote, nothing ever left this disk" | remote exists, `origin/main` has 27 commits | read `@{u}` on a divergent branch | `git remote -v` |
| "That folder is a legacy dumping ground, delete it" | 1.7 GB with live sources and a personal profile | judged by folder name and a partial listing | open it |
| "This copy has no live counterpart" | byte-identical copy exists | compared top-level names only | search nested paths |
| "Seven unique files exist nowhere else" | feature moved repos; live version worked the day before | compared one repo and its remote | grep the whole tree |
| "The private profile now exists in only one place" | two more copies, one a different revision | asserted containment without sweeping | `find` by filename, compare checksums |
| "It cannot be installed from here" | the target directory works, it just did not exist yet | one check of a directory that was empty | create it and test |
| "The plugin cache is empty" | 29 entries, read minutes later | single snapshot of a directory that churns | read it twice |

Six of the eight were caught by the user pushing back rather than by any check. That is the
part worth fixing.

## A correction that does not sweep every copy is not finished

Three instances in one day, all the same shape: a fact was corrected in one place and left
standing in another, where it went on misleading.

- A retired runtime was swept from the vault, the session-close template, and the skill —
  but not from a second agent's own config, which for three days was still instructed to
  maintain the dead service, runbook and all.
- A false claim ("this repo has no commits yet") was corrected in one orientation file —
  which even recorded that it had misled an agent — while the project home note kept the
  false version for days.
- A new rail was written into the planning note in the morning, and the author wrote a
  whole session's notes in violation of it the same day, having restated the rail in three
  files along the way.

The mechanism is always the same: **the thing's category changed, and habits attached to
the old category came along.** When correcting a durable fact, ask where else it is
asserted — other agents' configs, project notes, skills, repo docs — and sweep all of them
in the same pass. Grep the whole tree for the old claim before calling it fixed.

## A verification step written from a note and never run is a guess

A documented pre-update check expected "84 insertions across two files". Run for real, it
returned three files and 96 insertions — a lockfile had gone dirty in the meantime. The
protected changes were intact, but the check as written read as "something changed" and
would have triggered a recovery that was not needed. Same shape twice more the same day: a
linter carried two latent crashes that only surfaced the first time it was pointed at a
directory instead of a single file, and a baseline nobody had measured turned out to
predate the change being blamed for it.

**Run the check you are about to write down, against real breadth, before writing it
down.**

## Traps that generalise

- **Repos nest one level down.** A parent folder is often not the repo.
- **Worktrees live outside the project tree.** No directory scan finds them; run
  `git worktree list`.
- **No upstream does not mean no remote.** Run `git remote -v` before concluding anything is
  unbacked.
- **A count read at the wrong level is an artifact, not a fact.** A backup of a live store
  capturing 534 of 2,194 entries looks exactly like data loss.
- **A count read off a live store is wrong, and wrong low.** Stop the writer, then count.
- **Directories that churn give snapshots, not properties.** Anything read from a cache the
  application rebuilds is true for that instant only.

## Why this is a rule and not a note

A false alarm is not free. Each one in that session produced real work: a rescue archive
that was not needed, a deletion plan that had to be withdrawn, a fallback plan the user had
to reject, and a stretch of effort spent on a data-loss scare that was a divergent branch.

**Being wrong in the cautious direction still costs time and still erodes trust in the next
finding.**

For a memory system specifically: a learning loop that files false findings as lessons is
worse than no learning loop, because now the false finding has a confidence counter on it.

## Search Anchors

- why do my audits keep producing false alarms
- how do I check whether something is really missing
- is that folder really a duplicate
- what scoping mistakes have been made before
- how should I verify before reporting something broken

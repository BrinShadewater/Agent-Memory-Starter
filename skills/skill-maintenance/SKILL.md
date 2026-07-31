---
name: skill-maintenance
description: >
  Audit, clean, upgrade, and repackage your own skills on an ongoing basis. Use
  whenever the user says "look at my skills", "audit my skills", "are any of my
  skills stale / bloated / redundant", "upgrade a skill", "clean up a skill",
  "repackage this skill", "should I retire any skills", or wants to wire skills
  together. Encodes the packaging contract, the patch protocol, and the failure
  modes that silently corrupt a skill library.
  SKIP for building a brand-new skill from scratch (use skill-creator) and for
  memory-vault work (use project-memory). This skill audits and repackages skills
  that already exist.
---

# Skill maintenance

A standing playbook for keeping a skill library healthy. The point is to never re-derive
the traps or re-hunt for where things live.

Read [`craft/skill-authoring.md`](../../craft/skill-authoring.md) alongside this — that
covers how to *write* a skill; this covers how to *maintain* a set of them.

## First: know which runtime you are in

Skills that make claims about one runtime — a sandbox, a mount, a host-only tool — without
naming the other case will actively mislead an agent running elsewhere. **An agent that
follows sandbox rules on a real host wastes effort staging work it could do directly.**

Establish where you are before touching files, and when writing a skill that has runtime
constraints, **say which runtime each rule belongs to.** `scripts/check_scoped.py` is the
automated version of this check.

## Never edit an installed skill

Installed skills are typically a **read-only or app-managed cache**. Editing them does
nothing, or worse, appears to work and is silently reverted later.

The loop that actually sticks:

1. Edit the skill's **source** files.
2. Package the directory as a `.skill` — a zip whose top folder is the skill name and
   contains `SKILL.md`.
3. Install from the package.

**Keep a source tree for every skill you own.** Where none exists, extract the package to
a scratch directory, patch there, rebuild. That is the normal case in most libraries, not
the exception.

## The maintenance loop

1. **Inventory.** List the skills; separate the ones you own and can edit from stock ones
   you can only enable or disable.

2. **Audit each against four lenses:**
   - *Staleness* — dead file references, old tool names, dated facts, broken paths.
   - *Bloat* — scratch directories, `__pycache__`, temp renders, stray PDFs, a `SKILL.md`
     that has ballooned past ~500 lines.
   - *Overlap* — two skills that trigger on the same request. Tighten one description and
     point it at the other (front-door pattern).
   - *Earns-its-keep* — does it actually fire usefully? **Use the telemetry, not your
     impression** (`hooks/log-skill-usage.py`), and do not report dormancy until the log
     covers the dormancy window.

3. **Decide and say it straight:** keep / retire / clean / upgrade.

4. **Make changes in a scratch directory**, against real data. A check tool that cries
   wolf is worse than none.

5. **Wire skills together** where it beats a new skill — a deploy skill that gates on a
   content check, for instance. Integration is often the highest-leverage upgrade
   available and it is consistently under-considered next to writing something new.

6. **Package and validate:**
   ```
   python scripts/build_skill.py <parent-dir> <skill-name> <out.skill> [expected-file-count]
   ```
   Checks zip integrity, a single top-level folder matching the skill name, `SKILL.md`
   present, frontmatter parsing, `name:` exact, an optional file-count guard, no dead
   paths in bundled text, and that every `.py` and `.json` parses. Exits non-zero on any
   failure.

7. **Verify the install, then close the loop.** Tell the user exactly what to click and
   flag anything still theirs to do.

## Quality bar

- **Frontmatter:** `name` plus a *pushy* `description` packed with concrete trigger
  phrases. Agents under-trigger skills; spell out when to use it, and give every `SKIP`
  a named alternative.
- **Lean `SKILL.md`** (under 500 lines). Depth goes in `references/`, deterministic work
  in `scripts/`, output assets in `assets/`.
- **Scripts over prose** for anything repeatable and checkable — tested on real inputs.
- **No scratch in the package.** A skill should not ship its author's debris.
- **Do not surprise the user:** never auto-commit or push to an auto-deploying repo,
  never delete files without explicit permission.

## Self-modification guard — read before editing THIS skill

This is the skill that edits other skills, so it is the one that can edit itself.

**Never patch this skill while running a procedure defined by it.** The instructions you
are following are the ones being rewritten; a half-applied edit changes the remaining
steps under you, and **the failure is invisible because the run continues against the new
text.** If a pass concludes this skill needs changing: finish the pass, report the
finding, then start a fresh run whose only job is that edit.

## Patch protocol, for any skill including this one

1. **Copy the package aside first**, with a dated suffix. Before the first edit, not after
   the first mistake.
2. **Patch narrowly.** One concern per pass. Do not reflow or reorganise while fixing.
3. **Re-read the patched file end to end.** Not the diff — the file. **A diff shows what
   changed and hides what the change broke around it.**
4. **Validate** with `build_skill.py`.
5. **Auto-revert on failure.** Restore the copy from step 1 *before* diagnosing. Do not
   leave a broken package in place while investigating — that is the state an unattended
   run or a distracted session picks up.
6. **Verify the install by file count, never by comparing text.**

## Four failures this protocol exists to prevent

All four happened, and all four were caught by running a check rather than by reasoning:

- **`name:` changed during a rewrite.** Install overwrites by frontmatter name, so the
  edit **silently created a second skill** instead of replacing the first. Two versions
  then fire on overlapping triggers with no indication of which ran.
- **A package went stale against its own installed copy.** The package lacked a patch
  that both the installed skill and the source tree carried, so "reinstalling from the
  package" would have *regressed* the live skill. **Compare package against installed
  before treating the package as newer.**
- **Installing from a bare `SKILL.md` silently deleted every bundled script.** Eight
  skills lost their resources; one lost 101 files including the 37 scripts its own
  instructions call. **And the obvious check passed** — all eight had a byte-perfect
  `SKILL.md`. Count files against the package instead.
- **A substring scan produced false alarms.** A check for skills making runtime claims
  matched `mount` inside `paramount` and `blend_amount`. Use word boundaries.

## Verification requires a fresh session

**A running session's skill list is fixed at start.** No amount of re-checking inside the
current session proves an install worked.

## The scripts

| Script | What it does |
|---|---|
| `build_skill.py` | Rebuild and validate a `.skill` **before** installing. The gate. |
| `check_scoped.py` | Flags skills making single-runtime claims without naming the other case. Word-boundary matching. |
| `scan_skills.py` | **Locator, not a health metric.** Finds which packages mention which patterns. Tells you where to look, not whether anything is wrong. |
| `show_hits.py` | Prints the matching lines from `scan_skills.py` hits, for triage. |

`check_scoped.py`, `scan_skills.py` and `show_hits.py` carry pattern lists marked
**EDIT THIS FOR YOUR SETUP**. They ship with example markers; they are worthless until
they describe your actual retired paths and your actual runtimes.

# Changelog

Notable changes to Agent Memory Kit. Newest first.

This kit is derived from a working private vault, so changes arrive as that vault learns
things — usually a trap that cost someone real time. Entries say what changed and *why it
was worth changing*, because the reasoning is the part you can judge against your own setup.

Versions are `MAJOR.MINOR.PATCH`:

- **MAJOR** — you must change something in your vault to stay compatible (a renamed required
  field, a removed file, a changed contract).
- **MINOR** — new capability or new guidance; existing vaults keep working untouched.
- **PATCH** — corrections and clarifications, no new behaviour.

## [0.3.0] — 2026-08-06

### Changed

- **Orientation-file guidance moved from "update both" to "one canonical file, imported
  by the other".** `craft/skill-authoring.md` and `vault/40_Knowledge/policies/
  multi-agent-handoff.md` previously taught that `AGENTS.md` and `CLAUDE.md` are
  separate files to be hand-mirrored on every durable rule change. Hand-mirroring is
  how the documented 199-line drift happened in the first place. Both now teach the
  structural fix: `AGENTS.md` is the canonical, agent-neutral file (per-agent rules in
  labelled sections), and `CLAUDE.md` shrinks to a Claude Code import line plus a
  genuinely agent-specific addendum. The import is expanded mechanically at load time,
  which is a stronger guarantee than a "read the other file" pointer the model has to
  choose to follow. The direction is forced, not stylistic: tools without an import
  mechanism read `AGENTS.md` natively, so the neutral file must be canonical. The
  "update both" rule survives as the stated fallback for tools supporting neither.
- **This repo's own `CLAUDE.md` now practises the pattern** — an import plus a short
  addendum, replacing the prose pointer. The change was made only after the same
  migration ran across the private workspace it derives from and was verified in a
  live session (import expansion confirmed in loaded context, and by an
  instructions-loaded audit hook).



### Fixed

- **`lint_frontmatter.py` crashed on a directory argument.** It printed "not a markdown file"
  and then died with an unhandled `PermissionError` — a traceback where a usage message
  belonged.
- **`lint_frontmatter.py` crashed on any note whose `status`, `privacy`, `source` or
  `confidence` was a list or empty.** Every enum test was `value not in ENUM`, which raises
  `TypeError: unhashable type: 'list'` on a non-scalar. A bare `source:` in a template file
  parses to an empty list and killed the whole run. Non-scalars are now reported at the
  field's own severity instead of crashing.

  Both bugs had been latent since the linter was written. Neither appeared until it was
  pointed at a whole vault for the first time — checking one note at a time never exercised
  them. **If you have been linting file-by-file, run it over your whole vault once.**

### Added

- **Directory mode.** Pass a folder and the linter walks `*.md` recursively, ending with a
  `N file(s) checked, N failed` summary and a non-zero exit if any failed. Single-file
  behaviour and exit codes are unchanged.
- **`templates/` is skipped in directory mode.** Template frontmatter is placeholder by
  design; linting it produced 5 failures out of 87 on the first run, all noise. A check whose
  failures are all false gets ignored, and then the real one is ignored too. Pass a template
  path explicitly if you do want it checked.
- **`task-health.py`** — surfaces unattended scheduled jobs that failed or went stale.
- Search anchors on the four substantive policy notes, so they are findable by the question
  you would actually ask.

### Changed

- **`windows-scripting.md`: the cp1252 character list was wrong on half its examples.** It
  claimed em dashes and curly quotes break Windows console output. They do not — cp1252
  includes the smart-punctuation block. Arrows, checkmarks and emoji *do* fail. The old list
  was the kind of overstated warning that gets disbelieved, after which the real cases bite.
- Added MSYS/WSL path-mangling and shell-quoting traps to the same note.

## [0.1.0] — 2026-07-28

Initial release: policies, rules, and the `project-memory` skill, de-personalised from a
working vault.

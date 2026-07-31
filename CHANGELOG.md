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

## [0.2.0] — 2026-07-28

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

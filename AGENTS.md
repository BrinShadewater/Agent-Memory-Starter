# AGENTS.md — working on this repo

This file is about **developing the kit**. It is not the kit's doctrine.

The memory rules an agent follows when *using* a vault live in `vault/10_Rules/`
and `skills/project-memory/SKILL.md`. `README.md` explains, at length and on
purpose, why those two overlap. Do not let this file become a third copy — this
repo argues that always-loaded context should stay short and detail belongs in
on-demand docs, and an `AGENTS.md` that sprawled would contradict the thing it
documents.

Contributing to the project, as opposed to working in it: `CONTRIBUTING.md`.
Reporting something sensitive: `SECURITY.md`.

## The rule that outranks everything

**This kit ships empty.** No memories, no project names, no personal data. The
structure is the product, and it is extracted from a real working vault that was
dense with things which must never be published.

That matters more here than in a normal repo: this one has clones. A personal
detail committed is not a tidy-up later — it is in someone else's checkout and in
the history, immediately.

`.gitignore` blocks the live-vault directories (`90_Journal`, `30_Decisions`,
`20_Inbox`) precisely because this layout invites people to use the repo *as*
their vault. Do not remove that block casually.

## Before anything is published

```bash
python scripts/check_export_safe.py           # whole kit
python scripts/check_export_safe.py --staged  # staged files only, pre-commit
```

Exit 0 clean, 1 on a HARD hit, 2 on usage error. HARD hits are shape-based
identifiers (emails, absolute home paths, snowflake IDs) plus anything listed in
`scripts/identifiers.local.txt` — which is **gitignored and must stay that way**.
Only `identifiers.example.txt` ships.

**Three things about this gate that are easy to get wrong:**

1. **That gitignore is not stylistic.** The checker previously carried real
   identifiers as literal strings in its own source, so the leak lived inside the
   leak detector — and because the script skips itself when scanning, it could
   never have flagged it. It was caught by reading the file, not by running
   anything.
2. **A clean run means "the known patterns are absent", never "safe to publish".**
   The docstring says so itself; a new kind of identifier needs a new pattern.
   Grep is not a substitute for reading the diff — that original leak survived a
   grep sweep, because a generic email regex wanted a literal TLD and the strings
   were regex fragments.
3. **A fix in a later commit does not remove anything from history.** If something
   leaks, rewriting history is the remedy, not a cleanup commit on top.

The checker deliberately does **not** scan for secrets. Adding a half-good secret
scanner would imply a guarantee it cannot make; use a real one in CI if you want
that guarantee.

**Known false positive, so it does not train you to ignore the alarm.** If you add
your own GitHub handle to `identifiers.local.txt` — which the instructions tell you
to do — the gate will then block on this repo's *own* URLs, such as the security
advisory link in `.github/ISSUE_TEMPLATE/config.yml`. Those URLs must contain the
owner handle to work at all. The patterns are tuned for de-personalising a private
vault, where the handle should never appear; inside the published repo it
necessarily does.

Two hits on your own canonical repo URLs are expected. **Anything else is not.**
Read every hit rather than dismissing the run — a gate you have learned to wave
through protects nothing, which is the same failure this repo names about alarms
elsewhere.

## Conventions that are decisions, not accidents

- **Python only. No bash, anywhere.** So Windows users need no git-bash, and no
  path has to cross a shell/Python boundary. A `.sh` script here is a bug.
- **`post-compact-reorient.py` registers under `SessionStart` with
  `matcher: "compact"` — never `PostCompact`.** `PostCompact` fires but cannot
  inject into the model's context, so the hook would run and change nothing. This
  is the difference between the hook working and being decorative.
- **Do not "fix" the rules/skill duplication.** It is load-time redundancy and it
  is the safety net: the rules load every session, the skill only when triggered.
  `README.md` has the full argument. If you must cut, cut detail from the rules
  files and let the skill own it, never the reverse.
- **Hooks stay silent when healthy.** A hook that chatters every session gets
  disabled, and then it protects nothing.

## Versioning

`MAJOR.MINOR.PATCH`, tracked in `CHANGELOG.md`. **MAJOR means a user's vault needs
a change to stay compatible** — a real cost to someone downstream, not a version
-number formality. MINOR and PATCH must be safe to take blind.

Write entries with the *reasoning*, not just the change. Most entries here come
from a trap that cost someone real time, and whether it applies to a given reader
depends on their setup.

## Where things live

| Path | What it is |
|---|---|
| `vault/` | The memory structure. Ships empty; schema and policies filled in. |
| `hooks/` | Four hooks plus an installer with real installer discipline. |
| `skills/` | `project-memory`, `skill-maintenance`, `site-scaffold`. |
| `craft/` | Skill and procedure authoring. Independent of the memory system. |
| `scripts/` | The export gate. |
| `tools/` | Pointers to adjacent tools, and why they are not bundled. |

`MANIFEST.md` documents what each file is and — more usefully — what was left out
and why. Read it before adding anything; the omissions are argued, not accidental.

## Provenance worth preserving

Rules here carry their war stories inline, with what actually went wrong. That is
deliberate: a rule written from what you intended is prose, and a rule written from
what broke survives contact with the next reader. If you add a rule, bring its
incident with it. If you edit one, do not quietly delete the incident that earned
it.

The repo is honest about its limits, and that should stay true. It has not been
tested for multiple users, for non-Windows hosts beyond incidental use, or for
vaults past a few hundred notes. Do not let a doc edit quietly upgrade those
claims.

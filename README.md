# Agent Memory Kit

![Licence](https://img.shields.io/badge/licence-MIT-blue?style=flat-square) ![Python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square) ![Claude Skill](https://img.shields.io/badge/Claude-skill-d97757?style=flat-square) ![Shadewater Labs](https://img.shields.io/badge/Shadewater%20Labs-%E2%9A%97%EF%B8%8F-6b4fa2?style=flat-square)

A markdown memory vault, four hooks, three skills, and the operating discipline that
makes them work. For Claude Code, though most of it is portable to any agent that reads files.

**It ships empty.** No memories, no personal data, no project names. The structure and
the rules are the product; the contents become yours as you use it.

## What problem this solves

Agents forget between sessions. The usual fix is a memory store, and the usual outcome is
a memory store full of things that are wrong. This kit is mostly about the second problem.

Three ideas do most of the work:

1. **Volatile facts belong in a hook that recomputes them, not a note someone has to
   remember to update.** Live state written into a note rots, and a stale fact that looks
   authoritative is worse than no fact, because an agent will act on it.
2. **Notes state their own trigger, not their topic.** A note organised by topic has to
   be remembered before it can help. `applies_when:` announces itself.
3. **Capture the fix, never the failure.** "X is broken" written into memory becomes a
   refusal cited back months after X was fixed.

Everything else is detail hanging off those three.

## What's in it

```
vault/         The memory structure. Ships empty, with the schema and policies filled in.
hooks/         Four hooks + an installer with proper installer discipline.
skills/        project-memory  - orient, write, close out (+ 3 validated scripts)
               skill-maintenance - audit, patch and repackage a skill library (+ 4 tools)
               site-scaffold   - stand up a new site on one consistent stack
craft/         Skill and procedure authoring craft. Independent of the memory system.
tools/         Pointers to two adjacent tools, and why they are not bundled.
```

**Read [`MANIFEST.md`](MANIFEST.md)** for what each file is and — more usefully — what was
deliberately left out and why.

### The hooks, which are the fastest win

| Hook | Event | What it does |
|---|---|---|
| `git-sweep.py` | `SessionStart` | Computes real repo state fresh each session. Handles the five traps that make a naive check confidently wrong. Silent when healthy. |
| `post-compact-reorient.py` | `SessionStart(compact)` | Re-orients after context compaction, with named anchors rather than generic advice. |
| `log-skill-usage.py` | `PostToolUse(Skill)` | One JSONL line per skill invocation, so skill audits rest on data instead of impression. |
| `task-health.py` | `SessionStart` | Surfaces scheduled jobs that failed or stopped firing. An alarm nobody reads is the same shape as the problem it was built to catch. Windows Task Scheduler; read-only. |

`post-compact-reorient.py` is registered under **`SessionStart` with `matcher: "compact"`,
not `PostCompact`.** `PostCompact` fires after compaction but cannot inject text into the
model's context, so a reorientation notice printed from it runs and changes nothing. This
distinction is the difference between the hook working and the hook being decorative.

## Install

See [`INSTALL.md`](INSTALL.md). Short version:

```bash
python hooks/install-hooks.py          # dry run, shows exactly what it would do
python hooks/install-hooks.py --apply  # backs up settings.json first, merges additively
```

Then set two environment variables, copy `vault/` where you want it, and **start a fresh
session** — a running session's hooks and skills are fixed at start.

## The 10-minute version

If you adopt nothing else:

1. Copy `vault/` somewhere and set `AGENT_VAULT`.
2. Install `git-sweep.py` and set `AGENT_PROJECTS`.
3. Read [`vault/10_Rules/verification-discipline.md`](vault/10_Rules/verification-discipline.md).
   It is 80 lines and it is the highest-value file here.
4. Add `applies_when:` to notes you already have.

## Why the rules appear twice

A reviewer noticed that `10_Rules/operating-rules.md` overlaps heavily with what you would
also put in `AGENTS.md`/`CLAUDE.md`, and that `skills/project-memory/SKILL.md` restates much
of the same procedure. That is deliberate, and worth understanding before you "fix" it.

**The two layers load at different times.** The rules files load at wake-up, every session,
unconditionally. The skill loads only when it triggers. An agent that never trips the skill
still gets the rails — that redundancy *is* the safety net. Delete the overlap and you have
a system that behaves correctly only when the skill happens to fire.

**What each layer owns**, if you want to trim rather than delete:

- **Rules files** — the non-negotiables, stated once and briefly. Things whose violation is
  expensive: git safety, secrets, verify-before-asserting.
- **The skill** — *procedure*. The ordered steps, the edge cases, the commands. Detail here
  is cheap because it is only paid when the skill runs.

If you cut, cut *detail from the rules files* and let the skill own it — not the other way
round. Guidance from Anthropic on newer models points the same direction: keep always-loaded
context brief, push detail into on-demand skills.

## Releases and versioning

Tagged releases with a [`CHANGELOG`](CHANGELOG.md), so you can diff between versions rather
than against a moving `main`. Versions are `MAJOR.MINOR.PATCH` — MAJOR means your vault needs
a change to stay compatible; MINOR and PATCH are safe to take.

Pin to a tag if you have customised heavily. Track `main` if you want fixes as they land —
and read the CHANGELOG's *reasoning*, not just its entries: most changes here come from a
trap that cost someone real time, and whether it applies to you depends on your setup.

## Requirements

Python 3.8+, git, and Claude Code (for the hooks and skill; the vault and policies are
plain markdown and need nothing).

Cross-platform. **No bash required** — every script is Python specifically so Windows
users do not need git-bash, and so no path ever has to cross a shell/Python boundary.

## Licence

MIT. See [`LICENSE`](LICENSE).

The kit bundles no third-party code. One adjacent tool is *pointed at* rather than
included, with its own authors and licence noted in [`tools/README.md`](tools/README.md) —
read that before redistributing anything from this repo alongside it.

## Provenance and honesty

This is extracted from a working setup, not designed in the abstract. Every rule with a
war story attached actually happened; the incidents are kept inline **with what went
wrong**, because a rule written from what you intend is prose, and a rule written from
what broke survives contact with the next reader.

Some of the discipline here — trigger-based notes, the anti-capture list, the destination
ladder, bidirectional supersession, evidence-first session close — was adapted from a
learning-loop package shared privately by a friend, which was better on all of those
points than what it replaced. That package layered a learning loop over a local vector
store. **This kit keeps the discipline and drops the store**, because markdown is
inspectable, greppable, diffable, and readable by more than one agent at a time. If you
want semantic retrieval, add it over the top — scope it to retrieval, never storage.

**What this kit has not been tested for:** multiple users, non-Windows hosts beyond
incidental use, and vaults past a few hundred notes. Lexical retrieval plus aliases and
search anchors has been competitive so far; at some scale it will not be.

---
title: Multi-Agent Handoff
aliases:
  - how agents avoid clobbering each other
  - work log convention
  - who did what
  - agent attribution
status: active
created: 2026-07-27
updated: 2026-08-06
privacy: working
applies_when: >
  Starting or finishing work on a project that more than one agent touches, or
  trying to work out who changed something and when.
verify: >
  git -C "<repo>" worktree list && git -C "<repo>" branch -a
---

# Multi-Agent Handoff

The vault covers *what is known*. This covers *how multiple agents avoid standing on
each other*. Skip this file entirely if only one agent works in your setup.

Nearly all of this was in practice before it was written down, which is the normal
order — the useful version of this policy is the one you write after the first
collision, not before.

## One handoff mechanism, fed from both ends

A per-project `WORK-LOG.md`, newest first, with the project's agent-orientation file
instructing every agent to **read it before touching anything**. That is the whole
mechanism and it works.

**Read before starting, append before finishing.** The common failure is
one-directional: an agent reads the vault and ignores the work log, or writes the log
and never reads it. Either way the handoff silently stops working while looking fine.

Two cautions:

- **Do not add a work log to every project by default.** An unused log is worse than
  none, because it looks authoritative while going stale.
- **Do not run two handoff mechanisms.** A work log *and* a continuity-note system
  means two places to look and guaranteed drift, and then neither gets trusted. Pick
  one per project.

## Attribution: never trust commit metadata

**Git authorship usually cannot distinguish agents.** Agents typically commit under the
human's configured name and email, so `git log --format=%an` tells you nothing about
which agent — or whether it was an agent at all. Repos that span years often carry
several of the human's own historical identities too, which makes the metadata look
more informative than it is.

Attribution comes from:

- **Branch prefix.** Give each agent one: `codex/*`, `claude/*`.
- **Worktree path.** Agent tooling that uses worktrees puts them in predictable places.
- **The vault.** Journal entries and project notes carry a `source:` field. That is the
  reliable record of who did what.

Where a worktree's directory name disagrees with its branch, **trust the branch.**

## Worktrees are invisible to a directory scan

Agent tooling routinely puts worktrees entirely outside the project tree. Any tooling
that scans folders will miss them and report a misleadingly simple picture — usually
"this repo is idle", about a repo that is not.

**Always `git worktree list`.** The session-start sweep in this kit does it and records
the result.

## Never resolve another agent's divergence

`git pull --rebase` on a rejected push is fine and expected. **Never reset, force-push,
or delete another agent's branch, worktree, or stash.** Surface it to the human.

The asymmetry is deliberate: cleaning up after another agent looks tidy and occasionally
destroys work that agent was mid-way through, and neither agent will be able to tell you
what was lost.

## Boundaries are per-agent and worth writing down

If one agent has narrower access than another — recall-only, or read-only outside a
granted path — state it explicitly in the vault and in that agent's orientation file.
An unstated boundary is not a boundary.

Likewise: **keep one agent's persona or runtime memory out of shared project memory.**
They are different kinds of thing and mixing them makes both less trustworthy.

## Orientation files are per-agent, and they drift

`AGENTS.md` addresses one tool, `CLAUDE.md` another. Kept as two full copies, they
diverge: one project here reached 199 lines of guidance for one agent with no
equivalent for the other — including a rule about material that must never be
published. That gap was closed by hand, and hand-mirroring is why it opened.

**The structural fix: one canonical file, imported by the other.** Make `AGENTS.md`
the canonical, agent-neutral orientation file — per-agent rules go in labelled
sections at the bottom — and reduce `CLAUDE.md` to an import line plus whatever is
genuinely Claude-specific. Claude Code expands a line that is just an `@`-prefixed
path into that file's contents at load time, so the import is mechanical, not an
instruction the model has to choose to follow. The direction is forced: tools
without an import mechanism read `AGENTS.md` natively, so the neutral file must be
the canonical one.

If a tool in your setup supports neither `AGENTS.md` nor imports, the old rule is
the fallback — **when a durable project rule changes, update both files** — and the
drift above is what that costs when it slips.

## Search Anchors

- how do two agents avoid clobbering each other
- what is the work log convention
- how do I tell which agent made a change
- where do agent worktrees live
- can I clean up another agent's branch

---
title: Memory Write Guards
aliases:
  - what should I never store
  - what not to capture as a lesson
  - can I write down that a tool is broken
status: active
created: 2026-07-27
updated: 2026-07-27
privacy: private
applies_when: >
  About to write anything into the vault, or about to record a "lesson" from
  something that just went wrong.
---

# Memory Write Guards

Two halves: what never goes in, and what looks like a lesson but poisons the store.

## Never store

- API keys, bot tokens, passwords, auth headers, session cookies, private
  credentials, raw `.env` values. Not in a journal entry, not in an inbox fragment,
  not temporarily.
- Personal, financial, legal, medical, or relationship information about anyone,
  without being asked. Default no. **Keep a private location outside the vault for
  this and keep it out of every index, sync, and agent read path.**
- Brainstorming presented as settled strategy. That goes to `20_Inbox` and only gets
  promoted once a human confirms it is load-bearing.

**A public verification token is not a credential.** Some values look like keys and are
meant to be world-readable — a search-engine domain-verification file, for instance,
whose entire mechanism is being published. Redacting one protects nothing and breaks the
next agent's ability to check the setup.

The test is **not** whether it looks random. It is: *does the value grant access, or
does it only prove ownership of something already public?* If publishing it is the
mechanism, it is not a secret. If in doubt treat it as a secret and ask — but do not
reflexively flag anything hex-shaped, or the guard gets ignored through noise.

## What NOT to capture

Some things look like lessons and become self-imposed constraints that bite later when
the environment changes.

> **Capture the fix, never the failure.**

- **Never record a negative capability claim.** "X is broken", "that tool does not
  work", "we cannot do Y". These harden into refusals that get cited back months after
  the underlying problem was fixed. **Writing one down manufactures a future false
  refusal.** If a tool failed, record the *working* command or the setup step, not the
  verdict.
- **Never record environment-dependent failures** as durable facts: a missing binary,
  unconfigured credentials, an uninstalled package, a path that did not exist yet. That
  is setup state, and setup state changes. A directory not existing meant it was
  *unused*, not *unusable* — and treating the absence as a limit cost a working
  afternoon here.
- **Never record transient errors that resolved.** If a retry worked, the lesson is the
  retry, not the original error.
- **Never record one-off task narratives.** "Summarised today's numbers." A single task
  is not a class of work.
- **Never record live state without a `verify:` command.** See `schema.md`.

## Before recording that something is missing

An absence is a claim about the entire search space. Follow
[`verification-discipline.md`](../../10_Rules/verification-discipline.md): name the
space searched, name a place you did not search, search it, *then* report.

## Tags are a leaky proxy

Do not let a tag decide whether something is durable, portable, or shareable. **Read the
body.** A note tagged `workflow` can be entirely machine-specific, and a note tagged
with one project can hold a universal principle.

## Bulk-generated content carries a batch id

Anything written in bulk — an import, a migration, a generated set — gets a marker
identifying the batch, so the whole operation is **reversible with one query** instead
of being unpickable from hand-authored notes.

This matters most for any automated writer. Its output must be distinguishable from
human writing *after the fact*, or the first bad batch is permanent. And treat ambiguous
provenance as hand-authored, so the failure mode defaults to inaction.

## Search Anchors

- what should I never store in the vault
- can I write down that a tool is broken
- what not to capture as a lesson
- how do I record bulk-generated notes
- is that random-looking string actually a secret

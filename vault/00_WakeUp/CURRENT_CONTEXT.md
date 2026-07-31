---
title: Current Context
aliases: [host context, source of truth paths]
status: active
created: 2026-07-27
updated: 2026-07-27
privacy: working
---

# Current Context

Host context and source-of-truth paths. Read at session start.

## Paths
- Vault root:
- Projects root:
- Anything else an agent needs the location of:

## Environment
- OS / shell:
- Language runtimes that matter:

## What deliberately is NOT in this file

**Live git state.** No branch names, no dirty-file counts, no "current high-risk repos"
list. That section existed in the vault this kit came from, rotted quietly, and was
wrong on two of three repos when it was finally checked -- by which point an agent
reading it would have branched defensively around a clean repo while treating 177
uncommitted files as "no commits yet".

Volatile facts are computed by `hooks/git-sweep.py` at session start. If you want to
know the state of a repo, run the check. Do not read it from a note.

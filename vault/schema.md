---
title: Vault Schema
aliases:
  - frontmatter contract
  - what fields does a note need
  - when do I need a verify command
status: active
created: 2026-07-27
updated: 2026-07-27
privacy: private
---

# Vault Schema

How notes in this vault are shaped. Two fields here (`applies_when` and `verify`) do
most of the work; the rest is bookkeeping.

## Frontmatter

```yaml
---
title:                                       # required
aliases:                                     # optional list, improves retrieval a lot
tags:                                        # optional list
status: draft | active | archived | superseded
project:                                     # required when the note is about one project
created: YYYY-MM-DD                          # required
updated: YYYY-MM-DD                          # required, bump on meaningful change
source: human | agent | claude | codex | audit | research
confidence: low | medium | high              # mark uncertain claims low
privacy: private | working | public          # required
applies_when:                                # optional; the trigger, not the topic
verify:                                      # REQUIRED if the note asserts anything volatile
---
```

**Required**: `title`, `created`, `updated`, `privacy`. Everything else is recommended,
except `verify:`, which is required whenever the note states a fact that can change.

Validate with `python scripts/lint_frontmatter.py <note>` before saving.

**Folder `README.md` files are signposts, not notes.** They carry no frontmatter and are
excluded from linting. Everything else in the vault is a note and should pass.

## `applies_when:` — write triggers, not topics

**This is the highest-leverage field in the schema.**

A note organised by topic has to be remembered before it can help. A note that states
its own trigger announces itself.

```yaml
applies_when: >
  About to edit a file in a repo that tracks a remote.
```

Prefer a specific condition over a subject label. "Before any deploy to production"
beats "deployment notes". Where a rule has an exception, say so in the body under a
**DO NOT APPLY WHEN** line — the boundary is the part that gets forgotten, and a rule
applied outside its boundary is how a helpful note becomes a false constraint.

## `verify:` — volatile facts carry their own recheck

**Live state does not belong in a note.** Branch names, dirty file counts, install
status, versions, "the current problem repos" — all of it rots, and a stale fact that
looks authoritative is worse than no fact, because an agent will act on it.

The vault this kit came from carried a "current high-risk git state" block for eleven
weeks. When finally checked it was wrong on two of three repos: a clean repo described
as dirty on a branch it had left, and a repo with 177 uncommitted files described as
having none.

So:

- If a fact can change, either **leave it out** and record how to check it, or record it
  **with a `verify:` command and a date**.
- **If you cannot write a cheap command that rechecks the claim, that is a strong signal
  the claim does not belong in a durable note.** This test is mechanical, which is why it
  works — you do not have to judge whether something is durable, you try to write the
  one-liner, fail, and delete the note.
- Prefer a hook that computes the fact fresh over a human bumping a date.

```yaml
verify: git -C "<repo>" status -sb && git -C "<repo>" remote -v
```

## Supersession is marked on BOTH notes

When a note replaces an older one, update **both** in the same pass:

1. The new note records what it supersedes.
2. The **old** note gets `status: superseded` plus a line at the top pointing at the
   replacement, and is retained for history.

One-directional marking is not enough. **A stale note that still reads as current will
outrank its own replacement in search and hand back a confidently wrong answer, with
nothing signalling the staleness.** The rationale is written here rather than left
implicit because otherwise this gets dropped as pedantry.

**The `updated:` field is load-bearing.** Bump it whenever the body materially changes.
A drifted `updated:` makes a current note look stale to retrieval and to other agents.

## Retrieval

If you are not running embeddings, retrieval is lexical, and `aliases` plus a
**Search Anchors** section at the foot of each note are what make it work. Write the
anchors as natural-language questions someone would actually ask:

```markdown
## Search Anchors
- why did we choose Postgres over SQLite
- is it safe to delete the staging bucket
```

**When retrieval feels weak, add anchors before you change anything else.** In practice
that has been competitive with semantic search, and it costs no infrastructure.

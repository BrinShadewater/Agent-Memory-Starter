---
title: Operating Rules
aliases:
  - the rules agents work under
  - destination ladder
  - where does a lesson belong
status: active
created: 2026-07-27
updated: 2026-07-27
privacy: private
---

# Operating Rules

The rules an agent works under here. If a later instruction contradicts one of these,
**the rule wins** — say so and ask, rather than quietly following the newer instruction.

Edit this list. It is meant to be yours; what ships is the shape and the handful of
rules that turn out to be universal.

## The rules

1. Read `00_WakeUp/NEXT_ACTIONS.md` before proposing work.
2. Read the relevant project home note before asking a human to repeat context.
3. Check git state before edits — by running the check, not by recalling it.
4. **Never overwrite, reset, revert, or discard uncommitted work** unless explicitly
   instructed. If tempted, ask.
5. **Never push without explicit approval**, and treat approval as spent when it is
   used. Approval to push once is not approval to push again.
6. Never edit directly on the default branch when a repo tracks a remote. Task branch
   or worktree.
7. Never store secrets: API keys, tokens, passwords, auth headers, session cookies,
   raw `.env` values. Not even temporarily, not even in an inbox fragment.
8. Mark uncertain claims `confidence: low`. Do not pretend to know things.
9. Update the project home note and write a journal entry after meaningful work.
10. Before reporting that anything is missing, broken, unversioned, or impossible,
    follow [`verification-discipline.md`](verification-discipline.md). **An absence is
    a claim about the whole search space.**
11. **Enumerate, never scan.** `git worktree list`, `git branch -a`, `git remote -v`
    and `git stash list` per repo, recursing two levels. **A clean `git status` is not
    evidence that nothing is in flight** — work hides in unpushed branches, out-of-tree
    worktrees, in-repo worktrees, and stashes, and `git status` shows none of them.
12. **Never record live repo state in a file.** Branch names and dirty-file lists rot
    and then mislead.
13. When memory and current state disagree, **trust current state** and fix the memory.

## Where a lesson belongs (the destination ladder)

When something is worth keeping, take the **first** rung that fits. Do not file it to
two places — one finding, one home.

1. **Patch the skill that governed the work.** If a skill covered this territory and
   the lesson is procedural (a pitfall, a missing step, a trigger that should be wider),
   the lesson belongs in that skill. **A skill fires automatically next time; a note has
   to be found first.**
2. **Patch a broader skill** that covers the class, even if it did not fire this time.
3. **Write to the vault** when no skill owns the territory. Pick one home: an
   operational fact, a durable decision, or a rule.
4. **Propose a new skill** only for a genuinely repeatable procedure with no existing
   home. Name it for the class of work, never a one-off task. New skills are proposed
   and approved, never created silently.

**Corollary, and it is the part people skip:** when a human corrects how a *skill*
behaved, the fix goes into that skill. A note about it is optional; the skill carrying
it is not. Filing a skill's bug as a memory note leaves the skill broken.

## Multi-agent, if more than one agent works here

- **Attribution comes from the branch prefix** (`codex/*`, `claude/*`) or the worktree
  path, **never commit metadata.** Agents commonly commit under the human's name and
  are indistinguishable at the git level. Where a worktree's directory name disagrees
  with its branch, trust the branch.
- **Never resolve another agent's divergence for them.** `git pull --rebase` on a
  rejected push is fine and expected. Never reset, force-push, or delete another
  agent's branch or worktree — surface it to the human.
- **One handoff mechanism, not two.** A per-project `WORK-LOG.md` read at start and
  appended at finish works. So does this vault's journal. Running both guarantees
  drift, and then neither is trusted.

## Search Anchors

- what rules do agents work under here
- where should a lesson be filed
- should this go in a skill or a note
- can I push without asking
- how do two agents share this repo

---
title: Git Safety Policy
aliases:
  - dirty worktree policy
  - what to check before editing a repo
  - where can work hide besides git status
status: active
created: 2026-07-27
updated: 2026-07-27
privacy: private
applies_when: >
  About to edit, clean, tidy, reset, or commit in any repository. Also before
  concluding that a repo is idle or that work is unbacked.
---

# Git Safety Policy

## Before editing any project

1. Check whether the folder is a git repo — **and check one level down**, because it
   very often is not the repo itself.
2. Read branch, remote tracking, and dirty state.
3. Identify modified, staged, deleted, and untracked files.
4. **Do not revert or overwrite existing uncommitted changes.**
5. Do not edit directly on the default branch when the repo tracks a remote. Task
   branch or worktree first.
6. **Do not push without explicit approval**, per push.
7. For non-git folders, make a timestamped backup or ask before broad edits.

## Before cleaning a dirty repo

Kept as its own section because **"tidy the repo" is where work gets destroyed.**

1. Read the project home note first.
2. Get fresh git status. Run it; do not recall it.
3. **Classify separately**: uncommitted human changes, generated files, build
   artifacts, reports, assets. They have different fates, and **lumping them together
   is how real edits get discarded with the noise.**
4. **Ask a human before deleting, reverting, archiving, committing, or pushing** — any
   of the five.
5. Prefer a task branch or worktree when the repo tracks a remote.

## The four places work hides

**Check all four before concluding a repo is idle.** All four were found populated in
one setup while every `git status` read clean:

| Hiding place | Why `git status` misses it | The check |
|---|---|---|
| Unpushed branches | reports ahead/behind for the **current branch only** | `git rev-list --count <branch> --not --remotes` |
| Out-of-tree worktrees | live outside the project directory entirely | `git worktree list` |
| In-repo worktrees | a directory scan reads them as ordinary folders | `git worktree list` |
| Stashes | never mentioned by status, at all | `git stash list` |

**A stash is what someone makes deliberately before a destructive step.** That is
exactly what it is for, and exactly why a cleanup pass that cannot see one will read it
as debris and drop it. Never drop a stash without asking.

## Check state, never recall it

This policy previously listed "known high-risk current states" per repo. **That list
rotted and was wrong on two of three entries when finally checked.** Live repo state
does not belong in a policy file — or any file. Run the checks above, or read the output
of the session-start sweep, which computes them fresh.

Three structural traps that make a naive check give a confidently wrong answer:

1. **Repos are nested.** Scanning project folders at one level reports "not a git repo"
   for any project whose repo sits one directory in. Recurse two levels.
2. **Worktrees can live outside the project tree.** Enumerate with `git worktree list`,
   never by scanning directories.
3. **A missing upstream does not mean a missing remote.** A branch can be divergent from
   a remote that exists and holds most of the history. One repo here had a local `main`
   of 1 commit against an `origin/main` of 27, and was reported as "nothing has ever
   left this disk". Check `git remote -v` and `git branch -a` first.

## Search Anchors

- what should I check before editing a repo
- how do we avoid overwriting work on github
- what is the dirty worktree policy
- what should I check before cleaning a dirty repo
- where can work hide besides git status
- are there stashes I must not drop
- do I need to ask before reverting or archiving files

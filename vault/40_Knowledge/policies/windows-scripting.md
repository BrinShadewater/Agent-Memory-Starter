---
title: Windows Scripting Traps
aliases:
  - cp1252 encoding trap
  - zero byte output file
  - robocopy retry hang
  - powershell exit code bitmask
status: active
created: 2026-07-27
updated: 2026-07-28
privacy: working
applies_when: >
  Writing or modifying any script that will run on Windows: PowerShell, Python,
  batch, or a scheduled task. Also when a script "succeeded" but produced
  nothing, or hung.
verify: >
  Run it once end to end and check its output artifact is non-empty and its exit
  code is what the scheduler will see.
---

# Windows Scripting Traps

Traps that produce **silent** failures: the script reports success, and the output is
empty, truncated, or never arrives. Relevant to any package that expects Windows users.

## The console is cp1252, and that turns success into a 0-byte file

Printing a character that **cp1252 cannot represent** raises `UnicodeEncodeError`. If
stdout was being redirected to a file, the result is **a zero-byte file that looks like a
successful empty result.** Not an error. An empty answer that reads as "nothing found".

**Know which characters actually fail**, because the obvious guess is wrong:

| Survives cp1252 | Actually fails |
|---|---|
| em dash `—`, en dash `–` | arrows `→` |
| curly quotes `’ “ ”` | checkmark `✓`, cross `✗` |
| ellipsis `…`, bullet `•` | warning `⚠` |
| | every emoji |

cp1252 is latin-1 **plus** the smart-punctuation block at 0x80–0x9F, which is exactly where
em dashes and curly quotes live. Typographic punctuation is safe; symbols and emoji are not.

This distinction matters more than it looks. **An overstated rule gets disbelieved.**
Someone tests "non-ASCII breaks output" with an em dash, watches it work fine, writes the
rule off as folklore — and then ships a `✓` in a status line that dies silently under
redirection.

That shape is especially bad for a memory system, where "nothing found" is a legitimate
result. A query returning empty becomes indistinguishable from a query that died on a smart
quote in a pasted lesson.

- **Write a UTF-8 file directly** from the script. Do not build an output artifact by
  redirecting stdout.
- **Print ASCII only**, and keep printed output to a short status line or a count.
- When reading, open with an explicit `encoding="utf-8"`.

## MSYS path conversion breaks paths in BOTH directions

`/c/Users/...` must be converted to `C:\Users\...` before it crosses from a shell script
into Python. Any package that hands paths from bash hooks into Python helpers will hit this.

**And the mirror image, which is nastier because it exits 0.** A *Linux* path passed
through git-bash to WSL gets rewritten into a Windows path:

```
wsl -d Ubuntu -- /home/me/.local/bin/mytool update
  -> /bin/bash: C:/Program Files/Git/home/me/.local/bin/mytool: No such file or directory
```

The command fails, and **the pipeline still reports success**, so anything checking the
exit code concludes the job ran. Run WSL commands from PowerShell rather than git-bash, or
set `MSYS_NO_PATHCONV=1` for the call — and verify the artifact either way.

## Unquoted variables split on spaces in paths

A bash loop over paths containing a space (`My Documents`, `Program Files`) will split
each path into fragments unless the variable is quoted:

```bash
for f in $(find "$DIR" -name '*.md'); do check $f;   done   # WRONG
for f in $(find "$DIR" -name '*.md'); do check "$f"; done   # right
```

Unquoted, every check fails on a fragment that is not a real file — which reads as a
catastrophic result rather than a broken test. This produced a "0 of 152 files pass" lint
result against a directory that was entirely clean.

The broader point: if the only reason a package requires git-bash is a handful of shell
scripts that check mtimes, iterate directories, run `git` and print — port them to the
Python you already require. It removes a prerequisite, removes the "open it from git-bash,
not PowerShell" install step, and removes this whole class of bug. **On Windows that install
step is the one most likely to be got wrong, and getting it wrong produces a system that
appears installed and does nothing.**

## Robocopy retries forever by default

The default is **one million retries at 30 seconds each**. A single locked file blocks the
run indefinitely, and a scheduled job simply never finishes.

- Always pass `/R:2 /W:5`. A backup that skips one locked file beats one that never ends.
- Always pass `/NFL /NDL /NP` unless you want tens of thousands of lines burying the
  summary.
- Exclude scratch that holds live locks: `tmp`, `__pycache__`, `.venv`, `node_modules`,
  `dist`, plus any per-tool worktree or cache directory.
- Observed: a leftover browser test profile holding a `Cookies` file locked hung a backup in
  a retry loop for hours.

## Robocopy exit codes are a bitmask, not a status

Codes under 8 are success: `0` nothing copied, `1` files copied, `2` extras, `4` mismatches.
Only `8+` means a file genuinely failed.

**This leaks.** A PowerShell script that ends after a robocopy call inherits
`$LASTEXITCODE`, so a perfectly healthy run exits `1` and Task Scheduler records a failure.
End such scripts with an explicit `exit 0`, or exit non-zero only on a real verification
failure, so a red task means something actually went wrong.

## Paths with spaces

Always quote. Two consequences that have bitten:

- **`diff -rq` quotes only paths containing spaces**, so a filter matching the quoted form
  silently skips every folder without one. Match both forms.
- Zip archives written by some Windows tooling use **backslash path separators**, which is
  outside the ZIP spec. Windows extracts them fine; on Linux or macOS the entries become
  literal filenames containing backslashes rather than a directory tree. **A backup that
  only restores on the machine that made it is a weaker backup than it appears.**

## Moving directories can fail while a handle is open

`mv` in git-bash returns "Device or resource busy" when anything holds a file in the tree,
including background indexers. PowerShell `Move-Item` often succeeds where it fails;
`robocopy /MOVE` is the fallback. Verify the destination and the emptied source afterwards.

## Scheduled tasks and per-user config

A task running as one user cannot find another user's config. Verify the account a scheduled
task runs under whenever it depends on per-user configuration — otherwise it fails silently,
every night, in a way nothing reports.

## Search Anchors

- why did my script produce an empty file
- do em dashes break windows output
- which characters actually fail on a cp1252 console
- why does wsl fail from git bash
- why did my loop report every file as broken
- robocopy hangs on a locked file
- why does the scheduled task show as failed when it worked
- how do I verify a backup actually worked

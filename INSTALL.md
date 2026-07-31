# Install

Roughly ten minutes. Nothing here is destructive, and every step is reversible.

## 0. Requirements

- Python 3.8+ on `PATH`
- git
- Claude Code (for hooks and the skill; the vault itself is plain markdown)

No bash. No git-bash on Windows. Every script here is Python on purpose.

## 1. Put the vault somewhere

```bash
cp -r vault ~/memory-vault          # or anywhere you like
```

Then set the environment variable so the scripts can find it:

```bash
# macOS / Linux — add to your shell profile
export AGENT_VAULT="$HOME/memory-vault"
export AGENT_PROJECTS="$HOME/code"      # the root the git sweep will scan
```

```powershell
# Windows PowerShell — persists across sessions
[Environment]::SetEnvironmentVariable("AGENT_VAULT", "$HOME\memory-vault", "User")
[Environment]::SetEnvironmentVariable("AGENT_PROJECTS", "$HOME\code", "User")
```

**`AGENT_PROJECTS` is not optional if you want the git sweep to do anything.** Unset, it
exits silently — deliberately, since an unconfigured hook should be inert rather than
noisy, but it does mean a silent no-op is the default failure.

## 2. Install the hooks

```bash
python hooks/install-hooks.py
```

Dry run. It prints every file it would copy and every registration it would add, and
writes nothing. Read that output before continuing.

```bash
python hooks/install-hooks.py --apply
```

What it does, and what it refuses to do:

- **Backs up `~/.claude/settings.json` first**, to `settings.json.pre-kit-<timestamp>`.
  Nothing is touched before the copy exists.
- **Merges additively.** It will not replace a hooks block you did not author.
- **Dedupes by script basename**, so re-running is safe and does not stack duplicates.
- **Refuses to wire a script that is not on disk.** A registered path that does not exist
  is a hook that fails silently every session.
- **Refuses to write if `settings.json` is not valid JSON.** Fix it yourself first; an
  installer that overwrites a file it cannot parse is worse than no installer.

## 3. Install the skill

```bash
cp -r skills/project-memory ~/.claude/skills/
```

Edit its `description:` frontmatter — the `TRIGGER` clause should name **your** projects
and the phrases **you** actually use. A skill that does not trigger is not installed in
any meaningful sense.

## 4. Start a fresh session

**Required, not optional.** A running session's hooks and skill list are fixed at start.
No amount of re-checking inside this session will show the change.

## 5. Verify — registration is not evidence

Check the artifact, not the exit code:

```bash
cat ~/.claude/hook_state/git-sweep.json      # should exist, with your repos in it
```

- **File missing?** `AGENT_PROJECTS` is unset, or you have not started a fresh session.
- **File present but `repos` is empty?** `AGENT_PROJECTS` points somewhere with no repos
  within two levels.
- **Nothing printed at session start?** Correct, if everything is healthy. The sweep is
  silent by design and only speaks when something is structurally odd. To prove it works,
  point it at a folder containing a repo with no remote.

Then, to check the skill:

```
"wake up"
```

It should read `NEXT_ACTIONS.md` and orient rather than asking you what to do.

## 6. Fill in the vault

The kit ships empty. Start here, in order:

1. `00_WakeUp/CURRENT_CONTEXT.md` — your paths and host context
2. `00_WakeUp/NEXT_ACTIONS.md` — what is actually outstanding
3. `10_Rules/operating-rules.md` — **edit these; they are meant to be yours**
4. One project home note from `templates/project-home.md`

**Expect nothing visible for the first few weeks.** A capture system produces no value
until it has captured something, and the decisions folder in particular stays empty for
a while. That is the intended cold start, not a fault.

## Uninstall

```bash
cp ~/.claude/settings.json.pre-kit-<timestamp> ~/.claude/settings.json
rm ~/.claude/hooks/{git-sweep,post-compact-reorient,log-skill-usage}.py
rm -rf ~/.claude/skills/project-memory
```

The vault is just markdown files. Keep or delete them; nothing else depends on them.

## Pausing without uninstalling

```bash
touch ~/.claude/automation.paused      # stops all three hooks
rm ~/.claude/automation.paused         # resumes
```

Per-hook: `automation-gitsweep.paused`, `automation-reorient.paused`,
`automation-telemetry.paused`.

Set `CLAUDE_HOOKS_SKIP=1` before launching any nested or headless agent run, or a hook's
output gets captured as that subprocess's answer.

## Troubleshooting

**A hook seems to do nothing.** Hooks here always exit 0 and swallow exceptions on
purpose — a broken hook must never block a session. To see actual errors, run it by hand:

```bash
echo '{}' | python ~/.claude/hooks/git-sweep.py
```

**Windows: a script "succeeded" but produced an empty file.** Read
`vault/40_Knowledge/policies/windows-scripting.md`. The console is cp1252, printing any
non-ASCII character raises `UnicodeEncodeError`, and under redirection that lands as a
zero-byte file that looks like a successful empty result.

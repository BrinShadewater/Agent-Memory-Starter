# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

Use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**), which opens a private channel with the maintainer.

Include what you found, how to reproduce it, and what an attacker could achieve.

## Scope

This kit is markdown plus a handful of local scripts and git hooks. In scope:

- **`scripts/check_export_safe.py` failing to catch something it claims to catch.** This
  is the highest-value report here: people rely on it before publishing a vault derived
  from private notes. A pattern that silently does not match is a real finding.
- **The hooks in `hooks/`.** They run automatically in an agent session and touch git.
  Command injection, path handling, or anything that could execute unintended code is in
  scope.
- **Anything that causes the kit to write outside its own directory**, or to include
  ignored files in an export.

## Known limits, stated plainly

- **The export checker cannot prove the absence of personal detail.** It matches the
  patterns it is given. A new kind of identifier needs a new pattern, and a clean run
  means "the known patterns are absent", never "this is safe to publish".
- **It is not a secret scanner.** It deliberately does not try to be. Use a real one in
  CI if you need that guarantee.

## Your own identifiers

`scripts/identifiers.local.txt` is gitignored and is meant to stay that way. If you have
committed yours by accident, treat it as published: rotate anything sensitive and rewrite
the history rather than deleting the file in a later commit.

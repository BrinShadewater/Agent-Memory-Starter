#!/usr/bin/env python3
"""Refuse to ship personal detail in a kit derived from a private vault.

WHY
---
This kit is de-personalised from a working vault that is dense with things which must not be
published: a real Windows user profile, Discord IDs, private repo names, a person's email.
De-personalising is done by hand, and by-hand is exactly the process that misses one.

The kit also has a downstream consumer now. A leak here is not "fix it in the next commit" —
it is in someone else's clone, and in the GitHub history, immediately.

WHAT IT CHECKS
--------------
Patterns that should never appear in published files. Two classes:

  HARD   shape-based identifiers (emails, absolute home paths, snowflake IDs), plus
         whatever you list in scripts/identifiers.local.txt. Any hit fails the run.
  SOFT   things that are usually fine but occasionally leak context (absolute Windows paths
         that are not the documented placeholder). Reported, does not fail.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not scan for secrets. `memory-write-guards.md` already forbids storing them and the
vault has never held one; adding a half-good secret scanner here would imply a guarantee this
script cannot make. Use a real secret scanner in CI if you want that guarantee.

It also cannot prove the *absence* of personal detail — only the absence of the patterns
listed. A new kind of identifier needs a new pattern. Treat a clean run as "the known leaks
are not present", never as "this is safe to publish".

USAGE
-----
    python scripts/check_export_safe.py            # scan the whole kit
    python scripts/check_export_safe.py --staged   # scan only staged files (pre-commit use)

Exit 0 clean, 1 on any HARD hit, 2 on usage error.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IDENTIFIERS_FILE = ROOT / "scripts" / "identifiers.local.txt"
IDENTIFIERS_EXAMPLE = ROOT / "scripts" / "identifiers.example.txt"

# Shape-based identifiers. These describe a *kind* of thing, so they are safe to ship
# and mean the same thing in anyone's checkout.
# Names a document may legitimately use to *show* a path without naming anyone.
PLACEHOLDER = r"(?:me|you|user|users?name|myusername|youruser|name|USER|<[^>]+>|\.\.\.|%\w+%|\$\w+)"

# Shape-based identifiers: they describe a *kind* of thing, so they are safe to ship and
# mean the same thing in anyone's checkout. Each excludes the placeholder set, so docs can
# still demonstrate a path.
GENERIC_HARD = [
    (r"\b\d{17,19}\b", "possible Discord/Slack snowflake ID"),
    (rf"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net))[A-Za-z0-9.-]+\.[A-Za-z]{{2,}}\b",
     "email address"),
    (rf"[A-Z]:\\+Users\\+(?!{PLACEHOLDER}(?![A-Za-z0-9._-]))[A-Za-z0-9._-]+", "absolute Windows user path"),
    (rf"/mnt/[a-z]/Users/(?!{PLACEHOLDER}(?![A-Za-z0-9._-]))[A-Za-z0-9._-]+", "absolute WSL user path"),
    (rf"/(?:home|Users)/(?!{PLACEHOLDER}(?![A-Za-z0-9._-]))[A-Za-z0-9._-]+/", "absolute home directory path"),
]


def load_local_identifiers():
    """Your own names, handles and directories, from a file git never sees.

    They deliberately do not live in this script. A checker that ships the very strings
    it hunts for publishes them to every reader, and one hardcoded to its author's
    identifiers cannot protect anybody else.

    Format: one regex per line. `#` starts a comment. Blank lines ignored.
    An optional `||` suffix labels the hit: `\bmyuser\b || my username`
    """
    if not IDENTIFIERS_FILE.exists():
        return [], False
    out = []
    for raw in IDENTIFIERS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern, _, label = line.partition("||")
        out.append((pattern.strip(), label.strip() or "personal identifier"))
    return out, True

# Contextual. Reported, not fatal.
SOFT = [
    (r"[A-Z]:\\+Users\\+(?!<)", "absolute Windows user path (use a placeholder)"),
]

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}
SKIP_FILES = {
    "CHANGELOG.md",              # may legitimately describe the source project's history
    "identifiers.local.txt",     # lists your identifiers by design, and is gitignored
    "identifiers.example.txt",   # ships placeholder examples of the same
}
TEXT_SUFFIXES = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".toml", ".cfg", ".sh", ".ps1"}


def candidate_files(staged_only: bool):
    if staged_only:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=ROOT, capture_output=True, text=True,
        )
        for line in out.stdout.splitlines():
            p = ROOT / line.strip()
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and p.name not in SKIP_FILES:
                yield p
        return
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if set(p.parts) & SKIP_DIRS or p.name in SKIP_FILES:
            continue
        if p.name == Path(__file__).name:      # this file lists the patterns by design
            continue
        yield p


def scan(path: Path, patterns):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        for pattern, why in patterns:
            m = re.search(pattern, line)
            if m:
                yield lineno, m.group(0), why, line.strip()[:100]


def main(argv):
    ap = argparse.ArgumentParser(description="Check the kit for personal detail before publishing.")
    ap.add_argument("--staged", action="store_true", help="scan only staged files")
    args = ap.parse_args(argv)

    local_patterns, have_local = load_local_identifiers()
    hard = GENERIC_HARD + local_patterns

    files = list(candidate_files(args.staged))
    if not files:
        print("No files to scan." if args.staged else "error: no text files found", file=sys.stderr)
        return 0 if args.staged else 2

    hard_hits, soft_hits = [], []
    for f in files:
        rel = f.relative_to(ROOT)
        for lineno, found, why, ctx in scan(f, hard):
            hard_hits.append((rel, lineno, found, why, ctx))
        for lineno, found, why, ctx in scan(f, SOFT):
            soft_hits.append((rel, lineno, found, why, ctx))

    for rel, lineno, found, why, ctx in hard_hits:
        print(f"BLOCK  {rel}:{lineno}: {why} -- {found!r}")
        print(f"       {ctx}")
    for rel, lineno, found, why, ctx in soft_hits:
        print(f"WARN   {rel}:{lineno}: {why} -- {found!r}")

    print("")
    print(f"{len(files)} file(s) scanned, {len(hard_hits)} blocking, {len(soft_hits)} warning.")
    if hard_hits:
        print("Personal detail found. Do not publish until these are removed.")
        return 1
    if not have_local:
        print(f"NOTE   no {IDENTIFIERS_FILE.name} found, so only shape-based patterns ran.")
        print(f"       Copy {IDENTIFIERS_EXAMPLE.name} to {IDENTIFIERS_FILE.name} and add your")
        print("       own username, handles and home directory. Without it this check is weaker.")
    print("No known personal-detail patterns present. This is not proof of safety -- "
          "a new kind of identifier needs a new pattern.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""
lint_frontmatter.py  -  validate YAML frontmatter on vault notes.

Usage:
    python lint_frontmatter.py <path-to-note.md>
    python lint_frontmatter.py <path-to-note.md> --strict   # treat warnings as errors

Checks:
- Frontmatter block present (between two --- delimiters at top of file)
- Required fields: title, created, updated, privacy
- 'project' required when filename or path suggests a project-specific note
- Dates in YYYY-MM-DD format
- updated >= created
- updated not in future relative to today (within reason)
- status in {draft, active, archived, superseded} if present
- privacy in {private, working, public}
- source in {human, agent, claude, codex, audit, research} if present
- confidence in {low, medium, high} if present

Warnings (don't fail the lint by default):
- Missing aliases on durable notes
- Missing source on audits/journal entries
- No "## Search Anchors" section in body of durable note

Exit codes:
    0  pass (no errors)
    1  fail (one or more errors)
    2  argument error
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED = {"title", "created", "updated", "privacy"}
STATUS_ENUM = {"draft", "active", "archived", "superseded", "needs-review", "verified",
               "reviewed", "abandoned"}
# "ops" is emitted by the shared memory-writeback tooling for operational notes
# shared across agents; documented in 60_Agents/Claude.md. It was missing here,
# so five legitimate notes linted as errors.
PRIVACY_ENUM = {"private", "working", "ops", "public"}
SOURCE_ENUM = {"human", "agent", "claude", "codex", "audit", "research"}
CONFIDENCE_ENUM = {"low", "medium", "high"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Minimal YAML frontmatter parser. Handles flat scalar fields and simple list
    fields (- item per line). Doesn't handle nested mappings  -  vault notes
    don't use them.
    """
    if not text.startswith("---\n"):
        raise ValueError("No frontmatter delimiter at top of file")
    end = text.find("\n---\n", 4)
    if end < 0:
        # Try \r\n style or final line
        end = text.find("\n---", 4)
        if end < 0:
            raise ValueError("Unterminated frontmatter block")
    block = text[4:end]
    body = text[end + len("\n---\n"):] if text[end:end + len("\n---\n")] == "\n---\n" else text[end + len("\n---"):]

    data: Dict[str, Any] = {}
    current_key = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        # List continuation (indented or flush)
        if line.startswith("  - ") or line.startswith("- "):
            if current_key is None:
                continue
            value = line.split("- ", 1)[1].strip()
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(value)
            continue
        # key: value or key:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        current_key = key
        if value == "":
            # Empty value  -  may be followed by list items, or may be intentionally null.
            # Initialize as empty list; if no list items follow, it stays [] which is
            # truthy-equivalent to None for our checks.
            data[key] = []
        else:
            data[key] = value
    return data, body


# Files that live in the vault but are NOT notes. They carry no frontmatter by design
# and linting them produces a permanent, meaningless failure.
#
# Why this matters more than it looks: a linter that always reports one failure trains
# whoever runs it to read "1 failure" as the healthy state. The next real failure then
# arrives as "2 failures" and looks like noise. A check with a standing known-bad result
# is a check nobody reads.
#
# CLAUDE.md / AGENTS.md are orientation files addressed to an agent; README.md files are
# folder signposts. Both are prose, deliberately.
NOT_NOTES = {"CLAUDE.md", "AGENTS.md", "README.md"}

# Scaffolds, not notes. A `templates/` folder holds the shapes a real note is copied from, so
# its frontmatter is placeholder by design — bare keys, no title, no dates. Linting them
# reported 5 failures out of 87 the first time this was pointed at a whole vault, every one of
# them noise, which is the standing-known-bad problem described above arriving by a different
# route. Skipped in directory mode only; pass a template explicitly if you need to lint it.
NOT_NOTE_DIRS = {"templates"}


def lint(path: Path, strict: bool = False) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if path.name in NOT_NOTES:
        return errors, warnings

    text = path.read_text(encoding="utf-8")
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        errors.append(f"frontmatter: {e}")
        return errors, warnings

    # Required (with journal exception: `date:` substitutes for created+updated)
    is_journal_entry = (
        path.parent.name == "90_Journal"
        or fm.get("type") in ("journal", "audit", "session-close")
    )
    required = set(REQUIRED)
    if is_journal_entry and isinstance(fm.get("date"), str) and DATE_RE.match(fm["date"]):
        # Treat `date` as both created and updated for journal entries
        fm.setdefault("created", fm["date"])
        fm.setdefault("updated", fm["date"])

    for field in required:
        if field not in fm or fm[field] in (None, "", []):
            errors.append(f"missing required field: {field}")

    # Date format
    today = datetime.date.today()
    for field in ("created", "updated"):
        v = fm.get(field)
        if isinstance(v, str) and not DATE_RE.match(v):
            errors.append(f"{field}: invalid date format (expected YYYY-MM-DD), got {v!r}")

    # updated >= created
    try:
        c = fm.get("created")
        u = fm.get("updated")
        if isinstance(c, str) and isinstance(u, str) and DATE_RE.match(c) and DATE_RE.match(u):
            cd = datetime.date.fromisoformat(c)
            ud = datetime.date.fromisoformat(u)
            if ud < cd:
                errors.append(f"updated ({u}) is older than created ({c})")
            if ud > today + datetime.timedelta(days=1):
                warnings.append(f"updated ({u}) is in the future relative to system clock")
    except Exception:
        pass

    # Enums.
    #
    # Every one of these tests was `fm[key] not in ENUM`, which raises
    # `TypeError: unhashable type: 'list'` the moment a value is a list or dict rather than
    # a scalar. A bare `source:` with nothing after it parses to an empty list and killed the
    # whole run. Checking one note at a time had never exercised it; walking a directory found
    # it immediately.
    #
    # A non-scalar here is a real authoring mistake, so it is reported at the same severity
    # the field would otherwise carry, rather than crashing or being silently skipped.
    def enum_check(key: str, enum: set, severity: List[str], label: str) -> None:
        if key not in fm:
            return
        value = fm[key]
        if value is None or isinstance(value, (list, dict)):
            severity.append(
                f"{key}: expected a single value, got {type(value).__name__} {value!r}"
                " (an empty or list-valued key — check for a bare `key:` with nothing after it)"
            )
            return
        if value not in enum:
            severity.append(f"{key}: {label} {sorted(enum)}, got {value!r}")

    enum_check("status", STATUS_ENUM, warnings, "unexpected value; common values are")
    enum_check("privacy", PRIVACY_ENUM, errors, "must be one of")
    enum_check("source", SOURCE_ENUM, warnings, "unexpected value; common values are")
    enum_check("confidence", CONFIDENCE_ENUM, errors, "must be one of")

    # Project-aware: project home notes and project journals should have `project`
    parent = path.parent.name
    if parent == "Websites" or "project" in fm.get("tags", []) if isinstance(fm.get("tags"), list) else False:
        if "project" not in fm:
            warnings.append("missing recommended field: project (this looks like a project-specific note)")

    # Durable-note hygiene: aliases + search anchors
    is_durable = parent in {"Websites", "policies", "Decisions"} or path.name == "schema.md" or path.name == "index.md"
    if is_durable:
        if "aliases" not in fm or not fm.get("aliases"):
            warnings.append("durable note has no aliases  -  retrieval may suffer; consider adding 2-3 aliases")
        if "## Search Anchors" not in body:
            warnings.append("durable note has no '## Search Anchors' section  -  consider adding for retrieval")

    # source recommended on audits/journals
    if path.parent.name == "90_Journal" or "audit" in (fm.get("tags") or []):
        if "source" not in fm:
            warnings.append("audit/journal note missing 'source' field (recommended)")

    return errors, warnings


def lint_one(path: Path, strict: bool) -> int:
    """Lint a single file and print its verdict. Returns 0 ok, 1 failed."""
    # "not applicable" and "passed" are different results. Printing OK for a file that
    # was never checked is the same defect as a pipeline reporting "no problems found"
    # when it means "the check did not run".
    if path.name in NOT_NOTES:
        print(f"SKIP   {path}: not a note (orientation file or folder signpost)")
        return 0

    errors, warnings = lint(path, strict=strict)

    for e in errors:
        print(f"ERROR  {path}: {e}")
    for w in warnings:
        print(f"WARN   {path}: {w}")

    if not errors and not warnings:
        print(f"OK     {path}")
        return 0
    if errors:
        return 1
    if strict and warnings:
        return 1
    return 0


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Validate vault frontmatter")
    p.add_argument("path", type=Path, help="a .md note, or a directory to walk recursively")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = p.parse_args(argv)

    if not args.path.exists():
        print(f"error: path not found: {args.path}", file=sys.stderr)
        return 2

    # Directory mode. Passing a folder used to print a "not a markdown file" warning and then
    # die with an unhandled PermissionError from read_text() — a traceback where a usage
    # message belonged. Linting a whole tree is also the thing you usually want after a
    # session that touched several notes.
    if args.path.is_dir():
        found = sorted(args.path.rglob("*.md"))
        if not found:
            print(f"error: no .md files under {args.path}", file=sys.stderr)
            return 2

        # Directory mode only: an explicitly-passed template still gets linted.
        notes = [n for n in found if not (set(n.parts) & NOT_NOTE_DIRS)]
        skipped_dirs = len(found) - len(notes)

        failed = 0
        for note in notes:
            failed += lint_one(note, args.strict)

        print("")
        summary = f"{len(notes)} file(s) checked, {failed} failed."
        if skipped_dirs:
            summary += f" {skipped_dirs} skipped as scaffolds ({'/, '.join(sorted(NOT_NOTE_DIRS))}/)."
        print(summary)
        return 1 if failed else 0

    if args.path.suffix.lower() != ".md":
        print(f"error: not a markdown file: {args.path}", file=sys.stderr)
        return 2

    return lint_one(args.path, args.strict)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

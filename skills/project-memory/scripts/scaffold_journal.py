#!/usr/bin/env python3
"""
scaffold_journal.py  -  scaffold a new journal entry in the vault.

Generates the file with correct filename (YYYY-MM-DD-[project-]topic.md) and
pre-populated frontmatter so naming and frontmatter drift can't happen.

Usage:
    python scaffold_journal.py --topic "auth-rewrite-closeout" --project "My Web App" --agent claude
    python scaffold_journal.py --topic "vault-architecture-cleanup" --agent claude   # cross-project
    python scaffold_journal.py --topic "session-close-X" --project "Project" --agent claude --template session-close

Templates:
    journal       (default)   -  minimal journal entry skeleton
    session-close             -  full session-close template
    audit                     -  audit entry skeleton

Outputs the path to the created file on stdout. Exits non-zero if a file with
that filename already exists (refuses to clobber).
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

VAULT_ROOT_ENV = "AGENT_VAULT"
DEFAULT_VAULT = ""   # no default on purpose: set AGENT_VAULT or pass --vault


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s


def journal_template(title: str, date: str, project: str | None, agent: str) -> str:
    fm = [
        "---",
        f"title: {title}",
        f"date: {date}",
    ]
    if project:
        fm.append(f"project: {project}")
    fm.extend([
        f"agent: {agent}",
        "type: journal",
        "tags:",
        "privacy: working",
        "status: draft",
        "---",
        "",
        f"# {title}",
        "",
        "## Summary",
        "",
        "## What Changed",
        "",
        "## Decisions / Durable Context",
        "",
        "## Open Questions",
        "",
        "## Safe Next Actions",
        "",
        "## Search Anchors",
        "",
        "- ",
    ])
    return "\n".join(fm) + "\n"


def session_close_template(title: str, date: str, project: str | None, agent: str) -> str:
    fm = [
        "---",
        f"title: {title}",
        f"date: {date}",
    ]
    if project:
        fm.append(f"project: {project}")
    fm.extend([
        f"agent: {agent}",
        "type: session-close",
        "tags:",
        "  - session",
        "  - closeout",
        "privacy: working",
        "status: draft",
        "sync_status: not-synced",
        "---",
        "",
        f"# {title}",
        "",
        "## Project",
        "",
        f"- Project: {project or 'n/a'}",
        "- Project path: ",
        "- Related project note: ",
        f"- Agent: {agent}",
        f"- Date: {date}",
        "",
        "## What Changed",
        "",
        "- ",
        "",
        "## Files Touched",
        "",
        "- ",
        "",
        "## Git State After Work",
        "",
        "- Branch: ",
        "- Remote tracking: ",
        "- Dirty files: ",
        "- Untracked files: ",
        "- Commit/push status: ",
        "",
        "## Decisions / Durable Context",
        "",
        "- ",
        "",
        "## Open Questions",
        "",
        "- ",
        "",
        "## Safe Next Actions",
        "",
        "- ",
        "",
        "## Memory Updates",
        "",
        "- [ ] Project note updated",
        "- [ ] Journal note created (this file)",
        "- [ ] Retrieval index refreshed, if you run one (verify the index, not the exit code)",
        "",
        "## Search Anchors",
        "",
        "- ",
    ])
    return "\n".join(fm) + "\n"


def audit_template(title: str, date: str, project: str | None, agent: str) -> str:
    fm = [
        "---",
        f"title: {title}",
        f"date: {date}",
    ]
    if project:
        fm.append(f"project: {project}")
    fm.extend([
        f"agent: {agent}",
        "type: audit",
        "tags:",
        "  - audit",
        "privacy: working",
        "status: needs-review",
        "---",
        "",
        f"# {title}",
        "",
        "## Scope",
        "",
        "## Findings",
        "",
        "## Verification",
        "",
        "## Recommendations",
        "",
        "## Safe Next Actions",
        "",
        "## Search Anchors",
        "",
        "- ",
    ])
    return "\n".join(fm) + "\n"


TEMPLATES = {
    "journal": journal_template,
    "session-close": session_close_template,
    "audit": audit_template,
}


def main(argv):
    import os
    p = argparse.ArgumentParser(description="Scaffold a journal entry")
    p.add_argument("--topic", required=True, help="kebab-case topic slug")
    p.add_argument("--project", default=None, help="project name (optional)")
    p.add_argument("--agent", required=True, choices=["claude", "codex", "agent", "human"])
    p.add_argument("--template", default="journal", choices=sorted(TEMPLATES.keys()))
    p.add_argument("--vault", default=os.environ.get(VAULT_ROOT_ENV, DEFAULT_VAULT))
    p.add_argument("--date", default=None, help="override date (default: today)")
    args = p.parse_args(argv)

    date = args.date or datetime.date.today().isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        print(f"error: invalid date format: {date}", file=sys.stderr)
        return 2

    topic_slug = slugify(args.topic)
    project_slug = slugify(args.project) if args.project else None

    if project_slug:
        filename = f"{date}-{project_slug}-{topic_slug}.md"
    else:
        filename = f"{date}-{topic_slug}.md"

    if not args.vault:
        print(f"error: no vault location. Set the {VAULT_ROOT_ENV} environment "
              f"variable to your vault root, or pass --vault <path>.", file=sys.stderr)
        return 2

    journal_dir = Path(args.vault) / "90_Journal"
    if not journal_dir.exists():
        print(f"error: journal dir not found: {journal_dir}", file=sys.stderr)
        return 2

    out_path = journal_dir / filename
    if out_path.exists():
        print(f"error: file already exists, refusing to clobber: {out_path}", file=sys.stderr)
        return 1

    title = args.topic.replace("-", " ").title()
    if args.project:
        title = f"{args.project}  -  {title}"

    content = TEMPLATES[args.template](title, date, args.project, args.agent)
    out_path.write_text(content, encoding="utf-8")

    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

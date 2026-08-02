# CLAUDE.md

**Read [`AGENTS.md`](AGENTS.md).** It is the guide for working on this repo and it
is deliberately short.

This file exists only so Claude Code finds the guidance by the name it looks for.
Keeping the content in one place is the point — this repo argues at length that
duplicated always-loaded context is a cost, and it would be a poor advertisement
for that argument to duplicate its own instructions.

Two things worth having in front of you before any edit:

- **The kit ships empty.** Never commit a real memory, project name, or personal
  detail. This repo has clones, and git history keeps what you delete.
- **Run `python scripts/check_export_safe.py` before publishing anything**, and
  read `AGENTS.md` on why a clean run is not proof of safety.

If you are looking for the memory rules an agent should follow when *using* a
vault — as opposed to developing this kit — those are in `vault/10_Rules/` and
`skills/project-memory/SKILL.md`, not here.

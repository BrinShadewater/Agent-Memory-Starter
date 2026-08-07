@AGENTS.md

## Claude Code addendum

The line above is a Claude Code import: the full contents of `AGENTS.md` load with
this file, mechanically. This file used to say "Read AGENTS.md" instead — a pointer
the model had to notice and choose to follow, which is a softer guarantee than an
import. Keeping the content in one place is still the point; this repo argues at
length that duplicated always-loaded context is a cost.

If you are looking for the memory rules an agent should follow when *using* a
vault — as opposed to developing this kit — those are in `vault/10_Rules/` and
`skills/project-memory/SKILL.md`, not here.

# Contributing

This is a small project maintained by one person, so here is the honest version rather
than a template.

## What is welcome

- **Reports that the discipline failed you.** The rules in `vault/10_Rules/` and the
  policies in `vault/40_Knowledge/` exist because something went wrong once. If one of
  them is wrong, unclear, or made your agent behave badly, that is the most useful thing
  you can tell me.
- **A trap this kit does not cover.** The verification-discipline incident log is the
  heart of the kit. New entries — an audit that produced a confident wrong answer, and
  the check that would have caught it — are genuinely valuable.
- **Bug reports for the hooks and scripts**, with the platform you ran them on. They are
  developed on Windows with git-bash and WSL; other combinations get less exercise.
- **Documentation corrections.** If something read as misleading, it misled everyone.

## What to expect

Response times depend on whether this is currently in the middle of the work it was
built for. Please do not read silence as dismissal — issues are read.

Large refactors or new subsystems are unlikely to be merged unprompted. Open an issue
first and let's agree on the shape before you spend real time.

## Before opening a pull request

- Run `python scripts/check_export_safe.py`. It must exit 0. If you added examples,
  make sure they use placeholder names rather than your own.
- Keep the vault files *empty of content*. This kit ships structure on purpose; a
  populated example note would become the thing people copy instead of thinking.
- Match the voice of the file you are editing. The vault notes argue for a rule and say
  what it cost to learn — they are not reference docs.

## Licence

Contributions are accepted under this project's MIT licence.

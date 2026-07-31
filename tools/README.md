# Adjacent tools — not bundled, and why

Two tools were considered for this kit and are pointed at rather than copied in. Both
decisions are about provenance, not quality.

## SEO auditing — use the upstream project

**Not included, because it is not mine to give.**

The SEO skill in use here is third-party: **Agentic SEO Skill**, MIT licensed,
copyright 2026 Bhanu Namikaze and agricidaniel.

- Source: `github.com/Bhanunamikaze/Agentic-SEO-Skill`
- Install per that repo's own `install.sh` / `install.ps1`

MIT would permit redistributing it inside this kit with the licence retained. It is still
the wrong call: it is already public, actively maintained upstream, and 105 files of it
would double the kit's size while making its authorship ambiguous to anyone who unzips
it. **Get it from the authors, who will have a newer version than any copy I could
bundle.**

If you use it alongside this kit, one note from experience: it ships 33 scripts that its
own `SKILL.md` calls. If you ever install it from a bare `SKILL.md`, those scripts are
silently deleted — see the file-count check in
[`skills/skill-maintenance/`](../skills/skill-maintenance/SKILL.md).

## Image pipeline — not included

**Not included, because the package is a product rather than a tool.**

The image pipeline used here (`webp-me-daddy`) is genuinely good at what it does — a
recipe-driven WebP pipeline producing optimised assets, responsive variants, structured
metadata, accessibility-safe alt text, and lintable output contracts.

But the package is 3.2 MB, and most of that is not the tool:

| Part | Size | Nature |
|---|---|---|
| `webp_me_daddy_core.py` | 165 KB | the actual tool |
| Brand logo assets | 548 KB | one company's branding |
| Explainer PDFs | 660 KB | marketing collateral |
| Render review scratch | ~1.8 MB | debris that should never have shipped |
| `product-brief-roadmap.md` | 7 KB | **commercial product strategy** |
| `landing-page-messaging.md` | 6 KB | **commercial positioning** |

Stripping it to the tool is a real piece of work, not a copy. Until that is done,
shipping it means shipping someone's product roadmap and brand assets to whoever gets the
kit.

**The transferable part is already in this kit** — the rule that a skill must not ship its
author's debris is in `skills/skill-maintenance/SKILL.md`, and this package is the worked
example of violating it.

## The general principle

Both of these are the same judgement in different clothes: **check what a package actually
contains before redistributing it.** A `.skill` file is a zip, and the file listing tells
you things the description does not — third-party licences, brand assets, business
documents, and scratch directories that were never meant to leave the machine.

```bash
python -c "import zipfile;[print(f'{zipfile.ZipFile(\"x.skill\").getinfo(f).file_size:>9,}  {f}') for f in zipfile.ZipFile('x.skill').namelist()]"
```

Run that before you hand anything to anyone.

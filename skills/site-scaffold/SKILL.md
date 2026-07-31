---
name: site-scaffold
description: >
  Spin up a new website on one consistent house stack (Vite + React + TypeScript,
  deploy-on-push, react-router, react-markdown, lucide-react, a verify gate, and an
  optional content pipeline) so new sites match each other instead of drifting. Use
  whenever the user wants to "start a new site", "scaffold a site", "set up another
  web project", spin up a landing page or microsite, or bootstrap a content-driven
  book or guide site.
  SKIP for deploying or rebuilding a site that already exists, and for auditing an
  existing site. This skill is for standing a NEW site up.
---

# New site scaffold

Every site sharing a stack is what lets one deploy procedure, one image pipeline and one
SEO pass work everywhere. This bootstraps a new one on those conventions instead of
copy-pasting an old repo and inheriting its cruft.

**The stack itself is a choice, not a recommendation.** Edit
[`references/stack.md`](references/stack.md) to describe yours, then edit the script to
emit it. What transfers is the discipline: one standard, a verify gate from day one, and
a scaffold that refuses to clobber.

## Scaffold it

```bash
python3 <SKILL_DIR>/scripts/init_site.py <target-dir> --name "Site Name" [--content]
```

- **Plain site** (landing page, portfolio, microsite): omit `--content`.
- **Content-driven site** (a book, a field guide, a docs set): add `--content` for the
  `content/` + `pipeline/` + `app/public/content/` skeleton.

**The script only writes files that do not already exist — it never clobbers.** Then:

```bash
cd <target-dir>/app && npm install && npm run dev
```

Wire up a repo, import it in your host, and it deploys on push to `main`.

## After scaffolding

- **Images:** run them through an image pipeline before they go near a commit.
- **SEO:** once there is real content, not before — an SEO pass on placeholder copy tells
  you nothing.
- **Content sites:** implement the content build in `pipeline/`. Remember content is
  fetched at runtime, so content-only changes do not need a rebuild.

## Why a verify gate from day one

A stub `verify.cjs` that does nothing is still worth scaffolding, because the gate is the
thing that is never added later. Once `npm run verify` exists and is wired into the push
path, adding a check to it is a five-minute job. Adding the gate itself to a mature repo
means touching every contributor's habits.

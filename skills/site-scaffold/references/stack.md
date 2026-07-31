# House web stack

The conventions a new site should match, so your deploy, image and SEO tooling keeps
working across all of them. **This is one opinionated stack, not the only good one** —
the value is that every site matches *something*, not that it matches this.

## Core

- **Vite + React 18 + TypeScript**, SPA. Build: `tsc -b && vite build`.
- **Routing:** react-router-dom. **Markdown:** react-markdown + remark-gfm.
- **Icons:** lucide-react. **Perf:** your host's speed-insights package.
- **Hosting:** auto-deploy on push to `main`. **`dist/` is gitignored** — the host builds
  on push. Never commit `dist`.

## The verify gate

Gate pushes behind `npm run verify`, which orchestrates whatever checks the project has
grown: pagination, image audit, performance budgets, built-site checks, a browser smoke
test. A new site starts with a stub `verify.cjs` and ports checks in as it needs them.

The point is that the gate exists from day one. A verify script added later never gets
added.

## Content-driven sites

Source of truth is a manuscript or markdown set living *above* `app/`. A pipeline parses
it into `content/*.json`; a publish step copies `content/*` into `app/public/content/`.

**Content is fetched at runtime**, so content-only fixes can be staged into
`public/content` and deployed without a rebuild. Code changes need a real build. Knowing
which of the two you are making saves a lot of confused debugging.

## Known traps

- **Vite litters `vite.config.ts.timestamp-*.mjs`** on every config change. The
  scaffold's `.gitignore` already excludes them.
- **Know which disk your build is landing on.** If your agent runtime mounts the project
  rather than working on it directly, builds and verification must be routed to the real
  disk, and a mount can serve stale or truncated copies of files with long lines. State
  which runtime each rule belongs to, or the rule misleads whoever reads it elsewhere.

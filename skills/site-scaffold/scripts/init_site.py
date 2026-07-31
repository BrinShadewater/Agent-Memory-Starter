#!/usr/bin/env python3
"""
Scaffold a new Vite + React + TypeScript site on one consistent house standard:
Vercel-on-push, react-router, react-markdown,
lucide-react, a verify gate, and a place for a content pipeline.

Usage:
  python3 init_site.py <target-dir> --name "Site Name" [--content]

--content adds a content/ + pipeline/ skeleton for manuscript-driven sites (a book,
a field guide, a docs set). Omit it for a plain marketing/portfolio site.

Creates files only if they don't already exist; never overwrites. Run `npm install`
afterward, then `npm run dev`.
"""
import argparse, json, os, textwrap

def w(path, content):
    if os.path.exists(path):
        print(f"  skip (exists): {path}"); return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote: {path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--name", required=True)
    ap.add_argument("--content", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.target)
    app = os.path.join(root, "app")
    print(f"Scaffolding '{a.name}' at {root}")

    pkg = {
        "name": a.name.lower().replace(" ", "-"),
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc -b && vite build",
            "preview": "vite preview",
            "verify": "node scripts/verify.cjs",
        },
        "dependencies": {
            "lucide-react": "^0.383.0",
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "react-markdown": "^9.0.0",
            "react-router-dom": "^6.23.0",
            "remark-gfm": "^4.0.0",
            "@vercel/speed-insights": "^1.0.0",
        },
        "devDependencies": {
            "@types/react": "^18.3.0",
            "@types/react-dom": "^18.3.0",
            "@vitejs/plugin-react": "^4.3.0",
            "typescript": "^5.4.0",
            "vite": "^5.2.0",
        },
    }
    w(os.path.join(app, "package.json"), json.dumps(pkg, indent=2) + "\n")

    w(os.path.join(app, "vite.config.ts"), textwrap.dedent('''\
        import { defineConfig } from "vite";
        import react from "@vitejs/plugin-react";

        // House default: SPA on Vercel, build output in dist/ (gitignored).
        export default defineConfig({
          plugins: [react()],
          build: { outDir: "dist" },
        });
        '''))

    w(os.path.join(app, "vercel.json"), json.dumps({
        "rewrites": [{"source": "/(.*)", "destination": "/index.html"}]
    }, indent=2) + "\n")

    w(os.path.join(app, "tsconfig.json"), json.dumps({
        "compilerOptions": {
            "target": "ES2020", "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"], "module": "ESNext",
            "skipLibCheck": True, "moduleResolution": "bundler",
            "jsx": "react-jsx", "strict": True, "noEmit": True,
        },
        "include": ["src"],
    }, indent=2) + "\n")

    w(os.path.join(app, "index.html"), textwrap.dedent(f'''\
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{a.name}</title>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/main.tsx"></script>
          </body>
        </html>
        '''))

    w(os.path.join(app, "src", "main.tsx"), textwrap.dedent('''\
        import React from "react";
        import ReactDOM from "react-dom/client";
        import { BrowserRouter } from "react-router-dom";
        import App from "./App";

        ReactDOM.createRoot(document.getElementById("root")!).render(
          <React.StrictMode>
            <BrowserRouter><App /></BrowserRouter>
          </React.StrictMode>
        );
        '''))

    w(os.path.join(app, "src", "App.tsx"), textwrap.dedent(f'''\
        export default function App() {{
          return <main style={{{{ maxWidth: 720, margin: "0 auto", padding: 24 }}}}>
            <h1>{a.name}</h1>
            <p>Scaffolded on the house stack. Replace me.</p>
          </main>;
        }}
        '''))

    w(os.path.join(app, "scripts", "verify.cjs"), textwrap.dedent('''\
        // House verify gate. Add project checks here and run `npm run verify`
        // before pushing (Vercel deploys on push to main).
        // Add your own check:* scripts here (pagination, image audit, perf
        // budgets, built-site smoke) as the site grows.
        console.log("verify: no checks wired yet  -  add them before relying on this gate.");
        '''))

    w(os.path.join(app, ".gitignore"), "node_modules\ndist\n*.timestamp-*.mjs\n.vercel\n")

    if a.content:
        w(os.path.join(root, "content", ".gitkeep"), "")
        w(os.path.join(root, "pipeline", "build_content.py"), textwrap.dedent('''\
            #!/usr/bin/env python3
            """Parse the manuscript/source into content/*.json. Implement this for your
            pipeline here; content is fetched at runtime, so a content-only change can be
            staged into app/public/content and deployed without a rebuild."""
            print("TODO: implement the content build for this site.")
            '''))
        w(os.path.join(app, "public", "content", ".gitkeep"), "")

    print("\nNext:\n  cd", os.path.join(a.target, "app"),
          "\n  npm install\n  npm run dev\n"
          "Then wire a GitHub repo and import it in Vercel for deploy-on-push.")

if __name__ == "__main__":
    main()

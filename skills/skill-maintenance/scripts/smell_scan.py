r"""Rank SKILL.md files by patchwork smell density, and print the hits so they get read.

Why this exists: the first two de-patching passes ranked targets with an ad-hoc
`grep -ciE "corrected|stale|no longer|..."` over each SKILL.md. That picked
`deploy-web-edition` correctly and then picked `data-goblin-manuscript-check`
wrongly - 7 of its 8 hits were the words "corrected" and "stale" used as *subject
matter*, because its whole job is checking that corrected values are still present.
A substring count measures what a skill is about, not how patched it is. Same
failure class as the mention-count warning in references/source-map.md.

Two corrections are baked in here:

1. **Domain-vocabulary exclusion.** A term that appears in the skill's own
   frontmatter description is that skill's topic. Hits on it are suppressed
   (and counted separately, so the suppression is visible rather than silent).
2. **The hits are printed.** The score orders candidates; the lines decide.
   `--quiet` exists for a bare table, but the default makes reading them the
   path of least resistance.

Usage:
    python smell_scan.py                     # default Claude catalog
    python smell_scan.py --root <dir>        # e.g. ...\.codex\skills
    python smell_scan.py --skill deploy-web-edition   # one skill, all hits
    python smell_scan.py --self-test         # falsifiability fixtures
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".claude" / "skills"

# Each pattern targets prose that documents a *past repair* or bolts an exception
# onto a rule - the two things the de-patching doctrine says to fold. Patterns are
# deliberately narrow: a bare "note:" or "actually" matched far too much ordinary
# writing in the first version of this metric.
PATTERNS: list[tuple[str, str]] = [
    ("dated-correction", r"\b(corrected|fixed|changed|updated|re-based|rebased)\s+\d{4}-\d{2}-\d{2}"),
    ("dated-correction", r"\*\*(corrected|correction|update)\b[^*]{0,40}\d{4}-\d{2}-\d{2}"),
    ("version-archaeology", r"\bthe (previous|old|earlier|former) version\b"),
    ("version-archaeology", r"\b(this|that|it) (used to|once) (be|say|read|point|live|claim)"),
    ("version-archaeology", r"\b(is|are|was|were) no longer\b"),
    ("version-archaeology", r"\bturns? out\b"),
    ("version-archaeology", r"\b(was|were|is|proved) (confidently )?wrong\b"),
    ("version-archaeology", r"\buntil \d{4}-\d{2}-\d{2}\b"),
    ("bolted-exception", r"\bexcept when\b"),
    ("bolted-exception", r"\bunless you (are|have|know|explicitly)\b"),
    ("bolted-exception", r"\bbut only if\b"),
    ("bolted-exception", r"\bdo not assume\b"),
    ("stale-marker", r"\b(stale|dead|rotted|drifted) (path|paths|fact|facts|note|notes|copy|copies)\b"),
]

WORD_RE = re.compile(r"[a-z][a-z\-]{2,}")


def _stem(word: str) -> str:
    """Crude singularisation. 'stale facts' in a description must cover 'stale fact'
    in the body, or the suppression silently misses and the topic counts as smell -
    which is exactly what the self-test fixture caught on the first build."""
    for suffix in ("ies", "es", "s"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def _stems(words) -> set[str]:
    return {_stem(w) for w in words}


def description_vocab(text: str) -> set[str]:
    """Words in the frontmatter description - i.e. what this skill is *about*."""
    if not text.startswith("---"):
        return set()
    end = text.find("\n---", 3)
    if end == -1:
        return set()
    front = text[3:end]
    m = re.search(r"^description:(.*?)(?=^\w+:|\Z)", front, re.M | re.S)
    if not m:
        return set()
    return _stems(WORD_RE.findall(m.group(1).lower()))


def scan_text(text: str) -> tuple[list[tuple[int, str, str]], list[tuple[int, str, str]]]:
    """Return (hits, suppressed). Each entry is (line_no, category, line)."""
    vocab = description_vocab(text)
    hits: list[tuple[int, str, str]] = []
    suppressed: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        for category, pat in PATTERNS:
            m = re.search(pat, low)
            if not m:
                continue
            matched_words = _stems(WORD_RE.findall(m.group(0)))
            # Topic, not disease: the match is built from the skill's own subject
            # vocabulary. Count it separately instead of letting it inflate the score.
            if matched_words and matched_words <= vocab:
                suppressed.append((i, category, line.strip()))
            else:
                hits.append((i, category, line.strip()))
            break
    return hits, suppressed


def scan_skill(skill_dir: Path):
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return None
    text = md.read_text(encoding="utf-8", errors="replace")
    lines = max(1, len(text.splitlines()))
    hits, suppressed = scan_text(text)
    return {
        "name": skill_dir.name,
        "lines": lines,
        "hits": hits,
        "suppressed": suppressed,
        "density": round(len(hits) * 100 / lines, 1),
    }


def self_test() -> int:
    """Falsifiability: the metric must catch real patchwork and ignore topic words."""
    patched = (
        "---\nname: x\ndescription: Deploy a website to production.\n---\n"
        "Corrected 2026-07-28: node is on PATH now.\n"
        "The previous version of this skill used the wrong profile.\n"
        "NODE_ENV is no longer set to production.\n"
        "Do this, except when the mount is stale.\n"
    )
    topical = (
        "---\nname: y\ndescription: >\n  Checks that corrected values from the ledger are\n"
        "  still present and that stale facts have not crept back.\n---\n"
        "The sweep reports corrected values that went missing.\n"
        "It flags a stale fact that reappeared after an edit.\n"
    )
    p_hits, _ = scan_text(patched)
    t_hits, t_supp = scan_text(topical)
    ok = True
    if len(p_hits) < 4:
        print(f"FAIL: real patchwork under-detected ({len(p_hits)}/4 hits)")
        ok = False
    else:
        print(f"pass: real patchwork detected ({len(p_hits)} hits)")
    if t_hits:
        print(f"FAIL: topic vocabulary counted as smell ({t_hits})")
        ok = False
    else:
        print(f"pass: topic vocabulary not counted ({len(t_supp)} suppressed)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="skills catalog to scan")
    ap.add_argument("--skill", help="scan one skill and show every hit")
    ap.add_argument("--quiet", action="store_true", help="table only, no hit lines")
    ap.add_argument("--self-test", action="store_true", help="run the fixtures and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root)
    if not root.is_dir():
        print(f"No such catalog: {root}")
        return 2

    dirs = [root / args.skill] if args.skill else sorted(d for d in root.iterdir() if d.is_dir())
    results = [r for r in (scan_skill(d) for d in dirs) if r]
    if not results:
        print(f"No SKILL.md found under {root}")
        return 2
    results.sort(key=lambda r: (-r["density"], -len(r["hits"])))

    print(f"Catalog: {len(results)} skill(s) from {root}\n")
    print(f"{'skill':<32}{'lines':>6}{'hits':>6}{'/100':>7}{'suppressed':>12}")
    for r in results:
        print(f"{r['name']:<32}{r['lines']:>6}{len(r['hits']):>6}{r['density']:>7}{len(r['suppressed']):>12}")

    print(
        "\nDensity orders candidates; it does not judge them. Read the hits before"
        "\nrewriting anything - 'suppressed' counts matches on the skill's own topic"
        "\nvocabulary, which is the trap this metric was rebuilt to avoid."
    )

    if args.quiet:
        return 0

    shown = [r for r in results if r["hits"]][: (None if args.skill else 3)]
    for r in shown:
        print(f"\n--- {r['name']} ({len(r['hits'])} hit(s)) ---")
        for line_no, category, line in r["hits"]:
            print(f"  {line_no:>4}  [{category}] {line[:110]}")
        if r["suppressed"] and args.skill:
            print(f"  ({len(r['suppressed'])} suppressed as topic vocabulary)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

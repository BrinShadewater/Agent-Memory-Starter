"""Deterministic trigger/routing evals for your skill catalog.

Ported idea: addyosmani/agent-skills "Tier 2" evals (MIT). Positive prompts must
rank their skill near the top of a lexical (stemmed TF-IDF) ranking over skill
descriptions; negative prompts must be won by the skill that owns them; and no
two descriptions may drift into near-collision. This is a lexical approximation
of routing -- it cannot judge semantics, but it catches the two failure modes
that dominate real trigger bugs: a description missing the vocabulary the user
actually uses (false negative), and an over-broad description that outranks the
right skill (false positive). A failure here usually means "fix the
description", not "fix the eval".

House adaptation, load-bearing: the house descriptions carry deliberate SKIP
clauses that NAME their competitors ("SKIP for X (use other-skill)"). Feeding
those words to a lexical ranker would systematically misroute negatives into
the skill that disclaims them, so routing text is truncated at the first SKIP
clause before vectorising. The SKIP clause still matters for the real model
router -- this only keeps the lexical approximation honest.

Usage (from anywhere; output is pure ASCII for cp1252 consoles):

    python trigger_evals.py                      # scan ~/.claude/skills, report
    python trigger_evals.py --root <dir> ...     # add/replace scan roots
    python trigger_evals.py --min-rank1 70       # exit 1 below this rank-1 %
    python trigger_evals.py --verbose            # show top-3 for every prompt

Exit code is 0 unless --min-rank1 is given and unmet: a report that blocks
work gets disabled (house lesson, check_kit_drift tuning history).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".claude" / "skills"
DEFAULT_CASES = Path(__file__).resolve().parent.parent / "evals" / "cases.json"

# First occurrence of a SKIP/NOT-for clause ends the routing text (see module
# docstring). Case-sensitive on purpose: house convention capitalises them.
SKIP_CLAUSE = re.compile(r"\bSKIP\b|\bNOT for\b|\bDo NOT use\b|\bDo not invoke\b")

STOPWORDS = frozenset(
    """a an and are as at be before by can do does for from has have how i in is
    it its me my of on or our so that the this to use user users want wants we
    what when whenever which will with you your""".split()
)

TOKEN = re.compile(r"[a-z0-9]+")


def stem(token: str) -> str:
    """Light suffix stripper -- enough to unite plan/planning, audit/audits."""
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: len(token) - len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


def parse_frontmatter(skill_md: Path) -> tuple[str, str] | None:
    """Return (name, description) or None. Tolerates multi-line descriptions."""
    try:
        lines = skill_md.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    name, desc, in_desc = "", [], False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if re.match(r"^name\s*:", line):
            name, in_desc = line.split(":", 1)[1].strip(), False
        elif re.match(r"^description\s*:", line):
            first = line.split(":", 1)[1].strip()
            desc, in_desc = ([first.lstrip(">|").strip()] if first not in (">", "|", ">-", "|-") else []), True
        elif in_desc and (line.startswith(" ") or line.startswith("\t")):
            desc.append(line.strip())
        elif line.strip():
            in_desc = False
    if not name:
        return None
    return name, " ".join(desc)


def routing_text(name: str, description: str) -> str:
    cut = SKIP_CLAUSE.search(description)
    body = description[: cut.start()] if cut else description
    # Name tokens are trigger vocabulary too ("webp me daddy", "lucid sheep").
    return name.replace("-", " ") + " " + body


def scan_catalog(roots: list[Path]) -> dict[str, str]:
    """name -> routing text. First root wins on duplicate names."""
    catalog: dict[str, str] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            md = child / "SKILL.md"
            if child.is_dir() and md.is_file():
                parsed = parse_frontmatter(md)
                if parsed and parsed[0] not in catalog:
                    catalog[parsed[0]] = routing_text(*parsed)
    return catalog


class Ranker:
    def __init__(self, catalog: dict[str, str]):
        self.names = list(catalog)
        docs = [tokenize(catalog[n]) for n in self.names]
        self.df: dict[str, int] = {}
        for doc in docs:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1
        self.n_docs = max(len(docs), 1)
        self.doc_vecs = [self._vector(doc) for doc in docs]

    def _idf(self, term: str) -> float:
        return math.log((self.n_docs + 1) / (self.df.get(term, 0) + 1)) + 1.0

    def _vector(self, tokens: list[str]) -> dict[str, float]:
        tf: dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        vec = {t: (1 + math.log(c)) * self._idf(t) for t, c in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        return {t: w / norm for t, w in vec.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if len(b) < len(a):
            a, b = b, a
        return sum(w * b.get(t, 0.0) for t, w in a.items())

    def rank(self, prompt: str) -> list[tuple[str, float]]:
        q = self._vector(tokenize(prompt))
        scored = [(n, self._cosine(q, v)) for n, v in zip(self.names, self.doc_vecs)]
        return sorted(scored, key=lambda x: (-x[1], x[0]))

    def collisions(self) -> list[tuple[str, str, float]]:
        out = []
        for i in range(len(self.names)):
            for j in range(i + 1, len(self.names)):
                sim = self._cosine(self.doc_vecs[i], self.doc_vecs[j])
                if sim >= 0.50:
                    out.append((self.names[i], self.names[j], sim))
        return sorted(out, key=lambda x: -x[2])


def top3(ranking: list[tuple[str, float]]) -> str:
    return ", ".join(f"{n} ({s:.2f})" for n, s in ranking[:3])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", action="append", type=Path, default=None,
                    help="catalog root(s); default ~/.claude/skills")
    ap.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    ap.add_argument("--min-rank1", type=float, default=None,
                    help="exit 1 if positive rank-1 rate falls below this percent")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    roots = args.root or [DEFAULT_ROOT]
    catalog = scan_catalog(roots)
    if not catalog:
        print(f"ERROR: no skills found under {[str(r) for r in roots]}")
        return 1
    try:
        cases = json.loads(args.cases.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot load cases file {args.cases}: {exc}")
        return 1

    ranker = Ranker(catalog)
    print(f"Catalog: {len(catalog)} skills from {', '.join(str(r) for r in roots)}")
    print()

    pos_total = pos_rank1 = pos_topk = 0
    failures: list[str] = []
    skipped: list[str] = []

    for skill, spec in sorted(cases.items()):
        if skill not in catalog:
            skipped.append(skill)
            continue
        for case in spec.get("positive", []):
            prompt, k = case["prompt"], case.get("top_k", 3)
            ranking = ranker.rank(prompt)
            rank = next(i for i, (n, _) in enumerate(ranking, 1) if n == skill)
            pos_total += 1
            pos_rank1 += rank == 1
            ok = rank <= k
            pos_topk += ok
            mark = "PASS" if ok else "FAIL"
            if not ok:
                failures.append(f"  {skill} <- \"{prompt}\" ranked {rank} (top-{k}); top-3: {top3(ranking)}")
            if args.verbose or not ok:
                print(f"{mark} pos [{skill}] rank {rank}/{k}: \"{prompt}\"")
        for case in spec.get("negative", []):
            prompt, owner = case["prompt"], case.get("owner")
            ranking = ranker.rank(prompt)
            first = ranking[0][0]
            if owner and owner in catalog:
                rank_owner = next(i for i, (n, _) in enumerate(ranking, 1) if n == owner)
                rank_self = next(i for i, (n, _) in enumerate(ranking, 1) if n == skill)
                ok = rank_owner < rank_self
                detail = f"owner {owner} rank {rank_owner} vs {skill} rank {rank_self}"
            else:
                ok = first != skill
                detail = f"first: {first}" + (f" (owner {owner} not in catalog)" if owner else "")
            if not ok:
                failures.append(f"  {skill} neg \"{prompt}\": {detail}; top-3: {top3(ranking)}")
            if args.verbose or not ok:
                print(f"{'PASS' if ok else 'FAIL'} neg [{skill}]: \"{prompt}\" ({detail})")

    print()
    if pos_total:
        rate1 = 100.0 * pos_rank1 / pos_total
        ratek = 100.0 * pos_topk / pos_total
        print(f"Positive triggers: {pos_topk}/{pos_total} within top-k ({ratek:.0f}%), "
              f"rank-1 rate {rate1:.0f}%")
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(f)
    else:
        print("No routing failures.")
    if skipped:
        print(f"Skipped (not in scanned catalog): {', '.join(sorted(skipped))}")
        print("  (webp-me-daddy / transparent-gif-loop are plugin-served on the Claude")
        print("   side; add --root %USERPROFILE%\\.codex\\skills to include them.)")

    coll = ranker.collisions()
    print()
    if coll:
        print("Description similarity (>=0.50 warn, >=0.75 error):")
        for a, b, s in coll:
            level = "ERROR" if s >= 0.75 else "warn "
            print(f"  {level} {s:.2f}  {a} <-> {b}")
    else:
        print("No description collisions (all pairwise similarity < 0.50).")

    if args.min_rank1 is not None and pos_total and (100.0 * pos_rank1 / pos_total) < args.min_rank1:
        print(f"FAIL: rank-1 rate below --min-rank1 {args.min_rank1}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

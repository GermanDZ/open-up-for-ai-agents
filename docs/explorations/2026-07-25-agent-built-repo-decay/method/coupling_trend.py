#!/usr/bin/env python3
"""Does co-change coupling get worse as an agent-built codebase ages?

Splits history into equal-commit-count eras and recomputes the coupling graph
inside each, so eras are comparable. The headline number is the share of
co-change pairs that CROSS a module boundary — the thing an architectural
gate (design-queue D1) would actually threshold on.

Usage: coupling_trend.py --repo PATH [--label NAME] [--include GLOB]... [--eras N]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from decay import (DEFAULT_EXCLUDES, DOC_EXCLUDES, agentic, is_bot,
                   load_commits, module_of)


def coupling(commits, min_support, max_files, depth):
    pair = Counter()
    single = Counter()
    skipped = 0
    for c in commits:
        files = sorted({p for p, _, _ in c["files"]})
        if len(files) > max_files:
            skipped += 1
            continue
        for f in files:
            single[f] += 1
        for a, b in combinations(files, 2):
            pair[(a, b)] += 1

    rows = []
    for (a, b), n in pair.items():
        if n < min_support:
            continue
        union = single[a] + single[b] - n
        rows.append({
            "a": a, "b": b, "support": n,
            "jaccard": round(n / union, 4) if union else None,
            "cross_module": module_of(a, depth) != module_of(b, depth),
        })
    rows.sort(key=lambda r: (-r["support"], -(r["jaccard"] or 0)))
    cross = sum(1 for r in rows if r["cross_module"])
    return {
        "pairs": len(rows),
        "cross_module_pairs": cross,
        "cross_module_share": round(cross / len(rows), 4) if rows else None,
        "median_jaccard": (round(sorted(r["jaccard"] for r in rows)[len(rows) // 2], 4)
                           if rows else None),
        "max_support": rows[0]["support"] if rows else None,
        "skipped_large_commits": skipped,
        "top": rows[:10],
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--label", default="repo")
    ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--eras", type=int, default=4)
    ap.add_argument("--min-support", type=int, default=3)
    ap.add_argument("--max-files", type=int, default=40)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--json", dest="out")
    args = ap.parse_args(argv)

    pats = list(DEFAULT_EXCLUDES) + list(DOC_EXCLUDES)
    commits = [c for c in load_commits(args.repo, pats, tuple(args.include))
               if not is_bot(c) and c["files"]]

    size = max(1, len(commits) // args.eras)
    eras = []
    for i in range(0, len(commits), size):
        chunk = commits[i:i + size]
        if len(chunk) < size // 2 and eras:
            break
        r = coupling(chunk, args.min_support, args.max_files, args.depth)
        r.update({
            "era": f"{chunk[0]['date'][:10]}..{chunk[-1]['date'][:10]}",
            "commits": len(chunk),
            "agent_share": round(sum(1 for c in chunk if agentic(c)) / len(chunk), 3),
        })
        eras.append(r)

    res = {"label": args.label, "commits": len(commits), "eras": eras,
           "whole_history": coupling(commits, args.min_support, args.max_files, args.depth)}
    text = json.dumps(res, indent=1, sort_keys=True)
    if args.out:
        open(args.out, "w").write(text)
        print(f"{args.label}: {len(eras)} eras -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

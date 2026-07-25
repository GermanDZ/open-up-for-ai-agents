#!/usr/bin/env python3
"""Structural snapshots: rebuild the codebase's shape at the end of each month.

Tests the "god objects accumulate / structure stops keeping pace" half of the
decay thesis directly, rather than inferring it from commit behaviour. Every
number is measured on the tree as it actually stood at that date.

Usage: snapshots.py --repo PATH [--label NAME] [--include GLOB]... [--json OUT]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import statistics
import subprocess
import sys
from collections import Counter

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from decay import CODE_EXT, DEFAULT_EXCLUDES, DOC_EXCLUDES, TEST_RE, excluded, sh


def month_ends(repo):
    """Last commit sha of each calendar month, oldest first."""
    out = sh(repo, "log", "--reverse", "--format=%H %aI")
    last = {}
    for line in out.splitlines():
        sha, _, iso = line.partition(" ")
        if sha and iso:
            last[iso[:7]] = sha
    return sorted(last.items())


def tree_sizes(repo, sha, pats, includes):
    """path -> line count for every in-scope code file at `sha`."""
    listing = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", sha],
                             capture_output=True, text=True, errors="replace")
    paths = [p for p in listing.stdout.splitlines()
             if p.endswith(CODE_EXT) and not excluded(p, pats, includes)]
    if not paths:
        return {}
    proc = subprocess.run(["git", "-C", repo, "cat-file", "--batch"],
                          input="".join(f"{sha}:{p}\n" for p in paths).encode(),
                          capture_output=True)
    stream, pos, sizes, i = proc.stdout, 0, {}, 0
    while pos < len(stream) and i < len(paths):
        nl = stream.find(b"\n", pos)
        if nl < 0:
            break
        header = stream[pos:nl].split()
        if len(header) != 3:          # "missing" line — skip this path
            pos = nl + 1
            i += 1
            continue
        n = int(header[2])
        blob = stream[nl + 1:nl + 1 + n]
        sizes[paths[i]] = blob.count(b"\n") + (0 if blob.endswith(b"\n") or not blob else 1)
        pos = nl + 1 + n + 1
        i += 1
    return sizes


def module_of(path, depth=2):
    bits = path.split("/")
    return "/".join(bits[:depth]) if len(bits) > depth else "/".join(bits[:-1]) or "."


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--label", default="repo")
    ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--json", dest="out")
    args = ap.parse_args(argv)

    pats = list(DEFAULT_EXCLUDES) + list(DOC_EXCLUDES)
    includes = tuple(args.include)

    rows = []
    for month, sha in month_ends(args.repo):
        sizes = tree_sizes(args.repo, sha, pats, includes)
        if not sizes:
            continue
        vals = sorted(sizes.values())
        test_files = [p for p in sizes if TEST_RE.search(p)]
        src_lines = sum(v for p, v in sizes.items() if not TEST_RE.search(p))
        test_lines = sum(v for p, v in sizes.items() if TEST_RE.search(p))
        mods = Counter(module_of(p) for p in sizes)
        rows.append({
            "month": month,
            "code_files": len(vals),
            "code_lines": sum(vals),
            "med_file_lines": statistics.median(vals),
            "p90_file_lines": (round(statistics.quantiles(vals, n=10)[-1], 1)
                               if len(vals) > 10 else None),
            "max_file_lines": vals[-1],
            "files_gt_400": sum(1 for v in vals if v > 400),
            "share_gt_400": round(sum(1 for v in vals if v > 400) / len(vals), 4),
            "modules": len(mods),
            "files_per_module": round(len(vals) / len(mods), 2),
            "largest_module_files": mods.most_common(1)[0][1],
            "test_files": len(test_files),
            "test_to_src_lines": round(test_lines / src_lines, 3) if src_lines else None,
        })

    res = {"label": args.label, "includes": list(includes), "snapshots": rows}
    text = json.dumps(res, indent=1, sort_keys=True)
    if args.out:
        open(args.out, "w").write(text)
        print(f"{args.label}: {len(rows)} monthly snapshots -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

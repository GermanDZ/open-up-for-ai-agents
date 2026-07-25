#!/usr/bin/env python3
"""Line survival: of the lines a commit added, how many still exist at HEAD?

Message-independent, so it is immune to the conventional-commit confound that
contaminates any fix-rate read off commit subjects (agents write `fix:` far
more consistently than humans do, which inflates their apparent defect rate).

Survival falls with age for everyone, so the only honest comparison is
age-matched: cohorts are compared inside the same commit-age bucket.

Usage: survival.py --repo PATH [--label NAME] [--json OUT]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from decay import (CODE_EXT, DEFAULT_EXCLUDES, DOC_EXCLUDES, TEST_RE, agentic,
                   excluded, is_bot, load_commits, med, sh)

SHA_RE = re.compile(r"^([0-9a-f]{40}) \d+ \d+(?: \d+)?$")


def blame_file(repo, path):
    """sha -> surviving line count for one file at HEAD."""
    proc = subprocess.run(
        ["git", "-C", repo, "blame", "-w", "--line-porcelain", "HEAD", "--", path],
        capture_output=True, text=True, errors="replace")
    if proc.returncode != 0:
        return Counter()
    return Counter(m.group(1) for m in
                   (SHA_RE.match(l) for l in proc.stdout.splitlines()) if m)


def survival_by_commit(repo, paths, workers=8):
    total = Counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for c in pool.map(lambda p: blame_file(repo, p), paths):
            total.update(c)
    return total


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--label", default="repo")
    ap.add_argument("--json", dest="out")
    ap.add_argument("--include", action="append", default=[],
                    help="allowlist glob; when given, only matching paths count")
    ap.add_argument("--age-buckets", type=int, default=4)
    ap.add_argument("--min-added", type=int, default=20,
                    help="ignore commits adding fewer lines than this (noisy ratios)")
    args = ap.parse_args(argv)

    pats = list(DEFAULT_EXCLUDES) + list(DOC_EXCLUDES)
    commits = [c for c in load_commits(args.repo, pats, tuple(args.include)) if not is_bot(c) and c["files"]]
    by_sha = {c["sha"]: c for c in commits}

    paths = [p for p in sh(args.repo, "ls-files").splitlines()
             if p.endswith(CODE_EXT) and not excluded(p, pats, tuple(args.include))]
    surviving = survival_by_commit(args.repo, paths)

    now = datetime.now(timezone.utc).timestamp()
    rows = []
    for sha, c in by_sha.items():
        added = sum(a for p, a, _ in c["files"] if p.endswith(CODE_EXT))
        if added < args.min_added:
            continue
        alive = surviving.get(sha, 0)
        rows.append({
            "sha": sha[:12],
            "added": added,
            "alive": alive,
            "survival": round(min(1.0, alive / added), 4),
            "agent": agentic(c),
            "age_days": round((now - datetime.fromisoformat(c["date"]).timestamp()) / 86400.0, 1),
            "date": c["date"][:10],
            "test_only": all(TEST_RE.search(p) for p, _, _ in c["files"]),
        })
    rows.sort(key=lambda r: -r["age_days"])   # oldest first

    def agg(rs, name):
        if not rs:
            return {"cohort": name, "n": 0}
        added = sum(r["added"] for r in rs)
        alive = sum(r["alive"] for r in rs)
        return {
            "cohort": name,
            "n": len(rs),
            "lines_added": added,
            "lines_alive": alive,
            "pooled_survival": round(alive / added, 4) if added else None,
            "median_commit_survival": med([r["survival"] for r in rs]),
            "median_age_days": med([r["age_days"] for r in rs]),
        }

    # age-matched buckets: equal-size slices of the age-ordered commit list
    size = max(1, len(rows) // args.age_buckets)
    buckets = []
    for i in range(0, len(rows), size):
        chunk = rows[i:i + size]
        if len(chunk) < size // 2 and buckets:
            break
        buckets.append({
            "bucket": f"{chunk[0]['date']}..{chunk[-1]['date']}",
            "age_days_med": med([r["age_days"] for r in chunk]),
            "agent": agg([r for r in chunk if r["agent"]], "agent"),
            "human": agg([r for r in chunk if not r["agent"]], "human"),
        })

    # Same-month comparison: both cohorts share one exposure window and one
    # endpoint (HEAD), so survival is age-matched by construction. Rank-ordered
    # buckets do not guarantee that when activity is uneven across months.
    by_month = defaultdict(list)
    for r in rows:
        by_month[r["date"][:7]].append(r)
    monthly = []
    for m in sorted(by_month):
        a = [r for r in by_month[m] if r["agent"]]
        h = [r for r in by_month[m] if not r["agent"]]
        monthly.append({"month": m, "agent": agg(a, "agent"), "human": agg(h, "human")})

    res = {
        "label": args.label,
        "code_files_blamed": len(paths),
        "commits_scored": len(rows),
        "by_month": monthly,
        "rows": rows,
        "overall": [agg([r for r in rows if r["agent"]], "agent"),
                    agg([r for r in rows if not r["agent"]], "human")],
        "age_matched": buckets,
    }
    text = json.dumps(res, indent=1, sort_keys=True)
    if args.out:
        open(args.out, "w").write(text)
        print(f"{args.label}: blamed {len(paths)} files, scored {len(rows)} commits -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

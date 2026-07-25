#!/usr/bin/env python3
"""Controlled comparisons that the naive cohort split cannot make.

Three analyses, each killing a specific confound:

  paired   agent-vs-human within the SAME calendar month, so codebase age,
           feature area and team habits are held roughly constant. The
           whole-history cohort split confounds authorship with era.
  equaln   trend over equal-COMMIT-COUNT buckets instead of calendar months,
           so revisit/rework rates are not inflated by busy months.
  convcommit  adoption of conventional-commit prefixes over time — the
           control for reading fix-rate off commit subjects at all.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from decay import (DEFAULT_EXCLUDES, DOC_EXCLUDES, FIX_RE, TEST_RE, agentic,
                   is_bot, load_commits, med, mean, module_of, month_of)

STRICT_FIX_RE = __import__("re").compile(r"^\s*(fix|revert)(\([^)]*\))?!?:", __import__("re").I)
CONV_RE = __import__("re").compile(r"^\s*[a-z]+(\([^)]*\))?!?:\s", __import__("re").I)


def summarize(cs):
    if not cs:
        return None
    files_per = [len(c["files"]) for c in cs]
    mods = [len({module_of(p) for p, _, _ in c["files"]}) for c in cs]
    adds = sum(a for c in cs for _, a, _ in c["files"])
    dels = sum(d for c in cs for _, _, d in c["files"])
    tf = sum(1 for c in cs for p, _, _ in c["files"] if TEST_RE.search(p))
    nf = sum(len(c["files"]) for c in cs)
    return {
        "n": len(cs),
        "files_mean": mean(files_per),
        "files_med": med(files_per),
        "modules_mean": mean(mods),
        "churn": round(dels / adds, 3) if adds else None,
        "fix_loose": round(sum(1 for c in cs if FIX_RE.search(c["subject"])) / len(cs), 3),
        "fix_strict": round(sum(1 for c in cs if STRICT_FIX_RE.search(c["subject"])) / len(cs), 3),
        "conv": round(sum(1 for c in cs if CONV_RE.search(c["subject"])) / len(cs), 3),
        "test_share": round(tf / nf, 3) if nf else None,
        "lines_per_commit": round((adds + dels) / len(cs), 1),
    }


def paired(commits, min_each):
    by_month = defaultdict(list)
    for c in commits:
        by_month[month_of(c["date"])].append(c)
    rows = []
    for m in sorted(by_month):
        a = [c for c in by_month[m] if agentic(c)]
        h = [c for c in by_month[m] if not agentic(c)]
        if len(a) >= min_each and len(h) >= min_each:
            rows.append({"month": m, "agent": summarize(a), "human": summarize(h)})
    return rows


def equaln(commits, buckets):
    if not commits:
        return []
    size = max(1, len(commits) // buckets)
    out = []
    for i in range(0, len(commits), size):
        chunk = commits[i:i + size]
        if len(chunk) < size // 2 and out:
            break
        s = summarize(chunk)
        gaps = [g for c in chunk for g in c["revisit_gaps"]]
        ages = [a for c in chunk for a in c["file_ages"]]
        s.update({
            "bucket": f"{i}-{i + len(chunk) - 1}",
            "from": chunk[0]["date"][:10],
            "to": chunk[-1]["date"][:10],
            "agent_share": round(sum(1 for c in chunk if agentic(c)) / len(chunk), 3),
            "revisit_gap_med": med(gaps),
            "rework_lt7d": round(sum(1 for g in gaps if g < 7) / len(gaps), 3) if gaps else None,
            "file_age_med": med(ages),
            "distinct_files": len({p for c in chunk for p, _, _ in c["files"]}),
        })
        out.append(s)
    return out


def lifecycle(commits):
    """Re-derive per-file lifecycle fields (load_commits does not set them)."""
    from datetime import datetime
    created, last = {}, {}
    for c in commits:
        t = datetime.fromisoformat(c["date"]).timestamp()
        ages, gaps = [], []
        for path, _, _ in c["files"]:
            if path in created:
                ages.append((t - created[path]) / 86400.0)
                gaps.append((t - last[path]) / 86400.0)
            else:
                created[path] = t
            last[path] = t
        c["file_ages"], c["revisit_gaps"] = ages, gaps
    return commits


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--label", default="repo")
    ap.add_argument("--buckets", type=int, default=8)
    ap.add_argument("--min-each", type=int, default=10)
    ap.add_argument("--include-docs", action="store_true")
    ap.add_argument("--json", dest="out")
    ap.add_argument("--include", action="append", default=[],
                    help="allowlist glob; when given, only matching paths count")
    args = ap.parse_args(argv)

    pats = list(DEFAULT_EXCLUDES) + ([] if args.include_docs else list(DOC_EXCLUDES))
    commits = [c for c in load_commits(args.repo, pats, tuple(args.include)) if not is_bot(c) and c["files"]]
    commits = lifecycle(commits)

    res = {
        "label": args.label,
        "commits": len(commits),
        "paired_months": paired(commits, args.min_each),
        "equal_n_buckets": equaln(commits, args.buckets),
        "conv_adoption": [
            {"month": m, "n": len(cs),
             "conv": round(sum(1 for c in cs if CONV_RE.search(c["subject"])) / len(cs), 3),
             "agent_share": round(sum(1 for c in cs if agentic(c)) / len(cs), 3)}
            for m, cs in sorted(
                ((m, [c for c in commits if month_of(c["date"]) == m])
                 for m in sorted({month_of(c["date"]) for c in commits})))
        ],
    }
    text = json.dumps(res, indent=1, sort_keys=True)
    if args.out:
        open(args.out, "w").write(text)
        print(f"{args.label}: {len(commits)} commits, "
              f"{len(res['paired_months'])} paired months -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

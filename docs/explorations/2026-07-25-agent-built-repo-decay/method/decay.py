#!/usr/bin/env python3
"""Decay battery: monthly time-series maintainability proxies from git history.

Report-only. Tests the claim that agent-built codebases start struggling at
3-6 months. Every metric is computed per calendar month so a trend is visible.

Usage: decay.py --repo PATH [--label NAME] [--json OUT] [--exclude GLOB]...
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime

REC = "\x01"
SEP = "\x1f"

AGENT_RE = re.compile(r"co-authored-by:.*(claude|copilot|cursor|aider|devin)", re.I)
BOT_RE = re.compile(r"dependabot|renovate|github-action", re.I)
FIX_RE = re.compile(r"^\s*(fix|bug|hotfix|revert|repair|patch)\b|\bfix(es|ed)?\b", re.I)
REVERT_RE = re.compile(r"^\s*revert\b", re.I)

DEFAULT_EXCLUDES = (
    "docs-eng-process/*", ".claude/*", ".cursor/*", ".github/*",
    "coverage/*", "log/*", "node_modules/*", "vendor/*", "tmp/*",
    "*.lock", "package-lock.json", "Gemfile.lock", "yarn.lock",
    "openup-knowledge-base/*", ".openup/*",
)
DOC_EXCLUDES = ("docs/*", "*.md")

TEST_RE = re.compile(r"(^|/)(test|tests|spec|specs)/|_test\.|_spec\.|\.test\.|\.spec\.")
CODE_EXT = (".rb", ".py", ".js", ".ts", ".jsx", ".tsx", ".erb", ".go", ".java",
            ".rs", ".c", ".cc", ".cpp", ".h", ".css", ".scss", ".sh", ".sql")


def sh(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {out.stderr[:400]}")
    return out.stdout


def excluded(path, patterns, includes=()):
    """True if `path` is out of scope: outside the allowlist, or blocklisted.

    An allowlist is the only defensible scope for these repos — the app repos
    vendor this framework's own scripts/ tree, so a blocklist keeps admitting
    copied-in files as if they were application code.
    """
    if includes and not any(fnmatch.fnmatch(path, i) for i in includes):
        return True
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def load_commits(repo, patterns, includes=()):
    """Every non-merge commit, oldest first, with its numstat file list."""
    fmt = f"{REC}%H{SEP}%aI{SEP}%an{SEP}%s{SEP}%b{SEP}"
    raw = sh(repo, "log", "--reverse", "--no-merges", "--numstat",
             f"--format={fmt}", "--no-renames")
    commits = []
    for chunk in raw.split(REC):
        if not chunk.strip():
            continue
        # fmt ends with a trailing SEP, so the numstat block is its own field —
        # the body keeps its newlines (that is where Co-Authored-By lives).
        fields = chunk.split(SEP)
        if len(fields) < 6:
            continue
        sha, date, author, subject, body = fields[:5]
        numstat = SEP.join(fields[5:])
        files = []
        for line in numstat.splitlines():
            line = line.strip()
            if not line:
                continue
            bits = line.split("\t")
            if len(bits) != 3:
                continue
            adds, dels, path = bits
            if excluded(path, patterns, includes):
                continue
            files.append((path, 0 if adds == "-" else int(adds),
                          0 if dels == "-" else int(dels)))
        commits.append({
            "sha": sha, "date": date, "author": author, "subject": subject,
            "body": body, "files": files,
        })
    return commits


def month_of(iso):
    return iso[:7]


def agentic(c):
    return bool(AGENT_RE.search(c["body"] or "")) or "claude" in c["author"].lower()


def is_bot(c):
    return bool(BOT_RE.search(c["author"])) or bool(BOT_RE.search(c["subject"]))


def module_of(path, depth=2):
    bits = path.split("/")
    return "/".join(bits[:depth]) if len(bits) > depth else "/".join(bits[:-1]) or "."


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.fmean(xs), 3) if xs else None


def gini(counts):
    xs = sorted(counts)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return None
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return round((2 * cum) / (n * sum(xs)) - (n + 1) / n, 3)


def analyse(repo, label, patterns, include_docs, includes=()):
    pats = list(patterns)
    if not include_docs:
        pats += list(DOC_EXCLUDES)
    commits = load_commits(repo, pats, includes)
    commits = [c for c in commits if not is_bot(c)]
    commits = [c for c in commits if c["files"]]

    # ---- file lifecycle: creation + last-touch, walked in commit order ----
    created = {}
    last_touch = {}
    touch_count = Counter()
    for c in commits:
        t = datetime.fromisoformat(c["date"]).timestamp()
        ages, rework = [], []
        for path, _, _ in c["files"]:
            touch_count[path] += 1
            if path in created:
                ages.append((t - created[path]) / 86400.0)
                rework.append((t - last_touch[path]) / 86400.0)
            else:
                created[path] = t
            last_touch[path] = t
        c["file_ages"] = ages
        c["revisit_gaps"] = rework
        c["new_files"] = len(c["files"]) - len(ages)

    by_month = defaultdict(list)
    for c in commits:
        by_month[month_of(c["date"])].append(c)

    months = []
    for m in sorted(by_month):
        cs = by_month[m]
        files_per = [len(c["files"]) for c in cs]
        mods_per = [len({module_of(p) for p, _, _ in c["files"]}) for c in cs]
        adds = sum(a for c in cs for _, a, _ in c["files"])
        dels = sum(d for c in cs for _, _, d in c["files"])
        ages = [a for c in cs for a in c["file_ages"]]
        gaps = [g for c in cs for g in c["revisit_gaps"]]
        touched = [p for c in cs for p, _, _ in c["files"]]
        edits = sum(len(c["file_ages"]) for c in cs)
        new = sum(c["new_files"] for c in cs)
        test_files = sum(1 for p in touched if TEST_RE.search(p))
        code_files = sum(1 for p in touched if p.endswith(CODE_EXT))
        months.append({
            "month": m,
            "commits": len(cs),
            "agent_share": round(sum(1 for c in cs if agentic(c)) / len(cs), 3),
            "files_per_commit_med": med(files_per),
            "files_per_commit_mean": mean(files_per),
            "modules_per_commit_mean": mean(mods_per),
            "lines_added": adds,
            "lines_deleted": dels,
            "churn_ratio": round(dels / adds, 3) if adds else None,
            "edit_vs_new_ratio": round(edits / new, 3) if new else None,
            "median_file_age_days_at_edit": med(ages),
            "median_revisit_gap_days": med(gaps),
            "rework_lt_7d_share": (round(sum(1 for g in gaps if g < 7) / len(gaps), 3)
                                   if gaps else None),
            "fix_commit_share": round(sum(1 for c in cs if FIX_RE.search(c["subject"]))
                                      / len(cs), 3),
            "revert_commit_share": round(sum(1 for c in cs
                                             if REVERT_RE.search(c["subject"])) / len(cs), 3),
            "test_touch_share": (round(test_files / len(touched), 3) if touched else None),
            "distinct_files_touched": len(set(touched)),
            "hotspot_gini": gini(list(Counter(touched).values())),
            "code_files_touched": code_files,
        })

    # ---- authorship split (whole-history, not monthly) ----
    def slice_stats(cs, name):
        if not cs:
            return {"cohort": name, "commits": 0}
        files_per = [len(c["files"]) for c in cs]
        mods_per = [len({module_of(p) for p, _, _ in c["files"]}) for c in cs]
        adds = sum(a for c in cs for _, a, _ in c["files"])
        dels = sum(d for c in cs for _, _, d in c["files"])
        gaps = [g for c in cs for g in c["revisit_gaps"]]
        return {
            "cohort": name,
            "commits": len(cs),
            "files_per_commit_med": med(files_per),
            "files_per_commit_mean": mean(files_per),
            "modules_per_commit_mean": mean(mods_per),
            "churn_ratio": round(dels / adds, 3) if adds else None,
            "median_revisit_gap_days": med(gaps),
            "rework_lt_7d_share": (round(sum(1 for g in gaps if g < 7) / len(gaps), 3)
                                   if gaps else None),
            "fix_commit_share": round(sum(1 for c in cs if FIX_RE.search(c["subject"]))
                                      / len(cs), 3),
            "test_touch_share": round(
                sum(1 for c in cs for p, _, _ in c["files"] if TEST_RE.search(p))
                / max(1, sum(len(c["files"]) for c in cs)), 3),
        }

    cohorts = [
        slice_stats([c for c in commits if agentic(c)], "agent"),
        slice_stats([c for c in commits if not agentic(c)], "human"),
    ]

    # ---- final-state structure ----
    tracked = [p for p in sh(repo, "ls-files").splitlines()
               if not excluded(p, pats, includes)]
    # line counts straight from HEAD via one cat-file --batch, not N `git show`s
    code_paths = [p for p in tracked if p.endswith(CODE_EXT)]
    sizes = []
    if code_paths:
        # bytes, not str: cat-file sizes are byte counts, so slicing a decoded
        # string would desync the stream on the first non-ASCII file.
        proc = subprocess.run(
            ["git", "-C", repo, "cat-file", "--batch"],
            input="".join(f"HEAD:{p}\n" for p in code_paths).encode(),
            capture_output=True)
        stream = proc.stdout
        pos = 0
        while pos < len(stream):
            nl = stream.find(b"\n", pos)
            if nl < 0:
                break
            header = stream[pos:nl].split()
            if len(header) != 3:
                pos = nl + 1
                continue
            size = int(header[2])
            blob = stream[nl + 1:nl + 1 + size]
            sizes.append(blob.count(b"\n") + (0 if blob.endswith(b"\n") or not blob else 1))
            pos = nl + 1 + size + 1
    structure = {
        "tracked_files": len(tracked),
        "code_files": len(sizes),
        "code_lines_total": sum(sizes),
        "code_file_lines_med": med(sizes),
        "code_file_lines_p90": (round(statistics.quantiles(sizes, n=10)[-1], 1)
                                if len(sizes) > 10 else None),
        "code_file_lines_max": max(sizes) if sizes else None,
        "files_over_400_lines": sum(1 for s in sizes if s > 400),
        "modules": len({module_of(p) for p in tracked}),
    }

    return {
        "label": label,
        "repo": repo,
        "commits_analysed": len(commits),
        "span": [months[0]["month"], months[-1]["month"]] if months else None,
        "include_docs": include_docs,
        "includes": list(includes),
        "excludes": pats,
        "months": months,
        "cohorts": cohorts,
        "structure": structure,
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--label", default=None)
    ap.add_argument("--json", dest="out", default=None)
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--include-docs", action="store_true")
    ap.add_argument("--include", action="append", default=[],
                    help="allowlist glob; when given, only matching paths count")
    args = ap.parse_args(argv)

    pats = list(DEFAULT_EXCLUDES) + args.exclude
    res = analyse(args.repo, args.label or args.repo.rsplit("/", 1)[-1],
                  pats, args.include_docs, tuple(args.include))
    text = json.dumps(res, indent=1, sort_keys=True)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"{res['label']}: {res['commits_analysed']} commits, "
              f"span {res['span']} -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

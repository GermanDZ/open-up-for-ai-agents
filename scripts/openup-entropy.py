#!/usr/bin/env python3
"""OpenUP entropy report (T-127).

Measures codebase-entropy signals from telemetry the process **already emits**,
so the question "is this codebase decaying?" is answered with numbers instead of
a thesis. Three independent inputs, none of them authored by a model:

  * declared surface   ``docs/changes/**/plan.md`` frontmatter ``touches:``
  * lane run logs      ``docs/agent-logs/runs/*.jsonl`` (session_begin/_end, commit)
  * actual diffs       ``git log --numstat``, joined on a ``[T-NNN]`` commit subject

Everything is a projection of one **unit-of-work x file** bipartite graph, built
twice — once from what a lane *declared* it would touch, once from what its
commits *actually* touched. The unit is a **task** by default; ``--unit commit``
or ``--unit pr`` (T-128) make a repo with no task-id convention measurable, which
is what any comparison against a non-OpenUP codebase requires. Reported:

  cost      per-task declared/actual file counts, duration, commits, module spread,
            bucketed by task-index window and by calendar month (medians)
  drift     declared vs actual per task — Jaccard, and files changed but never
            declared. This is the falsifiability check on using ``touches`` as a
            coupling proxy at all.
  coupling  co-change over file pairs — support, Jaccard, lift — computed over the
            declared graph and the actual graph independently, cross-module flagged

Design rules (mirror scripts/openup-board.py):
  * Deterministic. Never invokes a model. Python standard library only. No network.
  * **Report-only.** There is no write path: no gate, no threshold, no state, no
    file created in the analyzed repo. Gates are justified by evidence, and this
    is the script that produces the evidence.
  * Identical inputs -> byte-identical output (no timestamps, no randomness).
  * Each input degrades independently — a foreign repo with only git history
    still yields actual-diff cost and coupling; declared sections read "no data".

Exit codes:
  0  success
  2  argparse / usage error
  3  nothing readable (not a git repo and no change folders)
"""

import argparse
import importlib.util
import json
import re
import statistics
import subprocess
import sys
from fnmatch import fnmatch
from itertools import combinations
from pathlib import Path

# --------------------------------------------------------------------------
# Reuse openup-claims.py's path matcher (hyphenated filename -> importlib), the
# same way openup-board.py does. A lane's `touches:` legitimately carries
# DIRECTORY entries (`docs-eng-process/templates/`), and the fence matches them
# by segment-prefix. Re-implementing that as string equality would score every
# directory declaration as a total miss — so the drift metric must use the
# fence's own semantics, not a lookalike.
# --------------------------------------------------------------------------
_CLAIMS_PATH = Path(__file__).resolve().parent / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]
seg_prefix_collide = claims.seg_prefix_collide

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_DATA = 3

# Paths every lane touches by construction (derived views, lane-owned audit trees,
# the lane's own change folder). Leaving them in makes every file pair look
# coupled, which is an artifact of the process rather than of the code.
DEFAULT_EXCLUDES = (
    "docs/roadmap.md",
    "docs/project-status.md",
    "docs/INDEX.md",
    "docs/agent-logs/*",
    "docs/status-notes/*",
    "docs/changes/*",
    ".openup/*",
)

# Bracketed tag is the repo convention (`fix(T-124): ... [T-124]`). The fallback
# reads a conventional-commit scope (`feat(T-124): ...`) for repos that never
# adopted the trailer.
TASK_RE_BRACKET = re.compile(r"\[([A-Za-z]{1,6}-\d{1,6})\]")
TASK_RE_SCOPE = re.compile(r"^\w+\(([A-Za-z]{1,6}-\d{1,6})\)")
TASK_ID_RE = re.compile(r"^[A-Za-z]{1,6}-\d{1,6}$")
# GitHub's squash-merge convention: "Display tool calls in message template (#416)".
PR_RE = re.compile(r"\(#(\d{1,7})\)")

# The unit of work every metric is keyed on. "task" is one choice, not the only
# one — a repo that never adopted a task-id convention is still measurable per
# commit or per merged PR. Never inferred: switching units silently would make
# two reports look comparable when their rows count different things.
UNITS = ("task", "commit", "pr")

BEGIN_EVENTS = {"session_begin", "iteration_start"}
END_EVENTS = {"session_end", "iteration_complete"}

_REC_SEP = "\x01"
_FLD_SEP = "\x02"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def task_index(task_id):
    """Numeric ordinal of a task id (``T-127`` -> 127); ``None`` if unparseable."""
    _, _, tail = task_id.rpartition("-")
    return int(tail) if tail.isdigit() else None


def is_task_id(value):
    return bool(value) and bool(TASK_ID_RE.match(value))


def module_of(path, depth):
    """Top-``depth`` path segments — the unit cross-module coupling is judged on."""
    parts = Path(path).parts
    return "/".join(parts[:depth]) if parts else path


def excluded(path, patterns, includes=()):
    """True if ``path`` is out of scope: outside the allowlist, or blocklisted.

    ``includes`` is an allowlist applied FIRST: when non-empty, any path that
    matches none of its patterns is excluded regardless of ``patterns``. An
    empty (default) allowlist means "everything is in scope", so existing
    blocklist-only behavior is unchanged when ``--include`` is never passed.
    """
    if includes and not any(fnmatch(path, inc) for inc in includes):
        return True
    return any(fnmatch(path, pat) for pat in patterns)


def median(values):
    vals = [v for v in values if v is not None]
    return round(statistics.median(vals), 2) if vals else None


def jaccard(a, b):
    union = len(a | b)
    return round(len(a & b) / union, 4) if union else None


def parse_iso(ts):
    """Parse a log timestamp to epoch seconds; ``None`` if unusable."""
    if not isinstance(ts, str):
        return None
    from datetime import datetime

    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def month_of(ts):
    return ts[:7] if isinstance(ts, str) and len(ts) >= 7 else None


# ---------------------------------------------------------------------------
# loaders — each returns {} when its source is absent (never raises)
# ---------------------------------------------------------------------------
def _frontmatter_touches(text):
    """Extract ``id`` and the ``touches:`` block list from a plan's frontmatter.

    Deliberately a small hand parser rather than a YAML dependency — the repo's
    scripts are stdlib-only, and the two keys are a fixed, simple shape.
    """
    if not text.startswith("---"):
        return None, []
    end = text.find("\n---", 3)
    if end == -1:
        return None, []
    block = text[3:end]

    task_id = None
    m = re.search(r"^id:\s*(\S+)", block, re.M)
    if m:
        task_id = m.group(1).strip().strip("\"'")

    touches = []
    m = re.search(r"^touches:\s*$", block, re.M)
    if m:
        for line in block[m.end():].splitlines():
            if not line.strip():
                continue
            item = re.match(r"^\s+-\s+(.*)$", line)
            if not item:
                break  # next top-level key ends the list
            # Entries legitimately carry an inline YAML comment:
            #   - scripts/            # openup-claims.py + tests
            # Keeping it would make the entry match nothing at all.
            value = re.split(r"\s+#", item.group(1), maxsplit=1)[0]
            value = value.strip().strip("\"'")
            if value:
                touches.append(value)
    return task_id, touches


def load_declared(root, changes_dir="docs/changes"):
    """{task_id: set(declared paths)} from change-folder frontmatter."""
    base = root / changes_dir
    if not base.is_dir():
        return {}
    out = {}
    for plan in sorted(base.rglob("plan.md")):
        try:
            text = plan.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        task_id, touches = _frontmatter_touches(text)
        if is_task_id(task_id):
            out.setdefault(task_id, set()).update(touches)
    return out


def load_runlogs(root, log_dir="docs/agent-logs/runs"):
    """{task_id: {duration_minutes, sessions, commits_logged}} from JSONL shards.

    Durations are **paired** (each begin matched to the next end) and summed, so a
    lane spanning two days reports worked time rather than wall-clock span.
    """
    base = root / log_dir
    if not base.is_dir():
        return {}
    events = {}
    for shard in sorted(base.glob("*.jsonl")):
        try:
            lines = shard.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            task_id = rec.get("task_id")
            if not is_task_id(task_id):
                continue
            events.setdefault(task_id, []).append((rec.get("ts"), rec.get("event")))

    out = {}
    for task_id, evs in events.items():
        ordered = sorted((parse_iso(ts), ev, ts) for ts, ev in evs if parse_iso(ts) is not None)
        total, sessions, open_at = 0.0, 0, None
        for epoch, event, _ in ordered:
            if event in BEGIN_EVENTS and open_at is None:
                open_at = epoch
            elif event in END_EVENTS and open_at is not None:
                total += epoch - open_at
                sessions += 1
                open_at = None
        first_ts = ordered[0][2] if ordered else None
        out[task_id] = {
            "duration_minutes": round(total / 60.0, 2) if sessions else None,
            "sessions": sessions,
            "commits_logged": sum(1 for _, ev in evs if ev == "commit"),
            "first_ts": first_ts,
        }
    return out


def _git(root, args):
    try:
        proc = subprocess.run(
            ["git", "-C", str(root)] + args,
            capture_output=True, text=True, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def is_shallow_repo(root):
    """``True``/``False`` if git can answer; ``None`` if ``root`` isn't a git repo.

    A shallow checkout (``git clone --depth N``, the default on most CI
    ``actions/checkout``) attributes the whole pre-boundary tree to the boundary
    commit — T1 in the T-127 baseline corrupted 34/126 tasks this way. The
    analyzer still runs (report-only, degrades independently), but the result
    must be flagged so a downstream consumer can refuse it.
    """
    out = _git(root, ["rev-parse", "--is-shallow-repository"])
    if out is None:
        return None
    return out.strip() == "true"


def load_git(root, task_re=None, unit="task"):
    """{unit_key: {files, commits, first_ts, last_ts}} from ``git log --numstat``.

    ``--no-merges`` avoids double-counting a merge alongside the commits it
    carries; ``--no-renames`` keeps numstat paths plain (a rename reads as a
    delete plus an add, which is the honest signal for co-change anyway).

    Only the **key** varies by unit — every downstream metric is unchanged, which
    is what keeps ``--unit task`` byte-identical to the pre-T-128 output.
    """
    fmt = f"{_REC_SEP}%H{_FLD_SEP}%aI{_FLD_SEP}%s"
    out = _git(root, ["log", "--no-merges", "--no-renames", "--numstat", f"--format={fmt}"])
    if out is None:
        return {}, None

    commits = []  # (sha, subject, iso_date, [paths])
    cur = None
    for line in out.splitlines():
        if line.startswith(_REC_SEP):
            parts = line[1:].split(_FLD_SEP)
            if len(parts) >= 3:
                cur = (parts[0], parts[2], parts[1], [])
                commits.append(cur)
            continue
        if cur is None or not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) == 3 and cols[2]:
            cur[3].append(cols[2])

    def collect(key_of):
        acc = {}
        for sha, subject, date, paths in commits:
            key = key_of(sha, subject)
            if key is None:
                continue
            rec = acc.setdefault(key, {"files": set(), "commits": 0, "dates": []})
            rec["files"].update(paths)
            rec["commits"] += 1
            rec["dates"].append(date)
        return acc

    if unit == "commit":
        # Every non-merge commit is its own unit — the fallback that makes a repo
        # with no task-id convention measurable at all.
        acc, matched = collect(lambda sha, subj: sha[:12]), "commit"
    elif unit == "pr":
        # Commits with no (#N) are dropped rather than each becoming a unit;
        # mixing PR-sized and commit-sized rows would corrupt every median.
        def pr_key(sha, subject):
            m = PR_RE.search(subject)
            return f"#{m.group(1)}" if m else None
        acc, matched = collect(pr_key), "pr"
    else:
        def task_key(pattern):
            def keyer(sha, subject):
                m = pattern.search(subject)
                if not m:
                    return None
                return m.group(1) if is_task_id(m.group(1)) else None
            return keyer

        if task_re is not None:
            acc, matched = collect(task_key(task_re)), "custom"
        else:
            acc, matched = collect(task_key(TASK_RE_BRACKET)), "bracket"
            if not acc:
                acc, matched = collect(task_key(TASK_RE_SCOPE)), "scope"

    for rec in acc.values():
        dates = sorted(rec.pop("dates"))
        rec["first_ts"] = dates[0] if dates else None
        rec["last_ts"] = dates[-1] if dates else None
    return acc, (matched if acc else None)


# Structural snapshots (``--snapshots``) measure *code* shape, so — unlike the
# rest of this module, which is extension-agnostic — they filter to source
# file extensions and flag tests separately. Ported from the reference
# implementation (docs/explorations/2026-07-25-agent-built-repo-decay/method/
# decay.py + snapshots.py) so a snapshot run reproduces its published numbers.
SNAPSHOT_CODE_EXT = (".rb", ".py", ".js", ".ts", ".jsx", ".tsx", ".erb", ".go",
                     ".java", ".rs", ".c", ".cc", ".cpp", ".h", ".css", ".scss",
                     ".sh", ".sql")
SNAPSHOT_TEST_RE = re.compile(r"(^|/)(test|tests|spec|specs)/|_test\.|_spec\.|\.test\.|\.spec\.")


def month_ends(root):
    """Last commit sha of each calendar month, oldest first."""
    out = _git(root, ["log", "--reverse", "--format=%H %aI"])
    if out is None:
        return []
    last = {}
    for line in out.splitlines():
        sha, _, iso = line.partition(" ")
        if sha and iso:
            last[iso[:7]] = sha
    return sorted(last.items())


def tree_sizes(root, sha, excludes, includes):
    """path -> line count for every in-scope, in-extension file at ``sha``."""
    listing = _git(root, ["ls-tree", "-r", "--name-only", sha])
    if listing is None:
        return {}
    paths = [p for p in listing.splitlines()
             if p.endswith(SNAPSHOT_CODE_EXT) and not excluded(p, excludes, includes)]
    if not paths:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input="".join(f"{sha}:{p}\n" for p in paths).encode(),
        capture_output=True,
    )
    stream, pos, sizes, i = proc.stdout, 0, {}, 0
    while pos < len(stream) and i < len(paths):
        nl = stream.find(b"\n", pos)
        if nl < 0:
            break
        header = stream[pos:nl].split()
        if len(header) != 3:  # "missing" line — skip this path
            pos = nl + 1
            i += 1
            continue
        n = int(header[2])
        blob = stream[nl + 1:nl + 1 + n]
        sizes[paths[i]] = blob.count(b"\n") + (0 if blob.endswith(b"\n") or not blob else 1)
        pos = nl + 1 + n + 1
        i += 1
    return sizes


def build_snapshots(root, excludes, includes, depth, threshold=400):
    """One row per calendar month: file/line counts, size percentiles, module
    spread, and test/src line ratio, measured on the tree as it stood then."""
    rows = []
    for month, sha in month_ends(root):
        sizes = tree_sizes(root, sha, excludes, includes)
        if not sizes:
            continue
        vals = sorted(sizes.values())
        test_files = [p for p in sizes if SNAPSHOT_TEST_RE.search(p)]
        src_lines = sum(v for p, v in sizes.items() if not SNAPSHOT_TEST_RE.search(p))
        test_lines = sum(v for p, v in sizes.items() if SNAPSHOT_TEST_RE.search(p))
        mods = {}
        for p in sizes:
            mods[module_of(p, depth)] = mods.get(module_of(p, depth), 0) + 1
        rows.append({
            "month": month,
            "code_files": len(vals),
            "code_lines": sum(vals),
            "med_file_lines": median(vals),
            "p90_file_lines": (round(statistics.quantiles(vals, n=10)[-1], 1)
                               if len(vals) > 10 else None),
            "max_file_lines": vals[-1],
            "files_over_threshold": sum(1 for v in vals if v > threshold),
            "share_over_threshold": round(sum(1 for v in vals if v > threshold) / len(vals), 4),
            "modules": len(mods),
            "files_per_module": round(len(vals) / len(mods), 2) if mods else None,
            "largest_module_files": max(mods.values()) if mods else None,
            "test_files": len(test_files),
            "test_to_src_lines": round(test_lines / src_lines, 3) if src_lines else None,
        })
    return rows


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
def build_tasks(declared, runlogs, gitdata, excludes, depth, unit="task", includes=()):
    """Join the three sources into one ordered per-unit series."""
    # Only TASK keys carry an ordinal. A commit sha of all digits would otherwise
    # parse as one (and an enormous one), scattering the series — so the ordinal
    # is computed for the task unit alone; other units order by date.
    def index_of(t):
        return task_index(t) if unit == "task" else None

    def order_key(t):
        idx = index_of(t)
        date = (gitdata.get(t) or {}).get("first_ts") or (runlogs.get(t) or {}).get("first_ts") or ""
        return (idx if idx is not None else 1 << 30, date, t)

    ids = sorted(set(declared) | set(runlogs) | set(gitdata), key=order_key)
    rows = []
    for task_id in ids:
        dec = {p for p in declared.get(task_id, set()) if not excluded(p, excludes, includes)}
        git_rec = gitdata.get(task_id, {})
        act = {p for p in git_rec.get("files", set()) if not excluded(p, excludes, includes)}
        log_rec = runlogs.get(task_id, {})
        first_ts = git_rec.get("first_ts") or log_rec.get("first_ts")
        # Drift is only defined when both signals exist for this lane.
        d = drift_for(dec, act) if (task_id in declared and task_id in gitdata) else {}
        rows.append({
            "task": task_id,
            "index": index_of(task_id),
            "date": first_ts,
            "month": month_of(first_ts),
            "declared_touches": len(dec) if task_id in declared else None,
            "actual_files": len(act) if task_id in gitdata else None,
            "duration_minutes": log_rec.get("duration_minutes"),
            "commits": git_rec.get("commits", log_rec.get("commits_logged")) or None,
            "modules_declared": len({module_of(p, depth) for p in dec}) or None,
            "modules_actual": len({module_of(p, depth) for p in act}) or None,
            "coverage": d.get("coverage"),
            "drift_jaccard": d.get("jaccard"),
            "_declared": dec,
            "_actual": act,
        })
    return rows


METRIC_KEYS = (
    "declared_touches", "actual_files", "duration_minutes",
    "commits", "modules_actual", "coverage", "drift_jaccard",
)


def _bucket_summary(label, rows):
    summary = {"bucket": label, "n": len(rows)}
    for key in METRIC_KEYS:
        vals = [r[key] for r in rows if r.get(key) is not None]
        summary[key] = median(vals)
        summary[f"{key}_n"] = len(vals)
    return summary


def bucket_by_index(rows, buckets):
    # `rows` arrives already ordered (task ordinal, else date). Units other than
    # `task` have no ordinal, so bucket on position in that series rather than on
    # a parsed index.
    ordered = [r for r in rows if r["index"] is not None] or list(rows)
    if not ordered or buckets < 1:
        return []
    size = max(1, len(ordered) // buckets)
    out = []
    for i in range(0, len(ordered), size):
        chunk = ordered[i:i + size]
        if not chunk:
            continue
        label = f"{chunk[0]['task']}..{chunk[-1]['task']}"
        out.append(_bucket_summary(label, chunk))
    return out


def bucket_by_month(rows):
    months = {}
    for row in rows:
        if row["month"]:
            months.setdefault(row["month"], []).append(row)
    return [_bucket_summary(m, months[m]) for m in sorted(months)]


def drift_for(declared, actual):
    """Compare one lane's declared surface against what it actually changed.

    Declared entries match actual paths by **segment-prefix** (the fence's rule),
    so a directory declaration covers the files beneath it. Metrics:

      coverage  |covered actual| / |actual|            — did the lane declare what it changed
      precision |used declarations| / |declarations|   — did it declare things it never touched
      jaccard   |covered| / (|actual| + |unused declarations|)

    Jaccard generalizes the plain set form: with exact file paths and no
    directory entries it reduces to |A n B| / |A u B| exactly.
    """
    covered = {p for p in actual if any(seg_prefix_collide(p, d) for d in declared)}
    used = {d for d in declared if any(seg_prefix_collide(p, d) for p in actual)}
    unused = declared - used
    union = len(actual) + len(unused)
    return {
        "coverage": round(len(covered) / len(actual), 4) if actual else None,
        "precision": round(len(used) / len(declared), 4) if declared else None,
        "jaccard": round(len(covered) / union, 4) if union else None,
        "undeclared_files": sorted(actual - covered),
        "unused_declarations": sorted(unused),
    }


def compute_drift(rows):
    """Declared vs actual, per task and in aggregate."""
    per_task = []
    for row in rows:
        if row["declared_touches"] is None or row["actual_files"] is None:
            continue
        dec, act = row["_declared"], row["_actual"]
        if not dec and not act:
            continue
        d = drift_for(dec, act)
        per_task.append({
            "task": row["task"],
            "declared": len(dec),
            "actual": len(act),
            "coverage": d["coverage"],
            "precision": d["precision"],
            "jaccard": d["jaccard"],
            "undeclared": len(d["undeclared_files"]),
            "undeclared_files": d["undeclared_files"],
            "unused_declarations": len(d["unused_declarations"]),
        })
    return {
        "tasks_with_both": len(per_task),
        "median_coverage": median([p["coverage"] for p in per_task]),
        "median_precision": median([p["precision"] for p in per_task]),
        "median_jaccard": median([p["jaccard"] for p in per_task]),
        "median_undeclared": median([p["undeclared"] for p in per_task]),
        "per_task": per_task,
    }


def compute_coupling(graph, min_support, top, depth, max_files):
    """Co-change support / Jaccard / lift over file pairs.

    ``graph`` is {task: set(files)}. Tasks above ``max_files`` are skipped (a
    500-file task contributes 124k pairs of nothing) and **reported**, never
    silently dropped.
    """
    usable = {t: fs for t, fs in graph.items() if len(fs) >= 2}
    skipped = sorted(t for t, fs in usable.items() if len(fs) > max_files)
    usable = {t: fs for t, fs in usable.items() if len(fs) <= max_files}

    n = len(usable)
    if n == 0:
        return {"tasks": 0, "pairs": 0, "skipped_tasks": skipped, "top": []}

    freq, pair_support = {}, {}
    for files in usable.values():
        ordered = sorted(files)
        for path in ordered:
            freq[path] = freq.get(path, 0) + 1
        for a, b in combinations(ordered, 2):
            pair_support[(a, b)] = pair_support.get((a, b), 0) + 1

    pairs = []
    for (a, b), support in pair_support.items():
        if support < min_support:
            continue
        fa, fb = freq[a], freq[b]
        pairs.append({
            "a": a,
            "b": b,
            "support": support,
            "jaccard": round(support / (fa + fb - support), 4),
            "lift": round((support * n) / (fa * fb), 3),
            "cross_module": module_of(a, depth) != module_of(b, depth),
        })
    pairs.sort(key=lambda p: (-p["support"], -p["jaccard"], p["a"], p["b"]))
    return {
        "tasks": n,
        "pairs": len(pairs),
        "skipped_tasks": skipped,
        "cross_module_pairs": sum(1 for p in pairs if p["cross_module"]),
        "top": pairs[:top],
    }


def bucket_commits_by_era(root, excludes, includes, n):
    """N equal-commit-count chronological eras, each a {commit: files} graph
    ready for ``compute_coupling()``. Independent of ``--unit`` — era slicing
    is always per-commit, the same reference-implementation shape as
    ``docs/explorations/2026-07-25-agent-built-repo-decay/method/coupling_trend.py``.
    """
    fmt = f"{_REC_SEP}%H{_FLD_SEP}%aI{_FLD_SEP}%s"
    out = _git(root, ["log", "--reverse", "--no-merges", "--no-renames", "--numstat", f"--format={fmt}"])
    if out is None or n < 1:
        return []

    commits, cur = [], None
    for line in out.splitlines():
        if line.startswith(_REC_SEP):
            parts = line[1:].split(_FLD_SEP)
            if len(parts) >= 2:
                cur = {"sha": parts[0], "date": parts[1], "files": []}
                commits.append(cur)
            continue
        if cur is None or not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) == 3 and cols[2] and not excluded(cols[2], excludes, includes):
            cur["files"].append(cols[2])
    commits = [c for c in commits if c["files"]]
    if not commits:
        return []

    size = max(1, len(commits) // n)
    eras = []
    for i in range(0, len(commits), size):
        chunk = commits[i:i + size]
        if not chunk:
            continue
        label = f"{chunk[0]['date'][:10]}..{chunk[-1]['date'][:10]}"
        graph = {c["sha"][:12]: set(c["files"]) for c in chunk}
        eras.append((label, graph))
    return eras


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def build_report(root, args):
    excludes = list(args.exclude) if args.no_default_excludes else list(DEFAULT_EXCLUDES) + list(args.exclude)
    includes = list(args.include)
    task_re = re.compile(args.task_pattern) if args.task_pattern else None

    unit = getattr(args, "unit", "task")
    runlogs = load_runlogs(root, args.log_dir)
    gitdata, matched_by = load_git(root, task_re, unit)
    # A declared surface exists per TASK only. Under another unit there is nothing
    # legitimate to compare a commit's diff against, so drift reports no data
    # rather than inventing one.
    declared = load_declared(root, args.changes_dir) if unit == "task" else {}

    rows = build_tasks(declared, runlogs, gitdata, excludes, args.module_depth, unit, includes)

    declared_graph = {r["task"]: r["_declared"] for r in rows if r["declared_touches"] is not None}
    actual_graph = {r["task"]: r["_actual"] for r in rows if r["actual_files"] is not None}

    report = {
        "sources": {
            "unit": unit,
            "declared_tasks": len(declared),
            "runlog_tasks": len(runlogs),
            "git_tasks": len(gitdata),
            "git_id_pattern": matched_by,
            "excludes": excludes,
            "includes": includes,
            "module_depth": args.module_depth,
            "min_support": args.min_support,
            "shallow": is_shallow_repo(root),
        },
        "tasks": [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
        "cost": {
            "by_index": bucket_by_index(rows, args.buckets),
            "by_month": bucket_by_month(rows),
        },
        "drift": compute_drift(rows),
        "coupling": {
            "declared": compute_coupling(
                declared_graph, args.min_support, args.top, args.module_depth, args.max_files),
            "actual": compute_coupling(
                actual_graph, args.min_support, args.top, args.module_depth, args.max_files),
        },
    }

    if args.snapshots:
        report["snapshots"] = build_snapshots(root, excludes, includes, args.module_depth)

    if args.by_era:
        report["coupling"]["by_era"] = [
            {
                "era": label,
                **compute_coupling(graph, args.min_support, args.top, args.module_depth, args.max_files),
            }
            for label, graph in bucket_commits_by_era(root, excludes, includes, args.by_era)
        ]

    return report


def _fmt(value):
    return "-" if value is None else str(value)


def render_text(report, root):
    src = report["sources"]
    out = []
    add = out.append

    unit = src.get("unit", "task")
    add(f"OpenUP entropy report — {root}")
    add("=" * 72)
    add(f"unit of work: {unit}"
        + ("" if unit == "task" else "   (declared-surface drift is task-only; "
                                     "not comparable with a task-unit report)"))
    add(f"sources: declared={src['declared_tasks']} tasks · runlogs={src['runlog_tasks']} tasks "
        f"· git={src['git_tasks']} {unit}s (id pattern: {_fmt(src['git_id_pattern'])})")
    add(f"includes: {', '.join(src['includes']) if src.get('includes') else '(everything)'}")
    add(f"excludes: {', '.join(src['excludes']) if src['excludes'] else '(none)'}")
    add(f"module depth: {src['module_depth']} · min support: {src['min_support']}")
    add("")

    if not report["tasks"]:
        add("no tasks discovered — nothing to report")
        return "\n".join(out)

    for title, key in (("Cost by task-index window", "by_index"), ("Cost by month", "by_month")):
        buckets = report["cost"][key]
        add(title)
        add("-" * 72)
        if not buckets:
            add("  no data")
        else:
            add(f"  {'bucket':<24}{'n':>4}{'declared':>10}{'actual':>9}"
                f"{'min':>8}{'commits':>9}{'modules':>9}{'coverage':>10}{'jaccard':>9}")
            for b in buckets:
                add(f"  {b['bucket']:<24}{b['n']:>4}{_fmt(b['declared_touches']):>10}"
                    f"{_fmt(b['actual_files']):>9}{_fmt(b['duration_minutes']):>8}"
                    f"{_fmt(b['commits']):>9}{_fmt(b['modules_actual']):>9}"
                    f"{_fmt(b['coverage']):>10}{_fmt(b['drift_jaccard']):>9}")
        add("")

    drift = report["drift"]
    add("Declared vs actual drift")
    add("-" * 72)
    if not drift["tasks_with_both"]:
        add("  no data (no task has both a declared surface and matched commits)")
    else:
        add(f"  tasks with both signals : {drift['tasks_with_both']}")
        add(f"  median coverage         : {_fmt(drift['median_coverage'])}"
            "   (share of changed files that were declared)")
        add(f"  median precision        : {_fmt(drift['median_precision'])}"
            "   (share of declarations that were used)")
        add(f"  median Jaccard          : {_fmt(drift['median_jaccard'])}")
        add(f"  median undeclared files : {_fmt(drift['median_undeclared'])}")
        worst = sorted(drift["per_task"], key=lambda p: (p["coverage"] or 0, p["task"]))[:5]
        if worst:
            add("  lowest-coverage tasks:")
            for p in worst:
                add(f"    {p['task']:<10} coverage={_fmt(p['coverage']):<8}"
                    f"declared={p['declared']:<4} actual={p['actual']:<4} undeclared={p['undeclared']}")
    add("")

    for label in ("declared", "actual"):
        cp = report["coupling"][label]
        add(f"Co-change coupling — {label} graph")
        add("-" * 72)
        if not cp["tasks"]:
            add("  no data (no task contributes 2+ files to this graph)")
        elif not cp["top"]:
            add(f"  {cp['tasks']} tasks, no pair reaches min support {report['sources']['min_support']}")
        else:
            add(f"  {cp['tasks']} tasks · {cp['pairs']} pairs at/over min support "
                f"· {cp['cross_module_pairs']} cross-module")
            add(f"  {'sup':>4}{'jacc':>8}{'lift':>8}  {'x':^3} pair")
            for p in cp["top"]:
                flag = "!" if p["cross_module"] else " "
                add(f"  {p['support']:>4}{p['jaccard']:>8}{p['lift']:>8}  {flag:^3} {p['a']}")
                add(f"  {'':>20}      {p['b']}")
        if cp["skipped_tasks"]:
            add(f"  skipped (over --max-files): {', '.join(cp['skipped_tasks'])}")
        add("")

    if "snapshots" in report:
        add("Structural snapshots (month-end)")
        add("-" * 72)
        rows = report["snapshots"]
        if not rows:
            add("  no data")
        else:
            add(f"  {'month':<9}{'files':>7}{'lines':>9}{'med':>7}{'p90':>7}{'max':>7}"
                f"{'share>400':>11}{'mods':>6}{'test/src':>10}")
            for r in rows:
                add(f"  {r['month']:<9}{r['code_files']:>7}{r['code_lines']:>9}"
                    f"{_fmt(r['med_file_lines']):>7}{_fmt(r['p90_file_lines']):>7}"
                    f"{r['max_file_lines']:>7}{_fmt(r['share_over_threshold']):>11}"
                    f"{r['modules']:>6}{_fmt(r['test_to_src_lines']):>10}")
        add("")

    if "by_era" in report["coupling"]:
        add("Co-change coupling by era — actual graph")
        add("-" * 72)
        eras = report["coupling"]["by_era"]
        if not eras:
            add("  no data")
        else:
            add(f"  {'era':<24}{'commits':>8}{'pairs':>7}{'x-module':>9}")
            for e in eras:
                add(f"  {e['era']:<24}{e['tasks']:>8}{e['pairs']:>7}{e['cross_module_pairs']:>9}")
        add("")

    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report-only codebase-entropy metrics from OpenUP telemetry + git history.",
    )
    parser.add_argument("--repo", default=".", help="repository to analyze (default: cwd)")
    parser.add_argument("--unit", choices=UNITS, default="task",
                        help="unit of work every metric is keyed on (default: task). "
                             "'commit' measures repos with no task-id convention; "
                             "'pr' groups by a trailing (#N). Never inferred — a report "
                             "is only comparable with another of the same unit.")
    parser.add_argument("--json", action="store_true", help="emit the JSON payload instead of text")
    parser.add_argument("--buckets", type=int, default=4, help="task-index buckets (default: 4)")
    parser.add_argument("--top", type=int, default=20, help="coupling pairs to list (default: 20)")
    parser.add_argument("--min-support", type=int, default=3,
                        help="minimum co-change count for a pair (default: 3)")
    parser.add_argument("--module-depth", type=int, default=1,
                        help="path segments defining a module (default: 1)")
    parser.add_argument("--max-files", type=int, default=60,
                        help="skip tasks touching more files than this in the coupling graph "
                             "(default: 60; skipped tasks are reported)")
    parser.add_argument("--include", action="append", default=[],
                        help="allowlist fnmatch pattern (repeatable); when given, only "
                             "matching paths are in scope, applied BEFORE --exclude "
                             "(default: everything is in scope). The fix for repos that "
                             "vendor this framework's own scripts/ tree wholesale — "
                             "e.g. --include 'app/*' to keep vendored code out of every metric.")
    parser.add_argument("--exclude", action="append", default=[],
                        help="extra fnmatch pattern to exclude (repeatable)")
    parser.add_argument("--no-default-excludes", action="store_true",
                        help="drop the built-in process-noise exclusions")
    parser.add_argument("--snapshots", action="store_true",
                        help="add a month-end structural series: file-count/line-count "
                             "percentiles, share of files over 400 lines, module spread, "
                             "test/src ratio, measured on the tree as it stood each month-end")
    parser.add_argument("--by-era", type=int, default=None, metavar="N",
                        help="slice actual-graph coupling into N equal-commit-count "
                             "chronological eras, reported alongside the pooled "
                             "whole-history coupling (default: off)")
    parser.add_argument("--changes-dir", default="docs/changes", help="change-folder root")
    parser.add_argument("--log-dir", default="docs/agent-logs/runs", help="run-log shard dir")
    parser.add_argument("--task-pattern", default=None,
                        help="regex with one group capturing the task id in a commit subject "
                             "(default: bracketed tag, falling back to conventional-commit scope)")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return EXIT_NO_DATA

    report = build_report(root, args)
    src = report["sources"]
    if not (src["declared_tasks"] or src["runlog_tasks"] or src["git_tasks"]):
        print(f"error: no telemetry found in {root} "
              "(no change folders, no run logs, no task-tagged commits)", file=sys.stderr)
        return EXIT_NO_DATA

    if src["shallow"]:
        print(
            "*** WARNING: shallow clone detected — history is truncated, so the "
            "boundary commit's diff attributes the ENTIRE pre-boundary tree to "
            "itself (falsely inflating that task's cost/coupling numbers). "
            "Run `git fetch --unshallow` and re-run for a reliable report. ***",
            file=sys.stderr,
        )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report, root))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

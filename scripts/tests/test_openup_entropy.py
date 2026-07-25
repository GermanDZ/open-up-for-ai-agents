#!/usr/bin/env python3
"""Unit tests for scripts/openup-entropy.py (T-127).

Run with either:
    python3 -m unittest scripts.tests.test_openup_entropy
    python3 scripts/tests/test_openup_entropy.py

Hermetic: every test builds a throwaway git repo under a temp dir with its own
change folders, run-log shards, and commit history, so nothing depends on the
live repo's telemetry. The analyzer is exercised through its CLI (the way a
maintainer runs it) and through its importable functions (for the metric math).
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-entropy.py"

OK, USAGE, NO_DATA = 0, 2, 3

_spec = importlib.util.spec_from_file_location("openup_entropy", SCRIPT)
entropy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(entropy)


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x",
             "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
             "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(cwd)},
    )


class Fixture:
    """Throwaway repo with change folders, run logs, and task-tagged commits."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp())
        git(self.dir, "init", "-q", "-b", "main")

    def declare(self, task, touches, folder=None):
        d = self.dir / "docs" / "changes" / (folder or task)
        d.mkdir(parents=True, exist_ok=True)
        body = "".join(f"  - {t}\n" for t in touches)
        (d / "plan.md").write_text(
            f"---\nid: {task}\ntitle: \"x\"\nstatus: done\ntouches:\n{body}---\n\n# {task}\n",
            encoding="utf-8",
        )

    def log(self, task, records):
        d = self.dir / "docs" / "agent-logs" / "runs"
        d.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps({"task_id": task, **r}) for r in records]
        (d / f"2026-06-01-{task}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def commit(self, task, files, subject=None, date="2026-06-01T10:00:00+00:00"):
        for rel in files:
            p = self.dir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text((p.read_text() if p.exists() else "") + "x\n", encoding="utf-8")
        git(self.dir, "add", "-A")
        msg = subject or f"feat({task}): work [{task}]"
        res = subprocess.run(
            ["git", "commit", "-q", "-m", msg], cwd=self.dir,
            capture_output=True, text=True,
            env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x",
                 "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
                 "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
                 "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.dir)},
        )
        assert res.returncode == 0, res.stderr

    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.dir), *args],
            capture_output=True, text=True,
        )

    def payload(self, *args):
        res = self.run("--json", *args)
        assert res.returncode == OK, res.stderr
        return json.loads(res.stdout)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class FrontmatterTests(unittest.TestCase):
    """The declared surface is parsed the way lanes actually write it."""

    def test_inline_comment_is_stripped(self):
        text = ('---\nid: T-009\ntouches:\n'
                '  - scripts/            # claims + tests\n'
                '  - docs-eng-process/\n---\n')
        task, touches = entropy._frontmatter_touches(text)
        self.assertEqual(task, "T-009")
        self.assertEqual(touches, ["scripts/", "docs-eng-process/"])

    def test_list_ends_at_next_key(self):
        text = '---\nid: T-002\ntouches:\n  - a.py\ndefer-until: "later"\n---\n'
        _, touches = entropy._frontmatter_touches(text)
        self.assertEqual(touches, ["a.py"])

    def test_no_frontmatter_is_empty(self):
        self.assertEqual(entropy._frontmatter_touches("# just a heading\n"), (None, []))


class DriftMathTests(unittest.TestCase):
    """Requirement 3 — prefix semantics, not string equality."""

    def test_partial_overlap_scenario(self):
        # Spec scenario: declared [a.py, b.py], actual [a.py, c.py].
        d = entropy.drift_for({"a.py", "b.py"}, {"a.py", "c.py"})
        self.assertEqual(d["jaccard"], 0.3333)
        self.assertEqual(d["coverage"], 0.5)
        self.assertEqual(d["precision"], 0.5)
        self.assertEqual(d["undeclared_files"], ["c.py"])

    def test_directory_declaration_covers_children(self):
        # Spec scenario: declaring `src/` covers src/a.py and src/b.py.
        d = entropy.drift_for({"src/"}, {"src/a.py", "src/b.py"})
        self.assertEqual(d["coverage"], 1.0)
        self.assertEqual(d["undeclared_files"], [])
        self.assertEqual(d["precision"], 1.0)

    def test_sibling_directory_does_not_match(self):
        # seg_prefix_collide must not treat `src` as a prefix of `srcgen/`.
        d = entropy.drift_for({"src/"}, {"srcgen/a.py"})
        self.assertEqual(d["coverage"], 0.0)
        self.assertEqual(d["undeclared_files"], ["srcgen/a.py"])

    def test_unused_declaration_lowers_precision_and_jaccard(self):
        d = entropy.drift_for({"a.py", "never.py"}, {"a.py"})
        self.assertEqual(d["coverage"], 1.0)
        self.assertEqual(d["precision"], 0.5)
        self.assertEqual(d["jaccard"], 0.5)  # 1 covered / (1 actual + 1 unused)
        self.assertEqual(d["unused_declarations"], ["never.py"])


class CouplingMathTests(unittest.TestCase):
    """Requirement 4 — support / Jaccard / lift and the cross-module flag."""

    def test_pair_metrics_and_cross_module_flag(self):
        # Spec scenario: two files co-occur in 5 of 10 tasks, each only in those 5.
        graph = {}
        for i in range(5):
            graph[f"T-{i:03d}"] = {"scripts/a.py", "docs/b.md"}
        for i in range(5, 10):
            graph[f"T-{i:03d}"] = {"other/c.py", "other/d.py"}
        cp = entropy.compute_coupling(graph, min_support=3, top=20, depth=1, max_files=60)
        pair = next(p for p in cp["top"] if p["a"] == "docs/b.md")
        self.assertEqual(pair["support"], 5)
        self.assertEqual(pair["jaccard"], 1.0)
        self.assertEqual(pair["lift"], 2.0)
        self.assertTrue(pair["cross_module"])

    def test_min_support_filters_noise(self):
        graph = {"T-001": {"a.py", "b.py"}, "T-002": {"a.py", "b.py"}}
        self.assertEqual(entropy.compute_coupling(graph, 3, 20, 1, 60)["top"], [])
        self.assertEqual(len(entropy.compute_coupling(graph, 2, 20, 1, 60)["top"]), 1)

    def test_oversized_task_is_skipped_and_reported(self):
        graph = {"T-001": {f"f{i}.py" for i in range(10)}}
        cp = entropy.compute_coupling(graph, 1, 20, 1, max_files=5)
        self.assertEqual(cp["skipped_tasks"], ["T-001"])
        self.assertEqual(cp["tasks"], 0)


class ReportTests(unittest.TestCase):
    """End-to-end over a hermetic git fixture."""

    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_cost_series_joins_three_sources(self):
        # Requirement 1 — one record per task, absent fields null (not 0).
        self.fx.declare("T-001", ["src/a.py", "src/b.py"])
        self.fx.log("T-001", [
            {"event": "session_begin", "ts": "2026-06-01T10:00:00Z"},
            {"event": "session_end", "ts": "2026-06-01T10:30:00Z"},
        ])
        self.fx.commit("T-001", ["src/a.py"])
        row = next(t for t in self.fx.payload()["tasks"] if t["task"] == "T-001")
        self.assertEqual(row["declared_touches"], 2)
        self.assertEqual(row["actual_files"], 1)
        self.assertEqual(row["duration_minutes"], 30.0)
        self.assertEqual(row["commits"], 1)

    def test_absent_metric_is_null_not_zero(self):
        # A task with only a declared surface must not report 0 commits.
        self.fx.declare("T-002", ["src/a.py"])
        self.fx.commit("T-999", ["seed.txt"], subject="chore: seed")
        row = next(t for t in self.fx.payload()["tasks"] if t["task"] == "T-002")
        self.assertIsNone(row["actual_files"])
        self.assertIsNone(row["commits"])
        self.assertIsNone(row["duration_minutes"])

    def test_buckets_by_index_and_month(self):
        # Requirement 2 — both bucketings, medians over present values only.
        for i in range(1, 13):
            month = f"2026-0{4 + (i - 1) // 4}"
            self.fx.declare(f"T-{i:03d}", [f"src/f{i}.py"])
            self.fx.commit(f"T-{i:03d}", [f"src/f{i}.py"], date=f"{month}-02T10:00:00+00:00")
        cost = self.fx.payload("--buckets", "4")["cost"]
        self.assertEqual(len(cost["by_index"]), 4)
        self.assertEqual([b["bucket"] for b in cost["by_month"]], ["2026-04", "2026-05", "2026-06"])
        self.assertTrue(all(b["n"] == 3 for b in cost["by_index"]))

    def test_drift_is_bucketed_alongside_cost(self):
        # Requirement 3a — buckets carry median coverage / jaccard.
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        bucket = self.fx.payload("--buckets", "1")["cost"]["by_index"][0]
        self.assertEqual(bucket["coverage"], 1.0)
        self.assertEqual(bucket["drift_jaccard"], 1.0)

    def test_directory_declaration_scores_full_coverage_end_to_end(self):
        self.fx.declare("T-001", ["src/"])
        self.fx.commit("T-001", ["src/a.py", "src/b.py"])
        drift = self.fx.payload()["drift"]
        self.assertEqual(drift["median_coverage"], 1.0)
        self.assertEqual(drift["median_undeclared"], 0)

    def test_default_excludes_drop_process_noise(self):
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py", "docs/roadmap.md"])
        # By default only src/a.py survives: the derived view docs/roadmap.md and
        # the lane's own docs/changes/T-001/plan.md are process noise every lane
        # touches by construction.
        row = next(t for t in self.fx.payload()["tasks"] if t["task"] == "T-001")
        self.assertEqual(row["actual_files"], 1)
        # Opting out restores them, so the exclusion is what removed them.
        row = next(t for t in self.fx.payload("--no-default-excludes")["tasks"]
                   if t["task"] == "T-001")
        self.assertEqual(row["actual_files"], 3)

    def test_conventional_scope_fallback_when_no_bracket_tag(self):
        self.fx.commit("T-001", ["src/a.py"], subject="feat(T-001): no trailer here")
        payload = self.fx.payload()
        self.assertEqual(payload["sources"]["git_id_pattern"], "scope")
        self.assertEqual(payload["sources"]["git_tasks"], 1)

    def test_degrades_to_git_only(self):
        # Requirement 5 — no change folders: exit 0, declared sections empty.
        self.fx.commit("T-001", ["src/a.py", "src/b.py"])
        res = self.fx.run()
        self.assertEqual(res.returncode, OK)
        payload = self.fx.payload()
        self.assertEqual(payload["sources"]["declared_tasks"], 0)
        self.assertEqual(payload["sources"]["git_tasks"], 1)
        self.assertEqual(payload["drift"]["tasks_with_both"], 0)
        self.assertIn("no data", res.stdout)

    def test_degrades_to_declared_only(self):
        self.fx.declare("T-001", ["src/a.py", "src/b.py"])
        payload = self.fx.payload()
        self.assertEqual(payload["sources"]["git_tasks"], 0)
        self.assertIsNone(payload["sources"]["git_id_pattern"])
        self.assertEqual(payload["coupling"]["actual"]["tasks"], 0)
        self.assertEqual(payload["coupling"]["declared"]["tasks"], 1)

    def test_empty_repo_exits_no_data(self):
        res = self.fx.run()
        self.assertEqual(res.returncode, NO_DATA)
        self.assertIn("no telemetry", res.stderr)

    def test_json_output_is_byte_identical_across_runs(self):
        # Requirement 6 — determinism.
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        first = self.fx.run("--json").stdout
        second = self.fx.run("--json").stdout
        self.assertEqual(first, second)

    def test_report_writes_nothing_to_the_analyzed_repo(self):
        # Requirement 7 — report-only invariant.
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        before = git(self.fx.dir, "status", "--porcelain", "--untracked-files=all").stdout
        self.fx.run()
        self.fx.run("--json")
        after = git(self.fx.dir, "status", "--porcelain", "--untracked-files=all").stdout
        self.assertEqual(before, after)
        self.assertFalse((self.fx.dir / ".openup").exists())

    def test_paired_sessions_sum_worked_time(self):
        # Two sessions on separate days sum to 45 min, not a 24h wall-clock span.
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.log("T-001", [
            {"event": "session_begin", "ts": "2026-06-01T10:00:00Z"},
            {"event": "session_end", "ts": "2026-06-01T10:30:00Z"},
            {"event": "session_begin", "ts": "2026-06-02T10:00:00Z"},
            {"event": "session_end", "ts": "2026-06-02T10:15:00Z"},
        ])
        row = next(t for t in self.fx.payload()["tasks"] if t["task"] == "T-001")
        self.assertEqual(row["duration_minutes"], 45.0)
        self.assertEqual(row["index"], 1)


class ShallowCloneTests(unittest.TestCase):
    """F5 — a truncated history is flagged, never silently trusted."""

    def setUp(self):
        self.fx = Fixture()
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        self.fx.declare("T-002", ["src/b.py"])
        self.fx.commit("T-002", ["src/b.py"])

    def tearDown(self):
        self.fx.cleanup()

    def test_full_clone_reports_not_shallow(self):
        self.assertFalse(self.fx.payload()["sources"]["shallow"])

    def test_non_git_dir_reports_shallow_as_null(self):
        plain = Path(tempfile.mkdtemp())
        try:
            self.assertIsNone(entropy.is_shallow_repo(plain))
        finally:
            shutil.rmtree(plain, ignore_errors=True)

    def test_shallow_clone_is_flagged_and_warns(self):
        shallow_dir = Path(tempfile.mkdtemp())
        try:
            cloned = subprocess.run(
                ["git", "clone", "-q", "--depth", "1", f"file://{self.fx.dir}", str(shallow_dir)],
                capture_output=True, text=True,
            )
            assert cloned.returncode == 0, cloned.stderr
            res = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(shallow_dir), "--json"],
                capture_output=True, text=True,
            )
            self.assertEqual(res.returncode, OK)
            payload = json.loads(res.stdout)
            self.assertTrue(payload["sources"]["shallow"])
            self.assertIn("shallow clone detected", res.stderr)
            self.assertIn("git fetch --unshallow", res.stderr)
        finally:
            shutil.rmtree(shallow_dir, ignore_errors=True)

    def test_text_mode_also_warns_on_stderr(self):
        shallow_dir = Path(tempfile.mkdtemp())
        try:
            cloned = subprocess.run(
                ["git", "clone", "-q", "--depth", "1", f"file://{self.fx.dir}", str(shallow_dir)],
                capture_output=True, text=True,
            )
            assert cloned.returncode == 0, cloned.stderr
            res = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(shallow_dir)],
                capture_output=True, text=True,
            )
            self.assertEqual(res.returncode, OK)
            self.assertIn("shallow clone detected", res.stderr)
            self.assertNotIn("shallow clone detected", res.stdout)
        finally:
            shutil.rmtree(shallow_dir, ignore_errors=True)


class UnitOfWorkTests(unittest.TestCase):
    """T-128 — a task is one unit of work; commits and PRs are others."""

    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_default_unit_matches_explicit_task(self):
        # R1 — the default must not drift from `--unit task`.
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        self.assertEqual(self.fx.run("--json").stdout,
                         self.fx.run("--unit", "task", "--json").stdout)
        self.assertEqual(self.fx.payload()["sources"]["unit"], "task")

    def test_commit_unit_measures_a_repo_with_no_task_ids(self):
        # R2 — the case that exits 3 under the task unit.
        # src/a.py and src/b.py change together 4 times (real co-change); each
        # commit also touches a unique file, so the graph isn't degenerate.
        for i in range(4):
            self.fx.commit("x", ["src/a.py", "src/b.py", f"src/only{i}.py"],
                           subject=f"Bump to 1.{i}")
        self.assertEqual(self.fx.run().returncode, NO_DATA)  # task unit: nothing
        payload = self.fx.payload("--unit", "commit", "--min-support", "3")
        self.assertEqual(payload["sources"]["unit"], "commit")
        self.assertEqual(payload["sources"]["git_tasks"], 4)
        top = payload["coupling"]["actual"]["top"]
        self.assertEqual([(p["a"], p["b"], p["support"]) for p in top],
                         [("src/a.py", "src/b.py", 4)])

    def test_pr_unit_groups_by_number_and_drops_untagged(self):
        # R3 — two commits share #7; the untagged one is not its own unit.
        self.fx.commit("x", ["src/a.py"], subject="Add a thing (#7)")
        self.fx.commit("x", ["src/b.py"], subject="Fix that thing (#7)")
        self.fx.commit("x", ["src/c.py"], subject="Untagged work")
        payload = self.fx.payload("--unit", "pr")
        self.assertEqual(payload["sources"]["git_tasks"], 1)
        row = payload["tasks"][0]
        self.assertEqual(row["task"], "#7")
        self.assertEqual(row["actual_files"], 2)

    def test_unit_is_named_in_header_and_payload(self):
        # R4 — reports of different units must never look silently comparable.
        self.fx.commit("x", ["src/a.py"], subject="Plain subject")
        res = self.fx.run("--unit", "commit")
        self.assertIn("unit of work: commit", res.stdout)
        self.assertEqual(self.fx.payload("--unit", "commit")["sources"]["unit"], "commit")

    def test_drift_is_task_only(self):
        # R5 — a commit has no declared surface; don't invent one.
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        payload = self.fx.payload("--unit", "commit")
        self.assertEqual(payload["drift"]["tasks_with_both"], 0)
        self.assertEqual(payload["sources"]["declared_tasks"], 0)
        self.assertIn("no data", self.fx.run("--unit", "commit").stdout)

    def test_all_digit_sha_does_not_parse_as_a_task_ordinal(self):
        # Regression: an all-digit sha parsed as an enormous ordinal, which
        # collapsed the index buckets to the handful of such commits.
        for i in range(6):
            self.fx.commit("x", [f"src/f{i}.py"], subject=f"Commit {i}")
        payload = self.fx.payload("--unit", "commit", "--buckets", "3")
        self.assertTrue(all(r["index"] is None for r in payload["tasks"]))
        self.assertEqual(len(payload["cost"]["by_index"]), 3)
        self.assertTrue(all(b["n"] == 2 for b in payload["cost"]["by_index"]))


class AllowlistTests(unittest.TestCase):
    """T-132 Requirement 1 — --include is an allowlist applied before --exclude."""

    def test_excluded_precedence(self):
        # includes present + no match -> excluded even with an empty blocklist.
        self.assertTrue(entropy.excluded("scripts/x.py", [], includes=["app/*"]))
        # includes present + match -> not excluded (blocklist still applies too).
        self.assertFalse(entropy.excluded("app/x.py", [], includes=["app/*"]))
        # includes absent -> unchanged blocklist-only behavior (pre-T-132 contract).
        self.assertFalse(entropy.excluded("scripts/x.py", []))
        self.assertTrue(entropy.excluded("scripts/x.py", ["scripts/*"]))


class AllowlistReportTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_include_scopes_out_vendored_framework_code(self):
        # Exploration trap T4: 100% of scripts/ is vendored framework code in
        # the app repos; --include 'app/*' must exclude it from every metric —
        # the fix that reversed the Project A conclusion.
        self.fx.declare("T-001", ["app/real.py", "scripts/vendored.py"])
        self.fx.commit("T-001", ["app/real.py", "scripts/vendored.py"])
        payload = self.fx.payload("--include", "app/*", "--no-default-excludes")
        self.assertEqual(payload["sources"]["includes"], ["app/*"])
        row = next(t for t in payload["tasks"] if t["task"] == "T-001")
        self.assertEqual(row["declared_touches"], 1)
        self.assertEqual(row["actual_files"], 1)

    def test_include_absent_preserves_pre_t132_default(self):
        self.fx.declare("T-001", ["src/a.py"])
        self.fx.commit("T-001", ["src/a.py"])
        payload = self.fx.payload()
        self.assertEqual(payload["sources"]["includes"], [])
        self.assertEqual(payload["sources"]["declared_tasks"], 1)


class SnapshotsTests(unittest.TestCase):
    """T-132 Requirement 2 — month-end structural series, off by default."""

    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_snapshots_absent_by_default(self):
        self.fx.commit("T-001", ["src/a.py"])
        self.assertNotIn("snapshots", self.fx.payload())

    def test_month_end_series_and_size_threshold(self):
        # 12 one-line files (p90 needs >10) plus one 410-line file, committed
        # in June — the tree at month-end reflects everything by then.
        files = [f"src/f{i}.py" for i in range(12)]
        self.fx.commit("T-006", files, date="2026-06-05T10:00:00+00:00")
        big = self.fx.dir / "src" / "big.py"
        big.write_text("x\n" * 410, encoding="utf-8")
        git(self.fx.dir, "add", "-A")
        subprocess.run(
            ["git", "commit", "-q", "-m", "feat(T-006): add a large file [T-006]"],
            cwd=self.fx.dir, capture_output=True, text=True,
            env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x",
                 "GIT_AUTHOR_DATE": "2026-06-06T10:00:00+00:00",
                 "GIT_COMMITTER_DATE": "2026-06-06T10:00:00+00:00",
                 "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
                 "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.fx.dir)},
        )
        rows = self.fx.payload("--snapshots")["snapshots"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["month"], "2026-06")
        self.assertEqual(row["code_files"], 13)
        self.assertIsNotNone(row["p90_file_lines"])
        self.assertEqual(row["max_file_lines"], 410)
        self.assertEqual(row["files_over_threshold"], 1)

    def test_default_excludes_apply_to_snapshots(self):
        self.fx.commit("T-001", ["src/a.py", ".openup/cache.py"], date="2026-06-01T10:00:00+00:00")
        row = self.fx.payload("--snapshots")["snapshots"][0]
        self.assertEqual(row["code_files"], 1)


class ByEraTests(unittest.TestCase):
    """T-132 Requirement 3 — coupling sliced into N equal-commit-count eras."""

    def setUp(self):
        self.fx = Fixture()

    def tearDown(self):
        self.fx.cleanup()

    def test_by_era_absent_by_default(self):
        self.fx.commit("x", ["a.py", "b.py"], subject="c0")
        self.assertNotIn("by_era", self.fx.payload("--unit", "commit")["coupling"])

    def test_two_equal_eras_isolate_coupling(self):
        # First 4 commits co-change a.py/b.py; next 4 co-change c.py/d.py —
        # pooled coupling would show both pairs, but each era must see only
        # its own chunk's commits.
        for i in range(4):
            self.fx.commit("x", ["a.py", "b.py"], subject=f"era1-{i}",
                            date=f"2026-06-0{i + 1}T10:00:00+00:00")
        for i in range(4):
            self.fx.commit("x", ["c.py", "d.py"], subject=f"era2-{i}",
                            date=f"2026-07-0{i + 1}T10:00:00+00:00")
        eras = self.fx.payload("--unit", "commit", "--by-era", "2",
                               "--min-support", "3")["coupling"]["by_era"]
        self.assertEqual(len(eras), 2)
        pair1 = eras[0]["top"][0]
        self.assertEqual({pair1["a"], pair1["b"]}, {"a.py", "b.py"})
        pair2 = eras[1]["top"][0]
        self.assertEqual({pair2["a"], pair2["b"]}, {"c.py", "d.py"})

    def test_uneven_split_gets_an_extra_remainder_chunk(self):
        # 7 commits / N=3 -> size = 7//3 = 2 -> chunks of 2,2,2,1 (4 chunks,
        # not 3) — the same ceil(len/size) shape as the ported reference
        # implementation (method/coupling_trend.py), not "N chunks with the
        # last absorbing the remainder".
        for i in range(7):
            self.fx.commit("x", [f"f{i}.py", f"g{i}.py"], subject=f"c{i}",
                            date=f"2026-06-{i + 1:02d}T10:00:00+00:00")
        eras = self.fx.payload("--unit", "commit", "--by-era", "3")["coupling"]["by_era"]
        self.assertEqual(len(eras), 4)
        self.assertEqual(eras[-1]["tasks"], 1)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Hermetic tests for scripts/analyze-authoring-reliability.py (T-136).

Run with either:
    python3 -m unittest scripts.tests.test_analyze_authoring_reliability
    python3 scripts/tests/test_analyze_authoring_reliability.py

Synthetic fixture logs cover the four classification cases; a regression
test also runs against this session's real saved t107-gate-nano logs, if
present on disk (skipped otherwise — those logs are gitignored .openup/
state, not committed).
"""

import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze-authoring-reliability.py"
_loader = importlib.machinery.SourceFileLoader("analyze_authoring_reliability", str(SCRIPT))
_spec = importlib.util.spec_from_file_location(
    "analyze_authoring_reliability", SCRIPT, loader=_loader)
aar = importlib.util.module_from_spec(_spec)
_loader.exec_module(aar)


def _sub_run(name, turns, tool_lines=()):
    lines = ["[openup-agent] procedure=%s model=test-model endpoint=https://x/v1" % name]
    for i in range(1, turns + 1):
        lines.append("[openup-agent] model turn %d/50" % i)
        if i - 1 < len(tool_lines):
            lines.append(tool_lines[i - 1])
    return "\n".join(lines)


class ParseTests(unittest.TestCase):
    def test_splits_multiple_sub_runs(self):
        log = "\n".join([
            _sub_run("A", 2, ["[openup-agent] write_file a.md"]),
            _sub_run("B", 3, ["[openup-agent] read_file b.md"]),
        ])
        blocks = aar.parse_sub_runs(log)
        self.assertEqual([b["name"] for b in blocks], ["A", "B"])
        self.assertEqual(blocks[0]["turns"], 2)
        self.assertEqual(blocks[1]["turns"], 3)

    def test_fatal_line_recorded_on_current_block(self):
        log = "\n".join([
            _sub_run("A", 3),
            "[openup-agent] FATAL: endpoint error on iteration 3: HTTP 429 from endpoint: {",
        ])
        blocks = aar.parse_sub_runs(log)
        self.assertIn("HTTP 429", blocks[0]["fatal"])


class ClassifySubRunTests(unittest.TestCase):
    def test_clean_short_run_no_repeats(self):
        block = {"name": "clean-one", "turns": 3, "fatal": None,
                "tool_calls": [("write_file", "x.md")]}
        result = aar.classify_sub_run(block)
        self.assertTrue(result["clean"])
        self.assertIsNone(result["reason"])

    def test_exceeds_turn_ceiling(self):
        block = {"name": "slow-one", "turns": 9, "fatal": None,
                "tool_calls": [("read_file", "a.md"), ("write_file", "b.md")]}
        result = aar.classify_sub_run(block, max_turns=6)
        self.assertFalse(result["clean"])
        self.assertIn("max-turns", result["reason"])

    def test_restart_detected_via_repeated_tool_call(self):
        block = {"name": "looping-one", "turns": 5, "fatal": None,
                "tool_calls": [("glob", "docs/**/x.md")] * 3}
        result = aar.classify_sub_run(block, repeat_threshold=3)
        self.assertFalse(result["clean"])
        self.assertIn("restart", result["reason"])
        self.assertIn("glob", result["reason"])

    def test_restart_takes_priority_over_coincidental_fatal(self):
        # The real run-04 case: a genuine restart pattern, cut off by an
        # unrelated rate limit — the restart is the more informative reason.
        block = {"name": "Plan Iteration", "turns": 25,
                "fatal": "endpoint error on iteration 25: HTTP 429",
                "tool_calls": [("glob", "docs/**/technical-specification*.md")] * 12}
        result = aar.classify_sub_run(block)
        self.assertFalse(result["clean"])
        self.assertIn("restart", result["reason"])
        self.assertNotIn("429", result["reason"])

    def test_fatal_with_no_restart_pattern_reports_fatal(self):
        block = {"name": "unlucky-one", "turns": 1,
                "fatal": "endpoint error on iteration 1: HTTP 429", "tool_calls": []}
        result = aar.classify_sub_run(block)
        self.assertFalse(result["clean"])
        self.assertIn("endpoint/driver error", result["reason"])

    def test_two_identical_calls_is_not_yet_a_restart(self):
        # Below the default threshold (3) — a single incidental duplicate
        # read should not be flagged.
        block = {"name": "borderline", "turns": 3, "fatal": None,
                "tool_calls": [("read_file", "a.md"), ("read_file", "a.md")]}
        result = aar.classify_sub_run(block)
        self.assertTrue(result["clean"])


class ClassifyRunTests(unittest.TestCase):
    def _write(self, tmp, name, text):
        p = Path(tmp) / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_clean_run_all_sub_runs_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = "\n".join([
                _sub_run("A", 2, ["[openup-agent] write_file a.md"]),
                _sub_run("B", 3, ["[openup-agent] read_file b.md"]),
            ])
            p = self._write(tmp, "run-01.driver.log", log)
            result = aar.classify_run(p)
            self.assertTrue(result["clean"])
            self.assertEqual(len(result["sub_runs"]), 2)

    def test_never_started_run_is_not_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = "[openup-agent] FATAL: endpoint error on iteration 1: connection refused"
            p = self._write(tmp, "run-02.driver.log", log)
            result = aar.classify_run(p)
            self.assertFalse(result["clean"])
            self.assertIn("no sub-run", result["reason"])

    def test_one_bad_sub_run_fails_the_whole_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = "\n".join([
                _sub_run("A", 2, ["[openup-agent] write_file a.md"]),
                _sub_run("B", 5, ["[openup-agent] glob x"] * 4),
            ])
            p = self._write(tmp, "run-03.driver.log", log)
            result = aar.classify_run(p)
            self.assertFalse(result["clean"])
            self.assertIn("B:", result["reason"])


class AnalyzeBatchTests(unittest.TestCase):
    def test_clean_rate_over_a_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            clean_log = _sub_run("A", 2, ["[openup-agent] write_file a.md"])
            bad_log = "\n".join([
                _sub_run("A", 2, ["[openup-agent] write_file a.md"]),
                _sub_run("B", 5, ["[openup-agent] glob x"] * 4),
            ])
            for i, log in enumerate([clean_log, clean_log, clean_log, bad_log], start=1):
                (Path(tmp) / ("run-0%d.driver.log" % i)).write_text(log, encoding="utf-8")
            result = aar.analyze(tmp)
            self.assertEqual(result["runs"], 4)
            self.assertEqual(result["authoring_chain_clean"], 3)
            self.assertEqual(result["clean_rate"], 0.75)

    def test_empty_dir_reports_zero_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = aar.analyze(tmp)
            self.assertEqual(result["runs"], 0)
            self.assertEqual(result["clean_rate"], 0.0)


class RealLogsRegressionTest(unittest.TestCase):
    """Regression against this session's real saved gate-check logs, if
    present (.openup/ is gitignored — absent in a fresh checkout/CI)."""

    def test_t107_gate_nano_matches_hand_verified_finding(self):
        bench_dir = REPO_ROOT / ".openup" / "bench" / "t107-gate-nano"
        if not bench_dir.is_dir():
            self.skipTest("real bench logs not present on disk (gitignored .openup/ state)")
        result = aar.analyze(bench_dir)
        self.assertEqual(result["runs"], 5)
        self.assertEqual(result["authoring_chain_clean"], 4)
        self.assertEqual(result["clean_rate"], 0.8)
        bad = next(r for r in result["per_run"] if not r["clean"])
        self.assertEqual(bad["run"], "run-04.driver.log")
        self.assertIn("restart", bad["reason"])


if __name__ == "__main__":
    unittest.main()

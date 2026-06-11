#!/usr/bin/env python3
"""Unit tests for the T-010 graded-track routing layer.

Covers:
  - the pure ``suggest_track()`` classifier (imported directly), and
  - the ``on-task-request.py`` intake hook end-to-end, driven exactly as the
    harness drives it (JSON payload on stdin, behavior asserted via exit code +
    stderr), in both the no-active-iteration and active-iteration branches.

Run with either:
    python3 -m unittest scripts.tests.test_t010_tracks
    python3 scripts/tests/test_t010_tracks.py
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "scripts" / "hooks"
HOOK = HOOKS_DIR / "on-task-request.py"


def _load_hook_module():
    """Import on-task-request.py as a module so suggest_track() is callable.

    The filename has dashes, so it is loaded via importlib from its path.
    Returns None if import fails (the hook is still tested end-to-end).
    """
    try:
        spec = importlib.util.spec_from_file_location("on_task_request", HOOK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def run_hook(payload, cwd):
    """Invoke the hook with a JSON payload on stdin; return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class TempProject:
    """A throwaway dir with a project-status.md so the hook treats it OpenUP."""

    def __init__(self, status: str = "planned", current_task: str = "None",
                 phase: str = "construction"):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "docs").mkdir(parents=True, exist_ok=True)
        (self.dir / "docs" / "project-status.md").write_text(
            "# Project Status\n\n"
            f"**Phase**: {phase}\n"
            f"**Status**: {status}\n"
            f"**Current Task**: {current_task}\n"
        )

    def payload(self, prompt: str) -> dict:
        return {
            "hook_event_name": "UserPromptSubmit",
            "prompt": prompt,
            "cwd": str(self.dir),
        }

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


# --------------------------------------------------------------------------
# Pure classifier
# --------------------------------------------------------------------------
class SuggestTrackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_hook_module()

    def setUp(self):
        if self.mod is None or not hasattr(self.mod, "suggest_track"):
            self.skipTest("on-task-request.py not importable as a module")

    def test_quick_scope(self):
        for p in ("fix typo in README", "bump version to 1.2.0",
                  "rename a variable", "add a comment", "tiny one-liner",
                  "update the docs"):
            self.assertEqual(self.mod.suggest_track(p), "quick", p)

    def test_full_scope(self):
        for p in ("redesign the auth architecture", "migrate the database",
                  "schema change across services", "rework the module",
                  "multi-component refactor", "broad refactor of the core"):
            self.assertEqual(self.mod.suggest_track(p), "full", p)

    def test_standard_default(self):
        for p in ("implement the export feature", "add pagination to the list",
                  "build the checkout flow"):
            self.assertEqual(self.mod.suggest_track(p), "standard", p)

    def test_quick_wins_over_full(self):
        # A small-scope word is decisive even when a broad word is present.
        self.assertEqual(
            self.mod.suggest_track("tiny refactor: rename one symbol"), "quick")


# --------------------------------------------------------------------------
# Intake hook end-to-end — no active iteration
# --------------------------------------------------------------------------
class NoActiveIterationTests(unittest.TestCase):
    def setUp(self):
        self.proj = TempProject(status="planned", current_task="None")

    def tearDown(self):
        self.proj.cleanup()

    def test_quick_prompt_suggests_quick(self):
        proc = run_hook(self.proj.payload("fix typo in README for T-010"),
                        self.proj.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Suggested track: quick", proc.stderr)
        # Folded into the start-iteration suggestion.
        self.assertIn("track: quick", proc.stderr)
        self.assertIn("/openup-start-iteration", proc.stderr)

    def test_architectural_prompt_suggests_full(self):
        proc = run_hook(
            self.proj.payload("implement T-010: redesign the architecture"),
            self.proj.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Suggested track: full", proc.stderr)
        self.assertIn("track: full", proc.stderr)

    def test_plain_feature_suggests_standard(self):
        proc = run_hook(
            self.proj.payload("implement the export feature for T-010"),
            self.proj.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Suggested track: standard", proc.stderr)
        self.assertIn("track: standard", proc.stderr)


# --------------------------------------------------------------------------
# Intake hook end-to-end — active iteration
# --------------------------------------------------------------------------
class ActiveIterationTests(unittest.TestCase):
    def setUp(self):
        self.proj = TempProject(status="in-progress", current_task="T-010")

    def tearDown(self):
        self.proj.cleanup()

    def test_active_branch_still_suggests_track(self):
        proc = run_hook(
            self.proj.payload("continue with T-010 — fix typo in the doc"),
            self.proj.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Active iteration", proc.stderr)
        self.assertIn("Suggested track: quick", proc.stderr)

    def test_active_full_scope(self):
        proc = run_hook(
            self.proj.payload("work on T-010 migration across services"),
            self.proj.dir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Suggested track: full", proc.stderr)


# --------------------------------------------------------------------------
# Exit-code preservation (non-task / non-OpenUP)
# --------------------------------------------------------------------------
class ExitCodeTests(unittest.TestCase):
    def test_non_task_prompt_exits_zero(self):
        proj = TempProject()
        try:
            proc = run_hook(proj.payload("what does this function return?"),
                            proj.dir)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr.strip(), "")
        finally:
            proj.cleanup()

    def test_non_openup_project_exits_zero(self):
        # A task-ish prompt but no docs/project-status.md → not OpenUP-managed.
        d = Path(tempfile.mkdtemp())
        try:
            payload = {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "implement the feature",
                "cwd": str(d),
            }
            proc = run_hook(payload, d)
            self.assertEqual(proc.returncode, 0)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

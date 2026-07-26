#!/usr/bin/env python3
"""Hermetic tests for on-task-request.py's classifier (T-135).

Run with either:
    python3 -m unittest scripts.tests.test_on_task_request_hook
    python3 scripts/tests/test_on_task_request_hook.py

Every fixture below is a real quote from the 2026-07-26 session that
motivated this task — false positives that must NOT classify as a request,
and genuine directives that must. Driven exactly as the harness drives the
hook: a JSON payload on stdin, behavior asserted via exit code + stderr
(the ``test_t006_hooks.py`` convention).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "docs-eng-process" / ".claude-templates" / "scripts" / "hooks" / "on-task-request.py"


def run_hook(prompt, cwd, status_text=None):
    """Invoke the hook with a UserPromptSubmit payload; return CompletedProcess.

    ``status_text``, when given, is written to ``docs/project-status.md``
    under ``cwd`` first (so the hook sees a real OpenUP-managed project).
    """
    if status_text is not None:
        docs = Path(cwd) / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "project-status.md").write_text(status_text, encoding="utf-8")
    payload = {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": str(cwd)}
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True,
    )


NO_ITERATION_STATUS = "**Phase**: construction\n**Status**: pending\n**Current Task**: None\n"
IN_PROGRESS_STATUS = "**Phase**: construction\n**Status**: in-progress\n**Current Task**: T-999\n"

# Real false positives verified this session — must NOT classify as a request.
FALSE_POSITIVES = [
    "What do you need for T-107?",
    "What's official openapi endpoint?",
    "Why pausing for human? that should run autonomously",
    "What are we missing to have the harness to follow the openup process (or any process) ?",
]

# Real genuine directives from this session (or equivalent phrasing) —
# must classify as a request, unchanged from before this task.
GENUINE_DIRECTIVES = [
    "implement T-107",
    "fix the login bug",
    "let's build this feature",
    "continue with T-042",
]

# Accepted, documented recall gap — NOT a regression. No task-language verb
# in TASK_LANG_RE matches "run"; this task is a precision fix, not a recall
# improvement, so this must stay unclassified both before and after.
ACCEPTED_GAP = "Try nano and run the batch"


class TrueFalsePositiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_false_positives_do_not_block(self):
        for prompt in FALSE_POSITIVES:
            with self.subTest(prompt=prompt):
                proc = run_hook(prompt, self.cwd, status_text=NO_ITERATION_STATUS)
                self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                self.assertEqual(proc.stderr, "")

    def test_genuine_directives_block_with_no_active_iteration(self):
        for prompt in GENUINE_DIRECTIVES:
            with self.subTest(prompt=prompt):
                proc = run_hook(prompt, self.cwd, status_text=NO_ITERATION_STATUS)
                self.assertEqual(proc.returncode, 2, msg=proc.stderr)
                self.assertIn("[on-task-request]", proc.stderr)
                self.assertIn("/openup-start-iteration", proc.stderr)

    def test_accepted_recall_gap_stays_unclassified(self):
        proc = run_hook(ACCEPTED_GAP, self.cwd, status_text=NO_ITERATION_STATUS)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)


class ActiveIterationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_active_iteration_reminder_still_advisory(self):
        # A genuine directive with an iteration already active must NOT block
        # — this branch has no missing precondition, only a continuation nudge.
        proc = run_hook("implement T-107", self.cwd, status_text=IN_PROGRESS_STATUS)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("[on-task-request]", proc.stderr)
        self.assertIn("Active iteration detected", proc.stderr)


class BareIdLengthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_short_bare_id_mention_blocks(self):
        proc = run_hook("T-107", self.cwd, status_text=NO_ITERATION_STATUS)
        self.assertEqual(proc.returncode, 2, msg=proc.stderr)

    def test_long_bare_id_mention_does_not_block(self):
        long_prompt = (
            "I was reading through the archive and noticed that T-107 has "
            "an interesting history worth understanding before we move on"
        )
        proc = run_hook(long_prompt, self.cwd, status_text=NO_ITERATION_STATUS)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)


class NonOpenUpProjectTest(unittest.TestCase):
    def test_no_project_status_file_is_a_noop(self):
        with tempfile.TemporaryDirectory() as cwd:
            proc = run_hook("implement T-107", cwd)  # no project-status.md written
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stderr, "")


if __name__ == "__main__":
    unittest.main()

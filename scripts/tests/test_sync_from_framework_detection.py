#!/usr/bin/env python3
"""Tests for the framework self-detection guard in scripts/sync-from-framework.sh.

Regression for the false-positive that refused to run the sync in a legitimate
consuming project: the guard used docs-eng-process/.claude-templates/ as its
"framework repository itself" marker, but older syncs / manual setups copied
that tree into consuming projects too, so the guard aborted with "You appear to
be in the framework repository itself." even in a valid consumer.

The definitive marker is scripts/sync-templates-to-claude.sh — framework-only,
never distributed to consumers, and the exact script the error tells you to run.

The guard only runs during auto-detection (the `if [ -z "$FRAMEWORK_PATH" ]`
block); passing --framework-path skips it. So these tests exercise auto-detect:
the framework is placed at the sibling path `../open-up-for-ai-agents` (the
first entry the script probes) and the script is run WITHOUT --framework-path.

Hermetic: each test builds a throwaway consumer + framework on disk and runs
the real script with --dry-run — never touching the live project.
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "sync-from-framework.sh"

# The script probes "$PROJECT_ROOT/../open-up-for-ai-agents" first.
FRAMEWORK_DIRNAME = "open-up-for-ai-agents"


def make_framework(root: Path) -> None:
    """Minimal tree that satisfies auto-detection + framework validation."""
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    # The real sync script, so the framework tree can run its own copy.
    shutil.copy(SCRIPT, root / "scripts" / "sync-from-framework.sh")
    # The definitive framework-only marker.
    (root / "scripts" / "sync-templates-to-claude.sh").write_text("#!/bin/bash\n")
    templates = root / "docs-eng-process" / ".claude-templates"
    templates.mkdir(parents=True, exist_ok=True)
    (templates / "CLAUDE.md").write_text("# framework templates\n")


def make_consumer(root: Path, with_templates_tree: bool) -> None:
    """A project that USES the framework. It carries its own copy of the sync
    script under scripts/, but never scripts/sync-templates-to-claude.sh.

    with_templates_tree reproduces the bug's precondition: an older sync left a
    docs-eng-process/.claude-templates/ tree in the consumer.
    """
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(SCRIPT, root / "scripts" / "sync-from-framework.sh")
    if with_templates_tree:
        templates = root / "docs-eng-process" / ".claude-templates"
        templates.mkdir(parents=True, exist_ok=True)
        (templates / "CLAUDE.md").write_text("# stale copy left by an old sync\n")


def run_sync_autodetect(project: Path) -> subprocess.CompletedProcess:
    """Run the project's own copy of the script with NO --framework-path, so the
    auto-detection block (which contains the guard) executes."""
    return subprocess.run(
        ["bash", str(project / "scripts" / "sync-from-framework.sh"), "--dry-run"],
        capture_output=True, text=True,
    )


class DetectionGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        # Sibling framework at ../open-up-for-ai-agents relative to any consumer.
        self.framework = self.base / FRAMEWORK_DIRNAME
        make_framework(self.framework)

    def tearDown(self):
        self._tmp.cleanup()

    def test_consumer_with_stale_templates_tree_is_not_misdetected(self):
        # The reported bug: a consumer that carries a .claude-templates/ tree
        # must NOT be mistaken for the framework. It should pass the guard,
        # auto-detect the sibling framework, and proceed (dry-run).
        # NB: this script's log_error() writes to stdout, so assert on the
        # combined output rather than stderr alone.
        consumer = self.base / "consumer"
        make_consumer(consumer, with_templates_tree=True)
        proc = run_sync_autodetect(consumer)
        out = proc.stdout + proc.stderr
        self.assertNotIn("framework repository itself", out, msg=out)
        self.assertIn("Found framework at", out, msg=out)
        self.assertEqual(proc.returncode, 0, msg=out)

    def test_plain_consumer_is_not_misdetected(self):
        consumer = self.base / "consumer"
        make_consumer(consumer, with_templates_tree=False)
        proc = run_sync_autodetect(consumer)
        out = proc.stdout + proc.stderr
        self.assertNotIn("framework repository itself", out, msg=out)
        self.assertEqual(proc.returncode, 0, msg=out)

    def test_framework_repo_still_self_aborts(self):
        # Running the sync from inside a real framework tree (auto-detect, no
        # --framework-path) must still abort with the guard — that half of the
        # behavior is unchanged.
        proc = run_sync_autodetect(self.framework)
        out = proc.stdout + proc.stderr
        self.assertIn("framework repository itself", out, msg=out)
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()

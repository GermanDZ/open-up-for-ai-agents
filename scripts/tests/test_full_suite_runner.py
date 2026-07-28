#!/usr/bin/env python3
"""Guard tests for scripts/run-tests.sh — the "full suite" runner (T-160).

The runner's directory list is *enumerated*, not discovered, because discovery
would sweep `venv/` and `.claude/worktrees/` (both contain `test_*.py`) and
excluding them is a denylist that rots. The trade-off is that a new project test
directory could be silently omitted — which is exactly the class of defect the
runner exists to fix, so it must fail loudly instead.

`test_every_project_test_dir_is_covered` is that guard. It is the reason this
file exists; the rest are cheap structural checks on the script itself.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts" / "run-tests.sh"

# Directories that legitimately contain `test_*.py` but are NOT this project's
# tests. Kept narrow and explicit: a broad pattern here would re-open the gap.
NOT_OURS = ("venv", ".venv", ".git", "node_modules", ".claude")


def _declared_dirs() -> list[str]:
    """The TEST_DIRS array as the shell script declares it."""
    text = RUNNER.read_text(encoding="utf-8")
    block = re.search(r"TEST_DIRS=\((.*?)\)", text, re.DOTALL)
    assert block, "TEST_DIRS array not found — did the runner's shape change?"
    return re.findall(r'"([^"]+)"', block.group(1))


def _discovered_dirs() -> set[str]:
    """Top-level project directories that actually contain test files."""
    found = set()
    for path in REPO_ROOT.rglob("test_*.py"):
        rel = path.relative_to(REPO_ROOT)
        if rel.parts[0] in NOT_OURS:
            continue
        found.add(str(rel.parent))
    return found


class TestRunnerExists:
    def test_runner_is_executable(self):
        assert RUNNER.exists(), "scripts/run-tests.sh must exist"
        assert RUNNER.stat().st_mode & 0o111, "run-tests.sh must be executable"

    def test_declares_both_known_dirs(self):
        """Requirement 1: the two project test directories are both covered."""
        declared = _declared_dirs()
        assert "scripts/tests" in declared
        assert "tests" in declared

    def test_does_not_mask_failures(self):
        """The aggregate exit code must not be swallowed. `|| true` or a bare
        `exit 0` would make a red suite look green — the same disarming trap
        T-150 rejected for hook guards."""
        text = RUNNER.read_text(encoding="utf-8")
        assert "|| true" not in text, "must not suppress a failing directory"
        assert re.search(r'^exit "\$overall"', text, re.MULTILINE), (
            "must exit with the aggregated code"
        )


class TestCoverageGuard:
    def test_every_project_test_dir_is_covered(self):
        """Requirement 3 — the reason this file exists.

        If someone adds a third project test directory and forgets the runner,
        this fails and names it, rather than the suite quietly shrinking.
        """
        declared = set(_declared_dirs())
        discovered = _discovered_dirs()
        uncovered = discovered - declared
        assert not uncovered, (
            "these directories contain tests but are not in run-tests.sh's "
            f"TEST_DIRS: {sorted(uncovered)}. Add them to scripts/run-tests.sh."
        )

    def test_guard_detects_a_synthetic_uncovered_dir(self, tmp_path):
        """Bite check: prove the guard above would actually fire.

        A guard that cannot be shown to fail is not a guard. This reproduces its
        logic against a fixture containing an undeclared test directory, rather
        than trusting that the real assertion works.
        """
        (tmp_path / "extra_tests").mkdir()
        (tmp_path / "extra_tests" / "test_new.py").write_text("def test_x(): pass\n")
        (tmp_path / "venv" / "lib").mkdir(parents=True)
        (tmp_path / "venv" / "lib" / "test_vendored.py").write_text("def test_y(): pass\n")

        declared = {"scripts/tests", "tests"}
        discovered = set()
        for path in tmp_path.rglob("test_*.py"):
            rel = path.relative_to(tmp_path)
            if rel.parts[0] in NOT_OURS:
                continue
            discovered.add(str(rel.parent))

        assert "extra_tests" in discovered - declared, "guard must flag the new dir"
        assert not any("venv" in d for d in discovered), (
            "guard must still ignore vendored tests"
        )

    def test_no_declared_dir_is_missing_from_disk(self):
        """The inverse drift: a directory listed but deleted. The runner treats
        that as a failure rather than skipping it, so assert the list is live."""
        for d in _declared_dirs():
            assert (REPO_ROOT / d).is_dir(), f"run-tests.sh lists a missing dir: {d}"


class TestRunnerBehaviour:
    def test_runs_and_reports_both_directories(self):
        """Requirement 1, end to end — collect only, so this stays fast."""
        proc = subprocess.run(
            ["bash", str(RUNNER), "--collect-only", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        assert "=== scripts/tests ===" in proc.stdout
        assert "=== tests ===" in proc.stdout
        assert "full suite: PASSED" in proc.stdout

    def test_summary_lists_every_directory(self):
        proc = subprocess.run(
            ["bash", str(RUNNER), "--collect-only", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        for d in _declared_dirs():
            assert f"  {d}: passed" in proc.stdout, f"summary omitted {d}"

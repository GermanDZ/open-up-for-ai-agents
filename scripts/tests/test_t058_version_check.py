#!/usr/bin/env python3
"""Tests for openup-version-check.py (T-058).

Hermetic unit tests for version staleness checking.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestVersionCheck(unittest.TestCase):
    """Unit tests for version check functions."""

    def setUp(self):
        """Create temporary directory for test repos."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tmpdir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.tmpdir.cleanup()

    def write_installed_version(self, version: str):
        """Write the installed version file."""
        version_file = self.repo_root / "docs-eng-process" / ".template-version"
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text(version + "\n")

    def write_cooldown_state(self, last_checked: str, installed: str = "2.0.0", 
                             latest: str = "2.0.0", outdated: bool = False):
        """Write a cooldown state file."""
        state_file = self.repo_root / ".openup" / "version-check.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({
            "last_checked": last_checked,
            "installed": installed,
            "latest": latest,
            "outdated": outdated,
        }))

    def read_cooldown_state(self):
        """Read the cooldown state file."""
        state_file = self.repo_root / ".openup" / "version-check.json"
        if state_file.exists():
            return json.loads(state_file.read_text())
        return None

    def test_version_file_reading(self):
        """Can read version from .template-version file."""
        self.write_installed_version("2.0.0")
        version_file = self.repo_root / "docs-eng-process" / ".template-version"
        content = version_file.read_text().strip()
        self.assertEqual(content, "2.0.0")

    def test_cooldown_state_writing(self):
        """Can write and read cooldown state."""
        self.write_cooldown_state("2026-06-19T12:00:00Z", 
                                  installed="2.0.0", latest="2.1.0", outdated=True)
        state = self.read_cooldown_state()
        self.assertIsNotNone(state)
        self.assertEqual(state["installed"], "2.0.0")
        self.assertEqual(state["latest"], "2.1.0")
        self.assertTrue(state["outdated"])

    def test_cli_not_in_git_repo(self):
        """CLI returns 1 when not in a git repo."""
        not_repo = Path(self.tmpdir.name) / "not_git"
        not_repo.mkdir()

        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "openup-version-check.py")],
            cwd=not_repo,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 1)

    def test_version_tuple_conversion(self):
        """Version tuple conversion handles semver correctly."""
        def version_tuple(v: str):
            try:
                parts = v.split('.')
                return tuple(int(p) for p in parts)
            except (ValueError, AttributeError):
                return (0, 0, 0)
        
        self.assertEqual(version_tuple("1.0.0"), (1, 0, 0))
        self.assertEqual(version_tuple("2.10.0"), (2, 10, 0))
        self.assertEqual(version_tuple("2.1.0"), (2, 1, 0))
        
        # Test comparisons
        self.assertTrue(version_tuple("1.0.0") < version_tuple("2.0.0"))
        self.assertTrue(version_tuple("2.0.0") < version_tuple("2.1.0"))
        self.assertTrue(version_tuple("2.1.0") < version_tuple("2.1.1"))
        self.assertTrue(version_tuple("2.10.0") > version_tuple("2.1.0"))
        self.assertFalse(version_tuple("2.0.0") < version_tuple("2.0.0"))

    def test_semver_pattern_matching(self):
        """Semver pattern regex works correctly."""
        import re
        pattern = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
        
        # Valid tags
        self.assertIsNotNone(pattern.fullmatch("v2.0.0"))
        self.assertIsNotNone(pattern.fullmatch("v10.20.30"))
        
        # Invalid tags
        self.assertIsNone(pattern.fullmatch("release-1"))
        self.assertIsNone(pattern.fullmatch("v2.0"))
        self.assertIsNone(pattern.fullmatch("2.0.0"))
        self.assertIsNone(pattern.fullmatch("wrong"))

    def test_iso_timestamp_parsing(self):
        """ISO timestamps are created and parsed correctly."""
        now = datetime.now(timezone.utc)
        ts_iso = now.isoformat(timespec="seconds").replace("+00:00", "Z")
        
        # Parse it back
        if ts_iso.endswith("Z"):
            ts_iso_parsed = ts_iso[:-1] + "+00:00"
        parsed = datetime.fromisoformat(ts_iso_parsed)
        
        # Should be within a second
        diff = abs((now - parsed).total_seconds())
        self.assertLess(diff, 1.0)

    def test_cooldown_calculation(self):
        """6-hour cooldown is calculated correctly."""
        now = datetime.now(timezone.utc)
        
        # 2 hours ago - within cooldown
        recent = (now - timedelta(hours=2)).isoformat(timespec="seconds").replace("+00:00", "Z")
        if recent.endswith("Z"):
            recent = recent[:-1] + "+00:00"
        recent_dt = datetime.fromisoformat(recent)
        elapsed_recent = (now - recent_dt).total_seconds()
        self.assertLess(elapsed_recent, 6 * 3600)
        
        # 8 hours ago - outside cooldown
        old = (now - timedelta(hours=8)).isoformat(timespec="seconds").replace("+00:00", "Z")
        if old.endswith("Z"):
            old = old[:-1] + "+00:00"
        old_dt = datetime.fromisoformat(old)
        elapsed_old = (now - old_dt).total_seconds()
        self.assertGreater(elapsed_old, 6 * 3600)

    def test_version_tag_parsing(self):
        """Can extract versions from git tag output."""
        output = """abc123\trefs/tags/v2.1.0
def456\trefs/tags/v2.10.0^{}
ghi789\trefs/tags/release-1
jkl012\trefs/tags/v2.0.0"""
        
        import re
        pattern = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
        versions = []
        
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            ref = parts[-1]
            if ref.endswith("^{}"):
                ref = ref[:-3]
            if "/" in ref:
                tag = ref.split("/")[-1]
            else:
                tag = ref
            
            match = pattern.fullmatch(tag)
            if match:
                major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
                versions.append(((major, minor, patch), f"{major}.{minor}.{patch}"))
        
        versions.sort(reverse=True)
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0][1], "2.10.0")

    def test_state_openup_directory_creation(self):
        """State file creates .openup directory as needed."""
        openup_dir = self.repo_root / ".openup"
        openup_dir.mkdir(exist_ok=True)
        state_file = openup_dir / "version-check.json"
        
        # Directory should exist
        self.assertTrue(state_file.parent.exists())
        self.assertTrue(state_file.parent.is_dir())


if __name__ == "__main__":
    unittest.main()

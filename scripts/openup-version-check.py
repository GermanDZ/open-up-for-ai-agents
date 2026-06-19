#!/usr/bin/env python3
"""Periodic framework version staleness check (T-058).

Checks whether the installed OpenUP framework version is behind the latest
remote release. Throttled by a 6-hour cooldown to avoid repeated network calls.
Non-blocking: network failures, missing files, or parse errors fail silently.

Callable as:
  - check_once(repo_root: str) → None
      Load cooldown state, check if update is needed (6h throttle), emit
      advisory warning to stderr if outdated, write cooldown state.
      On any error: return silently (fail-open).
  - CLI: python3 openup-version-check.py
      Calls check_once() in the current git repo.

Exit codes (CLI only):
  0  success or any error (fail-open)
  1  not a git repository (catchable by the caller if needed)
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


COOLDOWN_SECONDS = 6 * 3600  # 6 hours
GIT_TIMEOUT_SECONDS = 5
VERSION_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")


def check_once(repo_root: str) -> None:
    """Load cooldown state, check version, emit advisory, write state.

    Silently returns on any error (fail-open).
    """
    try:
        repo_path = Path(repo_root).resolve()
        state_file = repo_path / ".openup" / "version-check.json"
        version_file = repo_path / "docs-eng-process" / ".template-version"

        # Load cooldown state
        state = _load_state(state_file)

        # Check if we're still in cooldown
        if _in_cooldown(state):
            return

        # Fetch latest remote version
        latest = _fetch_latest_version(repo_path)
        if latest is None:
            return  # No tags found or network error; fail-open

        # Read installed version
        installed = _read_installed_version(version_file)
        if installed is None:
            return  # No .template-version found; fail-open

        # Compare versions (as tuples for semver comparison)
        def version_tuple(v: str):
            try:
                parts = v.split('.')
                return tuple(int(p) for p in parts)
            except (ValueError, AttributeError):
                return (0, 0, 0)
        
        outdated = version_tuple(installed) < version_tuple(latest)
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        # Write new state
        new_state = {
            "last_checked": now_iso,
            "latest": latest,
            "installed": installed,
            "outdated": outdated,
        }
        _save_state(state_file, new_state)

        # Emit advisory if outdated
        if outdated:
            sys.stderr.write(
                f"[openup] ⚠️  Framework version outdated: installed={installed}  latest={latest}\n"
            )
            sys.stderr.write("           Run: sync-from-framework.sh --framework-path <path>  or  force-upgrade.sh\n")

    except Exception:
        # Fail-open: silently ignore any error
        pass


def _load_state(state_file: Path) -> dict:
    """Load the cooldown state file. Return empty dict if missing or invalid."""
    try:
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_state(state_file: Path, state: dict) -> None:
    """Write the cooldown state file. Create .openup/ if needed."""
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(state, f)
    except OSError:
        pass  # Fail-open


def _in_cooldown(state: dict) -> bool:
    """Check if the last check is still within the 6-hour cooldown window."""
    if "last_checked" not in state:
        return False
    try:
        last_checked_str = state["last_checked"]
        # Parse ISO format timestamp (e.g., "2026-06-19T14:00:00Z")
        if last_checked_str.endswith("Z"):
            last_checked_str = last_checked_str[:-1] + "+00:00"
        last_checked = datetime.fromisoformat(last_checked_str)
        now = datetime.now(timezone.utc)
        elapsed = (now - last_checked).total_seconds()
        return elapsed < COOLDOWN_SECONDS
    except (ValueError, KeyError):
        return False


def _fetch_latest_version(repo_path: Path) -> str | None:
    """Fetch the latest semver tag from origin. Return None on error."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", "v*"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            return None

        # Parse all tags and find the highest semver
        versions = []
        for line in result.stdout.splitlines():
            # Line format: "commit_hash\trefs/tags/vX.Y.Z" or "...\trefs/tags/vX.Y.Z^{}"
            parts = line.split()
            if len(parts) < 2:
                continue
            ref = parts[-1]
            # Strip ^{} suffix (annotated tag dereference)
            if ref.endswith("^{}"):
                ref = ref[:-3]
            # Extract tag name
            if "/" in ref:
                tag = ref.split("/")[-1]
            else:
                tag = ref

            # Try to parse as semver
            match = VERSION_PATTERN.fullmatch(tag)
            if match:
                major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
                versions.append(((major, minor, patch), f"{major}.{minor}.{patch}"))

        if not versions:
            return None

        # Return the highest version (lexicographic sort on tuples)
        versions.sort(reverse=True)
        return versions[0][1]

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError, FileNotFoundError):
        return None


def _read_installed_version(version_file: Path) -> str | None:
    """Read the installed version from .template-version. Return None if missing."""
    try:
        if version_file.exists():
            with open(version_file) as f:
                version = f.read().strip()
                # Validate it looks like a semver
                if VERSION_PATTERN.fullmatch(version):
                    return version
    except OSError:
        pass
    return None


if __name__ == "__main__":
    try:
        repo_root = Path.cwd()
        # Verify we're in a git repo
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_root,
            capture_output=True,
            check=True,
            timeout=2,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        sys.exit(1)

    check_once(str(repo_root))
    sys.exit(0)

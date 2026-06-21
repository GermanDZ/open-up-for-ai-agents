"""Unit tests for openup-claims.py heartbeat + reap subcommands (T-060).

All tests are hermetic: they use a tmp_path claims dir and synthetic claim
files so no real git state is needed.
"""

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Load openup-claims as a module (hyphenated filename).
import importlib.util

_CLAIMS_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
_claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_claims)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_claim(cdir: Path, task_id: str, *, heartbeat: str | None = None) -> Path:
    """Write a synthetic claim file; optionally include last_heartbeat."""
    payload = {
        "task_id": task_id,
        "session_id": "test-session",
        "branch": f"feat/{task_id}-test",
        "worktree": f"/tmp/{task_id}",
        "claimed_at": "2026-06-21T00:00:00Z",
        "touches": [f"docs/changes/{task_id}/"],
    }
    if heartbeat is not None:
        payload["last_heartbeat"] = heartbeat
    cdir.mkdir(parents=True, exist_ok=True)
    fp = cdir / f"{task_id}.json"
    fp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return fp


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stale_iso(seconds_ago: int = 7200) -> str:
    dt = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_claims(argv: list[str]) -> int:
    return _claims.main(argv)


# ---------------------------------------------------------------------------
# heartbeat tests
# ---------------------------------------------------------------------------

class TestHeartbeat:
    def test_stamps_last_heartbeat_on_existing_claim(self, tmp_path):
        cdir = tmp_path / "claims"
        fp = _make_claim(cdir, "T-042")
        data_before = json.loads(fp.read_text())
        assert "last_heartbeat" not in data_before

        rc = _run_claims(["heartbeat", "--task-id", "T-042", "--claims-dir", str(cdir)])

        assert rc == 0
        data_after = json.loads(fp.read_text())
        assert "last_heartbeat" in data_after

    def test_heartbeat_is_recent_iso8601(self, tmp_path):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "T-042")
        before = datetime.now(timezone.utc)

        _run_claims(["heartbeat", "--task-id", "T-042", "--claims-dir", str(cdir)])

        data = json.loads((cdir / "T-042.json").read_text())
        hb = data["last_heartbeat"]
        hb_dt = datetime.fromisoformat(hb.replace("Z", "+00:00"))
        assert hb_dt >= before.replace(microsecond=0)

    def test_preserves_existing_claim_fields(self, tmp_path):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "T-042")

        _run_claims(["heartbeat", "--task-id", "T-042", "--claims-dir", str(cdir)])

        data = json.loads((cdir / "T-042.json").read_text())
        assert data["task_id"] == "T-042"
        assert data["session_id"] == "test-session"
        assert data["touches"] == ["docs/changes/T-042/"]

    def test_updates_existing_heartbeat(self, tmp_path):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "T-042", heartbeat="2000-01-01T00:00:00Z")

        _run_claims(["heartbeat", "--task-id", "T-042", "--claims-dir", str(cdir)])

        data = json.loads((cdir / "T-042.json").read_text())
        assert data["last_heartbeat"] != "2000-01-01T00:00:00Z"

    def test_exits_7_when_no_claim(self, tmp_path):
        cdir = tmp_path / "claims"
        cdir.mkdir(parents=True, exist_ok=True)

        rc = _run_claims(["heartbeat", "--task-id", "T-099", "--claims-dir", str(cdir)])

        assert rc == _claims.EXIT_BAD_INPUT  # 7
        assert not (cdir / "T-099.json").exists()

    def test_claims_dir_is_unchanged_on_exit7(self, tmp_path):
        cdir = tmp_path / "claims"
        cdir.mkdir(parents=True, exist_ok=True)

        _run_claims(["heartbeat", "--task-id", "T-099", "--claims-dir", str(cdir)])

        assert list(cdir.glob("*.json")) == []


# ---------------------------------------------------------------------------
# reap tests
# ---------------------------------------------------------------------------

class TestReap:
    def test_skips_claim_with_no_heartbeat(self, tmp_path):
        cdir = tmp_path / "claims"
        fp = _make_claim(cdir, "T-001")  # no heartbeat

        rc = _run_claims(["reap", "--stale-after", "300", "--claims-dir", str(cdir)])

        assert rc == 0
        assert fp.exists(), "no-heartbeat claim must NOT be reaped"

    def test_skips_fresh_heartbeat(self, tmp_path):
        cdir = tmp_path / "claims"
        fp = _make_claim(cdir, "T-001", heartbeat=_now_iso())

        rc = _run_claims(["reap", "--stale-after", "300", "--claims-dir", str(cdir)])

        assert rc == 0
        assert fp.exists(), "fresh-heartbeat claim must NOT be reaped"

    def test_reaps_stale_heartbeat(self, tmp_path):
        cdir = tmp_path / "claims"
        fp = _make_claim(cdir, "T-001", heartbeat=_stale_iso(seconds_ago=7200))

        rc = _run_claims(["reap", "--stale-after", "300", "--claims-dir", str(cdir)])

        assert rc == 0
        assert not fp.exists(), "stale-heartbeat claim MUST be reaped"

    def test_dry_run_does_not_delete(self, tmp_path):
        cdir = tmp_path / "claims"
        fp = _make_claim(cdir, "T-001", heartbeat=_stale_iso(seconds_ago=7200))

        rc = _run_claims([
            "reap", "--dry-run", "--stale-after", "300", "--claims-dir", str(cdir)
        ])

        assert rc == 0
        assert fp.exists(), "--dry-run must NOT delete the stale claim"

    def test_dry_run_prints_would_reap(self, tmp_path, capsys):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "T-001", heartbeat=_stale_iso(seconds_ago=7200))

        _run_claims([
            "reap", "--dry-run", "--stale-after", "300", "--claims-dir", str(cdir)
        ])

        captured = capsys.readouterr()
        assert "would reap T-001" in captured.out

    def test_mixed_claims(self, tmp_path):
        cdir = tmp_path / "claims"
        fp_no_hb = _make_claim(cdir, "T-001")
        fp_fresh = _make_claim(cdir, "T-002", heartbeat=_now_iso())
        fp_stale = _make_claim(cdir, "T-003", heartbeat=_stale_iso(seconds_ago=7200))

        rc = _run_claims(["reap", "--stale-after", "300", "--claims-dir", str(cdir)])

        assert rc == 0
        assert fp_no_hb.exists(), "no-heartbeat claim preserved"
        assert fp_fresh.exists(), "fresh-heartbeat claim preserved"
        assert not fp_stale.exists(), "stale-heartbeat claim reaped"

    def test_always_exits_0(self, tmp_path):
        cdir = tmp_path / "claims"
        # Even with no claims at all, reap should exit 0.
        cdir.mkdir(parents=True, exist_ok=True)

        rc = _run_claims(["reap", "--claims-dir", str(cdir)])

        assert rc == 0

    def test_default_stale_after_is_1800(self, tmp_path):
        """A claim whose heartbeat is 1800s old with no --stale-after is reaped."""
        cdir = tmp_path / "claims"
        fp = _make_claim(cdir, "T-001", heartbeat=_stale_iso(seconds_ago=1801))

        _run_claims(["reap", "--claims-dir", str(cdir)])

        assert not fp.exists()

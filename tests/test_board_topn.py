"""Unit tests for openup-board.py top-n subcommand (T-060).

All tests are hermetic: they create a temporary repo skeleton (docs/changes/
plan.md files + empty claims dir) so no real git state is needed.
"""

import json
import sys
import textwrap
from pathlib import Path

import pytest
import importlib.util

_BOARD_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openup-board.py"
_spec = importlib.util.spec_from_file_location("openup_board", _BOARD_PATH)
_board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_board)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Minimal plan.md builder
# ---------------------------------------------------------------------------

def _make_plan(root: Path, task_id: str, *, touches: list, priority: str = "high",
               status: str = "ready", depends_on: list | None = None) -> Path:
    """Write a minimal plan.md so build_lane can read it."""
    change_dir = root / "docs" / "changes" / task_id
    change_dir.mkdir(parents=True, exist_ok=True)
    plan = change_dir / "plan.md"
    deps_line = ""
    if depends_on:
        deps_line = f"depends-on: [{', '.join(depends_on)}]\n"
    touches_block = "\n".join(f"  - {t}" for t in touches)
    # Operations has one unchecked box so the lane has a next_action
    plan.write_text(textwrap.dedent(f"""\
        ---
        id: {task_id}
        title: "{task_id} test lane"
        status: {status}
        priority: {priority}
        {deps_line}touches:
        {touches_block}
        ---

        # {task_id}

        ## Operations

        - [ ] Do the thing
        """), encoding="utf-8")
    return plan


def _run_board(argv: list[str]) -> tuple[int, str]:
    """Run openup-board main; return (exit_code, stdout_text)."""
    import io
    from unittest.mock import patch
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        rc = _board.main(argv)
    return rc, buf.getvalue()


# ---------------------------------------------------------------------------
# top-n tests
# ---------------------------------------------------------------------------

class TestTopN:
    def test_returns_single_ready_lane(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "T-001", touches=["docs/changes/T-001/"])

        rc, out = _run_board([
            "top-n", "4",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        lanes = json.loads(out)
        assert isinstance(lanes, list)
        assert len(lanes) == 1
        assert lanes[0]["task"] == "T-001"

    def test_returns_disjoint_lanes(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "T-001", touches=["docs/changes/T-001/"])
        _make_plan(root, "T-002", touches=["docs/changes/T-002/"])

        rc, out = _run_board([
            "top-n", "4",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        lanes = json.loads(out)
        tasks = {l["task"] for l in lanes}
        assert "T-001" in tasks
        assert "T-002" in tasks
        assert len(lanes) == 2

    def test_excludes_colliding_lane(self, tmp_path):
        """Lane 1 and lane 3 share a prefix; lane 2 is disjoint.
        top-n 4 should return lanes 1 and 2 (greedy in priority order)."""
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        # All same priority so they sort by task id (T-001 < T-002 < T-003)
        _make_plan(root, "T-001", touches=["scripts/openup-claims.py"])
        _make_plan(root, "T-002", touches=["docs/changes/T-002/"])
        _make_plan(root, "T-003", touches=["scripts/"])  # overlaps T-001

        rc, out = _run_board([
            "top-n", "4",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        lanes = json.loads(out)
        tasks = [l["task"] for l in lanes]
        assert "T-001" in tasks
        assert "T-002" in tasks
        assert "T-003" not in tasks, "T-003 collides with T-001 (scripts/ prefix)"

    def test_stops_at_n(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        for i in range(1, 5):
            _make_plan(root, f"T-00{i}", touches=[f"docs/changes/T-00{i}/"])

        rc, out = _run_board([
            "top-n", "2",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        lanes = json.loads(out)
        assert len(lanes) == 2

    def test_exits_3_when_no_ready_lanes(self, tmp_path):
        """Board with no plans at all → no READY lanes → exit 3."""
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        (root / "docs" / "changes").mkdir(parents=True, exist_ok=True)

        rc, _out = _run_board([
            "top-n", "4",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 3

    def test_returns_empty_list_when_n_is_zero(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "T-001", touches=["docs/changes/T-001/"])

        rc, out = _run_board([
            "top-n", "0",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        lanes = json.loads(out)
        assert lanes == []

    def test_output_is_valid_json_array(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "T-001", touches=["docs/changes/T-001/"])

        rc, out = _run_board([
            "top-n", "4",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        parsed = json.loads(out)
        assert isinstance(parsed, list)

    def test_lane_schema_matches_top(self, tmp_path):
        """Each lane in top-n output has the same keys as the `top` subcommand returns."""
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "T-001", touches=["docs/changes/T-001/"])

        _, top_out = _run_board([
            "top",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])
        top_lane = json.loads(top_out)

        _, topn_out = _run_board([
            "top-n", "1",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])
        topn_lane = json.loads(topn_out)[0]

        assert set(top_lane.keys()) == set(topn_lane.keys())

    def test_priority_order_respected(self, tmp_path):
        """High-priority lane appears before medium-priority lane in the result."""
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "T-002", touches=["docs/changes/T-002/"], priority="medium")
        _make_plan(root, "T-001", touches=["docs/changes/T-001/"], priority="high")

        rc, out = _run_board([
            "top-n", "2",
            "--root", str(root),
            "--claims-dir", str(cdir),
            "--out", str(tmp_path / "board.json"),
        ])

        assert rc == 0
        lanes = json.loads(out)
        assert lanes[0]["task"] == "T-001"  # high priority first
        assert lanes[1]["task"] == "T-002"

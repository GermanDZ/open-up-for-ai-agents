"""Unit tests for the T-078 resolve paths: assess-iteration + milestone-review.

Both fire only for real phase-aware iterations / phase boundaries and never for
single-lane / promote flows — that invariant is the point, so the fixtures build
the exact minimal repo state that reaches each path. Hermetic: temp repo
skeleton, synthetic claim files, no git.
"""

import importlib.util
import textwrap
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_BOARD_PATH = _REPO / "scripts" / "openup-board.py"
_spec = importlib.util.spec_from_file_location("openup_board", _BOARD_PATH)
_board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_board)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _iteration_plan(root: Path, name: str, traces, *, status="approved",
                    assessed=False) -> None:
    d = root / "docs" / "iteration-plans"
    d.mkdir(parents=True, exist_ok=True)
    inline = "[" + ", ".join(traces) + "]"
    body = "\n## Assessment\n\nEvaluation criteria met.\n" if assessed else "\nbody\n"
    (d / f"{name}.md").write_text(
        f"---\ntype: iteration-plan\nid: {name}\nstatus: {status}\n"
        f"traces-from: {inline}\n---\n{body}", encoding="utf-8")


def _archive_work_item(root: Path, wid: str) -> None:
    a = root / "docs" / "changes" / "archive" / wid
    a.mkdir(parents=True, exist_ok=True)
    (a / "plan.md").write_text(f"---\nid: {wid}\nstatus: done\n---\n\ndone\n",
                               encoding="utf-8")


def _active_work_item(root: Path, wid: str, status="ready") -> None:
    c = root / "docs" / "changes" / wid
    c.mkdir(parents=True, exist_ok=True)
    (c / "plan.md").write_text(textwrap.dedent(f"""\
        ---
        id: {wid}
        title: "{wid}"
        status: {status}
        touches:
          - docs/changes/{wid}/
        ---

        # {wid}

        ## Operations

        - [ ] do it
        """), encoding="utf-8")


def _milestone(root: Path, phase: str, cycle: int, decision: str) -> None:
    m = root / "docs" / "product" / "milestones"
    m.mkdir(parents=True, exist_ok=True)
    (m / f"{phase}-{cycle}.md").write_text(textwrap.dedent(f"""\
        ---
        phase: {phase}
        cycle: {cycle}
        milestone: {phase.title()} milestone
        decision: {decision}
        date: 2026-07-13
        decided-by: owner
        ---

        evidence
        """), encoding="utf-8")


def _roadmap(root: Path, body="# Roadmap\n") -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "roadmap.md").write_text(body, encoding="utf-8")
    (root / "docs" / "changes").mkdir(parents=True, exist_ok=True)


def _cdir(tmp_path: Path) -> Path:
    c = tmp_path / "claims"
    c.mkdir(exist_ok=True)
    return c


# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_work_item_done_archived(self, tmp_path):
        _archive_work_item(tmp_path, "C3-001")
        assert _board._work_item_done(tmp_path, "C3-001") is True

    def test_work_item_done_active_done(self, tmp_path):
        _active_work_item(tmp_path, "C3-002", status="verified")
        assert _board._work_item_done(tmp_path, "C3-002") is True

    def test_work_item_not_done_active_ready(self, tmp_path):
        _active_work_item(tmp_path, "C3-003", status="ready")
        assert _board._work_item_done(tmp_path, "C3-003") is False

    def test_work_item_missing_is_not_done(self, tmp_path):
        assert _board._work_item_done(tmp_path, "C3-404") is False

    def test_phase_exit_ready_all_met(self):
        status = {"criteria": [{"state": "met"}, {"state": "human-judgment"}]}
        assert _board._phase_exit_ready(status) is True

    def test_phase_exit_not_ready_with_unmet(self):
        status = {"criteria": [{"state": "met"}, {"state": "unmet"}]}
        assert _board._phase_exit_ready(status) is False

    def test_phase_exit_not_ready_no_criteria(self):
        assert _board._phase_exit_ready({"criteria": []}) is False

    def test_active_iteration_plan_ignores_legacy(self, tmp_path):
        # traces to a legacy T-NNN id → not iteration-prefixed → not a minted iteration.
        _iteration_plan(tmp_path, "legacy", ["T-063"])
        assert _board._active_iteration_plan(tmp_path) is None


# ---------------------------------------------------------------------------
# assess-iteration
# ---------------------------------------------------------------------------

class TestAssessIteration:
    def test_fires_when_exhausted_and_unassessed(self, tmp_path):
        _roadmap(tmp_path)
        _iteration_plan(tmp_path, "C3", ["C3-001", "C3-002"])
        _archive_work_item(tmp_path, "C3-001")
        _archive_work_item(tmp_path, "C3-002")

        d = _board.resolve_decision(tmp_path, _cdir(tmp_path))
        assert d["path"] == "assess-iteration"
        assert d["lane"]["task"] == "C3"
        assert d["lane"]["plan"].endswith("iteration-plans/C3.md")

    def test_does_not_fire_when_work_remains(self, tmp_path):
        # C3-002 still active/ready → a pickable lane exists → §1b pick wins.
        _roadmap(tmp_path)
        _iteration_plan(tmp_path, "C3", ["C3-001", "C3-002"])
        _archive_work_item(tmp_path, "C3-001")
        _active_work_item(tmp_path, "C3-002", status="ready")

        d = _board.resolve_decision(tmp_path, _cdir(tmp_path))
        assert d["path"] == "pick"
        assert d["lane"]["task"] == "C3-002"

    def test_does_not_fire_when_already_assessed(self, tmp_path):
        _roadmap(tmp_path)  # empty roadmap → nothing to promote
        _iteration_plan(tmp_path, "C3", ["C3-001"], assessed=True)
        _archive_work_item(tmp_path, "C3-001")

        d = _board.resolve_decision(tmp_path, _cdir(tmp_path))
        assert d["path"] != "assess-iteration"


# ---------------------------------------------------------------------------
# milestone-review
# ---------------------------------------------------------------------------

class TestMilestoneReview:
    def test_fires_when_phase_exit_ready_and_no_record(self, tmp_path):
        # elaboration GO → current phase construction; empty roadmap →
        # functionality_complete (roadmap-clear) met; human criteria pending.
        _roadmap(tmp_path)
        _milestone(tmp_path, "elaboration", 1, "GO")

        d = _board.resolve_decision(tmp_path, _cdir(tmp_path))
        assert d["path"] == "milestone-review"
        assert d["phase"] == "construction"
        assert d["cycle"] == 1
        assert d["lane"]["task"] == "construction"

    def test_does_not_fire_once_recorded(self, tmp_path):
        # A construction NO-GO keeps the derived phase at construction (only a GO
        # advances it), and _milestone_exists(construction,1) now suppresses a
        # re-review — the loop must not re-ask a decided milestone.
        _roadmap(tmp_path)
        _milestone(tmp_path, "elaboration", 1, "GO")
        _milestone(tmp_path, "construction", 1, "NO-GO")

        d = _board.resolve_decision(tmp_path, _cdir(tmp_path))
        assert d["phase"] == "construction"          # NO-GO did not advance phase
        assert d["path"] != "milestone-review"       # but the milestone isn't re-offered

    def test_pending_work_is_planned_not_reviewed(self, tmp_path):
        # construction phase but a pending roadmap task → functionality_complete
        # unmet → plan-iteration wins, not milestone-review.
        _roadmap(tmp_path, textwrap.dedent("""\
            # Roadmap

            ## T-200: pending work
            **Status**: pending
            **Priority**: high
            **Description**: do it.
            """))
        _milestone(tmp_path, "elaboration", 1, "GO")

        d = _board.resolve_decision(tmp_path, _cdir(tmp_path))
        assert d["path"] == "plan-iteration"
        assert d["lane"]["task"] == "T-200"

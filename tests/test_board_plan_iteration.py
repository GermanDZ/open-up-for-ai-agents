"""Unit tests for the phase-aware, iteration-scoped board resolve (T-077, R4).

Covers the iteration-prefix helpers, iteration-scoped `pick`, the relabelled
`plan-iteration` path (with its `promote` back-compat alias), and determinism
(divergence=0). Hermetic: temp repo skeleton + synthetic claim files.
"""

import importlib.util
import json
import textwrap
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_BOARD_PATH = _REPO / "scripts" / "openup-board.py"
_spec = importlib.util.spec_from_file_location("openup_board", _BOARD_PATH)
_board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_board)  # type: ignore[union-attr]


def _make_plan(root: Path, task_id: str, *, priority="high", status="ready",
               touches=None) -> None:
    touches = touches or [f"docs/changes/{task_id}/"]
    cdir = root / "docs" / "changes" / task_id
    cdir.mkdir(parents=True, exist_ok=True)
    touches_block = "\n".join(f"  - {t}" for t in touches)
    (cdir / "plan.md").write_text(textwrap.dedent(f"""\
        ---
        id: {task_id}
        title: "{task_id} lane"
        status: {status}
        priority: {priority}
        touches:
        {touches_block}
        ---

        # {task_id}

        ## Operations

        - [ ] Do the thing
        """), encoding="utf-8")


def _make_claim(cdir: Path, task_id: str) -> None:
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / f"{task_id}.json").write_text(json.dumps({
        "task_id": task_id,
        "session_id": "s",
        "branch": f"feat/{task_id}",
        "worktree": f"/tmp/{task_id}",
        "claimed_at": "2026-07-13T00:00:00Z",
        "touches": [f"docs/changes/{task_id}/"],
    }) + "\n", encoding="utf-8")


# ── iteration_prefix (pure) ─────────────────────────────────────────────────

class TestIterationPrefix:
    def test_prefixed_id(self):
        assert _board.iteration_prefix("C3-001") == "C3"

    def test_transition_iteration(self):
        assert _board.iteration_prefix("T1-002") == "T1"

    def test_legacy_task_id_is_none(self):
        # T-077 has no digit before the dash → not an iteration-prefixed id.
        assert _board.iteration_prefix("T-077") is None

    def test_none_input(self):
        assert _board.iteration_prefix(None) is None


# ── _active_iteration_prefix (from live claims) ─────────────────────────────

class TestActiveIterationPrefix:
    def test_single_iteration_lease(self, tmp_path):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "C3-001")
        assert _board._active_iteration_prefix(cdir) == "C3"

    def test_multiple_lanes_same_iteration(self, tmp_path):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "C3-001")
        _make_claim(cdir, "C3-002")
        assert _board._active_iteration_prefix(cdir) == "C3"

    def test_two_iterations_active_is_unscoped(self, tmp_path):
        # Parallel iterations (T-079) — no single active iteration to scope to.
        cdir = tmp_path / "claims"
        _make_claim(cdir, "C3-001")
        _make_claim(cdir, "C4-001")
        assert _board._active_iteration_prefix(cdir) is None

    def test_legacy_lease_is_unscoped(self, tmp_path):
        cdir = tmp_path / "claims"
        _make_claim(cdir, "T-077")
        assert _board._active_iteration_prefix(cdir) is None

    def test_no_claims_is_none(self, tmp_path):
        assert _board._active_iteration_prefix(tmp_path / "claims") is None


# ── resolve_decision: iteration-scoped pick ─────────────────────────────────

class TestIterationScopedPick:
    def test_pick_stays_within_active_iteration(self, tmp_path):
        """C3 is active (C3-001 leased). C4-001 is higher priority and would win
        without scoping; C3-002 is lower priority. Scoping must pick C3-002 and
        skip C4-001 (a different iteration waits its turn)."""
        root = tmp_path
        cdir = tmp_path / "claims"
        _make_claim(cdir, "C3-001")               # active-iteration marker (leased)
        _make_plan(root, "C3-002", priority="medium")
        _make_plan(root, "C4-001", priority="high")

        d = _board.resolve_decision(root, cdir)
        assert d["path"] == "pick"
        assert d["lane"]["task"] == "C3-002", "pick must stay in active iteration C3"

    def test_unscoped_when_no_iteration_active(self, tmp_path):
        """No prefixed lease → legacy behavior: top pickable by priority wins."""
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_plan(root, "C3-002", priority="medium")
        _make_plan(root, "C4-001", priority="high")

        d = _board.resolve_decision(root, cdir)
        assert d["path"] == "pick"
        assert d["lane"]["task"] == "C4-001"  # unscoped → highest priority


# ── resolve_decision: plan-iteration emission ───────────────────────────────

class TestPlanIterationPath:
    def _roadmap(self, root: Path) -> None:
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "roadmap.md").write_text(textwrap.dedent("""\
            # Roadmap

            ## T-100: A pending task
            **Status**: pending
            **Priority**: high
            **Description**: something to do.
            """), encoding="utf-8")
        (root / "docs" / "changes").mkdir(parents=True, exist_ok=True)

    def test_emits_plan_iteration_not_promote(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        self._roadmap(root)

        d = _board.resolve_decision(root, cdir)
        assert d["path"] == "plan-iteration"
        assert d["legacy_path"] == "promote", "back-compat alias for the T-077→T-078 window"
        assert d["lane"]["task"] == "T-100"   # single-work-item degeneration
        assert "phase" in d

    def test_decision_carries_phase_key_on_every_path(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        cdir.mkdir()
        self._roadmap(root)
        d = _board.resolve_decision(root, cdir)
        assert "phase" in d  # None is acceptable; the key must exist


# ── determinism ─────────────────────────────────────────────────────────────

class TestDivergenceZero:
    def test_resolve_is_deterministic(self, tmp_path):
        root = tmp_path
        cdir = tmp_path / "claims"
        _make_claim(cdir, "C3-001")
        _make_plan(root, "C3-002", priority="medium")
        _make_plan(root, "C4-001", priority="high")

        first = json.dumps(_board.resolve_decision(root, cdir), sort_keys=True)
        second = json.dumps(_board.resolve_decision(root, cdir), sort_keys=True)
        assert first == second, "two identical-input resolves must not diverge"

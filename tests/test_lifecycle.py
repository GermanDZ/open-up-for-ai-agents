"""Unit tests for openup-lifecycle.py (T-075).

Hermetic: each test builds a temporary repo skeleton (docs/ + .openup/) so no
real git state is needed. The lifecycle module is loaded by path because its
filename is hyphenated.
"""

import importlib.util
import json
import textwrap
from pathlib import Path

import pytest

_LC_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openup-lifecycle.py"
_spec = importlib.util.spec_from_file_location("openup_lifecycle", _LC_PATH)
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _write_state(root: Path, phase: str = "construction", **extra) -> None:
    sdir = root / ".openup"
    sdir.mkdir(parents=True, exist_ok=True)
    state = {"schema": 1, "task_id": "T-000", "phase": phase, "track": "standard",
             "gates": {}}
    state.update(extra)
    (sdir / "state.json").write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")


def _write_milestone(root: Path, name: str, phase: str, cycle: int,
                     decision: str, extra_fm: str = "") -> None:
    mdir = root / "docs" / "product" / "milestones"
    mdir.mkdir(parents=True, exist_ok=True)
    fm = textwrap.dedent(f"""\
        ---
        phase: {phase}
        cycle: {cycle}
        milestone: {phase.title()} milestone
        decision: {decision}
        date: 2026-07-13
        decided-by: owner
        {extra_fm}---

        evidence: ...
        """)
    (mdir / f"{name}.md").write_text(fm, encoding="utf-8")


def _write_instance(root: Path, rel: str, typ: str, status: str = "implemented") -> None:
    p = root / "docs" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntype: {typ}\nid: X\nstatus: {status}\n---\n\nbody\n",
                 encoding="utf-8")


def _sdir(root: Path) -> Path:
    return root / ".openup"


# ---------------------------------------------------------------------------
# R1 — phase derivation
# ---------------------------------------------------------------------------

def test_milestone_anchored_phase(tmp_path):
    """Latest GO milestone (elaboration) → current phase construction."""
    _write_state(tmp_path, phase="inception")  # stale; records win
    _write_milestone(tmp_path, "inception-1", "inception", 1, "GO")
    _write_milestone(tmp_path, "elaboration-1", "elaboration", 1, "GO")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    assert result["phase"] == "construction"
    assert result["cycle"] == 1
    assert result["source"] == "milestone"


def test_state_fallback_when_no_records(tmp_path):
    """No records → fall back to state phase, flagged state-fallback."""
    _write_state(tmp_path, phase="construction")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    assert result["phase"] == "construction"
    assert result["source"] == "state-fallback"
    assert result["records"] == 0


def test_no_go_keeps_current_phase(tmp_path):
    """A record without a GO keeps the phase at that record's phase."""
    _write_state(tmp_path, phase="inception")
    _write_milestone(tmp_path, "elaboration-1", "elaboration", 1, "CONDITIONAL")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    assert result["phase"] == "elaboration"
    assert result["source"] == "milestone"


def test_transition_go_is_released(tmp_path):
    _write_state(tmp_path, phase="transition")
    _write_milestone(tmp_path, "transition-1", "transition", 1, "GO")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    assert result["phase"] == "released"
    assert result["criteria"] == []


# ---------------------------------------------------------------------------
# R2 — criteria (met / unmet / human-judgment)
# ---------------------------------------------------------------------------

def test_inception_criteria_met_unmet_human(tmp_path):
    """Vision present → met; risk list absent → unmet; scope → human-judgment."""
    _write_state(tmp_path, phase="inception")
    _write_instance(tmp_path, "product/vision.md", "vision")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    crit = {c["id"]: c["state"] for c in result["criteria"]}
    assert crit["vision_defined"] == "met"
    assert crit["risk_list_present"] == "unmet"
    assert crit["scope_agreed"] == "human-judgment"


def test_risk_list_detected_by_keyword(tmp_path):
    _write_state(tmp_path, phase="inception")
    _write_instance(tmp_path, "product/risk-list.md", "requirement")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    crit = {c["id"]: c["state"] for c in result["criteria"]}
    assert crit["risk_list_present"] == "met"


def test_construction_functionality_unmet_with_open_folder(tmp_path):
    _write_state(tmp_path, phase="construction")
    plan = tmp_path / "docs" / "changes" / "T-001" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("---\nid: T-001\nstatus: in-progress\n---\n", encoding="utf-8")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    crit = {c["id"]: c["state"] for c in result["criteria"]}
    assert crit["functionality_complete"] == "unmet"


def test_construction_functionality_met_when_all_done(tmp_path):
    _write_state(tmp_path, phase="construction")
    plan = tmp_path / "docs" / "changes" / "T-001" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("---\nid: T-001\nstatus: done\n---\n", encoding="utf-8")
    result = lc.compute_status(tmp_path, _sdir(tmp_path))
    crit = {c["id"]: c["state"] for c in result["criteria"]}
    assert crit["functionality_complete"] == "met"


# ---------------------------------------------------------------------------
# R3 — malformed record
# ---------------------------------------------------------------------------

def test_malformed_record_missing_decision(tmp_path):
    _write_state(tmp_path, phase="inception")
    mdir = tmp_path / "docs" / "product" / "milestones"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "inception-1.md").write_text(
        "---\nphase: inception\ncycle: 1\n---\n", encoding="utf-8")
    with pytest.raises(ValueError) as e:
        lc.compute_status(tmp_path, _sdir(tmp_path))
    assert "inception-1.md" in str(e.value)
    assert "decision" in str(e.value)


def test_malformed_record_bad_phase(tmp_path):
    _write_state(tmp_path, phase="inception")
    mdir = tmp_path / "docs" / "product" / "milestones"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "bogus-1.md").write_text(
        "---\nphase: nonsense\ncycle: 1\ndecision: GO\n---\n", encoding="utf-8")
    with pytest.raises(ValueError) as e:
        lc.compute_status(tmp_path, _sdir(tmp_path))
    assert "bogus-1.md" in str(e.value)


def test_status_cli_exit2_on_malformed(tmp_path, capsys):
    _write_state(tmp_path, phase="inception")
    mdir = tmp_path / "docs" / "product" / "milestones"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "inception-1.md").write_text(
        "---\nphase: inception\ncycle: 1\n---\n", encoding="utf-8")
    rc = lc.main(["--repo-root", str(tmp_path), "--state-dir", str(_sdir(tmp_path)),
                  "status", "--json"])
    assert rc == lc.EXIT_USAGE
    assert "decision" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# R4 — stamp-phase idempotency
# ---------------------------------------------------------------------------

def test_stamp_phase_updates_and_is_idempotent(tmp_path):
    # state says elaboration; records resolve to construction
    _write_state(tmp_path, phase="elaboration")
    _write_milestone(tmp_path, "elaboration-1", "elaboration", 1, "GO")
    sdir = _sdir(tmp_path)
    rc = lc.main(["--repo-root", str(tmp_path), "--state-dir", str(sdir), "stamp-phase"])
    assert rc == lc.EXIT_OK
    assert json.loads((sdir / "state.json").read_text())["phase"] == "construction"
    # second run: byte-identical file
    before = (sdir / "state.json").read_bytes()
    rc2 = lc.main(["--repo-root", str(tmp_path), "--state-dir", str(sdir), "stamp-phase"])
    assert rc2 == lc.EXIT_OK
    assert (sdir / "state.json").read_bytes() == before


def test_stamp_phase_no_state(tmp_path, capsys):
    rc = lc.main(["--repo-root", str(tmp_path), "--state-dir", str(_sdir(tmp_path)),
                  "stamp-phase"])
    assert rc == lc.EXIT_NO_STATE
    assert "no state file" in capsys.readouterr().err

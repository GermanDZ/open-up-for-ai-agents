"""T-117 — `openup-doctor --fix` applies auto-heal-class findings.

One corrupted-state fixture per class, asserting the exploration's falsifiable
acceptance shape (2026-07-15-self-healing-interrupted-process-state.md §Refine):

  --fix restores every auto-heal-class finding (derived-view drift, single-valued
  unset plan_persisted gate) to green non-interactively, touches nothing in the
  confirm/human classes without --confirm, and is proven by corrupt→fix→clean.

Hermetic: each test builds a temp repo skeleton with only the stub scripts the
class under test needs; every other doctor check degrades to INFO (script absent)
and never errors. Stubs stand in for the real owning scripts so the test asserts
the *orchestration* (invoke owning script, re-detect) without a full framework.
"""

import importlib.util
import json
import os
import stat
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOCTOR_PATH = _REPO / "scripts" / "openup-doctor.py"
_spec = importlib.util.spec_from_file_location("openup_doctor", _DOCTOR_PATH)
doctor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(doctor)  # type: ignore[union-attr]


def _write_exec(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IRWXU)


def _mk_repo(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs").mkdir()
    return tmp_path


# ── Class A: derived-view drift heals ─────────────────────────────────────────
def test_auto_derived_view_drift_heals(tmp_path):
    repo = _mk_repo(tmp_path)
    index = repo / "docs" / "INDEX.md"
    index.write_text("STALE\n", encoding="utf-8")
    # Stub owning generator: --check fails while INDEX != GOOD; bare run regenerates.
    _write_exec(repo / "scripts" / "docs-index.py", (
        "#!/usr/bin/env python3\n"
        "import sys, pathlib\n"
        "idx = pathlib.Path(__file__).resolve().parents[1] / 'docs' / 'INDEX.md'\n"
        "if '--check' in sys.argv:\n"
        "    sys.exit(0 if idx.read_text() == 'GOOD\\n' else 1)\n"
        "idx.write_text('GOOD\\n'); sys.exit(0)\n"
    ))

    before = doctor.detect_all(repo.as_posix(), None)
    drift = [f for f in before if f.check == "aggregate" and "docs-index" in f.message]
    assert drift, "expected a docs-index drift finding"
    assert drift[0].fix_class == doctor.AUTO
    assert drift[0].fix_cmd == ["docs-index.py"]

    post, applied = doctor.apply_fixes(repo.as_posix(), before, confirm=False,
                                       framework_path=None)
    assert any("docs-index.py" in a and a.startswith("ran") for a in applied)
    assert index.read_text() == "GOOD\n"
    assert not [f for f in post if f.check == "aggregate" and "docs-index" in f.message
                and f.severity == doctor.WARNING], "drift should be gone after --fix"


# ── Class C: single-valued unset plan_persisted gate heals ────────────────────
def test_auto_plan_gate_heals(tmp_path):
    repo = _mk_repo(tmp_path)
    (repo / ".openup").mkdir()
    state = repo / ".openup" / "state.json"
    state.write_text(json.dumps({"task_id": "T-999", "gates": {"plan_persisted": False}}),
                     encoding="utf-8")
    plan = repo / "docs" / "changes" / "T-999"
    plan.mkdir(parents=True)
    (plan / "plan.md").write_text("---\nid: T-999\n---\nbody\n", encoding="utf-8")
    # Stub owning script: `set-gate plan_persisted <path>` flips the gate; `validate` ok.
    _write_exec(repo / "scripts" / "openup-state.py", (
        "#!/usr/bin/env python3\n"
        "import sys, json, pathlib\n"
        "st = pathlib.Path(__file__).resolve().parents[1] / '.openup' / 'state.json'\n"
        "if sys.argv[1:2] == ['validate']:\n"
        "    sys.exit(0)\n"
        "if sys.argv[1:3] == ['set-gate', 'plan_persisted']:\n"
        "    d = json.loads(st.read_text()); d['gates']['plan_persisted'] = sys.argv[3]\n"
        "    st.write_text(json.dumps(d)); sys.exit(0)\n"
        "sys.exit(2)\n"
    ))

    before = doctor.detect_all(repo.as_posix(), None)
    gate = [f for f in before if f.check == "plan-gate"]
    assert gate, "expected a plan-gate finding"
    assert gate[0].fix_class == doctor.AUTO
    assert gate[0].fix_cmd[:3] == ["openup-state.py", "set-gate", "plan_persisted"]

    post, applied = doctor.apply_fixes(repo.as_posix(), before, confirm=False,
                                       framework_path=None)
    assert any("set-gate" in a and a.startswith("ran") for a in applied)
    assert json.loads(state.read_text())["gates"]["plan_persisted"]
    assert not [f for f in post if f.check == "plan-gate"], "gate finding should be gone"


def test_plan_gate_not_flagged_when_no_plan(tmp_path):
    # Boundary: unset gate but NO plan.md → not the single-valued case, no finding.
    repo = _mk_repo(tmp_path)
    (repo / ".openup").mkdir()
    (repo / ".openup" / "state.json").write_text(
        json.dumps({"task_id": "T-999", "gates": {"plan_persisted": False}}),
        encoding="utf-8")
    assert not [f for f in doctor.detect_all(repo.as_posix(), None) if f.check == "plan-gate"]


# ── Boundary: confirm/human classes untouched without --confirm ───────────────
def _sentinel_fix(repo: Path, name: str) -> list:
    """A stub script that writes a sentinel when invoked; returns its fix_cmd."""
    _write_exec(repo / "scripts" / name, (
        "#!/usr/bin/env python3\n"
        "import pathlib\n"
        f"(pathlib.Path(__file__).resolve().parents[1] / '{name}.ran').write_text('x')\n"
    ))
    return [name]


def test_confirm_and_human_boundary(tmp_path):
    repo = _mk_repo(tmp_path)
    confirm_cmd = _sentinel_fix(repo, "confirm-fix.py")
    human_cmd = _sentinel_fix(repo, "human-fix.py")
    auto_cmd = _sentinel_fix(repo, "auto-fix.py")
    findings = [
        doctor.Finding(doctor.WARNING, "x", "auto", doctor.AUTO, auto_cmd),
        doctor.Finding(doctor.WARNING, "x", "confirm", doctor.CONFIRM, confirm_cmd),
        doctor.Finding(doctor.WARNING, "x", "human", doctor.HUMAN, human_cmd),
    ]

    # Without --confirm: only the auto fix runs.
    doctor.apply_fixes(repo.as_posix(), findings, confirm=False, framework_path=None)
    assert (repo / "auto-fix.py.ran").exists()
    assert not (repo / "confirm-fix.py.ran").exists()
    assert not (repo / "human-fix.py.ran").exists()
    # Confirm-class is surfaced as a proposal (not silently dropped).
    props = doctor.unapplied_proposals(findings, confirm=False)
    assert [f.message for f in props] == ["confirm"]

    # With --confirm: confirm fix runs too; human is still never touched.
    doctor.apply_fixes(repo.as_posix(), findings, confirm=True, framework_path=None)
    assert (repo / "confirm-fix.py.ran").exists()
    assert not (repo / "human-fix.py.ran").exists()
    assert doctor.unapplied_proposals(findings, confirm=True) == []


# ── Default run stays read-only (no --fix) ────────────────────────────────────
def test_default_run_is_read_only(tmp_path):
    repo = _mk_repo(tmp_path)
    index = repo / "docs" / "INDEX.md"
    index.write_text("STALE\n", encoding="utf-8")
    _write_exec(repo / "scripts" / "docs-index.py", (
        "#!/usr/bin/env python3\n"
        "import sys, pathlib\n"
        "idx = pathlib.Path(__file__).resolve().parents[1] / 'docs' / 'INDEX.md'\n"
        "if '--check' in sys.argv:\n"
        "    sys.exit(0 if idx.read_text() == 'GOOD\\n' else 1)\n"
        "idx.write_text('GOOD\\n'); sys.exit(0)\n"
    ))
    rc = doctor.main(["--repo-root", repo.as_posix(), "--json"])
    assert rc == 0  # drift is a WARNING, not an error
    assert index.read_text() == "STALE\n", "default (no --fix) run must write nothing"

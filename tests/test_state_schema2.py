"""Unit tests for openup-state.py schema 2 (T-078).

Schema 2 names the iteration (`iteration_id`) and project cycle (`cycle`) and
documents `phase` as a derived cache. A schema-1 state file is auto-migrated to
schema 2 on read (additively, in place). Hermetic: each test uses a temporary
--state-dir; the module is loaded by path (hyphenated filename).
"""

import importlib.util
import json
from pathlib import Path

import pytest

_ST_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openup-state.py"
_spec = importlib.util.spec_from_file_location("openup_state", _ST_PATH)
st = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(st)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

SCHEMA1 = {
    "schema": 1,
    "task_id": "T-050",
    "iteration": 5,
    "phase": "construction",
    "track": "standard",
    "branch": "feat/x",
    "worktree": "/w",
    "session_id": None,
    "started_at": "2026-01-01T00:00:00Z",
    "gates": {
        "team_deployed": False,
        "plan_persisted": False,
        "log_written": False,
        "roadmap_synced": False,
        "retro_due": False,
    },
    "iterations_since_retro": 0,
}


def _write(sdir: Path, state: dict) -> Path:
    sdir.mkdir(parents=True, exist_ok=True)
    p = sdir / "state.json"
    p.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return p


def _read(sdir: Path) -> dict:
    return json.loads((sdir / "state.json").read_text(encoding="utf-8"))


def _init(sdir: Path, extra=None):
    argv = [
        "init", "--task-id", "T-078", "--iteration", "48",
        "--phase", "construction", "--track", "standard",
        "--branch", "feat/x", "--worktree", "/w",
        "--state-dir", str(sdir),
    ]
    if extra:
        argv += extra
    return st.main(argv)


# ---------------------------------------------------------------------------
# R5 — init writes schema 2
# ---------------------------------------------------------------------------

def test_init_writes_schema2_with_defaults(tmp_path):
    sdir = tmp_path / ".openup"
    assert _init(sdir) == 0
    state = _read(sdir)
    assert state["schema"] == 2
    assert state["iteration_id"] is None      # single-lane default
    assert state["cycle"] == 1
    # validate agrees
    assert st.main(["validate", "--state-dir", str(sdir)]) == 0


def test_init_carries_iteration_id_and_cycle(tmp_path):
    sdir = tmp_path / ".openup"
    assert _init(sdir, ["--iteration-id", "C3", "--cycle", "2"]) == 0
    state = _read(sdir)
    assert state["iteration_id"] == "C3"
    assert state["cycle"] == 2


# ---------------------------------------------------------------------------
# R5 — schema-1 → schema-2 migration on read
# ---------------------------------------------------------------------------

def test_schema1_migrates_on_read_in_place(tmp_path):
    sdir = tmp_path / ".openup"
    _write(sdir, SCHEMA1)
    # `get` reads → migrates → persists.
    assert st.main(["get", "--state-dir", str(sdir)]) == 0
    on_disk = _read(sdir)
    assert on_disk["schema"] == 2
    assert on_disk["iteration_id"] is None
    assert on_disk["cycle"] == 1
    # existing fields preserved (additive migration)
    assert on_disk["task_id"] == "T-050"
    assert on_disk["iteration"] == 5
    assert on_disk["gates"]["plan_persisted"] is False


def test_migrated_schema1_validates(tmp_path):
    sdir = tmp_path / ".openup"
    _write(sdir, SCHEMA1)
    # validate() reads → migrates → then validates the schema-2 result: exit 0.
    assert st.main(["validate", "--state-dir", str(sdir)]) == 0


def test_migrate_state_is_pure_and_idempotent():
    # schema-1 dict upgrades once; a second pass is a no-op.
    s1 = dict(SCHEMA1)
    upgraded, changed = st.migrate_state(s1)
    assert changed is True and upgraded["schema"] == 2
    again, changed2 = st.migrate_state(upgraded)
    assert changed2 is False and again["schema"] == 2


def test_migrate_preserves_explicit_iteration_fields():
    # A partially-upgraded file that already carries iteration_id must not be
    # clobbered back to null.
    partial = dict(SCHEMA1)
    partial["iteration_id"] = "C7"
    partial["cycle"] = 4
    upgraded, changed = st.migrate_state(partial)
    assert changed is True  # schema bumped
    assert upgraded["iteration_id"] == "C7"
    assert upgraded["cycle"] == 4


# ---------------------------------------------------------------------------
# Negative — a genuinely invalid state is still rejected
# ---------------------------------------------------------------------------

def test_invalid_state_rejected_by_validate(tmp_path):
    sdir = tmp_path / ".openup"
    bad = dict(SCHEMA1)
    bad["schema"] = 2            # claims schema 2 but omits the new required keys
    _write(sdir, bad)           # no iteration_id / cycle, and migrate won't add (schema already 2)
    with pytest.raises(SystemExit) as ei:
        st.main(["validate", "--state-dir", str(sdir)])
    assert ei.value.code == st.EXIT_INVALID

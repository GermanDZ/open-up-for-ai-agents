"""Unit tests for openup-process-map.py — the process map loader + iteration
minting (T-077, R1 + R3).

Hermetic: the loader reads the shipped docs-eng-process/process-map.yaml for the
real-file assertions, and a temp fixture map for the negative-validate case;
minting scans a temp repo skeleton (roadmap text + change-folder names).
"""

import importlib.util
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_PM_PATH = _REPO / "scripts" / "openup-process-map.py"
_spec = importlib.util.spec_from_file_location("openup_process_map", _PM_PATH)
_pm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pm)  # type: ignore[union-attr]


# ── R1: load + queries against the shipped map ──────────────────────────────

class TestShippedMap:
    def test_shipped_map_validates(self):
        mp = _pm.load_map(_REPO)
        assert _pm.validate(mp) == [], "the shipped process-map.yaml must be valid"

    def test_all_four_phases_present(self):
        mp = _pm.load_map(_REPO)
        assert set(mp["phases"]) == {
            "inception", "elaboration", "construction", "transition"}

    def test_construction_activities_resolve_to_role_and_skills(self):
        mp = _pm.load_map(_REPO)
        acts = _pm.activities_for(mp, "construction")
        names = [a["name"] for a in acts]
        # KB §4 Construction composition, in order.
        assert names == [
            "identify-refine-requirements", "develop-solution-increment",
            "test-solution", "plan-manage-iteration"]
        dev = next(a for a in acts if a["name"] == "develop-solution-increment")
        assert dev["role"] == "developer"
        assert "openup-tdd-workflow" in dev["skills"]

    def test_inception_is_analyst_led_vision_and_requirements(self):
        mp = _pm.load_map(_REPO)
        acts = _pm.activities_for(mp, "inception")
        initiate = next(a for a in acts if a["name"] == "initiate-project")
        assert initiate["role"] == "analyst"
        assert "openup-create-vision" in initiate["skills"]

    def test_phase_letters(self):
        mp = _pm.load_map(_REPO)
        assert _pm.phase_letter(mp, "construction") == "C"
        assert _pm.phase_letter(mp, "inception") == "I"

    def test_unknown_phase_raises(self):
        mp = _pm.load_map(_REPO)
        with pytest.raises(_pm.MapError):
            _pm.activities_for(mp, "nonexistent")


# ── R1: negative validate on a fixture map ──────────────────────────────────

def _write_map(root: Path, body: str) -> None:
    d = root / "docs-eng-process"
    d.mkdir(parents=True, exist_ok=True)
    (d / "process-map.yaml").write_text(body, encoding="utf-8")


class TestValidateCatchesDrift:
    def test_phase_referencing_undefined_activity_fails(self, tmp_path):
        _write_map(tmp_path, (
            "phases:\n"
            "  construction: [develop-solution-increment, ghost-activity]\n"
            "activities:\n"
            "  develop-solution-increment: { role: developer, skills: [openup-tdd-workflow] }\n"
            "phase_letters:\n"
            "  construction: C\n"
        ))
        mp = _pm.load_map(tmp_path)
        problems = _pm.validate(mp)
        assert any("ghost-activity" in p for p in problems)

    def test_missing_phase_letter_fails(self, tmp_path):
        _write_map(tmp_path, (
            "phases:\n"
            "  construction: [develop-solution-increment]\n"
            "activities:\n"
            "  develop-solution-increment: { role: developer, skills: [] }\n"
            "phase_letters:\n"
            "  inception: I\n"
        ))
        mp = _pm.load_map(tmp_path)
        assert any("phase_letters" in p for p in _pm.validate(mp))

    def test_missing_map_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _pm.load_map(tmp_path)


# ── R3: iteration-id minting ────────────────────────────────────────────────

def _make_repo(root: Path, roadmap: str = "", change_folders=()) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "roadmap.md").write_text(roadmap, encoding="utf-8")
    changes = root / "docs" / "changes"
    changes.mkdir(parents=True, exist_ok=True)
    for name in change_folders:
        (changes / name).mkdir(parents=True, exist_ok=True)


class TestMintIterationId:
    def test_first_iteration_is_ordinal_1(self, tmp_path):
        _make_repo(tmp_path)
        mp = _pm.load_map(_REPO)
        assert _pm.mint_iteration_id(tmp_path, mp, "construction") == "C1"

    def test_ordinal_is_repo_monotonic(self, tmp_path):
        # Two prior Construction iterations exist (lanes C1-001, C2-003).
        _make_repo(tmp_path, roadmap="- C1-001 done\n- C2-003 done\n")
        mp = _pm.load_map(_REPO)
        assert _pm.mint_iteration_id(tmp_path, mp, "construction") == "C3"

    def test_counts_change_folder_names(self, tmp_path):
        _make_repo(tmp_path, change_folders=["C1-001", "C1-002"])
        mp = _pm.load_map(_REPO)
        assert _pm.mint_iteration_id(tmp_path, mp, "construction") == "C2"

    def test_legacy_task_ids_do_not_inflate_ordinal(self, tmp_path):
        # T-077 is a legacy id (no digit before the dash) — must NOT count as a
        # Transition iteration. Transition should still mint T1.
        _make_repo(tmp_path, roadmap="- T-077 done\n- T-076 done\n",
                   change_folders=["T-077", "T-076"])
        mp = _pm.load_map(_REPO)
        assert _pm.mint_iteration_id(tmp_path, mp, "transition") == "T1"

    def test_different_phases_are_independent(self, tmp_path):
        _make_repo(tmp_path, roadmap="- C5-001 done\n")
        mp = _pm.load_map(_REPO)
        assert _pm.mint_iteration_id(tmp_path, mp, "construction") == "C6"
        assert _pm.mint_iteration_id(tmp_path, mp, "elaboration") == "E1"


# ── T-139: project-owned process sources ────────────────────────────────────
# A project overrides the framework's map/library by creating docs/process/*.yaml.
# The pair of concerns these tests pin: the override WINS when present, and its
# absence changes nothing (the "additive only" safeguard — these no-override
# cases were written and passing BEFORE the candidate tuples gained the new
# entry, so they are a real regression guard, not a description of new code).

_MARKER_MAP = (
    "phases:\n"
    "  construction: [{activity}]\n"
    "activities:\n"
    "  {activity}: {{ role: developer, skills: [] }}\n"
    "phase_letters:\n"
    "  construction: C\n"
)

_MARKER_LIB = (
    "tasks:\n"
    "  {task_id}:\n"
    "    name: Marker Task\n"
    "    role: analyst\n"
    "    artifact: vision\n"
    "    output_path: docs/vision.md\n"
    "    source: driver\n"
    "    inputs:\n"
    "      - Stakeholder Requests\n"
    "    judgment:\n"
    "      - First judgment bullet for the marker task.\n"
    "      - Second judgment bullet for the marker task.\n"
    "      - Third judgment bullet for the marker task.\n"
)


def _write_yaml(root: Path, rel: str, body: str) -> None:
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")


class TestNoOverrideIsUnchanged:
    """R2 — a repo with no docs/process/ resolves the vendored copies, exactly
    as it did before the project-owned candidate existed."""

    def test_map_without_override_comes_from_vendored_copy(self, tmp_path):
        _write_yaml(tmp_path, "docs-eng-process/process-map.yaml",
                    _MARKER_MAP.format(activity="vendored-activity"))
        mp = _pm.load_map(tmp_path)
        assert [a["name"] for a in _pm.activities_for(mp, "construction")] == [
            "vendored-activity"]

    def test_library_without_override_comes_from_vendored_copy(self, tmp_path):
        _write_yaml(tmp_path, "docs-eng-process/task-library.yaml",
                    _MARKER_LIB.format(task_id="vendored-task"))
        assert list(_pm.load_tasks(tmp_path)) == ["vendored-task"]

    def test_this_repo_still_resolves_the_framework_library(self):
        # This repo has no docs/process/ (and must not — see the spec's
        # "must not shadow itself" safeguard), so the framework's own defs win.
        tasks = _pm.load_tasks(_REPO)
        assert "develop-technical-vision" in tasks
        assert _pm.validate_tasks(tasks) == []

    def test_this_repo_still_resolves_the_framework_map(self):
        mp = _pm.load_map(_REPO)
        assert _pm.validate(mp) == []
        assert set(mp["phases"]) == {
            "inception", "elaboration", "construction", "transition"}


class TestProjectOwnedOverrideWins:
    """R1 — docs/process/ resolves ahead of the vendored docs-eng-process/ copy."""

    def test_project_map_shadows_vendored_map(self, tmp_path):
        _write_yaml(tmp_path, "docs-eng-process/process-map.yaml",
                    _MARKER_MAP.format(activity="vendored-activity"))
        _write_yaml(tmp_path, "docs/process/process-map.yaml",
                    _MARKER_MAP.format(activity="project-activity"))
        mp = _pm.load_map(tmp_path)
        assert [a["name"] for a in _pm.activities_for(mp, "construction")] == [
            "project-activity"]

    def test_project_library_shadows_vendored_library(self, tmp_path):
        _write_yaml(tmp_path, "docs-eng-process/task-library.yaml",
                    _MARKER_LIB.format(task_id="vendored-task"))
        _write_yaml(tmp_path, "docs/process/task-library.yaml",
                    _MARKER_LIB.format(task_id="project-task"))
        tasks = _pm.load_tasks(tmp_path)
        # Replace, not merge: the vendored def is gone, not shadowed per-key.
        assert list(tasks) == ["project-task"]
        assert _pm.validate_tasks(tasks) == []

    def test_escape_hatch_loses_to_both(self, tmp_path):
        _write_yaml(tmp_path, "scripts/task-library.yaml",
                    _MARKER_LIB.format(task_id="escape-hatch-task"))
        _write_yaml(tmp_path, "docs-eng-process/task-library.yaml",
                    _MARKER_LIB.format(task_id="vendored-task"))
        assert list(_pm.load_tasks(tmp_path)) == ["vendored-task"]


class TestCompilerHonoursProjectOverride:
    """R3 — build-task-library.py --check resolves the same project-owned library
    (it shares load_tasks), so a project's own defs are checkable."""

    def test_check_passes_against_project_owned_library(self, tmp_path):
        import subprocess
        import sys
        _write_yaml(tmp_path, "docs/process/task-library.yaml",
                    _MARKER_LIB.format(task_id="project-task"))
        proc = subprocess.run(
            [sys.executable, str(_REPO / "scripts" / "build-task-library.py"),
             "--repo-root", str(tmp_path), "--check"],
            capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        assert "in sync" in proc.stdout

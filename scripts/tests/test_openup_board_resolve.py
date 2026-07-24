#!/usr/bin/env python3
"""Unit tests for openup-board.py `resolve` / `status` (T-065).

Run with either:
    python3 -m unittest scripts.tests.test_openup_board_resolve
    python3 scripts/tests/test_openup_board_resolve.py

Hermetic: each test builds an isolated fixture repo (docs/changes/*/plan.md,
docs/roadmap.md, docs/input-requests/*.md, .openup/state.json) and an injected
--claims-dir, so it never touches the live repo or real leases. `resolve` is
exercised through the CLI exactly as /openup-next §0–§1 would call it.

Path coverage: one fixture forces each `path` ∈ {resume(active), resume(input),
pick, promote, noop}. Plus the two invariants the spec calls out: `resolve`
writes nothing (read-only) and its output stays within the ~40-line budget.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-board.py"

OK, USAGE, NONE_PICKABLE = 0, 2, 3


# --------------------------------------------------------------------------
# Fixture builders
# --------------------------------------------------------------------------
def write_plan(root, task_id, *, title="T", status="ready", priority="medium",
               depends_on=None, touches=None, operations=None):
    folder = root / "docs" / "changes" / task_id
    folder.mkdir(parents=True, exist_ok=True)
    fm = [f"id: {task_id}", f"title: {title}", f"status: {status}",
          f"priority: {priority}", "depends-on: [%s]" % ", ".join(depends_on or [])]
    if touches:
        fm.append("touches: [%s]" % ", ".join(touches))
    body = ["---", *fm, "---", "", f"# {task_id} — {title}", "", "## Operations", ""]
    body.extend(operations or ["- [ ] do the thing"])
    body.append("")
    (folder / "plan.md").write_text("\n".join(body), encoding="utf-8")


def write_roadmap(root, rows):
    """rows: list of (task_id, status) → manual `## T-NNN:` sections."""
    lines = ["# Roadmap", ""]
    for task_id, status in rows:
        lines += [f"## {task_id}: fixture task {task_id}",
                  f"**Status**: {status}", "**Priority**: high", ""]
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "roadmap.md").write_text("\n".join(lines), encoding="utf-8")


def write_state(root, task_id):
    d = root / ".openup"
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(json.dumps({
        "schema": 1, "task_id": task_id, "iteration": 1,
        "phase": "construction", "track": "standard",
    }), encoding="utf-8")


def write_answered_input(root, task_id, name="req-1.md"):
    d = root / "docs" / "input-requests"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(
        f"---\nstatus: answered\nrelated_task: {task_id}\ntitle: Q\n---\n\nA.\n",
        encoding="utf-8")


def resolve(root, cdir, verb="resolve", expect=OK):
    out = root / ".openup" / "board.json"
    cmd = [sys.executable, str(SCRIPT), verb,
           "--root", str(root), "--claims-dir", str(cdir), "--out", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == expect, (
        f"expected exit {expect}, got {proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


class ResolvePathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cdir = self.root / "claims"
        self.cdir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self._tmp.cleanup()

    def decision(self, verb="resolve"):
        return json.loads(resolve(self.root, self.cdir, verb).stdout)

    # -- path coverage -----------------------------------------------------
    def test_resume_active_iteration(self):
        """An active .openup/state.json → path=resume via active_iteration."""
        write_state(self.root, "T-900")
        write_plan(self.root, "T-901")  # a pickable lane exists, but active wins
        d = self.decision()
        self.assertEqual(d["path"], "resume")
        self.assertEqual(d["active_iteration"], {"task": "T-900"})
        self.assertEqual(d["lane"]["task"], "T-900")

    def test_resume_answered_input_outranks_active(self):
        """§0 answered-input outranks §1a active iteration."""
        write_answered_input(self.root, "T-800")
        write_state(self.root, "T-900")
        d = self.decision()
        self.assertEqual(d["path"], "resume")
        self.assertEqual(d["resumable_input"]["task"], "T-800")
        self.assertEqual(d["lane"]["task"], "T-800")

    def test_pick_top_lane(self):
        """No active iteration / input, but a READY change-folder lane → pick."""
        write_plan(self.root, "T-901", status="ready")
        d = self.decision()
        self.assertEqual(d["path"], "pick")
        self.assertEqual(d["lane"]["task"], "T-901")

    def test_promote_roadmap_task(self):
        """No lanes at all, but a pending roadmap task → plan-iteration (the
        promote path, renamed to plan-iteration in T-078; legacy_path == promote)."""
        write_roadmap(self.root, [("T-950", "pending")])
        d = self.decision()
        self.assertEqual(d["path"], "plan-iteration")
        self.assertEqual(d.get("legacy_path"), "promote")
        self.assertEqual((d.get("lane") or {}).get("task"), "T-950")

    def _write_process_map(self):
        d = self.root / "docs-eng-process"
        d.mkdir(parents=True, exist_ok=True)
        (d / "process-map.yaml").write_text(
            "phases:\n  inception: [initiate-project]\n"
            "activities:\n  initiate-project: { role: analyst, "
            "skills: [openup-create-vision] }\n"
            "phase_letters:\n  inception: I\n", encoding="utf-8")

    def test_fresh_inception_plans_from_map(self):
        """T-101: a fresh authoring phase (inception; unmet machine criteria) with
        no roadmap and a process map → plan-iteration, phase-driven (no lane)."""
        self._write_process_map()  # no roadmap, no vision, no state
        d = self.decision()
        self.assertEqual(d["path"], "plan-iteration")
        self.assertEqual(d["phase"], "inception")
        self.assertEqual(d.get("legacy_path"), "plan-fresh")
        self.assertIsNone(d.get("lane"))

    def test_fresh_without_process_map_stays_noop(self):
        """Fail-open: no process map → the fresh trigger cannot resolve
        activities, so it does not fire (noop), never a crash."""
        d = self.decision()  # no process-map.yaml seeded
        self.assertEqual(d["path"], "noop")

    def test_promote_matches_roadmap_next(self):
        """resolve's promote pick == `openup-roadmap.py next` (no divergence)."""
        write_roadmap(self.root, [("T-950", "pending"), ("T-951", "pending")])
        d = self.decision()
        rm = Path(__file__).resolve().parents[1] / "openup-roadmap.py"
        proc = subprocess.run(
            [sys.executable, str(rm), "next", "--root", str(self.root),
             "--claims-dir", str(self.cdir)], capture_output=True, text=True)
        self.assertEqual(json.loads(proc.stdout)["id"], d["lane"]["task"])

    def test_noop_when_exhausted(self):
        """No lanes, no promotable roadmap task → noop with a specific reason."""
        write_roadmap(self.root, [("T-950", "completed")])
        d = self.decision()
        self.assertEqual(d["path"], "noop")
        self.assertTrue(d["reason"])
        self.assertIsNone(d["lane"])

    # -- invariants --------------------------------------------------------
    def test_resolve_is_read_only(self):
        """resolve mutates nothing: state.json, roadmap.md, claims, and any
        pre-existing board.json are byte-identical after the call."""
        write_state(self.root, "T-900")
        write_roadmap(self.root, [("T-950", "pending")])
        board = self.root / ".openup" / "board.json"
        board.parent.mkdir(parents=True, exist_ok=True)
        board.write_text('{"sentinel": true}\n', encoding="utf-8")
        snap = {p: p.read_bytes() for p in [
            self.root / ".openup" / "state.json",
            self.root / "docs" / "roadmap.md",
            board,
        ]}
        claim_before = sorted(x.name for x in self.cdir.glob("*"))
        resolve(self.root, self.cdir)
        for p, before in snap.items():
            self.assertEqual(p.read_bytes(), before, f"{p.name} mutated by resolve")
        self.assertEqual(sorted(x.name for x in self.cdir.glob("*")), claim_before)

    def test_line_budget(self):
        """resolve output stays within the ~40-line budget on a real path."""
        write_plan(self.root, "T-901", status="ready")
        proc = resolve(self.root, self.cdir)
        self.assertLessEqual(len(proc.stdout.splitlines()), 40)

    # -- status ------------------------------------------------------------
    def test_status_superset(self):
        """status reports active iteration + leases + pickable + promotable."""
        write_state(self.root, "T-900")
        write_plan(self.root, "T-901", status="ready")
        write_roadmap(self.root, [("T-950", "pending")])
        d = self.decision("status")
        self.assertEqual(d["active_iteration"], {"task": "T-900"})
        self.assertIn("leases", d)
        self.assertIn("pickable", d)
        self.assertIn("promotable_next", d)


if __name__ == "__main__":
    unittest.main()

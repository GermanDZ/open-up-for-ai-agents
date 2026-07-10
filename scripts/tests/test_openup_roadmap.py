#!/usr/bin/env python3
"""Unit tests for scripts/openup-roadmap.py (T-064).

Run with either:
    python3 -m unittest scripts.tests.test_openup_roadmap
    python3 scripts/tests/test_openup_roadmap.py

Hermetic: each test builds an isolated fixture repo (docs/roadmap.md + optional
change folders) and an injected --claims-dir, so it never touches the live repo
or real leases. The script is exercised through its CLI exactly as /openup-next
would.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-roadmap.py"

OK, USAGE, NONE = 0, 2, 3


# A fixture roadmap exercising BOTH entry shapes: a table block and manual
# ## T-NNN: sections, interleaved with prose (which must not confuse the parser).
FIXTURE = """# Roadmap

### Maintenance (standalone fixes)

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-100 | A done table task | completed (2026-01-01) | medium | — |
| [T-101](changes/T-101/plan.md) | A pending table task | pending | high | T-100 |

**Value (T-101)**: some multi-paragraph prose that is not a table row and
must be ignored by the parser.

## T-200: A pending section task
**Status**: pending
**Priority**: high
**Value**: ships the thing
**Description**: do it
**Dependencies**: none
**See**: `docs/iteration-plans/t-200.md`

---

## T-201: A section task blocked on T-200
**Status**: pending
**Priority**: medium
**Dependencies**: T-200
**See**: `docs/iteration-plans/t-201.md`
"""


def make_repo(roadmap=FIXTURE):
    root = Path(tempfile.mkdtemp(prefix="openup-roadmap-test-"))
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "roadmap.md").write_text(roadmap, encoding="utf-8")
    cdir = root / "_claims"
    cdir.mkdir(parents=True, exist_ok=True)
    return root, cdir


def active_folder(root, task_id, status="ready"):
    folder = root / "docs" / "changes" / task_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.md").write_text(
        f"---\nid: {task_id}\nstatus: {status}\n---\n# {task_id}\n", encoding="utf-8")


def archived_folder(root, task_id):
    folder = root / "docs" / "changes" / "archive" / task_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.md").write_text(f"# {task_id} (archived)\n", encoding="utf-8")


def write_claim(cdir, task_id, session="S1"):
    (cdir / f"{task_id}.json").write_text(json.dumps({
        "task_id": task_id, "session_id": session, "touches": [],
        "branch": f"feat/{task_id}", "worktree": f"/tmp/wt-{task_id}",
        "claimed_at": "2026-01-01T00:00:00Z",
    }), encoding="utf-8")


def run(root, cdir, *cli, expect=None):
    cmd = [sys.executable, str(SCRIPT), *cli,
           "--root", str(root), "--claims-dir", str(cdir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"expected exit {expect}, got {proc.returncode}\n"
            f"cli={cli}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


class ParseAndList(unittest.TestCase):
    def test_list_pending_both_shapes_in_document_order(self):
        root, cdir = make_repo()
        out = json.loads(run(root, cdir, "list", "--status", "pending",
                             expect=OK).stdout)
        ids = [e["id"] for e in out]
        # Table-row pending (T-101) then section pendings (T-200, T-201) — the
        # order they occur in the file. T-100 is completed → excluded.
        self.assertEqual(ids, ["T-101", "T-200", "T-201"])

    def test_list_captures_section_fields(self):
        root, cdir = make_repo()
        out = json.loads(run(root, cdir, "list", "--status", "pending",
                             expect=OK).stdout)
        t200 = next(e for e in out if e["id"] == "T-200")
        self.assertEqual(t200["priority"], "high")
        self.assertEqual(t200["value"], "ships the thing")
        self.assertEqual(t200["depends_on"], [])
        self.assertEqual(t200["see"], "docs/iteration-plans/t-200.md")

    def test_list_default_is_promotable(self):
        root, cdir = make_repo()
        out = json.loads(run(root, cdir, "list", expect=OK).stdout)
        self.assertEqual([e["id"] for e in out], ["T-101", "T-200", "T-201"])

    def test_list_completed(self):
        root, cdir = make_repo()
        out = json.loads(run(root, cdir, "list", "--status", "completed",
                             expect=OK).stdout)
        self.assertEqual([e["id"] for e in out], ["T-100"])

    def test_list_all(self):
        root, cdir = make_repo()
        out = json.loads(run(root, cdir, "list", "--status", "all",
                             expect=OK).stdout)
        self.assertEqual([e["id"] for e in out],
                         ["T-100", "T-101", "T-200", "T-201"])


class Get(unittest.TestCase):
    def test_get_hit(self):
        root, cdir = make_repo()
        e = json.loads(run(root, cdir, "get", "T-200", expect=OK).stdout)
        self.assertEqual(e["id"], "T-200")

    def test_get_miss_exits_nonzero(self):
        root, cdir = make_repo()
        proc = run(root, cdir, "get", "T-999", expect=NONE)
        self.assertIn("not found", proc.stderr)


class Next(unittest.TestCase):
    def test_next_returns_first_promotable(self):
        # T-101 depends on T-100 (completed) → promotable and first in order.
        root, cdir = make_repo()
        e = json.loads(run(root, cdir, "next", expect=OK).stdout)
        self.assertEqual(e["id"], "T-101")

    def test_next_skips_active_folder(self):
        root, cdir = make_repo()
        active_folder(root, "T-101")  # already a lane
        e = json.loads(run(root, cdir, "next", expect=OK).stdout)
        self.assertEqual(e["id"], "T-200")  # next promotable after T-101

    def test_next_skips_archived_folder_p2_guard(self):
        # T-101 still prints `pending` but is actually delivered (archived
        # folder) — the T-063 status-rot case. It must NOT be re-promoted.
        root, cdir = make_repo()
        archived_folder(root, "T-101")
        e = json.loads(run(root, cdir, "next", expect=OK).stdout)
        self.assertEqual(e["id"], "T-200")

    def test_next_skips_live_lease(self):
        root, cdir = make_repo()
        write_claim(cdir, "T-101")
        e = json.loads(run(root, cdir, "next", expect=OK).stdout)
        self.assertEqual(e["id"], "T-200")

    def test_next_dep_satisfied_via_archived_folder(self):
        # T-201 depends on T-200; T-200 is pending-in-roadmap but delivered
        # (archived). The dep must count as satisfied, so with T-101 and T-200
        # both out of the way, T-201 becomes promotable.
        root, cdir = make_repo()
        archived_folder(root, "T-101")
        archived_folder(root, "T-200")
        e = json.loads(run(root, cdir, "next", expect=OK).stdout)
        self.assertEqual(e["id"], "T-201")

    def test_next_blocked_on_dep(self):
        # Only T-201 pending, its dep T-200 not delivered → blocked reason.
        roadmap = """# Roadmap

## T-201: blocked task
**Status**: pending
**Dependencies**: T-200
"""
        root, cdir = make_repo(roadmap)
        proc = run(root, cdir, "next", expect=NONE)
        self.assertIn("T-201 blocked on T-200", proc.stderr)

    def test_next_roadmap_exhausted(self):
        roadmap = """# Roadmap

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-100 | done | completed (2026-01-01) | low | — |
"""
        root, cdir = make_repo(roadmap)
        proc = run(root, cdir, "next", expect=NONE)
        self.assertIn("roadmap exhausted", proc.stderr)

    def test_next_deterministic_byte_identical(self):
        root, cdir = make_repo()
        a = run(root, cdir, "next", expect=OK)
        b = run(root, cdir, "next", expect=OK)
        self.assertEqual(a.stdout, b.stdout)  # divergence == 0


if __name__ == "__main__":
    unittest.main()

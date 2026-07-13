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

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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


class MissingRoadmap(unittest.TestCase):
    """T-093 — a freshly bootstrapped project has no docs/roadmap.md yet; the
    CLI must degrade cleanly (crash observed live via openup-agent.py cycle →
    openup-board.py resolve → cmd_next → FileNotFoundError)."""

    def _repo_without_roadmap(self):
        root, cdir = make_repo()
        (root / "docs" / "roadmap.md").unlink()
        return root, cdir

    def test_list_yields_empty_array(self):
        root, cdir = self._repo_without_roadmap()
        out = json.loads(run(root, cdir, "list", expect=OK).stdout)
        self.assertEqual(out, [])

    def test_get_exits_none(self):
        root, cdir = self._repo_without_roadmap()
        run(root, cdir, "get", "T-101", expect=NONE)

    def test_next_exits_none_not_traceback(self):
        root, cdir = self._repo_without_roadmap()
        proc = run(root, cdir, "next", "--no-remote-check", expect=NONE)
        self.assertNotIn("Traceback", proc.stderr)

    def test_board_resolve_returns_decision(self):
        root, cdir = self._repo_without_roadmap()
        board = Path(__file__).resolve().parents[1] / "openup-board.py"
        proc = subprocess.run(
            [sys.executable, str(board), "resolve",
             "--root", str(root), "--claims-dir", str(cdir)],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        decision = json.loads(proc.stdout)
        self.assertIn(decision["path"], ("noop", "milestone-review", "plan-iteration"))


class RemoteGuard(unittest.TestCase):
    """T-066: a task delivered in an open, unmerged PR shows up on ``origin`` as a
    branch encoding its id — invisible to the local folder/lease guards. ``next``
    must skip it (never re-promote) yet stay fail-open when the remote can't be
    consulted. Exercised against a REAL bare origin so the ls-remote path runs."""

    ROADMAP = """# Roadmap

## T-101: first pending
**Status**: pending

## T-200: second pending
**Status**: pending
"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="openup-roadmap-remote-"))
        self.remote = self.tmp / "origin.git"
        self.local = self.tmp / "repo"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)], check=True)
        subprocess.run(["git", "init", "-q", str(self.local)], check=True)
        self._git("config", "user.email", "t@example.com")
        self._git("config", "user.name", "t")
        (self.local / "docs").mkdir(parents=True)
        (self.local / "docs" / "roadmap.md").write_text(self.ROADMAP, encoding="utf-8")
        self.cdir = self.local / "_claims"
        self.cdir.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        self._git("branch", "-M", "main")
        self._git("remote", "add", "origin", str(self.remote))
        self._git("push", "-q", "origin", "main")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _git(self, *args):
        subprocess.run(["git", *args], cwd=str(self.local),
                       check=True, capture_output=True, text=True)

    def _push_branch(self, name):
        # A branch on origin (pointing at main) with no local checkout — exactly
        # the trace an open PR leaves after complete-task pushed the lane.
        self._git("push", "-q", "origin", "main:refs/heads/" + name)

    def _next(self, *extra, expect=None):
        cmd = [sys.executable, str(SCRIPT), "next",
               "--root", str(self.local), "--claims-dir", str(self.cdir), *extra]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if expect is not None:
            assert proc.returncode == expect, (
                f"expected exit {expect}, got {proc.returncode}\n"
                f"extra={extra}\nstdout={proc.stdout}\nstderr={proc.stderr}")
        return proc

    def test_no_matching_branch_promotes(self):
        # Only main on origin → nothing encodes T-101 → normal promote.
        e = json.loads(self._next(expect=OK).stdout)
        self.assertEqual(e["id"], "T-101")

    def test_matching_branch_skipped(self):
        # An origin branch encodes T-101 (delivered-but-unmerged) → skip it,
        # promote the next pending task instead.
        self._push_branch("feat/T-101-board-guard")
        e = json.loads(self._next(expect=OK).stdout)
        self.assertEqual(e["id"], "T-200")

    def test_sole_candidate_remote_skipped_exits_none_with_reason(self):
        self._push_branch("feat/T-101-x")
        self._push_branch("feat/T-200-y")
        proc = self._next(expect=NONE)
        self.assertIn("delivered-but-unmerged", proc.stderr)
        self.assertIn("T-101", proc.stderr)
        self.assertIn("merge its PR", proc.stderr)

    def test_no_remote_check_bypasses_guard(self):
        self._push_branch("feat/T-101-x")
        e = json.loads(self._next("--no-remote-check", expect=OK).stdout)
        self.assertEqual(e["id"], "T-101")

    def test_missing_remote_fails_open(self):
        # No origin at all → remote error → guard must NOT block promotion.
        self._push_branch("feat/T-101-x")   # (pushed before removal)
        self._git("remote", "remove", "origin")
        e = json.loads(self._next(expect=OK).stdout)
        self.assertEqual(e["id"], "T-101")

    def test_token_boundary_no_false_positive(self):
        # A branch for T-1010 must not match T-101 (id is a delimited token).
        self._push_branch("feat/T-1010-unrelated")
        e = json.loads(self._next(expect=OK).stdout)
        self.assertEqual(e["id"], "T-101")


class RemoteCacheUnit(unittest.TestCase):
    """T-066 req 3: N candidates needing the remote check cost ONE ls-remote."""

    def _load_module(self):
        spec = importlib.util.spec_from_file_location(
            "openup_roadmap_under_test", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_ls_remote_called_once_across_candidates(self):
        mod = self._load_module()
        root = Path(tempfile.mkdtemp(prefix="openup-roadmap-cache-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "roadmap.md").write_text(
            "# Roadmap\n\n## T-101: a\n**Status**: pending\n\n"
            "## T-200: b\n**Status**: pending\n", encoding="utf-8")
        cdir = root / "_claims"
        cdir.mkdir()

        calls = {"ls": 0}
        orig_git = mod.claims._git

        def fake_git(args, cwd=None):
            if args[:1] == ["remote"] and len(args) == 1:
                return "origin"
            if args[:2] == ["ls-remote", "--heads"]:
                calls["ls"] += 1
                return "sha\trefs/heads/feat/T-101-x"  # matches T-101 only
            return orig_git(args, cwd=cwd)

        mod.claims._git = fake_git
        try:
            args = SimpleNamespace(root=str(root), claims_dir=str(cdir),
                                   remote="origin", no_remote_check=False)
            rc = mod.cmd_next(args)   # T-101 skipped, T-200 promoted
        finally:
            mod.claims._git = orig_git

        self.assertEqual(rc, OK)
        self.assertEqual(calls["ls"], 1)   # cached — not once per candidate


if __name__ == "__main__":
    unittest.main()

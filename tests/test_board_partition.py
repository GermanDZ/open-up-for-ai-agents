"""Unit tests for openup-board.py partition subcommand + parallel iterations (T-079).

All tests are hermetic: they build a temporary repo skeleton (docs/changes/
plan.md files and/or an empty claims dir) so no real git state is needed.

Coverage maps to the plan's requirements:
  * R1 — connected-component clustering (touches-overlap ∪ depends-on).
  * R2 — deterministic, order-stable output.
  * R4 — the board runs disjoint clusters concurrently (unscoped pick when
         several iteration prefixes hold live leases).
  * R5 — worktree-per-lane isolation for concurrent clusters (distinct
         worktrees; and partition guarantees cross-cluster touches are disjoint).
"""

import io
import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import importlib.util

_BOARD_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openup-board.py"
_spec = importlib.util.spec_from_file_location("openup_board", _BOARD_PATH)
_board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_board)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_plan(root: Path, task_id: str, *, touches: list, priority: str = "high",
               status: str = "ready", depends_on: list | None = None) -> Path:
    """Write a minimal change-folder plan.md so partition can read it."""
    change_dir = root / "docs" / "changes" / task_id
    change_dir.mkdir(parents=True, exist_ok=True)
    plan = change_dir / "plan.md"
    deps_line = f"depends-on: [{', '.join(depends_on)}]\n" if depends_on else ""
    touches_block = "\n".join(f"  - {t}" for t in touches)
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


def _make_claim(cdir: Path, task_id: str, *, touches: list, worktree: str) -> Path:
    """Write a synthetic live claim for an iteration-prefixed lane."""
    payload = {
        "task_id": task_id,
        "session_id": f"sess-{task_id}",
        "branch": f"feat/{task_id}",
        "worktree": worktree,
        "touches": touches,
        "last_heartbeat": "2999-01-01T00:00:00Z",
    }
    fp = cdir / f"{task_id}.json"
    fp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return fp


def _run_board(argv: list[str], stdin_text: str | None = None) -> tuple[int, str]:
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        if stdin_text is not None:
            with patch("sys.stdin", io.StringIO(stdin_text)):
                rc = _board.main(argv)
        else:
            rc = _board.main(argv)
    return rc, buf.getvalue()


# ---------------------------------------------------------------------------
# R1 — clustering shapes (pure core, via --stdin so no folders needed)
# ---------------------------------------------------------------------------

class TestPartitionShapes:
    def test_disjoint_plus_overlap(self):
        """A and B share a touches prefix; C is disjoint → [[A,B],[C]]."""
        items = [
            {"id": "A", "touches": ["scripts/x.py"]},
            {"id": "B", "touches": ["scripts/x.py", "docs/a"]},
            {"id": "C", "touches": ["scripts/y.py"]},
        ]
        rc, out = _run_board(["partition", "--stdin"], json.dumps(items))
        assert rc == 0
        assert json.loads(out) == [["A", "B"], ["C"]]

    def test_dependency_forces_same_cluster(self):
        """Disjoint touches, but B depends-on A → one cluster (no concurrency)."""
        items = [
            {"id": "A", "touches": ["scripts/x.py"]},
            {"id": "B", "touches": ["scripts/y.py"], "depends-on": ["A"]},
        ]
        rc, out = _run_board(["partition", "--stdin"], json.dumps(items))
        assert rc == 0
        assert json.loads(out) == [["A", "B"]]

    def test_reverse_dependency_direction(self):
        """A depends-on B (edge is undirected) → still one cluster."""
        items = [
            {"id": "A", "touches": ["scripts/x.py"], "depends-on": ["B"]},
            {"id": "B", "touches": ["scripts/y.py"]},
        ]
        rc, out = _run_board(["partition", "--stdin"], json.dumps(items))
        assert rc == 0
        assert json.loads(out) == [["A", "B"]]

    def test_single_item(self):
        items = [{"id": "A", "touches": ["scripts/x.py"]}]
        rc, out = _run_board(["partition", "--stdin"], json.dumps(items))
        assert rc == 0
        assert json.loads(out) == [["A"]]

    def test_empty_input(self):
        rc, out = _run_board(["partition", "--stdin"], "[]")
        assert rc == 0
        assert json.loads(out) == []

    def test_transitive_merge(self):
        """A~B (touches) and B~C (dependency) → all three in one cluster,
        even though A and C share nothing directly (connected component)."""
        items = [
            {"id": "A", "touches": ["scripts/x.py"]},
            {"id": "B", "touches": ["scripts/x.py"], "depends-on": ["C"]},
            {"id": "C", "touches": ["scripts/z.py"]},
        ]
        rc, out = _run_board(["partition", "--stdin"], json.dumps(items))
        assert rc == 0
        assert json.loads(out) == [["A", "B", "C"]]

    def test_natural_id_ordering(self):
        """Clusters and members sort naturally: C3 before C10, not lexically."""
        items = [
            {"id": "C10-001", "touches": ["scripts/a.py"]},
            {"id": "C3-001", "touches": ["scripts/b.py"]},
        ]
        rc, out = _run_board(["partition", "--stdin"], json.dumps(items))
        assert rc == 0
        assert json.loads(out) == [["C3-001"], ["C10-001"]]


# ---------------------------------------------------------------------------
# R2 — determinism / order-stability
# ---------------------------------------------------------------------------

class TestPartitionDeterminism:
    def test_output_independent_of_input_order(self):
        forward = [
            {"id": "A", "touches": ["scripts/x.py"]},
            {"id": "B", "touches": ["scripts/x.py", "docs/a"]},
            {"id": "C", "touches": ["scripts/y.py"]},
        ]
        reverse = list(reversed(forward))
        _, out_f = _run_board(["partition", "--stdin"], json.dumps(forward))
        _, out_r = _run_board(["partition", "--stdin"], json.dumps(reverse))
        assert out_f == out_r  # byte-identical
        assert json.loads(out_f) == [["A", "B"], ["C"]]

    def test_invalid_json_stdin_exits_usage(self):
        rc, _ = _run_board(["partition", "--stdin"], "{not json")
        assert rc == 2

    def test_non_array_json_exits_usage(self):
        rc, _ = _run_board(["partition", "--stdin"], '{"id": "A"}')
        assert rc == 2


# ---------------------------------------------------------------------------
# R1 — folder mode: partition reads touches/depends-on from change folders
# ---------------------------------------------------------------------------

class TestPartitionFolderMode:
    def test_reads_from_change_folders(self, tmp_path):
        _make_plan(tmp_path, "C3-001", touches=["scripts/openup-board.py"])
        _make_plan(tmp_path, "C3-002", touches=["scripts/openup-board.py"])  # overlaps 001
        _make_plan(tmp_path, "C3-003", touches=["docs/parallel.md"])         # disjoint
        rc, out = _run_board(
            ["partition", "C3-001", "C3-002", "C3-003", "--root", str(tmp_path)]
        )
        assert rc == 0
        assert json.loads(out) == [["C3-001", "C3-002"], ["C3-003"]]

    def test_missing_folder_is_isolated(self, tmp_path):
        """An id with no change folder has no declared surface → its own cluster."""
        _make_plan(tmp_path, "C3-001", touches=["scripts/openup-board.py"])
        rc, out = _run_board(
            ["partition", "C3-001", "C3-999", "--root", str(tmp_path)]
        )
        assert rc == 0
        clusters = json.loads(out)
        assert ["C3-999"] in clusters
        assert ["C3-001"] in clusters


# ---------------------------------------------------------------------------
# R4 — the board runs disjoint clusters concurrently (unscoped pick)
# ---------------------------------------------------------------------------

class TestConcurrentIterations:
    def test_two_live_prefixes_are_unscoped(self, tmp_path):
        """Live leases on C3-001 and C4-001 (two iteration prefixes) →
        _active_iteration_prefix returns None → pick is unscoped across both,
        so disjoint clusters run concurrently (no re-scoping regression)."""
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_claim(cdir, "C3-001", touches=["scripts/a.py"], worktree="/wt/C3-001")
        _make_claim(cdir, "C4-001", touches=["scripts/b.py"], worktree="/wt/C4-001")
        assert _board._active_iteration_prefix(cdir) is None

    def test_single_live_prefix_scopes(self, tmp_path):
        """One live iteration prefix → pick is scoped to it (T-077 behavior)."""
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_claim(cdir, "C3-001", touches=["scripts/a.py"], worktree="/wt/C3-001")
        assert _board._active_iteration_prefix(cdir) == "C3"


# ---------------------------------------------------------------------------
# R5 — worktree-per-lane isolation for concurrent clusters
# ---------------------------------------------------------------------------

class TestWorktreeIsolation:
    def test_concurrent_cluster_lanes_have_distinct_worktrees(self, tmp_path):
        """Two lanes from different clusters, begun concurrently, occupy distinct
        worktree paths — their edits cannot interleave on disk (live-run F5)."""
        cdir = tmp_path / "claims"
        cdir.mkdir()
        _make_claim(cdir, "C3-001", touches=["scripts/a.py"], worktree="/wt/C3-001")
        _make_claim(cdir, "C4-001", touches=["scripts/b.py"], worktree="/wt/C4-001")
        import importlib.util as _il
        _claims_path = Path(__file__).resolve().parents[1] / "scripts" / "openup-claims.py"
        _cspec = _il.spec_from_file_location("openup_claims", _claims_path)
        _claims = _il.module_from_spec(_cspec)
        _cspec.loader.exec_module(_claims)
        worktrees = {c["worktree"] for c in _claims.live_claims(cdir)}
        assert len(worktrees) == 2  # distinct — no shared checkout

    def test_partition_guarantees_cross_cluster_touches_disjoint(self):
        """The property that makes concurrency safe: members of different
        clusters never share a touches prefix (so even the write-fence agrees)."""
        items = [
            {"id": "A", "touches": ["scripts/x.py"]},
            {"id": "B", "touches": ["scripts/x.py"]},   # cluster with A
            {"id": "C", "touches": ["docs/y.md"]},      # own cluster
            {"id": "D", "touches": ["tests/z.py"]},     # own cluster
        ]
        clusters = _board.partition_items(items)
        by_id = {it["id"]: it["touches"] for it in items}
        # For every pair of members in different clusters, touches must not overlap.
        for i, ci in enumerate(clusters):
            for cj in clusters[i + 1:]:
                for a in ci:
                    for b in cj:
                        assert not _board.claims.touches_overlap(by_id[a], by_id[b])

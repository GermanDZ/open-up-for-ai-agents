#!/usr/bin/env python3
"""Unit tests for scripts/openup-fence.py (T-024).

Run with either:
    python3 -m unittest scripts.tests.test_openup_fence
    python3 scripts/tests/test_openup_fence.py

Hermetic: each test builds an isolated fixture git repo (a `main` trunk and a
lane branch with its own plan frontmatter), an injected --claims-dir, and an
injected --state-dir, so it never depends on the live repo, real leases, or
the live trunk. The fence is exercised through its CLI exactly as the
pre-push hook and /openup-complete-task do.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "openup-fence.py"

_spec = importlib.util.spec_from_file_location("openup_fence_under_test", SCRIPT)
fence_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fence_mod)

OK, USAGE, NO_TASK, VIOLATION = 0, 2, 3, 8

TASK = "T-100"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


class FenceRepo:
    """Throwaway repo: main trunk + lane branch for TASK with frontmatter."""

    def __init__(self, touches=("src/widget.py",)):
        self.dir = Path(tempfile.mkdtemp())
        # Overrides live OUTSIDE the repo so `git add -A` never sees them.
        self.aux = Path(tempfile.mkdtemp())
        self.claims = self.aux / "claims-override"
        self.state = self.aux / "state-override"
        git(self.dir, "init", "-q")
        git(self.dir, "config", "user.email", "t@example.com")
        git(self.dir, "config", "user.name", "Tester")
        git(self.dir, "config", "commit.gpgsign", "false")
        git(self.dir, "checkout", "-q", "-b", "main")
        plan = self.dir / "docs" / "changes" / TASK
        plan.mkdir(parents=True)
        fm = "\n".join(
            ["---", f"id: {TASK}", "title: Fence fixture", "status: in-progress",
             "priority: medium", "depends-on: []",
             "touches: [%s]" % ", ".join(touches), "---", "", f"# {TASK}", ""]
        )
        (plan / "plan.md").write_text(fm, encoding="utf-8")
        (self.dir / "src").mkdir()
        (self.dir / "src" / "widget.py").write_text("x = 1\n")
        (self.dir / "src" / "other.py").write_text("y = 1\n")
        (self.dir / "docs" / "roadmap.md").write_text("# Roadmap\n")
        (self.dir / "docs" / "project-status.md").write_text("# Status\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "seed")
        git(self.dir, "checkout", "-q", "-b", f"lane/{TASK}")

    def commit(self, relpath, content="changed\n", msg="lane edit"):
        p = self.dir / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", msg)

    def advance_main(self):
        """Move main ahead so it is no longer an ancestor of the lane."""
        git(self.dir, "checkout", "-q", "main")
        (self.dir / "TRUNK.md").write_text("moved\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "trunk moves")
        git(self.dir, "checkout", "-q", f"lane/{TASK}")

    def write_state(self, task_id=TASK, base_sha=None):
        self.state.mkdir(parents=True, exist_ok=True)
        payload = {"task_id": task_id}
        if base_sha is not None:
            payload["base_sha"] = base_sha
        (self.state / "state.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def write_claim(self, touches, task_id=TASK):
        self.claims.mkdir(parents=True, exist_ok=True)
        (self.claims / f"{task_id}.json").write_text(
            json.dumps({"task_id": task_id, "session_id": "S1",
                        "touches": list(touches)}),
            encoding="utf-8",
        )

    def fence(self, *args, sub="check", base="main"):
        base_flags = ["--base", base] if base is not None else []
        cmd = [sys.executable, str(SCRIPT), sub, *base_flags,
               "--claims-dir", str(self.claims),
               "--state-dir", str(self.state), *args]
        return subprocess.run(cmd, cwd=self.dir, capture_output=True, text=True)

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.aux, ignore_errors=True)


class FenceCheckTests(unittest.TestCase):
    def setUp(self):
        self.repo = FenceRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_in_lane_touches_and_change_folder_pass(self):
        self.repo.commit("src/widget.py")
        self.repo.commit(f"docs/changes/{TASK}/design.md", "decision\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_out_of_lane_blocks_and_names_file(self):
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)
        self.assertIn("src/other.py", proc.stderr)

    def test_lane_owned_audit_surfaces_pass(self):
        self.repo.commit("docs/agent-logs/2026/06/12/run.md", "log\n")
        self.repo.commit("docs/status-notes/2026-06-12-T-100.md", "note\n")
        self.repo.commit("docs/explorations/2026-06-12-idea.md", "notes\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_claude_memory_files_pass_without_being_claimed(self):
        """T-147: both files are written by mechanisms no lane opts into.

        `.claude/memory/bypass-log.md` is appended by gate-edits / check-iteration
        / validate-commit; `.claude/memory/iteration-learnings.md` by
        `openup-scribe.py learnings`, which /openup-complete-task runs on every
        track. The fixture's `touches` is `src/widget.py` only — neither path is
        claimed, which is exactly the downstream situation (FD-003).
        """
        self.repo.commit(".claude/memory/bypass-log.md", "- bypass\n")
        self.repo.commit(".claude/memory/iteration-learnings.md", "- learning\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertNotIn("OUT OF LANE", proc.stderr)

    def test_other_claude_file_is_still_out_of_lane(self):
        """The exemption is the two files, not `.claude/`."""
        self.repo.commit(".claude/settings.json", "{}\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)
        self.assertIn(".claude/settings.json", proc.stderr)

    def test_claude_memory_dir_is_not_blanket_exempt(self):
        """Guards the files-not-prefix decision (T-147 spec assumption).

        If someone widens ALWAYS_ALLOWED to `.claude/memory/`, this fails — which
        is the point: widening it would silently exempt whatever else a consumer
        project keeps there.
        """
        self.repo.commit(".claude/memory/scratch-notes.md", "notes\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)
        self.assertIn(".claude/memory/scratch-notes.md", proc.stderr)

    def test_archive_destination_passes(self):
        self.repo.commit(f"docs/changes/archive/{TASK}/state.json", "{}\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_views_with_fresh_base_pass(self):
        self.repo.commit("docs/roadmap.md", "# Roadmap v2\n")
        self.repo.commit("docs/project-status.md", "# Status v2\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_views_with_stale_base_block_with_rebase_hint(self):
        self.repo.commit("docs/roadmap.md", "# Roadmap v2\n")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("STALE VIEW", proc.stderr)
        self.assertIn("docs/roadmap.md", proc.stderr)
        self.assertIn("Rebase", proc.stderr)

    def test_allow_views_overrides_stale_base(self):
        self.repo.commit("docs/roadmap.md", "# Roadmap v2\n")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK, "--allow-views")
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_index_view_with_fresh_base_passes(self):
        # T-122/B8: docs/INDEX.md is a fenced derived view — a fresh-base
        # regeneration must NOT be flagged OUT OF LANE (the T-003 revert).
        self.repo.commit("docs/INDEX.md", "# Index v2\n")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertNotIn("OUT OF LANE", proc.stderr)

    def test_index_view_with_stale_base_is_stale_view_not_out_of_lane(self):
        # T-122/B8: on a stale base INDEX.md is a STALE VIEW (like the other
        # views), never OUT OF LANE.
        self.repo.commit("docs/INDEX.md", "# Index v2\n")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("STALE VIEW", proc.stderr)
        self.assertIn("docs/INDEX.md", proc.stderr)
        self.assertNotIn("OUT OF LANE", proc.stderr)

    def test_index_view_allow_views_overrides_stale_base(self):
        # T-122/B8: --allow-views frees INDEX.md exactly as for the other views.
        self.repo.commit("docs/INDEX.md", "# Index v2\n")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK, "--allow-views")
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_stale_base_does_not_excuse_out_of_lane(self):
        self.repo.commit("src/other.py")
        self.repo.advance_main()
        proc = self.repo.fence("--task-id", TASK, "--allow-views")
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)

    def test_extra_allow_paths(self):
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK, "--allow", "src/other.py")
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_claim_touches_preferred_over_frontmatter(self):
        # frontmatter only covers src/widget.py; the live claim covers other.py
        self.repo.write_claim(["src/widget.py", "src/other.py"])
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_task_id_resolved_from_state(self):
        self.repo.write_state()
        self.repo.commit("src/widget.py")
        proc = self.repo.fence()
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertIn(TASK, proc.stdout)

    def test_no_task_id_exits_3(self):
        self.repo.commit("src/widget.py")
        proc = self.repo.fence()
        self.assertEqual(proc.returncode, NO_TASK)

    def test_no_changes_is_clean_pass(self):
        proc = self.repo.fence("--task-id", TASK)
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertIn("no changes", proc.stdout)

    def test_unresolvable_base_is_inapplicable_not_fatal(self):
        self.repo.commit("src/other.py")
        proc = self.repo.fence("--task-id", TASK, "--base", "no-such-ref")
        self.assertEqual(proc.returncode, OK)
        self.assertIn("inapplicable", proc.stderr)


class FenceAllowedTests(unittest.TestCase):
    def setUp(self):
        self.repo = FenceRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_allowed_prints_resolved_allowlist(self):
        proc = self.repo.fence("--task-id", TASK, sub="allowed")
        self.assertEqual(proc.returncode, OK, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["task"], TASK)
        self.assertIn("src/widget.py", payload["allowed"])
        self.assertIn(f"docs/changes/{TASK}/", payload["allowed"])
        self.assertIn("docs/status-notes/", payload["allowed"])
        self.assertIn("docs/roadmap.md", payload["views"])
        self.assertIn("docs/INDEX.md", payload["views"])  # T-122/B8

    def test_allowed_lists_the_claude_memory_files(self):
        """T-147: present for every task, with nothing declared in `touches`."""
        proc = self.repo.fence("--task-id", TASK, sub="allowed")
        self.assertEqual(proc.returncode, OK, proc.stderr)
        allowed = json.loads(proc.stdout)["allowed"]
        self.assertIn(".claude/memory/bypass-log.md", allowed)
        self.assertIn(".claude/memory/iteration-learnings.md", allowed)
        self.assertNotIn(".claude/memory/", allowed)  # files, not a prefix


class FenceQuickTrackTests(unittest.TestCase):
    """T-042 G2: a quick-track lane with no declared surface is unfenced."""

    def setUp(self):
        self.repo = FenceRepo()

    def tearDown(self):
        self.repo.cleanup()

    def _quick_state(self, task_id="T-101"):
        # A task with NO change folder + a quick-track live state.
        self.repo.state.mkdir(parents=True, exist_ok=True)
        (self.repo.state / "state.json").write_text(
            json.dumps({"task_id": task_id, "track": "quick"}),
            encoding="utf-8",
        )

    def test_quick_no_touches_is_unfenced(self):
        self.repo.commit("src/anything.py")
        self._quick_state("T-101")
        proc = self.repo.fence("--task-id", "T-101")
        self.assertEqual(proc.returncode, OK, proc.stderr)
        self.assertIn("unfenced", proc.stdout)

    def test_quick_with_allow_fences_normally(self):
        # Declaring a surface (--allow) opts back into fencing.
        self.repo.commit("src/anything.py")
        self._quick_state("T-101")
        proc = self.repo.fence("--task-id", "T-101", "--allow", "src/other.py")
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)

    def test_quick_still_flags_stale_views(self):
        # Quick relaxes lane purity, not view freshness.
        self.repo.commit("docs/roadmap.md", "# v2\n")
        self.repo.advance_main()
        self._quick_state("T-101")
        proc = self.repo.fence("--task-id", "T-101")
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("STALE VIEW", proc.stderr)

    def test_standard_empty_touches_still_blocks(self):
        # The relaxation is quick-only: a standard lane with empty touches still
        # fences (guards against the quick-path leaking into standard).
        self.repo.commit("src/anything.py")
        self.repo.state.mkdir(parents=True, exist_ok=True)
        (self.repo.state / "state.json").write_text(
            json.dumps({"task_id": "T-101", "track": "standard"}),
            encoding="utf-8",
        )
        proc = self.repo.fence("--task-id", "T-101")
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("OUT OF LANE", proc.stderr)


class ResolveBaseTests(unittest.TestCase):
    """T-131 / F3 — resolve_base precedence, unit-level (no CLI round-trip)."""

    def setUp(self):
        self.repo = FenceRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_explicit_wins_over_stamped(self):
        base = fence_mod.resolve_base("main", cwd=self.repo.dir, stamped="lane/" + TASK)
        self.assertEqual(base, "main")

    def test_stamped_wins_when_no_explicit(self):
        base = fence_mod.resolve_base(None, cwd=self.repo.dir, stamped="main")
        self.assertEqual(base, "main")

    def test_falls_through_to_origin_main_then_main_when_no_stamped(self):
        base = fence_mod.resolve_base(None, cwd=self.repo.dir, stamped=None)
        self.assertEqual(base, "main")

    def test_explicit_unresolvable_does_not_fall_back(self):
        # Preserves the pre-existing contract: an explicit-but-invalid --base
        # is inapplicable, never silently substituted.
        base = fence_mod.resolve_base("no-such-ref", cwd=self.repo.dir, stamped="main")
        self.assertIsNone(base)


class FenceBaseShaTests(unittest.TestCase):
    """T-131 / F3 — the sequential-lane-on-one-branch live scenario (T-128-vs-T-127)."""

    def setUp(self):
        self.repo = FenceRepo()
        # Move everything onto `main` itself — the shape that actually broke
        # live: two lanes landing sequentially on one shared branch, not two
        # separate worktree branches.
        git(self.repo.dir, "checkout", "-q", "main")

    def tearDown(self):
        self.repo.cleanup()

    def _land_prior_lane(self):
        """Simulate lane-1's already-merged commit directly on `main`."""
        self.repo.commit("docs/changes/T-127/plan.md", "lane-1 spec\n", msg="lane-1 work")
        return git(self.repo.dir, "rev-parse", "HEAD").stdout.strip()

    def test_stamped_base_sha_excuses_a_prior_already_merged_lane(self):
        base_sha = self._land_prior_lane()
        self.repo.commit("src/widget.py", msg="lane-2 in-lane work")  # TASK's own touches
        self.repo.write_state(base_sha=base_sha)
        proc = self.repo.fence("--task-id", TASK, base=None)
        self.assertEqual(proc.returncode, OK, proc.stderr)

    def test_stamped_base_sha_still_catches_a_genuine_out_of_lane_file(self):
        base_sha = self._land_prior_lane()
        self.repo.commit("src/other.py", msg="lane-2 out-of-lane work")  # NOT in TASK's touches
        self.repo.write_state(base_sha=base_sha)
        proc = self.repo.fence("--task-id", TASK, base=None)
        self.assertEqual(proc.returncode, VIOLATION)
        self.assertIn("src/other.py", proc.stderr)

    def test_no_base_sha_falls_back_to_origin_main_chain(self):
        # A pre-existing state.json (no base_sha key) must degrade to today's
        # resolution, not error — Requirement 6.
        self._land_prior_lane()
        self.repo.commit("src/widget.py", msg="lane-2 in-lane work")
        self.repo.write_state()  # no base_sha
        proc = self.repo.fence("--task-id", TASK, base=None)
        self.assertEqual(proc.returncode, OK, proc.stderr)


if __name__ == "__main__":
    unittest.main()

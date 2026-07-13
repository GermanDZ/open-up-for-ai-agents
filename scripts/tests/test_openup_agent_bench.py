"""Hermetic test for the reference-driver benchmark harness (T-080).

Drives the WHOLE harness (`openup-agent-bench.py`) against a scripted local
`http.server` — no live model — so fixture construction, scenario seeding,
`resolve == pick`, the driver subprocess run, usage/latency capture, the
post-run gate re-check + work-delta, and aggregation are all exercised in CI.

The scripted "model" runs a minimal clean cycle: write the lane's state, produce
the scenario deliverable, then emit the sentinel with no tool calls. Each
completion carries a `usage` object so the token/iteration capture is covered.
"""

import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_BENCH = _REPO / "scripts" / "openup-agent-bench.py"
_spec = importlib.util.spec_from_file_location("openup_agent_bench", _BENCH)
bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench)  # type: ignore[union-attr]

# The driver package (for the usage-hook unit test).
import sys as _sys
_sys.path.insert(0, str(_REPO / "scripts"))
from openup_agent import loop as _loop  # noqa: E402

_TIER_MAP = (
    "claude-code:\n  reasoning: inherit\n"
    "driver:\n  reasoning: \"${OPENUP_MODEL_MAIN:-local-main}\"\n"
)
_DEMO_PROC = ("---\nname: openup-demo\ntier: reasoning\n---\n\n"
              "# Demo\nEmit `OPENUP-DEMO: DONE — x` when done.\n")


def _demo_root(tmp: Path):
    (tmp / "docs-eng-process" / "procedures").mkdir(parents=True)
    (tmp / "docs-eng-process" / "tier-map.yaml").write_text(_TIER_MAP)
    (tmp / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_DEMO_PROC)
    return tmp


class UsageHookTest(unittest.TestCase):
    """Requirement 1 — env-gated OPENUP_AGENT_USAGE_LOG capture in loop.run."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = _demo_root(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def _completion(self, usage):
        # One turn: immediately emit the sentinel (no tool calls). run_gates
        # skips absent scripts, so the sentinel is accepted → exactly 1 LLM call.
        def _c(model, msgs, tool_defs):
            return {"choices": [{"message": {"role": "assistant",
                    "content": "OPENUP-DEMO: DONE — x"}}], "usage": usage}
        return _c

    def test_writes_one_record_per_call_when_set(self):
        log = Path(self.tmp.name) / "u.jsonl"
        env = {"LLM_API_URL": "http://x/v1", "OPENUP_MODEL_MAIN": "m",
               "OPENUP_AGENT_USAGE_LOG": str(log)}
        rc = _loop.run(str(self.root), "demo", env=env,
                       _completion=self._completion({"prompt_tokens": 7,
                                                     "completion_tokens": 3,
                                                     "total_tokens": 10}))
        self.assertEqual(rc, 0)
        lines = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        rec = lines[0]
        self.assertEqual(rec["iteration"], 1)
        self.assertEqual(rec["model"], "m")
        self.assertIn("latency_ms", rec)
        self.assertEqual(rec["usage"]["total_tokens"], 10)

    def test_no_file_when_unset(self):
        log = Path(self.tmp.name) / "u.jsonl"
        env = {"LLM_API_URL": "http://x/v1", "OPENUP_MODEL_MAIN": "m"}
        rc = _loop.run(str(self.root), "demo", env=env,
                       _completion=self._completion({"total_tokens": 10}))
        self.assertEqual(rc, 0)
        self.assertFalse(log.exists())


def _asst(content=None, tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}}


def _tool_call(cid, name, args):
    return {"id": cid, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


# The scripted cycle: state → deliverable → sentinel. Chosen from the
# conversation state in EACH request (count of prior assistant turns), so it is
# stateless — it resets naturally for every fresh run in a batch and tolerates
# gate re-injections.
_STATE_JSON = json.dumps({"schema": 2, "task_id": "BENCH-001", "track": "quick",
                          "gates": {}})


def _script_for(turn):
    if turn == 0:
        return _asst(tool_calls=[_tool_call("c1", "write_file",
                     {"path": ".openup/state.json", "content": _STATE_JSON})])
    if turn == 1:
        return _asst(tool_calls=[_tool_call("c2", "write_file",
                     {"path": "docs/bench-scratch/note.md", "content": "bench ok\n"})])
    return _asst(content="Work done.\nOPENUP-NEXT: ADVANCED — BENCH-001")


class _ScriptedHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length))
        turn = sum(1 for m in req.get("messages", []) if m.get("role") == "assistant")
        payload = _script_for(turn)
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class BenchHarnessTest(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), _ScriptedHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d/v1" % self.server.server_address[1]
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def _run(self, runs=1):
        out = Path(self.tmp.name) / "out"
        work = Path(self.tmp.name) / "work"
        env = dict(os.environ)
        env["LLM_API_URL"] = self.url
        env["LLM_API_KEY"] = "k"
        env["OPENUP_MODEL_MAIN"] = "mock-model"
        args = bench.build_parser().parse_args([
            "--repo", str(_REPO), "--runs", str(runs),
            "--out", str(out), "--workdir", str(work),
            "--max-iterations", "8", "--timeout", "120",
        ])
        rc = bench.run_batch(args, env)
        return rc, out

    def test_seeded_fixture_resolves_to_pick(self):
        """build_fixture produces a fresh git repo whose board resolves to the
        seeded lane (not the source backlog)."""
        fixture = Path(self.tmp.name) / "fx"
        seed_sha, scenario = bench.build_fixture(
            _REPO, fixture, bench.DEFAULT_SCENARIO_DIR, include_working_tree=False)
        self.assertTrue((fixture / ".git").is_dir())
        self.assertTrue((fixture / "docs" / "changes" / "BENCH-001" / "plan.md").exists())
        ok, decision = bench.resolves_to(fixture, scenario["expect_pick"])
        self.assertTrue(ok, "board did not resolve to BENCH-001: %s" % decision)
        self.assertEqual(decision["path"], "pick")

    def test_source_repo_untouched(self):
        """A batch never writes to the repo under test."""
        before = os.popen("git -C %s status --porcelain" % _REPO).read()
        self._run(runs=1)
        after = os.popen("git -C %s status --porcelain" % _REPO).read()
        self.assertEqual(before, after)

    def test_full_batch_pipeline(self):
        rc, out = self._run(runs=2)
        self.assertEqual(rc, 0)
        results = out / "results.jsonl"
        self.assertTrue(results.exists())
        records = [json.loads(l) for l in results.read_text().splitlines() if l.strip()]
        self.assertEqual(len(records), 2)
        r = records[0]
        # Outcome + gates
        self.assertEqual(r["outcome"], "pass")
        self.assertTrue(r["gates"]["fence"])
        self.assertTrue(r["gates"]["check_docs"])
        # Iterations + tokens (from the usage log)
        self.assertEqual(r["iterations"], 3)
        self.assertEqual(r["tokens"]["total"], 360)  # 3 calls × 120
        # Latency captured
        self.assertEqual(r["latency_ms"]["calls"], 3)
        # Work delta — the deliverable was really produced on the fixture
        self.assertTrue(r["work"]["deliverable_produced"])
        self.assertTrue(r["seed_resolves_pick"])
        # Aggregation artifacts
        self.assertTrue((out / "summary.md").exists())
        agg = json.loads((out / "summary.json").read_text())
        self.assertEqual(agg["runs"], 2)
        self.assertEqual(agg["clean_passes"], 2)
        self.assertEqual(agg["pass_rate"], 1.0)

    def test_endpoint_error_reason_is_surfaced(self):
        """T-081 — a non-pass run records the driver's FATAL reason + stderr tail
        and writes a per-run driver log (no manual side-run needed)."""
        out = Path(self.tmp.name) / "out"
        work = Path(self.tmp.name) / "work"
        env = dict(os.environ)
        env["LLM_API_URL"] = "http://127.0.0.1:1/v1"  # nothing listens on port 1
        env["LLM_API_KEY"] = "k"
        env["OPENUP_MODEL_MAIN"] = "mock-model"
        args = bench.build_parser().parse_args([
            "--repo", str(_REPO), "--runs", "1", "--out", str(out),
            "--workdir", str(work), "--max-iterations", "2", "--timeout", "120",
        ])
        rc = bench.run_batch(args, env)
        self.assertEqual(rc, 0)  # the batch completes even though the run failed
        rec = json.loads((out / "results.jsonl").read_text().splitlines()[0])
        self.assertEqual(rec["outcome"], "endpoint-error")
        self.assertIsNotNone(rec["fatal"])
        self.assertIn("FATAL", rec["fatal"])
        self.assertTrue(rec["stderr_tail"])
        self.assertTrue((out / "run-01.driver.log").exists())


# ---------------------------------------------------------------------------
# T-083 — inception-vision scenario (drive create-vision, produce docs/vision.md)
# ---------------------------------------------------------------------------

_VISION_MD = (
    "# Vision — ShareShed\n\n"
    "## Problem Statement\nNeighbors own idle tools; there is no safe, simple way "
    "to lend and borrow them within a community.\n\n"
    "## Proposed Solution\nShareShed is a phone-friendly web app for verified "
    "neighbors to list, reserve, and return tools.\n\n"
    "## Stakeholders\nBorrowers, lenders, and the community administrator.\n\n"
    "## Key Features\nCatalogue, reservations, return reminders, membership.\n\n"
    "## Success Criteria\nTool utilization rises and overdue returns stay low in "
    "the first season.\n"
)

# Records whether the driver relayed the scenario's --instruction (it references
# the brief path, which appears nowhere else).
_vision = {"instruction_seen": False}


class _VisionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length))
        blob = json.dumps(req.get("messages", []))
        if "docs/inputs/stakeholder-brief.md" in blob:
            _vision["instruction_seen"] = True
        turn = sum(1 for m in req.get("messages", []) if m.get("role") == "assistant")
        if turn == 0:
            payload = _asst(tool_calls=[_tool_call("v1", "write_file",
                            {"path": "docs/vision.md", "content": _VISION_MD})])
        else:
            payload = _asst(content="OPENUP-CREATE-VISION: DONE — vision authored")
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class VisionScenarioTest(unittest.TestCase):
    def setUp(self):
        _vision["instruction_seen"] = False
        self.server = HTTPServer(("127.0.0.1", 0), _VisionHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d/v1" % self.server.server_address[1]
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def test_vision_scenario_scores_valid_vision(self):
        out = Path(self.tmp.name) / "out"
        work = Path(self.tmp.name) / "work"
        env = dict(os.environ)
        env.update({"LLM_API_URL": self.url, "LLM_API_KEY": "k",
                    "OPENUP_MODEL_MAIN": "mock", "OPENUP_MODEL_MID": "mock",
                    "OPENUP_MODEL_SMALL": "mock"})
        scenario = str(_REPO / "scripts" / "bench-scenarios" / "inception-vision")
        args = bench.build_parser().parse_args([
            "--repo", str(_REPO), "--runs", "1", "--out", str(out),
            "--workdir", str(work), "--scenario", scenario,
            "--max-iterations", "6", "--timeout", "120",
        ])
        rc = bench.run_batch(args, env)
        self.assertEqual(rc, 0)
        rec = json.loads((out / "results.jsonl").read_text().splitlines()[0])
        # Drove create-vision (from scenario.json), produced a sectioned vision,
        # and relayed the instruction that pointed at the brief.
        self.assertEqual(rec["outcome"], "pass")
        self.assertTrue(rec["work"]["deliverable_produced"])
        self.assertEqual(rec["work"]["missing_markers"], [])
        self.assertTrue(_vision["instruction_seen"])
        # No lane to fence on a fresh create-vision run → fence is inapplicable
        # (treated clean), so this counts as a clean pass.
        self.assertTrue(rec["gates"]["fence"])
        # T-084 — the produced vision is archived into the results dir for
        # inspection, surviving fixture teardown.
        self.assertEqual(rec["deliverable_archived"], "run-01.vision.md")
        archived = out / "run-01.vision.md"
        self.assertTrue(archived.exists())
        self.assertIn("ShareShed", archived.read_text())
        agg = json.loads((out / "summary.json").read_text())
        self.assertEqual(agg["meta"]["procedure"], "openup-create-vision")
        self.assertEqual(agg["clean_passes"], 1)

    def test_missing_section_fails_the_check(self):
        """required_markers is real: a vision missing a section fails."""
        fixture = Path(self.tmp.name) / "fx"
        seed_sha, scenario = bench.build_fixture(
            _REPO, fixture,
            Path(_REPO / "scripts" / "bench-scenarios" / "inception-vision"),
            include_working_tree=False)
        (fixture / "docs").mkdir(exist_ok=True)
        (fixture / "docs" / "vision.md").write_text(
            "# Vision — ShareShed\nProblem and Stakeholder but no success section.\n")
        work = bench.work_delta(fixture, seed_sha, scenario)
        self.assertFalse(work["deliverable_produced"])
        self.assertIn("Success", work["missing_markers"])


class CleanFixtureTest(unittest.TestCase):
    """T-085 — the fixture is a bootstrapped project (framework + empty docs +
    scenario), NOT a copy of the repo under test's own docs/."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_framework_present_repo_docs_absent(self):
        fixture = Path(self.tmp.name) / "fx"
        bench.build_fixture(_REPO, fixture, bench.DEFAULT_SCENARIO_DIR,
                            include_working_tree=False)
        # Framework copied…
        self.assertTrue((fixture / "docs-eng-process" / "procedures").is_dir())
        self.assertTrue((fixture / "scripts" / "openup-board.py").exists())
        # …but the repo's own developed docs are NOT (this repo has both).
        self.assertTrue((_REPO / "docs" / "roadmap.md").exists(),
                        "precondition: the repo under test has docs/roadmap.md")
        self.assertFalse((fixture / "docs" / "roadmap.md").exists())
        self.assertFalse((fixture / "docs" / "project-status.md").exists())
        self.assertFalse((fixture / "docs" / "changes" / "archive").exists())

    def test_vision_fixture_docs_holds_only_the_brief(self):
        fixture = Path(self.tmp.name) / "fxv"
        scenario_dir = _REPO / "scripts" / "bench-scenarios" / "inception-vision"
        bench.build_fixture(_REPO, fixture, scenario_dir, include_working_tree=False)
        self.assertTrue((fixture / "docs" / "inputs" / "stakeholder-brief.md").exists())
        # No pre-existing project state leaked in.
        self.assertFalse((fixture / "docs" / "project-status.md").exists())
        self.assertFalse((fixture / "docs" / "product").exists())


if __name__ == "__main__":
    unittest.main()

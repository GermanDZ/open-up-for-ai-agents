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


if __name__ == "__main__":
    unittest.main()

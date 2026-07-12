#!/usr/bin/env python3
"""Integration tests for the reference-driver loop (T-072).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent
    python3 scripts/tests/test_openup_agent

Hermetic: each test builds an isolated tmp OpenUP project (a neutral procedure
file + tier-map.yaml + optional gate scripts) and drives the loop with a SCRIPTED
completion function (the loop's `_completion` seam) — zero real network for the
loop tests. One separate test spins a stdlib http.server to exercise the real
urllib OpenAI-compatible client path.
"""

import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import llm, loop, tiers  # noqa: E402


TIER_MAP = """\
claude-code:
  scribe: haiku
  reasoning: inherit
driver:
  scribe: "${OPENUP_MODEL_SMALL:-local-small}"
  reasoning: "${OPENUP_MODEL_MAIN:-local-main}"
"""


def _procedure(tier="reasoning"):
    return (
        "---\n"
        "name: openup-demo\n"
        "description: a trivial demo procedure\n"
        "tier: %s\n"
        "---\n\n"
        "# Demo\n\nDo the thing, then emit `OPENUP-DEMO: DONE — <reason>`.\n"
    ) % tier


def _asst(content=None, tool_calls=None):
    """Build an OpenAI-style choices[0].message response."""
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def _tool_call(cid, name, args):
    return {"id": cid, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs-eng-process" / "procedures").mkdir(parents=True)
        (self.root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        (self.root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_procedure())
        (self.root / "scripts").mkdir()
        self.env = {"LLM_API_URL": "http://unused.local/v1", "LLM_API_KEY": "k"}

    def tearDown(self):
        self.tmp.cleanup()

    def _write_gate(self, name, body):
        (self.root / "scripts" / name).write_text(body)

    # -- happy paths ------------------------------------------------------
    def test_immediate_sentinel_exits_clean(self):
        calls = []

        def completion(model, messages, tools_):
            calls.append(model)
            return _asst("all done\nOPENUP-DEMO: DONE — nothing to do")

        rc = loop.run(str(self.root), "demo", env=self.env, _completion=completion)
        self.assertEqual(rc, 0)
        # model resolved from the driver column (reasoning -> local-main)
        self.assertEqual(calls[0], "local-main")

    def test_tool_call_then_sentinel(self):
        (self.root / "target.txt").write_text("payload-42\n")
        seen = {}

        def completion(model, messages, tools_):
            # first turn: ask to read a file; second: finish
            if not seen:
                seen["called"] = True
                return _asst(tool_calls=[_tool_call("c1", "read_file", {"path": "target.txt"})])
            # the tool result must be in the history
            tool_msgs = [m for m in messages if m.get("role") == "tool"]
            seen["tool_content"] = tool_msgs[-1]["content"]
            return _asst("read it\nOPENUP-DEMO: DONE — read the file")

        rc = loop.run(str(self.root), "demo", env=self.env, _completion=completion)
        self.assertEqual(rc, 0)
        self.assertIn("payload-42", seen["tool_content"])

    # -- gate enforcement -------------------------------------------------
    def test_gate_failure_reinjects_then_succeeds(self):
        # A fake fence that fails while a .gate_block file exists.
        self._write_gate("openup-fence.py",
                         "import os,sys\n"
                         "sys.exit(1 if os.path.exists('.gate_block') else 0)\n")
        # A cleanup script the model is allowed to exec (python3 scripts/*.py).
        self._write_gate("clear-block.py",
                         "import os\n"
                         "os.path.exists('.gate_block') and os.remove('.gate_block')\n")
        (self.root / ".gate_block").write_text("")
        turns = {"n": 0}
        reinjected = {"seen": False}

        def completion(model, messages, tools_):
            turns["n"] += 1
            if turns["n"] == 1:
                return _asst("OPENUP-DEMO: DONE — first try")  # gate will fail
            if turns["n"] == 2:
                # driver must have re-injected the gate failure as a user message
                if any("gates FAILED" in (m.get("content") or "") for m in messages):
                    reinjected["seen"] = True
                return _asst(tool_calls=[_tool_call("c9", "exec",
                             {"command": "python3 scripts/clear-block.py"})])
            return _asst("fixed\nOPENUP-DEMO: DONE — cleared block")

        rc = loop.run(str(self.root), "demo", env=self.env, _completion=completion)
        self.assertEqual(rc, 0)
        self.assertTrue(reinjected["seen"], "gate failure should be re-injected into the loop")
        self.assertFalse((self.root / ".gate_block").exists())

    def test_sentinel_blocked_while_gate_fails(self):
        self._write_gate("check-docs.py", "import sys; sys.exit(2)\n")

        def completion(model, messages, tools_):
            return _asst("OPENUP-DEMO: DONE — but docs are broken")

        rc = loop.run(str(self.root), "demo", max_iterations=3, env=self.env,
                      _completion=completion)
        # never accepts the sentinel because the gate never passes
        self.assertEqual(rc, 4)

    # -- termination guarantees ------------------------------------------
    def test_max_iterations_cap(self):
        def completion(model, messages, tools_):
            return _asst("still thinking, no sentinel")  # never terminal

        rc = loop.run(str(self.root), "demo", max_iterations=3, env=self.env,
                      _completion=completion)
        self.assertEqual(rc, 4)

    def test_endpoint_error_returns_3(self):
        def completion(model, messages, tools_):
            raise llm.LLMError("boom")

        rc = loop.run(str(self.root), "demo", env=self.env, _completion=completion)
        self.assertEqual(rc, 3)

    # -- config errors ----------------------------------------------------
    def test_missing_api_url_returns_2(self):
        rc = loop.run(str(self.root), "demo", env={}, _completion=lambda *a: None)
        self.assertEqual(rc, 2)

    def test_missing_procedure_returns_2(self):
        rc = loop.run(str(self.root), "nonexistent", env=self.env,
                      _completion=lambda *a: None)
        self.assertEqual(rc, 2)

    def test_unknown_tier_returns_2(self):
        (self.root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(
            _procedure(tier="mystery"))
        rc = loop.run(str(self.root), "demo", env=self.env, _completion=lambda *a: None)
        self.assertEqual(rc, 2)


class TierResolutionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs-eng-process" / "procedures").mkdir(parents=True)
        (self.root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        (self.root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_procedure())

    def tearDown(self):
        self.tmp.cleanup()

    def test_env_override(self):
        self.assertEqual(
            tiers.resolve_model(self.root, "demo", "driver", env={"OPENUP_MODEL_MAIN": "gpt-x"}),
            "gpt-x")

    def test_default_placeholder(self):
        self.assertEqual(tiers.resolve_model(self.root, "demo", "driver", env={}), "local-main")

    def test_openup_prefixed_name_accepted(self):
        self.assertEqual(tiers.resolve_model(self.root, "openup-demo", "driver", env={}),
                         "local-main")

    def test_unknown_tier_raises(self):
        (self.root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(
            _procedure(tier="mystery"))
        with self.assertRaises(tiers.TierError):
            tiers.resolve_model(self.root, "demo", "driver", env={})


class _CannedHandler(BaseHTTPRequestHandler):
    """Return a fixed completions response; capture the received model."""
    received = {}

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        _CannedHandler.received["model"] = body.get("model")
        _CannedHandler.received["auth"] = self.headers.get("Authorization")
        payload = json.dumps(_asst("OPENUP-DEMO: DONE — via http")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):  # silence
        pass


class HttpClientTest(unittest.TestCase):
    """Exercises the real urllib OpenAI-compatible path against a local server."""

    def setUp(self):
        _CannedHandler.received = {}
        self.server = HTTPServer(("127.0.0.1", 0), _CannedHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d/v1" % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_chat_completion_roundtrip(self):
        resp = llm.chat_completion(self.url, "sekret", "local-main",
                                   [{"role": "user", "content": "hi"}],
                                   tools=None)
        msg = llm.first_message(resp)
        self.assertIn("OPENUP-DEMO: DONE", msg["content"])
        self.assertEqual(_CannedHandler.received["model"], "local-main")
        self.assertEqual(_CannedHandler.received["auth"], "Bearer sekret")


if __name__ == "__main__":
    unittest.main()

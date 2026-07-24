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

    # -- debug transcript log (T-098) -------------------------------------
    def test_debug_log_records_full_interaction(self):
        def completion(model, messages, tools_):
            return _asst("done\nOPENUP-DEMO: DONE — ok")
        dbg = self.root / "llm-debug.jsonl"
        env = dict(self.env)
        env["OPENUP_AGENT_DEBUG_LOG"] = str(dbg)
        rc = loop.run(str(self.root), "demo", env=env, _completion=completion)
        self.assertEqual(rc, 0)
        lines = [json.loads(l) for l in dbg.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        rec = lines[0]
        self.assertEqual(rec["iteration"], 1)
        self.assertEqual(rec["model"], "local-main")
        self.assertTrue(any(m["role"] == "system" for m in rec["request"]))
        self.assertIn("OPENUP-DEMO: DONE", rec["response"]["content"])
        self.assertIn("tool_calls", rec["response"])

    def test_no_debug_log_when_unset(self):
        def completion(model, messages, tools_):
            return _asst("done\nOPENUP-DEMO: DONE — ok")
        rc = loop.run(str(self.root), "demo", env=self.env, _completion=completion)
        self.assertEqual(rc, 0)
        self.assertFalse((self.root / "llm-debug.jsonl").exists())

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


class NarrationTest(unittest.TestCase):
    """T-109: the console narrates targets and progress, with no blank lines;
    OPENUP_AGENT_VERBOSE=1 restores the old detail."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs-eng-process" / "procedures").mkdir(parents=True)
        (self.root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        (self.root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_procedure())
        (self.root / "scripts").mkdir()
        self.env = {"LLM_API_URL": "http://unused.local/v1", "LLM_API_KEY": "k"}
        self.addCleanup(self.tmp.cleanup)

    def _run_captured(self, completion):
        import contextlib, io
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            rc = loop.run(str(self.root), "demo", env=self.env,
                          _completion=completion)
        return rc, err.getvalue()

    def _read_then_done(self):
        (self.root / "target.txt").write_text("x\n")
        seen = {}

        def completion(model, messages, tools_):
            if not seen:
                seen["called"] = True
                return _asst(tool_calls=[
                    _tool_call("c1", "read_file", {"path": "target.txt"})])
            return _asst("OPENUP-DEMO: DONE — ok")
        return completion

    def test_tool_line_names_target_not_char_count(self):
        rc, err = self._run_captured(self._read_then_done())
        self.assertEqual(rc, 0)
        self.assertIn("read_file target.txt", err)
        self.assertNotIn("chars", err)

    def test_verbose_restores_char_counts(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"OPENUP_AGENT_VERBOSE": "1"}):
            rc, err = self._run_captured(self._read_then_done())
        self.assertEqual(rc, 0)
        self.assertIn("read_file target.txt -> ", err)
        self.assertIn("chars", err)

    def test_model_turn_progress_logged(self):
        rc, err = self._run_captured(self._read_then_done())
        self.assertEqual(rc, 0)
        self.assertIn("model turn 1/", err)
        self.assertIn("model turn 2/", err)

    def test_no_blank_lines_emitted(self):
        rc, err = self._run_captured(self._read_then_done())
        self.assertEqual(rc, 0)
        self.assertTrue(err.strip())
        self.assertNotIn("\n\n", err)
        loop._log("")   # the guard: a blank message emits nothing
        loop._log("  ")

    def test_exec_target_format(self):
        # the salient-arg formatter, directly
        self.assertEqual(loop._tool_target("exec", {"command": "git status"}),
                         ": git status")
        self.assertEqual(loop._tool_target("glob", {"pattern": "docs/*.md"}),
                         " docs/*.md")
        long = "x" * 80
        self.assertTrue(loop._tool_target("read_file", {"path": long})
                        .endswith("..."))


class AskUserTest(unittest.TestCase):
    """The 7th tool: interactive answer vs async suspend-into-input-request (T-074)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs-eng-process" / "procedures").mkdir(parents=True)
        (self.root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        (self.root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_procedure())
        (self.root / "docs" / "changes" / "T-9").mkdir(parents=True)
        (self.root / "docs" / "changes" / "T-9" / "plan.md").write_text(
            "---\nid: T-9\nstatus: ready\n---\n# T-9\n")
        (self.root / ".openup").mkdir()
        (self.root / ".openup" / "state.json").write_text(json.dumps({"task_id": "T-9"}))
        # The async path shells out to scripts/openup-input.py relative to --dir.
        (self.root / "scripts").symlink_to(Path(__file__).resolve().parents[1])
        self.env = {"LLM_API_URL": "http://unused.local/v1", "LLM_API_KEY": "k"}

    def tearDown(self):
        self.tmp.cleanup()

    def _ask_call(self):
        return _asst(tool_calls=[_tool_call("c1", "ask_user",
                     {"question": "pg or mysql?", "options": ["pg", "mysql"]})])

    def test_async_suspends_and_sets_awaiting_input(self):
        rc = loop.run(str(self.root), "demo", env=self.env, interactive=False,
                      _completion=lambda m, ms, t: self._ask_call())
        self.assertEqual(rc, loop.EXIT_SUSPEND)  # exit 5
        plan = (self.root / "docs" / "changes" / "T-9" / "plan.md").read_text()
        self.assertIn("awaiting-input:", plan)
        # a real input-request doc was created
        self.assertTrue(any((self.root / "docs" / "input-requests").glob("*.md")))

    def test_interactive_returns_answer_and_continues(self):
        seen = {}

        def completion(model, messages, tools_):
            if not seen:
                seen["x"] = 1
                return self._ask_call()
            # the human's answer must be in the tool result history
            tool_msgs = [m for m in messages if m.get("role") == "tool"]
            seen["answer_seen"] = "mysql" in tool_msgs[-1]["content"]
            return _asst("ok\nOPENUP-DEMO: DONE — answered")

        rc = loop.run(str(self.root), "demo", env=self.env, interactive=True,
                      _completion=completion, _ask=lambda q, o: "mysql")
        self.assertEqual(rc, 0)
        self.assertTrue(seen["answer_seen"])
        # interactive mode must NOT create an input-request
        self.assertFalse(any((self.root / "docs" / "input-requests").glob("*.md")))


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


class TimeoutHandlingTest(unittest.TestCase):
    """T-082 — a slow/failed transport is a clean LLMError, not an uncaught crash;
    the per-call timeout is configurable via OPENUP_AGENT_TIMEOUT."""

    def test_socket_timeout_becomes_llm_error(self):
        def raiser(_req):
            raise TimeoutError("timed out")  # what a socket read timeout raises
        with self.assertRaises(llm.LLMError):
            llm.chat_completion("http://x/v1", "k", "m",
                                [{"role": "user", "content": "hi"}], _opener=raiser)

    def test_oserror_becomes_llm_error(self):
        def raiser(_req):
            raise OSError("connection reset by peer")
        with self.assertRaises(llm.LLMError):
            llm.chat_completion("http://x/v1", "k", "m",
                                [{"role": "user", "content": "hi"}], _opener=raiser)

    def test_timeout_loop_exits_endpoint_error(self):
        """An LLM call that times out makes the loop return 3 (endpoint-error),
        never an uncaught exception."""
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "docs-eng-process" / "procedures").mkdir(parents=True)
        (root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        (root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_procedure())

        def completion(model, messages, tools_):
            raise llm.LLMError("transport failure after 600s … timed out")
        rc = loop.run(str(root), "demo",
                      env={"LLM_API_URL": "http://x/v1", "LLM_API_KEY": "k"},
                      _completion=completion)
        self.assertEqual(rc, 3)
        tmp.cleanup()

    def test_timeout_env_plumbs_through(self):
        """OPENUP_AGENT_TIMEOUT is parsed and passed to chat_completion."""
        from unittest.mock import patch
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "docs-eng-process" / "procedures").mkdir(parents=True)
        (root / "docs-eng-process" / "tier-map.yaml").write_text(TIER_MAP)
        (root / "docs-eng-process" / "procedures" / "openup-demo.md").write_text(_procedure())
        captured = {}

        def fake_cc(api_url, api_key, model, msgs, tools=None, timeout=None):
            captured["timeout"] = timeout
            return _asst("OPENUP-DEMO: DONE — x")
        env = {"LLM_API_URL": "http://x/v1", "LLM_API_KEY": "k",
               "OPENUP_AGENT_TIMEOUT": "42"}
        with patch.object(loop.llm, "chat_completion", fake_cc):
            rc = loop.run(str(root), "demo", env=env)
        self.assertEqual(rc, 0)
        self.assertEqual(captured["timeout"], 42)
        tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

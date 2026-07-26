#!/usr/bin/env python3
"""Hermetic tests for scripts/openup_agent/probe_task.py (T-134).

Run with either:
    python3 -m unittest scripts.tests.test_openup_agent_probe_task
    python3 scripts/tests/test_openup_agent_probe_task.py

Scripted `_completion` seam — zero real network. Confirms the standalone
runner passes the task-def's instruction/system_prompt through to loop.run
unchanged, and never touches docs-eng-process/process-map.yaml.
"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openup_agent import probe_task  # noqa: E402


TASK_DEF = {
    "name": "Probe Code Artifact",
    "role": "developer",
    "artifact": "code",
    "output_path": "probe/hello.rb",
    "inputs": [],
    "judgment": [
        "Writes a small, self-contained Ruby script with no external dependencies.",
        "The script prints the exact line `OPENUP-CODE-PROBE-OK` to stdout when run.",
        "After writing the file, runs it with exec as `ruby probe/hello.rb` and confirms the marker line appears in stdout.",
    ],
}


def _asst(content=None, tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def _tool_call(cid, name, args):
    return {"id": cid, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


class ProbeTaskTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = {"LLM_API_URL": "http://unused.local/v1", "LLM_API_KEY": "k"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_tool_call_happy_path(self):
        calls = []

        def completion(model, messages, tools_):
            calls.append(model)
            if len(calls) == 1:
                self.assertIn("Probe Code Artifact", messages[-1]["content"])
                self.assertIn("probe/hello.rb", messages[-1]["content"])
                return _asst(tool_calls=[_tool_call(
                    "c1", "write_file",
                    {"path": "probe/hello.rb", "content": "puts 'OPENUP-CODE-PROBE-OK'\n"})])
            if len(calls) == 2:
                return _asst(tool_calls=[_tool_call(
                    "c2", "exec", {"command": "ruby probe/hello.rb"})])
            return _asst("confirmed\nOPENUP-TASK: DONE")

        rc = probe_task.run_probe_task(
            self.root, TASK_DEF, "test-model", env=self.env, _completion=completion)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, ["test-model"] * 3)
        self.assertEqual(
            (self.root / "probe" / "hello.rb").read_text(encoding="utf-8"),
            "puts 'OPENUP-CODE-PROBE-OK'\n",
        )

    def test_system_prompt_permits_a_tool_call_after_write(self):
        # The shared cycle.py _task_system_prompt forbids any tool call after
        # write_file — this probe's own prompt must NOT carry that restriction.
        self.assertNotIn("do NOT read the file back", probe_task._CODE_TASK_SYSTEM_PROMPT)
        self.assertIn("exec", probe_task._CODE_TASK_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()

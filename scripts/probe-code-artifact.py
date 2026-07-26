#!/usr/bin/env python3
"""Run the T-134 code-artifact probe once, in a disposable fixture.

Standalone — does NOT go through openup-agent.py's cycle engine or any
phase/activity resolution. Builds a fresh, disposable, git-init'd fixture
(reusing openup-agent-bench.py's build_fixture, with --include-working-tree
semantics so this task's own in-progress edits to task-library.yaml /
tools.py / openup-process-map.py are what gets tested), loads the
probe-code-artifact task-def from the fixture's own vendored
docs-eng-process/task-library.yaml, drives ONE bounded sub-run via
openup_agent.probe_task.run_probe_task, then independently re-runs the
produced file to confirm it actually works (defense in depth against a
model that fakes success).

Never point this at a persistent/real repository — the fixture is always a
fresh tempfile.mkdtemp() (see Safeguards in docs/changes/T-134/plan.md).

Usage:
    python3 scripts/probe-code-artifact.py [--keep] [--max-iterations N]

Requires the same env as the reference driver: LLM_API_URL, LLM_API_KEY,
OPENUP_MODEL_MAIN (used as the sub-run's model).

Prints one JSON line: {exit_code, marker_in_source, exec_confirmed,
independent_rerun_ok, iterations, fixture} and exits 0 on a clean pass,
1 otherwise (a failing result is still a complete, valid probe outcome —
see docs/changes/T-134/plan.md's Success Measures).
"""

import argparse
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
SCENARIO_DIR = HERE / "bench-scenarios" / "code-probe"
TASK_ID = "probe-code-artifact"
MARKER = "OPENUP-CODE-PROBE-OK"


def _load_hyphenated(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


bench = _load_hyphenated("openup_agent_bench", HERE / "openup-agent-bench.py")
pm = _load_hyphenated("openup_process_map", HERE / "openup-process-map.py")

sys.path.insert(0, str(HERE))
from openup_agent import probe_task  # noqa: E402


def _count_usage_turns(usage_log_path):
    if not usage_log_path.exists():
        return 0
    return sum(1 for line in usage_log_path.read_text(encoding="utf-8").splitlines() if line.strip())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true", help="keep the fixture after the run (debugging)")
    ap.add_argument("--max-iterations", type=int, default=20)
    args = ap.parse_args(argv)

    env = dict(os.environ)
    model = env.get("OPENUP_MODEL_MAIN")
    if not env.get("LLM_API_URL") or not model:
        print(json.dumps({"error": "LLM_API_URL and OPENUP_MODEL_MAIN must be set"}))
        return 2

    workroot = Path(tempfile.mkdtemp(prefix="openup-code-probe-"))
    fixture = workroot / "fixture"
    try:
        bench.build_fixture(REPO_ROOT, fixture, SCENARIO_DIR, include_working_tree=True)

        tasks = pm.load_tasks(fixture)
        task_def = tasks.get(TASK_ID)
        if task_def is None:
            print(json.dumps({"error": "%s not found in fixture's task-library.yaml" % TASK_ID}))
            return 2

        usage_log = workroot / "usage.jsonl"
        debug_log = workroot / "debug.jsonl"
        run_env = dict(env)
        run_env["OPENUP_AGENT_USAGE_LOG"] = str(usage_log)
        run_env["OPENUP_AGENT_DEBUG_LOG"] = str(debug_log)

        exit_code = probe_task.run_probe_task(
            fixture, task_def, model, env=run_env, max_iterations=args.max_iterations)

        out_file = fixture / task_def["output_path"]
        source = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
        marker_in_source = MARKER in source

        exec_confirmed = False
        rerun = subprocess.run(
            ["ruby", task_def["output_path"]], cwd=str(fixture),
            capture_output=True, text=True, timeout=30,
        ) if out_file.exists() else None
        independent_rerun_ok = bool(rerun and rerun.returncode == 0 and MARKER in rerun.stdout)

        if debug_log.exists():
            for line in debug_log.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                resp = rec.get("response") or {}
                for call in resp.get("tool_calls") or []:
                    fn = (call.get("function") or {})
                    if fn.get("name") == "exec":
                        try:
                            call_args = json.loads(fn.get("arguments") or "{}")
                        except ValueError:
                            call_args = {}
                        if str(call_args.get("command", "")).strip().startswith("ruby"):
                            exec_confirmed = True

        result = {
            "exit_code": exit_code,
            "marker_in_source": marker_in_source,
            "exec_confirmed": exec_confirmed,
            "independent_rerun_ok": independent_rerun_ok,
            "iterations": _count_usage_turns(usage_log),
            "fixture": str(fixture) if args.keep else None,
        }
        print(json.dumps(result, indent=2))
        clean_pass = exit_code == 0 and marker_in_source and exec_confirmed and independent_rerun_ok
        return 0 if clean_pass else 1
    finally:
        if not args.keep:
            shutil.rmtree(workroot, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

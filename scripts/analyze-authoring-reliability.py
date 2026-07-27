#!/usr/bin/env python3
"""Measures T-106's authoring-reliability gate from a completed
openup-agent-bench.py run's saved driver logs — independent of the run's
overall driver exit code (T-136).

The inception-taskdef scenario's driver process cannot report a clean
"pass" exit today: by design (T-092 recovery mode), it runs past the fixed
Inception authoring activities into a deterministic consent-gate pause that
every run hits, regardless of model quality (see docs/changes/T-136/plan.md
Current State). This script measures the thing the gate actually cares
about — did each authoring sub-run complete without restarting and within
the turn ceiling — directly from the driver's own per-sub-run log lines.

A run's "authoring-chain clean" iff every one of its sub-runs (each block
starting at a "procedure=<name> model=<model> ..." line and running until
the next such line, a FATAL: line, or end of file) used <= --max-turns
turns and no tool call repeated 3+ times consecutively within it.

Reads only. Never modifies openup-agent-bench.py's own pass/fail semantics.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROCEDURE_RE = re.compile(r"^\[openup-agent\] procedure=(?P<name>.+?) model=")
TURN_RE = re.compile(r"^\[openup-agent\] model turn (?P<i>\d+)/(?P<n>\d+)")
FATAL_RE = re.compile(r"^\[openup-agent\] FATAL: (?P<reason>.+)$")
TOOL_CALL_RE = re.compile(
    r"^\[openup-agent\] (?P<name>read_file|write_file|edit_file|glob|grep|exec)"
    r"[: ]?\s*(?P<arg>.*)$"
)

DEFAULT_MAX_TURNS = 6
DEFAULT_REPEAT_THRESHOLD = 3


def parse_sub_runs(log_text):
    """Split a driver log into sub-run blocks: [{name, turns, tool_calls, fatal}]."""
    blocks = []
    cur = None
    for line in log_text.splitlines():
        m = PROCEDURE_RE.match(line)
        if m:
            cur = {"name": m.group("name"), "turns": 0, "tool_calls": [], "fatal": None}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        m = TURN_RE.match(line)
        if m:
            cur["turns"] = int(m.group("i"))
            continue
        m = FATAL_RE.match(line)
        if m:
            cur["fatal"] = m.group("reason").strip()
            continue
        m = TOOL_CALL_RE.match(line)
        if m:
            cur["tool_calls"].append((m.group("name"), m.group("arg").strip()))
    return blocks


def _max_consecutive_repeat(tool_calls):
    """Longest run of consecutive identical (name, arg) tuples; the offending
    call, or (0, None) if there are no tool calls."""
    best_len, best_call = 0, None
    run_len, run_call = 0, None
    for call in tool_calls:
        if call == run_call:
            run_len += 1
        else:
            run_call, run_len = call, 1
        if run_len > best_len:
            best_len, best_call = run_len, run_call
    return best_len, best_call


def classify_sub_run(block, max_turns=DEFAULT_MAX_TURNS,
                     repeat_threshold=DEFAULT_REPEAT_THRESHOLD):
    """Return {name, turns, clean, reason}.

    Checked in diagnostic-priority order, not just "what stopped the run":
    a restart pattern is the more informative root cause even when a FATAL
    error also occurred in the same block (e.g. a rate limit that happened
    to cut off an already-looping sub-run) — surfacing the restart, not the
    coincidental external error, is the point of this analyzer (T-136).
    """
    repeat_len, repeat_call = _max_consecutive_repeat(block["tool_calls"])
    if repeat_len >= repeat_threshold:
        return {"name": block["name"], "turns": block["turns"], "clean": False,
                "reason": "restart: %r repeated %d times consecutively"
                         % (repeat_call, repeat_len)}
    if block["fatal"]:
        return {"name": block["name"], "turns": block["turns"], "clean": False,
                "reason": "endpoint/driver error: %s" % block["fatal"]}
    if block["turns"] > max_turns:
        return {"name": block["name"], "turns": block["turns"], "clean": False,
                "reason": "exceeded max-turns (%d > %d)" % (block["turns"], max_turns)}
    return {"name": block["name"], "turns": block["turns"], "clean": True, "reason": None}


def classify_run(log_path, max_turns=DEFAULT_MAX_TURNS,
                 repeat_threshold=DEFAULT_REPEAT_THRESHOLD):
    text = log_path.read_text(encoding="utf-8", errors="replace")
    blocks = parse_sub_runs(text)
    if not blocks:
        return {"run": log_path.name, "clean": False,
                "reason": "no sub-run ever started", "sub_runs": []}
    sub_runs = [classify_sub_run(b, max_turns, repeat_threshold) for b in blocks]
    bad = [s for s in sub_runs if not s["clean"]]
    if bad:
        return {"run": log_path.name, "clean": False,
                "reason": "%s: %s" % (bad[0]["name"], bad[0]["reason"]),
                "sub_runs": sub_runs}
    return {"run": log_path.name, "clean": True, "reason": None, "sub_runs": sub_runs}


def analyze(bench_dir, max_turns=DEFAULT_MAX_TURNS,
           repeat_threshold=DEFAULT_REPEAT_THRESHOLD):
    logs = sorted(Path(bench_dir).glob("run-*.driver.log"))
    per_run = [classify_run(p, max_turns, repeat_threshold) for p in logs]
    clean = [r for r in per_run if r["clean"]]
    return {
        "runs": len(per_run),
        "authoring_chain_clean": len(clean),
        "clean_rate": round(len(clean) / len(per_run), 4) if per_run else 0.0,
        "per_run": per_run,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench-dir", required=True,
                    help="a completed openup-agent-bench.py output dir "
                         "(contains run-0N.driver.log files)")
    ap.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    ap.add_argument("--repeat-threshold", type=int, default=DEFAULT_REPEAT_THRESHOLD)
    args = ap.parse_args(argv)

    result = analyze(args.bench_dir, args.max_turns, args.repeat_threshold)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

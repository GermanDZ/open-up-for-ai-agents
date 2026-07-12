"""The reference-driver agentic loop (T-072).

Procedure-agnostic: loads docs-eng-process/procedures/openup-<procedure>.md as the
model's task instruction, resolves ONE model from its `tier:` via the tier-map
driver column, advertises the six-tool surface, and runs a plain turn loop against
an OpenAI-compatible endpoint. The DRIVER — not the model — runs the deterministic
gates (openup-fence.py check, check-docs.py) before accepting a terminal sentinel,
so enforcement never depends on the model remembering to check.

Stdlib-only. Progress goes to stderr; the procedure's sentinel line is the only
thing printed to stdout, so an outer loop can read it.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import llm, tiers, tools

# A terminal sentinel is a line like "OPENUP-NEXT: ADVANCED — T-072" or
# "OPENUP-NEXT: DONE — board empty". Any procedure that ends with an
# "OPENUP-<NAME>: <VERB> …" line is recognized.
SENTINEL_RE = re.compile(r"^OPENUP-[A-Z][A-Z-]*:\s*\S", re.MULTILINE)

# Deterministic gates the driver runs itself before accepting a sentinel.
# Each is (label, argv); a gate whose script is absent under --dir is skipped.
GATES = [
    ("fence", ["python3", "scripts/openup-fence.py", "check"]),
    ("check-docs", ["python3", "scripts/check-docs.py"]),
]

DEFAULT_MAX_ITERATIONS = 50


class ConfigError(Exception):
    """Missing/invalid runtime configuration (env, procedure, tier)."""


def _log(msg):
    sys.stderr.write("[openup-agent] %s\n" % msg)
    sys.stderr.flush()


def _env_config(env):
    api_url = env.get("LLM_API_URL")
    if not api_url:
        raise ConfigError(
            "LLM_API_URL is not set — export LLM_API_URL (and LLM_API_KEY) to an "
            "OpenAI-compatible endpoint (e.g. http://localhost:1234/v1)"
        )
    return api_url, env.get("LLM_API_KEY", "")


def _system_prompt(root, procedure, procedure_text):
    return (
        "You are an OpenUP delivery agent. Drive the procedure below to completion "
        "using ONLY the provided tools (read_file, write_file, edit_file, glob, grep, "
        "exec). exec runs `git …` and `python3 scripts/*.py …` only.\n"
        "Working directory (all paths are relative to it): %s\n"
        "Deterministic steps are scripts — call them via exec; the LLM is needed only "
        "for judgment (authoring specs/code, grading). The driver runs the enforcement "
        "gates itself; do not skip persistence.\n"
        "When the procedure is COMPLETE, reply with NO tool calls and put its sentinel "
        "line last (e.g. `OPENUP-NEXT: ADVANCED — <task>` or `OPENUP-NEXT: DONE — "
        "<reason>`).\n\n"
        "----- PROCEDURE: %s -----\n%s"
    ) % (root, procedure, procedure_text)


def run_gates(root):
    """Run each present deterministic gate. Return (ok, report_str).

    ok is False iff any *present* gate exits non-zero. A gate whose script is
    absent under --dir is skipped (the driver stays usable on partial trees).
    """
    root = Path(root)
    lines, ok = [], True
    for label, argv in GATES:
        script = root / argv[1]
        if not script.exists():
            lines.append("%s: skipped (no %s)" % (label, argv[1]))
            continue
        proc = subprocess.run(argv, cwd=str(root), capture_output=True, text=True)
        if proc.returncode == 0:
            lines.append("%s: OK" % label)
        else:
            ok = False
            detail = (proc.stdout + proc.stderr).strip()
            lines.append("%s: FAILED (exit %d)\n%s" % (label, proc.returncode, detail[:2000]))
    return ok, "\n".join(lines)


def _dispatch_tool_calls(tool_impl, tool_calls):
    """Run each tool call; return the list of role:tool result messages."""
    results = []
    for call in tool_calls:
        fn = call.get("function", {})
        name = fn.get("name", "")
        raw_args = fn.get("arguments", "") or "{}"
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError as e:
            result = "ERROR: could not parse arguments for %s: %s" % (name, e)
        else:
            result = tool_impl.dispatch(name, args)
        _log("tool %s -> %d chars" % (name, len(str(result))))
        results.append({
            "role": "tool",
            "tool_call_id": call.get("id", ""),
            "content": str(result),
        })
    return results


def run(dir, procedure, max_iterations=DEFAULT_MAX_ITERATIONS, env=None,
        _completion=None):
    """Drive `procedure` under `dir`. Return an int exit code.

    `_completion` is a test seam: a callable(model, messages, tools) -> response
    dict replacing the live llm.chat_completion.
    """
    env = os.environ if env is None else env
    root = Path(dir).resolve()

    try:
        api_url, api_key = _env_config(env)
        proc_path = tiers.procedure_path(root, procedure)
        if not proc_path.exists():
            raise ConfigError("procedure not found: %s" % proc_path)
        procedure_text = proc_path.read_text(encoding="utf-8")
        model = tiers.resolve_model(root, procedure, target="driver", env=env)
    except (ConfigError, tiers.TierError) as e:
        _log("FATAL: %s" % e)
        return 2

    _log("procedure=%s model=%s endpoint=%s dir=%s"
         % (procedure, model, llm.completions_url(api_url), root))

    tool_impl = tools.Tools(root)
    messages = [
        {"role": "system", "content": _system_prompt(root, procedure, procedure_text)},
        {"role": "user", "content": "Execute the procedure now."},
    ]

    def complete(msgs):
        if _completion is not None:
            return _completion(model, msgs, tools.TOOL_DEFS)
        return llm.chat_completion(api_url, api_key, model, msgs, tools=tools.TOOL_DEFS)

    for i in range(1, max_iterations + 1):
        try:
            response = complete(messages)
            message = llm.first_message(response)
        except llm.LLMError as e:
            _log("FATAL: endpoint error on iteration %d: %s" % (i, e))
            return 3

        tool_calls = message.get("tool_calls") or []
        messages.append(message)

        if tool_calls:
            messages.extend(_dispatch_tool_calls(tool_impl, tool_calls))
            continue

        content = message.get("content") or ""
        if SENTINEL_RE.search(content):
            ok, report = run_gates(root)
            if ok:
                sentinel = next(l for l in content.splitlines() if SENTINEL_RE.match(l))
                _log("procedure complete on iteration %d; gates clean" % i)
                print(sentinel.strip())
                return 0
            _log("sentinel emitted but gates failed on iteration %d; re-injecting" % i)
            messages.append({
                "role": "user",
                "content": "The deterministic gates FAILED — you cannot finish yet. "
                           "Fix these, then re-emit the sentinel:\n" + report,
            })
            continue

        # No tool calls and no sentinel: nudge once toward a terminal state.
        _log("no tool calls and no sentinel on iteration %d; nudging" % i)
        messages.append({
            "role": "user",
            "content": "Continue with tool calls, or if the procedure is complete "
                       "emit its sentinel line (e.g. `OPENUP-NEXT: DONE — <reason>`).",
        })

    _log("max iterations (%d) reached with no clean sentinel" % max_iterations)
    return 4

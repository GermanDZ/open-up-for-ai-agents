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
import time
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

# Gate exit codes that mean "inapplicable here" (skip, don't fail): the fence
# returns 3 when there is no lane/state to fence — e.g. a fresh-project procedure
# run (create-vision in Inception) that never went through start-iteration. That
# is not a violation, so treat it like an absent gate. A real lane still fences.
GATE_INAPPLICABLE = {"fence": {3}}

DEFAULT_MAX_ITERATIONS = 50

# Async human-input suspend: distinct sentinel + exit code so an outer loop can
# tell "suspended, awaiting a human answer" apart from success/error (T-074).
SUSPEND_SENTINEL = "OPENUP-AGENT: SUSPENDED"
EXIT_SUSPEND = 5


class ConfigError(Exception):
    """Missing/invalid runtime configuration (env, procedure, tier)."""


def _log(msg):
    sys.stderr.write("[openup-agent] %s\n" % msg)
    sys.stderr.flush()


def _append_usage(path, iteration, model, latency_ms, response):
    """Append one per-completion usage record to OPENUP_AGENT_USAGE_LOG (T-080).

    Opt-in benchmarking side channel: when the env var is set, one JSON line per
    LLM call records the endpoint's `usage` object (verbatim; ``{}`` if omitted)
    plus the iteration, model, and measured latency. When the var is unset the
    caller never invokes this, so the driver's behavior is byte-for-byte
    unchanged. Failures to write are swallowed — instrumentation must never break
    a run.
    """
    record = {
        "iteration": iteration,
        "model": model,
        "latency_ms": latency_ms,
        "usage": (response.get("usage") or {}) if isinstance(response, dict) else {},
    }
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        _log("usage-log write failed (%s); continuing" % e)


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
        elif proc.returncode in GATE_INAPPLICABLE.get(label, set()):
            lines.append("%s: skipped (inapplicable, exit %d)" % (label, proc.returncode))
        else:
            ok = False
            detail = (proc.stdout + proc.stderr).strip()
            lines.append("%s: FAILED (exit %d)\n%s" % (label, proc.returncode, detail[:2000]))
    return ok, "\n".join(lines)


def _tool_msg(call, content):
    return {"role": "tool", "tool_call_id": call.get("id", ""), "content": str(content)}


def _active_task(root):
    """Read the active lane's task_id from .openup/state.json under root (or None)."""
    p = Path(root) / ".openup" / "state.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("task_id")
    except (json.JSONDecodeError, OSError):
        return None


def _prompt_tty(question, options):
    """Default interactive prompt: ask on the TTY, return a line of input."""
    sys.stderr.write("\n[openup-agent] the procedure needs your input:\n  %s\n" % question)
    if options:
        for i, opt in enumerate(options, 1):
            sys.stderr.write("    %d) %s\n" % (i, opt))
    sys.stderr.flush()
    try:
        return input("answer> ").strip()
    except EOFError:
        return ""


def _create_request(root, task_id, question, options):
    """Create an input-request (+ suspend the lane) via the deterministic
    openup-input.py creator. Returns the request path, or an error string."""
    argv = ["python3", "scripts/openup-input.py", "request", "--root", str(root),
            "--title", (question[:60] or "Question"), "--question", question, "--json"]
    if task_id:
        argv += ["--task-id", task_id]
    for opt in options or []:
        argv += ["--option", opt]
    proc = subprocess.run(argv, cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        return "(request creation failed: %s)" % (proc.stderr or proc.stdout)[:300]
    try:
        return json.loads(proc.stdout)["request"]
    except (json.JSONDecodeError, KeyError):
        return proc.stdout.strip()


def _dispatch_tool_calls(tool_impl, tool_calls, interactive, root, task_id, ask):
    """Run each tool call. Returns (messages, suspend_request_or_None).

    `ask_user` is intercepted here (not dispatched through Tools): interactive
    mode returns the human's answer as the tool result; async mode creates an
    input-request, suspends the lane, and signals the loop to stop by returning
    the request path as the second element.
    """
    results = []
    for call in tool_calls:
        fn = call.get("function", {})
        name = fn.get("name", "")
        raw_args = fn.get("arguments", "") or "{}"
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError as e:
            results.append(_tool_msg(call, "ERROR: could not parse arguments for %s: %s" % (name, e)))
            continue

        if name == "ask_user":
            question = args.get("question", "")
            options = args.get("options")
            if interactive:
                answer = ask(question, options)
                _log("ask_user (interactive) -> %d chars" % len(answer or ""))
                results.append(_tool_msg(call, "User answered: %s" % answer))
                continue
            request = _create_request(root, task_id, question, options)
            _log("ask_user (async) -> suspended into %s" % request)
            results.append(_tool_msg(call, "SUSPENDED: created input-request %s" % request))
            return results, request

        result = tool_impl.dispatch(name, args)
        _log("tool %s -> %d chars" % (name, len(str(result))))
        results.append(_tool_msg(call, result))
    return results, None


def run(dir, procedure, max_iterations=DEFAULT_MAX_ITERATIONS, env=None,
        interactive=False, instruction=None, _completion=None, _ask=None,
        system_prompt=None, model=None):
    """Drive `procedure` under `dir`. Return an int exit code.

    `interactive` makes `ask_user` prompt on the TTY and wait; otherwise a human
    question suspends the run into an input-request (exit 5). `instruction`, when
    given, is extra task context appended to the initial user message (e.g. the
    stakeholder brief to read for a vision run). `_completion` and `_ask` are test
    seams replacing the live LLM call and the TTY prompt.

    `system_prompt` + `model` (T-089, both additive): when `system_prompt` is
    given, the procedure-file load and its tier resolution are skipped —
    `procedure` serves only as a log label and `model` MUST be supplied. This
    is the cycle engine's step-scoped sub-run hook; absent ⇒ unchanged behavior.
    """
    env = os.environ if env is None else env
    root = Path(dir).resolve()
    ask = _ask or _prompt_tty
    task_id = _active_task(root)

    try:
        api_url, api_key = _env_config(env)
        if system_prompt is None:
            proc_path = tiers.procedure_path(root, procedure)
            if not proc_path.exists():
                raise ConfigError("procedure not found: %s" % proc_path)
            procedure_text = proc_path.read_text(encoding="utf-8")
            model = tiers.resolve_model(root, procedure, target="driver", env=env)
            system_text = _system_prompt(root, procedure, procedure_text)
        else:
            if model is None:
                raise ConfigError("system_prompt override requires an explicit model")
            system_text = system_prompt
    except (ConfigError, tiers.TierError) as e:
        _log("FATAL: %s" % e)
        return 2

    _log("procedure=%s model=%s endpoint=%s dir=%s"
         % (procedure, model, llm.completions_url(api_url), root))

    tool_impl = tools.Tools(root)
    user_msg = "Execute the procedure now."
    if instruction:
        user_msg += "\n\nTask context:\n" + instruction
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_msg},
    ]

    usage_log = env.get("OPENUP_AGENT_USAGE_LOG")
    try:
        req_timeout = int(env.get("OPENUP_AGENT_TIMEOUT", "600"))
    except ValueError:
        req_timeout = 600

    def complete(msgs):
        if _completion is not None:
            return _completion(model, msgs, tools.TOOL_DEFS)
        return llm.chat_completion(api_url, api_key, model, msgs,
                                   tools=tools.TOOL_DEFS, timeout=req_timeout)

    for i in range(1, max_iterations + 1):
        try:
            _t0 = time.monotonic()
            response = complete(messages)
            if usage_log:
                _append_usage(usage_log, i, model,
                              int((time.monotonic() - _t0) * 1000), response)
            message = llm.first_message(response)
        except llm.LLMError as e:
            _log("FATAL: endpoint error on iteration %d: %s" % (i, e))
            return 3

        tool_calls = message.get("tool_calls") or []
        messages.append(message)

        if tool_calls:
            tool_msgs, suspend = _dispatch_tool_calls(
                tool_impl, tool_calls, interactive, root, task_id, ask)
            messages.extend(tool_msgs)
            if suspend is not None:
                _log("procedure suspended on iteration %d awaiting human input" % i)
                print("%s — %s" % (SUSPEND_SENTINEL, suspend))
                return EXIT_SUSPEND
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

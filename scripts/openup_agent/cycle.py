"""Deterministic cycle engine — pick/resume + Operations-step executor (T-089).

Inverts the reference driver's control (exploration 2026-07-13): one
``run_cycle()`` call runs ONE delivery cycle as a deterministic state machine
over the *existing* scripts — ``openup-board.py resolve`` → ``openup-session.py
begin`` → per-Operations-box executor → gates → deterministic completion —
dropping to the LLM only at genuine judgment points, each as a fresh, bounded,
step-scoped ``loop.run()`` sub-run. Ceremony is code; the LLM only authors.

The engine COMPOSES the process scripts as subprocesses under ``--dir`` and
never reimplements their logic (board decisions, claims, state, views, gates
all stay single-sourced). All inter-step state lives in the repo (Operations
checkboxes, ``.openup/state.json``, the lease), so a killed cycle resumes at
the first unchecked box for free.

Step classification (spec assumption, T-089 plan.md):
  * an explicit ``(auto)`` marker forces script execution; ``(judgment)``
    forces an LLM sub-run;
  * otherwise a box that carries an extractable ``git …`` / ``python3 …``
    command (backtick-quoted, or from the first such token to end of line) is
    a script-step; a bare ``scripts/<name>.py`` backtick span is run via
    ``python3``;
  * everything else is a judgment sub-run.
Keep script-step boxes command-only — trailing prose after an unquoted command
becomes part of the command line.

Exit codes (superset of loop.run's, so an outer harness can type them):
    0  cycle completed; sentinel on stdout (OPENUP-NEXT: ADVANCED/DONE)
    2  configuration error (no board decision, missing plan, env/tier)
    3  endpoint/transport error inside a judgment sub-run
    4  a judgment sub-run hit its iteration cap with no clean sentinel
    5  suspended awaiting a human answer (sub-run ask_user); sentinel on stdout
    6  a deterministic gate (fence / check-docs) failed after a step
    7  decision path not supported by this engine slice (T-090/T-091)
    8  a script-step / session-ceremony command failed

Stdlib-only.
"""

import contextlib
import io
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import loop, tiers

EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_ENDPOINT = 3
EXIT_MAX_ITERATIONS = 4
EXIT_SUSPEND = 5
EXIT_GATE = 6
EXIT_UNSUPPORTED = 7
EXIT_STEP = 8

DEFAULT_STEP_MAX_ITERATIONS = 10
DEFAULT_STEP_TIER = "authoring"

# Decision paths this slice does NOT run, and the roadmap task that will.
UNSUPPORTED_PATHS = {
    "plan-iteration": "T-090",
    "assess-iteration": "T-091",
    "milestone-review": "T-091",
}

BOX_RE = re.compile(r"^- \[( |x)\] (.*\S)\s*$")
HAT_RE = re.compile(r"^\(([a-z][a-z-]*)\)\s+")
MARKER_RE = re.compile(r"^\((auto|judgment)\)\s+")
CMD_START_RE = re.compile(r"(?:python3|git)\s\S.*$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
OPERATIONS_HEADING_RE = re.compile(r"^##\s+Operations\s*$")
HEADING_RE = re.compile(r"^##\s+")

STEP_SENTINEL_HINT = "OPENUP-STEP: DONE"

STEP_SYSTEM_PROMPT = """\
You are an OpenUP delivery agent completing ONE step of one task. Use ONLY the
provided tools (read_file, write_file, edit_file, glob, grep, exec). exec runs
`git ...` and `python3 scripts/*.py ...` only.
Working directory (all paths are relative to it): %(root)s

The deterministic ceremony around you — picking the lane, session state,
ticking Operations checkboxes, gates, completion, commits — is run by the cycle
engine, NOT by you. Do not tick checkboxes, do not run session/completion
scripts, do not start any other step. Do exactly the one step you are given and
persist its output to files in the repository.

When the step's work is saved, reply with NO tool calls and put this sentinel
line last: `%(sentinel)s — <one-line summary>`.
"""


class CycleError(Exception):
    """Unrecoverable engine-side failure (configuration / composition)."""


def _log(msg):
    sys.stderr.write("[openup-cycle] %s\n" % msg)
    sys.stderr.flush()


def _utc_today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _run(argv, root, check=False):
    """Run one composed command under root; return CompletedProcess."""
    proc = subprocess.run(argv, cwd=str(root), text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise CycleError(
            "command failed (exit %d): %s\n%s"
            % (proc.returncode, " ".join(argv),
               (proc.stdout + proc.stderr).strip()[:2000])
        )
    return proc


def _git(args, root, check=False):
    return _run(["git"] + args, root, check=check)


# --------------------------------------------------------------------------
# Repo readers (deliberately tiny — the scripts stay the source of truth)
# --------------------------------------------------------------------------
def read_frontmatter(path):
    """Minimal single-level frontmatter reader (id/title/status/track/...).

    Only scalar ``key: value`` lines are read — enough for the engine's needs
    (id, title, status, track). Lists and nesting are the scripts' business.
    """
    fm = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return fm
    if not text.startswith("---"):
        return fm
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if m and m.group(2).strip():
            fm[m.group(1)] = m.group(2).split("#", 1)[0].strip().strip("\"'")
    return fm


def read_state(root):
    p = Path(root) / ".openup" / "state.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_iteration_number(root):
    """Next iteration ordinal from docs/project-status.md (fallback 1)."""
    p = Path(root) / "docs" / "project-status.md"
    try:
        m = re.search(r"^\*\*Iteration\*\*:\s*(\d+)", p.read_text(encoding="utf-8"), re.M)
        return int(m.group(1)) + 1 if m else 1
    except OSError:
        return 1


# --------------------------------------------------------------------------
# Decision (openup-board.py resolve — composed, never reimplemented)
# --------------------------------------------------------------------------
def resolve_decision(root):
    proc = _run(["python3", "scripts/openup-board.py", "resolve"], root)
    if proc.returncode != 0:
        raise CycleError("openup-board.py resolve failed: %s"
                         % (proc.stdout + proc.stderr).strip()[:1000])
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise CycleError("unparseable resolve output: %s" % e)


# --------------------------------------------------------------------------
# Operations boxes — parse / classify / tick
# --------------------------------------------------------------------------
def parse_boxes(plan_text):
    """All Operations checkboxes, in order.

    Returns a list of ``{raw, checked, hat, marker, body}`` where ``raw`` is
    the exact line (for ticking), ``hat`` the ``(role)`` tag (default
    ``developer``), ``marker`` an explicit ``(auto)``/``(judgment)`` override
    or None, and ``body`` the step text with hat + marker stripped.
    """
    boxes, in_ops = [], False
    for line in plan_text.splitlines():
        if OPERATIONS_HEADING_RE.match(line):
            in_ops = True
            continue
        if in_ops and HEADING_RE.match(line):
            break
        if not in_ops:
            continue
        m = BOX_RE.match(line)
        if not m:
            # continuation lines of a wrapped box are context, not new steps
            continue
        checked, text = m.group(1) == "x", m.group(2)
        hat = "developer"
        marker = None
        hm = HAT_RE.match(text)
        if hm and hm.group(1) in ("auto", "judgment"):
            marker, text = hm.group(1), text[hm.end():]
        elif hm:
            hat, text = hm.group(1), text[hm.end():]
        if marker is None:
            mm = MARKER_RE.match(text)
            if mm:
                marker, text = mm.group(1), text[mm.end():]
        boxes.append({"raw": line, "checked": checked, "hat": hat,
                      "marker": marker, "body": text.strip()})
    return boxes


def extract_command(body):
    """The script command a box carries, or None (⇒ judgment step)."""
    for span in BACKTICK_RE.findall(body):
        span = span.strip()
        if span.startswith(("python3 ", "git ")):
            return span
        if re.match(r"^scripts/[\w./-]+\.py(\s|$)", span):
            return "python3 " + span
    m = CMD_START_RE.search(body)
    if m:
        return m.group(0).rstrip(" .`")
    return None


def classify_box(box):
    """Return ('script', command) or ('judgment', None) for one parsed box."""
    if box["marker"] == "judgment":
        return "judgment", None
    cmd = extract_command(box["body"])
    if box["marker"] == "auto":
        if cmd is None:
            raise CycleError("(auto) box has no extractable command: %s" % box["body"])
        return "script", cmd
    if cmd is not None:
        return "script", cmd
    return "judgment", None


def tick_box(plan_path, raw_line):
    """Flip one exact ``- [ ]`` line to ``- [x]`` (the sanctioned progress edit)."""
    plan_path = Path(plan_path)
    text = plan_path.read_text(encoding="utf-8")
    if raw_line not in text.splitlines():
        raise CycleError("box line no longer present in %s: %s" % (plan_path, raw_line))
    ticked = raw_line.replace("- [ ]", "- [x]", 1)
    plan_path.write_text(
        "\n".join(ticked if l == raw_line else l for l in text.splitlines())
        + ("\n" if text.endswith("\n") else ""),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------
# Acquire (branch + openup-session.py begin — composed)
# --------------------------------------------------------------------------
def _cycle_meta_path(root):
    return Path(root) / ".openup" / "cycle.json"


def _write_cycle_meta(root, data):
    p = _cycle_meta_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")


def read_cycle_meta(root):
    p = _cycle_meta_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _checkout_task_branch(root, branch):
    current = _git(["rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip()
    if current == branch:
        return current
    if _git(["rev-parse", "--verify", "--quiet", branch], root).returncode == 0:
        _git(["checkout", branch], root, check=True)
    else:
        _git(["checkout", "-b", branch], root, check=True)
    return current


def acquire(root, task, decision, env):
    """In-place task branch + one atomic session begin. Returns state dict."""
    plan = Path(root) / "docs" / "changes" / task / "plan.md"
    if not plan.exists():
        raise CycleError("no spec for %s at %s" % (task, plan))
    fm = read_frontmatter(plan)
    track = (decision.get("lane") or {}).get("track") or fm.get("track") or "standard"
    phase = decision.get("phase") or "construction"
    branch = "task/%s-cycle" % task
    base_branch = _checkout_task_branch(root, branch)
    _write_cycle_meta(root, {"task": task, "branch": branch,
                             "base_branch": base_branch})
    argv = [
        "python3", "scripts/openup-session.py", "begin",
        "--task-id", task,
        "--iteration", str(_read_iteration_number(root)),
        "--phase", str(phase),
        "--track", str(track),
        "--branch", branch,
        "--worktree", str(root),
        "--session-id", branch,
        "--goal", fm.get("title") or ("cycle-driven delivery of %s" % task),
        "--run-id", "cycle-%s" % _utc_today(),
    ]
    proc = _run(argv, root)
    if proc.returncode != 0:
        raise CycleError(
            "session begin refused (exit %d) for %s — resolve the "
            "dependency/collision/duplicate above.\n%s"
            % (proc.returncode, task, (proc.stdout + proc.stderr).strip()[:2000])
        )
    # the plan gate: the spec IS the persisted plan for a change-folder lane.
    _run(["python3", "scripts/openup-state.py", "set-gate", "plan_persisted",
          "docs/changes/%s/plan.md" % task], root)
    _log("acquired %s (track=%s, branch=%s)" % (task, track, branch))
    state = read_state(root)
    if state is None:
        raise CycleError("begin succeeded but .openup/state.json is unreadable")
    return state


# --------------------------------------------------------------------------
# Judgment sub-run (fresh, bounded loop.run — the measured cheap shape)
# --------------------------------------------------------------------------
def build_step_instruction(task, hat, body, resumable_input=None):
    lines = [
        "Task: %s. Role hat for this step: %s." % (task, hat),
        "",
        "THE ONE STEP TO COMPLETE NOW:",
        body,
        "",
        "Briefing (read before acting):",
        "- docs/changes/%s/plan.md — the task spec (requirements, safeguards)" % task,
        "- docs/changes/%s/design.md — in-flight decisions (if present)" % task,
        "- Ring-1 product docs under docs/product/ — consult what the step needs",
    ]
    if resumable_input:
        lines.append("- %s — the answered human input that resumed this lane"
                     % resumable_input)
    lines += [
        "",
        "Persist your output to files. Then emit `%s — <summary>`." % STEP_SENTINEL_HINT,
    ]
    return "\n".join(lines)


def run_judgment_step(root, task, box, env, step_tier, max_iterations,
                      interactive=False, resumable_input=None, _completion=None):
    """One fresh, bounded sub-run for one judgment box. Returns loop exit code."""
    model = tiers.resolve_tier_model(root, step_tier, target="driver", env=env)
    instruction = build_step_instruction(task, box["hat"], box["body"],
                                         resumable_input=resumable_input)
    _log("judgment step (%s, tier=%s, model=%s, cap=%d): %s"
         % (box["hat"], step_tier, model, max_iterations, box["body"][:80]))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = loop.run(
            dir=str(root),
            procedure="cycle-step",
            max_iterations=max_iterations,
            env=env,
            interactive=interactive,
            instruction=instruction,
            system_prompt=STEP_SYSTEM_PROMPT % {"root": root,
                                                "sentinel": STEP_SENTINEL_HINT},
            model=model,
            _completion=_completion,
        )
    out = buf.getvalue().strip()
    if out:
        _log("sub-run stdout: %s" % out[:200])
    if rc == EXIT_SUSPEND:
        # relay the sub-run's suspend sentinel on the ENGINE's stdout
        print(out.splitlines()[-1] if out else loop.SUSPEND_SENTINEL)
    return rc


# --------------------------------------------------------------------------
# Deterministic completion (mirrors /openup-complete-task's per-track ceremony)
# --------------------------------------------------------------------------
def _flip_plan_status(plan_path, new_status):
    text = plan_path.read_text(encoding="utf-8")
    flipped, done = [], False
    for line in text.splitlines():
        if not done and re.match(r"^status\s*:", line):
            comment = ""
            if "#" in line:
                comment = "   #" + line.split("#", 1)[1]
            flipped.append("status: %s%s" % (new_status, comment))
            done = True
        else:
            flipped.append(line)
    plan_path.write_text("\n".join(flipped) + ("\n" if text.endswith("\n") else ""),
                         encoding="utf-8")


def _write_status_note(root, task, fm, counts):
    notes_dir = Path(root) / "docs" / "status-notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note = notes_dir / ("%s-%s.md" % (_utc_today(), task))
    note.write_text(
        "**%s** (%s, %s): %s — delivered by the reference cycle engine "
        "(`openup-agent.py cycle`): ceremony ran as code; %d script step(s) and "
        "%d judgment sub-run(s) executed, gates green.\n"
        % (task, _utc_today(), fm.get("track") or "standard",
           fm.get("title") or task, counts["script"], counts["judgment"]),
        encoding="utf-8",
    )


def complete(root, task, env, counts):
    """All boxes ticked → close the lane deterministically, sentinel, exit 0."""
    root = Path(root)
    plan = root / "docs" / "changes" / task / "plan.md"
    fm = read_frontmatter(plan)
    # 1. spec status → done (dependency resolution reads this frontmatter);
    #    `verified` stays reserved for rubric-graded full-track completions.
    _flip_plan_status(plan, "done")
    # 2. lane-owned completion shard (sync-status assembles the Notes view).
    _write_status_note(root, task, fm, counts)
    # 3. traceability log + the log_written gate sync-status requires.
    _run(["python3", "scripts/openup-state.py", "log-event",
          "--event", "task_completed", "--task-id", task], root)
    _run(["python3", "scripts/openup-state.py", "set-gate",
          "log_written", "true"], root, check=True)
    # 4. regenerate the derived shared views (never hand-edited).
    _run(["python3", "scripts/sync-status.py"], root, check=True)
    # 5. final deterministic gates before anything irreversible.
    ok, report = loop.run_gates(root)
    if not ok:
        _log("completion gates FAILED:\n%s" % report)
        return EXIT_GATE
    # 6. retro cadence counter (durable; fail-open like the skill).
    _run(["python3", "scripts/openup-state.py", "retro", "increment"], root)
    # 7. atomic teardown: archive state INTO the change folder, log, release.
    _run(["python3", "scripts/openup-session.py", "end",
          "--task-id", task,
          "--archive-to", "docs/changes/%s/state.json" % task], root, check=True)
    # 8. archive the change folder (Ring 2 → archive ring).
    (root / "docs" / "changes" / "archive").mkdir(parents=True, exist_ok=True)
    _git(["mv", "docs/changes/%s" % task, "docs/changes/archive/%s" % task],
         root, check=True)
    # 9. one completion commit carrying the lane's whole delivery.
    _git(["add", "-A"], root, check=True)
    _git(["commit", "-m",
          "chore(%s): complete lane via cycle engine [%s]" % (task, task)],
         root, check=True)
    # 10. merge the task branch back where the cycle started (no-remote world;
    #     PR ceremony belongs to harnesses that have one).
    meta = read_cycle_meta(root)
    base = meta.get("base_branch")
    branch = meta.get("branch")
    if base and branch and base != branch:
        _git(["checkout", base], root, check=True)
        merge = _git(["merge", "--no-ff", branch, "-m",
                      "merge %s: %s [%s]" % (branch, fm.get("title") or task, task)],
                     root)
        if merge.returncode != 0:
            _log("merge back to %s failed — task branch %s holds the completed "
                 "lane:\n%s" % (base, branch, (merge.stdout + merge.stderr)[:1000]))
            return EXIT_STEP
    print("OPENUP-NEXT: ADVANCED — %s" % task)
    return EXIT_OK


# --------------------------------------------------------------------------
# The cycle
# --------------------------------------------------------------------------
def run_cycle(dir, env=None, step_max_iterations=DEFAULT_STEP_MAX_ITERATIONS,
              step_tier=DEFAULT_STEP_TIER, interactive=False,
              _completion=None, _subrun=None):
    """Run ONE delivery cycle under ``dir``. Returns an int exit code.

    ``_completion`` is loop.run's scripted-LLM test seam, passed through to
    every judgment sub-run; ``_subrun`` replaces the whole judgment-step call
    (signature: fn(task, box, instruction) -> int) for engine-level tests.
    """
    import os
    env = os.environ if env is None else env
    root = Path(dir).resolve()

    try:
        decision = resolve_decision(root)
    except CycleError as e:
        _log("FATAL: %s" % e)
        return EXIT_CONFIG

    path = decision.get("path")
    reason = decision.get("reason") or ""
    _log("decision: path=%s — %s" % (path, reason))

    if path == "noop":
        print("OPENUP-NEXT: DONE — %s" % (reason or "nothing to do"))
        return EXIT_OK
    if path in UNSUPPORTED_PATHS:
        _log("FATAL: decision path '%s' is not supported by the cycle engine "
             "core — it lands with %s. Use the `next` procedure (or the Claude "
             "Code skills) for this path meanwhile." % (path, UNSUPPORTED_PATHS[path]))
        return EXIT_UNSUPPORTED
    if path not in ("pick", "resume"):
        _log("FATAL: unknown decision path '%s'" % path)
        return EXIT_CONFIG

    task = (decision.get("lane") or {}).get("task")
    if not task:
        _log("FATAL: decision carried no lane task")
        return EXIT_CONFIG
    resumable_input = (decision.get("resumable_input") or {}).get("request")

    state = read_state(root)
    try:
        if state and state.get("task_id") == task:
            _log("resuming %s (state present)" % task)
            meta = read_cycle_meta(root)
            if meta.get("task") == task and meta.get("branch"):
                _checkout_task_branch(root, meta["branch"])
        else:
            acquire(root, task, decision, env)
    except CycleError as e:
        _log("FATAL: %s" % e)
        return EXIT_STEP

    plan = root / "docs" / "changes" / task / "plan.md"
    counts = {"script": 0, "judgment": 0}

    while True:
        try:
            boxes = parse_boxes(plan.read_text(encoding="utf-8"))
        except OSError as e:
            _log("FATAL: cannot read %s: %s" % (plan, e))
            return EXIT_CONFIG
        pending = [b for b in boxes if not b["checked"]]
        if not boxes:
            _log("FATAL: %s has no Operations checkboxes — nothing the engine "
                 "can execute" % plan)
            return EXIT_CONFIG
        if not pending:
            break
        box = pending[0]

        try:
            kind, command = classify_box(box)
        except CycleError as e:
            _log("FATAL: %s" % e)
            return EXIT_STEP

        if kind == "script":
            counts["script"] += 1
            _log("script step: %s" % command)
            try:
                argv = shlex.split(command)
            except ValueError as e:
                _log("FATAL: unparseable command %r: %s" % (command, e))
                return EXIT_STEP
            proc = _run(argv, root)
            if proc.returncode != 0:
                _log("script step FAILED (exit %d): %s\n%s"
                     % (proc.returncode, command,
                        (proc.stdout + proc.stderr).strip()[:2000]))
                return EXIT_STEP
        else:
            counts["judgment"] += 1
            if _subrun is not None:
                instruction = build_step_instruction(
                    task, box["hat"], box["body"], resumable_input=resumable_input)
                rc = _subrun(task, box, instruction)
            else:
                try:
                    rc = run_judgment_step(
                        root, task, box, env, step_tier, step_max_iterations,
                        interactive=interactive, resumable_input=resumable_input,
                        _completion=_completion)
                except tiers.TierError as e:
                    _log("FATAL: %s" % e)
                    return EXIT_CONFIG
            if rc == EXIT_SUSPEND:
                _log("cycle suspended awaiting human input (box left unticked)")
                return EXIT_SUSPEND
            if rc != 0:
                _log("judgment step failed (exit %d); box left unticked" % rc)
                return rc if rc in (EXIT_CONFIG, EXIT_ENDPOINT,
                                    EXIT_MAX_ITERATIONS) else EXIT_STEP

        # gates BEFORE the tick: a failed gate leaves the box unchecked so a
        # resumed cycle retries the step (spec Req 4).
        ok, report = loop.run_gates(root)
        if not ok:
            _log("gates FAILED after step; box left unticked:\n%s" % report)
            return EXIT_GATE
        try:
            tick_box(plan, box["raw"])
        except CycleError as e:
            _log("FATAL: %s" % e)
            return EXIT_STEP
        _log("ticked: %s" % box["body"][:80])

    try:
        return complete(root, task, env, counts)
    except CycleError as e:
        _log("FATAL: completion failed — %s" % e)
        return EXIT_STEP

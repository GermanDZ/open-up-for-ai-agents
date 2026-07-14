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

Recovery mode (T-092, default on; ``--no-recover`` opts out): when the engine
cannot proceed deterministically it rebuilds the repo state that blocks it,
then continues the SAME cycle —
  * **unclosed-lane reconcile** (zero LLM): on a ``plan-iteration``/``noop``
    decision, an *active* ``docs/changes/<id>/`` whose plan status is already
    satisfied (``done``/``verified``) is closed first — archived, committed,
    views resynced (fail-open), and merged to the trunk when the work sits on
    a side branch — so the loop never plans new work atop an unfinished
    delivery;
  * **missing-spec recovery** (one bounded sub-run): a persisting
    ``plan-iteration`` decision already names the next work item, so an
    ``analyst``-hat sub-run authors its ``plan.md`` (spec contract in the
    instruction), the spec is gated (``check-docs`` + ``openup-spec-scenarios``
    when present) and committed, and the re-resolved ``pick`` runs in the same
    invocation;
  * **consent-gated replenishment** (T-094): when nothing is promotable at all
    (roadmap present but exhausted/blocked mid-phase), the engine ASKS first —
    a TTY prompt under ``--interactive``, else an input-request + suspend
    (exit 5). An answered ``yes`` runs ONE ``product-manager``-hat sub-run
    that appends 1-5 pending roadmap entries (accepted only if
    ``openup-roadmap.py next`` then finds one promotable), committed
    ``[openup-skip]``, and the same invocation continues; ``no`` is remembered
    and ends the cycle cleanly. The LLM proposes, the human consents — scope
    is never invented silently.
    One round per case; a decision that does not advance exits 7 as before.

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

from . import assess, loop, plan_iteration, stamping, tiers

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
# Decision paths the engine still cannot advance on its own. assess-iteration and
# milestone-review are handled (T-091); plan-iteration is handled under recovery
# (T-090/T-092), so it only lands here under --no-recover.
UNSUPPORTED_PATHS = {
    "plan-iteration": "T-090 (only reachable here under --no-recover)",
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
                      interactive=False, resumable_input=None, _completion=None,
                      instruction=None):
    """One fresh, bounded sub-run for one judgment box. Returns loop exit code.

    ``instruction`` (T-094) overrides the default change-folder briefing — used
    by steps that belong to no lane (the replenishment pass)."""
    model = tiers.resolve_tier_model(root, step_tier, target="driver", env=env)
    instruction = instruction or build_step_instruction(
        task, box["hat"], box["body"], resumable_input=resumable_input)
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


def _dispatch_judgment(root, task, box, env, step_tier, cap, interactive,
                       resumable_input, _completion, _subrun, instruction=None):
    """One judgment step through the seam or the live sub-run (shared by the
    executor and recovery). Returns the loop exit code; raises TierError.
    ``instruction`` overrides the default change-folder briefing (T-094)."""
    if _subrun is not None:
        instruction = instruction or build_step_instruction(
            task, box["hat"], box["body"], resumable_input=resumable_input)
        return _subrun(task, box, instruction)
    return run_judgment_step(root, task, box, env, step_tier, cap,
                             interactive=interactive,
                             resumable_input=resumable_input,
                             _completion=_completion, instruction=instruction)


# --------------------------------------------------------------------------
# Recovery (T-092): rebuild the repo state that blocks the loop, then continue
# --------------------------------------------------------------------------
SATISFIED_STATUSES = {"done", "verified"}

SPEC_CONTRACT = """\
Author the task spec at docs/changes/%(task)s/plan.md for the roadmap work \
item %(task)s%(title)s. Read its docs/roadmap.md entry and the Ring-1 product \
docs (docs/vision.md, docs/product/) first. The spec file MUST carry:
- YAML frontmatter: id: %(task)s, title, status: ready, priority, \
track (quick|standard), touches (the file paths the task will change), \
depends-on
- ## Requirements — numbered assertions, each with at least one acceptance \
scenario using the bold markers **Given** / **When** / **Then**
- ## Operations — 1-8 unchecked checkbox steps (`- [ ] ...`), ordered. A step \
that is a command must be command-only (e.g. `- [ ] python3 scripts/x.py ...`); \
prose steps are judgment work; tag a step `(role)` only when it changes hats.
Author ONLY the spec file — do not begin the work itself."""


def _detect_trunk(root):
    p = _git(["symbolic-ref", "refs/remotes/origin/HEAD"], root)
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip().rsplit("/", 1)[-1]
    for cand in ("main", "master"):
        if _git(["rev-parse", "--verify", "--quiet", cand], root).returncode == 0:
            return cand
    return None


def unclosed_lanes(root):
    """Active docs/changes/<id>/ folders whose plan status is already
    satisfied — delivered work whose closure ceremony never ran."""
    changes = Path(root) / "docs" / "changes"
    out = []
    for plan in sorted(changes.glob("*/plan.md")):
        if plan.parent.name == "archive":
            continue
        fm = read_frontmatter(plan)
        if (fm.get("status") or "").lower() in SATISFIED_STATUSES:
            out.append(plan.parent.name)
    return out


def reconcile_unclosed_lanes(root):
    """Case B: close every done-but-unclosed lane deterministically (zero LLM).

    Archive each folder, commit, resync views (fail-open), and merge the
    current branch into the trunk when the delivered work sits on a side
    branch. Returns True when anything was closed (caller re-resolves).
    Raises CycleError on a failed ceremony command (incl. a merge conflict).
    """
    root = Path(root)
    lanes = unclosed_lanes(root)
    if not lanes:
        return False
    if _git(["status", "--porcelain"], root).stdout.strip():
        _log("recovery: %d done-but-unclosed lane(s) found but the working "
             "tree is dirty — skipping closure (commit or stash first)"
             % len(lanes))
        return False
    _log("recovery: closing done-but-unclosed lane(s): %s" % ", ".join(lanes))
    (root / "docs" / "changes" / "archive").mkdir(parents=True, exist_ok=True)
    for task in lanes:
        _git(["mv", "docs/changes/%s" % task, "docs/changes/archive/%s" % task],
             root, check=True)
    sync = _run(["python3", "scripts/sync-status.py"], root)
    if sync.returncode != 0:
        _log("sync-status.py failed (exit %d) — views not regenerated:\n%s"
             % (sync.returncode, (sync.stdout + sync.stderr).strip()[:800]))
    _git(["add", "-A"], root, check=True)
    _git(["commit", "-m",
          "chore(%s): recovery — close done-but-unclosed lane(s) %s [%s]"
          % (lanes[0], ", ".join(lanes), lanes[0])], root, check=True)
    trunk = _detect_trunk(root)
    current = _git(["rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip()
    if trunk and current != trunk:
        _git(["checkout", trunk], root, check=True)
        merge = _git(["merge", "--no-ff", current, "-m",
                      "chore(%s): recovery — merge unfinished delivery from "
                      "%s [%s]" % (lanes[0], current, lanes[0])], root)
        if merge.returncode != 0:
            raise CycleError(
                "recovery merge of %s into %s failed — resolve it by hand "
                "(branch left intact):\n%s"
                % (current, trunk, (merge.stdout + merge.stderr).strip()[:1000]))
    return True


def recover_missing_spec(root, decision, env, step_tier, cap, interactive,
                         _completion, _subrun):
    """Case A: author the plan-iteration decision's named work item's spec via
    ONE bounded analyst sub-run, gate it, commit it. Returns EXIT_OK when the
    spec landed (caller re-resolves once); any other code aborts the cycle."""
    root = Path(root)
    lane = decision.get("lane") or {}
    task = lane.get("task")
    if not task:
        _log("recovery: plan-iteration decision carries no work item — "
             "nothing to author")
        return EXIT_UNSUPPORTED
    plan = root / "docs" / "changes" / task / "plan.md"
    if plan.exists():
        _log("recovery: %s already has a spec but is not pickable "
             "(dependency/collision/suspension?) — not re-authoring" % task)
        return EXIT_UNSUPPORTED
    title = lane.get("title")
    box = {"hat": "analyst", "marker": None,
           "body": SPEC_CONTRACT % {"task": task,
                                    "title": (" — %s" % title) if title else ""}}
    _log("recovery: authoring missing spec for %s via one bounded sub-run" % task)
    try:
        rc = _dispatch_judgment(root, task, box, env, step_tier, cap,
                                interactive, None, _completion, _subrun)
    except tiers.TierError as e:
        _log("FATAL: %s" % e)
        return EXIT_CONFIG
    if rc == EXIT_SUSPEND:
        _log("recovery: spec authoring suspended awaiting human input")
        return EXIT_SUSPEND
    if rc != 0:
        _log("recovery: spec-authoring sub-run failed (exit %d)" % rc)
        return rc if rc in (EXIT_CONFIG, EXIT_ENDPOINT,
                            EXIT_MAX_ITERATIONS) else EXIT_STEP
    if not plan.exists():
        _log("recovery: sub-run finished but produced no %s" % plan)
        return EXIT_STEP
    scenarios = root / "scripts" / "openup-spec-scenarios.py"
    if scenarios.exists():
        check = _run(["python3", "scripts/openup-spec-scenarios.py", "check",
                      "docs/changes/%s/plan.md" % task], root)
        if check.returncode != 0:
            _log("recovery: authored spec fails scenario validation:\n%s"
                 % (check.stdout + check.stderr).strip()[:800])
            return EXIT_STEP
    docs_gate = _run(["python3", "scripts/check-docs.py"], root) \
        if (root / "scripts" / "check-docs.py").exists() else None
    if docs_gate is not None and docs_gate.returncode != 0:
        _log("recovery: authored spec fails check-docs:\n%s"
             % (docs_gate.stdout + docs_gate.stderr).strip()[:800])
        return EXIT_STEP
    try:
        _git(["add", "docs/changes/%s" % task], root, check=True)
        _git(["commit", "-m",
              "docs(%s): author spec via cycle recovery [%s]" % (task, task)],
             root, check=True)
    except CycleError as e:
        _log("FATAL: %s" % e)
        return EXIT_STEP
    _log("recovery: spec for %s authored, gated, committed" % task)
    return EXIT_OK


# --------------------------------------------------------------------------
# Consent-gated replenishment (T-094): ask the human, then let the PM propose
# --------------------------------------------------------------------------
REPLENISH_QUESTION = (
    "The cycle loop is stuck: docs/roadmap.md has no promotable entry and the "
    "phase is not complete. Approve ONE bounded LLM product-manager pass to "
    "propose the next 1-5 roadmap entries (pending, human-editable)?")

REPLENISH_CONTRACT = """\
The delivery loop is stuck: docs/roadmap.md has no promotable entry, but the \
phase is not complete. A human has APPROVED one product-manager planning pass.
Act as the product manager. Read docs/vision.md, docs/roadmap.md, \
docs/project-status.md, and the risk list (docs/risk-list.md or \
docs/product/risk-list.md) if present.
Append 1-5 NEW pending entries to docs/roadmap.md — the next most valuable \
work toward the vision:
- match the file's existing entry shape (table rows or `## T-NNN:` sections)
- reserve each new id first: exec `python3 scripts/openup-claims.py \
reserve-id --session-id replenish` and use the printed id
- every entry carries status pending, a priority, its dependencies, and a \
one-line **Value** rationale
- do NOT modify, reorder, or restate existing entries or their Status cells
Only edit docs/roadmap.md. Do not create change folders and do not start the \
work itself."""


def _ask_tty(question):
    sys.stderr.write("\n[openup-cycle] %s\n" % question)
    sys.stderr.flush()
    try:
        return input("approve? (yes/no)> ").strip()
    except EOFError:
        return ""


def _update_replenish_meta(root, **fields):
    meta = read_cycle_meta(root)
    rep = dict(meta.get("replenish") or {})
    rep.update(fields)
    meta["replenish"] = rep
    _write_cycle_meta(root, meta)


def _request_answer(root, rel_path):
    """(state, answer) for a recorded request: state ∈ {missing, pending,
    answered}; answer is the normalized yes/no text when answered (or None
    while unparseable — treated as still pending by the caller)."""
    path = Path(root) / rel_path
    if not path.exists():
        return "missing", None
    fm = read_frontmatter(path)
    if (fm.get("status") or "").strip().lower() != "answered":
        return "pending", None
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^- \[x\] `([^`]+)`", text, re.M)          # ticked option
    if not m:
        m = re.search(r"\*\*Answer\*\*:\s*(?!_)`?([A-Za-z]+)`?", text)
    if not m:
        return "answered", None
    ans = m.group(1).strip().lower()
    if ans.startswith("y"):
        return "answered", "yes"
    if ans.startswith("n"):
        return "answered", "no"
    return "answered", None


def _create_replenish_request(root):
    proc = _run(["python3", "scripts/openup-input.py", "request",
                 "--title", "Approve LLM roadmap replenishment",
                 "--question", REPLENISH_QUESTION,
                 "--option", "yes", "--option", "no", "--json"], root)
    if proc.returncode != 0:
        raise CycleError("could not create the replenishment input-request:\n%s"
                         % (proc.stdout + proc.stderr).strip()[:800])
    try:
        return json.loads(proc.stdout)["request"]
    except (json.JSONDecodeError, KeyError):
        return proc.stdout.strip().splitlines()[-1]


def _run_replenishment(root, env, step_tier, cap, interactive,
                       _completion, _subrun):
    """The approved PM pass + deterministic acceptance. EXIT_OK on success."""
    box = {"hat": "product-manager", "marker": None, "body": REPLENISH_CONTRACT}
    _log("recovery: running the approved product-manager replenishment pass")
    try:
        rc = _dispatch_judgment(root, "replenish", box, env, step_tier, cap,
                                interactive, None, _completion, _subrun,
                                instruction=REPLENISH_CONTRACT)
    except tiers.TierError as e:
        _log("FATAL: %s" % e)
        return EXIT_CONFIG
    if rc == EXIT_SUSPEND:
        return EXIT_SUSPEND
    if rc != 0:
        _log("recovery: replenishment sub-run failed (exit %d)" % rc)
        return rc if rc in (EXIT_CONFIG, EXIT_ENDPOINT,
                            EXIT_MAX_ITERATIONS) else EXIT_STEP
    # Deterministic acceptance: the roadmap must now be promotable.
    nxt = _run(["python3", "scripts/openup-roadmap.py", "next",
                "--no-remote-check"], root)
    if nxt.returncode != 0:
        _log("recovery: replenishment did not produce a promotable roadmap "
             "entry (openup-roadmap.py next exit %d) — nothing committed:\n%s"
             % (nxt.returncode, (nxt.stdout + nxt.stderr).strip()[:400]))
        return EXIT_STEP
    if (root / "scripts" / "check-docs.py").exists():
        docs = _run(["python3", "scripts/check-docs.py"], root)
        if docs.returncode != 0:
            _log("recovery: replenished roadmap fails check-docs — nothing "
                 "committed:\n%s" % (docs.stdout + docs.stderr).strip()[:400])
            return EXIT_STEP
    _git(["add", "docs/roadmap.md", "docs/input-requests"], root, check=True)
    _git(["commit", "-m",
          "docs(roadmap): replenish backlog via cycle recovery "
          "(human-approved) [openup-skip]"], root, check=True)
    _log("recovery: roadmap replenished and committed")
    return EXIT_OK


def replenish_flow(root, env, step_tier, cap, interactive,
                   _completion, _subrun, _ask):
    """The consent state machine. Returns None to proceed (approved and
    replenished — caller re-resolves), or a terminal exit code (sentinel
    already printed where one applies)."""
    root = Path(root)
    rep = read_cycle_meta(root).get("replenish") or {}

    if rep.get("consumed") and rep.get("answer") == "no":
        print("OPENUP-NEXT: DONE — replenishment declined by human (%s); "
              "nothing promotable" % rep.get("request", "earlier answer"))
        return EXIT_OK

    if rep.get("request") and not rep.get("consumed"):
        state, answer = _request_answer(root, rep["request"])
        if state == "pending" or (state == "answered" and answer is None):
            if state == "answered":
                _log("recovery: request answered but the answer is not a "
                     "clear yes/no — treating as still pending")
            print("%s — %s" % (loop.SUSPEND_SENTINEL, rep["request"]))
            return EXIT_SUSPEND
        if state == "answered" and answer == "no":
            _update_replenish_meta(root, consumed=True, answer="no")
            print("OPENUP-NEXT: DONE — replenishment declined by human (%s); "
                  "nothing promotable" % rep["request"])
            return EXIT_OK
        if state == "answered" and answer == "yes":
            _update_replenish_meta(root, consumed=True, answer="yes")
            rc = _run_replenishment(root, env, step_tier, cap, interactive,
                                    _completion, _subrun)
            return None if rc == EXIT_OK else rc
        # missing: the human removed the request — fall through and ask anew.
        _log("recovery: recorded request %s is gone — asking again"
             % rep["request"])

    if interactive:
        answer = (_ask or _ask_tty)(REPLENISH_QUESTION)
        if (answer or "").strip().lower().startswith("y"):
            rc = _run_replenishment(root, env, step_tier, cap, interactive,
                                    _completion, _subrun)
            return None if rc == EXIT_OK else rc
        print("OPENUP-NEXT: DONE — replenishment declined by human (tty); "
              "nothing promotable")
        return EXIT_OK

    try:
        request = _create_replenish_request(root)
    except CycleError as e:
        _log("FATAL: %s" % e)
        return EXIT_STEP
    _update_replenish_meta(root, request=request, consumed=False, answer=None)
    _log("recovery: loop stuck — awaiting human consent in %s" % request)
    print("%s — %s" % (loop.SUSPEND_SENTINEL, request))
    return EXIT_SUSPEND


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
    # 4. regenerate the derived shared views (never hand-edited). Fail-open: a
    #    freshly bootstrapped project may not carry the views yet (the driver's
    #    absent-gate spirit); the hard gates below stay blocking.
    sync = _run(["python3", "scripts/sync-status.py"], root)
    if sync.returncode != 0:
        _log("sync-status.py failed (exit %d) — views not regenerated:\n%s"
             % (sync.returncode, (sync.stdout + sync.stderr).strip()[:800]))
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

def _stamp_direct_artifact(root, procedure):
    """T-104: after a successful execution:direct authoring sub-run, stamp the
    typed instance frontmatter on the artifact the procedure produced — the
    model authored the body only. Runs before the gates, so check-docs (already
    in run_gates) validates the stamped result: the gate is the critic.
    Returns 0, or EXIT_STEP when stamping fails."""
    artifact = stamping.PROCEDURE_ARTIFACTS.get(procedure)
    if not artifact:
        return EXIT_OK
    type_, rel = artifact
    target = Path(root) / rel
    if not target.exists():
        return EXIT_OK
    try:
        info = stamping.stamp_file(root, target, type_)
        _log("stamped %s as %s (%s, status draft)" % (rel, info["id"], type_))
    except (ValueError, OSError) as e:
        _log("stamping %s failed: %s" % (rel, e))
        return EXIT_STEP
    return EXIT_OK


def _run_plan_iteration(root, phase, env, step_tier, cap, interactive,
                        _completion, _subrun):
    """Wire the real driver callables into plan_iteration.run_plan_iteration
    (T-090): the objectives sub-run, the per-lane spec sub-run (reusing
    _dispatch_judgment), gates, git-commit, and the deterministic script ops
    (mint/activities/reserve/partition/roadmap/lifecycle). Kept thin — the
    planning logic lives in plan_iteration.py."""
    root = Path(root)
    try:
        model = tiers.resolve_tier_model(root, step_tier, target="driver", env=env)
    except tiers.TierError as e:
        _log("FATAL: %s" % e)
        return EXIT_CONFIG

    def _runner(argv):
        p = _run(argv, root)
        return p.returncode, p.stdout

    def dispatch_objectives(instruction, system_prompt):
        _log("plan-iteration: objectives sub-run (tier=%s, model=%s)"
             % (step_tier, model))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = loop.run(dir=str(root), procedure="plan-objectives",
                          max_iterations=cap, env=env, interactive=interactive,
                          instruction=instruction, system_prompt=system_prompt,
                          model=model, _completion=_completion)
        out = buf.getvalue().strip()
        if rc == EXIT_SUSPEND and out:
            print(out.splitlines()[-1])
        return rc

    def dispatch_spec(lane_id, instruction):
        box = {"hat": "analyst", "marker": None, "body": instruction}
        try:
            return _dispatch_judgment(root, lane_id, box, env, step_tier, cap,
                                      interactive, None, _completion, _subrun,
                                      instruction=instruction)
        except tiers.TierError as e:
            _log("FATAL: %s" % e)
            return EXIT_CONFIG

    def git_commit(paths, message):
        _git(["add"] + list(paths), root, check=True)
        _git(["commit", "-m", message], root, check=True)

    def mint_id(ph):
        rc, out = _runner(["python3", "scripts/openup-process-map.py",
                           "mint-iteration-id", ph])
        return out.strip().splitlines()[-1] if rc == 0 and out.strip() else ""

    def activities_for(ph):
        rc, out = _runner(["python3", "scripts/openup-process-map.py",
                           "activities-for", ph, "--json"])
        if rc != 0:
            return []
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return []

    def reserve_id(prefix, session):
        rc, out = _runner(["python3", "scripts/openup-claims.py", "reserve-id",
                           "--prefix", prefix, "--pad", "3",
                           "--session-id", session])
        return out.strip().splitlines()[-1] if rc == 0 and out.strip() else ""

    def partition(candidates):
        p = subprocess.run(
            [sys.executable, "scripts/openup-board.py", "partition", "--stdin"],
            cwd=str(root), input=json.dumps(candidates),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            raise CycleError("partition failed: %s" % p.stderr.strip()[:200])
        return json.loads(p.stdout)

    def roadmap_pending():
        rc, out = _runner(["python3", "scripts/openup-roadmap.py", "list",
                           "--status", "pending"])
        if rc != 0:
            return []
        try:
            data = json.loads(out)
            return [e.get("title", "") for e in data] if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def lifecycle():
        rc, out = _runner(["python3", "scripts/openup-lifecycle.py", "status",
                           "--json"])
        if rc != 0:
            return {}
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {}

    def run_procedure(procedure, instruction):
        # An execution:direct activity runs its create-* procedure directly (T-101).
        # Capture the sub-procedure's DONE sentinel; the plan-iteration engine
        # reports its own cycle-level outcome. On failure surface the output.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = loop.run(dir=str(root), procedure=procedure,
                          max_iterations=loop.DEFAULT_MAX_ITERATIONS, env=env,
                          interactive=interactive, instruction=instruction,
                          _completion=_completion)
        out = buf.getvalue()
        if rc != 0:
            if out.strip():
                sys.stdout.write(out)
                sys.stdout.flush()
            return rc
        return _stamp_direct_artifact(root, procedure)

    return plan_iteration.run_plan_iteration(
        root, phase, dispatch_objectives=dispatch_objectives,
        dispatch_spec=dispatch_spec, run_gates=lambda: loop.run_gates(root),
        git_commit=git_commit, mint_id=mint_id, activities_for=activities_for,
        reserve_id=reserve_id, partition=partition,
        roadmap_pending=roadmap_pending, lifecycle=lifecycle,
        run_procedure=run_procedure, log=_log,
        suspend_sentinel=loop.SUSPEND_SENTINEL)


def _run_assess(root, decision, env, step_tier, cap, interactive, _completion,
                _subrun):
    """Wire the real callables into assess.run_assess (T-091): the grading
    sub-run, gates, and git-commit. Kept thin — the assess logic lives in
    assess.py."""
    root = Path(root)
    try:
        model = tiers.resolve_tier_model(root, step_tier, target="driver", env=env)
    except tiers.TierError as e:
        _log("FATAL: %s" % e)
        return EXIT_CONFIG

    def dispatch(instruction, system_prompt):
        _log("assess: grading sub-run (tier=%s, model=%s)" % (step_tier, model))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = loop.run(dir=str(root), procedure="assess-iteration",
                          max_iterations=cap, env=env, interactive=interactive,
                          instruction=instruction, system_prompt=system_prompt,
                          model=model, _completion=_completion)
        out = buf.getvalue().strip()
        if rc == EXIT_SUSPEND and out:
            print(out.splitlines()[-1])
        return rc

    def git_commit(paths, message):
        _git(["add"] + list(paths), root, check=True)
        _git(["commit", "-m", message], root, check=True)

    return assess.run_assess(root, decision, dispatch=dispatch,
                             run_gates=lambda: loop.run_gates(root),
                             git_commit=git_commit, log=_log)


def _sweep_run_logs(root):
    """T-108: register the cycle — sweep new/changed ``docs/agent-logs/``
    shards into a log-only ``[openup-skip]`` commit on the current branch, on
    EVERY cycle exit path. A cycle that suspended or failed still leaves its
    audit trail durable (observed stranded live on my-product). Never raises
    and never changes the cycle's exit code; a non-repo root is a no-op."""
    logs_rel = "docs/agent-logs"
    root = Path(root)
    if not (root / logs_rel).is_dir():
        return
    status = _git(["status", "--porcelain", "--", logs_rel], root)
    if status.returncode != 0 or not status.stdout.strip():
        return
    if _git(["add", "--", logs_rel], root).returncode != 0:
        _log("run-log sweep: git add failed; shards left uncommitted")
        return
    commit = _git(["commit", "-m",
                   "chore(process): sweep run-log shards [openup-skip]",
                   "--", logs_rel], root)
    if commit.returncode != 0:
        _log("run-log sweep: commit failed: %s"
             % (commit.stdout + commit.stderr).strip()[:200])
    else:
        _log("run-log sweep: committed %d shard change(s)"
             % len(status.stdout.strip().splitlines()))


def run_cycle(dir, env=None, step_max_iterations=DEFAULT_STEP_MAX_ITERATIONS,
              step_tier=DEFAULT_STEP_TIER, interactive=False, recover=True,
              _completion=None, _subrun=None, _ask=None,
              _plan_iteration=None, _assess=None, _milestone=None):
    """Run ONE delivery cycle under ``dir``. Returns an int exit code. Thin
    wrapper: on every exit path (advanced, done, suspend, typed failure) the
    run-log shards this cycle wrote are swept into a log-only commit (T-108).
    The full contract is on ``_run_cycle_inner``."""
    root = Path(dir).resolve()
    try:
        return _run_cycle_inner(
            dir, env=env, step_max_iterations=step_max_iterations,
            step_tier=step_tier, interactive=interactive, recover=recover,
            _completion=_completion, _subrun=_subrun, _ask=_ask,
            _plan_iteration=_plan_iteration, _assess=_assess,
            _milestone=_milestone)
    finally:
        _sweep_run_logs(root)


def _run_cycle_inner(dir, env=None,
                     step_max_iterations=DEFAULT_STEP_MAX_ITERATIONS,
                     step_tier=DEFAULT_STEP_TIER, interactive=False,
                     recover=True, _completion=None, _subrun=None, _ask=None,
                     _plan_iteration=None, _assess=None, _milestone=None):
    """Run ONE delivery cycle under ``dir``. Returns an int exit code.

    ``recover`` (default True, T-092/T-094) lets the engine rebuild blocking
    repo state — close done-but-unclosed lanes, author a plan-iteration
    decision's missing spec, and (with the human's explicit consent) run one
    product-manager replenishment pass when nothing is promotable — before
    dispatching; ``recover=False`` is byte-equivalent to the T-089 behavior.

    Navigation is deterministic (T-101): a fresh authoring phase resolves to
    ``plan-iteration`` from the process map, so a ``noop`` is a drained/complete
    state → ``DONE``. (The per-cycle LLM navigator was retired in T-103.)

    ``_completion`` is loop.run's scripted-LLM test seam, passed through to
    every judgment sub-run; ``_subrun`` replaces the whole judgment-step call
    (signature: fn(task, box, instruction) -> int); ``_ask`` replaces the
    interactive consent prompt (fn(question) -> str) for tests.
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

    # Recovery (T-092/T-094) — bounded: Case B once, then up to two rounds of
    # (Case A | consent-gated replenishment), each followed by one re-resolve.
    if recover and path in ("plan-iteration", "noop"):
        try:
            closed = reconcile_unclosed_lanes(root)
        except CycleError as e:
            _log("FATAL: %s" % e)
            return EXIT_STEP
        if closed:
            decision = resolve_decision(root)
            path = decision.get("path")
            _log("decision after lane closure: path=%s — %s"
                 % (path, decision.get("reason") or ""))
    replenished = False
    while recover:
        if path == "plan-iteration":
            # T-090: for an authoring phase (inception/elaboration) plan a full
            # phase-appropriate iteration; otherwise keep the T-092 single-row
            # promote (construction/transition feature delivery, unchanged).
            iter_phase = (decision.get("phase") or "").lower()
            if iter_phase in plan_iteration.AUTHORING_PHASES:
                if _plan_iteration is not None:
                    rc = _plan_iteration(root, decision, iter_phase)
                else:
                    rc = _run_plan_iteration(
                        root, iter_phase, env, step_tier, step_max_iterations,
                        interactive, _completion, _subrun)
                if rc == EXIT_SUSPEND:
                    _log("plan-iteration suspended awaiting human input")
                    return EXIT_SUSPEND
                if rc != EXIT_OK:
                    return rc if rc in (EXIT_CONFIG, EXIT_ENDPOINT,
                                        EXIT_MAX_ITERATIONS) else EXIT_STEP
                decision = resolve_decision(root)
                path = decision.get("path")
                _log("decision after plan-iteration: path=%s — %s"
                     % (path, decision.get("reason") or ""))
                if path in ("pick", "resume"):
                    break
                # planned but not advanced — fall through to the stuck check
            else:
                rc = recover_missing_spec(root, decision, env, step_tier,
                                          step_max_iterations, interactive,
                                          _completion, _subrun)
                if rc == EXIT_OK:
                    decision = resolve_decision(root)
                    path = decision.get("path")
                    _log("decision after spec recovery: path=%s — %s"
                         % (path, decision.get("reason") or ""))
                    if path in ("pick", "resume"):
                        break
                    # authored but not advanced — fall through to the stuck check
                elif rc != EXIT_UNSUPPORTED:
                    return rc
                # rc == EXIT_UNSUPPORTED: blocked lane — a stuck state too (T2)
        # Stuck (T-094): nothing deterministic left, roadmap present, one shot.
        if (path in ("noop", "plan-iteration") and not replenished
                and (root / "docs" / "roadmap.md").exists()):
            out = replenish_flow(root, env, step_tier, step_max_iterations,
                                 interactive, _completion, _subrun, _ask)
            if out is not None:
                return out
            replenished = True
            decision = resolve_decision(root)
            path = decision.get("path")
            _log("decision after replenishment: path=%s — %s"
                 % (path, decision.get("reason") or ""))
            continue  # one more round: the new decision may need Case A
        if path == "plan-iteration":
            _log("recovery did not advance the decision (path=%s) — stopping"
                 % path)
            return EXIT_UNSUPPORTED
        break

    if path == "noop":
        # Nothing pickable and nothing to plan. Navigation is deterministic
        # (T-101): a fresh authoring phase resolves to plan-iteration, not noop,
        # so a genuine noop here is a drained/complete state — report DONE. (The
        # per-cycle LLM navigator was retired in T-103.)
        print("OPENUP-NEXT: DONE — %s"
              % (decision.get("reason") or "nothing to do"))
        return EXIT_OK
    if path == "assess-iteration":
        # T-091: grade the exhausted iteration and record ## Assessment.
        if _assess is not None:
            return _assess(root, decision)
        return _run_assess(root, decision, env, step_tier,
                           step_max_iterations, interactive, _completion, _subrun)
    if path == "milestone-review":
        # T-091: prepare evidence + pause for the human go/no-go (zero LLM).
        if _milestone is not None:
            return _milestone(root, decision)
        return assess.run_milestone(
            root, decision, runner=lambda r, argv: (lambda p: (p.returncode, p.stdout))(
                _run(["python3"] + list(argv), r)),
            log=_log, suspend_sentinel=loop.SUSPEND_SENTINEL)
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
            try:
                rc = _dispatch_judgment(
                    root, task, box, env, step_tier, step_max_iterations,
                    interactive, resumable_input, _completion, _subrun)
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

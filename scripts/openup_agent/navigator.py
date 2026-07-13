"""navigator.py — the process navigator behind the reference driver (T-096).

The deterministic layers answer first: ``openup-board.py resolve`` → the T-089
``cycle`` engine handle every state they can *classify* (pick / resume /
plan-iteration / assess / milestone). When they yield **nothing actionable** — a
``noop`` decision, most importantly a fresh project with no ``docs/roadmap.md`` —
the old path was a hardcoded hint ("run openup-create-vision"). T-095 pushed that
hardcoded pre-Inception state machine one level up, into ``scripts/next-cycle``.

This module removes the hardcoding entirely. Instead of a fixed brief → vision →
cycle ladder, the driver asks an LLM to **navigate the OpenUP process against the
project's actual state**: it assembles facts deterministically (the process map,
the lifecycle status, a Ring-1 artifact survey, the procedures index) and runs
ONE bounded judgment sub-run that returns — as a structured file, the T-072
pattern — the next procedure to run, its ``--instruction``, and any **missing
human inputs**. The driver then runs that procedure, or raises the missing input
as a T-074 input-request.

Consent boundary (T-094): navigation that authors *process* artifacts (vision,
use-cases, architecture, iteration plan) runs directly; anything that would
propose *product scope* stays behind the T-094 consent gate and is never invented
here. ``PROCESS_ARTIFACT_PROCEDURES`` is the allowlist that may run directly.

Self-contained and stdlib-only: the two operations that touch the driver's guts
(dispatching the sub-run, running the chosen procedure) are passed in as
callables, so this module imports nothing from ``cycle`` and is unit-testable
with fakes.
"""

import json
import subprocess
import sys
from pathlib import Path

# Decision file the sub-run writes and the driver reads back (Ring-3, gitignored).
DECISION_REL = Path(".openup") / "navigator-decision.json"

# Procedures the navigator may run **directly** — process-artifact authoring at a
# bootstrap/unclassifiable state. Anything else that a decision might name is
# treated as product-scope-proposing and deferred to the T-094 consent gate.
PROCESS_ARTIFACT_PROCEDURES = frozenset({
    "openup-create-vision",
    "openup-shared-vision",
    "openup-create-use-case",
    "openup-detail-use-case",
    "openup-create-architecture-notebook",
    "openup-create-risk-list",
    "openup-create-iteration-plan",
    "openup-create-test-plan",
})

# Ring-1 artifacts surveyed. label -> repo-relative path. A path in
# SCAFFOLDABLE is a human-authored artifact the navigator can scaffold as a
# template; it counts as *present* only when it exists AND lacks the template
# marker (a still-templated scaffold reads as absent, so a filled artifact — not
# the empty scaffold — advances the loop).
RING1_ARTIFACTS = (
    ("vision", "docs/vision.md"),
    ("roadmap", "docs/roadmap.md"),
    ("project_status", "docs/project-status.md"),
    ("architecture", "docs/architecture-notebook.md"),
    ("risk_list", "docs/risk-list.md"),
    ("stakeholder_brief", "docs/inputs/stakeholder-brief.md"),
)

# The default human-input artifact for a fresh Inception project (the input the
# create-vision procedure reads). Used when the navigator flags a missing input
# but a weak model omits an explicit ``input_path`` — so convergence never
# depends on the model naming it.
DEFAULT_INPUT_PATH = "docs/inputs/stakeholder-brief.md"

# Marker distinguishing an unfilled scaffold from a human-filled artifact.
TEMPLATE_MARKER = ("<!-- template: replace every section with your product's "
                   "reality, delete this line, then re-run ./scripts/next-cycle -->")

SCAFFOLDABLE = frozenset({DEFAULT_INPUT_PATH})

# The standard instruction for the deterministic create-vision bootstrap step
# (T-098): with a filled brief and no vision, authoring the vision + an initial
# roadmap is the unambiguous next move — the LLM only *authors* (reliable), so
# navigation does not depend on it emitting a decision file.
VISION_INSTRUCTION = (
    "read docs/inputs/stakeholder-brief.md; produce docs/vision.md, and also "
    "author an initial docs/roadmap.md with 5-8 pending entries (a table with "
    "ID, Title, Status, Priority, Dependencies, Value columns) covering the path "
    "from the first use cases to the core features")

BRIEF_TEMPLATE = """\
%s

# Stakeholder Brief — <project name>

## The situation

<Who has what problem today? What have they already tried? Why does it fail?>

## Who cares (stakeholders)

- **<role>** — <what they need from this>
- **<role>** — <what they need from this>

## What they want (desired outcomes)

- <observable outcome, not a feature list>
- <observable outcome>

## Constraints & context

- <scale, platform, non-negotiables>

## Explicitly out of scope (for now)

- <the things v1 will NOT do>
""" % TEMPLATE_MARKER

NAVIGATOR_SYSTEM_PROMPT = """\
You are the OpenUP process navigator. The deterministic engine has found nothing
it can execute, so you decide the single next step by evaluating the OpenUP
workflow against the FACTS given in the user message.

You do NOT write product docs, code, or roadmap entries yourself. Your ONLY
output is a decision file. Use the write_file tool to write %(decision)s with
EXACTLY this JSON shape and nothing else:

{
  "procedure": "<an openup-* procedure name, or null>",
  "instruction": "<the --instruction text to hand that procedure, or empty>",
  "missing_inputs": ["<a human input the process needs before any procedure can run>"],
  "input_path": "<repo-relative file the human should author for that input, or empty>",
  "rationale": "<one line: which phase/activity and why>"
}

Rules:
- Pick the procedure from the phase's ordered activities in the FACTS (the first
  unmet activity's skill), constrained to procedures that exist in the FACTS'
  procedures index.
- If a required HUMAN input is absent (e.g. no vision AND no stakeholder brief to
  author one from), set "procedure": null and list the concrete missing input in
  "missing_inputs" — describe what the human must provide, not a procedure. When
  that input is a **document the human writes** (e.g. a stakeholder brief), set
  "input_path" to where it belongs (e.g. "docs/inputs/stakeholder-brief.md") so a
  fillable template can be scaffolded for them.
- If a procedure CAN run, set "missing_inputs": [] and give it a concrete
  "instruction" (what to read, what to produce).
- If nothing is actionable and nothing is missing (the project is genuinely
  complete for now), set "procedure": null and "missing_inputs": [].
- Do not invent product scope. Never name a procedure that appends roadmap
  entries to an existing backlog.

When the decision file is written, reply with NO tool calls and put this exact
sentinel on its own line: %(sentinel)s
""".rstrip()

NAVIGATOR_SENTINEL = "OPENUP-NAVIGATOR: DECIDED"


def _subprocess_runner(root, argv):
    """Default facts runner: run a script under ``root``, return (rc, stdout)."""
    proc = subprocess.run(["python3"] + argv, cwd=str(root),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True)
    return proc.returncode, proc.stdout


def _lifecycle_status(root, runner):
    rc, out = runner(root, ["scripts/openup-lifecycle.py", "status", "--json"])
    if rc != 0:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {}


def _phase_activities(root, phase, runner):
    if not phase:
        return []
    rc, out = runner(root, ["scripts/openup-process-map.py", "activities-for",
                            phase, "--json"])
    if rc != 0:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def _is_present(root, rel):
    """True if the artifact exists — and, for a scaffoldable one, is not still a
    bare template (marker present ⇒ unfilled ⇒ counts as absent)."""
    path = Path(root) / rel
    if not path.exists():
        return False
    if rel in SCAFFOLDABLE:
        try:
            return TEMPLATE_MARKER not in path.read_text(encoding="utf-8")
        except OSError:
            return False
    return True


def _ring1_survey(root):
    return {label: _is_present(root, rel) for label, rel in RING1_ARTIFACTS}


def _procedures_index(root):
    """Available procedure names (``openup-<name>`` → ``openup-<name>``)."""
    proc_dir = Path(root) / "docs-eng-process" / "procedures"
    if not proc_dir.is_dir():
        return []
    names = sorted(p.stem for p in proc_dir.glob("openup-*.md"))
    return names


def build_navigator_input(root, runner=_subprocess_runner):
    """Assemble the deterministic FACTS the navigator classifies. Pure data —
    every field is computed by a script call or a filesystem check, never by the
    LLM. ``runner`` is injectable for tests: fn(root, argv) -> (rc, stdout)."""
    status = _lifecycle_status(root, runner)
    phase = status.get("phase")
    return {
        "phase": phase,
        "milestone": status.get("milestone"),
        "milestone_criteria": status.get("criteria", []),
        "phase_activities": _phase_activities(root, phase, runner),
        "ring1_artifacts": _ring1_survey(root),
        "procedures_index": _procedures_index(root),
    }


def render_navigator_instruction(facts):
    """The sub-run's user message: the FACTS as JSON + the marching order."""
    return (
        "FACTS about this OpenUP project (computed deterministically):\n\n"
        + json.dumps(facts, indent=2, sort_keys=True)
        + "\n\nDecide the single next process step and write the decision file "
        "as instructed. Do not author any product artifact yourself."
    )


def read_navigator_decision(root):
    """Parse + validate the decision file. Returns a normalized dict
    ``{procedure, instruction, missing_inputs, rationale}`` or None when the file
    is absent or malformed."""
    path = Path(root) / DECISION_REL
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, dict):
        return None
    procedure = raw.get("procedure")
    if procedure is not None and not isinstance(procedure, str):
        return None
    procedure = (procedure or "").strip() or None
    missing = raw.get("missing_inputs") or []
    if not isinstance(missing, list):
        return None
    missing = [str(m).strip() for m in missing if str(m).strip()]
    return {
        "procedure": procedure,
        "instruction": str(raw.get("instruction") or "").strip(),
        "missing_inputs": missing,
        "input_path": str(raw.get("input_path") or "").strip(),
        "rationale": str(raw.get("rationale") or "").strip(),
    }


def _clear_decision(root):
    path = Path(root) / DECISION_REL
    try:
        path.unlink()
    except OSError:
        pass


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
# Exit codes mirror cycle.py's (kept in sync; imported there for the caller).
NAV_OK = 0
NAV_CONFIG = 2
NAV_SUSPEND = 5
NAV_STEP = 8

# cycle.py meta lives in .openup/cycle.json under key "navigator"; we keep the
# open input-request id there so a re-run does not duplicate it.
_META_REL = Path(".openup") / "cycle.json"


def _read_meta(root):
    path = Path(root) / _META_REL
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_nav_meta(root, **fields):
    path = Path(root) / _META_REL
    meta = _read_meta(root)
    nav = dict(meta.get("navigator") or {})
    nav.update(fields)
    meta["navigator"] = nav
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _request_open(root, rel_path):
    """True when a recorded input-request still exists and is unanswered."""
    if not rel_path:
        return False
    path = Path(root) / rel_path
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip().lower()
        if s.startswith("status:"):
            return s.split(":", 1)[1].strip() != "answered"
    return True


def _generic_template(missing):
    return ("%s\n\n# Input needed\n\nThe process needs this from you:\n\n%s\n\n"
            "Replace this with your content, delete the marker line above, then "
            "re-run ./scripts/next-cycle.\n"
            % (TEMPLATE_MARKER, "\n".join("- %s" % m for m in missing)))


def _default_input_path(root):
    """The canonical human-input artifact for a fresh pre-Inception project: the
    stakeholder brief, when neither a vision nor a filled brief exists yet.
    Returns "" when no default applies (e.g. a vision already exists)."""
    if _is_present(root, "docs/vision.md"):
        return ""
    if _is_present(root, DEFAULT_INPUT_PATH):
        return ""  # a filled brief already exists — not a scaffolding case
    return DEFAULT_INPUT_PATH


def _bootstrap_step(root, facts):
    """The deterministic Inception-bootstrap decision (T-098) — no navigator LLM.

    The fresh pre-vision states are unambiguous, so the driver must not depend on
    a weak model emitting a decision file to get past them:
      - inception, no vision, no filled brief -> ("scaffold", brief_path)
      - inception, filled brief, no vision     -> ("procedure", "openup-create-vision", instruction)
    Returns None for any other state (a vision exists, a non-inception phase, or
    create-vision is not in the procedures index) — those defer to the LLM
    navigator.
    """
    phase = (facts.get("phase") or "").strip().lower()
    if phase != "inception":
        return None
    ring1 = facts.get("ring1_artifacts") or {}
    if ring1.get("vision"):
        return None
    if not ring1.get("stakeholder_brief"):
        return ("scaffold", DEFAULT_INPUT_PATH)
    if "openup-create-vision" not in (facts.get("procedures_index") or []):
        return None
    return ("procedure", "openup-create-vision", VISION_INSTRUCTION)


def _scaffold_input(root, rel_path, missing, log, print_, suspend_sentinel):
    """Scaffold a fillable template at ``rel_path`` (never clobbering a filled or
    partially-filled file) and suspend, guiding the human to fill it. This is the
    artifact affordance a bare input-request cannot provide (T-097)."""
    path = Path(root) / rel_path
    body = BRIEF_TEMPLATE if rel_path == DEFAULT_INPUT_PATH else _generic_template(missing)
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError:
            existing = ""
        if TEMPLATE_MARKER not in existing:
            # Already filled — the loop should have advanced; re-guide anyway.
            log("navigator: %s exists and is filled — re-run to proceed" % rel_path)
            print_("%s — %s (already filled; re-run ./scripts/next-cycle)"
                   % (suspend_sentinel, rel_path))
            return NAV_SUSPEND
        log("navigator: %s already scaffolded (still a template) — awaiting fill"
            % rel_path)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        log("navigator: scaffolded a template at %s for the human to fill"
            % rel_path)
    print_("%s — fill %s (a template is there), then re-run ./scripts/next-cycle"
           % (suspend_sentinel, rel_path))
    return NAV_SUSPEND


def _raise_missing_input(root, missing, runner, log, print_, suspend_sentinel):
    """Ensure a single input-request captures the missing human input and
    suspend (exit 5). Re-suspends an already-open request without duplicating.
    Used only for a genuine short-answer question — a missing *artifact* is
    scaffolded instead (see _scaffold_input)."""
    nav = _read_meta(root).get("navigator") or {}
    existing = nav.get("request")
    if _request_open(root, existing):
        log("navigator: missing input still open — re-suspending %s" % existing)
        print_("%s — %s" % (suspend_sentinel, existing))
        return NAV_SUSPEND
    question = ("The process needs a human input before it can proceed: %s"
                % "; ".join(missing))
    rc, out = runner(root, ["scripts/openup-input.py", "request",
                            "--title", "Process navigator needs input",
                            "--question", question, "--json"])
    if rc != 0:
        log("navigator: could not create input-request:\n%s" % out.strip()[:800])
        return NAV_STEP
    try:
        request = json.loads(out)["request"]
    except (json.JSONDecodeError, KeyError, TypeError):
        request = out.strip().splitlines()[-1] if out.strip() else ""
    _write_nav_meta(root, request=request)
    log("navigator: awaiting human input in %s" % request)
    print_("%s — %s" % (suspend_sentinel, request))
    return NAV_SUSPEND


def run_navigator(root, *, dispatch, run_procedure, runner=_subprocess_runner,
                  log=None, print_=None, suspend_sentinel="OPENUP-AGENT: SUSPENDED"):
    """Navigate one unclassifiable/``noop`` state. Returns an int exit code.

    ``dispatch(instruction, system_prompt) -> int`` runs the bounded navigator
    sub-run (the LLM that writes the decision file). ``run_procedure(procedure,
    instruction) -> int`` runs a full OpenUP procedure. Both are injected by
    cycle.py (real) or tests (fakes), so this module never imports cycle.
    """
    root = Path(root)
    log = log or (lambda m: sys.stderr.write("[navigator] %s\n" % m))
    print_ = print_ or (lambda m: (sys.stdout.write(m + "\n"), sys.stdout.flush()))

    facts = build_navigator_input(root, runner=runner)
    log("navigating: phase=%s, ring1=%s"
        % (facts.get("phase"),
           {k: v for k, v in facts.get("ring1_artifacts", {}).items() if v}))

    # T-098: handle the unambiguous Inception bootstrap deterministically — do NOT
    # spend (or depend on) a navigator LLM call a weak model may not complete.
    boot = _bootstrap_step(root, facts)
    if boot is not None:
        if boot[0] == "scaffold":
            log("navigator: fresh Inception, no brief — scaffolding %s "
                "(deterministic, no navigator LLM)" % boot[1])
            return _scaffold_input(root, boot[1], ["a stakeholder brief"],
                                   log, print_, suspend_sentinel)
        # ("procedure", name, instruction): filled brief, no vision → author it.
        log("navigator: filled brief, no vision — running %s deterministically "
            "(no navigator LLM; the model only authors)" % boot[1])
        return run_procedure(boot[1], boot[2])

    _clear_decision(root)  # never read a stale decision
    instruction = render_navigator_instruction(facts)
    system_prompt = NAVIGATOR_SYSTEM_PROMPT % {"decision": DECISION_REL.as_posix(),
                                               "sentinel": NAVIGATOR_SENTINEL}
    rc = dispatch(instruction, system_prompt)
    if rc == NAV_SUSPEND:
        return NAV_SUSPEND
    if rc != 0:
        log("navigator sub-run failed (exit %d)" % rc)
        return rc if rc in (NAV_CONFIG,) else NAV_STEP

    decision = read_navigator_decision(root)
    if decision is None:
        log("navigator produced no valid decision file (%s) — cannot navigate"
            % DECISION_REL.as_posix())
        return NAV_STEP
    log("navigator decision: procedure=%s missing=%d — %s"
        % (decision["procedure"], len(decision["missing_inputs"]),
           decision["rationale"][:120]))

    if decision["missing_inputs"]:
        # A missing human *artifact* (the LLM's input_path, or the fresh-project
        # brief default) gets a fillable template — an input-request cannot
        # produce a document, so it would never converge (T-097). A genuine
        # short-answer question with no artifact path still uses the request.
        artifact = decision["input_path"] or _default_input_path(root)
        if artifact:
            return _scaffold_input(root, artifact, decision["missing_inputs"],
                                   log, print_, suspend_sentinel)
        return _raise_missing_input(root, decision["missing_inputs"], runner,
                                    log, print_, suspend_sentinel)

    procedure = decision["procedure"]
    if not procedure:
        print_("OPENUP-NEXT: DONE — navigator found nothing actionable (%s)"
               % (decision["rationale"] or "no next step"))
        return NAV_OK

    if procedure not in PROCESS_ARTIFACT_PROCEDURES:
        # Product-scope territory — must not run silently (T-094 consent gate
        # owns backlog proposals). Refuse to run directly.
        log("navigator named a non-process-artifact procedure (%s) — that is "
            "product-scope work behind the T-094 consent gate, not run directly"
            % procedure)
        print_("OPENUP-NEXT: DONE — navigator deferred %s to the consent gate "
               "(product scope is never authored silently)" % procedure)
        return NAV_OK

    log("navigator: running process-artifact procedure %s directly" % procedure)
    return run_procedure(procedure, decision["instruction"])

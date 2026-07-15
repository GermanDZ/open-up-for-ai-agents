"""plan_iteration.py — the cycle engine's Plan Iteration path (T-090).

When ``openup-board.py resolve`` returns ``plan-iteration`` for an **authoring
phase** (inception / elaboration) with no active iteration, the engine plans a
phase-appropriate iteration deterministically — porting ``/openup-start-iteration``
§0b into code — and drops to the LLM only for the two genuine judgment points:

    mint iteration id                                   # code
    LLM: choose 1-5 objectives                          # judgment (one sub-run)
    activities-for(phase) -> candidate lanes            # code
    partition into clusters (T-079)                     # code
    per lane: reserve id + LLM authors its spec + gate  # judgment (one sub-run each)
    write the iteration-plan instance (traces lanes)    # code
                                                        # -> re-resolve picks lane 1

Everything deterministic is a composition of existing scripts (mint-iteration-id,
reserve-id --prefix, activities-for, partition, the gates). The two judgment
points reuse the T-089/T-092 bounded-sub-run machinery. All inter-step state is
the repo (reserved ids, committed specs, the instance), so a crashed plan resumes.

Construction/transition plan-iteration is NOT handled here — it keeps the T-092
single-row promote (``recover_missing_spec``). This module is phase-gated by the
caller via ``AUTHORING_PHASES``.

Self-contained + stdlib-only: the driver-coupled operations (run a sub-run, run
gates, git-commit, run a script) are injected, so this module imports nothing
from ``cycle`` and is unit-testable with fakes.
"""

import json
import re
from pathlib import Path

# Phases whose activities compose create-* work-product authoring — the ones a
# Plan Iteration plans. Construction/transition promote features one row at a
# time (the T-092 path), not a multi-lane authoring iteration.
AUTHORING_PHASES = frozenset({"inception", "elaboration"})

OBJECTIVES_REL = Path(".openup") / "iteration-objectives.json"

OBJECTIVES_SENTINEL = "OPENUP-OBJECTIVES: CHOSEN"

OBJECTIVES_SYSTEM_PROMPT = """\
You are the OpenUP iteration planner. Choose the objectives for ONE iteration of
the current phase, from the FACTS in the user message (the phase, its milestone
criteria, the pending roadmap order, and the phase's activity composition).

You do NOT author any artifact. Your ONLY output is a decision file. Use
write_file to write %(objectives)s with EXACTLY this JSON shape:

{
  "objectives": ["<1 to 5 short, deliverable objectives for this iteration>"],
  "rationale": "<one line: why these, in this phase>"
}

Rules:
- 1 to 5 objectives, each achievable in one iteration and phrased as an outcome.
- Consume the pending roadmap order as given (do not re-rank it); prefer the
  highest-value pending items and the phase's own objectives.
- Do not invent product scope beyond what the FACTS imply.

When the file is written, reply with NO tool calls and put this exact sentinel
on its own line: %(sentinel)s
""".rstrip()

# Per-lane spec authoring — a phase-activity lane produces an OpenUP work product
# via its create-* skill. The lane's plan.md is a task-spec (status ready→done),
# read by the executor and _work_item_done — NOT a typed maturity instance.
LANE_SPEC_CONTRACT = """\
Author the task spec at docs/changes/%(lane)s/plan.md for iteration %(iteration)s.
This lane performs the OpenUP activity **%(activity)s** (role: %(role)s) using the
%(skill)s procedure, in service of these iteration objectives:
%(objectives)s

Read docs/vision.md and the Ring-1 product docs (docs/product/) first if present.
The spec file MUST carry:
- YAML frontmatter: id: %(lane)s, title, status: ready, priority, track
  (quick|standard), touches (the file paths this lane will produce/change),
  depends-on: []
- ## Requirements — numbered assertions, each with at least one acceptance
  scenario using the bold markers **Given** / **When** / **Then**
- ## Operations — 1-8 unchecked checkbox steps (`- [ ] ...`), ordered; the first
  step should invoke the %(skill)s work (e.g. produce the artifact it authors). A
  step that is a command must be command-only; prose steps are judgment work; tag
  a step `(%(role)s)` when it runs under this lane's role hat.
Author ONLY the spec file — do not begin the activity's work itself."""


# --------------------------------------------------------------------------
# T-104 — engine-owned authoring ceremony for execution:direct sub-runs.
# The model authors the document BODY only; frontmatter stamping (stamping.py),
# project-config lookup, and validation (check-docs in the gates) are engine
# work. The exclusion below counteracts the ceremony the procedure file still
# fans out to in S1; the procedure read itself disappears in T-106.
# --------------------------------------------------------------------------
CEREMONY_EXCLUSION = """\
Author the document BODY only — headings and prose. Do NOT write YAML
frontmatter: the engine stamps the typed instance frontmatter (type, id, title,
status) after you finish. Do NOT read or apply doc-frontmatter.md,
docs-meta.schema.json, trace-model.json, or any rubric file, and do NOT read
docs/project-config.yaml — everything project-specific you need is injected in
this instruction. Do NOT self-critique or grade your own output; the engine
validates the result deterministically (check-docs) after you finish."""

# T-106: the T-099 pinned initial-roadmap contract now lives in the task library
# as the `author-initial-roadmap` def's `judgment` bullets (the header row, the
# `T-NNN` id scheme, `pending` status, the priority enum, and delivery ordering) —
# retiring the interim ROADMAP_FORMAT constant that lived here (T-104). The
# roadmap task's instruction is built from that def like any other task.

CONFIG_REL = Path("docs") / "project-config.yaml"


def _config_context(lines):
    """The top-level ``context:`` block-scalar text (dedented), or ''."""
    out, in_block = [], False
    for raw in lines:
        if in_block:
            if raw.strip() and not raw.startswith((" ", "\t")):
                break
            out.append(raw.strip())
        elif re.match(r"context:\s*(\|[+-]?\s*)?(#.*)?$", raw):
            in_block = True
        elif raw.startswith("context:"):
            return raw.partition(":")[2].split("#", 1)[0].strip()
    return "\n".join(out).strip()


def _config_rules(lines, artifact):
    """The ``rules.<artifact>:`` list items, or []. Artifact keys equal the
    /openup-create-<type> skill suffix (project-config.md §artifact-type keys)."""
    items, in_rules, in_artifact = [], False, False
    for raw in lines:
        stripped = raw.strip()
        if in_artifact:
            if stripped.startswith("- "):
                items.append(stripped[2:].split(" #", 1)[0].strip())
                continue
            if stripped and not stripped.startswith("#"):
                break
        elif in_rules:
            if raw.strip() and not raw.startswith((" ", "\t")):
                break
            if stripped.rstrip(":").strip() == artifact and stripped.endswith(":"):
                in_artifact = True
        elif raw.startswith("rules:"):
            in_rules = True
    return items


def project_config_block(root, artifact=None):
    """<project-context>/<project-rules> injection text from
    docs/project-config.yaml, or '' when absent. The ENGINE reads the file,
    exactly once — the model never probes for it (the 5x re-read noise
    observed live on the qwen fixture)."""
    path = Path(root) / CONFIG_REL
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    parts = []
    context = _config_context(lines)
    if context:
        parts.append("<project-context>\n%s\n</project-context>" % context)
    rules = _config_rules(lines, artifact) if artifact else []
    if rules:
        parts.append("<project-rules>\n%s\n</project-rules>"
                     % "\n".join("- %s" % r for r in rules))
    return "\n\n".join(parts)


def render_task_instruction(root, task_def, objectives):
    """Assemble a task-def authoring sub-run's instruction (T-106): the task ask
    (name, role, artifact, output path) + its ``judgment`` (what-good-looks-like)
    + its declared inputs + the T-104 engine-owned-ceremony contract (exclusion,
    injected config). No procedure file is read — this instruction IS the spec.

    The pinned initial-roadmap format is carried by the author-initial-roadmap
    def's judgment bullets (no special-casing here)."""
    judgment = "\n".join("- %s" % b for b in task_def.get("judgment", []))
    inputs = ", ".join(task_def.get("inputs") or []) or "none"
    parts = [
        "Perform the OpenUP task '%s' (role: %s). Produce the %s at %s, in "
        "service of these objectives:\n%s"
        % (task_def.get("name"), task_def.get("role"), task_def.get("artifact"),
           task_def.get("output_path"),
           "\n".join("- %s" % o for o in objectives)),
        "What a good result looks like:\n%s" % judgment,
        "Inputs to read: %s." % inputs,
        CEREMONY_EXCLUSION,
    ]
    config = project_config_block(root, task_def.get("artifact"))
    if config:
        parts.append(config)
    return "\n\n".join(parts)


# --------------------------------------------------------------------------
# Deterministic helpers (pure / data)
# --------------------------------------------------------------------------
def build_objectives_input(phase, milestone, criteria, activities, roadmap_pending):
    """The FACTS the objectives sub-run chooses from (all computed in code)."""
    return {
        "phase": phase,
        "milestone": milestone,
        "milestone_criteria": criteria,
        "phase_activities": [a.get("name") for a in activities],
        "roadmap_pending": roadmap_pending,
    }


def render_objectives_instruction(facts):
    return (
        "FACTS for planning this iteration (computed deterministically):\n\n"
        + json.dumps(facts, indent=2, sort_keys=True)
        + "\n\nChoose 1-5 objectives and write the decision file as instructed. "
        "Author no product artifact yourself."
    )


def read_objectives(root):
    """Parse .openup/iteration-objectives.json → list[str] (1-5) or None."""
    path = Path(root) / OBJECTIVES_REL
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    objs = raw.get("objectives") if isinstance(raw, dict) else None
    if not isinstance(objs, list):
        return None
    objs = [str(o).strip() for o in objs if str(o).strip()]
    if not (1 <= len(objs) <= 5):
        return None
    return objs


def generate_lanes(activities):
    """One candidate lane per phase activity (deterministic). Each carries the
    activity name, its role hat, its first authoring skill, and (T-101) its
    ``execution`` mode + declared ``requires_input``. Activities with no skill
    (e.g. ``ongoing-tasks``) are skipped — nothing to author."""
    lanes = []
    for a in activities:
        skills = a.get("skills") or []
        if not skills:
            continue
        lanes.append({"activity": a.get("name"), "role": a.get("role"),
                      "skill": skills[0],
                      "execution": a.get("execution") or "spec-then-execute",
                      "requires_input": a.get("requires_input"),
                      # T-106: ordered task-library ids driving the direct path.
                      "tasks": a.get("tasks") or []})
    return lanes


# Marker distinguishing an unfilled scaffold from a human-filled artifact (T-101,
# generalizing the T-097 brief scaffold to any declared input).
INPUT_TEMPLATE_MARKER = ("<!-- template: replace this with your content, delete "
                         "this line, then re-run -->")


def _input_present(root, rel_path):
    """True if a declared input file exists AND is not a bare template."""
    p = Path(root) / rel_path
    if not p.exists():
        return False
    try:
        return INPUT_TEMPLATE_MARKER not in p.read_text(encoding="utf-8")
    except OSError:
        return False


def _scaffold_required_input(root, rel_path, describe):
    """Write a marker-guarded template at ``rel_path`` for a missing declared
    input (never clobbering a filled/partial file). Returns True if it scaffolded
    (or the file is a still-unfilled template); the caller suspends."""
    p = Path(root) / rel_path
    if p.exists():
        return True  # exists but templated (caller checked _input_present) — keep
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("%s\n\n# %s\n\n<Replace this with %s.>\n"
                 % (INPUT_TEMPLATE_MARKER, describe or "Required input", describe
                    or "your content"), encoding="utf-8")
    return True


def _first_missing_input(root, activities):
    """The first activity (in order) whose declared requires_input is missing/
    templated → (path, describe); or None when all declared inputs are present."""
    for a in activities:
        ri = a.get("requires_input")
        if isinstance(ri, dict) and ri.get("path") and not _input_present(root, ri["path"]):
            return ri["path"], ri.get("describe")
    return None


def iteration_plan_path(phase, iteration):
    return Path("docs") / "phases" / phase / ("iteration-%s-plan.md" % iteration)


def render_iteration_plan_instance(phase, iteration, lane_ids, objectives,
                                   direct_done=None):
    """The iteration-plan work-product instance (typed; traces its spec-then-
    execute lanes). ``direct_done`` lists execution:direct activities that ran
    their procedure directly (recorded in the body, not traced as work items)."""
    fm = [
        "---",
        "type: iteration-plan",
        "id: IP-%s" % iteration,
        "title: Iteration %s — %s" % (iteration, phase.capitalize()),
        "status: approved",
        "traces-from: [%s]" % ", ".join(lane_ids),
        "owner-role: project-manager",
        "iteration: %s-%s" % (phase, iteration),
        "---",
        "",
        "# Iteration %s — %s" % (iteration, phase.capitalize()),
        "",
        "**Phase**: %s" % phase,
        "",
        "## Objectives",
        "",
    ]
    fm += ["- %s" % o for o in objectives]
    fm += [
        "",
        "## Committed Work Items",
        "",
    ]
    fm += ["- %s" % lid for lid in lane_ids] or ["- (none — all activities ran directly)"]
    if direct_done:
        fm += ["", "## Directly-run activities (execution: direct)", ""]
        fm += ["- %s" % a for a in direct_done]
    fm += [
        "",
        "## Evaluation Criteria",
        "",
        "- Every committed work item is delivered (its change folder archived or "
        "its plan status done/verified).",
        "- Each authored artifact passes its gates (check-docs, fence).",
        "- The iteration's objectives above are met.",
        "",
    ]
    return "\n".join(fm)


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
# Exit codes mirror cycle.py's.
PI_OK = 0
PI_CONFIG = 2
PI_SUSPEND = 5
PI_STEP = 8

_SEQ_RE = re.compile(r"-(\d+)$")


def run_plan_iteration(root, phase, *, dispatch_objectives, dispatch_spec,
                       run_gates, git_commit, mint_id, activities_for,
                       reserve_id, partition, roadmap_pending, lifecycle,
                       run_task=None, task_defs=None, log=None, print_=None,
                       suspend_sentinel="OPENUP-AGENT: SUSPENDED"):
    """Plan one phase-appropriate iteration. Returns an int exit code.

    Injected callables (cycle.py wires the real ones; tests pass fakes):
      - ``dispatch_objectives(instruction, system_prompt) -> int`` — the sub-run
        that writes ``.openup/iteration-objectives.json``.
      - ``dispatch_spec(lane_id, instruction) -> int`` — the sub-run that writes
        ``docs/changes/<lane_id>/plan.md``.
      - ``run_gates() -> (ok, report)`` — fence + check-docs on the repo.
      - ``git_commit(paths, message) -> None`` — stage + commit (raises on error).
      - ``mint_id(phase) -> iteration_id`` (e.g. ``I1``).
      - ``activities_for(phase) -> list[{name, role, skills}]``.
      - ``reserve_id(prefix, session) -> lane_id`` (e.g. ``I1-001``).
      - ``partition(candidates) -> list[list[str]]`` — T-079 clusters.
      - ``roadmap_pending() -> list[str]`` — pending roadmap titles, in order.
      - ``lifecycle() -> {phase, milestone, criteria}``.
      - ``run_task(task_def, instruction) -> int`` (T-106) — a bounded authoring
        sub-run driven by a task def (a generic system prompt, no procedure file
        read); stamps the def's typed artifact on success.
      - ``task_defs`` — the committed task library ``{id: def}`` (from
        ``openup-process-map.py load_tasks``); the direct path resolves each
        activity ``tasks:`` id against it.
    """
    import sys as _sys
    log = log or (lambda m: None)
    print_ = print_ or (lambda m: (_sys.stdout.write(m + "\n"), _sys.stdout.flush()))
    if phase not in AUTHORING_PHASES:
        log("plan-iteration: phase %r is not an authoring phase — not planned "
            "here (single-row promote handles it)" % phase)
        return PI_STEP

    # 0. Map-driven input gate (T-101): before minting anything, ensure every
    # activity's declared requires_input exists. The first missing one is
    # scaffolded (marker-guarded template) and the cycle suspends — the human
    # provides it and re-runs. This replaces the hardcoded brief bootstrap with a
    # data-driven, process-agnostic affordance.
    activities = activities_for(phase) or []
    missing = _first_missing_input(root, activities)
    if missing:
        path, describe = missing
        _scaffold_required_input(root, path, describe)
        log("plan-iteration: activity input missing — scaffolded %s, awaiting fill"
            % path)
        print_("%s — fill %s (%s; a template is there), then re-run"
               % (suspend_sentinel, path, describe or "required input"))
        return PI_SUSPEND

    iteration = (mint_id(phase) or "").strip()
    if not iteration:
        log("plan-iteration: could not mint an iteration id for %s" % phase)
        return PI_CONFIG
    log("plan-iteration: planning iteration %s (%s)" % (iteration, phase))

    # 1. Objectives — one bounded sub-run.
    status = lifecycle() or {}
    facts = build_objectives_input(
        phase, status.get("milestone"), status.get("criteria", []),
        activities, roadmap_pending() or [])
    instruction = render_objectives_instruction(facts)
    system_prompt = OBJECTIVES_SYSTEM_PROMPT % {
        "objectives": OBJECTIVES_REL.as_posix(), "sentinel": OBJECTIVES_SENTINEL}
    rc = dispatch_objectives(instruction, system_prompt)
    if rc == PI_SUSPEND:
        return PI_SUSPEND
    if rc != 0:
        log("plan-iteration: objectives sub-run failed (exit %d)" % rc)
        return rc if rc in (PI_CONFIG,) else PI_STEP
    objectives = read_objectives(root)
    if not objectives:
        log("plan-iteration: no valid objectives file (%s) — aborting, nothing "
            "committed" % OBJECTIVES_REL.as_posix())
        return PI_STEP
    log("plan-iteration: %d objective(s) chosen" % len(objectives))

    # 2. Lanes from activities-for (code) + partition (T-079).
    candidate_lanes = generate_lanes(activities)
    if not candidate_lanes:
        log("plan-iteration: phase %s has no authoring activities — nothing to "
            "plan" % phase)
        return PI_STEP

    # 3. Per activity: an `execution: direct` authoring activity RUNS its procedure
    #    directly (no spec sub-run, no change-folder lane) — the model only authors
    #    (reliable), navigation stays deterministic; a `spec-then-execute` activity
    #    keeps the T-090 reserve-id + spec-authoring lane flow (traced by the
    #    iteration-plan instance). Direct activities are recorded in the instance
    #    body, not as `traces-from` work items (open question 2).
    prefix = "%s-" % iteration
    lane_ids, lane_touches, direct_done = [], [], []
    for lane in candidate_lanes:
        if lane.get("execution") == "direct":
            # T-106: iterate the activity's ordered task-library defs, one bounded
            # authoring sub-run each (generic system prompt, no procedure file
            # read). initiate-project runs [develop-technical-vision,
            # author-initial-roadmap] — vision body, then the roadmap.
            if run_task is None:
                log("plan-iteration: activity %s is execution:direct but no "
                    "task runner was wired — aborting" % lane["activity"])
                return PI_CONFIG
            task_ids = lane.get("tasks") or []
            if not task_ids:
                log("plan-iteration: direct activity %s has no tasks: wired in the "
                    "process map — aborting" % lane["activity"])
                return PI_CONFIG
            defs = task_defs or {}
            for tid in task_ids:
                tdef = defs.get(tid)
                if not tdef:
                    log("plan-iteration: task %r (activity %s) not in the task "
                        "library — aborting" % (tid, lane["activity"]))
                    return PI_CONFIG
                instruction = render_task_instruction(root, tdef, objectives)
                log("plan-iteration: running task %s (%s → %s) for activity %s"
                    % (tid, tdef.get("artifact"), tdef.get("output_path"),
                       lane["activity"]))
                rc = run_task(tdef, instruction)
                if rc == PI_SUSPEND:
                    return PI_SUSPEND
                if rc != 0:
                    log("plan-iteration: task %s (activity %s) failed (exit %d) — "
                        "aborting" % (tid, lane["activity"], rc))
                    return rc if rc in (PI_CONFIG,) else PI_STEP
            # T-108: the direct outputs (stamped artifact + companions like the
            # initial roadmap) must be durable the moment they exist — gate,
            # then commit the whole docs/ delta, same discipline as the lane
            # specs below. An uncommitted vision/roadmap is invisible to the
            # board and lost on a crash (observed live on my-product).
            ok, report = run_gates()
            if not ok:
                log("plan-iteration: gates failed after direct activity %s — "
                    "aborting, nothing committed:\n%s"
                    % (lane["activity"], report))
                return PI_STEP
            git_commit(["docs/"],
                       "docs(%s): %s — authored via task defs [%s]"
                       % (iteration, lane["activity"], iteration))
            log("plan-iteration: %s done — outputs gated and committed"
                % lane["activity"])
            direct_done.append(lane["activity"])
            continue
        lid = (reserve_id(prefix, iteration) or "").strip()
        if not lid:
            log("plan-iteration: could not reserve a lane id under %s" % prefix)
            return PI_CONFIG
        instruction = LANE_SPEC_CONTRACT % {
            "lane": lid, "iteration": iteration, "activity": lane["activity"],
            "role": lane["role"], "skill": lane["skill"],
            "objectives": "\n".join("- %s" % o for o in objectives)}
        rc = dispatch_spec(lid, instruction)
        if rc == PI_SUSPEND:
            return PI_SUSPEND
        if rc != 0:
            log("plan-iteration: spec sub-run for %s failed (exit %d) — "
                "aborting before the iteration is recorded" % (lid, rc))
            return rc if rc in (PI_CONFIG,) else PI_STEP
        plan_rel = "docs/changes/%s/plan.md" % lid
        if not (Path(root) / plan_rel).exists():
            log("plan-iteration: spec sub-run for %s produced no %s — aborting"
                % (lid, plan_rel))
            return PI_STEP
        ok, report = run_gates()
        if not ok:
            log("plan-iteration: gates failed after authoring %s — aborting:\n%s"
                % (lid, report))
            return PI_STEP
        git_commit(["docs/changes/%s" % lid],
                   "docs(%s): author lane spec via plan-iteration [%s]"
                   % (lid, iteration))
        lane_ids.append(lid)
        lane_touches.append({"id": lid, "touches": ["docs/changes/%s/" % lid],
                             "depends-on": []})
        log("plan-iteration: authored lane %s (%s)" % (lid, lane["activity"]))

    # 4. Partition (T-079) — recorded for observability; the board picks the top
    #    collision-free lane next regardless. A single cluster is the common case.
    try:
        clusters = partition(lane_touches)
        log("plan-iteration: %d lane(s) in %d cluster(s)"
            % (len(lane_ids), len(clusters or [[]])))
    except Exception as e:  # partition is advisory here; never block the plan
        log("plan-iteration: partition skipped (%s)" % e)

    # 5. Write the iteration-plan instance (traces the lanes) + gate + commit.
    inst_rel = iteration_plan_path(phase, iteration).as_posix()
    inst_path = Path(root) / inst_rel
    inst_path.parent.mkdir(parents=True, exist_ok=True)
    inst_path.write_text(
        render_iteration_plan_instance(phase, iteration, lane_ids, objectives,
                                       direct_done=direct_done),
        encoding="utf-8")
    ok, report = run_gates()
    if not ok:
        log("plan-iteration: gates failed after writing the iteration-plan "
            "instance — aborting:\n%s" % report)
        return PI_STEP
    git_commit([inst_rel],
               "docs(%s): iteration-plan instance via plan-iteration [%s]"
               % (iteration, iteration))
    log("plan-iteration: iteration %s planned (%d lane(s), %d direct); re-resolve "
        "continues" % (iteration, len(lane_ids), len(direct_done)))
    return PI_OK

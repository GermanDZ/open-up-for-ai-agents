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
    activity name, its role hat, and its first authoring skill. Activities with
    no skill (e.g. ``ongoing-tasks``) are skipped — nothing to author."""
    lanes = []
    for a in activities:
        skills = a.get("skills") or []
        if not skills:
            continue
        lanes.append({"activity": a.get("name"), "role": a.get("role"),
                      "skill": skills[0]})
    return lanes


def iteration_plan_path(phase, iteration):
    return Path("docs") / "phases" / phase / ("iteration-%s-plan.md" % iteration)


def render_iteration_plan_instance(phase, iteration, lane_ids, objectives):
    """The iteration-plan work-product instance (typed; traces its lanes)."""
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
    fm += ["- %s" % lid for lid in lane_ids]
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
                       log=None):
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
    """
    log = log or (lambda m: None)
    if phase not in AUTHORING_PHASES:
        log("plan-iteration: phase %r is not an authoring phase — not planned "
            "here (single-row promote handles it)" % phase)
        return PI_STEP

    iteration = (mint_id(phase) or "").strip()
    if not iteration:
        log("plan-iteration: could not mint an iteration id for %s" % phase)
        return PI_CONFIG
    log("plan-iteration: planning iteration %s (%s)" % (iteration, phase))

    # 1. Objectives — one bounded sub-run.
    status = lifecycle() or {}
    activities = activities_for(phase) or []
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

    # 3. Reserve an iteration-prefixed id per lane; author its spec; gate; commit.
    prefix = "%s-" % iteration
    lane_ids, lane_touches = [], []
    for lane in candidate_lanes:
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
        render_iteration_plan_instance(phase, iteration, lane_ids, objectives),
        encoding="utf-8")
    ok, report = run_gates()
    if not ok:
        log("plan-iteration: gates failed after writing the iteration-plan "
            "instance — aborting:\n%s" % report)
        return PI_STEP
    git_commit([inst_rel],
               "docs(%s): iteration-plan instance via plan-iteration [%s]"
               % (iteration, iteration))
    log("plan-iteration: iteration %s planned (%d lane(s)); re-resolve picks the "
        "first lane" % (iteration, len(lane_ids)))
    return PI_OK

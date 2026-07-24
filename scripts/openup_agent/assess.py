"""assess.py — the cycle engine's assess + milestone paths (T-091).

Two of ``openup-board.py resolve``'s decision paths reach the engine here,
completing ``/openup-next`` parity:

  - **assess-iteration** (§1c-assess): a T-090-planned iteration whose committed
    lanes are all delivered and whose iteration-plan instance has no
    ``## Assessment`` yet. Done-ness is already code (it fired the decision); the
    genuine judgment is grading the **non-derivable** evaluation criteria
    (objectives met? demo verdict) against repo evidence — ONE bounded sub-run
    whose structured output the engine appends as an ``## Assessment`` section
    (the assessed marker ``resolve`` reads) and commits. Emits the ``ADVANCED``
    sentinel. It records evidence; it does **not** auto-enqueue discovered work as
    roadmap scope (that stays behind the T-094 consent gate) and never advances a
    phase.

  - **milestone-review** (§1c-milestone): the roadmap is drained and the phase's
    exit criteria are met with no milestone record. **Zero LLM** — the engine
    prepares evidence and raises the human go/no-go as a T-074 input-request,
    suspends (exit 5), and remembers the request so a re-run re-suspends without a
    duplicate. It **records evidence and pauses; it never advances the phase** —
    the human go/no-go + ``openup-lifecycle.py`` own that (exactly
    ``/openup-phase-review``).

Self-contained + stdlib-only: driver-coupled operations (the sub-run, gates,
git-commit, running scripts) are injected, so this module imports nothing from
``cycle`` and is unit-testable with fakes.
"""

import json
import re
import sys
from pathlib import Path

# Exit codes mirror cycle.py's.
AS_OK = 0
AS_CONFIG = 2
AS_SUSPEND = 5
AS_STEP = 8

ASSESSMENT_REL = Path(".openup") / "assessment.json"
ASSESSMENT_SENTINEL = "OPENUP-ASSESSMENT: GRADED"

GRADING_SYSTEM_PROMPT = """\
You are the OpenUP iteration assessor (Assess Results). Grade the iteration
described in the user message against its evaluation criteria, using ONLY repo
evidence (delivered lanes, passing tests, landed artifacts) — not intention.

You do NOT change code or roadmap. Your ONLY output is a decision file. Use
write_file to write %(assessment)s with EXACTLY this JSON shape:

{
  "criteria": [{"criterion": "<text>", "grade": "met|unmet", "evidence": "<what in the repo shows it>"}],
  "demo": ["<work items genuinely complete AND acceptance-tested>"],
  "excluded": ["<committed item excluded from demo + why>"],
  "discovered": ["<work/defects surfaced this iteration, not yet captured>"],
  "verdict": "<one line: objectives met / partially / carried forward>"
}

Rules:
- Grade every evaluation criterion; cite concrete evidence.
- Demo ONLY items that are both complete and acceptance-tested; exclude the rest
  with a reason.
- List discovered work as notes — do NOT edit the roadmap yourself.

When the file is written, reply with NO tool calls and put this exact sentinel on
its own line: %(sentinel)s
""".rstrip()

MILESTONE_QUESTION = (
    "Phase '%(phase)s' (cycle %(cycle)s) has met its machine-checkable exit "
    "criteria and the roadmap is drained. Milestone go/no-go: advance the phase? "
    "Evidence:\n%(evidence)s")

_META_REL = Path(".openup") / "cycle.json"


# --------------------------------------------------------------------------
# Assess helpers (pure)
# --------------------------------------------------------------------------
def render_grading_instruction(instance_text, evidence=""):
    """The grading sub-run's instruction. T-120: when the engine assembles a
    deterministic ``evidence`` bundle (delivered lanes + their artifact paths),
    inline it so the grader needs no discovery grep to find repo evidence."""
    head = (
        "The committed lanes of this iteration are ALL delivered (that is why "
        "assessment is due). Grade it against its evaluation criteria using repo "
        "evidence, and write the decision file.\n\n")
    body = ("Iteration-plan instance (objectives, committed work items, "
            "evaluation criteria):\n\n" + instance_text)
    if evidence:
        return head + evidence + "\n\n" + body
    return head + body


def _read_frontmatter(path):
    """Minimal front-matter reader for evidence gathering: scalar ``title`` /
    ``status`` plus the ``touches:`` list. Self-contained (assess.py imports
    nothing from cycle)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text[3:]
    fm, in_touches, touches = {}, False, []
    for line in block.splitlines():
        if in_touches:
            m = re.match(r"\s+-\s+(.*)$", line)
            if m:
                touches.append(m.group(1).strip().strip("\"'"))
                continue
            in_touches = False
        m = re.match(r"([\w-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "touches" and not val:
            in_touches = True
            continue
        fm[key] = val.strip("\"'")
    fm["touches"] = touches
    return fm


def _iteration_evidence(root, iteration):
    """Deterministic grading evidence: the iteration's delivered lanes (active or
    archived change folders under the ``<iteration>-`` prefix) with their
    status/title and declared artifact paths — so the grader needs no discovery
    grep (T-120). Returns '' when nothing is found (grader falls back to the
    instance text alone)."""
    root = Path(root)
    changes = root / "docs" / "changes"
    prefix = "%s-" % iteration
    lines = []
    for base in (changes, changes / "archive"):
        if not base.is_dir():
            continue
        for plan in sorted(base.glob("%s*/plan.md" % prefix)):
            fm = _read_frontmatter(plan)
            lid = plan.parent.name
            status = (fm.get("status") or "?").strip()
            title = (fm.get("title") or "").strip()
            lines.append("- %s (%s) — %s" % (lid, status, title))
            for t in fm.get("touches") or []:
                lines.append("    · %s" % t)
    if not lines:
        return ""
    return ("Delivered lanes and their declared artifacts (repo evidence):\n"
            + "\n".join(lines))


def read_assessment(root):
    """Parse .openup/assessment.json → normalized dict or None."""
    path = Path(root) / ASSESSMENT_REL
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, dict):
        return None
    crits = raw.get("criteria")
    if not isinstance(crits, list) or not crits:
        return None
    norm = []
    for c in crits:
        if not isinstance(c, dict) or not str(c.get("criterion", "")).strip():
            continue
        grade = str(c.get("grade", "")).strip().lower()
        norm.append({"criterion": str(c["criterion"]).strip(),
                     "grade": "met" if grade == "met" else "unmet",
                     "evidence": str(c.get("evidence", "")).strip()})
    if not norm:
        return None

    def _list(k):
        v = raw.get(k) or []
        return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []

    return {"criteria": norm, "demo": _list("demo"), "excluded": _list("excluded"),
            "discovered": _list("discovered"),
            "verdict": str(raw.get("verdict", "")).strip() or "(no verdict)"}


def render_assessment_section(assessment):
    """The deterministic ``## Assessment`` section appended to the instance."""
    lines = ["", "## Assessment", ""]
    lines.append("**Verdict**: %s" % assessment["verdict"])
    lines += ["", "### Evaluation criteria", ""]
    for c in assessment["criteria"]:
        mark = "✅" if c["grade"] == "met" else "❌"
        ev = " — %s" % c["evidence"] if c["evidence"] else ""
        lines.append("- %s %s%s" % (mark, c["criterion"], ev))
    if assessment["demo"]:
        lines += ["", "### Demo scope", ""]
        lines += ["- %s" % d for d in assessment["demo"]]
    if assessment["excluded"]:
        lines += ["", "### Excluded from demo", ""]
        lines += ["- %s" % e for e in assessment["excluded"]]
    if assessment["discovered"]:
        lines += ["", "### Discovered work (fed back — enqueue via the consent gate)", ""]
        lines += ["- %s" % d for d in assessment["discovered"]]
    lines.append("")
    return "\n".join(lines)


def _instance_rel(decision):
    lane = decision.get("lane") or {}
    return lane.get("plan")


# --------------------------------------------------------------------------
# Assess orchestration
# --------------------------------------------------------------------------
def run_assess(root, decision, *, dispatch, run_gates, git_commit,
               log=None, print_=None):
    """Grade the iteration and record ``## Assessment``. Returns an exit code."""
    root = Path(root)
    log = log or (lambda m: None)
    print_ = print_ or (lambda m: (sys.stdout.write(m + "\n"), sys.stdout.flush()))

    inst_rel = _instance_rel(decision)
    iteration = (decision.get("lane") or {}).get("task") or "?"
    if not inst_rel:
        log("assess: decision carried no iteration-plan instance path")
        return AS_CONFIG
    inst_path = root / inst_rel
    if not inst_path.exists():
        log("assess: iteration-plan instance %s not found" % inst_rel)
        return AS_CONFIG

    # clear any stale assessment file, then grade (one bounded sub-run).
    stale = root / ASSESSMENT_REL
    try:
        stale.unlink()
    except OSError:
        pass
    evidence = _iteration_evidence(root, iteration)
    instruction = render_grading_instruction(
        inst_path.read_text(encoding="utf-8"), evidence)
    system_prompt = GRADING_SYSTEM_PROMPT % {
        "assessment": ASSESSMENT_REL.as_posix(), "sentinel": ASSESSMENT_SENTINEL}
    rc = dispatch(instruction, system_prompt)
    if rc == AS_SUSPEND:
        return AS_SUSPEND
    if rc != 0:
        log("assess: grading sub-run failed (exit %d)" % rc)
        return rc if rc in (AS_CONFIG,) else AS_STEP

    assessment = read_assessment(root)
    if not assessment:
        log("assess: no valid assessment file (%s) — aborting, nothing recorded"
            % ASSESSMENT_REL.as_posix())
        return AS_STEP

    # append the ## Assessment section deterministically.
    text = inst_path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    inst_path.write_text(text + render_assessment_section(assessment),
                         encoding="utf-8")
    ok, report = run_gates()
    if not ok:
        log("assess: gates failed after recording the assessment — aborting:\n%s"
            % report)
        return AS_STEP
    git_commit([inst_rel],
               "docs(%s): record iteration assessment via cycle [%s]"
               % (iteration, iteration))
    log("assess: iteration %s assessed (%d criteria; verdict: %s)"
        % (iteration, len(assessment["criteria"]), assessment["verdict"]))
    print_("OPENUP-NEXT: ADVANCED — assessed %s" % iteration)
    return AS_OK


# --------------------------------------------------------------------------
# Milestone orchestration (zero LLM)
# --------------------------------------------------------------------------
def _read_meta(root):
    path = Path(root) / _META_REL
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_milestone_meta(root, **fields):
    path = Path(root) / _META_REL
    meta = _read_meta(root)
    ms = dict(meta.get("milestone") or {})
    ms.update(fields)
    meta["milestone"] = ms
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _request_open(root, rel_path):
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


def _milestone_evidence(decision):
    phase = (decision.get("lane") or {}).get("task") or decision.get("phase") or "?"
    cycle = decision.get("cycle")
    reason = decision.get("reason") or ""
    return phase, cycle, reason


def run_milestone(root, decision, *, runner, log=None, print_=None,
                  suspend_sentinel="OPENUP-AGENT: SUSPENDED"):
    """Prepare evidence + raise the human go/no-go as an input-request, suspend
    (exit 5). Re-suspends an already-open request without duplicating. Zero LLM;
    never advances the phase."""
    root = Path(root)
    log = log or (lambda m: None)
    print_ = print_ or (lambda m: (sys.stdout.write(m + "\n"), sys.stdout.flush()))

    ms = _read_meta(root).get("milestone") or {}
    existing = ms.get("request")
    if _request_open(root, existing):
        log("milestone: go/no-go still open — re-suspending %s" % existing)
        print_("%s — %s" % (suspend_sentinel, existing))
        return AS_SUSPEND

    phase, cycle, reason = _milestone_evidence(decision)
    question = MILESTONE_QUESTION % {"phase": phase, "cycle": cycle,
                                     "evidence": reason}
    rc, out = runner(root, ["scripts/openup-input.py", "request",
                            "--title", "Milestone go/no-go: %s phase" % phase,
                            "--question", question,
                            "--option", "GO", "--option", "NO-GO", "--json"])
    if rc != 0:
        log("milestone: could not create the go/no-go input-request:\n%s"
            % out.strip()[:800])
        return AS_STEP
    try:
        request = json.loads(out)["request"]
    except (json.JSONDecodeError, KeyError, TypeError):
        request = out.strip().splitlines()[-1] if out.strip() else ""
    _write_milestone_meta(root, request=request, phase=phase, cycle=cycle)
    log("milestone: %s phase exit criteria met — awaiting human go/no-go in %s"
        % (phase, request))
    print_("%s — %s" % (suspend_sentinel, request))
    return AS_SUSPEND

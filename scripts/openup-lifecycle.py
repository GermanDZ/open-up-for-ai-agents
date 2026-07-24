#!/usr/bin/env python3
"""OpenUP project-lifecycle status — derived, read-only (T-075).

The outer, stakeholder-level layer of OpenUP's three-layer state machine
(project lifecycle -> iteration -> micro-increment). Sibling to
``openup-board.py``: it *derives* the current phase and per-milestone criteria
state from repo facts and recorded human go/no-go decisions — it never authors
them.

Two inputs decide the answer:

  * **Milestone decision records** — ``docs/product/milestones/<phase>-<cycle>.md``,
    each recording a human go/no-go at a phase boundary (LCO/LCA/IOC/PR). The
    *record* is authoritative for "phase advanced"; this script only reads it.
    (Records are authored by ``/openup-phase-review`` — never by this script.)
  * **Work-product instances + roadmap facts** — used only to compute the
    per-milestone *criteria* state (what the current milestone still needs),
    never to decide the phase.

Honesty rule (exploration §"Criteria detection fidelity"): a criterion is
reported ``met`` / ``unmet`` only when a script can verify it mechanically
(a typed work-product instance exists, per T-038 traceability frontmatter).
Criteria that require human judgment ("architecture validated" = a *tested*
skeleton, "stakeholder concurrence") are reported ``human-judgment`` — never
auto-``met``.

When no milestone record exists yet, ``phase`` falls back to the value already
in ``.openup/state.json`` (flagged ``source: state-fallback``) — this script
does NOT invent retroactive go/no-go history.

Subcommands
  status [--json]   Print the derived phase, cycle, and milestone criteria.
  stamp-phase       Write the derived phase into .openup/state.json (idempotent).

Exit codes
  0  success
  2  usage / structure error (bad args, malformed milestone record)
  3  no state file (stamp-phase with nothing to stamp)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Reuse openup-claims.py frontmatter parsing (hyphenated filename -> importlib),
# the same shared implementation openup-board.py loads, so lifecycle and board
# read frontmatter identically.
_CLAIMS_PATH = SCRIPT_DIR / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_STATE = 3

# Ordered project lifecycle. `released` is the terminal state after the
# Transition / Product-Release milestone.
PHASES = ["inception", "elaboration", "construction", "transition"]
PHASE_ORDER = {p: i for i, p in enumerate(PHASES)}
NEXT_PHASE = {
    "inception": "elaboration",
    "elaboration": "construction",
    "construction": "transition",
    "transition": "released",
}

DECISIONS = {"GO", "NO-GO", "CONDITIONAL"}

# Statuses on a typed instance that require human judgment are never asserted
# by this script; artifact criteria only need the instance to exist and carry
# a status (T-038 maturity enum).

# Milestone model — KB §2 (phase -> milestone -> exit criteria). Each criterion:
#   id       stable slug
#   desc     human-readable
#   kind     "artifact" | "human" | "roadmap-clear"
#   types    (artifact only) accepted `type:` frontmatter values
#   keywords (artifact only) filename hints for artifacts with no spine `type:`
#            (risk-list, architecture-notebook, test-plan have no spine type)
MILESTONES = {
    "inception": {
        "name": "Lifecycle Objectives (LCO)",
        "criteria": [
            {"id": "vision_defined", "desc": "Vision / scope captured",
             "kind": "artifact", "types": {"vision"}, "keywords": ("vision",)},
            {"id": "requirements_outlined", "desc": "Key functionality outlined (use cases)",
             "kind": "artifact", "types": {"use-case"}, "keywords": ("use-case", "use_case")},
            {"id": "risk_list_present", "desc": "Initial risk list identified",
             "kind": "artifact", "types": set(), "keywords": ("risk-list", "risk_list")},
            {"id": "scope_agreed", "desc": "Stakeholders agree on scope + objectives (proceed?)",
             "kind": "human"},
        ],
    },
    "elaboration": {
        "name": "Lifecycle Architecture (LCA)",
        "criteria": [
            {"id": "architecture_baselined", "desc": "Architecture notebook / significant decisions captured",
             "kind": "artifact", "types": {"decision"}, "keywords": ("architecture",)},
            {"id": "test_approach_defined", "desc": "Test plan / test cases drafted",
             "kind": "artifact", "types": {"test-case"}, "keywords": ("test-plan", "test_plan")},
            {"id": "architecture_validated", "desc": "Executable architecture validated (tested skeleton)",
             "kind": "human"},
            {"id": "risk_acceptable", "desc": "Remaining risk + value-so-far acceptable",
             "kind": "human"},
        ],
    },
    "construction": {
        "name": "Initial Operational Capability (IOC)",
        "criteria": [
            {"id": "functionality_complete", "desc": "All planned work items delivered (no open change folders)",
             "kind": "roadmap-clear"},
            {"id": "alpha_tested", "desc": "Alpha testing done",
             "kind": "human"},
            {"id": "ready_for_beta", "desc": "Product close enough to release for beta",
             "kind": "human"},
        ],
    },
    "transition": {
        "name": "Product Release (PR)",
        "criteria": [
            {"id": "deployment_complete", "desc": "Deployment complete",
             "kind": "human"},
            {"id": "stakeholder_acceptance", "desc": "Customer reviews + accepts deliverables",
             "kind": "human"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Milestone decision records
# ---------------------------------------------------------------------------

def milestones_dir(root: Path) -> Path:
    return root / "docs" / "product" / "milestones"


def read_milestone_records(root: Path) -> list[dict]:
    """Parse every ``docs/product/milestones/<phase>-<cycle>.md`` record.

    Returns dicts with keys: phase, cycle, milestone, decision, date,
    decided_by, path. Raises ``ValueError`` (-> exit 2) on a malformed record
    so a bad file never yields a silently-wrong phase.
    """
    mdir = milestones_dir(root)
    records: list[dict] = []
    if not mdir.is_dir():
        return records
    for p in sorted(mdir.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        fm = claims.parse_frontmatter(p)
        phase = str(fm.get("phase", "")).strip().lower()
        decision = str(fm.get("decision", "")).strip().upper()
        cycle_raw = fm.get("cycle", "")
        if phase not in PHASE_ORDER:
            raise ValueError(
                f"milestone record {p.name}: 'phase' must be one of {PHASES}, got {phase!r}")
        if decision not in DECISIONS:
            raise ValueError(
                f"milestone record {p.name}: 'decision' must be one of "
                f"{sorted(DECISIONS)}, got {decision or '(missing)'!r}")
        try:
            cycle = int(str(cycle_raw).strip())
        except (TypeError, ValueError):
            raise ValueError(
                f"milestone record {p.name}: 'cycle' must be an integer, got {cycle_raw!r}")
        records.append({
            "phase": phase, "cycle": cycle, "decision": decision,
            "milestone": str(fm.get("milestone", "")).strip(),
            "date": str(fm.get("date", "")).strip(),
            "decided_by": str(fm.get("decided-by", fm.get("decided_by", ""))).strip(),
            "path": str(p.relative_to(root)),
        })
    return records


def resolve_phase(records: list[dict], state_phase: str | None) -> tuple[str, int, str]:
    """Return (phase, cycle, source).

    Authoritative source is the milestone records. With none, fall back to the
    phase recorded in state (``source: state-fallback``) — no fabricated history.
    """
    if not records:
        phase = (state_phase or "inception").strip().lower()
        if phase not in PHASE_ORDER and phase != "released":
            phase = "inception"
        return phase, 1, "state-fallback"

    def key(r: dict) -> tuple[int, int]:
        return (PHASE_ORDER[r["phase"]], r["cycle"])

    go = [r for r in records if r["decision"] == "GO"]
    if not go:
        # Still inside the phase of the most-recent record (awaiting go/no-go).
        latest = max(records, key=key)
        return latest["phase"], latest["cycle"], "milestone"

    latest_go = max(go, key=key)
    nxt = NEXT_PHASE[latest_go["phase"]]
    if nxt == "released":
        return "released", latest_go["cycle"], "milestone"
    return nxt, latest_go["cycle"], "milestone"


# ---------------------------------------------------------------------------
# Work-product instance scan (for criteria)
# ---------------------------------------------------------------------------

# docs subtrees that never hold product work-product instances.
_SKIP_DIRS = {"changes", "agent-logs", "status-notes", "explorations", "plans",
              "iteration-retrospectives", "input-requests"}


def scan_instances(root: Path) -> list[dict]:
    """Every ``docs/**/*.md`` carrying typed traceability frontmatter (T-038):
    returns dicts {type, status, name (filename stem), path}."""
    docs = root / "docs"
    out: list[dict] = []
    if not docs.is_dir():
        return out
    for p in docs.rglob("*.md"):
        rel_parts = p.relative_to(docs).parts
        if rel_parts and rel_parts[0] in _SKIP_DIRS:
            continue
        if "milestones" in rel_parts:
            continue
        fm = claims.parse_frontmatter(p)
        typ = str(fm.get("type", "")).strip().lower()
        if not typ or typ == "template":
            continue
        out.append({
            "type": typ,
            "status": str(fm.get("status", "")).strip().lower(),
            "name": p.stem.lower(),
            "path": str(p.relative_to(root)),
        })
    return out


def _artifact_met(crit: dict, instances: list[dict]) -> bool:
    types = crit.get("types") or set()
    keywords = crit.get("keywords") or ()
    for inst in instances:
        if types and inst["type"] in types:
            return True
        if keywords and any(k in inst["name"] for k in keywords) and inst["status"]:
            return True
    return False


def _roadmap_clear(root: Path) -> bool:
    """True when no change folder is still open (all delivered/archived).

    Mechanical proxy for "all functionality developed": every
    ``docs/changes/<id>/plan.md`` (archive excluded) has a done status.
    """
    cdir = root / "docs" / "changes"
    if not cdir.is_dir():
        return True
    for sub in cdir.iterdir():
        if not sub.is_dir() or sub.name == "archive":
            continue
        plan = sub / "plan.md"
        if not plan.exists():
            continue
        fm = claims.parse_frontmatter(plan)
        status = str(fm.get("status", "")).strip().lower()
        if status not in {"done", "verified", "completed"}:
            return False
    return True


def evaluate_criteria(phase: str, root: Path, instances: list[dict]) -> list[dict]:
    milestone = MILESTONES.get(phase)
    if not milestone:
        return []
    results = []
    for crit in milestone["criteria"]:
        kind = crit["kind"]
        if kind == "human":
            state = "human-judgment"
        elif kind == "roadmap-clear":
            state = "met" if _roadmap_clear(root) else "unmet"
        else:  # artifact
            state = "met" if _artifact_met(crit, instances) else "unmet"
        results.append({"id": crit["id"], "desc": crit["desc"], "state": state})
    return results


# ---------------------------------------------------------------------------
# State (phase cache)
# ---------------------------------------------------------------------------

def state_dir(root: Path, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return root / ".openup"


def read_state(sdir: Path) -> dict | None:
    p = sdir / "state.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def write_state(sdir: Path, state: dict) -> None:
    p = sdir / "state.json"
    p.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def compute_status(root: Path, sdir: Path) -> dict:
    state = read_state(sdir)
    state_phase = state.get("phase") if state else None
    records = read_milestone_records(root)
    phase, cycle, source = resolve_phase(records, state_phase)
    instances = scan_instances(root)
    criteria = evaluate_criteria(phase, root, instances) if phase != "released" else []
    milestone = MILESTONES.get(phase, {}).get("name") if phase != "released" else None
    return {
        "phase": phase,
        "cycle": cycle,
        "source": source,
        "milestone": milestone,
        "criteria": criteria,
        "records": len(records),
    }


def cmd_status(args) -> int:
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    sdir = state_dir(root, args.state_dir)
    try:
        result = compute_status(root, sdir)
    except ValueError as e:
        sys.stderr.write(f"[lifecycle] {e}\n")
        return EXIT_USAGE
    if args.json:
        print(json.dumps(result, indent=1))
        return EXIT_OK
    src = "" if result["source"] == "milestone" else f"  (source: {result['source']})"
    print(f"Phase: {result['phase']}  cycle {result['cycle']}{src}")
    if result["milestone"]:
        print(f"Milestone: {result['milestone']}")
    for c in result["criteria"]:
        mark = {"met": "✓", "unmet": "✗", "human-judgment": "?"}[c["state"]]
        print(f"  [{mark}] {c['id']}: {c['desc']} — {c['state']}")
    return EXIT_OK


def cmd_stamp_phase(args) -> int:
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    sdir = state_dir(root, args.state_dir)
    state = read_state(sdir)
    if state is None:
        sys.stderr.write(f"[lifecycle] no state file at {sdir / 'state.json'}\n")
        return EXIT_NO_STATE
    try:
        result = compute_status(root, sdir)
    except ValueError as e:
        sys.stderr.write(f"[lifecycle] {e}\n")
        return EXIT_USAGE
    derived = result["phase"]
    if state.get("phase") == derived:
        print(f"phase already {derived} (no change)")
        return EXIT_OK
    old = state.get("phase")
    state["phase"] = derived
    write_state(sdir, state)
    print(f"phase {old} -> {derived} (stamped from lifecycle status)")
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Derived, read-only OpenUP project-lifecycle status.")
    parser.add_argument("--repo-root", help="Override repo root (default: script's parent).")
    parser.add_argument("--state-dir", help="Override the .openup directory.")
    sub = parser.add_subparsers(dest="command", required=True)

    ps = sub.add_parser("status", help="Print derived phase + milestone criteria.")
    ps.add_argument("--json", action="store_true", help="Emit JSON.")
    ps.set_defaults(func=cmd_status)

    pst = sub.add_parser("stamp-phase", help="Write derived phase into state (idempotent).")
    pst.set_defaults(func=cmd_stamp_phase)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""OpenUP process map loader — the process as data (T-077), read-only.

Reads ``docs-eng-process/process-map.yaml`` (KB §4: phase → activity → role →
skill) so that Plan Iteration (/openup-start-iteration) can generate
phase-appropriate work-item lanes from data instead of a human hand-writing each
roadmap row. Stdlib only — no pyyaml — parsing the small, controlled YAML subset
the map file uses (flow lists ``[a, b]`` and flow maps ``{ k: v }`` under three
top-level sections).

The map file is framework-owned and vendored; the loader resolves it relative to
the repo root, preferring ``docs-eng-process/process-map.yaml`` (canonical) and
falling back to ``scripts/process-map.yaml`` (shipped-into-a-project layout, the
same precedent as ``openup-state.schema.json``).

Subcommands
  activities-for <phase> [--json]   Ordered activities for a phase, each resolved
                                    to its {role, skills}.
  activity <name> [--json]          One activity's {role, skills}.
  phase-letter <phase>              Iteration-id prefix letter (e.g. construction -> C).
  mint-iteration-id <phase>         Stable iteration id <letter><ordinal> (e.g. C3),
                                    repo-monotonic per phase letter.
  validate                          Structural check of the shipped map.

Exit codes
  0  success
  2  usage / structure error (unknown phase/activity, malformed map)
  3  map file not found
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

_MAP_CANDIDATES = (
    "docs-eng-process/process-map.yaml",  # canonical (framework repo)
    "scripts/process-map.yaml",           # shipped-into-a-project fallback
)

KNOWN_ROLES = {
    "analyst",
    "architect",
    "developer",
    "tester",
    "project-manager",
    "product-manager",
}
KNOWN_PHASES = ("inception", "elaboration", "construction", "transition")

# ── Task library (T-105) ─────────────────────────────────────────────────────
# The v1 spine work-product types (mirror scripts/docs-meta.schema.json `type`
# enum) an authoring task def may declare as its `artifact`.
SPINE_TYPES = (
    "vision", "requirement", "work-item", "iteration-plan",
    "use-case", "test-case", "decision",
)
_TASK_CANDIDATES = (
    "docs-eng-process/task-library.yaml",  # canonical (framework repo)
    "scripts/task-library.yaml",           # shipped-into-a-project fallback
)
# Fields on a task def: scalars first, then the two list fields.
_TASK_SCALARS = ("name", "role", "artifact", "output_path", "source")
_TASK_LISTS = ("inputs", "judgment")


class MapError(Exception):
    """Structural problem in the process map (usage error, exit 2)."""


# ── stdlib YAML-subset parsing ──────────────────────────────────────────────

def _strip_comment(line: str) -> str:
    """Drop a trailing ``#`` comment. The map file never puts ``#`` inside a
    value, so a naive split is safe and keeps the parser tiny."""
    hashpos = line.find("#")
    return line[:hashpos] if hashpos != -1 else line


def _split_top_level(body: str, open_ch: str, close_ch: str) -> list:
    """Split ``body`` on commas that are not nested inside ``[]``/``{}``."""
    parts, depth, buf = [], 0, []
    for ch in body:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _parse_flow_list(value: str) -> list:
    """``[a, b, c]`` -> ['a','b','c']; ``[]`` -> []."""
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        raise MapError(f"expected a flow list, got: {value!r}")
    return _split_top_level(value[1:-1], "[", "]")


def _parse_flow_map(value: str) -> dict:
    """``{ role: x, skills: [a, b] }`` -> {'role':'x','skills':['a','b']}."""
    value = value.strip()
    if not (value.startswith("{") and value.endswith("}")):
        raise MapError(f"expected a flow map, got: {value!r}")
    out = {}
    for pair in _split_top_level(value[1:-1], "{", "}"):
        if ":" not in pair:
            raise MapError(f"malformed key: value pair: {pair!r}")
        key, _, val = pair.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("["):
            out[key] = _parse_flow_list(val)
        elif val.startswith("{"):
            out[key] = _parse_flow_map(val)        # nested map (e.g. requires_input) — T-100
        else:
            out[key] = _unquote(val)
    return out


def _unquote(val: str) -> str:
    """Strip a single pair of matching surrounding quotes from a scalar (YAML
    would); leaves an unquoted scalar untouched."""
    val = val.strip()
    if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
        return val[1:-1]
    return val


def load_map(root: Path) -> dict:
    """Parse the process map into {phases, activities, phase_letters}."""
    path = None
    for rel in _MAP_CANDIDATES:
        cand = root / rel
        if cand.exists():
            path = cand
            break
    if path is None:
        raise FileNotFoundError(
            "process-map.yaml not found (looked in "
            + ", ".join(_MAP_CANDIDATES) + ")"
        )

    phases, activities, phase_letters = {}, {}, {}
    section = None
    for raw in path.read_text().splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indented = line[0] in " \t"
        if not indented and stripped.endswith(":"):
            key = stripped[:-1].strip()
            section = key if key in ("phases", "activities", "phase_letters") else None
            continue
        if section is None or not indented:
            continue
        if ":" not in stripped:
            raise MapError(f"malformed line under {section}: {stripped!r}")
        name, _, val = stripped.partition(":")
        name, val = name.strip(), val.strip()
        if section == "phases":
            phases[name] = _parse_flow_list(val)
        elif section == "activities":
            activities[name] = _parse_flow_map(val)
        elif section == "phase_letters":
            phase_letters[name] = val

    return {"phases": phases, "activities": activities, "phase_letters": phase_letters}


# ── queries ─────────────────────────────────────────────────────────────────

# Default execution mode when an activity does not declare one (T-100). Preserves
# pre-T-100 behavior: a work item is a lane whose spec is authored then executed.
DEFAULT_EXECUTION = "spec-then-execute"
EXECUTION_MODES = ("direct", "spec-then-execute")


def _activity_record(name: str, act: dict) -> dict:
    """Normalize one activity to the exposed record, including the T-100 fields
    ``requires_input`` (a ``{path, describe}`` dict or None) and ``execution``
    (default ``spec-then-execute``)."""
    ri = act.get("requires_input")
    return {
        "name": name,
        "role": act.get("role"),
        "skills": act.get("skills", []),
        "requires_input": ri if isinstance(ri, dict) else None,
        "execution": act.get("execution") or DEFAULT_EXECUTION,
        # T-106: ordered task-library ids driving this activity's authoring
        # sub-runs (the granularity mechanism). Empty ⇒ pre-T-106 procedure path.
        "tasks": act.get("tasks", []),
    }


def activities_for(mp: dict, phase: str) -> list:
    """Ordered activities for a phase, each resolved to {name, role, skills,
    requires_input, execution}."""
    if phase not in mp["phases"]:
        raise MapError(f"unknown phase: {phase!r} (known: {', '.join(mp['phases'])})")
    out = []
    for name in mp["phases"][phase]:
        act = mp["activities"].get(name)
        if act is None:
            raise MapError(f"phase {phase!r} references unknown activity {name!r}")
        out.append(_activity_record(name, act))
    return out


def activity(mp: dict, name: str) -> dict:
    if name not in mp["activities"]:
        raise MapError(f"unknown activity: {name!r}")
    return _activity_record(name, mp["activities"][name])


def phase_letter(mp: dict, phase: str) -> str:
    letter = mp["phase_letters"].get(phase)
    if not letter:
        raise MapError(f"no phase_letters entry for phase {phase!r}")
    return letter


def existing_ordinals(root: Path, letter: str) -> set:
    """All iteration ordinals already used for a phase letter, scanned from repo
    facts (roadmap text + active/archived change-folder names) — e.g. ``C3-001``
    contributes ordinal 3. Legacy ids (``T-077`` — no digit before the dash)
    never match, so they don't inflate the count."""
    ords = set()
    pat = re.compile(rf"\b{re.escape(letter)}(\d+)-\d+\b")
    texts = []
    rm = root / "docs" / "roadmap.md"
    if rm.exists():
        texts.append(rm.read_text(encoding="utf-8", errors="ignore"))
    for base in (root / "docs" / "changes", root / "docs" / "changes" / "archive"):
        if base.is_dir():
            texts.extend(d.name for d in base.iterdir() if d.is_dir())
    for text in texts:
        for m in pat.finditer(text):
            ords.add(int(m.group(1)))
    return ords


def mint_iteration_id(root: Path, mp: dict, phase: str) -> str:
    """A stable iteration id ``<PhaseLetter><ordinal>`` (e.g. ``C3``) for the
    current phase. The ordinal is repo-monotonic per phase letter (max existing
    + 1, or 1) so ids stay globally unique across cycles — no state field needed
    (schema 1; the id is recorded in the iteration-plan instance by R2)."""
    letter = phase_letter(mp, phase)
    ords = existing_ordinals(root, letter)
    return f"{letter}{(max(ords) + 1) if ords else 1}"


def validate(mp: dict, task_ids: set | None = None) -> list:
    """Return a list of structural problems (empty == valid). When ``task_ids``
    is given (the committed task-library ids), every activity ``tasks:`` entry
    must resolve into it (T-106 map wiring)."""
    problems = []
    for name, act in mp["activities"].items():
        tasks = act.get("tasks") or []
        if tasks and not isinstance(tasks, list):
            problems.append(f"activity {name!r} tasks is not a list")
        elif task_ids is not None:
            for tid in tasks:
                if tid not in task_ids:
                    problems.append(
                        f"activity {name!r} tasks references unknown task id {tid!r} "
                        f"(not in task-library.yaml)")
    for phase, acts in mp["phases"].items():
        if phase not in KNOWN_PHASES:
            problems.append(f"phases: unknown phase {phase!r}")
        for name in acts:
            act = mp["activities"].get(name)
            if act is None:
                problems.append(f"phase {phase!r} references undefined activity {name!r}")
                continue
            role = act.get("role")
            if role not in KNOWN_ROLES:
                problems.append(f"activity {name!r} has unknown role {role!r}")
            if "skills" in act and not isinstance(act["skills"], list):
                problems.append(f"activity {name!r} skills is not a list")
            # T-100: gate requires_input + execution.
            ri = act.get("requires_input")
            if ri is not None:
                if not isinstance(ri, dict) or not str(ri.get("path", "")).strip():
                    problems.append(
                        f"activity {name!r} requires_input must be a map with a "
                        f"non-empty 'path'")
            ex = act.get("execution")
            if ex is not None and ex not in EXECUTION_MODES:
                problems.append(
                    f"activity {name!r} execution {ex!r} not in "
                    f"{EXECUTION_MODES}")
            # T-119: the direct path is TASK-driven (T-106), not skill-driven — it
            # runs the activity's ordered `tasks:` defs, never a single procedure.
            # So a direct activity must declare >=1 task; `skills` (Claude Code path)
            # is no longer constrained. (Replaces the obsolete exactly-one-skill rule.)
            if ex == "direct" and len(act.get("tasks", []) or []) < 1:
                problems.append(
                    f"activity {name!r} execution: direct requires >=1 task "
                    f"(the task-def(s) to run); none wired")
        if phase not in mp["phase_letters"]:
            problems.append(f"phase {phase!r} has no phase_letters entry")
    if not mp["phases"]:
        problems.append("no phases defined")
    return problems


# ── Task library (T-105): block parser + validator ──────────────────────────
# task-library.yaml is a two-level block map (no pyyaml): `tasks:` → task-id
# (2-space indent) → field (4-space); list fields (`inputs`, `judgment`) carry
# `- item` entries at 6-space indent. Kept a dedicated parser (not the flow-map
# parser) so `judgment` prose bullets stay readable one-per-line.

def _indent(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" "))


def load_tasks(root: Path) -> dict:
    """Parse task-library.yaml into {task-id: {name, role, artifact,
    output_path, source, inputs:[...], judgment:[...]}}."""
    path = None
    for rel in _TASK_CANDIDATES:
        cand = root / rel
        if cand.exists():
            path = cand
            break
    if path is None:
        raise FileNotFoundError(
            "task-library.yaml not found (looked in " + ", ".join(_TASK_CANDIDATES) + ")")

    tasks: dict = {}
    in_tasks = False
    cur_id = None
    cur_list = None  # name of the list field currently accumulating items
    for raw in path.read_text().splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        ind = _indent(line)
        stripped = line.strip()
        if ind == 0:
            in_tasks = (stripped == "tasks:")
            cur_id = cur_list = None
            continue
        if not in_tasks:
            continue
        if ind == 2 and stripped.endswith(":"):
            cur_id = stripped[:-1].strip()
            tasks[cur_id] = {"inputs": [], "judgment": []}
            cur_list = None
            continue
        if cur_id is None:
            raise MapError(f"task field before any task id: {stripped!r}")
        if ind == 6 and stripped.startswith("- "):
            if cur_list is None:
                raise MapError(f"list item outside a list field: {stripped!r}")
            tasks[cur_id][cur_list].append(_unquote(stripped[2:].strip()))
            continue
        if ind == 4:
            if ":" not in stripped:
                raise MapError(f"malformed task field: {stripped!r}")
            key, _, val = stripped.partition(":")
            key, val = key.strip(), val.strip()
            if key in _TASK_LISTS:
                cur_list = key
                if val:  # inline flow list allowed too: inputs: [a, b]
                    tasks[cur_id][key] = _parse_flow_list(val)
                    cur_list = None
            else:
                tasks[cur_id][key] = _unquote(val)
                cur_list = None
            continue
        raise MapError(f"unexpected indentation in task-library: {raw!r}")
    return tasks


def validate_tasks(tasks: dict) -> list:
    """Return a list of task-def problems (empty == valid). Hard gate."""
    problems = []
    if not tasks:
        problems.append("no tasks defined")
    for tid, d in tasks.items():
        for f in _TASK_SCALARS:
            if not str(d.get(f, "")).strip():
                problems.append(f"task {tid!r} missing field {f!r}")
        role = d.get("role")
        if role and role not in KNOWN_ROLES:
            problems.append(f"task {tid!r} unknown role {role!r}")
        artifact = d.get("artifact")
        if artifact and artifact not in SPINE_TYPES:
            problems.append(f"task {tid!r} artifact {artifact!r} not a spine type "
                            f"({', '.join(SPINE_TYPES)})")
        out = str(d.get("output_path", ""))
        if out and (out.startswith("/") or not out.endswith(".md")):
            problems.append(f"task {tid!r} output_path {out!r} must be a relative .md path")
        judgment = d.get("judgment") or []
        if not (3 <= len(judgment) <= 8):
            problems.append(f"task {tid!r} judgment has {len(judgment)} bullets (need 3–8)")
        if not isinstance(d.get("inputs"), list):
            problems.append(f"task {tid!r} inputs is not a list")
    return problems


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="OpenUP process map loader (read-only).")
    parser.add_argument("--repo-root", help="Repo root (default: script's parent).")
    sub = parser.add_subparsers(dest="command", required=True)

    pa = sub.add_parser("activities-for", help="Ordered activities for a phase.")
    pa.add_argument("phase")
    pa.add_argument("--json", action="store_true")

    pv = sub.add_parser("activity", help="One activity's role + skills.")
    pv.add_argument("name")
    pv.add_argument("--json", action="store_true")

    pl = sub.add_parser("phase-letter", help="Iteration-id prefix letter for a phase.")
    pl.add_argument("phase")

    pm = sub.add_parser("mint-iteration-id",
                        help="Stable iteration id <letter><ordinal> for a phase (e.g. C3).")
    pm.add_argument("phase")

    sub.add_parser("validate", help="Structural check of the shipped map.")

    pt = sub.add_parser("tasks", help="Task-library queries (T-105).")
    pt.add_argument("--validate", action="store_true",
                    help="Structural check of the committed task-library.yaml.")
    pt.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT

    try:
        mp = load_map(root)
    except FileNotFoundError as exc:
        print(f"[process-map] {exc}", file=sys.stderr)
        return 3

    try:
        if args.command == "activities-for":
            acts = activities_for(mp, args.phase)
            if args.json:
                print(json.dumps(acts, indent=1))
            else:
                for a in acts:
                    skills = ", ".join(a["skills"]) or "—"
                    print(f"{a['name']:<30} {a['role']:<16} {skills}")
            return 0
        if args.command == "activity":
            a = activity(mp, args.name)
            print(json.dumps(a, indent=1) if args.json else f"{a['role']}: {', '.join(a['skills']) or '—'}")
            return 0
        if args.command == "phase-letter":
            print(phase_letter(mp, args.phase))
            return 0
        if args.command == "mint-iteration-id":
            print(mint_iteration_id(root, mp, args.phase))
            return 0
        if args.command == "validate":
            # T-106: join activity tasks: against the committed library when present.
            try:
                task_ids = set(load_tasks(root))
            except FileNotFoundError:
                task_ids = None
            problems = validate(mp, task_ids)
            if problems:
                for p in problems:
                    print(f"[process-map] ✗ {p}", file=sys.stderr)
                return 2
            n = len(mp["phases"])
            print(f"[process-map] ✓ valid — {n} phases, {len(mp['activities'])} activities")
            return 0
        if args.command == "tasks":
            try:
                tasks = load_tasks(root)
            except FileNotFoundError as exc:
                print(f"[task-library] {exc}", file=sys.stderr)
                return 3
            if args.json:
                print(json.dumps(tasks, indent=1))
                return 0
            problems = validate_tasks(tasks)
            if problems:
                for p in problems:
                    print(f"[task-library] ✗ {p}", file=sys.stderr)
                return 2
            print(f"[task-library] ✓ valid — {len(tasks)} task def(s)")
            return 0
    except MapError as exc:
        print(f"[process-map] ✗ {exc}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())

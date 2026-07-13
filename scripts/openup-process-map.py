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
  validate                          Structural check of the shipped map.

Exit codes
  0  success
  2  usage / structure error (unknown phase/activity, malformed map)
  3  map file not found
"""

import argparse
import json
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
        out[key] = _parse_flow_list(val) if val.startswith("[") else val
    return out


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

def activities_for(mp: dict, phase: str) -> list:
    """Ordered activities for a phase, each resolved to {name, role, skills}."""
    if phase not in mp["phases"]:
        raise MapError(f"unknown phase: {phase!r} (known: {', '.join(mp['phases'])})")
    out = []
    for name in mp["phases"][phase]:
        act = mp["activities"].get(name)
        if act is None:
            raise MapError(f"phase {phase!r} references unknown activity {name!r}")
        out.append({"name": name, "role": act.get("role"), "skills": act.get("skills", [])})
    return out


def activity(mp: dict, name: str) -> dict:
    if name not in mp["activities"]:
        raise MapError(f"unknown activity: {name!r}")
    act = mp["activities"][name]
    return {"name": name, "role": act.get("role"), "skills": act.get("skills", [])}


def phase_letter(mp: dict, phase: str) -> str:
    letter = mp["phase_letters"].get(phase)
    if not letter:
        raise MapError(f"no phase_letters entry for phase {phase!r}")
    return letter


def validate(mp: dict) -> list:
    """Return a list of structural problems (empty == valid)."""
    problems = []
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
        if phase not in mp["phase_letters"]:
            problems.append(f"phase {phase!r} has no phase_letters entry")
    if not mp["phases"]:
        problems.append("no phases defined")
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

    sub.add_parser("validate", help="Structural check of the shipped map.")

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
        if args.command == "validate":
            problems = validate(mp)
            if problems:
                for p in problems:
                    print(f"[process-map] ✗ {p}", file=sys.stderr)
                return 2
            n = len(mp["phases"])
            print(f"[process-map] ✓ valid — {n} phases, {len(mp['activities'])} activities")
            return 0
    except MapError as exc:
        print(f"[process-map] ✗ {exc}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())

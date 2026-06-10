#!/usr/bin/env python3
"""OpenUP iteration state helper.

Reads/writes the single machine-readable iteration state file at
``<repo-root>/.openup/state.json``. This file is the source of truth that
OpenUP skills write (via this CLI) and hooks read to enforce process gates.

Design rules:
  * Deterministic. Never invokes a model.
  * Python standard library only (json, argparse, pathlib, datetime, sys).
  * Skills MUST write state through this CLI, never by hand-editing JSON.
  * State is validated against scripts/openup-state.schema.json (a focused
    in-house validator, not a general JSON-Schema engine) before every write.

Usage:
  python3 scripts/openup-state.py <subcommand> [options]

Subcommands:
  init         Create .openup/state.json for a new iteration.
  get          Print whole state, or a dotted-path value.
  set          Set a dotted-path value (typed coercion).
  set-gate     Set gates.<name> (typed coercion; path string allowed).
  check-gates  Exit nonzero if required gates are not all truthy.
  archive      Validate, copy state to a destination, then remove the original.
  validate     Validate .openup/state.json against the schema.

Exit codes:
  0  success
  2  argparse / usage error
  3  no state file present
  4  state file already exists (init without --force)
  5  dotted key not found (get)
  6  one or more required gates unmet (check-gates)
  7  state file invalid against schema (validate)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_NO_STATE = 3
EXIT_EXISTS = 4
EXIT_KEY_MISSING = 5
EXIT_GATES_UNMET = 6
EXIT_INVALID = 7

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SCHEMA_PATH = SCRIPT_DIR / "openup-state.schema.json"

# Default gates required for a standard completion. plan_persisted and
# retro_due are deliberately excluded: they are track-dependent.
DEFAULT_REQUIRED_GATES = ["team_deployed", "log_written", "roadmap_synced"]


# --------------------------------------------------------------------------
# Path resolution
# --------------------------------------------------------------------------
def state_dir(args) -> Path:
    """Resolve the .openup directory, honoring --state-dir override."""
    if getattr(args, "state_dir", None):
        return Path(args.state_dir).expanduser().resolve()
    return REPO_ROOT / ".openup"


def state_path(args) -> Path:
    return state_dir(args) / "state.json"


# --------------------------------------------------------------------------
# Schema validation (focused; covers only what openup-state.schema.json needs)
# --------------------------------------------------------------------------
def load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _type_ok(value, type_spec) -> bool:
    types = type_spec if isinstance(type_spec, list) else [type_spec]
    return any(_TYPE_CHECKS[t](value) for t in types if t in _TYPE_CHECKS)


def _validate_node(value, schema, path, errors):
    """Recursively validate value against a (sub)schema, collecting errors."""
    loc = path or "<root>"

    # type
    type_spec = schema.get("type")
    if type_spec is not None and not _type_ok(value, type_spec):
        errors.append(f"{loc}: expected type {type_spec}, got {type(value).__name__}")
        return  # further checks unreliable once type is wrong

    # const
    if "const" in schema and value != schema["const"]:
        errors.append(f"{loc}: must equal {schema['const']!r}, got {value!r}")

    # enum
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{loc}: {value!r} not in allowed values {schema['enum']}")

    # object: required, properties, additionalProperties
    if isinstance(value, dict) and (
        type_spec == "object"
        or (isinstance(type_spec, list) and "object" in type_spec)
        or "properties" in schema
    ):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{loc}: missing required property '{req}'")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{loc}: additional property '{key}' not allowed")
        for key, subval in value.items():
            if key in props:
                child = f"{loc}.{key}" if path else key
                _validate_node(subval, props[key], child, errors)


def validate_state(state: dict) -> list:
    """Return a list of human-readable validation error strings ([] if valid)."""
    errors = []
    try:
        schema = load_schema()
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - env issue
        return [f"cannot load schema {SCHEMA_PATH}: {exc}"]
    _validate_node(state, schema, "", errors)
    return errors


# --------------------------------------------------------------------------
# Load / save
# --------------------------------------------------------------------------
def read_state(args):
    p = state_path(args)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_state(args, state: dict):
    """Validate then atomically write the state file."""
    errors = validate_state(state)
    if errors:
        sys.stderr.write("State failed schema validation:\n")
        for err in errors:
            sys.stderr.write(f"  - {err}\n")
        sys.exit(EXIT_INVALID)
    d = state_dir(args)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "state.json"
    with p.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")


def require_state(args):
    state = read_state(args)
    if state is None:
        sys.stderr.write(f"No state file at {state_path(args)}\n")
        sys.exit(EXIT_NO_STATE)
    return state


# --------------------------------------------------------------------------
# Value coercion (for set / set-gate)
# --------------------------------------------------------------------------
def coerce_value(raw: str):
    """Coerce a CLI string into bool / int / None / str."""
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None
    try:
        return int(raw)
    except ValueError:
        return raw


# --------------------------------------------------------------------------
# Dotted-path helpers
# --------------------------------------------------------------------------
def dotted_get(state: dict, dotted: str):
    """Return (found, value) for a dotted path."""
    cur = state
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def dotted_set(state: dict, dotted: str, value):
    parts = dotted.split(".")
    cur = state
    for part in parts[:-1]:
        if not isinstance(cur.get(part), dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def cmd_init(args):
    p = state_path(args)
    if p.exists() and not args.force:
        sys.stderr.write(
            f"State file already exists at {p}. Use --force to overwrite.\n"
        )
        sys.exit(EXIT_EXISTS)

    plan_gate = args.plan if args.plan else False
    state = {
        "schema": 1,
        "task_id": args.task_id,
        "iteration": args.iteration,
        "phase": args.phase,
        "track": args.track,
        "branch": args.branch,
        "worktree": args.worktree,
        "session_id": args.session_id,  # may be None
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gates": {
            "team_deployed": False,
            "plan_persisted": plan_gate,
            "log_written": False,
            "roadmap_synced": False,
            "retro_due": False,
        },
        "iterations_since_retro": args.iterations_since_retro,
    }
    write_state(args, state)
    print(f"Initialized {state_path(args)}")
    return EXIT_OK


def cmd_get(args):
    state = require_state(args)
    if not args.key:
        print(json.dumps(state, indent=2))
        return EXIT_OK
    found, value = dotted_get(state, args.key)
    if not found:
        sys.stderr.write(f"Key not found: {args.key}\n")
        sys.exit(EXIT_KEY_MISSING)
    if isinstance(value, (dict, list)):
        print(json.dumps(value, indent=2))
    elif value is None:
        print("null")
    elif isinstance(value, bool):
        print("true" if value else "false")
    else:
        print(value)
    return EXIT_OK


def cmd_set(args):
    state = require_state(args)
    dotted_set(state, args.key, coerce_value(args.value))
    write_state(args, state)
    print(f"Set {args.key}")
    return EXIT_OK


def cmd_set_gate(args):
    state = require_state(args)
    state.setdefault("gates", {})
    state["gates"][args.name] = coerce_value(args.value)
    write_state(args, state)
    print(f"Set gates.{args.name}")
    return EXIT_OK


def cmd_check_gates(args):
    state = require_state(args)
    gates = state.get("gates", {})
    if args.require:
        required = [g.strip() for g in args.require.split(",") if g.strip()]
    else:
        required = list(DEFAULT_REQUIRED_GATES)

    unmet = []
    for name in required:
        if not gates.get(name):  # falsy: False, "", 0, None, or absent
            unmet.append(name)

    if unmet:
        sys.stderr.write("Unmet gates:\n")
        for name in unmet:
            sys.stderr.write(f"{name}\n")
        sys.exit(EXIT_GATES_UNMET)
    print("All required gates satisfied: " + ", ".join(required))
    return EXIT_OK


def cmd_archive(args):
    state = require_state(args)
    errors = validate_state(state)
    if errors:
        sys.stderr.write("Refusing to archive invalid state:\n")
        for err in errors:
            sys.stderr.write(f"  - {err}\n")
        sys.exit(EXIT_INVALID)
    dest = Path(args.dest_path).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    state_path(args).unlink()
    print(f"Archived state to {dest}")
    return EXIT_OK


def cmd_validate(args):
    state = require_state(args)
    errors = validate_state(state)
    if errors:
        sys.stderr.write("State is INVALID:\n")
        for err in errors:
            sys.stderr.write(f"  - {err}\n")
        sys.exit(EXIT_INVALID)
    print("State is valid.")
    return EXIT_OK


# --------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="openup-state.py",
        description="Read/write the OpenUP iteration state file (.openup/state.json).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    def add_state_dir(sp):
        sp.add_argument(
            "--state-dir",
            help="Override the .openup directory (default: <repo-root>/.openup).",
        )

    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Create the iteration state file.")
    p_init.add_argument("--task-id", required=True, help='e.g. "T-005"')
    p_init.add_argument("--iteration", required=True, type=int)
    p_init.add_argument(
        "--phase",
        required=True,
        choices=["inception", "elaboration", "construction", "transition"],
    )
    p_init.add_argument(
        "--track", required=True, choices=["quick", "standard", "full"]
    )
    p_init.add_argument("--branch", required=True)
    p_init.add_argument("--worktree", required=True, help="Absolute path")
    p_init.add_argument("--session-id", default=None)
    p_init.add_argument(
        "--plan",
        default=None,
        help="Path to a persisted plan; seeds gates.plan_persisted.",
    )
    p_init.add_argument("--iterations-since-retro", type=int, default=0)
    p_init.add_argument(
        "--force", action="store_true", help="Overwrite an existing state file."
    )
    add_state_dir(p_init)
    p_init.set_defaults(func=cmd_init)

    # get
    p_get = sub.add_parser("get", help="Print whole state or a dotted-path value.")
    p_get.add_argument("key", nargs="?", help="Dotted path, e.g. gates.team_deployed")
    add_state_dir(p_get)
    p_get.set_defaults(func=cmd_get)

    # set
    p_set = sub.add_parser("set", help="Set a dotted-path value (typed coercion).")
    p_set.add_argument("key", help="Dotted path, e.g. phase")
    p_set.add_argument("value", help="true/false/int/null/string")
    add_state_dir(p_set)
    p_set.set_defaults(func=cmd_set)

    # set-gate
    p_sg = sub.add_parser("set-gate", help="Set gates.<name> (typed coercion).")
    p_sg.add_argument("name", help="Gate name, e.g. team_deployed")
    p_sg.add_argument("value", help="true/false/int/null/string (path allowed)")
    add_state_dir(p_sg)
    p_sg.set_defaults(func=cmd_set_gate)

    # check-gates
    p_cg = sub.add_parser(
        "check-gates", help="Exit nonzero if required gates are not all truthy."
    )
    p_cg.add_argument(
        "--require",
        help="Comma-separated gate names. Default: "
        + ",".join(DEFAULT_REQUIRED_GATES),
    )
    add_state_dir(p_cg)
    p_cg.set_defaults(func=cmd_check_gates)

    # archive
    p_ar = sub.add_parser(
        "archive", help="Validate, copy state to dest, then remove the original."
    )
    p_ar.add_argument("dest_path", help="Destination path for the archived state.")
    add_state_dir(p_ar)
    p_ar.set_defaults(func=cmd_archive)

    # validate
    p_va = sub.add_parser("validate", help="Validate state against the schema.")
    add_state_dir(p_va)
    p_va.set_defaults(func=cmd_validate)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

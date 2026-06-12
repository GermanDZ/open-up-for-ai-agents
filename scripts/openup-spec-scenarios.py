#!/usr/bin/env python3
"""OpenUP requirement-scenario validator (T-020).

Deterministically checks that every entry in a task spec's ``## Requirements``
section carries at least one **Given / When / Then** acceptance scenario.
Writing the scenario is where a vague requirement breaks down — this check turns
the *absence* of one into a mechanical failure rather than a reviewer's judgement
call, closing the "specs assert testability but never demonstrate it" gap.

Scope: the check applies on the ``standard`` and ``full`` ceremony tracks; the
``quick`` track is skipped (a single-file / doc edit has not earned scenario
ceremony — see ``docs-eng-process/tracks.md``).

Determinism (mirrors openup-board.py / openup-claims.py):
  * Python standard library only. Never invokes a model. Identical input →
    identical output (no timestamps, no randomness).
  * Frontmatter parsing is *imported* from openup-claims.py, so the notion of
    "track" this validator reads agrees with the board and the claim pre-flight.

A scenario is recognised when a requirement's block contains all three bold
markers ``**Given**``, ``**When**``, ``**Then**`` (case-insensitive). The bold
form is deliberate: it never appears in ordinary requirement prose, so the check
has no false positives. Markers may sit on one line
(``- **Given** … **When** … **Then** …``) or span several lines.

Subcommands:
  check <plan.md>   Validate the requirements of one task spec.

Exit codes:
  0  every requirement carries a scenario (or the track is ``quick`` → skipped)
  1  one or more requirements lack a Given/When/Then scenario (listed on stderr)
  2  usage / structure error (file missing, or no ``## Requirements`` section)
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Reuse openup-claims.py (hyphenated filename → load via importlib), exactly as
# openup-board.py does, so "track" is parsed by one shared implementation.
# --------------------------------------------------------------------------
_CLAIMS_PATH = Path(__file__).resolve().parent / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

EXIT_OK = 0
EXIT_GAP = 1
EXIT_USAGE = 2

# Tracks on which the scenario requirement is enforced. ``quick`` is exempt.
ENFORCED_TRACKS = {"standard", "full"}
DEFAULT_TRACK = "standard"

# A top-level numbered requirement: ``1. text`` at the left margin (sub-bullets
# are indented and belong to the requirement above them).
REQUIREMENT_RE = re.compile(r"^(\d+)\.\s+(.*)$")
GIVEN_RE = re.compile(r"\*\*given\*\*", re.IGNORECASE)
WHEN_RE = re.compile(r"\*\*when\*\*", re.IGNORECASE)
THEN_RE = re.compile(r"\*\*then\*\*", re.IGNORECASE)


def requirements_section(plan_text: str):
    """Return the lines of the ``## Requirements`` section (exclusive of the
    heading, up to the next ``## `` heading), or ``None`` if there is no such
    section."""
    lines = plan_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and line.strip().lower() == "## requirements":
            start = i + 1
            break
    if start is None:
        return None
    out = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        out.append(line)
    return out


def parse_requirements(section_lines):
    """Split a Requirements section into ``(number, first_line, block_text)``
    tuples — one per top-level numbered requirement. ``block_text`` is every
    line from the requirement's number up to (not including) the next one, so a
    multi-line scenario underneath a requirement counts toward it."""
    reqs = []
    current = None  # (number, first_line, [block lines])
    for line in section_lines:
        m = REQUIREMENT_RE.match(line)
        if m:
            if current is not None:
                reqs.append(current)
            current = (m.group(1), m.group(2).strip(), [line])
        elif current is not None:
            current[2].append(line)
    if current is not None:
        reqs.append(current)
    return [(n, first, "\n".join(block)) for (n, first, block) in reqs]


def has_scenario(block_text: str) -> bool:
    """True when the requirement block contains a Given/When/Then scenario
    (all three bold markers present)."""
    return bool(
        GIVEN_RE.search(block_text)
        and WHEN_RE.search(block_text)
        and THEN_RE.search(block_text)
    )


def resolve_track(plan_path: Path, override):
    """The ceremony track to validate under: explicit ``--track`` wins, else the
    plan's frontmatter ``track``, else the default (``standard``)."""
    if override:
        return override.lower()
    fm = claims.parse_frontmatter(plan_path)
    track = fm.get("track")
    if isinstance(track, str) and track.strip():
        return track.strip().lower()
    return DEFAULT_TRACK


def cmd_check(args) -> int:
    plan_path = Path(args.plan)
    if not plan_path.is_file():
        print(f"[spec-scenarios] file not found: {plan_path}", file=sys.stderr)
        return EXIT_USAGE

    track = resolve_track(plan_path, args.track)
    if track not in ENFORCED_TRACKS:
        print(f"[spec-scenarios] skipped — '{track}' track is exempt from the "
              "scenario requirement")
        return EXIT_OK

    text = plan_path.read_text(encoding="utf-8")
    section = requirements_section(text)
    if section is None:
        print("[spec-scenarios] no '## Requirements' section found in "
              f"{plan_path}", file=sys.stderr)
        return EXIT_USAGE

    reqs = parse_requirements(section)
    if not reqs:
        print("[spec-scenarios] '## Requirements' has no numbered requirements "
              f"to validate in {plan_path}", file=sys.stderr)
        return EXIT_GAP

    missing = [(n, first) for (n, first, block) in reqs if not has_scenario(block)]
    if missing:
        print(f"[spec-scenarios] ✗ {len(missing)} of {len(reqs)} requirement(s) "
              "lack a Given/When/Then scenario:", file=sys.stderr)
        for number, first in missing:
            snippet = (first[:70] + "…") if len(first) > 70 else first
            print(f"    {number}. {snippet}", file=sys.stderr)
        print("\nAdd a scenario under each, e.g.:\n"
              "    - **Given** <precondition> **When** <action> "
              "**Then** <observable outcome>", file=sys.stderr)
        return EXIT_GAP

    print(f"[spec-scenarios] ✓ all {len(reqs)} requirement(s) carry a "
          f"Given/When/Then scenario ({track} track)")
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog="openup-spec-scenarios.py",
        description="Validate that every task-spec requirement carries a "
                    "Given/When/Then scenario.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Validate one task spec's requirements.")
    check.add_argument("plan", help="Path to the task spec (docs/changes/T-NNN/plan.md).")
    check.add_argument("--track", default=None,
                       help="Override the ceremony track (quick|standard|full). "
                            "Defaults to the plan's frontmatter, else 'standard'.")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

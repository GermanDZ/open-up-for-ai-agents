#!/usr/bin/env python3
"""Translate a harness-neutral OpenUP procedure into Claude Code skill frontmatter.

The neutral procedure pack (``docs-eng-process/procedures/openup-*.md``) is the
single source of truth for every procedure body (T-071). It declares a tier
*name* (``tier:``) instead of a concrete model, plus a ``capabilities:`` line
Claude Code does not consume. This adapter is the Claude Code translation layer:
it reads one neutral procedure and emits the exact ``.claude/skills/<name>/SKILL.md``
Claude Code expects, restoring ``model:`` from ``tier-map.yaml`` and dropping the
neutral-only ``capabilities:`` key. Everything else — ``name``/``description``/
``arguments``/``fit`` and the whole body — passes through verbatim, so the emitted
file is byte-for-byte parity-equal to today's hand-synced skill.

``scripts/sync-templates-to-claude.sh`` calls this per procedure; the frontmatter
surgery lives here (structured, testable) rather than in shell/sed.

Design rules (matching scripts/openup-*.py + check-model-tiers.py):
  * Deterministic. Never invokes a model.
  * Python standard library only (no PyYAML — the sync path runs at bootstrap).

Usage:
  python3 scripts/render-claude-adapter.py <procedure.md> \
      [--tier-map docs-eng-process/tier-map.yaml] [--target claude-code]

Writes the rendered SKILL.md to stdout. Exit codes:
  0  rendered OK
  2  usage / structure error (no frontmatter, missing tier:, unknown tier name)
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_TIER_MAP = REPO_ROOT / "docs-eng-process" / "tier-map.yaml"

EXIT_OK = 0
EXIT_USAGE = 2


def load_tier_map(path):
    """Parse the simple two-level tier-map.yaml with the standard library only.

    Structure (only this shape is supported — nothing fancier is needed):

        target-a:
          tier-name: model
          ...
        target-b:
          ...

    Returns {target: {tier: model}}. Comments (#...) and blank lines ignored;
    quotes around a value are stripped. Not a general YAML parser by design.
    """
    result = {}
    current = None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line[0].isspace():
            # top-level `target:` key
            key = line.rstrip(":").strip()
            current = {}
            result[key] = current
        else:
            if current is None:
                continue
            k, _, v = line.strip().partition(":")
            v = v.strip().strip('"').strip("'")
            current[k.strip()] = v
    return result


def split_frontmatter(text):
    """Return (fm_lines, body, trailing_nl) or (None, None, None) if no block.

    fm_lines are the lines BETWEEN the leading and closing ``---`` markers;
    body is everything after the closing marker (kept verbatim).
    """
    if not text.startswith("---"):
        return None, None, None
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return None, None, None
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return None, None, None
    fm = lines[1:close]
    body = lines[close + 1:]
    return fm, body, text.endswith("\n")


def render(text, tier_map, target):
    """Translate one neutral procedure's text into Claude skill text."""
    fm, body, trailing_nl = split_frontmatter(text)
    if fm is None:
        sys.stderr.write("error: no frontmatter block (leading ---) found\n")
        sys.exit(EXIT_USAGE)

    target_map = tier_map.get(target)
    if target_map is None:
        sys.stderr.write("error: target '%s' not in tier map\n" % target)
        sys.exit(EXIT_USAGE)

    out_fm = []
    saw_tier = False
    skipping_caps = False
    for line in fm:
        # Drop the neutral-only capabilities key (single-line or block form).
        if re.match(r"^capabilities\s*:", line):
            skipping_caps = True
            continue
        if skipping_caps:
            # a continuation of capabilities is indented; a new key ends the skip
            if line[:1].isspace() and line.strip():
                continue
            skipping_caps = False
        m = re.match(r"^tier\s*:\s*(\S+)\s*$", line)
        if m:
            tier = m.group(1)
            if tier not in target_map:
                sys.stderr.write(
                    "error: unknown tier '%s' — not in tier-map '%s' column "
                    "(no silent default)\n" % (tier, target)
                )
                sys.exit(EXIT_USAGE)
            out_fm.append("model: %s" % target_map[tier])
            saw_tier = True
            continue
        out_fm.append(line)

    if not saw_tier:
        sys.stderr.write("error: procedure has no `tier:` field\n")
        sys.exit(EXIT_USAGE)

    rebuilt = ["---"] + out_fm + ["---"] + body
    result = "\n".join(rebuilt)
    if trailing_nl:
        result += "\n"
    return result


def main(argv):
    ap = argparse.ArgumentParser(description="Render a neutral procedure into Claude skill frontmatter.")
    ap.add_argument("procedure", help="path to a docs-eng-process/procedures/openup-*.md file")
    ap.add_argument("--tier-map", default=str(DEFAULT_TIER_MAP), help="path to tier-map.yaml")
    ap.add_argument("--target", default="claude-code", help="tier-map column to resolve against")
    args = ap.parse_args(argv)

    tier_map = load_tier_map(args.tier_map)
    text = Path(args.procedure).read_text(encoding="utf-8")
    sys.stdout.write(render(text, tier_map, args.target))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

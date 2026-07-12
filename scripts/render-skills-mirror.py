#!/usr/bin/env python3
"""Generate the tracked Claude-format skill mirror from the neutral pack (T-071).

Background: the harness-neutral procedure pack (``docs-eng-process/procedures/
openup-*.md``) is the single *editable* source for every OpenUP procedure body.
Two downstream consumers still read the Claude-format tree
``docs-eng-process/.claude-templates/skills/openup-<name>/SKILL.md``:
``check-claude-sync.sh`` (pairs it against the live ``.claude/skills/``) and
``check-skills-guide.py`` (regenerates ``skills-guide.md`` from it), and
``sync-from-framework.sh`` ships it to downstream projects. Rather than rewire
those (owner decision 2026-07-12, Option A: generated mirror), this tool keeps
``.claude-templates/skills/`` alive but makes it a **derived mirror rendered from
the pack** — byte-identical to what ``render-claude-adapter.py`` emits for the
``claude-code`` target. The mirror is committed/tracked but never hand-edited.

This gives Requirement 5 a single *editable* source (the pack) while the two
gates and the downstream sync keep working unchanged.

Modes:
  --write   (re)generate every mirror SKILL.md from the pack.
  --check   verify each mirror equals render(pack); exit nonzero on drift. This
            is the drift guard wired into .githooks/pre-commit and openup-doctor,
            so a hand-edit to the mirror (instead of the pack) fails CI.

Design rules (matching scripts/render-claude-adapter.py + check-*.py):
  * Deterministic. Never invokes a model. Python standard library only.

Usage:
  python3 scripts/render-skills-mirror.py --check [-q]
  python3 scripts/render-skills-mirror.py --write

Exit codes:
  0  in sync (--check) / written (--write)
  1  drift detected — mirror differs from, is missing, or is stale vs the pack
  2  usage / structure error (missing pack, adapter error)
"""

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_PROCEDURES_DIR = REPO_ROOT / "docs-eng-process" / "procedures"
DEFAULT_MIRROR_DIR = REPO_ROOT / "docs-eng-process" / ".claude-templates" / "skills"
DEFAULT_TIER_MAP = REPO_ROOT / "docs-eng-process" / "tier-map.yaml"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2


def _load_adapter():
    """Import render-claude-adapter.py (hyphenated name → importlib)."""
    path = SCRIPT_DIR / "render-claude-adapter.py"
    spec = importlib.util.spec_from_file_location("render_claude_adapter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_pack(procedures_dir, tier_map_path, target="claude-code"):
    """Return {skill_name: rendered_skill_text} for every procedure in the pack."""
    adapter = _load_adapter()
    tier_map = adapter.load_tier_map(tier_map_path)
    rendered = {}
    for proc in sorted(Path(procedures_dir).glob("openup-*.md")):
        text = proc.read_text(encoding="utf-8")
        rendered[proc.stem] = adapter.render(text, tier_map, target)
    return rendered


def mirror_path(mirror_dir, name):
    return Path(mirror_dir) / name / "SKILL.md"


def check(procedures_dir, mirror_dir, tier_map_path, quiet=False):
    rendered = render_pack(procedures_dir, tier_map_path)
    if not rendered:
        sys.stderr.write("error: no procedures found in %s\n" % procedures_dir)
        return EXIT_USAGE

    differs, missing = [], []
    for name, want in rendered.items():
        dest = mirror_path(mirror_dir, name)
        if not dest.exists():
            missing.append(name)
        elif dest.read_text(encoding="utf-8") != want:
            differs.append(name)

    # Stale: a mirror skill dir with no corresponding procedure in the pack.
    stale = []
    mirror_dir = Path(mirror_dir)
    if mirror_dir.is_dir():
        for d in sorted(mirror_dir.glob("openup-*/")):
            if d.name not in rendered:
                stale.append(d.name)

    drift = differs or missing or stale
    if not drift:
        if not quiet:
            print(
                "[render-skills-mirror] ✓ mirror in sync with the pack "
                "(%d skills)" % len(rendered)
            )
        return EXIT_OK

    sys.stderr.write(
        "[render-skills-mirror] ✗ mirror has drifted from the neutral pack\n\n"
    )
    if differs:
        sys.stderr.write("Differs from render(pack) (hand-edited mirror?):\n")
        for n in differs:
            sys.stderr.write("  %s\n" % n)
    if missing:
        sys.stderr.write("\nIn the pack but missing from the mirror:\n")
        for n in missing:
            sys.stderr.write("  %s\n" % n)
    if stale:
        sys.stderr.write("\nIn the mirror but not in the pack (stale):\n")
        for n in stale:
            sys.stderr.write("  %s\n" % n)
    sys.stderr.write(
        "\nThe pack is the single editable source. Do not hand-edit the mirror.\n"
        "  - Edit the body in docs-eng-process/procedures/openup-<name>.md\n"
        "  - Run:  python3 scripts/render-skills-mirror.py --write\n"
    )
    return EXIT_DRIFT


def write(procedures_dir, mirror_dir, tier_map_path, quiet=False):
    rendered = render_pack(procedures_dir, tier_map_path)
    if not rendered:
        sys.stderr.write("error: no procedures found in %s\n" % procedures_dir)
        return EXIT_USAGE

    changed = 0
    for name, want in rendered.items():
        dest = mirror_path(mirror_dir, name)
        if dest.exists() and dest.read_text(encoding="utf-8") == want:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(want, encoding="utf-8")
        changed += 1

    if not quiet:
        print(
            "[render-skills-mirror] wrote mirror from the pack "
            "(%d skills, %d updated)" % (len(rendered), changed)
        )
    return EXIT_OK


def main(argv):
    ap = argparse.ArgumentParser(
        description="Generate/verify the Claude-format skill mirror from the neutral pack."
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="exit nonzero on drift (CI)")
    g.add_argument("--write", action="store_true", help="regenerate the mirror in place")
    ap.add_argument("--procedures-dir", default=str(DEFAULT_PROCEDURES_DIR),
                    help="override the neutral pack dir (tests)")
    ap.add_argument("--mirror-dir", default=str(DEFAULT_MIRROR_DIR),
                    help="override the .claude-templates/skills dir (tests)")
    ap.add_argument("--tier-map", default=str(DEFAULT_TIER_MAP),
                    help="override tier-map.yaml (tests)")
    ap.add_argument("-q", "--quiet", action="store_true", help="suppress success output")
    args = ap.parse_args(argv)

    if args.check:
        return check(args.procedures_dir, args.mirror_dir, args.tier_map, args.quiet)
    return write(args.procedures_dir, args.mirror_dir, args.tier_map, args.quiet)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

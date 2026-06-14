#!/usr/bin/env python3
"""Keep docs-eng-process/model-tiers.md in sync with live `model:` frontmatter.

The per-skill and per-agent model tables in ``model-tiers.md`` used to be
hand-maintained and drifted from the actual skill frontmatter (wrong counts,
skills missing from the table entirely). This tool makes the tables
**generated**: it reads the ``model:`` line from every skill and agent under
``docs-eng-process/.claude-templates/`` and rewrites the marked blocks in
``model-tiers.md``.

Design rules (matching the other ``scripts/openup-*.py`` tools):
  * Deterministic. Never invokes a model.
  * Python standard library only.

Usage:
  python3 scripts/check-model-tiers.py --check   # CI: exit nonzero on drift
  python3 scripts/check-model-tiers.py --write    # regenerate the tables

Exit codes:
  0  in sync (--check) / written (--write)
  1  drift detected, or a skill/agent is missing a `model:` field (--check)
  2  usage / file-structure error (e.g. markers missing)
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATES = REPO_ROOT / "docs-eng-process" / ".claude-templates"
SKILLS_DIR = TEMPLATES / "skills"
AGENTS_DIR = TEMPLATES / "agents"
DOC = REPO_ROOT / "docs-eng-process" / "model-tiers.md"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2

MODEL_ORDER = {"haiku": 0, "sonnet": 1, "inherit": 2}


def frontmatter_field(text, field):
    """Return the value of `field:` from a leading `---` YAML block, or None."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    m = re.search(r"^%s:\s*(.+?)\s*$" % re.escape(field), block, re.MULTILINE)
    return m.group(1).strip() if m else None


def collect(paths):
    """Return (rows, missing) where rows is [(name, model)] and missing is [name]."""
    rows, missing = [], []
    for p in sorted(paths):
        text = p.read_text(encoding="utf-8")
        name = frontmatter_field(text, "name") or p.parent.name
        model = frontmatter_field(text, "model")
        if model is None:
            missing.append(name)
            continue
        rows.append((name, model))
    return rows, missing


def render_table(rows, header):
    rows = sorted(rows, key=lambda r: (MODEL_ORDER.get(r[1], 99), r[0]))
    lines = ["| %s | Model |" % header, "|%s|-------|" % ("-" * (len(header) + 2))]
    for name, model in rows:
        lines.append("| %s | `%s` |" % (name, model))
    return "\n".join(lines)


def totals_line(rows):
    counts = {}
    for _, model in rows:
        counts[model] = counts.get(model, 0) + 1
    parts = ["%d × `%s`" % (counts[m], m) for m in sorted(counts, key=lambda m: MODEL_ORDER.get(m, 99))]
    return "**Totals:** %s (%d skills)." % (", ".join(parts), len(rows))


def replace_block(doc_text, marker, body):
    begin = "<!-- BEGIN GENERATED: %s (scripts/check-model-tiers.py) -->" % marker
    end = "<!-- END GENERATED: %s -->" % marker
    pat = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if not pat.search(doc_text):
        sys.stderr.write("error: markers for '%s' not found in %s\n" % (marker, DOC))
        sys.exit(EXIT_USAGE)
    return pat.sub(begin + "\n" + body + "\n" + end, doc_text)


def build(doc_text, templates=TEMPLATES, doc=DOC):
    skill_rows, skill_missing = collect((templates / "skills").glob("*/SKILL.md"))
    agent_rows, agent_missing = collect((templates / "agents").glob("*.md"))

    skill_body = render_table(skill_rows, "Skill") + "\n\n" + totals_line(skill_rows)
    agent_body = render_table(agent_rows, "Agent")

    out = replace_block(doc_text, "skill-model-table", skill_body)
    out = replace_block(out, "agent-model-table", agent_body)
    return out, skill_missing + agent_missing


def main(argv):
    ap = argparse.ArgumentParser(description="Sync model-tiers.md with live frontmatter.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="exit nonzero on drift (CI)")
    g.add_argument("--write", action="store_true", help="regenerate the tables in place")
    ap.add_argument("--templates-dir", default=str(TEMPLATES),
                    help="override .claude-templates dir (for tests)")
    ap.add_argument("--doc", default=str(DOC),
                    help="override model-tiers.md path (for tests)")
    args = ap.parse_args(argv)

    templates = Path(args.templates_dir)
    doc = Path(args.doc)
    doc_text = doc.read_text(encoding="utf-8")
    new_text, missing = build(doc_text, templates=templates, doc=doc)

    if missing:
        sys.stderr.write(
            "error: missing `model:` frontmatter in: %s\n" % ", ".join(sorted(missing))
        )
        return EXIT_DRIFT

    if args.write:
        if new_text != doc_text:
            doc.write_text(new_text, encoding="utf-8")
            print("model-tiers.md tables regenerated.")
        else:
            print("model-tiers.md already up to date.")
        return EXIT_OK

    # --check
    if new_text != doc_text:
        sys.stderr.write(
            "error: model-tiers.md is out of sync with skill/agent `model:` "
            "frontmatter.\n       Run: python3 scripts/check-model-tiers.py --write\n"
        )
        return EXIT_DRIFT
    n = len(list((templates / "skills").glob("*/SKILL.md")))
    print("model-tiers.md is in sync (%d skills, all have model:)." % n)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

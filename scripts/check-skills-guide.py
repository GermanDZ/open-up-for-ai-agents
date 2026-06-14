#!/usr/bin/env python3
"""Keep docs-eng-process/skills-guide.md generated from the live skill files.

The per-skill reference in ``skills-guide.md`` used to be ~1,000 hand-written
lines duplicating each skill's frontmatter and "When to Use" prose. It drifted:
five shipped skills were missing from it entirely, and descriptions/arguments
fell out of sync with the SKILL.md files. This tool makes the reference + index
**generated** — the SKILL.md files are the single source of truth.

For every skill under ``docs-eng-process/.claude-templates/skills/*/SKILL.md`` it
reads:
  * frontmatter  — ``description``, ``model``, ``fit:`` buckets, ``arguments:``
  * body         — the verbatim ``## When to Use`` / ``## When NOT to Use`` /
                   ``## Success Criteria`` / ``## See Also`` sections, when present
and rewrites the two marked blocks in skills-guide.md (the grouped Skill
Reference and the Skill Index table). All prose outside the markers is
hand-authored and left untouched.

Design rules (matching scripts/check-model-tiers.py and the openup-*.py tools):
  * Deterministic. Never invokes a model. Python standard library only.

Usage:
  python3 scripts/check-skills-guide.py --check   # CI: exit nonzero on drift
  python3 scripts/check-skills-guide.py --write    # regenerate the blocks

Exit codes:
  0  in sync (--check) / written (--write)
  1  drift detected, or a skill is missing required frontmatter (--check)
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
DOC = REPO_ROOT / "docs-eng-process" / "skills-guide.md"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2

# Skills whose name (sans the openup- prefix) places them in a group. Anything
# matching neither the phase set nor the artifact rule is a workflow skill.
PHASE = {"inception", "elaboration", "construction", "transition"}
ARTIFACT_EXTRA = {"shared-vision", "detail-use-case"}
# create-* skills that are workflow actions, not work-product artifacts.
WORKFLOW_OVERRIDE = {"create-pr", "create-handoff"}

GROUP_ORDER = ["Phase", "Artifact", "Workflow"]
GROUP_BLURB = {
    "Phase": "Phase skills guide you through each OpenUP phase, providing "
             "context-specific activities and completion criteria.",
    "Artifact": "Artifact skills create OpenUP work products from templates.",
    "Workflow": "Workflow skills automate common workflow operations.",
}

# Verbatim body sections lifted into the reference, in render order.
BODY_SECTIONS = ["When to Use", "When NOT to Use", "Success Criteria"]


# --------------------------------------------------------------------------
# Frontmatter parsing (focused: only the shapes the skills' frontmatter uses)
# --------------------------------------------------------------------------
def split_frontmatter(text):
    """Return (frontmatter_lines, body_text). Empty list/'' if no block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return [], text


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def top_scalar(fm_lines, key):
    """Value of a top-level (indent 0) ``key: value`` scalar, or None."""
    pat = re.compile(r"^%s:\s*(.*)$" % re.escape(key))
    for ln in fm_lines:
        if _indent(ln) != 0:
            continue
        m = pat.match(ln)
        if m:
            return m.group(1).strip().strip('"').strip("'") or None
    return None


def sub_block(fm_lines, key):
    """Lines indented under a top-level ``key:`` (until the next indent-0 key)."""
    out = []
    collecting = False
    for ln in fm_lines:
        if _indent(ln) == 0 and re.match(r"^%s:\s*$" % re.escape(key), ln):
            collecting = True
            continue
        if collecting:
            if ln.strip() == "":
                out.append(ln)
                continue
            if _indent(ln) == 0:
                break
            out.append(ln)
    return out


def parse_fit(fm_lines):
    """Return [(bucket, raw)] for the fit: great/ok/poor mapping, in order."""
    block = sub_block(fm_lines, "fit")
    out = []
    for bucket in ("great", "ok", "poor"):
        for ln in block:
            m = re.match(r"^\s*%s:\s*(.*)$" % bucket, ln)
            if m:
                raw = m.group(1).strip()
                if raw.startswith("[") and raw.endswith("]"):
                    raw = raw[1:-1].strip()
                if raw:
                    out.append((bucket, raw))
                break
    return out


def parse_arguments(fm_lines):
    """Return [(name, description, required)] from the arguments: list-of-maps."""
    block = sub_block(fm_lines, "arguments")
    args = []
    cur = None
    for ln in block:
        if ln.strip() == "":
            continue
        m = re.match(r"^\s*-\s*name:\s*(.*)$", ln)
        if m:
            if cur:
                args.append(cur)
            cur = {"name": m.group(1).strip().strip('"').strip("'"),
                   "description": "", "required": False}
            continue
        if cur is None:
            continue
        md = re.match(r"^\s*description:\s*(.*)$", ln)
        if md:
            cur["description"] = md.group(1).strip().strip('"').strip("'")
            continue
        mr = re.match(r"^\s*required:\s*(.*)$", ln)
        if mr:
            cur["required"] = mr.group(1).strip().lower() == "true"
    if cur:
        args.append(cur)
    return args


# --------------------------------------------------------------------------
# Body section extraction (verbatim)
# --------------------------------------------------------------------------
def body_section(body_text, name):
    """The verbatim lines under ``## <name>`` up to the next ``#`` heading."""
    out = []
    capturing = False
    for ln in body_text.splitlines():
        if ln.startswith("#"):
            if ln.startswith("## ") and ln[3:].strip().lower() == name.lower():
                capturing = True
                continue
            if capturing:
                break
            continue
        if capturing:
            out.append(ln)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) if out else None


def flatten_links(text):
    """``[label](url)`` -> ```label```` so cross-links survive as readable names."""
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"`\1`", text)


# --------------------------------------------------------------------------
# Model assembly
# --------------------------------------------------------------------------
def categorize(short_name):
    if short_name in PHASE:
        return "Phase"
    if short_name in WORKFLOW_OVERRIDE:
        return "Workflow"
    if short_name.startswith("create-") or short_name in ARTIFACT_EXTRA:
        return "Artifact"
    return "Workflow"


def collect_skills(skills_dir=SKILLS_DIR):
    """Return (skills, missing). skills sorted by (group, name)."""
    skills, missing = [], []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        name = top_scalar(fm, "name") or skill_md.parent.name
        description = top_scalar(fm, "description")
        model = top_scalar(fm, "model")
        if not description or not model:
            missing.append(name)
            continue
        short = name[len("openup-"):] if name.startswith("openup-") else name
        skills.append({
            "name": name,
            "short": short,
            "group": categorize(short),
            "description": description,
            "model": model,
            "fit": parse_fit(fm),
            "arguments": parse_arguments(fm),
            "sections": {s: body_section(body, s) for s in BODY_SECTIONS},
            "see_also": body_section(body, "See Also"),
        })
    group_rank = {g: i for i, g in enumerate(GROUP_ORDER)}
    skills.sort(key=lambda s: (group_rank.get(s["group"], 9), s["name"]))
    return skills, missing


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def render_skill(skill):
    lines = ["### /%s" % skill["name"], "", skill["description"], "",
             "**Model**: `%s`" % skill["model"]]
    for section in BODY_SECTIONS:
        content = skill["sections"].get(section)
        if content:
            lines += ["", "**%s**" % section, "", content]
    if skill["fit"]:
        label = {"great": "Great fit", "ok": "OK fit", "poor": "Poor fit"}
        lines += ["", "**Fit**:"]
        for bucket, raw in skill["fit"]:
            lines.append("- %s: %s" % (label[bucket], raw))
    lines += ["", "**Arguments**:"]
    if skill["arguments"]:
        for a in skill["arguments"]:
            req = "required" if a["required"] else "optional"
            desc = (" — %s" % a["description"]) if a["description"] else ""
            lines.append("- `%s` (%s)%s" % (a["name"], req, desc))
    else:
        lines.append("- None")
    if skill["see_also"]:
        lines += ["", "**See Also**: " +
                  " · ".join(_see_also_names(skill["see_also"]))]
    return "\n".join(lines)


def _see_also_names(see_also_text):
    names = []
    for m in re.finditer(r"\[([^\]]+)\]\([^)]+\)", see_also_text):
        names.append("`%s`" % m.group(1).strip())
    if not names:  # plain text fallback
        names = [flatten_links(see_also_text).strip()]
    # de-dup preserving order
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def render_reference(skills):
    out = []
    for group in GROUP_ORDER:
        members = [s for s in skills if s["group"] == group]
        if not members:
            continue
        out += ["## %s Skills" % group, "", GROUP_BLURB[group], ""]
        out += [render_skill(s) + "\n" for s in members]
    return "\n".join(out).rstrip()


def render_index(skills):
    lines = ["| Skill | Group | What it does |", "|-------|-------|--------------|"]
    for s in skills:
        lines.append("| `/%s` | %s | %s |" % (s["name"], s["group"], s["description"]))
    return "\n".join(lines)


# --------------------------------------------------------------------------
def replace_block(doc_text, marker, body):
    begin = "<!-- BEGIN GENERATED: %s (scripts/check-skills-guide.py) -->" % marker
    end = "<!-- END GENERATED: %s -->" % marker
    pat = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if not pat.search(doc_text):
        sys.stderr.write("error: markers for '%s' not found in %s\n" % (marker, DOC))
        sys.exit(EXIT_USAGE)
    return pat.sub(begin + "\n" + body + "\n" + end, doc_text)


def build(doc_text, skills_dir=SKILLS_DIR):
    skills, missing = collect_skills(skills_dir)
    out = replace_block(doc_text, "skill-reference", render_reference(skills))
    out = replace_block(out, "skill-index", render_index(skills))
    return out, missing, len(skills)


def main(argv):
    ap = argparse.ArgumentParser(description="Sync skills-guide.md with live skill files.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="exit nonzero on drift (CI)")
    g.add_argument("--write", action="store_true", help="regenerate the blocks in place")
    ap.add_argument("--doc", default=str(DOC), help="override skills-guide.md path (tests)")
    ap.add_argument("--skills-dir", default=str(SKILLS_DIR),
                    help="override the skills dir (tests)")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="suppress the success line (errors still print); for hooks")
    args = ap.parse_args(argv)

    doc = Path(args.doc)
    doc_text = doc.read_text(encoding="utf-8")
    new_text, missing, n = build(doc_text, Path(args.skills_dir))

    if missing:
        sys.stderr.write(
            "error: missing description/model frontmatter in: %s\n"
            % ", ".join(sorted(missing)))
        return EXIT_DRIFT

    if args.write:
        if new_text != doc_text:
            doc.write_text(new_text, encoding="utf-8")
            if not args.quiet:
                print("skills-guide.md regenerated (%d skills)." % n)
        elif not args.quiet:
            print("skills-guide.md already up to date.")
        return EXIT_OK

    # --check
    if new_text != doc_text:
        sys.stderr.write(
            "error: skills-guide.md is out of sync with the skill files.\n"
            "       Run: python3 scripts/check-skills-guide.py --write\n")
        return EXIT_DRIFT
    if not args.quiet:
        print("skills-guide.md is in sync (%d skills)." % n)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

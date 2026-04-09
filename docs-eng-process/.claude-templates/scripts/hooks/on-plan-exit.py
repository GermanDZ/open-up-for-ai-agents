#!/usr/bin/env python3
"""
on-plan-exit.py — OpenUP hook: runs after ExitPlanMode is approved.

Automatically:
  1. Finds the most recently modified plan file in ~/.claude/plans/
  2. Copies it to docs/plans/YYYY-MM-DD-<slug>.md in the project
  3. Appends a "pending plan" entry to docs/roadmap.md

This ensures plan context survives session boundaries — a new session can
read docs/roadmap.md, find the plan entry, and pick up exactly where the
planning left off.

Hook event: PostToolUse / ExitPlanMode
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text.strip())
    return re.sub(r"-+", "-", text)[:60].strip("-")


def find_latest_plan() -> Path | None:
    plans_dir = Path.home() / ".claude" / "plans"
    if not plans_dir.exists():
        return None
    md_files = sorted(plans_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return md_files[0] if md_files else None


def extract_title(content: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            # Strip leading "Plan: " prefix if present
            title = line.lstrip("# ").strip()
            title = re.sub(r"^[Pp]lan:\s*", "", title)
            return title
    return "Untitled Plan"


def append_to_roadmap(roadmap_path: Path, plan_rel_path: str, title: str, today: str) -> None:
    """Append a planned task entry to docs/roadmap.md."""
    entry = (
        f"\n\n<!-- plan-hook: {today} -->\n"
        f"### Planned: {title}\n\n"
        f"- **Status**: `planned` (awaiting implementation)\n"
        f"- **Plan**: [{plan_rel_path}]({plan_rel_path})\n"
        f"- **Created**: {today}\n"
        f"- **Next step**: Run `/openup-start-iteration` referencing this plan\n"
    )

    if roadmap_path.exists():
        with open(roadmap_path, "a") as f:
            f.write(entry)
    else:
        roadmap_path.parent.mkdir(parents=True, exist_ok=True)
        with open(roadmap_path, "w") as f:
            f.write(f"# Roadmap\n{entry}")


def main() -> None:
    # Read hook payload from stdin (may be empty if called directly)
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    # Only act on ExitPlanMode events
    tool_name = payload.get("tool_name", "ExitPlanMode")
    if tool_name != "ExitPlanMode":
        sys.exit(0)

    # Project root is the cwd when Claude Code runs the hook
    project_root = Path(payload.get("cwd", os.getcwd()))

    # Find the plan file
    plan_src = find_latest_plan()
    if not plan_src:
        print("[on-plan-exit] No plan file found in ~/.claude/plans/ — skipping.", file=sys.stderr)
        sys.exit(0)

    content = plan_src.read_text(encoding="utf-8")
    title = extract_title(content)
    today = date.today().isoformat()
    slug = slugify(title)
    dest_filename = f"{today}-{slug}.md"

    # Save plan to docs/plans/
    plans_dir = project_root / "docs" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    dest_path = plans_dir / dest_filename

    # Don't overwrite if the exact same plan was already saved
    if dest_path.exists() and dest_path.read_text(encoding="utf-8") == content:
        print(f"[on-plan-exit] Plan already saved: docs/plans/{dest_filename}", file=sys.stderr)
        sys.exit(0)

    dest_path.write_text(content, encoding="utf-8")

    # Append to roadmap
    roadmap_path = project_root / "docs" / "roadmap.md"
    plan_rel = f"plans/{dest_filename}"
    append_to_roadmap(roadmap_path, plan_rel, title, today)

    print(
        f"[on-plan-exit] Plan saved → docs/plans/{dest_filename}\n"
        f"[on-plan-exit] Roadmap updated → docs/roadmap.md",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

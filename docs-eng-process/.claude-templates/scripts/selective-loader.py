#!/usr/bin/env python3
"""
Selective Context Loader for OpenUP

Loads only relevant context based on task type and role.
Reduces token usage by avoiding loading unnecessary documents.

This is the smart loader that implements tiered context loading.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


def get_relevant_context(
    task_type: str,
    role: Optional[str] = None,
    tier: str = "standard",
    project_dir: str = "."
) -> Dict[str, Any]:
    """
    Load only relevant context for the given task type and role.

    Args:
        task_type: Type of task (feature, bugfix, refactor, docs, testing, planning)
        role: OpenUP role (analyst, architect, developer, tester, project-manager)
        tier: Context tier (minimal, standard, full)
        project_dir: Project root directory

    Returns:
        Dict with relevant context only
    """
    base_path = Path(project_dir)
    docs_path = base_path / "docs"

    # Import cache manager
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from cache_manager import ContextCache
        cache = ContextCache()
    except ImportError:
        cache = None

    # Import parse scripts
    scripts_path = Path(__file__).parent.parent / "skills" / "scripts"
    sys.path.insert(0, str(scripts_path))

    try:
        from parse_project_status import parse_project_status
        from parse_roadmap import parse_roadmap, get_task
    except ImportError:
        return {"error": "Failed to import parse scripts"}

    context = {
        "tier": tier,
        "task_type": task_type,
        "role": role,
        "loaded_at": datetime.now().isoformat(),
        "project_status": None,
        "roadmap": None,
        "documents": {},
        "role_instructions": None
    }

    # Tier 1: Minimal - Current task only
    if tier == "minimal":
        status_file = docs_path / "project-status.md"
        if status_file.exists():
            status = parse_project_status(str(status_file), use_cache=True)
            if "error" not in status:
                context["project_status"] = {
                    "phase": status.get("phase"),
                    "iteration": status.get("iteration"),
                    "goal": status.get("iteration_goal"),
                    "current_task": status.get("current_task")
                }

        # Load current task if specified
        if context["project_status"].get("current_task"):
            task = get_task(
                context["project_status"]["current_task"],
                str(docs_path / "roadmap.md")
            )
            if "error" not in task:
                context["current_task"] = {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "description": task.get("description"),
                    "status": task.get("status")
                }

    # Tier 2: Standard - Project status + relevant role info
    elif tier == "standard":
        # Full project status
        status_file = docs_path / "project-status.md"
        if status_file.exists():
            context["project_status"] = parse_project_status(str(status_file), use_cache=True)

        # Current task from roadmap
        if context["project_status"] and context["project_status"].get("current_task"):
            task = get_task(
                context["project_status"]["current_task"],
                str(docs_path / "roadmap.md")
            )
            if "error" not in task:
                context["current_task"] = task

        # Role-specific context
        if role:
            context["role_instructions"] = _get_role_instructions(role, mode="standard")

        # Task-type specific documents
        context["documents"] = _get_task_documents(task_type, docs_path, mode="standard")

    # Tier 3: Full - All context
    elif tier == "full":
        # Everything from standard plus more
        context["project_status"] = parse_project_status(str(docs_path / "project-status.md"), use_cache=True)
        context["roadmap"] = parse_roadmap(str(docs_path / "roadmap.md"), use_cache=True)

        if role:
            context["role_instructions"] = _get_role_instructions(role, mode="full")

        # All relevant documents
        context["documents"] = _get_task_documents(task_type, docs_path, mode="full")

        # Add additional context
        for doc_name in ["vision", "risk-list", "architecture-notebook"]:
            doc_file = docs_path / f"{doc_name}.md"
            if doc_file.exists():
                context["documents"][doc_name] = {
                    "exists": True,
                    "path": str(doc_file),
                    "summary": _summarize_document(doc_file)
                }

    return context


def _get_role_instructions(role: str, mode: str = "standard") -> Dict[str, Any]:
    """Get role instructions based on mode."""
    # For minimal/standard, return compact version
    if mode in ["minimal", "standard"]:
        compact_file = Path(__file__).parent.parent / "teammates" / f"{role}-compact.md"
        if compact_file.exists():
            return {
                "source": "compact",
                "content": compact_file.read_text()
            }

    # For full, return complete instructions
    full_file = Path(__file__).parent.parent / "teammates" / f"{role}.md"
    if full_file.exists():
        return {
            "source": "full",
            "content": full_file.read_text()
        }

    return {"error": f"Role instructions not found: {role}"}


def _get_task_documents(task_type: str, docs_path: Path, mode: str = "standard") -> Dict[str, Any]:
    """Get documents relevant to the task type."""
    doc_map = {
        "feature": ["vision", "architecture-notebook"],
        "bugfix": ["risk-list"],
        "refactor": ["architecture-notebook"],
        "docs": ["vision"],
        "testing": ["vision"],
        "planning": ["vision", "risk-list", "roadmap"]
    }

    relevant_docs = doc_map.get(task_type, [])
    result = {}

    for doc_name in relevant_docs:
        doc_file = docs_path / f"{doc_name}.md"
        if doc_file.exists():
            if mode == "full":
                result[doc_name] = {
                    "exists": True,
                    "path": str(doc_file),
                    "content": doc_file.read_text()
                }
            else:
                result[doc_name] = {
                    "exists": True,
                    "path": str(doc_file),
                    "summary": _summarize_document(doc_file)
                }

    return result


def _summarize_document(file_path: Path) -> str:
    """Create a brief summary of the document."""
    try:
        content = file_path.read_text()
        lines = content.split("\n")

        # Get title
        title = lines[0].lstrip("#").strip() if lines else file_path.name

        # Get first paragraph
        description = ""
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                description = stripped
                break

        return f"**{title}**: {description[:100]}..."

    except Exception:
        return f"Document at {file_path.name}"


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Load selective context for OpenUP")
    parser.add_argument("--task-type", required=True,
                       choices=["feature", "bugfix", "refactor", "docs", "testing", "planning"],
                       help="Type of task")
    parser.add_argument("--role", help="OpenUP role (analyst, architect, etc.)")
    parser.add_argument("--tier", default="standard", choices=["minimal", "standard", "full"],
                       help="Context tier")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    context = get_relevant_context(
        task_type=args.task_type,
        role=args.role,
        tier=args.tier,
        project_dir=args.project_dir
    )

    indent = 2 if args.pretty else None
    print(json.dumps(context, indent=indent))


if __name__ == "__main__":
    main()

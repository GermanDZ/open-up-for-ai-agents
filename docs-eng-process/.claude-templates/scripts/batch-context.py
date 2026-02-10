#!/usr/bin/env python3
"""
Batch Context Loader for OpenUP

Loads all project state documents in a single script call for efficiency.
Combines project-status, roadmap, and other state documents into one JSON output.

Expected token savings: 20-30% by avoiding multiple script invocations.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional


def load_all_context(
    project_dir: str = ".",
    use_cache: bool = True,
    include_docs: Optional[list] = None
) -> Dict[str, Any]:
    """
    Load all project state documents in one call.

    Args:
        project_dir: Root directory of the project
        use_cache: Whether to use cached data if available
        include_docs: List of additional docs to include (e.g., ['vision', 'risk-list'])

    Returns:
        Dict containing all project state
    """
    base_path = Path(project_dir)
    docs_path = base_path / "docs"

    result = {
        "project_status": None,
        "roadmap": None,
        "additional_docs": {},
        "meta": {
            "project_dir": str(base_path.absolute()),
            "loaded_at": None
        }
    }

    # Import parse scripts
    scripts_path = Path(__file__).parent.parent / "skills" / "scripts"
    sys.path.insert(0, str(scripts_path))

    try:
        from parse_project_status import parse_project_status
        from parse_roadmap import parse_roadmap
    except ImportError as e:
        result["error"] = f"Failed to import parse scripts: {e}"
        return result

    # Load project status
    status_file = docs_path / "project-status.md"
    if status_file.exists():
        result["project_status"] = parse_project_status(str(status_file), use_cache=use_cache)

    # Load roadmap
    roadmap_file = docs_path / "roadmap.md"
    if roadmap_file.exists():
        result["roadmap"] = parse_roadmap(str(roadmap_file), use_cache=use_cache)

    # Load additional docs if requested
    if include_docs:
        for doc_name in include_docs:
            doc_file = docs_path / f"{doc_name}.md"
            if doc_file.exists():
                result["additional_docs"][doc_name] = {
                    "exists": True,
                    "path": str(doc_file),
                    "content": doc_file.read_text() if use_cache else None  # For now, just flag existence
                }

    # Add timestamp
    from datetime import datetime
    result["meta"]["loaded_at"] = datetime.now().isoformat()

    return result


def get_current_iteration_context(project_dir: str = ".") -> Dict[str, Any]:
    """
    Get context for the current iteration only (minimal mode).

    Args:
        project_dir: Root directory of the project

    Returns:
        Dict containing current iteration info only
    """
    base_path = Path(project_dir)
    docs_path = base_path / "docs"

    # Import parse scripts
    scripts_path = Path(__file__).parent.parent / "skills" / "scripts"
    sys.path.insert(0, str(scripts_path))

    try:
        from parse_project_status import parse_project_status
        from parse_roadmap import parse_roadmap
    except ImportError:
        return {"error": "Failed to import parse scripts"}

    result = {}

    # Load only project status
    status_file = docs_path / "project-status.md"
    if status_file.exists():
        status = parse_project_status(str(status_file), use_cache=True)
        if "error" not in status:
            result["phase"] = status.get("phase")
            result["iteration"] = status.get("iteration")
            result["goal"] = status.get("iteration_goal")
            result["current_task"] = status.get("current_task")

    # Load current task from roadmap if available
    if result.get("current_task"):
        from parse_roadmap import get_task
        task = get_task(result["current_task"], str(docs_path / "roadmap.md"))
        if "error" not in task:
            result["task"] = {
                "id": task.get("id"),
                "title": task.get("title"),
                "status": task.get("status"),
                "priority": task.get("priority")
            }

    return result


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Load OpenUP project context")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--minimal", action="store_true", help="Load only current iteration context")
    parser.add_argument("--include", nargs="*", help="Additional docs to include")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    if args.minimal:
        result = get_current_iteration_context(args.project_dir)
    else:
        result = load_all_context(
            project_dir=args.project_dir,
            use_cache=not args.no_cache,
            include_docs=args.include
        )

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    main()

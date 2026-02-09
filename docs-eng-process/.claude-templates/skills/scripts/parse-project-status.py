#!/usr/bin/env python3
"""
Parse project status from docs/project-status.md

This script extracts phase, iteration, and goals from the project status file.
Returns JSON output for easy consumption by skills.
"""

import sys
import re
import json
from pathlib import Path


def parse_project_status(file_path="docs/project-status.md"):
    """
    Parse project status markdown file and extract key information.

    Args:
        file_path: Path to project-status.md file

    Returns:
        dict with keys: phase, iteration, iteration_goal, status, last_updated
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"Project status file not found: {file_path}"}

    content = path.read_text()

    result = {
        "phase": None,
        "iteration": None,
        "iteration_goal": None,
        "status": None,
        "last_updated": None,
        "updated_by": None
    }

    # Extract phase
    phase_match = re.search(r'phase:\s*(\w+)', content, re.IGNORECASE)
    if phase_match:
        result["phase"] = phase_match.group(1)

    # Extract iteration
    iter_match = re.search(r'iteration:\s*(\d+)', content, re.IGNORECASE)
    if iter_match:
        result["iteration"] = int(iter_match.group(1))

    # Extract iteration goal
    goal_match = re.search(r'iteration_goal:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if goal_match:
        result["iteration_goal"] = goal_match.group(1).strip()

    # Extract status
    status_match = re.search(r'status:\s*(\w+)', content, re.IGNORECASE)
    if status_match:
        result["status"] = status_match.group(1)

    # Extract last_updated
    updated_match = re.search(r'last_updated:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if updated_match:
        result["last_updated"] = updated_match.group(1).strip()

    # Extract updated_by
    by_match = re.search(r'updated_by:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if by_match:
        result["updated_by"] = by_match.group(1).strip()

    return result


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "docs/project-status.md"

    result = parse_project_status(file_path)

    # Output as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Parse roadmap from docs/roadmap.md

This script extracts task information from the roadmap file.
Returns JSON output for easy consumption by skills.
"""

import sys
import re
import json
from pathlib import Path


def parse_roadmap(file_path="docs/roadmap.md"):
    """
    Parse roadmap markdown file and extract task information.

    Args:
        file_path: Path to roadmap.md file

    Returns:
        dict with tasks array containing task information
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"Roadmap file not found: {file_path}"}

    content = path.read_text()

    result = {
        "tasks": [],
        "total": 0,
        "by_status": {}
    }

    # Find all task sections (e.g., ## T-001: Task name)
    task_pattern = re.compile(r'##\s+([Tt]-?\d+):\s*(.+?)(?=\n##|\Z)', re.DOTALL)
    tasks = task_pattern.findall(content)

    for task_id, task_content in tasks:
        task_info = {
            "id": task_id.upper(),
            "title": "",
            "status": None,
            "priority": None,
            "assigned_to": None,
            "description": "",
            "related_requirements": [],
            "related_risks": []
        }

        # Extract title (first line after heading)
        lines = task_content.strip().split('\n')
        if lines:
            task_info["title"] = lines[0].strip()

        # Extract status
        status_match = re.search(r'\*\*Status\*\*:\s*(\w+)', task_content, re.IGNORECASE)
        if status_match:
            task_info["status"] = status_match.group(1).lower()

        # Extract priority
        priority_match = re.search(r'\*\*Priority\*\*:\s*(\w+)', task_content, re.IGNORECASE)
        if priority_match:
            task_info["priority"] = priority_match.group(1).lower()

        # Extract assigned to
        assigned_match = re.search(r'\*\*Assigned to\*\*:\s*(.+?)(?:\n|$)', task_content, re.IGNORECASE)
        if assigned_match:
            task_info["assigned_to"] = assigned_match.group(1).strip()

        # Extract description
        desc_match = re.search(r'\*\*Description\*\*:\s*(.+?)(?:\n\*\*|\Z)', task_content, re.DOTALL | re.IGNORECASE)
        if desc_match:
            task_info["description"] = desc_match.group(1).strip()

        # Extract related requirements
        req_match = re.search(r'\*\*Related Requirements\*\*:\s*(.+?)(?:\n\*\*|\Z)', task_content, re.DOTALL | re.IGNORECASE)
        if req_match:
            reqs = re.findall(r'[Rr][Ee][Qq]-?\d+', req_match.group(1))
            task_info["related_requirements"] = reqs

        # Extract related risks
        risk_match = re.search(r'\*\*Related Risks\*\*:\s*(.+?)(?:\n\*\*|\Z)', task_content, re.DOTALL | re.IGNORECASE)
        if risk_match:
            risks = re.findall(r'[Rr]-?\d+', risk_match.group(1))
            task_info["related_risks"] = risks

        result["tasks"].append(task_info)

        # Track by status
        status = task_info["status"] or "unknown"
        if status not in result["by_status"]:
            result["by_status"][status] = 0
        result["by_status"][status] += 1

    result["total"] = len(result["tasks"])

    return result


def get_task(task_id, file_path="docs/roadmap.md"):
    """
    Get a specific task from the roadmap by ID.

    Args:
        task_id: Task ID (e.g., T-001)
        file_path: Path to roadmap.md file

    Returns:
        dict with task information or None if not found
    """
    result = parse_roadmap(file_path)

    if "error" in result:
        return result

    # Normalize task_id for matching
    task_id = task_id.upper().replace('T-', 'T').replace('T', 'T-')

    for task in result["tasks"]:
        if task["id"].upper() == task_id.upper():
            return task

    return {"error": f"Task {task_id} not found in roadmap"}


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--task" and len(sys.argv) > 2:
            # Get specific task
            result = get_task(sys.argv[2])
        else:
            # Parse custom file path
            result = parse_roadmap(sys.argv[1])
    else:
        result = parse_roadmap()

    # Output as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

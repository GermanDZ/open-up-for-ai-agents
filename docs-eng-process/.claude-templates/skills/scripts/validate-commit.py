#!/usr/bin/env python3
"""
Validate git commit success

This script verifies that a commit was successful and returns commit information.
Returns JSON output for easy consumption by skills.
"""

import sys
import subprocess
import json
import re


def get_latest_commit():
    """
    Get information about the latest commit.

    Returns:
        dict with commit info or error
    """
    try:
        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        sha = sha_result.stdout.strip()

        # Get commit info
        log_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%H|%an|%ae|%ai|%s"],
            capture_output=True,
            text=True,
            check=True
        )
        log_output = log_result.stdout.strip()

        parts = log_output.split('|')
        if len(parts) >= 5:
            return {
                "success": True,
                "sha": parts[0],
                "author_name": parts[1],
                "author_email": parts[2],
                "timestamp": parts[3],
                "message": parts[4]
            }

        return {
            "success": True,
            "sha": sha,
            "message": "Unable to parse full commit info"
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": f"Git command failed: {e.stderr.strip()}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def check_uncommitted_changes():
    """
    Check for uncommitted changes.

    Returns:
        dict with uncommitted status
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout.strip()

        if output:
            # Parse the output
            changes = []
            for line in output.split('\n'):
                if line:
                    status = line[:2]
                    path = line[3:]
                    changes.append({
                        "status": status,
                        "path": path
                    })

            return {
                "has_uncommitted": True,
                "count": len(changes),
                "changes": changes
            }

        return {
            "has_uncommitted": False,
            "count": 0,
            "changes": []
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"Git status failed: {e.stderr.strip()}"
        }


def validate_commit(expected_sha=None):
    """
    Validate that a commit was successful.

    Args:
        expected_sha: Optional expected commit SHA to verify

    Returns:
        dict with validation result
    """
    # Get latest commit
    commit_info = get_latest_commit()

    if not commit_info.get("success"):
        return {
            "valid": False,
            "error": commit_info.get("error", "Unknown error")
        }

    # Check uncommitted changes
    uncommitted_info = check_uncommitted_changes()

    result = {
        "valid": True,
        "commit": commit_info,
        "uncommitted": uncommitted_info
    }

    # Verify SHA if expected
    if expected_sha:
        actual_sha = commit_info.get("sha")
        if actual_sha != expected_sha:
            result["valid"] = False
            result["error"] = f"SHA mismatch: expected {expected_sha}, got {actual_sha}"

    return result


def main():
    """Main entry point for CLI usage."""
    expected_sha = None

    if len(sys.argv) > 1:
        expected_sha = sys.argv[1]

    result = validate_commit(expected_sha)

    # Output as JSON
    print(json.dumps(result, indent=2))

    # Exit with error code if invalid
    if not result.get("valid", True):
        sys.exit(1)


if __name__ == "__main__":
    main()

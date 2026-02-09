#!/usr/bin/env python3
"""
Detect trunk branch name

This script detects the trunk (main/master) branch using git commands.
Follows the algorithm: origin/HEAD -> main -> master -> develop -> development
Returns JSON output for easy consumption by skills.
"""

import sys
import subprocess
import json


def detect_trunk():
    """
    Detect the trunk branch name using git commands.

    Algorithm:
    1. Check origin/HEAD symbolic reference
    2. Fallback to common names: main, master, develop, development
    3. Final fallback: current branch's remote tracking branch

    Returns:
        dict with detected trunk branch and method used
    """
    result = {
        "trunk": None,
        "method": None,
        "all_candidates": []
    }

    # Method 1: Check origin/HEAD symbolic reference
    try:
        origin_head = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=False
        )

        if origin_head.returncode == 0:
            # Output format: refs/remotes/origin/<branch-name>
            ref = origin_head.stdout.strip()
            branch = ref.replace('refs/remotes/origin/', '')
            result["trunk"] = branch
            result["method"] = "origin/HEAD"
            result["all_candidates"].append(branch)
            return result

    except Exception:
        pass

    # Method 2: Check common branch names
    common_names = ["main", "master", "develop", "development"]

    for branch in common_names:
        try:
            # Check if branch exists locally or remotely
            local_check = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
                capture_output=True,
                check=False
            )

            remote_check = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
                capture_output=True,
                check=False
            )

            if local_check.returncode == 0 or remote_check.returncode == 0:
                result["trunk"] = branch
                result["method"] = f"common-name ({branch})"
                result["all_candidates"].append(branch)
                return result

        except Exception:
            continue

    # Method 3: Current branch's remote tracking branch
    try:
        upstream = subprocess.run(
            ["git", "for-each-ref", "--format=%(upstream:short)", "$(git symbolic-ref -q HEAD)"],
            capture_output=True,
            text=True,
            shell=True,
            check=False
        )

        if upstream.returncode == 0 and upstream.stdout.strip():
            branch = upstream.stdout.strip().split('/')[-1]
            result["trunk"] = branch
            result["method"] = "upstream"
            result["all_candidates"].append(branch)
            return result

    except Exception:
        pass

    # Method 4: Absolute fallback - check current branch
    try:
        current = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )

        branch = current.stdout.strip()
        if branch and branch != "HEAD":
            result["trunk"] = branch
            result["method"] = "current-branch-fallback"
            result["all_candidates"].append(branch)
            return result

    except Exception:
        pass

    # Could not detect
    result["error"] = "Could not detect trunk branch"
    return result


def main():
    """Main entry point for CLI usage."""
    result = detect_trunk()

    # Output as JSON
    print(json.dumps(result, indent=2))

    # Exit with error code if trunk not detected
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()

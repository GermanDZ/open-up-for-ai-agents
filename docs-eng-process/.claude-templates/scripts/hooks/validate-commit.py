#!/usr/bin/env python3
"""
validate-commit.py — OpenUP hook: fires before every Bash tool call.

Intercepts `git commit` commands and validates that the commit message
follows the canonical OpenUP format:

  type(scope): description [T-XXX]

Where:
  type   = feat | fix | refactor | test | docs | chore | style | perf | ci
  scope  = affected module/area (optional but encouraged)
  T-XXX  = task ID from roadmap (optional but encouraged for traceability)

Examples:
  feat(auth): add JWT validation [T-007]
  fix(api): handle null response from third-party service
  docs: update architecture notebook for new caching layer

Exit codes:
  0 — not a git commit, OR commit message is valid — allow the command
  2 — commit message is malformed — block with helpful error on stderr

Hook event: PreToolUse / Bash
"""

import json
import re
import sys

VALID_TYPES = {
    "feat", "fix", "refactor", "test", "docs", "chore",
    "style", "perf", "ci", "build", "revert", "quick",
}

# Canonical format: type(scope): description  (task id optional)
PATTERN = re.compile(
    r"^("
    + "|".join(VALID_TYPES)
    + r")(\([^)]+\))?!?: .{3,}"
)

# Patterns that indicate this bash command is a git commit
COMMIT_RE = re.compile(r'\bgit\b.*\bcommit\b', re.DOTALL)

# Extract -m / --message value (handles single and double quotes)
MSG_RE = re.compile(
    r"""(?:-m|--message)\s+(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""",
    re.DOTALL,
)


def extract_commit_message(command: str) -> str | None:
    """Return the commit message string, or None if we can't extract it."""
    m = MSG_RE.search(command)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip()


def first_line(msg: str) -> str:
    return msg.split("\n")[0].strip()


def main() -> None:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")

    # Only act on git commit commands
    if not COMMIT_RE.search(command):
        sys.exit(0)

    # Skip --amend without -m (uses existing message)
    if "--amend" in command and not re.search(r"(?:-m|--message)\s", command):
        sys.exit(0)

    # Skip --allow-empty-message
    if "--allow-empty-message" in command:
        sys.exit(0)

    msg = extract_commit_message(command)
    if msg is None:
        # Can't extract message (e.g. uses heredoc or -F flag) — allow through
        sys.exit(0)

    subject = first_line(msg)

    # Check for "Co-Authored-By" trailer only — those are fine
    if subject.startswith("Co-Authored-By"):
        sys.exit(0)

    if PATTERN.match(subject):
        sys.exit(0)

    # Malformed — block with a helpful message
    print(
        f"[validate-commit] ❌ Commit message does not follow the canonical format.\n\n"
        f"  Your message:    {subject!r}\n\n"
        f"  Required format: type(scope): description [T-XXX]\n"
        f"  Valid types:     {', '.join(sorted(VALID_TYPES))}\n\n"
        f"  Examples:\n"
        f"    feat(auth): add JWT token validation [T-007]\n"
        f"    fix(api): handle null upstream response\n"
        f"    docs: update architecture notebook\n"
        f"    refactor(cache): simplify TTL calculation [T-012]\n\n"
        f"Please rewrite the commit message to match the format, then retry.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()

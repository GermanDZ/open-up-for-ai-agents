#!/usr/bin/env bash
#
# run-tests.sh — the whole project test suite, in one command (T-160).
#
# WHY THIS EXISTS
# ---------------
# This repo has TWO project test directories, and nothing named a test command,
# so "full suite" was free prose in completion notes. Three consecutive lanes
# (T-155, T-157, T-158) reported the `scripts/tests/` figure alone as the "full
# suite" — omitting `tests/` and its 114 tests, among them
# `tests/test_claims_heartbeat_reap.py`, the coverage most relevant to the very
# defect T-159 went on to fix. No regression resulted, but the claims were
# narrower than their wording.
#
# From now on: "full suite" means THIS SCRIPT.
#
# The directory list is ENUMERATED, not discovered. Discovery would sweep
# `venv/` and `.claude/worktrees/`, both of which contain `test_*.py`, and
# excluding those is a denylist that rots silently. Instead the list is explicit
# and `scripts/tests/test_full_suite_runner.py` fails when a new top-level test
# directory appears that is not in it — a loud failure rather than a quiet gap.
#
# Usage:
#   scripts/run-tests.sh              # every project test directory
#   scripts/run-tests.sh -x           # extra args are passed through to pytest
#
# Exit code: 0 only if EVERY directory passed; otherwise the first failing
# directory's code. Never masks a failure.

set -uo pipefail

# The project's test directories. Keep in sync with the guard test — adding a
# directory here without adding it there (or vice versa) fails the guard.
TEST_DIRS=(
  "scripts/tests"
  "tests"
)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root" || exit 1

# Prefer the interpreter that actually has pytest. A bare `python3` on this
# machine resolves to one without it, which is its own silent-failure trap.
if command -v asdf >/dev/null 2>&1 && asdf exec python3 -m pytest --version >/dev/null 2>&1; then
  PY=(asdf exec python3)
elif python3 -m pytest --version >/dev/null 2>&1; then
  PY=(python3)
else
  echo "run-tests: pytest is not available to python3 or 'asdf exec python3'." >&2
  exit 1
fi

overall=0
declare -a summary=()

for d in "${TEST_DIRS[@]}"; do
  if [ ! -d "$d" ]; then
    echo "run-tests: MISSING directory '$d' — the list in this script is stale." >&2
    overall=1
    summary+=("$d: MISSING")
    continue
  fi
  echo "=== $d ==="
  "${PY[@]}" -m pytest "$d" "$@"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    # Keep the FIRST failing code; do not let a later pass overwrite it.
    [ "$overall" -eq 0 ] && overall="$rc"
    summary+=("$d: FAILED (exit $rc)")
  else
    summary+=("$d: passed")
  fi
done

echo
echo "=== full suite summary ==="
for line in "${summary[@]}"; do
  echo "  $line"
done
if [ "$overall" -eq 0 ]; then
  echo "full suite: PASSED (${#TEST_DIRS[@]} directories)"
else
  echo "full suite: FAILED (exit $overall)"
fi
exit "$overall"

#!/usr/bin/env bash
# openup-loop.sh — drive /openup-next in a fresh-process loop until done or capped.
# Each cycle is a separate `claude -p` process (cold context, minimal tokens).
#
# Usage: scripts/openup-loop.sh [--max-cycles N] [--stall-limit N] [--task-id T-NNN]
#
# Exit codes:
#   0  Clean stop: OPENUP-NEXT: DONE received
#   1  Cycle cap hit (--max-cycles reached without DONE)
#   2  Stall limit hit (same task produced ADVANCED exits --stall-limit times in a row)
#   3  Unexpected exit from claude -p (no sentinel line found)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MAX_CYCLES=50
STALL_LIMIT=3
TASK_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-cycles) MAX_CYCLES="$2"; shift 2 ;;
    --stall-limit) STALL_LIMIT="$2"; shift 2 ;;
    --task-id) TASK_ARG="task_id: $2"; shift 2 ;;
    --help|-h)
      echo "Usage: scripts/openup-loop.sh [--max-cycles N] [--stall-limit N] [--task-id T-NNN]"
      echo ""
      echo "Drive /openup-next in a fresh-process loop until done or capped."
      echo "Each cycle runs a separate 'claude -p' process (cold context)."
      echo ""
      echo "Options:"
      echo "  --max-cycles N    Stop after N cycles even without a DONE sentinel (default: 50)"
      echo "  --stall-limit N   Stop if the same task-id appears ADVANCED N times in a row (default: 3)"
      echo "  --task-id T-NNN   Pass a task_id argument to /openup-next each cycle"
      echo ""
      echo "Exit codes:"
      echo "  0  Clean stop: OPENUP-NEXT: DONE received"
      echo "  1  Cycle cap hit without DONE"
      echo "  2  Stall limit hit (same task stalled N times)"
      echo "  3  No sentinel line found in output (fail-safe)"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; echo "Run with --help for usage." >&2; exit 1 ;;
  esac
done

PROMPT="/openup-next${TASK_ARG:+ $TASK_ARG}"
stall_task=""
stall_count=0
cycle=0

echo "[openup-loop] Starting — max-cycles=$MAX_CYCLES stall-limit=$STALL_LIMIT"
echo "[openup-loop] Prompt: $PROMPT"

while (( cycle < MAX_CYCLES )); do
  cycle=$(( cycle + 1 ))
  echo ""
  echo "[openup-loop] === Cycle $cycle / $MAX_CYCLES ==="

  # No-op pre-check (T-065): resolve the §0–§1 decision as data BEFORE spawning a
  # cycle process. When the board resolves to `noop`, there is nothing to do — stop
  # cleanly without paying for a `claude -p` process. `resolve` is read-only and
  # always exits 0; a parse/tooling failure falls through to the normal cycle
  # (fail-open — never skip real work on a bad read).
  precheck=$(python3 "$SCRIPT_DIR/openup-board.py" resolve 2>/dev/null || true)
  if echo "$precheck" | grep -Eq '"path":[[:space:]]*"noop"'; then
    reason=$(echo "$precheck" | grep -o '"reason":[[:space:]]*"[^"]*"' | sed 's/.*"reason":[[:space:]]*"//;s/"$//' || true)
    echo "[openup-loop] Board resolves to no-op — stopping without spawning a cycle: ${reason:-nothing to do}"
    exit 0
  fi

  out=$(claude -p "$PROMPT" 2>&1)
  echo "$out"

  sentinel=$(echo "$out" | grep -E "^OPENUP-NEXT: (ADVANCED|DONE)" | tail -1 || true)

  if [[ -z "$sentinel" ]]; then
    echo "" >&2
    echo "[openup-loop] ERROR: no sentinel line found in cycle $cycle output — treating as DONE (fail-safe)" >&2
    exit 3
  fi

  if echo "$sentinel" | grep -q "^OPENUP-NEXT: DONE"; then
    reason=$(echo "$sentinel" | sed 's/^OPENUP-NEXT: DONE — //')
    echo ""
    echo "[openup-loop] Stopped cleanly after $cycle cycle(s): $reason"
    exit 0
  fi

  # ADVANCED — extract task-id and check for stall
  adv_task=$(echo "$sentinel" | sed 's/^OPENUP-NEXT: ADVANCED — //')
  if [[ "$adv_task" == "$stall_task" ]]; then
    stall_count=$(( stall_count + 1 ))
    echo "[openup-loop] Stall counter: $adv_task ($stall_count / $STALL_LIMIT)"
    if (( stall_count >= STALL_LIMIT )); then
      echo "" >&2
      echo "[openup-loop] STALL: $adv_task produced ADVANCED exits $stall_count times in a row without advancing to another task" >&2
      echo "[openup-loop] The lane may be stuck on a repeating question — check docs/input-requests/ and the lane's plan.md" >&2
      exit 2
    fi
  else
    stall_task="$adv_task"
    stall_count=1
  fi
done

echo "" >&2
echo "[openup-loop] Cycle cap ($MAX_CYCLES) reached without a DONE sentinel" >&2
exit 1

---
type: iteration-plan
id: T-059
status: implemented
title: "Loop support for /openup-next — sentinel output, loop section, openup-loop.sh"
traces-from: []
verified-by: []
---

# T-059: Loop Support for /openup-next

**Phase**: construction
**Status**: pending
**Goal**: Make `/openup-next` reliably driveable by an outer loop — a shell script, `/loop`, or cron — via a machine-readable sentinel, an explicit loop-behavior section in the skill, and a safe wrapper script.
**Priority**: high

---

## Context

`/openup-next` was designed for an outer loop: its `fit:` frontmatter names *"an outer /loop or cron repeatedly advancing the roadmap"* as a great-fit case, and its legal-exit model ensures all continuation state lives in the repo, not the conversation. But the loop has no reliable stop signal: a shell loop or `/loop` invocation must interpret free-form prose to know whether the cycle *advanced* or hit a *clean no-op* (drained board / blocked lanes / phase done). Without a sentinel, the outer loop must be manually stopped, can't self-terminate when the backlog is exhausted, and can't distinguish "no work left" from a crash.

This task closes the three gaps that make `/loop /openup-next` production-ready:

1. **Sentinel** — a stable last line on every `/openup-next` exit so any outer loop can pattern-match `ADVANCED` vs `DONE` without parsing prose.
2. **Loop-behavior section** in the skill — makes the stop/continue rule explicit and model-agnostic across sessions.
3. **`scripts/openup-loop.sh`** — ships the recommended shell-loop driver with a cycle cap, sentinel check, and per-run budget guard baked in.

---

## Current State

### `/openup-next` output section (`skills/openup-next/SKILL.md:Output`)

```markdown
## Output

A compact summary (≤6 bullets): which path ran (**resumed** / **picked** /
**promoted+started**, or the **clean no-op** reason), the lane and hat, what
landed, which boxes are now ticked, and which legal exit was taken.
```

No sentinel line. No loop-behavior instructions.

### `/openup-next` fit metadata

```yaml
fit:
  great: [... an outer /loop or cron repeatedly advancing the roadmap ...]
```

Named as a great-fit use case but the skill gives no instructions for it.

### No `scripts/openup-loop.sh`

There is no wrapper script. Users must write their own shell loop against `claude -p /openup-next` and manually decide the stop condition.

### `/loop` skill behavior (system-level)

`/loop` in dynamic mode (no interval) re-fires the prompt via `ScheduleWakeup` in the same conversation — context accumulates each tick. `/openup-next` is already repo-stateful so a fresh-process model (shell loop over `claude -p`) is the correct choice for production; `/loop` is useful for interactive sessions where the user wants to watch progress in one window.

---

## Proposed Design

### Change 1: Add sentinel to `/openup-next` Output section

**File**: `.claude/skills/openup-next/SKILL.md`

Add to the `## Output` section:

```markdown
### Sentinel line (machine-readable, always last)

Every exit — ADVANCED or DONE — must end with exactly one of these lines as the
very last line of output, with nothing after it:

```
OPENUP-NEXT: ADVANCED — <task-id>
OPENUP-NEXT: DONE — <reason>
```

`ADVANCED` means a lane was worked this cycle (resumed, picked, or promoted+started).
`DONE` means a clean no-op: either every lane is blocked/suspended/elsewhere, or the
roadmap has no pickable pending task. The `<reason>` on DONE names the specific
condition (e.g. "board empty — all lanes done", "roadmap exhausted — phase review
needed", "all lanes blocked or suspended"). An outer loop MUST stop on `DONE` and
continue on `ADVANCED`. Any exit that is neither is a crash; treat it as `DONE`
(fail-safe stop).
```

### Change 2: Add "When driven by an outer loop" section to `/openup-next`

**File**: `.claude/skills/openup-next/SKILL.md`

Add a new section after `## See Also`:

```markdown
## When Driven by an Outer Loop

`/openup-next` is designed to be re-invoked repeatedly by an outer driver — a
shell script (`openup-loop.sh`), `/loop`, or a cron job. The repo carries all
continuation state; each invocation starts cold.

**Stop rule (mandatory):** after every exit, check the last output line:
- `OPENUP-NEXT: ADVANCED — …` → schedule another invocation immediately (or
  after a short yield — never sleep longer than the worktree's expected cycle
  time).
- `OPENUP-NEXT: DONE — …` → stop the outer loop. Do not reinvoke. Surface the
  reason to the user.
- Anything else → treat as `DONE` (fail-safe stop; investigate the exit).

**Context model:** each invocation reads the repo from scratch. Nothing from a
prior invocation's conversation lives into the next. This is a feature — context
stays minimal every cycle regardless of how many cycles have run.

**Under `/loop` (interactive):** `/loop /openup-next` works but accumulates
context across ticks (same conversation). For long runs, prefer `openup-loop.sh`
(fresh `claude -p` process per cycle, truly cold context). Use `/loop` when you
want to watch progress interactively and the run is short (≤ ~10 cycles).

**Stall detection:** if the same task produces `create-handoff` exits N cycles in
a row (the lane keeps suspending on the same question), the outer loop should
stop and surface the stall rather than spinning. `openup-loop.sh` implements this
with `--stall-limit N` (default 3).
```

### Change 3: Add `scripts/openup-loop.sh`

**New file**: `scripts/openup-loop.sh`

```bash
#!/usr/bin/env bash
# openup-loop.sh — drive /openup-next in a fresh-process loop until done or capped.
# Each cycle is a separate `claude -p` process (cold context, minimal tokens).
#
# Usage: scripts/openup-loop.sh [--max-cycles N] [--stall-limit N] [--task-id T-NNN]
#
# Exit codes:
#   0  Clean stop: OPENUP-NEXT: DONE received
#   1  Cycle cap hit (--max-cycles reached without DONE)
#   2  Stall limit hit (same task produced handoff exits --stall-limit times)
#   3  Unexpected exit from claude -p (no sentinel line)

set -euo pipefail

MAX_CYCLES=50
STALL_LIMIT=3
TASK_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-cycles) MAX_CYCLES="$2"; shift 2 ;;
    --stall-limit) STALL_LIMIT="$2"; shift 2 ;;
    --task-id) TASK_ARG="task_id: $2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
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

  out=$(claude -p "$PROMPT" 2>&1)
  echo "$out"

  sentinel=$(echo "$out" | grep -E "^OPENUP-NEXT: (ADVANCED|DONE)" | tail -1 || true)

  if [[ -z "$sentinel" ]]; then
    echo "[openup-loop] ERROR: no sentinel line found — treating as DONE (fail-safe)" >&2
    exit 3
  fi

  if echo "$sentinel" | grep -q "^OPENUP-NEXT: DONE"; then
    reason=$(echo "$sentinel" | sed 's/^OPENUP-NEXT: DONE — //')
    echo ""
    echo "[openup-loop] Stopped cleanly after $cycle cycle(s): $reason"
    exit 0
  fi

  # ADVANCED — check for stall
  adv_task=$(echo "$sentinel" | sed 's/^OPENUP-NEXT: ADVANCED — //')
  if [[ "$adv_task" == "$stall_task" ]]; then
    stall_count=$(( stall_count + 1 ))
    if (( stall_count >= STALL_LIMIT )); then
      echo "[openup-loop] STALL: $adv_task produced handoff exit $stall_count times in a row" >&2
      exit 2
    fi
  else
    stall_task="$adv_task"
    stall_count=1
  fi
done

echo "[openup-loop] Cycle cap ($MAX_CYCLES) reached without DONE" >&2
exit 1
```

Also add an entry to `scripts/process-manifest.txt` so `sync-from-framework.sh` ships it to consuming projects.

---

## Acceptance Criteria

- [ ] Every `/openup-next` exit (ADVANCED and DONE, all sub-paths: resume/pick/promote/no-op) ends with exactly one `OPENUP-NEXT: ADVANCED — <task>` or `OPENUP-NEXT: DONE — <reason>` line as the last line of output.
- [ ] The `## When Driven by an Outer Loop` section exists in `openup-next/SKILL.md` and covers: stop rule, context model, `/loop` vs shell-loop trade-off, stall detection.
- [ ] `scripts/openup-loop.sh` exists, is executable, and exits 0 on a DONE sentinel, 1 on max-cycles, 2 on stall, 3 on missing sentinel.
- [ ] `openup-loop.sh --help` (or running with bad args) prints usage without crashing.
- [ ] `openup-loop.sh` is listed in `scripts/process-manifest.txt`.
- [ ] `.claude-templates/` is synced to `.claude/` (sentinel instruction lands in the templates copy).

---

## Success Measure

n/a — internal tooling; no user-facing metric. Falsifiable via the acceptance criteria above (sentinel present on all exits, script behaves correctly on exit codes).

---

## Testing Strategy

- **Unit (hermetic):** mock `claude -p` with scripts that emit fixed output; verify `openup-loop.sh` exit codes for DONE, ADVANCED, cap, stall, no-sentinel.
- **Integration:** run a 2-cycle scenario against a test roadmap; verify the sentinel appears on stdout and the loop stops on DONE.
- **Skill output check:** review the `## Output` and `## When Driven by an Outer Loop` sections pass the iteration-plan rubric criterion on failable acceptance criteria.

---

## Dependencies

None — T-059 is self-contained.

---

## Key Files

| File | Change |
|------|--------|
| `.claude/skills/openup-next/SKILL.md` | Add sentinel spec to Output section + new loop-behavior section |
| `.claude-templates/skills/openup-next/SKILL.md` | Keep in sync (templates canonical) |
| `scripts/openup-loop.sh` | New wrapper script |
| `scripts/process-manifest.txt` | Add `openup-loop.sh` entry |

---

## Out of Scope

- Parallel/fan-out execution (T-060).
- Cron scheduling (`/schedule` skill handles that separately).
- Modifying `/loop` skill internals (system-level, not project-owned).

---

## Open Questions

1. **Assumed: sentinel on stdout** (not stderr) so `$(claude -p …)` captures it without `2>&1`. Vetoable at review if a stderr sentinel is preferred for log separation.
2. **Assumed: stall detection is on consecutive handoff exits for the same task-id**, not on identical sentinel lines. Vetoable if a simpler "same sentinel N times" check is preferred.

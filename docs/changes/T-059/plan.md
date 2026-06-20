---
id: T-059
title: "Loop support for /openup-next — sentinel output, loop section, openup-loop.sh"
status: ready
priority: high
estimate: 1 session
plan: docs/iteration-plans/t-059-loop-support-openup-next.md
depends-on: []
blocks: [T-060]
last-synced: ""
touches:
  - docs-eng-process/.claude-templates/skills/openup-next/SKILL.md
  - .claude/skills/openup-next/SKILL.md
  - scripts/openup-loop.sh
  - scripts/process-manifest.txt
---

# T-059 — Loop support for /openup-next

## Story

> **As a** practitioner running `/openup-next` from a shell script or cron job
> **I want** a machine-readable sentinel on every exit and a safe wrapper script
> **So that** I can drain the backlog unattended without parsing prose or writing a custom loop driver

INVEST check:
✅ Independent (no unmet deps) · ✅ Negotiable (sentinel format and stall logic vetoable at review) · ✅ Valuable (enables unattended roadmap drain; prerequisite for T-060) · ✅ Estimable (1 session, ~80 LOC shell + ~40 lines markdown) · ✅ Small (4 files, 2 new sections, 1 new script) · ✅ Testable (sentinel regex, exit codes, diff check)

## Analysis Context

- **Domain.** The `/openup-next` skill's machine interface and the `scripts/` runtime distributed to consuming projects via `sync-from-framework.sh`.
- **Scope boundaries.** This task does NOT cover: parallel fan-out (T-060), cron scheduling (handled by the `/schedule` skill), modifying `/loop` skill internals (system-level, not project-owned), or changes to any `openup-board.py` / `openup-claims.py` scripts.
- **Definition of done.** Every `/openup-next` exit ends with a `OPENUP-NEXT: ADVANCED — <task>` or `OPENUP-NEXT: DONE — <reason>` line; `scripts/openup-loop.sh` exists, is executable, and exits 0/1/2/3 as specified; both the templates and deployed skill copies are updated; the manifest entry is present.

> **Assumption:** Sentinel is emitted on stdout (not stderr) so `$(claude -p …)` captures it without `2>&1`. *(Vetoable at review — if stderr is preferred for log separation, the loop script and test harness need updating.)*

> **Assumption:** Stall detection triggers on consecutive `create-handoff` exits for the same task-id returned by the ADVANCED sentinel, not on identical sentinel lines. *(Vetoable at review.)*

## Requirements

1. Every `/openup-next` exit — ADVANCED and DONE, covering all sub-paths (resume, pick, promote, no-op) — ends with exactly one sentinel line as the very last line of output: `OPENUP-NEXT: ADVANCED — <task-id>` or `OPENUP-NEXT: DONE — <reason>`.
   - **Given** an outer loop invokes `claude -p /openup-next` and a ready lane is available **When** the cycle completes (via complete-task or handoff) **Then** the last line of stdout matches `^OPENUP-NEXT: ADVANCED — .+$`
   - **Given** an outer loop invokes `claude -p /openup-next` and the board has no pickable lane and the roadmap has no promotable task **When** the no-op path runs **Then** the last line of stdout matches `^OPENUP-NEXT: DONE — .+$`

2. The `## When Driven by an Outer Loop` section exists in `openup-next/SKILL.md` (both the `docs-eng-process/.claude-templates/` and `.claude/` copies) and covers: stop rule, context model, `/loop` vs shell-loop trade-off, and stall detection.
   - **Given** a model reads the skill file cold **When** it looks for loop-driving instructions **Then** it finds the `## When Driven by an Outer Loop` section with an explicit stop rule (ADVANCED → continue, DONE → stop, else fail-safe stop)

3. `scripts/openup-loop.sh` exists, is executable, accepts `--max-cycles N`, `--stall-limit N`, `--task-id T-NNN` flags, and exits with the correct codes:
   - exit 0: DONE sentinel received
   - exit 1: `--max-cycles` cap reached without DONE
   - exit 2: stall limit hit (same task produced ADVANCED exits `--stall-limit` consecutive times without a different task in between)
   - exit 3: no sentinel line found in output (fail-safe)
   - **Given** `openup-loop.sh` receives a mock `claude -p` that outputs `OPENUP-NEXT: DONE — board empty` **When** the loop processes that output **Then** it exits 0
   - **Given** `openup-loop.sh` is called with `--max-cycles 1` and the mock outputs one ADVANCED line **When** the cap is reached **Then** it exits 1 without spawning another cycle
   - **Given** `openup-loop.sh` is called with `--stall-limit 2` and the mock outputs the same task-id ADVANCED twice consecutively **When** the stall count reaches 2 **Then** it exits 2
   - **Given** `openup-loop.sh` receives a mock that outputs no sentinel line **When** the sentinel grep finds nothing **Then** it exits 3

4. `scripts/openup-loop.sh` is listed in `scripts/process-manifest.txt` under the `scripts/` section so it is distributed to consuming projects.
   - **Given** `openup-loop.sh` is added to `process-manifest.txt` **When** `sync-from-framework.sh` runs in a consuming project **Then** `scripts/openup-loop.sh` is copied to that project's `scripts/` directory

5. The `.claude/skills/openup-next/SKILL.md` is identical to `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` after the task (templates are canonical; `.claude/` is the deployed copy).
   - **Given** both files have been edited **When** `diff docs-eng-process/.claude-templates/skills/openup-next/SKILL.md .claude/skills/openup-next/SKILL.md` runs **Then** it exits 0 (no diff)

## Behavior Delta

n/a — all Added (no pre-existing sentinel protocol, loop-behavior section, or loop wrapper script in Ring 1).

**Added:**
- Sentinel line protocol on every `/openup-next` exit: `OPENUP-NEXT: ADVANCED — <task-id>` or `OPENUP-NEXT: DONE — <reason>` as the very last line of stdout
- `## When Driven by an Outer Loop` section in `openup-next/SKILL.md` covering stop rule, context model, `/loop` vs shell-loop trade-off, stall detection
- `scripts/openup-loop.sh` — shell wrapper with cycle cap, stall detection, and sentinel-based stop (exit codes 0/1/2/3, flags `--max-cycles`, `--stall-limit`, `--task-id`)
- `scripts/openup-loop.sh` entry in `scripts/process-manifest.txt`

## Entities

- **`SKILL.md` (openup-next)** (modified) — `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` and `.claude/skills/openup-next/SKILL.md`
- **`openup-loop.sh`** (new) — `scripts/openup-loop.sh`
- **`process-manifest.txt`** (modified) — `scripts/process-manifest.txt`

## Approach

Extend the `/openup-next` skill by appending a sentinel contract to its `## Output` section and adding an explicit `## When Driven by an Outer Loop` section that gives any outer driver a model-agnostic stop rule. Ship `scripts/openup-loop.sh` as the recommended shell driver — a thin `claude -p` wrapper with a cycle cap, stall-detection counter, and sentinel-based exit — and register it in `scripts/process-manifest.txt` so it reaches consuming projects through the standard sync path. The templates copy (`docs-eng-process/.claude-templates/`) is the source of truth; the deployed copy (`.claude/`) must stay byte-for-byte identical.

## Structure

**Add:**
- `scripts/openup-loop.sh` — new wrapper script (~80 LOC bash; `set -euo pipefail`; exit codes 0/1/2/3)

**Modify:**
- `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` — append sentinel spec to `## Output`; add `## When Driven by an Outer Loop` section after `## See Also`
- `.claude/skills/openup-next/SKILL.md` — same edits (must stay in sync with templates copy)
- `scripts/process-manifest.txt` — add `scripts/openup-loop.sh` entry

**Do not touch:**
- `scripts/openup-board.py` — board extensions belong to T-060 (`top-n` subcommand)
- `scripts/openup-claims.py` — heartbeat/reap subcommands belong to T-060
- Any other file in `.claude/skills/openup-next/` — scope is `SKILL.md` only

## Operations

- [x] Edit `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md`: append sentinel spec (ADVANCED/DONE format, fail-safe rule) to `## Output` section and add `## When Driven by an Outer Loop` section after `## See Also`
- [x] Copy the same edits to `.claude/skills/openup-next/SKILL.md`; verify with `diff docs-eng-process/.claude-templates/skills/openup-next/SKILL.md .claude/skills/openup-next/SKILL.md` → must exit 0
- [x] Create `scripts/openup-loop.sh` with `set -euo pipefail`, flags `--max-cycles` (default 50), `--stall-limit` (default 3), `--task-id`; sentinel grep; exit codes 0/1/2/3; then `chmod +x scripts/openup-loop.sh`
- [x] Add `scripts/openup-loop.sh` entry to `scripts/process-manifest.txt` under the scripts section
- [x] (tester) Verify all acceptance criteria: sentinel grep in both SKILL.md copies, `diff` exits 0, `test -x scripts/openup-loop.sh`, manifest entry present; run mock exit-code tests for all four exit paths

## Success Measures

n/a — internal tooling with no user-facing metric. Falsifiable via the acceptance criteria above (sentinel present on all exits, script exits correctly for all four scenarios, diff clean).

## Rollout

n/a — internal framework tooling, not user-facing. The changes reach consuming projects when they next run `sync-from-framework.sh`; no flag or phased rollout needed.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, branch naming, etc.)
- `docs-eng-process/script-cli-reference.md` — CLI signature conventions for scripts in `scripts/`

## Safeguards

- **No-go zones.** Do not modify `openup-board.py`, `openup-claims.py`, or any file in `scripts/` other than `process-manifest.txt` and the new `openup-loop.sh`. T-060 owns those extension points.
- **Templates canonical.** `docs-eng-process/.claude-templates/` is the source of truth; `.claude/` must match byte-for-byte. Edit templates first, then copy.
- **Reversibility.** All changes are additive (new sections, new file) or append-only to the manifest. Rolling back is `git revert` with no data concerns.
- **Token budget.** Implementation is ~80 LOC shell + ~40 lines markdown. If scope grows significantly, re-examine whether T-060 scope crept in.

## Verification

- `grep -c "OPENUP-NEXT:" docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` → ≥1
- `grep -c "When Driven by an Outer Loop" docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` → ≥1
- `diff docs-eng-process/.claude-templates/skills/openup-next/SKILL.md .claude/skills/openup-next/SKILL.md` → exit 0
- `test -x scripts/openup-loop.sh` → exit 0
- `grep "openup-loop.sh" scripts/process-manifest.txt` → finds the entry
- Mock exit-code test: `CLAUDE_P_OUT="OPENUP-NEXT: DONE — board empty" scripts/openup-loop-test.sh` → exit 0 (or equivalent in-test assertion)
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-059/plan.md` → exit 0

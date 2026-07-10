---
id: T-065
title: "openup-board.py status/resolve verb + skill slimming"
status: ready
priority: high
estimate: 1 session
plan: docs/iteration-plans/t-065-openup-board-resolve-skill-slimming.md
depends-on: [T-064]
blocks: []
touches: [scripts/openup-board.py, scripts/tests/test_openup_board_resolve.py, scripts/openup-loop.sh, scripts/process-manifest.txt, docs-eng-process/script-cli-reference.md, docs-eng-process/.claude-templates/skills/openup-next/SKILL.md, docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md, .claude/skills/openup-start-iteration/SKILL.md, docs-eng-process/skills-guide.md]
last-synced: ""
---

# T-065 — openup-board.py status/resolve verb + skill slimming

## Story

> **As a** solo developer (or unattended loop) running `/openup-next` cycle after cycle
> **I want** the "where are we?" precedence answered by one deterministic script call
> **So that** each cycle stops paying a multi-call read-chain + double-read + heavy skill prose just to learn its next move

INVEST check:
✅ Independent (composes over shipped T-063/T-064 verbs; no new state) · ✅ Negotiable (line budget, exact JSON keys open) · ✅ Valuable (per-cycle token drop, compounding) · ✅ Estimable (one script verb pair + two skill edits + a shell pre-check) · ✅ Small (1 session) · ✅ Testable (path fixtures, read-only assertion, line budget)

## Analysis Context

- **Domain.** The `/openup-next` sequential continue-loop's state-discovery phase — §0–§1 precedence (resume → pick → promote → no-op) currently executed by the model across a chain of Bash calls plus a re-read inside `/openup-start-iteration`.
- **Scope boundaries.** This task does NOT change *what* the precedence decides (T-064 already made promote-selection deterministic) — it collapses *how* the decision is gathered into one call and trims the prose that describes the now-scripted mechanics. It does **not** move the live reap out of `refresh` (that stays a write path), does not touch the two-legal-exits contract, and does not alter the sentinel line.
- **Definition of done.** `openup-board.py resolve` returns the whole §0–§1 decision as one ≤~40-line read-only JSON object; `openup-board.py status` returns the superset human diagnostic; `/openup-next` §0–§1 is a single `resolve` call + branch on `.path`; `/openup-start-iteration` skips its status/roadmap re-read when handed a pre-resolved lane; `openup-loop.sh` short-circuits on `path:"noop"` without spawning a cycle process; reference + manifest updated; tests green.

> **Assumption:** `resolve` composes the existing verbs by importing their Python (`openup-input`, `openup-state`, `openup-roadmap`, and board's own `build_board`) in-process rather than shelling out to four subprocesses — one process, no round-trips. *(Vetoable at review — subprocess composition is the fallback if an import cycle appears.)*
> **Assumption:** the "pre-resolved lane" flag on `/openup-start-iteration` is a passed `task_id:` + `track:` pair (the caller already resolved) — start-iteration self-briefs (re-reads) only when invoked standalone with neither. *(Vetoable at review.)*
> **Assumption:** `status` is a read-only diagnostic (no `write_board`) so it is safe in `openup-doctor`-style contexts; only `refresh` writes `board.json` and runs the reap. *(Vetoable at review.)*

## Requirements

1. `openup-board.py resolve` returns exactly one JSON object whose `path` is one of `resume | pick | promote | noop`, with the matching `lane` (for pick/promote/resume-of-active) or `resumable_input` / `active_iteration` payload, and a human-readable `reason`.
   - **Given** a repo with an active iteration in `.openup/state.json` **When** `resolve` runs **Then** it prints `{"path":"resume", ...}` naming that task and exits 0.
2. The precedence inside `resolve` matches `/openup-next` §0–§1 exactly: answered resumable-input first, then active iteration, then top pickable lane, then promotable roadmap task, else noop.
   - **Given** an answered input-request resumable lane AND an active iteration both present **When** `resolve` runs **Then** `path` is `resume` for the *resumable-input* task (§0 outranks §1a), surfaced in `resumable_input`.
   - **Given** no active iteration and no resumable input but a READY change-folder lane **When** `resolve` runs **Then** `path` is `pick` with that lane.
   - **Given** no lanes at all but a pending roadmap task with satisfied deps **When** `resolve` runs **Then** `path` is `promote` with the roadmap-selected task (identical to `openup-roadmap.py next`).
   - **Given** every lane done/blocked and no promotable roadmap task **When** `resolve` runs **Then** `path` is `noop` with a specific exhaustion `reason`.
3. `resolve` is **read-only**: it writes no files (no `board.json`, no state, no claims mutation) and runs no reap.
   - **Given** a snapshot of `board.json`, `.openup/state.json`, and the claims dir **When** `resolve` runs **Then** all three are byte-identical afterward.
4. `resolve` output is compact — ≤~40 lines on a representative board.
   - **Given** a board with several lanes **When** `resolve` runs **Then** its stdout is ≤ 40 lines.
5. `openup-board.py status` returns the superset diagnostic: active iteration + all live leases + top-N pickable lanes + promotable roadmap queue, read-only.
   - **Given** a repo with one active lease and one pickable lane **When** `status` runs **Then** the JSON contains the active iteration, the lease, the pickable lane, and the promotable queue, and writes nothing.
6. `/openup-next` §0–§1 is a single `resolve` call followed by a branch on `.path`; the two-legal-exits contract and the sentinel line are unchanged.
   - **Given** the edited `openup-next/SKILL.md` **When** a reader follows §0–§1 **Then** it instructs one `resolve` call + act-on-path, and both `OPENUP-NEXT: ADVANCED/DONE` sentinels and the two exits still appear.
7. `/openup-start-iteration` skips its status/roadmap re-read when handed a pre-resolved lane (`task_id:` + `track:`), and still self-briefs when invoked standalone.
   - **Given** `start-iteration` invoked with a resolved `task_id`/`track` **When** it runs **Then** its SKILL text routes past the status/roadmap re-read step; **Given** it is invoked with neither **Then** the self-brief read still happens.
8. `openup-loop.sh` calls `resolve` as a pre-check and, on `path:"noop"`, stops without spawning a `claude -p` cycle process.
   - **Given** a board that resolves to `noop` **When** `openup-loop.sh` runs one iteration **Then** it exits on the sentinel-equivalent stop path and no cycle subprocess is launched.
9. `process-manifest.txt` and `docs-eng-process/script-cli-reference.md` document `resolve` and `status`.
   - **Given** the reference doc **When** grepped for `resolve` and `status` **Then** both verbs are listed with their signatures.

## Behavior Delta

This task changes the **process/tooling** layer, not Ring-1 product behavior of any target application. Within this framework repo the observable changes are:

**Added:**
- `openup-board.py resolve` — the §0–§1 precedence returned as a single read-only JSON decision.
- `openup-board.py status` — a read-only superset diagnostic (active iteration + leases + top-N + promotable queue).
- `openup-loop.sh` no-op pre-check that avoids spawning a cycle process.

**Modified:**
- `/openup-next` §0–§1 flow — `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md §Process steps 0–1`: multi-call precedence → single `resolve` call + branch. (Contract, sentinel, two exits unchanged.)
- `/openup-start-iteration` intake — `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md §steps 1–2`: status/roadmap re-read becomes conditional (skipped on a pre-resolved lane).

**Removed:**
- n/a — no behavior is removed; the hand-executed read-chain is *replaced* by the scripted call, but the equivalent decision remains reachable via the individual verbs for diagnostics.

## Entities

- **openup-board.py** (modified) — `scripts/openup-board.py` (add `cmd_resolve`, `cmd_status`, subparsers)
- **openup-roadmap.py** (read-only) — `scripts/openup-roadmap.py` (`next` reused for the promote branch)
- **openup-input.py / openup-state.py** (read-only) — reused for §0 / §1a inputs
- **openup-next SKILL** (modified) — `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md`
- **openup-start-iteration SKILL** (modified) — `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md`
- **openup-loop.sh** (modified) — `scripts/openup-loop.sh`
- **resolve test** (new) — `scripts/tests/test_openup_board_resolve.py`

## Approach

Add two read-only subcommands to the existing `openup-board.py` that *compose*, in-process, the same building blocks the model calls by hand today: `resolve` folds resumable-input → active-state → `build_board` top-pickable → `openup-roadmap.py next` into one precedence and emits a single small decision object; `status` emits the diagnostic superset without deciding. Neither writes — only `refresh` keeps the write + reap. Then slim the two skills that pay for the prose: `/openup-next` §0–§1 becomes "call `resolve`, branch on `.path`", and `/openup-start-iteration` gains a pre-resolved-lane fast path that skips the re-read. `openup-loop.sh` gets a `resolve`-based no-op pre-check so an exhausted board costs zero cycle processes. Design intent: move the *mechanics* into the script, leave the *judgment* (track selection, role work) in the skill.

## Structure

**Add:**
- `scripts/tests/test_openup_board_resolve.py` — path-coverage + read-only + line-budget tests.

**Modify:**
- `scripts/openup-board.py` — `cmd_resolve`, `cmd_status`, subparser wiring; reuse `build_board`, `is_pickable`, `none_pickable_reason`; import `openup_roadmap`/`openup_input`/`openup_state` helpers (or subprocess fallback).
- `scripts/openup-loop.sh` — `resolve` pre-check; skip cycle spawn on `path:"noop"`.
- `scripts/process-manifest.txt` — no new file to ship beyond the test (board.py already listed); add the test if manifest tracks tests.
- `docs-eng-process/script-cli-reference.md` — document `resolve` / `status`.
- `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` — §0–§1 → single `resolve` call + branch; slim prose.
- `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md` — skip re-read on pre-resolved lane.

**Do not touch:**
- `scripts/openup-roadmap.py` — consumed as-is (T-064); no behavior change.
- The live `.claude/skills/**` copies — edit the `docs-eng-process/.claude-templates/**` source; the sync script propagates (per stay-in-your-lane / template-source rule).
- `refresh`'s reap/write path — the only write path stays as-is.

## Operations

- [x] Add `cmd_resolve` to `scripts/openup-board.py`: compose resumable-input → active-state → top-pickable → roadmap-next → noop into one read-only JSON object; wire the `resolve` subparser.
- [x] Add `cmd_status`: read-only superset diagnostic (active iteration + live leases + top-N + promotable queue); wire the `status` subparser.
- [x] (tester) Write `scripts/tests/test_openup_board_resolve.py`: one fixture per `path` (resume-active, resume-input, pick, promote, noop) + a read-only (no-mutation) assertion + a ≤40-line budget assertion.
- [x] Slim `openup-next/SKILL.md` §0–§1 in `docs-eng-process/.claude-templates/…` to a single `resolve` call + branch on `.path`; preserve the two-exit contract and sentinel line.
- [x] Add the pre-resolved-lane fast path to `openup-start-iteration/SKILL.md` (skip status/roadmap re-read when `task_id`+`track` are passed).
- [x] Add the `resolve` no-op pre-check to `scripts/openup-loop.sh` (stop without spawning a cycle process on `path:"noop"`).
- [x] Update `docs-eng-process/script-cli-reference.md` (+ `process-manifest.txt` if it tracks the new test) with `resolve` / `status` signatures; run `python3 scripts/sync-templates-to-claude.sh` so live skills match.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, `[T-065]` trailer)
- `docs-eng-process/script-cli-reference.md` — CLI signature conventions for `openup-*.py`
- `.claude/CLAUDE.openup.md` — stay-in-your-lane (edit template source, not live `.claude/` copies), fix-spec-first, two-legal-exits

## Safeguards

- **Token / size budget.** `resolve` stdout ≤ ~40 lines; the §0–§1 slim must *reduce* `openup-next/SKILL.md` line count, not grow it.
- **Reversibility.** Pure additive script verbs + skill prose edits — revert the commit to restore the multi-call flow; no data migration, no state schema change.
- **No-go zones.** `resolve` and `status` MUST NOT write any file or run the reap (read-only invariant). The two-legal-exits contract and the `OPENUP-NEXT: ADVANCED/DONE` sentinel line MUST remain unchanged. Do not edit the live `.claude/skills/**` copies directly.
- **Determinism.** `resolve`'s promote branch must return the *same* task as `openup-roadmap.py next` on identical inputs (no divergent second selector).

## Verification

- `python3 scripts/openup-board.py resolve` on this repo returns a valid single-decision JSON with a correct `path`; `status` returns the diagnostic superset.
- `python3 -m pytest scripts/tests/test_openup_board_resolve.py` green (all five paths + read-only + line budget).
- `resolve`/`status` run leaves `board.json`, `.openup/state.json`, and the claims dir unchanged (read-only proof).
- `grep -n 'resolve\|status' docs-eng-process/script-cli-reference.md` shows both verbs documented.
- `openup-next/SKILL.md` §0–§1 shows a single `resolve` call; line count did not increase; sentinel + two exits still present.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

## Success Measures

We expect **input tokens spent on the state-discovery phase of a promote cycle** to drop by **≥40%** within the **first 10 `/openup-next` cycles** after release (single `resolve` call replacing the resumable→state→top→roadmap read-chain + the `start-iteration` double-read + trimmed §0–§1 prose). Instrumentation: before/after token counts on a promote cycle read from `docs/agent-logs/runs/`. Read-back: 10 cycles after release. Combined with T-064's determinism, a promote cycle becomes "one `resolve` call, one deterministic pick, one atomic `begin`".

## Rollout

`n/a — internal process tooling, not user-facing.` The new verbs are additive CLI subcommands read at invocation time; there is no runtime flag to gate and no in-flight user state — the kill-switch is `git revert` of the commit. `/openup-next` continues to work through the individual verbs if `resolve` is not adopted, so rollout is a same-commit cutover of the skill prose, not a staged flag.

---
id: T-033
title: "Autonomous continue-loop: suspend-on-question, resume-on-answer"
status: done   # proposed → ready → in-progress → done → verified
track: standard
depends-on: []
blocks: []
touches: [scripts/, docs-eng-process/.claude-templates/skills/openup-next/, docs-eng-process/.claude-templates/skills/openup-request-input/, scripts/openup-board.py, docs/changes/T-033/]
claimed-by: null
---

# T-033 — Autonomous continue-loop: suspend-on-question, resume-on-answer

## Context

Discovered 2026-06-14 dogfooding an autonomous-loop protocol: drive delivery by
repeating "do the next step" (`/openup-next`); the agent only stops when it needs
user input it cannot resolve, recording the questions in an input-request; the
next cycle, *before starting anything new*, checks for answers and resumes the
suspended task.

The experiment showed the protocol is **~80% supported already**: the board
models `status: blocked` as not-pickable, and Start-of-Run SOP Step 0 specifies
"process answered input-requests first, resume the related task." The missing
**20% is wiring**, currently done by hand each cycle:

1. The board reports a task awaiting input as generic `blocked`, indistinguishable
   from a dependency block — there is no `suspended (awaiting input)` signal.
2. Nothing deterministically detects an *answered* request and maps it back to its
   suspended task; the agent must grep and reason each cycle.
3. `/openup-next` does not run the Step-0 answered-check automatically before
   claiming a new lane, so resume depends on the agent remembering to.

## Behavior Delta

- **Before**: suspend/resume-on-answer works only if the agent manually greps
  `docs/input-requests/`, hand-maps answers to a blocked lane, and flips it.
- **After**: a lane with an open input-request shows as `suspended`; a
  deterministic helper lists answered→resumable lanes; `/openup-next` runs that
  check first and resumes before starting anything new.

## Requirements

1. The board reports a change folder whose frontmatter names an open (pending)
   input-request as a distinct non-pickable `suspended` state.
   - **Given** a change folder with `awaiting-input: <path>` and that request at
     `status: pending`, **When** `openup-board.py refresh` runs, **Then** the lane
     is reported `suspended` (not generic `blocked`) and is not pickable.

2. A deterministic helper maps answered input-requests back to their suspended
   tasks, so a loop can find resumable work without model judgment.
   - **Given** an input-request with `status: answered` and `related_task: T-002`,
     **When** `openup-input.py resumable` runs, **Then** it prints `T-002` with the
     request path and exits 0; with no answered requests it prints nothing, exit 0.

3. `/openup-next` runs the Step-0 answered-check **before** claiming any new lane
   and resumes the suspended task first.
   - **Given** a suspended `T-002` whose input-request is now `status: answered`,
     **When** the next `/openup-next` cycle runs, **Then** it resumes `T-002`
     (folds answers into the spec, flips the lane out of `suspended`, marks the
     request `processed`) before any other lane is claimed.

## Success Measures

- A test fixture (suspended lane + answered request) drives `openup-input.py
  resumable` and asserts it returns the task; it returns nothing while the request
  is `pending`. Fails before the fix, passes after.

## Safeguards

- An answered request must not auto-merge changes silently into code — it only
  un-suspends the lane and surfaces the answers; the spec edit still follows
  fix-spec-first.

## Rollout

- n/a — process/tooling, no runtime feature flag.

## Notes

- Reuses existing primitives: Asynchronous Input SOP (`sops/async-input.md`),
  `/openup-request-input`, Start-of-Run Step 0, and the board. This task makes the
  loop first-class rather than agent-remembered.

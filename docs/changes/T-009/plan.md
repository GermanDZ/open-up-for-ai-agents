---
id: T-009
title: Worktree-per-task + lease claims + collision pre-flight
status: in-progress
priority: medium
estimate: 2 sessions
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md#ws5c
depends-on: [T-005, T-008]
blocks: []
touches:
  - .claude/skills/openup-workflow/      # start-iteration, complete-task gain worktree/claim steps
  - .claude/scripts/hooks/               # pre-flight collision check
  - docs-eng-process/                    # parallel-work.md process doc
claimed-by: null
claimed-at: null
worktree: null
---

# T-009 — Worktree-per-task + lease claims + collision pre-flight (Process v2 WS5c)

## Story

> **As an** OpenUP agent running one of several simultaneous sessions
> **I want** each task to claim its own git worktree and a live lease in the git common
>   dir, with a pre-flight check that refuses to start when a dependency is unmet or my
>   declared surface collides with another live claim
> **So that** two sessions on disjoint tasks run in fully isolated working trees with
>   visible, machine-readable claims — and an overlapping claim is refused up front with
>   the owning session named, instead of surfacing later as a merge conflict.

INVEST: ✅ small-ish (2 sessions), independent (T-005 state + T-008 frontmatter/collision
algorithm both landed), testable (claim files and refusal messages are deterministic),
valuable (un-blocks genuine parallel work — the wave-3 sequencing milestone).

## Analysis Context

- **WS5c** of the Process v2 program plan (`#ws5c`). Builds directly on:
  - **T-008** — defined the coordination frontmatter (`claimed-by` / `claimed-at` /
    `worktree`, read-only there) and the path-segment-prefix collision algorithm
    (T-008 design.md **D2**). T-009 *writes and enforces* those fields and *reuses* that
    algorithm for pre-flight.
  - **T-005** — `.openup/state.json` schema + helper CLI. The `session_id` and active
    `task_id` come from state; the claim references them.
- **Claims are leases, one file per claim**, stored in **`.git/openup/claims/T-NNN.json`**
  (the git *common* dir, shared across all worktrees of the repo, never committed). This
  is the Kaze-evidence design: shared-markdown-file appends were the only source of merge
  conflicts, so claims live outside the tree, one file per task, no shared file to append.
- **Out of scope** (program plan): cross-machine parallel work (claims are single-host);
  a committed claims dir; CI-side enforcement. A `--steal`/override is also deferred — see
  design.md and Open Question #2 below.

## Design Decisions

(Numbered in-flight decisions live in `design.md`. Summary of the load-bearing ones:)

1. **Claim location = git common dir.** `.git/openup/claims/T-NNN.json`, resolved via
   `git rev-parse --git-common-dir` so every linked worktree sees the same claims dir.
   Never committed (it is under `.git/`, so no `.gitignore` entry is needed).
2. **One file per claim**, atomic write (write-temp + `rename`), to avoid any shared-file
   contention. Releasing = deleting the file.
3. **Pre-flight reuses T-008 D2** path-segment-prefix collision on `touches`, now against
   *live claim files* (not just frontmatter): the live set is the union of all
   non-stale claim files' `touches`.

## Requirements

1. **Worktree option in `/openup-start-iteration`.** A `worktree: true` option (default
   off until stable, per the program plan) creates `../<repo>-T-NNN` via
   `git worktree add`, on the task branch, and writes the claim. The created worktree path
   is recorded in the task's frontmatter `worktree:` field and in the claim file.
2. **Lease claim files.** Claims are leases, one JSON file per claim, at
   `.git/openup/claims/T-NNN.json`. Specify the exact shape (see "Claim file shape" below).
   The claims dir is created on first claim if absent.
3. **Pre-flight collision check.** Before writing a claim, refuse when (a) any id in the
   task's `depends-on` is not `done`/`verified`, or (b) the task's `touches` overlaps the
   `touches` of any **live** (non-stale) claim — printing **which session/task owns** the
   conflicting surface. Overlap uses T-008 D2 path-segment-prefix semantics.
4. **Release on complete.** `/openup-complete-task` releases the claim (deletes the claim
   file) and removes the worktree (`git worktree remove`), and nulls the frontmatter
   `claimed-by` / `claimed-at` / `worktree` fields.
5. **Process doc.** `docs-eng-process/parallel-work.md` documents the worktree+claim model,
   the claim shape, the pre-flight rules, stale-lease behavior, and the manual recovery path.
6. **Templates re-synced.** Mirror `.claude/` changes into
   `docs-eng-process/.claude-templates/` (template-sync is manual per T-008 D7 — verify).

## Claim file shape

`.git/openup/claims/T-NNN.json`:

```json
{
  "task_id": "T-009",
  "session_id": "<from .openup/state.json>",
  "branch": "feature/T-009-worktree-claims",
  "worktree": "../open-up-for-ai-agents-T-009",
  "claimed_at": "2026-06-11T14:32:00Z",
  "lease_ttl_hours": 24
}
```

- `claimed_at` is ISO-8601 UTC; a claim is **stale** when
  `now - claimed_at > lease_ttl_hours` (default 24h — see design.md D1).
- A stale claim does **not** block a new claim's collision check (it is excluded from the
  live set), but in v1 is **not auto-deleted** — it is cleared by manual `rm` (see
  design.md D2; flagged for PM confirmation).

## Definition of Done / Acceptance Criteria

- [ ] `/openup-start-iteration` exposes `worktree: true`, which runs
      `git worktree add ../<repo>-T-NNN <branch>` and writes the claim file.
- [ ] Claims are leases, one file per claim, at `.git/openup/claims/T-NNN.json`, with the
      shape above (task_id, session_id, branch, worktree, claimed_at, lease_ttl_hours).
- [ ] The claims dir is created on first claim if it does not exist; claim writes are
      atomic (write-temp-then-rename).
- [ ] Pre-flight **refuses** to claim if any `depends-on` id is not `done`/`verified`,
      naming the unmet dependency.
- [ ] Pre-flight **refuses** to claim if `touches` overlaps a live claim's `touches`
      (T-008 D2 path-segment-prefix semantics), printing the owning `session_id`/`task_id`.
- [ ] `/openup-complete-task` deletes the claim file, runs `git worktree remove`, and nulls
      `claimed-by` / `claimed-at` / `worktree` in the task frontmatter.
- [ ] **End-to-end:** two simultaneous sessions on disjoint tasks run in separate worktrees
      with visible claim files; a third session claiming an **overlapping** task is refused
      with the owning session named. (Program AC line, §"Acceptance Criteria".)
- [ ] `docs-eng-process/parallel-work.md` documents the model; templates re-synced; links intact.
- [ ] Verified by the tester against the end-to-end check above.

## Acceptance Check (from program plan)

> Two simultaneous sessions on disjoint tasks run in separate worktrees with visible
> claims; claiming an overlapping task is refused with the owning session named.

Concretely: session A claims T-X (worktree `../repo-T-X`, claim file present), session B
claims disjoint T-Y (separate worktree, separate claim file) — both succeed. Session C
attempts a task whose `touches` overlaps T-X's surface — pre-flight refuses and prints that
T-X / session A owns the surface. Tester confirms the refusal message names the owner and
that no worktree/claim was created for the refused task.

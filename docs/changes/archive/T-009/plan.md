---
id: T-009
title: Worktree-per-task + lease claims + collision pre-flight
status: done
completed: 2026-06-11
priority: medium
estimate: 2 sessions
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md#ws5c
depends-on: [T-005, T-008]
blocks: []
touches:
  - scripts/                             # openup-claims.py + tests (pre-flight lives here, not a hook)
  - .claude/skills/openup-workflow/      # start-iteration, complete-task gain worktree/claim steps
  - docs-eng-process/                    # parallel-work.md process doc + template mirror
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
  a committed claims dir; CI-side enforcement. A `--steal`/override and any claim TTL are
  also out of scope — Open Question #2 was **resolved (PM/user 2026-06-11): no expiry, manual
  `rm` only** (see design.md D1/D2).

## Design Decisions

(Numbered in-flight decisions live in `design.md`. Summary of the load-bearing ones:)

1. **Claim location = git common dir.** `.git/openup/claims/T-NNN.json`, resolved via
   `git rev-parse --git-common-dir` so every linked worktree sees the same claims dir.
   Never committed (it is under `.git/`, so no `.gitignore` entry is needed).
2. **One file per claim**, atomic write (write-temp + `rename`), to avoid any shared-file
   contention. Releasing = deleting the file.
3. **Pre-flight reuses T-008 D2** path-segment-prefix collision on `touches`, now against
   *live claim files* (not just frontmatter): the live set is the union of **all** claim
   files' `touches` (claims never expire — D1). Each claim carries its own `touches` (D7),
   so pre-flight reads only `.git/openup/claims/*.json`.

## Requirements

1. **Worktree-per-task in `/openup-start-iteration`, default-on** (PM/user 2026-06-11).
   Every iteration creates `../<repo>-T-NNN` via `git worktree add` on the task branch and
   writes the claim; a `worktree: false` escape hatch keeps the legacy in-place checkout.
   The created worktree path is recorded in the task's frontmatter `worktree:` field and in
   the claim file. (Bootstrap exception: T-009 itself runs in-place — design.md D6.)
2. **Lease claim files.** Claims are leases, one JSON file per claim, at
   `.git/openup/claims/T-NNN.json`. Specify the exact shape (see "Claim file shape" below).
   The claims dir is created on first claim if absent.
3. **Pre-flight collision check.** Before writing a claim, refuse when (a) any id in the
   task's `depends-on` is not `done`/`verified`, or (b) the task's `touches` overlaps the
   `touches` of **any live claim** — printing **which session/task owns** the conflicting
   surface. Overlap uses T-008 D2 path-segment-prefix semantics. (Claims never expire, so
   every present claim counts — D1.)
4. **Release on complete.** `/openup-complete-task` releases the claim (deletes the claim
   file) and removes the worktree (`git worktree remove`), and nulls the frontmatter
   `claimed-by` / `claimed-at` / `worktree` fields.
5. **Process doc.** `docs-eng-process/parallel-work.md` documents the worktree+claim model,
   the claim shape, the pre-flight rules, and — since claims never expire — the manual
   `rm` recovery path as the *sole* unblock mechanism for abandoned claims.
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
  "touches": [".claude/skills/openup-workflow/", ".claude/scripts/hooks/", "docs-eng-process/"]
}
```

- `claimed_at` is ISO-8601 UTC, recorded for owner/audit visibility only.
- `touches` is **copied into the claim from the task's frontmatter at claim time** (design.md
  D7, resolving Q6): the claim file is self-contained, so pre-flight unions live claims'
  `touches` by reading **only** `.git/openup/claims/*.json` — never joining back to
  frontmatter. This keeps the claim files authoritative for collision (D5).
- **Claims never expire** (PM/user 2026-06-11 — design.md D1): there is no `lease_ttl_hours`
  field and no staleness evaluation. Every present claim counts in the live collision set
  regardless of age, so an abandoned claim **blocks** an overlapping claim until cleared by
  manual `rm .git/openup/claims/T-NNN.json` (the sole recovery path — design.md D2).

## Definition of Done / Acceptance Criteria

- [x] `/openup-start-iteration` creates a worktree **by default** —
      `git worktree add ../<repo>-T-NNN <branch>` then writes the claim file (worktree
      first, claim second; roll back the worktree if the claim write fails — design.md D6);
      `worktree: false` opts out to in-place checkout.
- [x] Claims are one file per claim, at `.git/openup/claims/T-NNN.json`, with the shape
      above (task_id, session_id, branch, worktree, claimed_at, **touches** — **no** lease/TTL
      field). `touches` is copied from frontmatter at claim time so pre-flight reads only
      claim files (D7).
- [x] The claims dir is created on first claim if it does not exist; claim writes are
      atomic (write-temp-then-rename).
- [x] Pre-flight **refuses** to claim if any `depends-on` id is not `done`/`verified`,
      naming the unmet dependency.
- [x] Pre-flight **refuses** to claim if `touches` overlaps **any** live claim's `touches`
      (T-008 D2 path-segment-prefix semantics; no staleness filter), printing the owning
      `session_id`/`task_id`.
- [x] `/openup-complete-task` deletes the claim file, runs `git worktree remove`, and nulls
      `claimed-by` / `claimed-at` / `worktree` in the task frontmatter.
- [x] **End-to-end:** two simultaneous sessions on disjoint tasks run in separate worktrees
      with visible claim files; a third session claiming an **overlapping** task is refused
      with the owning session named. (Program AC line, §"Acceptance Criteria".)
- [x] `docs-eng-process/parallel-work.md` documents the model; templates re-synced; links intact.
- [x] Verified by the tester against the end-to-end check above.

## Acceptance Check (from program plan)

> Two simultaneous sessions on disjoint tasks run in separate worktrees with visible
> claims; claiming an overlapping task is refused with the owning session named.

Concretely: session A claims T-X (worktree `../repo-T-X`, claim file present), session B
claims disjoint T-Y (separate worktree, separate claim file) — both succeed. Session C
attempts a task whose `touches` overlaps T-X's surface — pre-flight refuses and prints that
T-X / session A owns the surface. Tester confirms the refusal message names the owner and
that no worktree/claim was created for the refused task.

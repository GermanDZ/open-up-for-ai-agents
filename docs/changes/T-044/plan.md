---
id: T-044
title: "Remote-aware claim preflight for openup-next (Option B: branch-as-claim)"
type: work-item
status: in-progress
track: standard
priority: high
depends-on: [T-009]
blocks: []
traces-from: docs/explorations/2026-06-16-cross-machine-claim-coordination.md
touches: [scripts/openup-claims.py, scripts/tests/test_openup_claims.py, .claude/skills/openup-next/SKILL.md, .claude/skills/openup-start-iteration/SKILL.md, docs-eng-process/.claude-templates/skills/openup-next/SKILL.md, docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md, docs-eng-process/parallel-work.md, docs-eng-process/script-cli-reference.md, docs/changes/T-044, docs/roadmap.md]
claimed-by: null
---

# T-044 — Remote-aware claim preflight for `openup-next`

## Context

The lease (`openup-claims.py`, T-009) lives at `<git-common-dir>/openup/claims/`
— inside `.git/`, never pushed — so it coordinates **sessions of one clone** and
nothing across machines (documented in T-043's parallelism-scope note). With
teammates about to run `openup-next` in parallel from separate clones, the
default outcome is two PRs for one task — exactly what happened on **TallyFox
(#462 vs #463, T-1102)**.

The seeding exploration
([2026-06-16-cross-machine-claim-coordination.md](../../explorations/2026-06-16-cross-machine-claim-coordination.md))
dispositioned **Option B (branch-as-claim)** as the cheap first step: before a
lane claims a task, consult the **remote** for an existing `*/T-NNN-*` branch —
the cross-machine-visible claim signal lanes already produce — and refuse if one
exists. The heavier atomic `refs/openup/claims/*` ref-lock (Option A) stays
gated behind measured duplicate frequency, which is why this task **also emits a
counter** so we can decide later with data, not vibes.

This is a **behavior change** to `openup-next` / `openup-start-iteration` (they
will now refuse a task they previously would have claimed) → spec-first.

## Requirements

1. **A remote-check subcommand on `openup-claims.py`.** `remote-check
   --task-id T-NNN [--remote origin] [--no-fetch] [--self-branch B]` lists remote
   branches and refuses when another branch already encodes the task.
   - **Given** `origin` has a branch `fix/T-044-foo` and we run
     `remote-check --task-id T-044 --self-branch feature/T-044-mine`, **When** it
     runs, **Then** it exits `9` (EXIT_REMOTE_DUP) and names the colliding
     remote branch on stderr.
   - **Given** `origin` has no branch matching the `T-044` token, **When** it
     runs, **Then** it exits `0` with `READY: no remote branch for T-044`.
   - **Given** the only matching remote branch IS `--self-branch` (our own lane,
     already pushed), **When** it runs, **Then** it exits `0` (don't collide with
     ourselves).
   - **Given** there is no `origin` remote (solo/offline), **When** it runs,
     **Then** it exits `0` with a stderr note (advisory, fail-open — never block
     work because the remote is unreachable).

2. **Token-accurate branch matching.** A branch matches task `T-NNN` only when
   `T-NNN` appears as a delimited token (`fix/T-44-x` must NOT match `T-044`;
   `feature/T-044-y`, `T-044`, `bugfix/T-044` must).

3. **`openup-next` and `openup-start-iteration` run remote-check before
   claiming.** Wired into the claim step; a non-zero remote-check refuses the
   start the same way an unmet dependency does (do not proceed to claim).
   - **Given** `openup-next` is about to claim `T-NNN` and a remote branch for it
     exists, **When** the cycle runs, **Then** it does not claim/branch, it
     emits a `duplicate_start_blocked` event, and it stops with the owner named.

4. **Duplicate-start counter (the measurement for Option A's go/no-go).** Each
   refusal appends a clock-stamped record to `docs/agent-logs/agent-runs.jsonl`
   via `openup-state.py log-event --event duplicate_start_blocked` (append-only,
   `merge=union` — never authored by the model, never a fabricated timestamp).

5. **Fail-open, not fail-closed.** Unlike the local collision preflight (which
   fail-closes on a corrupt claim), remote-check is **advisory**: any remote
   error (no remote, network down, auth) exits `0` so offline work is never
   blocked. The local lease remains the hard gate; this is the cross-machine
   *early-warning*.

## Operations

- [x] R1–R2: `remote-check` subcommand + token-accurate matcher in `openup-claims.py`
- [x] R5: fail-open behavior for missing/unreachable remote
- [x] R4: refusal emits `duplicate_start_blocked` via `openup-state.py log-event`
- [x] R3: wire remote-check into `openup-next` + `openup-start-iteration` claim steps
- [x] Mirror both skill edits into `docs-eng-process/.claude-templates/skills/...`
- [x] Tests: hermetic local-bare-remote cases for R1–R5 (5 new, 36/36 claims suite green)
- [x] Docs: `parallel-work.md` (behavior) + `script-cli-reference.md` (CLI signature)
- [x] Full claims suite green; `.claude`↔template sync green

## Success Measure

Falsifiable expectation: once shipped, **`duplicate_start_blocked` events in the
run log directly count how often two clones target the same task.** If, after a
sustained period of parallel work, that count is ~0, Option A (atomic ref-lock)
is unjustified and stays dropped; if it climbs, the count is the evidence that
promotes Option A. Either way the decision is data-backed. (No user-facing
metric; this is a process-tooling measure.)

## Where the spec came from

Seeded by the cross-machine exploration; track = standard (single feature, multi
file, no architectural decision); solo sequential, in-place — matching recent
framework iterations (T-041, T-042).

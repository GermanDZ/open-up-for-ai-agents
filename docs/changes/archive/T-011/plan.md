---
id: T-011
title: Retro cadence trigger + /openup-create-handoff
status: done
completed: 2026-06-11
priority: low
estimate: 1 session
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md#ws6
depends-on: [T-005]
blocks: []
touches:
  - .claude/skills/openup-workflow/start-iteration/        # retro-due gate check + refuse full-track start
  - .claude/skills/openup-workflow/complete-task/          # increment iterations_since_retro on completion
  - .claude/skills/openup-workflow/retrospective/          # reset iterations_since_retro + clear retro_due
  - .claude/skills/openup-workflow/openup-create-handoff/  # NEW skill (6c)
  - .claude/skills/openup-artifacts/                       # handoff template mirror (if artifacts host templates)
  - docs-eng-process/                                       # state-file.md (retro fields) + skills-guide.md (new skill)
  - .claude/CLAUDE.openup.md                                # common-commands list + cadence note
  - docs/roadmap.md                                         # mark T-011 status
---

# T-011 — Retro cadence trigger + `/openup-create-handoff` — Process v2 WS6 (6b + 6c)

## Story

> **As an** OpenUP team running iteration after iteration
> **I want** the retrospective to be triggered automatically by a cadence counter, and a
>   sanctioned `/openup-create-handoff` skill for the handoff-brief pattern
> **So that** retrospectives stop silently lapsing (Kaze hit a 26-iteration gap because the
>   "every 3–5 iterations" cadence was a convention with no trigger), and the handoff brief
>   that proved itself unprompted in Kaze T-015 becomes a first-class, repeatable artifact.

INVEST: ✅ small (1 session), independent (T-005 `.openup/state.json` already carries
`iterations_since_retro` and `gates.retro_due`; this task only adds the *logic* that reads
and writes them), testable (the counter increments, the gate refuses, the reset clears —
all deterministic), valuable (kills the retro-gap class + promotes a proven pattern),
estimable.

## Current State (what already exists from T-005)

- `scripts/openup-state.py` is the sanctioned, model-free state CLI (design rule: *skills
  MUST write state through this CLI, never by hand-editing JSON*). It already has
  `init / get / set / set-gate / check-gates / archive / validate`.
- `.openup/state.json` already carries `iterations_since_retro` (integer) and
  `gates.retro_due` (bool). The fields are written but **nothing reads or mutates them** —
  `grep -r iterations_since_retro` over skills/hooks returns zero functional hits.
- **Carry-forward problem:** `/openup-complete-task` *archives and removes*
  `.openup/state.json`, and `/openup-start-iteration` re-`init`s a fresh one. So the count
  has **no home that survives a completion** if it lives only inside `state.json`. This is
  the crux D1 must solve.
- `/openup-retrospective` exists (`.claude/skills/openup-workflow/retrospective/SKILL.md`)
  but does not reset the counter.
- `/openup-complete-task` does not increment the counter.
- `/openup-start-iteration` does not check `retro_due` and will start a `full`-track
  iteration regardless of cadence.
- There is **no** `/openup-create-handoff` skill.

**What is missing — this task (two deliverables):**

## Scope (deliverables)

### D1 (WS6b) — Retro cadence trigger

**Counter home (design decision — see design.md):** the authoritative counter lives in a
**durable** `.openup/retro.json` (`{"iterations_since_retro": N}`), *not* inside
`.openup/state.json`. Rationale: `state.json` is destroyed every completion (archive +
remove), so a counter inside it cannot survive across iterations. `.openup/retro.json` is in
the gitignored `.openup/` dir but is **not** touched by `archive`, so it persists locally
across the whole iteration stream. `state.json.iterations_since_retro` (schema-required) is
kept as an **init-time mirror** of the durable value for audit/visibility. Failure mode is
safe: if the local file is lost, the count resets to 0 and the next retro simply fires
sooner.

All three touch points go through a new `openup-state.py retro` subcommand (honors the
CLI-only write rule — no hand-edited JSON):

1. **Increment on completion** — `/openup-complete-task` runs
   `python3 scripts/openup-state.py retro increment` (independent of state.json archival, so
   ordering vs. archive does not matter).
2. **Check + raise the gate at start** — `/openup-start-iteration` runs
   `python3 scripts/openup-state.py retro check` (threshold 5). It seeds the new state's
   `iterations_since_retro` from `retro get`, and sets `gates.retro_due = true` when
   `N >= 5`. When `retro_due` **and** the selected track is `full`, **refuse to start** —
   redirect: "Retrospective overdue (N since last). Run `/openup-retrospective` before
   full-track work." `quick`/`standard` proceed with a non-blocking reminder (the gap-killer
   targets the heavy track, per the plan: "refuses `full`-track starts until
   `/openup-retrospective` runs").
3. **Reset on retro** — `/openup-retrospective` runs
   `python3 scripts/openup-state.py retro reset` (sets durable count = 0; also clears
   `gates.retro_due` and zeroes the mirror in a live `state.json` if one is present, so a
   between-iteration retro still resets cleanly).

Threshold: `>= 5` (plan WS6b). Document the exact rule in `docs-eng-process/state-file.md`.

### D2 (WS6c) — `/openup-create-handoff` skill

New skill at `.claude/skills/openup-workflow/openup-create-handoff/SKILL.md` (mirror the
existing workflow-skill shape: frontmatter with `name`, `description`, `model`, args;
Success Criteria; Process; Output; See Also). It codifies the Kaze T-015 handoff-brief
structure:

- **Acceptance criteria** — the testable conditions the receiver verifies.
- **Test cases / how to exercise it** — concrete steps or commands.
- **Troubleshooting** — known failure modes + resolutions observed during the work.
- **Open questions** — unresolved decisions handed to the next owner.

Source material: the skill reads Ring 1 + the active change folder
(`docs/changes/T-NNN/`) — `plan.md`, `design.md`, `test-notes.md` — and the agent log, and
emits `docs/changes/T-NNN/handoff.md`. `model: haiku` for the collection/formatting pass
(it is assembly, not deep reasoning). Add it to the common-commands list in
`CLAUDE.openup.md` and to `skills-guide.md`.

## Out of Scope

- Auto-running the retrospective. The trigger only *raises the gate / reminds*; a human or
  PM still invokes `/openup-retrospective`.
- Cross-machine durability of the counter. `.openup/retro.json` is local (gitignored); the
  cadence nudge fails safe if it is lost (next retro fires sooner). Committing the counter
  would put session state in `docs/`, violating the three-ring scoping.
- A configurable threshold surface beyond the `--threshold` flag default of 5 (hard-coded
  default per the plan; flag exists only so tests can exercise the boundary).

## Acceptance Criteria

- [x] AC1: After `/openup-complete-task`, the durable counter `iterations_since_retro` is
  exactly one greater than before. *(`retro increment`, test `test_increment_accumulates`;
  wired into complete-task step 7a.)*
- [x] AC2: With `iterations_since_retro >= 5`, `/openup-start-iteration … track:full`
  refuses to start and points the operator at `/openup-retrospective`. *(`retro check` sets
  `gates.retro_due`; refusal in start-iteration step 3b; test
  `test_check_at_threshold_sets_gate` + end-to-end walkthrough showed `due 5`.)*
- [x] AC3: With `iterations_since_retro >= 5`, a `quick`/`standard` start still proceeds but
  prints a non-blocking retro reminder. *(start-iteration step 3b.)*
- [x] AC4: After `/openup-retrospective` completes, `iterations_since_retro == 0` and
  `gates.retro_due == false`. *(`retro reset`, test `test_reset_clears_counter_and_gate`;
  wired into retrospective step 8.)*
- [x] AC5: `/openup-create-handoff` exists, follows the workflow-skill rubric shape, and
  emits `docs/changes/T-NNN/handoff.md` with the four sections.
- [x] AC6: `state-file.md`, `skills-guide.md`, and `CLAUDE.openup.md` document both the
  cadence rule and the new skill; roadmap T-011 row updated.

## Test Notes

These skills are markdown specs (no executable test harness), so verification is by
inspection + a dry walkthrough:
- Hand-edit `iterations_since_retro` to 5 in a scratch state and trace each skill's
  documented step to confirm the gate/refusal/reset wording matches ACs.
- Confirm `grep -r iterations_since_retro .claude/` now shows the three lifecycle touch
  points (complete-task increment, start-iteration check, retrospective reset).

## Design decisions

Living decisions during execution go in `docs/changes/T-011/design.md`.

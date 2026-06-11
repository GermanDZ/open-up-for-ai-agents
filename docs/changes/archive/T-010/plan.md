---
id: T-010
title: Graded tracks (quick / standard / full)
status: done
completed: 2026-06-11
priority: medium
estimate: 1 session
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md#ws6a
depends-on: [T-005, T-006]
blocks: []
touches:
  - .claude/skills/openup-workflow/start-iteration/   # track-selection step + track arg
  - .claude/scripts/hooks/on-task-request.py          # suggest track in intake message
  - docs-eng-process/                                  # tracks.md process doc + template mirror
  - .claude/CLAUDE.openup.md                           # graded-tracks index section
---

# T-010 — Graded tracks (quick / standard / full) — Process v2 WS6a

## Story

> **As an** OpenUP agent receiving a task request of varying size
> **I want** the intake + start-iteration flow to select one of three ceremony tracks
>   (`quick` / `standard` / `full`) from the declared scope, and to apply only the
>   ceremony that track warrants
> **So that** small work (docs/config/typo) takes the near-zero-friction path by default
>   instead of dragging a full team + plan gate through every change — the Kaze failure
>   mode where 18% of commits bypassed the process entirely because the only sanctioned
>   path was too heavy.

INVEST: ✅ small (1 session), independent (T-005 `track` field + T-006 `gate-edits.py`
quick relaxation already landed), testable (the intake heuristic and the per-track
ceremony are deterministic), valuable (makes the lightweight path the *default*, not an
opt-in), estimable.

## Current State (what already exists from T-005 / T-006)

- `.openup/state.json` carries a `track` field (`quick | standard | full`).
- `scripts/openup-state.py init --track {quick|standard|full}` validates the choice.
- `gate-edits.py` already relaxes the plan gate for `track == "quick"` (state required,
  plan not) and audits the bypass.

**What is missing — the routing/selection layer (this task):**

1. Nothing **selects** a track from scope. `start-iteration` lists `--track {…}` as a
   bare placeholder with no decision rule, so callers guess.
2. Team deployment is **unconditionally mandatory** in `start-iteration` — quick track is
   supposed to skip the team, but the skill has no track-awareness.
3. `on-task-request.py` suggests a *team* but never a *track*. The plan (WS6a) says the
   intake hook must "suggest the track in its intake message."
4. No process doc explains the three tracks, their selection heuristics, or their ceremony.

## Scope (deliverables)

### D1 — Track-selection step in `/openup-start-iteration`
- Add a `track` argument (optional; auto-selected from scope when omitted).
- New **"Select Track"** step (runs before Deploy-Team) with this decision table:

  | Track | When | Ceremony applied |
  |---|---|---|
  | `quick` | docs / config / typo / comment / ≤ ~50 LOC, single file | state file + auto-log only — **no plan gate, no team, no readiness** |
  | `standard` | single-feature work | plan gate + scribe logging + `/openup-readiness` check; team optional |
  | `full` | multi-role / architectural / cross-cutting | standard **+ team deployment + rubric assessment** at complete-task |

- Make **Deploy-Team track-conditional**: `quick` ⇒ skip team (equivalent to
  `deploy_team: false`); `standard` ⇒ team optional (phase default unless `team: none`);
  `full` ⇒ team mandatory. The existing `deploy_team`/`team` args still override.
- Pass the selected track into `openup-state.py init --track`.

### D2 — Track suggestion in `on-task-request.py` intake
- Classify the prompt's scope into a suggested track using keyword heuristics:
  - **quick**: typo, rename, comment, bump, version, doc/docs, readme, formatting,
    lint, whitespace, "small", "tiny", one-liner.
  - **full**: architecture/architectural, redesign, "across", migrate/migration,
    multi-(role|component|service), refactor (broad), schema change, "rework".
  - **standard**: default when neither set matches.
- Emit the suggested track in **both** branches (no-active-iteration and active-iteration),
  e.g. `Suggested track: quick — run /openup-start-iteration task_id: T-XXX track: quick`.
- Keep exit codes unchanged (still exit 2 to inject the intake instruction).

### D3 — Process doc `docs-eng-process/tracks.md`
- Document the three tracks: when to use, ceremony matrix, how track wires to
  `state.json.track`, `gate-edits.py`, team deployment, and complete-task rubric.
- Cross-link from `state-file.md` and `skills-guide.md`.

### D4 — `CLAUDE.openup.md` graded-tracks index section
- A short "Graded Tracks" subsection (the 3-row table + one-line selection rule),
  pointing to `tracks.md` for detail.

### D5 — Template mirror
- Mirror the skill + hook changes into `docs-eng-process/.claude-templates/` so consumer
  projects pick them up on re-sync (the template-sync hook covers `.claude/` → templates;
  verify it fired, otherwise mirror by hand).

## Open Questions — resolved for this task

- **OQ1 (quick-track gate strictness):** **A real task id is still required**; quick track
  does **not** auto-generate `QT-NNN` ids and the `[T-XXX]` commit tag stays mandatory.
  Friction is removed by skipping the *plan gate* and *team*, not by skipping the id/tag —
  keeping one id space avoids a second traceability scheme. (Auto-id is out of scope; the
  existing `/openup-quick-task` skill remains the other lightweight entry point and will be
  reconciled to set `track: quick` as part of D1.)
- **OQ4 (rubric in tracks):** `standard` track does **not** require
  `/openup-assess-completeness` for code-bearing tasks; **`full` does**. Standard keeps
  rubric checks for artifact-generating skills only (unchanged).

## Acceptance Criteria

- [ ] `/openup-start-iteration` has a Select-Track step with the decision table; omitting
      `track` auto-selects from scope; `quick` skips team deployment.
- [ ] `on-task-request.py` prints a `Suggested track: …` line in both intake branches,
      chosen by the keyword heuristic; exit-2 behavior preserved.
- [ ] A quick-scope prompt ("fix typo in README") suggests `quick`; an architectural prompt
      suggests `full`; a plain feature prompt suggests `standard`. (deterministic test)
- [ ] `docs-eng-process/tracks.md` exists and is cross-linked; `CLAUDE.openup.md` has the
      graded-tracks section.
- [ ] Template mirror updated (or template-sync hook confirmed to have run).
- [ ] No regression: existing hook tests still pass.

## Out of Scope

- Retro cadence trigger + `/openup-create-handoff` (that is **T-011**, WS6b/6c).
- `QT-NNN` auto-id scheme (OQ1 — deferred).
- Per-track changes to `/openup-complete-task` beyond gating the rubric on `full`.

## Test Notes

- Unit-test the `on-task-request.py` track classifier (quick/standard/full fixtures).
- Smoke-test `openup-state.py init --track quick|standard|full` still validates (regression).
- Confirm `gate-edits.py` quick relaxation still allows a no-plan edit under `track: quick`.

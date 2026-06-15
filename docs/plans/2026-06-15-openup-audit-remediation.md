# Program plan — OpenUP audit remediation (es-invoices findings)

**Status**: planned → in delivery as **T-041** (iteration 18, standard track, solo, in-place).
**Source**: audit of the `es-invoices` project's agent logs + 12 Claude session
transcripts, June 2026. Detailed spec and acceptance scenarios:
[docs/changes/T-041/plan.md](../changes/T-041/plan.md); evidence:
[docs/changes/T-041/design.md](../changes/T-041/design.md).

## Why

The audit confirmed the framework's guardrails work (hooks block correctly, scripts
run clean, no real bypasses) but found eight defects. The headline is **fabricated
timestamps in `agent-runs.jsonl` and run-log `.md`** — the model fills `[ts]`
placeholders with round invented times, corrupting the audit trail the process
exists to produce. The rest are install gaps and usability cliffs. All are
framework-level and propagate to bootstrapped projects.

## The eight fixes

1. **Script-stamp timestamps** — add `openup-state.py log-event` (stamps `ts` from
   the clock); skills call it instead of briefing the scribe with `[ts]`.
2. **Install agents** — `setup-agent-teams.sh` copies `.claude-templates/agents/`
   so `openup-scribe`/`openup-explorer` register (fixes `Agent type not found`).
3. **Spine docs off quick track** — `on-task-request.py` keeps vision/risk-list/
   use-case/architecture/test-plan on `standard`, preserving plan + rubric gates.
4. **`/openup-next` empty-board guidance** — exit-3 points to
   `/openup-create-task-spec` when pending rows lack a change folder.
5. **CLI reference** — `docs-eng-process/script-cli-reference.md`, linked from
   `scripts/README.md` and `CLAUDE.openup.md`, to cut `--help` discovery churn.
6. **Canonical bootstrap commit** — `bootstrap-project.sh` uses
   `chore(init): …` so it matches the hook it ships.
7. **Worktree-aware edit gate** — `gate-edits.py` reads state from the edit
   target's worktree root, not cwd (the bug that forced es-invoices to collapse a
   worktree mid-task, and that forced this iteration to run in-place).
8. **Exempt plan-mode plan files** — `gate-edits.py` treats the plan-mode plan
   dir as process-state (it blocked this very remediation's plan file).

## Sequencing

7 + 8 first (actively obstructing real sessions), then 1 (data integrity), then
2/3 (install + track), then 4/5/6 (docs/polish). Each hook/skill edit is mirrored
to `.claude-templates/`. Verify: full unittest suite + `check-claude-sync`.

## Not in scope / follow-ups

- `/openup-next` end-of-backlog behavior at a phase boundary is **correct as-is**
  (it stops and names the next move: `/openup-phase-review` → populate the next
  phase). Optional future polish: have the terminal message offer the phase-review
  command directly. Not included here.

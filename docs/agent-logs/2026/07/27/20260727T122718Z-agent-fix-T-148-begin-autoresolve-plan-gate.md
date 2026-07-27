# Agent Run — T-148

| Field | Value |
|---|---|
| Task | T-148 — `begin` never seeds the plan gate from the task's own spec |
| Branch | `fix/T-148-begin-autoresolve-plan-gate` |
| Phase | construction |
| Iteration | 103 |
| Track | standard (solo — no team) |
| Start | 2026-07-27T12:12:04Z |
| End | 2026-07-27T12:27:18Z |
| Base | `b2810c0` |

## Commits

| SHA | Message |
|---|---|
| `ace0911` | docs(T-148): promote lane — author spec, board-visible [T-148] |
| `f74cbb0` | fix(session): begin auto-resolves the plan gate from the task's own spec [T-148] |
| `682c129` | docs(T-148): document the auto-resolved plan gate; regenerate the skill mirror [T-148] |
| `a973a94` | docs(T-148): requirement grade, design decisions, ticked operations [T-148] |

## Files Changed

- `scripts/openup-session.py` — `_resolve_plan_path()` helper; wired into `cmd_begin`; `plan_gate_autoresolved` log event
- `scripts/tests/test_openup_session.py` — `TestPlanGateAutoResolve` (4 regression tests)
- `docs-eng-process/procedures/openup-start-iteration.md` — step 6: dropped the optional `--plan docs/plans/{plan}.md`, documented auto-resolution
- `docs-eng-process/script-cli-reference.md` — `begin` signature note
- `docs-eng-process/state-file.md` — `plan_persisted` gate-source row
- `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md` — regenerated mirror
- `.claude/skills/openup-start-iteration/SKILL.md` — synced mirror
- `docs/changes/T-148/plan.md`, `docs/changes/T-148/design.md` — spec + completion evidence

## Decisions

1. **Fixed the tool, not only the prose.** The roadmap scoped T-148 to the skill template, but its own acceptance bullet was behavioral ("a fresh `begin` … never needs a follow-up `set-gate`"), which prose alone cannot satisfy — re-wording an instruction that was skipped five times invites a sixth. Resolution moved into `openup-session.py`; the pack edit documents it.
2. **Resolution sits outside the T-063 rollback boundary** — called next to `base_sha`, before the claim, so no new failure path appears between claim and state-init.
3. **Three deliberate branches, each with a test**: explicit `--plan` wins verbatim; a missing spec is fail-open (gate stays `false`, `begin` still exits 0); `quick` never auto-resolves because `tracks.md` relaxes the gate there.
4. **Instrumented the fix** with a `plan_gate_autoresolved` run-log event, so the success measure has an instrument that exists in the environment it will be read back from.

## Verification

- All 7 spec requirements graded ✅ against the diff (see `design.md`).
- Mutation check: reverting `if plan_path:` → `if args.plan:` fails `test_standard_track_auto_resolves_task_spec`; restoring it passes.
- `scripts/tests` 844 passed / 1 skipped · `tests/` 106 passed · `check-docs.py` OK (8 instances) · `render-skills-mirror.py --check` exit 0 · `openup-fence.py check` exit 0.
- **Pre-existing, not caused here:** `tests/test-scripts.sh` Test 16 fails identically on `main` at `b2810c0` (16/17).

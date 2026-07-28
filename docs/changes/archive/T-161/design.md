# T-161 — design decisions

## DD1 — The diagnosis was wrong first, and fixing that saved the change

The defect was initially reported as `openup-board.py resolve` "conflating *no promotable
entries* with *no roadmap*", which pointed at the resolve precedence. Reading the code
refuted it: the plan-fresh branch (`openup-board.py:892-899`) is gated on
`phase in _AUTHORING_PHASES`, and its own comment states the intent exactly —
*"Construction/transition are excluded, so their drained-roadmap case still falls through to
noop."* The precedence was **already correct**.

The single fault was that the branch received `phase == "inception"` for a Construction
project. Had the first diagnosis been acted on, the change would have been larger, in the
wrong file, and would have broken the fresh-project bootstrap the branch exists to serve.

**`scripts/openup-board.py` is therefore deliberately untouched**, and requirement 7 verifies
the corrected behaviour arrives *through* it — `git diff --stat main...HEAD -- scripts/openup-board.py`
is empty.

## DD2 — Root cause: the durable record was never consulted

`resolve_phase(records, state_phase)` fell back to `state_phase or "inception"`, and
`compute_status` supplied `state_phase` from **live state only**
(`state.get("phase") if state else None`). `.openup/state.json` exists *only while a lane is
in flight*, so with no active lane the hint was `None` and every project — however mature —
derived `inception`.

Meanwhile `docs/project-status.md` carries `**Phase**: construction`, written by
`sync-status.py` from state at every completion. It is the **durable** record; live state is
the *transient* one. The fallback chain consulted the transient source and then gave up.

Chosen over reconstructing phase from archived states: ordering across archives is ambiguous
and the tree is large, whereas the synced view is a single authoritative line.

## DD3 — Precedence, and why live state still wins

`milestone records → live state → project-status → inception`.

Live state beats project-status because an **active lane is more current than the last synced
view** — mid-lane, state has the phase the lane is actually working in, while the view still
shows the previous completion. Requirement 3 pins this direction explicitly, since it is the
one the fix must not move.

`inception` remains the terminal default so a genuinely fresh project (no state, no records,
no project-status) bootstraps exactly as before — requirement 4, in two halves: file absent,
and file present without a `**Phase**:` line.

## DD4 — The fallback reports its own source, but only when used

`source` exists to answer *where did this come from*, so a new tier that reused
`state-fallback` would hide precisely the distinction this task adds. Hence
`project-status-fallback`.

Subtlety worth stating: when the hint **fails validation** the result is the hard-coded
default, and the source reports `state-fallback`, *not* the tier the rejected value came from
— labelling it otherwise would credit a value that was discarded. `resolve_phase` was
restructured so validation and attribution happen in one place rather than two.

## DD5 — Bite check

3 of 8 new tests fail against the unfixed code:
`test_falls_back_to_project_status_phase`, `test_fallback_reports_its_own_source`,
`test_phase_is_case_and_space_tolerant`.

The other 5 pass both ways **by design** — they are the no-regression guards for
requirements 3, 4 (×2), 5 and 6, whose expected values coincide with the old behaviour. That
is the point of them; recorded here so "5 of 8 already passed" is not misread as weak
coverage.

## DD6 — Verified in the real repo, not only in fixtures

Swapping only `scripts/openup-lifecycle.py` on `main` (board and everything else unchanged):

| | `path` | `phase` | reason |
|---|---|---|---|
| before | `plan-iteration` | `inception` | plan a fresh inception-phase iteration … (no roadmap yet; phase criteria unmet) |
| after | **`noop`** | **`construction`** | no pickable lane (1 in-progress). **roadmap exhausted — no promotable pending task.** |

`noop` + "roadmap exhausted" is exactly what `/openup-next`'s own contract prescribes for
this situation. Main was restored immediately after the check.

## DD7 — Trigger is general, not deferral-specific

T-073 and T-156 being deferred is merely what drained the roadmap today. The same misfire
occurs on **any** repo whose roadmap is fully delivered with no lane active — the ordinary
end state of a completed backlog. The deferrals made a latent, permanent hazard visible.

## DD8 — Verification (complete-task steps 1a / 1b)

### Step 1a

| # | Verdict | Evidence |
|---|---|---|
| 1 | ✅ | `read_project_status_phase()` + `compute_status` tier; `test_falls_back_to_project_status_phase` |
| 2 | ✅ | `project-status-fallback` source; `test_fallback_reports_its_own_source` |
| 3 | ✅ | tier guarded by `if not state_phase`; `test_live_state_still_wins` |
| 4 | ✅ | `test_fresh_project_still_defaults_to_inception`, `test_project_status_without_phase_line_defaults` |
| 5 | ✅ | validation retained in `resolve_phase`; `test_invalid_phase_value_is_discarded` |
| 6 | ✅ | records branch untouched; `test_milestone_records_still_win` |
| 7 | ✅ | DD6 — live before/after in this repo, `openup-board.py` untouched |
| 8 | ✅ | `script-cli-reference.md` now documents all three tiers and the discarded-hint rule |
| 9 | ✅ | `scripts/tests/` **899** unchanged (no test there touched); `tests/` **118 → 126**; no assertion edited |

**Result: 9/9 ✅.**

### Step 1b

`✅ instrumentation` — both instruments are committed here and readable **in this repo** (the
named read-back environment): the requirement-7 expectation (`resolve` → `noop` for a drained
roadmap in a non-authoring phase) and the `source` field itself, where
`project-status-fallback` is direct evidence the tier is live and `inception` beside a mature
`project-status.md` is the defect recurring. Read-back environment: **this repo**. Reader: not
required — the environment is local. **Read-back: the second retrospective after landing**,
backstop **2026-11-30**; and unusually the measure is answerable *on demand* in one call
(`openup-lifecycle.py status --json` with no lane active), so it never depends on a lane
having run.

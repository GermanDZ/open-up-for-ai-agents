# T-159 — design decisions

## DD1 — C1 fixes the source, not `reap`

The iteration-109 retrospective's *first* instinct, recorded in `docs/risk-list.md` R5, was
"give `reap` an age-based fallback for heartbeat-less claims". Measuring the premise
replaced it with something smaller: claims are **born** without a heartbeat, so stamping one
at creation closes the hole at its source and leaves `reap`'s backward-compat invariant —
correct for genuinely legacy files already on disk — untouched.

Requirement 4 asserts that invariant in the direction the fix must *not* move
(`test_legacy_heartbeatless_claim_still_skipped`), so a future simplification cannot quietly
turn this into a reap change.

One clock read is used for both `claimed_at` and `last_heartbeat`. Two timestamps
microseconds apart would invite a reader to find meaning in the difference; a claim is by
definition alive at the moment it is created.

## DD2 — C3: a predicate, not a widened return (design corrected mid-lane)

The spec first called for a third element on `update_roadmap()`'s return. Building it
revealed the conflict: **five pre-existing tests unpack that function as a 2-tuple**
(`test_sync_status_sections.py:60,69,76,77,83`), so widening it would have broken them and
contradicted this task's own requirement 8. `plan.md` requirement 5, Entities and Structure
were corrected **before** the code was written.

`roadmap_has_entry(text, task_id)` composes the two matchers `update_roadmap` already uses
(`_id_cell_matches` for table rows, `find_section_status` for sections), so there is no
second implementation to drift. `test_has_entry_matches_linked_id_cell` covers the
markdown-link row form specifically to prove the reuse is real rather than incidental, and
`test_update_roadmap_signature_unchanged` pins the 2-tuple so the rejected design cannot be
reintroduced silently.

**`changed` could not have served as the signal.** It is false both when the entry is absent
*and* when it is present but already correct — opposite situations. The predicate is called
**before** the write, because afterwards the two are indistinguishable.

## DD3 — The unmatched run still exits 0

Deliberate, and the reason is external. `/openup-complete-task`, `/openup-quick-task` and
`scripts/openup_agent/cycle.py` all treat a non-zero `sync-status.py` as fatal, so a
stricter exit code would convert a *reporting* bug into a completion outage — a strictly
worse failure than the one being fixed. The run genuinely did regenerate the project-status
header and `## Notes`, so it did useful work.

What changes is the claim: stdout now says `Synced project-status (status=…); roadmap
unchanged.` instead of `Synced roadmap + project-status for <task> …`, and stderr carries a
`WARNING` naming the task, the file, and the fix ("Add the entry, then re-run"). Recorded as
a vetoable Assumption in `plan.md` rather than settled silently.

## DD4 — Vacuous pass caught and removed

`test_claim_created_claim_is_reapable_when_stale` initially passed against the *unfixed*
code, because it back-dated `last_heartbeat` by assignment — introducing the very key whose
absence is the defect. It now asserts the field exists before back-dating it, which makes it
bite. Same class of vacuous pass flagged in T-157; caught here because that lane made a
habit of checking *why* a new test passes.

## DD5 — Verification

- **Both defects reproduced first**, against unmodified code: the claim payload lacked
  `last_heartbeat`; `sync-status.py` printed `Synced roadmap + project-status for T-777
  (status=in-progress).` with exit 0 for a task absent from the roadmap.
- **Bite check**: 3 of 4 new C1 tests and 5 of 7 new C3 tests failed pre-fix. The
  non-failing ones are deliberate guards — `test_legacy_heartbeatless_claim_still_skipped`
  (req 4, must pass both ways), `test_matched_task_output_unchanged` and
  `test_update_roadmap_signature_unchanged` (no-regression pins).
- **Additive across both suites**, stated separately per this lane's own safeguard:
  `tests/` **114 → 118**, `scripts/tests/` **884 → 891**, no assertion edited in either.
- **Empirical post-fix**: claim payload now carries `last_heartbeat`, equal to `claimed_at`;
  the unmatched sync emits the WARNING on stderr, the qualified line on stdout, exit 0.

### Step 1a — requirements graded against the diff

| # | Verdict | Evidence |
|---|---|---|
| 1 | ✅ | `openup-claims.py` payload gains `last_heartbeat`; `test_claim_writes_last_heartbeat` |
| 2 | ✅ | single `now_iso` used for both fields; `test_heartbeat_equals_claimed_at` |
| 3 | ✅ | `test_claim_created_claim_is_reapable_when_stale`, now non-vacuous per DD4 |
| 4 | ✅ | `cmd_reap` untouched; `test_legacy_heartbeatless_claim_still_skipped` passes unmodified |
| 5 | ✅ | `roadmap_has_entry()`; 4 tests incl. idempotent-section and linked-id-cell cases |
| 6 | ✅ | `main()` branches on `matched`; `test_unmatched_task_warns_on_stderr_and_exits_zero`; verified live |
| 7 | ✅ | `test_matched_task_output_unchanged` — stdout identical, stderr empty |
| 8 | ✅ | 114→118 and 884→891, no assertion edited |

**Result: 8/8 ✅.**

### Step 1b — success-measure instrumentation

`✅ instrumentation`, both committed by this task and both readable **in this repo** (the
named read-back environment): for C1, `TestClaimStampsHeartbeat` plus a one-line check over
`<git-common-dir>/openup/claims/*.json`; for C3, the stderr `WARNING` string itself — its
absence from a lane's completion output is the evidence there was nothing to warn about.
**Read-back: the second retrospective after landing**, backstop **2026-11-30**. The measure
requires reporting the lane count alongside the number, so a `0` from an empty window is not
mistaken for success.

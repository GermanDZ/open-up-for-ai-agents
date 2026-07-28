---
id: T-159
title: "Two silent failures: `claim` creates un-reapable claims; `sync-status` reports success for a task it cannot find"
status: ready
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-claims.py
  - scripts/sync-status.py
  - tests/test_claims_heartbeat_reap.py
  - scripts/tests/test_sync_status_sections.py
---

# T-159 — Two silent failures: `claim` creates un-reapable claims; `sync-status` reports success for a task it cannot find

## Story

> **As a** maintainer relying on OpenUP's tooling to tell me the truth about what it did
> **I want** `openup-claims.py claim` to produce a reapable claim, and `sync-status.py` to say when it matched nothing
> **So that** neither tool can leave the repo in a worse state while printing a success line — the failure mode that cost two lanes on 2026-07-27

INVEST check:
✅ Independent — two scripts, two existing test files · ✅ Negotiable — the warning's exit-code behaviour is open · ✅ Valuable — closes iteration-109's C1 (high) and C3 · ✅ Estimable — one payload field, one return flag · ✅ Small — well under 50 LOC of implementation · ✅ Testable — both defects reproduce mechanically today

## Analysis Context

- **Domain.** Two independent defects in `scripts/`, grouped because they are the same *class*: a tool that appears to succeed while leaving the caller worse off. Both were found by iteration-109's premise-verification pass.
- **Scope boundaries.** This does NOT change `reap`'s skip-when-no-heartbeat invariant (C1 fixes the source instead), does NOT add age-based reaping, does NOT change how `sync-status.py` derives status or which files it writes, and does NOT touch the `--views-only` path added by T-157.
- **Definition of done.** A claim written by bare `claim` carries `last_heartbeat`; a `sync-status.py` run that matches no roadmap entry says so instead of printing unqualified success.

**C1 premise (verified 2026-07-27, re-verified before drafting).** `cmd_claim`'s payload at `scripts/openup-claims.py:944-952` contains `task_id, session_id, branch, worktree, base_sha, claimed_at, touches` — **no `last_heartbeat`**. Confirmed empirically by claiming a throwaway id into an isolated `--claims-dir` and reading the written keys. `reap` skips heartbeat-less claims **by design** (`:1146-1147`, "backward-compat invariant"), so a claim created by bare `claim` can never be auto-reaped. Only `openup-session.py begin` stamps one, as a *separate* step after claiming.

**This is not hypothetical, and it is not only about legacy claims.** The documented recovery for mid-lane scope growth is release + `claim` (never `claim --force`, which strands the lane). That recovery was performed twice on 2026-07-27 — for T-157 and T-158 — and **each time it created a heartbeat-less, permanently un-reapable claim.** The 12 stale claims cleared that day were the same shape.

**C3 premise (verified — observed live during T-158).** With no roadmap entry for the task, `python3 scripts/sync-status.py` printed `Synced roadmap + project-status for T-158 (status=completed).` and wrote nothing to the roadmap. `update_roadmap()` tries table rows, falls back to `stamp_section_status()`, and returns the text unchanged when neither matches — but `main()` (`scripts/sync-status.py:623`) prints its success line unconditionally.

**The signal already exists and is discarded.** `stamp_section_status()` returns `(new_text, changed, title)` (`:226`) and `update_roadmap()` throws the middle value away: `new_text, _, sec_title = stamp_section_status(...)`. The fix propagates a match flag rather than inventing detection.

> **Assumption:** `claim` stamps `last_heartbeat` with the **same** timestamp as `claimed_at` (one `now()`, used twice) rather than a second clock read — a claim is by definition alive at creation, and two timestamps microseconds apart invites a reader to believe the difference is meaningful. *(Vetoable at review.)*

> **Assumption:** a `sync-status.py` run that matches no roadmap entry **warns on stderr and still exits 0**, rather than failing. It legitimately did useful work (the project-status header and `## Notes` were regenerated), and making it non-zero would break `/openup-complete-task`, `/openup-quick-task` and `openup_agent/cycle.py`, all of which treat a non-zero sync as fatal. The defect is the *false* success message, not the exit code. *(Vetoable at review.)*

> **Assumption:** "matched" means a table row matched **or** a `## T-NNN:` section was found — using `find_section_status(...) is not None`, not `changed`. `changed` is false both when the section is absent *and* when it is already correct (idempotent re-run), so it cannot distinguish them. *(Vetoable at review.)*

## Requirements

1. A claim written by `openup-claims.py claim` carries a `last_heartbeat` field.
   - **Given** an empty claims dir, **When** `openup-claims.py claim --task-id T-999 …` runs, **Then** the written `T-999.json` contains a `last_heartbeat` key whose value is a valid ISO-8601 `…Z` timestamp.

2. That heartbeat equals `claimed_at` at creation, so a fresh claim reads as alive.
   - **Given** a claim just created by `claim`, **When** its JSON is read, **Then** `last_heartbeat == claimed_at`.

3. A claim created by `claim` is therefore reapable once stale — closing the gap that made the 2026-07-27 cohort permanent.
   - **Given** a claim created by `claim` whose `last_heartbeat` is then back-dated beyond the stale threshold, **When** `openup-claims.py reap` runs, **Then** the claim is deleted and reported, rather than skipped as heartbeat-less.

4. `reap`'s existing skip-when-no-heartbeat invariant is unchanged for claims that genuinely lack the field.
   - **Given** a synthetic claim file on disk with **no** `last_heartbeat` (a legacy claim), **When** `reap` runs, **Then** it is still skipped, and `tests/test_claims_heartbeat_reap.py::test_skips_claim_with_no_heartbeat` still passes unmodified.

5. `update_roadmap()` reports whether it matched a roadmap entry, distinguishing "not found" from "found and already correct".
   - **Given** a roadmap containing a `## T-063:` section already reading `**Status**: completed (2026-01-01)`, **When** `update_roadmap(text, "T-063", "completed", today)` runs, **Then** it reports **matched** (idempotent, not missing); **and Given** the same roadmap and task id `T-900`, **Then** it reports **not matched**.

6. `sync-status.py` warns on stderr, instead of printing unqualified success, when it matched no roadmap entry.
   - **Given** a roadmap with no entry for the state's task id, **When** `sync-status.py` runs, **Then** stderr names the unmatched task id, stdout does **not** claim the roadmap was synced for it, and the exit code is still `0`.

7. A run that *does* match keeps its existing output and behaviour exactly.
   - **Given** a roadmap table row for the state's task id, **When** `sync-status.py` runs, **Then** stdout is the existing `Synced roadmap + project-status for <id> (status=<s>).` line, no warning is emitted, and the roadmap cell is stamped as before.

8. Both changes are additive: every existing test in both suites passes unmodified.
   - **Given** `tests/` (114) and `scripts/tests/` (884), **When** both run against the change, **Then** the pre-existing counts still pass with no assertion edited, and the totals rise only by the new cases.

## Behavior Delta

**Added:**
- `last_heartbeat` on every newly-created claim.
- A stderr warning from `sync-status.py` when no roadmap entry matches.
- A match flag in `update_roadmap()`'s return.

**Modified** — cited artifact + section:
- Claim payload contents — `docs-eng-process/parallel-work.md` describes the claim/lease model; the field list is documented in `docs-eng-process/script-cli-reference.md §openup-claims.py`. *(Both are documentation of a data shape that gains a field; neither asserts the old list is exhaustive, so this task changes no stated contract — see Do-not-touch.)*
- `sync-status.py`'s success output — `docs-eng-process/script-cli-reference.md §sync-status.py`.

**Removed** — none. `reap`'s invariant, all exit codes, and every existing flag are untouched.

## Entities

- **`cmd_claim`** (modified) — `scripts/openup-claims.py:944`; payload gains one field.
- **`cmd_reap`** (read-only) — `scripts/openup-claims.py:1142`; deliberately unchanged, and requirement 4 guards it.
- **`update_roadmap`** (modified) — `scripts/sync-status.py:138`; return gains a match flag.
- **`stamp_section_status`** (read-only) — `scripts/sync-status.py:225`; already returns the signal being propagated.
- **`main`** (modified) — `scripts/sync-status.py:623`; the unconditional success print.
- **Claim/reap tests** (modified) — `tests/test_claims_heartbeat_reap.py`.
- **Section/table tests** (modified) — `scripts/tests/test_sync_status_sections.py`.

## Approach

Both fixes move the check to where the information already is, rather than adding machinery downstream. For C1 the retrospective's first instinct — an age-based reap fallback — was rejected once the premise was measured: the defect is that claims are *born* without a heartbeat, so stamping one at creation closes it at the source and leaves `reap`'s backward-compat invariant (correct for genuinely legacy files) alone. For C3 the match signal is already computed and discarded, so the change is to propagate it and let `main()` phrase its output honestly; the run still exits 0 because it really did regenerate the project-status view, and three callers treat non-zero as fatal. Deliberately deferred: any change to how `reap` treats heartbeat-less claims, and any exit-code change.

## Structure

**Add:** nothing — both changes are edits to existing functions plus test cases.

**Modify:**
- `scripts/openup-claims.py` — add `last_heartbeat` to `cmd_claim`'s payload, reusing the `claimed_at` timestamp.
- `scripts/sync-status.py` — `update_roadmap()` returns a match flag; `main()` warns on stderr and adjusts stdout when unmatched.
- `tests/test_claims_heartbeat_reap.py` — cases for requirements 1–3 (real CLI, not the synthetic helper).
- `scripts/tests/test_sync_status_sections.py` — cases for requirements 5–7.

**Do not touch:**
- `cmd_reap`'s skip-when-no-heartbeat branch — tempting, since it is the proximate reason the stale cohort survived, but changing it would alter documented behaviour for legacy files on disk while C1 removes the *cause*. Requirement 4 asserts it still holds.
- `tests/test_claims_heartbeat_reap.py::test_skips_claim_with_no_heartbeat` — it writes a **synthetic** claim, so it must keep passing unmodified; if it fails, the fix went too far.
- `derive_status()`, `update_project_status()`, `assemble_notes()`, `run_views_only()` — C3 is about reporting, not derivation.
- `docs-eng-process/script-cli-reference.md` and `parallel-work.md` — the Behavior Delta names them as where the shapes are documented, but neither states an exhaustive field list or quotes the success string, so there is nothing to correct. Listed here so the omission reads as checked, not forgotten.

## Operations

- [ ] Reproduce both defects against the current code first: claim a throwaway id into an isolated `--claims-dir` and confirm the payload has no `last_heartbeat`; run `sync-status.py` against a roadmap with no matching entry and confirm it prints unqualified success.
- [ ] Write the failing cases — reqs 1–3 in `tests/test_claims_heartbeat_reap.py` (driving the real CLI), reqs 5–7 in `scripts/tests/test_sync_status_sections.py`; confirm each fails for the stated reason, not an import error.
- [ ] Implement C1: add `last_heartbeat` to `cmd_claim`'s payload reusing the `claimed_at` value; confirm reqs 1–3 pass and req 4's legacy test still passes untouched.
- [ ] Implement C3: propagate a match flag out of `update_roadmap()` and make `main()` warn on stderr / adjust stdout when unmatched, keeping exit 0; confirm reqs 5–7 pass.
- [ ] Verify additivity across **both** suites — `pytest tests/` and `pytest scripts/tests/` — and confirm the pre-existing counts (114 and 884) still pass with no assertion edited (req. 8).
- [ ] (tester) Verify the fixes bite where they were observed: re-run the C1 empirical check and confirm a heartbeat is now present; run `sync-status.py` against a no-entry roadmap and confirm the warning names the task id while the exit code stays 0.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process + script conventions.
- `docs-eng-process/parallel-work.md` — the claim/lease model C1 sits in.
- `docs-eng-process/state-file.md` — heartbeat/reap semantics.

## Safeguards

- **Do not change `reap`'s invariant.** C1 fixes the source. Requirement 4 is the guard; a failure in `test_skips_claim_with_no_heartbeat` means the fix overreached.
- **`sync-status.py` must keep exiting 0** on an unmatched task. `/openup-complete-task`, `/openup-quick-task` and `openup_agent/cycle.py` all treat non-zero as fatal; a stricter exit code would convert a reporting bug into a completion outage.
- **Both suites, every time.** This lane's own C2 sibling exists because "full suite" meant `scripts/tests/` only. Verification here must state both numbers.
- **No new dependencies, no new files.** Two edits and two test files.
- **Reversibility.** Revert the commit; both changes are additive and nothing persists a new format that would need migrating — a claim missing `last_heartbeat` still reads correctly.
- **Size budget.** ≤ ~30 LOC of implementation across both scripts. More means the shape was misread.

## Success Measures

We expect **the number of newly-created claims lacking `last_heartbeat`** to be **0** (from 2 of 2 re-claims on 2026-07-27), and **the number of `sync-status.py` runs that report success while matching no roadmap entry** to be **0** (from 1 observed in T-158), across **every lane in the next two retrospective cycles**. Instrumentation, both committed by this task: for C1, a test driving the real `claim` CLI and asserting the field, plus `python3 -c` over `<git-common-dir>/openup/claims/*.json` at any point (every live claim should have the field); for C3, the new stderr warning itself — its *absence* from a lane's completion output is the evidence there was nothing to warn about, and its presence is a caught defect rather than a silent one. Read-back environment: **this repo** — claims live in `.git/openup/` here and `sync-status.py` runs here on every completion. Read-back: **the second retrospective after landing** (absolute backstop **2026-11-30**).

A `0` here is meaningful rather than vacuous only if lanes actually ran in the window; if fewer than 3 lanes complete before read-back, report the lane count alongside the number.

## Rollout

`n/a — not user-facing.` Internal tooling; no flag. C1 changes a data shape additively — a claim without the field still parses, and `reap` still skips such files — so there is no migration and nothing to toggle. C3 changes one message and adds a warning. Both reach agents on merge and downstream consumers via their existing `sync-from-framework.sh`. No flag-removal follow-up is owed.

## Verification

- `asdf exec python3 -m pytest tests/ -q` — 114 pre-existing + new cases, all green.
- `asdf exec python3 -m pytest scripts/tests/ -q` — 884 pre-existing + new cases, all green.
- Empirical C1: claim into a temp `--claims-dir`, assert `last_heartbeat` present and `== claimed_at`.
- Empirical C3: run against a roadmap with no matching entry; stderr names the task, exit code 0.
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check` clean.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

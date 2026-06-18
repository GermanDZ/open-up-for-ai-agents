# T-053 — In-flight design decisions

## DD1 — Aggregation set is read-only only
Doctor is strictly read-only (Safeguard). So it aggregates only tools that have a
genuinely read-only invocation:
- `check-docs.py` (read-only validator) → failure = **error** (mirrors its complete-task BLOCKING role).
- `docs-index.py --check` → drift = **warning** (stale derived view).
- `build-trace-model.py --check` → drift = **warning**.
- `check-skills-guide.py --check`, `check-model-tiers.py --check`, `check-claude-sync.sh` → drift = **warning**; these are framework-repo-only (not in `process-manifest.txt`), so **absent in a downstream project → info "not present"**.
- `openup-fence.py check` → lane-diff-scoped; run only when `.openup/state.json` exists, else skip. Failure = **warning**.

**Excluded: `sync-status.py`** — it has no `--check`/read-only mode (it *writes* roadmap/status). Invoking it would violate read-only. Derived-view-drift is already covered by `docs-index.py --check`; status drift surfaces at complete-task's own sync. Recorded so a later reader doesn't "add the missing aggregation".

## DD2 — Framework-drift baseline
- Installed version = `docs-eng-process/.template-version` (currently 1.5.0).
- With `--framework-path <baseline-clone>`: compare versions (semver tuple) → behind = warning; then per manifest entry compare bytes → missing = **error**, differs = **warning**.
- Without a baseline (the common downstream case, and the only mode possible in this framework-source repo): report installed version + emit **info** "scripts not verified (no baseline)". Offline-degraded, never a failure.

## DD3 — State integrity reuses `openup-state.py validate`
No schema logic is reimplemented. Doctor shells `openup-state.py validate --state-dir <repo>/.openup`: exit 0 = ok; nonzero = **error** (surfacing its message). Absent state file = **info** "no active iteration".

## DD4 — Exit code
Nonzero iff any **error** finding exists. warning/info never fail the process (CI gates on errors only).

## Completion verification (step 1a/1b)

Graded against the actual diff + green tests (`scripts.tests.test_openup_doctor`, 13/13):
- ✅ R1 read-only — `test_read_only_does_not_mutate` (file mtimes unchanged); no write calls in `openup-doctor.py`.
- ✅ R2 framework-drift — `FrameworkDriftTests`: behind=warning, modified=warning, missing=error+exit1, offline=info.
- ✅ R3 state-integrity — `StateIntegrityTests`: corrupt=error+exit1, absent=info, valid=info (reuses `openup-state.py validate`).
- ✅ R4 aggregator — `AggregationTests`: failing check-docs=error, failing docs-index=warning, absent tool=info; invokes, never reimplements (DD1).
- ✅ R5 output contract — `ContractTests`: `--json` shape (severity/check/message), exit 0/1/2.
- ✅ R6 ships — `scripts/openup-doctor.py` in `process-manifest.txt`; `/openup-doctor` skill authored + synced to `.claude/`.

**Success-measure instrumentation (1b):** ✅ — the measure (failures doctor *would have* caught) is read back from doctor's own severity-tagged findings/exit codes (in the diff) cross-referenced with retro/run-log entries (pre-existing). Read-back: 2026-07-31 or first downstream adoption. Process-level measure, not app telemetry — no new event emitter required.

**Full suite:** 280/281 pass; the one failure (`test_docs_index.test_write_creates_index_file`) is the pre-existing macOS `/var`↔`/private/var` symlink path issue, documented in prior iteration notes, unrelated to T-053.

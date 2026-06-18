---
id: T-053
title: Add `scripts/openup-doctor.py` — read-only project health diagnostic + thin `/openup-doctor` skill
status: ready   # proposed → ready → in-progress → done → verified
priority: medium   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/explorations/2026-06-18-openup-doctor-health-check.md   # originating exploration (disposition "→ iteration", Option C)
depends-on: []
blocks: []
touches:
  - scripts/openup-doctor.py
  - scripts/tests/test_openup_doctor.py
  - scripts/process-manifest.txt
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/skills-guide.md
  - docs-eng-process/model-tiers.md
  - docs-eng-process/.claude-templates/skills/openup-doctor/
last-synced: ""
---

# T-053 — Add `scripts/openup-doctor.py` (read-only project health diagnostic) + thin `/openup-doctor` skill

## Story

> **As a** maintainer of a project that consumes OpenUP (downstream, fresh clone, or CI without the git hooks installed)
> **I want** one read-only command that tells me whether my installed framework is current and unmodified, whether my `.openup/state.json` is intact, and rolls up every existing read-only/`--check` validation
> **So that** I discover drift, a corrupt-state footgun, or a stale derived view *before* it silently mis-drives the workflow — instead of only at `complete-task` or never.

INVEST check:
✅ Independent — new script + thin skill; invokes existing checks, changes none of them ·
✅ Negotiable — severity lines and aggregation set are tunable ·
✅ Valuable — answers a question (framework-currency from a consumer POV) no command answers today ·
✅ Estimable — one deterministic script + manifest entry + skill wrapper ·
✅ Small — bounded by Option C scope; explicitly excludes re-implementing validators ·
✅ Testable — read-only, severity-tagged, `--json`, CI exit codes → hermetic fixtures assert each finding

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Project health / framework-adoption tooling. Sits alongside the existing validation suite (`check-docs.py`, `openup-fence.py`, the generator `--check` modes) and the version/manifest machinery (`.template-version`, `scripts/process-manifest.txt`, `sync-from-framework.sh`).
- **Scope boundaries.** This task does **not** re-implement document/fence/derived-view validation — doctor *invokes* the owning scripts and collates. It does **not** offer or apply fixes — strictly diagnostic/read-only. It does **not** replace `/openup-readiness` ("what can I work on") — doctor answers "is this project well-formed". It does **not** modify any existing validator.
- **Definition of done.** `python3 scripts/openup-doctor.py` runs in any OpenUP project, prints a severity-tagged human report (and `--json`), exits nonzero iff an `error`-severity finding is present, performs the two new checks (framework/manifest drift; state integrity) plus the aggregation, is registered in `process-manifest.txt`, and is fronted by a thin `/openup-doctor` skill. New checks covered by hermetic tests.

Non-blocking questions from the exploration, resolved by default (each vetoable at review):
> **Assumption:** Drift baseline is **offline-degraded by default** — with no `--framework-path`, doctor still reports version-currency from `.template-version` alone and emits an `info` "scripts not verified (no baseline)" note; a `--framework-path` enables byte-level CLI drift detection. *(Vetoable at review.)*
> **Assumption:** Severity model — **error** = corrupt/unreadable `.openup/state.json`, a manifest-listed CLI missing, or any aggregated check that itself exits error; **warning** = behind on framework version, a locally-modified shipped CLI, or a stale derived view (`--check` nonzero); **info** = advisory/coverage notes and "could not verify" degradations. Only `error` drives nonzero exit. *(Vetoable at review.)*
> **Assumption:** Doctor and `/openup-readiness` stay **separate commands** — no call-through in either direction for this task. *(Vetoable at review.)*

## Requirements

1. `openup-doctor.py` runs read-only and never writes, mutates, or fixes any file.
   - **Given** a project tree with a stale derived view and a corrupt state file **When** `openup-doctor.py` runs **Then** it reports both but the working tree is byte-for-byte unchanged afterward (no file mtime/content change attributable to doctor).
2. The framework-drift check reports version-currency and (with a baseline) per-CLI drift.
   - **Given** `.template-version` older than the framework baseline's version **When** doctor runs with `--framework-path <baseline>` **Then** it emits a `warning` "behind on framework version (X < Y)" finding.
   - **Given** a manifest-listed CLI that has been locally edited vs the baseline **When** doctor runs with `--framework-path` **Then** it emits a `warning` "locally modified: scripts/<name>" finding; **and Given** a manifest-listed CLI that is absent **Then** it emits an `error` "missing shipped CLI: scripts/<name>" finding.
   - **Given** no `--framework-path` supplied **When** doctor runs **Then** it still reports the installed version and emits an `info` "scripts not verified (no baseline)" finding rather than failing.
3. The state-integrity check validates `.openup/state.json` at read time.
   - **Given** a `.openup/state.json` that is malformed JSON or violates the state schema **When** doctor runs **Then** it emits an `error` finding naming the defect and exits nonzero.
   - **Given** no `.openup/state.json` (no active iteration) **When** doctor runs **Then** it emits an `info` "no active iteration state" finding, not an error.
4. The aggregator invokes the existing read-only / `--check` modes and collates results by severity without re-implementing their logic.
   - **Given** an aggregated check (e.g. `docs-index.py --check`) reports drift **When** doctor runs **Then** doctor surfaces that result as a `warning`/`error` line attributed to the owning script, and **Given** an aggregated tool is absent or errors out **Then** doctor degrades to an `info`/`warning` "could not run <tool>" line rather than crashing.
5. Output is severity-tagged human text by default and machine-readable under `--json`, with CI-gateable exit codes.
   - **Given** at least one `error` finding **When** doctor runs **Then** exit code is nonzero; **Given** only `warning`/`info` findings **Then** exit code is 0; **and Given** `--json` **Then** stdout is a single valid JSON object enumerating findings with `severity`, `check`, `message`.
6. Doctor ships into every project and is invokable as a skill.
   - **Given** a project installed/updated via the manifest **When** the install/update path runs **Then** `scripts/openup-doctor.py` is present (it is listed in `scripts/process-manifest.txt`); **and Given** a user runs `/openup-doctor` **Then** the skill executes the script and relays its report.

## Behavior Delta

This is framework tooling (process layer), not Ring-1 *product* behavior of a consuming app. No `docs/product/` artifact changes.

**Added** — behavior that did not exist before:
- A read-only `openup-doctor.py` health diagnostic (framework/manifest drift + state integrity + aggregation, severity-tagged, `--json`, CI exit codes).
- A `/openup-doctor` skill wrapping it.
- A new entry in `scripts/process-manifest.txt` so the CLI ships everywhere.

**Modified** — n/a (no existing validator's behavior changes; doctor only *invokes* them).

**Removed** — n/a.

## Success Measures

We expect **the share of downstream-adoption/sync issues caused by undetected framework-script drift or corrupt `.openup/state.json`** to **drop toward zero** within **the next ~3 iterations** of doctor shipping. Instrumentation: count of retro/run-log entries (and downstream reports) attributing a failure to drift/corrupt-state that `openup-doctor.py` *would have* surfaced — the falsifiable bar from the exploration ("does doctor surface a condition no existing check would have caught, on a real downstream project?"). Read-back: 2026-07-31, or first downstream adoption — whichever comes first.

## Entities

- **`openup-doctor.py`** (new) — `scripts/openup-doctor.py`, the real artifact.
- **`/openup-doctor` skill** (new) — `docs-eng-process/.claude-templates/skills/openup-doctor/SKILL.md` (canonical) + synced `.claude/skills/openup-doctor/SKILL.md`.
- **`process-manifest.txt`** (modified) — `scripts/process-manifest.txt`, add doctor.
- **`.template-version`** (read-only) — `docs-eng-process/.template-version`, the version half of the drift answer.
- **State schema** (read-only) — whatever `scripts/openup-state.py` validates against on write; reuse, don't fork.
- **Aggregated validators** (read-only, invoked) — `check-docs.py`, `openup-fence.py`, `sync-status.py --check`, `docs-index.py --check`, `build-trace-model.py --check`, `check-skills-guide.py --check`, `check-model-tiers.py --check`, `check-claude-sync.sh`.

## Approach

A single deterministic Python CLI, stdlib-only (matching the project-side hooks' constraint so it runs on a bare downstream clone). It collects `Finding(severity, check, message)` records from three sources: (1) a **drift module** comparing `.template-version` + manifest entries against an optional `--framework-path` baseline, degrading to version-only offline; (2) a **state-integrity module** reusing `openup-state.py`'s schema validation at read time; (3) an **aggregator** that subprocess-invokes each existing read-only/`--check` tool and maps its exit/output to a Finding, never copying its logic. A reporter renders findings grouped by severity (human) or as one JSON object (`--json`); process exit code is nonzero iff any `error` finding exists. The skill is a thin wrapper that runs the script and relays output.

## Structure

**Add:**
- `scripts/openup-doctor.py` — the diagnostic CLI (stdlib-only, read-only).
- `docs-eng-process/.claude-templates/skills/openup-doctor/SKILL.md` — canonical thin skill.
- `.claude/skills/openup-doctor/SKILL.md` — synced live copy (via the sync script, not hand-authored).
- `tests/` — hermetic test(s) for doctor's three check modules + exit-code/JSON contract (match the existing test harness location/convention).

**Modify:**
- `scripts/process-manifest.txt` — register `scripts/openup-doctor.py`.
- `docs-eng-process/script-cli-reference.md` — add doctor's signature (avoid `--help` round-trips).
- `docs-eng-process/skills-guide.md` — regenerated by `check-skills-guide.py --write` after the skill lands (derived; don't hand-edit).

**Do not touch:**
- `check-docs.py`, `openup-fence.py`, `sync-status.py`, `docs-index.py`, `build-trace-model.py`, `check-skills-guide.py`, `check-model-tiers.py`, `check-claude-sync.sh` — doctor invokes them; their logic is the single source of truth and must not be copied or altered.
- `openup-knowledge-base/**`, `docs-eng-process/templates/**` — OpenUP layer, read-only per the standing guardrail.

## Operations

- [x] Implement `scripts/openup-doctor.py` skeleton: `Finding` record, severity enum, arg parsing (`--json`, `--framework-path`, `--repo-root`), reporter (human + JSON), exit-code logic (nonzero iff any `error`).
- [x] Implement the **framework/manifest drift** check: read `.template-version`; with `--framework-path` compare version + per-CLI byte drift / missing against the manifest; offline-degraded `info` when no baseline.
- [x] Implement the **state-integrity** check: reuse `openup-state.py` schema validation to validate `.openup/state.json` at read time; absent file → `info`, malformed/invalid → `error`.
- [x] Implement the **aggregator**: subprocess-invoke each existing read-only/`--check` tool, map exit/output to Findings, degrade gracefully when a tool is absent or errors.
- [x] Register `scripts/openup-doctor.py` in `scripts/process-manifest.txt`; add its signature to `docs-eng-process/script-cli-reference.md`.
- [x] Author the thin canonical skill `docs-eng-process/.claude-templates/skills/openup-doctor/SKILL.md`; sync it to `.claude/` via the sync script; regenerate `skills-guide.md` with `check-skills-guide.py --write`.
- [x] (tester) Add hermetic tests covering all three check modules + the `--json`/exit-code contract; run the full suite and confirm green (note any pre-existing env-specific failures).

## Rollout

**Flagged?** No. Doctor is a new, additive, opt-in read-only command — running it changes nothing, and it is only invoked when a maintainer/CI calls it. There is no in-flight user state to protect and no behavior toggled on existing flows, so a flag would add ceremony without safety. Reach is via `process-manifest.txt` (ships to every install/update path) + the `/openup-doctor` skill. Reversible by removal (see Safeguards). `n/a — flag adds no safety for a read-only additive diagnostic.`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, `[T-053]` trailer, etc.).
- `docs-eng-process/script-cli-reference.md` — script CLI signature conventions.
- Existing `scripts/*.py` validators — follow their stdlib-only, `--check`/`--json`/exit-code idioms and severity vocabulary.

## Safeguards

- **Token / size budget.** Script focused on Option C scope; thin skill (no model-driven re-validation — the script is the artifact). No new logic copied from aggregated validators.
- **Reversibility.** Purely additive (new script + skill + one manifest line + doc references); revert by removing them. No data migration, no change to existing tool behavior.
- **No-go zones.** Read-only — doctor must never write/fix. Must not modify, fork, or duplicate the logic of any aggregated validator. Must not touch `openup-knowledge-base/**` or `docs-eng-process/templates/**`. Must not couple to `/openup-readiness`.
- **Stdlib-only.** Runs on a bare downstream clone with no extra deps (matches the project-side hook constraint).
- **Graceful degradation.** Missing baseline, missing state file, or an absent aggregated tool degrade to `info`/`warning` — never an unhandled crash.

## Verification

- `python3 scripts/openup-doctor.py` on this repo prints a severity-tagged report and exits 0 (healthy) or nonzero with a clear `error` line.
- `python3 scripts/openup-doctor.py --json` emits a single valid JSON object of findings.
- Hermetic tests for the three check modules + exit-code/JSON contract pass; full suite green (modulo documented pre-existing env failures).
- `scripts/openup-doctor.py` appears in `scripts/process-manifest.txt`; `/openup-doctor` resolves and runs.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-053/plan.md` exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

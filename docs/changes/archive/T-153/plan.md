---
id: T-153
title: "Nothing exercises the install path end to end, so consumer-only breakage is invisible"
status: done
priority: high
estimate: 0.5 session
plan: ""
depends-on: [T-150]
blocks: []
last-synced: ""
touches:
  - scripts/tests/test_consumer_smoke.py
  - docs/roadmap.md
---

# T-153 — Nothing exercises the install path end to end, so consumer-only breakage is invisible

## Story

> **As** the framework maintainer
> **I want** one test that installs a throwaway consumer and asserts it came out usable
> **So that** a change that is correct in this repo but broken in every consumer fails in
> CI instead of in someone else's project.

INVEST check:
✅ Independent (T-150 already merged) · ✅ Negotiable · ✅ Valuable (this class of bug has
shipped repeatedly) · ✅ Estimable (one pytest file over an existing, network-free script) ·
✅ Small · ✅ Testable (the smoke test is itself the assertion).

## Analysis Context

- **Domain.** The install path — `scripts/bootstrap-project.sh` (network-free,
  `--base-dir DIR <name>`) and the artifacts it must leave in a consumer.
- **Scope boundaries.** NOT a consumer integration suite. Does not test
  `install-openup.sh`'s version-resolution modes, `update-from-template.sh`, or any
  network path. Does not re-test what is already covered (see below). Adds no production code.
- **Definition of done.** One pytest file bootstraps a consumer into a temp dir and asserts
  the result is usable — process CLIs shipped, hook wiring present **and guarded**, the
  self-updater shipped, and the consumer not misdetectable as the framework.

**Two of the three sub-items in the roadmap entry are already covered — verified, not assumed.**

| Sub-item (from iteration-86 action item 1) | Status |
|---|---|
| `sync-from-framework` detection | **Already covered** — `scripts/tests/test_sync_from_framework_detection.py` (3 tests, real consumer fixtures: stale-templates consumer, plain consumer, framework self-abort) |
| tracked bypass-log dirty-stop | **Already covered** — `scripts/tests/test_t006_hooks.py` (the downstream-tracks-bypass-log case is explicit there) |
| settings / hook-script skew | **Not covered as a consumer scenario.** T-150 tests the guard *form*; nothing asserts a bootstrapped consumer actually receives guarded wiring |

So the genuine gap is narrower and sharper than "add a consumer smoke check": **no test runs
the install path at all.** Every existing test starts from a hand-built fixture that asserts
what the author believed the installer produces. This task closes that by using the real
installer.

> **Assumption:** the smoke check drives `bootstrap-project.sh` only. It is the network-free
> entry point that produces a complete consumer, so it exercises the most install surface per
> unit of runtime. `install-openup.sh`'s version modes are a separate concern with their own
> failure shapes. *(Vetoable at review.)*

> **Assumption:** assertions are about **usability**, not file inventory. "Every manifest
> entry is present" would restate `process-manifest.txt` and break on every legitimate
> addition; "the consumer has guarded hook wiring and a working updater" is the property that
> actually matters and is stable across additions. *(Vetoable at review.)*

> **Assumption:** the test skips (not fails) if `bootstrap-project.sh` is absent, matching
> `test_run_log_hooks.py`'s precedent for environment-dependent suites. *(Vetoable at review.)*

## Requirements

1. The smoke check installs a consumer using the real installer.
   - **Given** a temp directory, **When** the test runs `bootstrap-project.sh --base-dir <tmp>
     <name>`, **Then** it exits 0 and creates the project directory.

2. The bootstrapped consumer receives the process CLIs it needs to operate.
   - **Given** a freshly bootstrapped consumer, **When** its `scripts/` is inspected,
     **Then** the OpenUP CLIs it must run locally are present and executable.

3. The consumer receives its own self-updater.
   - **Given** the same consumer, **When** `scripts/sync-from-framework.sh` is checked,
     **Then** it exists — a consumer with no way to update is the T-110 failure.

4. The consumer's hook wiring is present and **guarded** (the T-150 property, consumer side).
   - **Given** the same consumer, **When** every `hooks[].command` in its settings is read,
     **Then** each is existence-guarded, so a partially-synced consumer cannot be locked out
     of both Bash and Write.

5. The consumer is not misdetectable as the framework repo.
   - **Given** the same consumer, **When** the framework-exclusive marker
     (`scripts/sync-templates-to-claude.sh`) is checked, **Then** it is absent, so
     `sync-from-framework.sh`'s auto-detection cannot mistake the consumer for its own source.

6. The check is hermetic and offline.
   - **Given** no network access, **When** the smoke test runs, **Then** it passes without
     any fetch, and leaves nothing outside its temp directory.

## Behavior Delta

**Added** — behavior that did not exist before:
- An end-to-end assertion that the install path produces a usable consumer.

**Modified** — behavior that changes:
- None. This task adds a test and changes no product behavior.

**Removed** — behavior that no longer holds:
- None.

## Entities

- **Smoke check** (new) — `scripts/tests/test_consumer_smoke.py`
- **Installer under test** (read-only) — `scripts/bootstrap-project.sh`
- **Shipped surface** (read-only) — `scripts/process-manifest.txt`, `docs-eng-process/.claude-templates/`
- **Existing coverage, not duplicated** (read-only) — `scripts/tests/test_sync_from_framework_detection.py`, `scripts/tests/test_t006_hooks.py`, `scripts/tests/test_hook_command_guards.py`

## Approach

Run the real installer into a temp directory and assert the four properties that make the
result *usable* rather than merely present: the CLIs are there, the self-updater is there,
the hook wiring is guarded, and the consumer cannot be mistaken for the framework. Asserting
usability rather than a file inventory keeps the test stable as the manifest grows — a
inventory test would restate `process-manifest.txt` and fail on every legitimate addition,
which is how a smoke check becomes noise and then gets deleted. The three already-covered
sub-items are deliberately not re-tested; the value here is that the installer itself runs.

## Structure

**Add:**
- `scripts/tests/test_consumer_smoke.py` — bootstrap into `tmp_path`, then the assertions above.

**Modify:**
- `docs/roadmap.md` — status row for T-153.

**Do not touch:**
- `scripts/bootstrap-project.sh` — under test; changing it here would invalidate the test.
- `scripts/process-manifest.txt` — the shipped surface is a separate decision.
- `test_sync_from_framework_detection.py` / `test_t006_hooks.py` — already cover their
  sub-items; duplicating them costs runtime and gains nothing.

## Operations

- [x] Add `scripts/tests/test_consumer_smoke.py` that bootstraps a consumer into `tmp_path`
      via the real `bootstrap-project.sh` and asserts it exits 0 and created the project.
- [x] Assert the consumer is usable: process CLIs present and executable, and
      `scripts/sync-from-framework.sh` shipped.
- [x] Assert the consumer's hook commands are all existence-guarded, and that the
      framework-exclusive marker is absent so it cannot be misdetected as the framework.
- [x] (tester) Run the new file plus the full suite; confirm hermetic (no network, nothing
      written outside `tmp_path`) and that it fails if the guard is stripped.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format
- `.claude/CLAUDE.openup.md` — legal exits, token-efficiency protocol
- `docs-eng-process/parallel-lanes.md` — lane-owned surfaces

## Safeguards

- **Hermetic.** No network, no writes outside `tmp_path`, no dependency on a sibling repo.
- **Do not restate the manifest.** Assert usability properties, not a file list — an
  inventory test breaks on every legitimate addition and gets deleted.
- **Do not duplicate existing coverage.** Detection and the bypass-log dirty-stop are
  already tested; re-testing them costs runtime and hides where the real coverage lives.
- **Runtime budget.** The whole file ≤ ~15s; it runs in the default suite.
- **Reversibility.** Test-only; deleting the file restores the prior state exactly.
- **No-go zones.** `bootstrap-project.sh` itself, the manifest, the production scripts.

## Success Measures

We expect **the number of consumer-only breakages that reach a downstream repo before CI
catches them** to move **from at least 2 known (T-110's missing self-updater; T-150's
hook-script skew) to 0** across **the next 3 changes touching the install path or
`.claude-templates/`**. Instrumentation: `scripts/tests/test_consumer_smoke.py` itself — it
fails the suite when a bootstrapped consumer comes out unusable, which is exactly the event
being counted. **Read-back environment: this repo** — the test runs here and the suite result
is read here. Read-back: at the next retrospective.

## Rollout

**Flagged? No.** A test has no runtime path to gate and reaches no users; the kill switch is
deleting the file. Not user-facing, so `n/a` for environment defaults and in-flight users —
no user state exists to strand.

## Verification

- `python3 -m pytest scripts/tests/test_consumer_smoke.py -q` passes.
- Negative check: stripping the guard from the shipped settings makes requirement 4 fail.
- Full suite green; runtime increase ≤ ~15s.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-153/plan.md` exits 0.
- `python3 scripts/check-docs.py` exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ (including
  criterion 12's new read-back-environment element from T-152).

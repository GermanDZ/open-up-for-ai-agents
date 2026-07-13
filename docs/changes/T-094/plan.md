---
id: T-094
title: Cycle recovery — consent-gated LLM replenishment when nothing is promotable
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-092]
blocks: []
touches:
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-094 — Consent-gated replenishment: ask the human, then let the LLM propose what's next

## Story

> **As** a practitioner running the `cycle` loop on a real project
> **I want** the engine, when even recovery has nothing deterministic left — a
> present-but-exhausted (or fully blocked) roadmap mid-phase — to *ask me*
> whether one bounded product-manager sub-run may propose the next roadmap
> entries, and on my "yes" to replenish, re-resolve, and keep delivering in the
> same invocation
> **So that** the loop recovers from its last stranding case without ever
> inventing scope silently: choosing what's next is the product-manager's
> value-ordering authority, so the LLM proposes and the human consents/vetoes.

INVEST — ✅ Independent (extends T-092's recovery; composes T-074 input-requests) · ✅ Negotiable (`--auto-replenish` deferred) · ✅ Valuable (closes the last loop-strand) · ✅ Estimable · ✅ Small (engine-only + tests + docs) · ✅ Testable (seam + fake-scripts fixture)

## Analysis Context

- **Domain.** `scripts/openup_agent/cycle.py` recovery (T-092). Post-T-092 the
  loop still strands when the repo state is *complete but empty of direction*:
  `noop` with a roadmap present but nothing promotable while the phase isn't
  done, or a recovery round that cannot advance (`plan-iteration` whose lane is
  blocked). The missing ingredient is product judgment, not ceremony.
- **The consent mechanism is the existing T-074 machinery**, used exactly as
  `ask_user` uses it: interactive ⇒ TTY prompt; otherwise
  `openup-input.py request` (multiple-choice `yes`/`no`, no `--task-id` — this
  question belongs to no lane) + the SUSPEND sentinel + exit 5. The request
  path is remembered in `.openup/cycle.json` so later cycles re-read the same
  request instead of spamming new ones; the human answers by flipping
  `status: answered` and filling the `**Answer**:` line.
- **Scope boundaries.** Fresh-no-roadmap stays the T-092 Inception hint (a
  vision cannot be consented into existence); `assess-iteration` /
  `milestone-review` stay T-091; multi-item Plan Iteration stays T-090 (which
  will *reuse* this PM judgment step via the planned path). No new CLI flags.
- **Definition of done.** A stuck cycle asks once (TTY or input-request), a
  pending ask suspends every subsequent cycle without duplicates, an answered
  "no" ends the cycle cleanly and is not re-asked, and an answered "yes" runs
  ONE product-manager sub-run that makes the roadmap promotable again — after
  which the SAME invocation chains into T-092 spec-authoring and delivery. All
  hermetic.

> **Assumption:** `--auto-replenish` (skip the ask for unattended loops) is
> **deferred out of this task** — the consent gate is the control point that
> keeps the PM value-ordering authority with a human; revisit only after live
> experience with the ask flow. *(Vetoable at review.)*

> **Assumption:** Stuck-triggers are exactly: (T1) a `noop` decision with
> `docs/roadmap.md` present (after Case B closure); (T2) a `plan-iteration`
> recovery that cannot advance (lane blocked, or authored spec not pickable).
> At most ONE ask and ONE replenishment per invocation. *(Vetoable at review.)*

> **Assumption:** An answered **no** is remembered (consumed in
> `.openup/cycle.json`) and ends that and future cycles with a clean DONE until
> the stuck condition itself changes — declining is an answer, not a snooze.
> *(Vetoable at review.)*

> **Assumption:** The replenishment sub-run wears the **product-manager** hat
> at the `authoring` tier, and its acceptance gate is deterministic:
> `openup-roadmap.py next` must exit 0 afterwards (something is promotable),
> plus `check-docs.py` when present; the roadmap commit is tagged
> `[openup-skip]` (planning-artifact edit belonging to no lane). *(Vetoable at
> review.)*

## Requirements

1. **Stuck detection + one ask.** With recovery on, trigger T1
   (`noop` + roadmap present, post-Case-B) or T2 (non-advancing
   `plan-iteration` recovery) leads to exactly one consent ask per invocation;
   `--no-recover` (or a missing roadmap) never asks.
   - **Given** a fixture whose decision is `noop` with a `docs/roadmap.md`
     present **When** `cycle` runs non-interactively **Then** one input-request
     is created (multiple-choice yes/no, no related task), the SUSPEND sentinel
     is the last stdout line, and the exit code is 5.
   - **Given** the same fixture without `docs/roadmap.md` **When** `cycle` runs
     **Then** no request is created and the DONE sentinel carries the T-092
     Inception hint.

2. **Interactive consent.** Under `--interactive` the ask happens on the TTY;
   "yes" proceeds to replenishment, anything else ends the cycle cleanly.
   - **Given** an interactive run whose ask seam answers `yes` **When** the
     stuck trigger fires **Then** the replenishment sub-run runs with no
     input-request created.
   - **Given** an ask seam answering `no` **When** the stuck trigger fires
     **Then** `cycle` exits 0 with a DONE sentinel naming the declined
     replenishment and runs no sub-run.

3. **Pending ask never duplicates.** While the recorded request is still
   `pending`, every subsequent stuck cycle re-suspends pointing at it and
   creates nothing new.
   - **Given** a recorded pending replenishment request **When** `cycle` runs
     again on the same stuck state **Then** exit 5, the sentinel names the
     existing request path, and `docs/input-requests/` gained no new file.

4. **Answered "yes" replenishes and continues the same cycle.** The
   product-manager sub-run proposes pending roadmap entries; after the
   deterministic acceptance gate and the roadmap commit, the SAME invocation
   re-resolves and chains into the T-092 recovery → pick → delivery.
   - **Given** a recorded request answered `yes` and sub-run seams that (a)
     append a promotable roadmap row and (b) author its spec **When** `cycle`
     runs **Then** the run ends `OPENUP-NEXT: ADVANCED — <new-task>` with the
     replenishment sub-run wearing the `product-manager` hat, the spec sub-run
     wearing `analyst`, in that order, and the roadmap commit precedes the spec
     commit.

5. **Answered "no" is respected durably.** A declined request is consumed and
   the cycle (and later cycles) end cleanly without re-asking.
   - **Given** a recorded request answered `no` **When** `cycle` runs twice
     **Then** both runs exit 0 with a DONE sentinel naming the decline, no
     sub-run runs, and no new request is created.

6. **Replenishment acceptance is deterministic.** A sub-run that does not make
   the roadmap promotable (`openup-roadmap.py next` still non-zero) fails the
   cycle typed, uncommitted alongside half-state.
   - **Given** an answered-`yes` request and a sub-run seam that changes
     nothing **When** `cycle` runs **Then** it exits 8 and no roadmap commit
     was created.

7. **Non-stuck behavior unchanged.** `pick`/`resume`, Case A/B recovery on
   advancing decisions, assess/milestone exits, and `--no-recover` semantics
   are untouched; the pre-existing suites pass with exactly one sanctioned
   edit — the T-092 test that asserted the *old* noop-with-roadmap default
   (`test_noop_with_roadmap_has_no_hint`) now passes `recover=False`, because
   that default is what this task changes (the ask; `--no-recover` keeps the
   old behavior reachable — the T-092 DD7 precedent).
   - **Given** the pre-existing T-089/T-092 test suites with only that one
     assertion switched to `recover=False` **When** they run **Then** they
     pass, and no other pre-existing test needed changes.

## Behavior Delta

**Added**
- Consent-gated replenishment: stuck detection (T1/T2), the yes/no ask
  (TTY or input-request + suspend), the product-manager replenishment sub-run,
  its deterministic acceptance gate, and the consumed-answer memory.

**Modified**
- `openup-agent.py cycle` on a stuck `noop`/non-advancing decision with
  recovery on: was a bare DONE / typed exit 7 — now asks first (suspends
  non-interactively) and can continue delivering after consent —
  `docs-eng-process/reference-driver.md §Recovery mode` (the authored doc of
  record; updated by this task).

**Removed** — none.

## Entities

- **cycle engine** (modified) — `scripts/openup_agent/cycle.py` (stuck
  detection, ask, replenish sub-run, answer memory in `.openup/cycle.json`)
- **engine tests** (modified) — `scripts/tests/test_openup_agent_cycle.py`
- **input-request CLI** (read-only, composed) — `scripts/openup-input.py`
  (`request --json`, answer read from the request file's frontmatter/body)
- **roadmap CLI** (read-only, composed) — `scripts/openup-roadmap.py`
  (`next` as the acceptance gate)
- **docs** (modified) — `docs-eng-process/reference-driver.md`,
  `docs-eng-process/script-cli-reference.md`

## Approach

Extend T-092's recovery with a third, human-gated case: after Case B (and
after a failed Case A advance), a stuck decision routes through a small
consent state machine keyed by `.openup/cycle.json` — no record ⇒ ask (TTY or
`openup-input.py request` + suspend); pending ⇒ re-suspend; answered-no ⇒
consumed + clean DONE; answered-yes ⇒ one product-manager sub-run through the
existing `_dispatch_judgment`, gated by `openup-roadmap.py next` + `check-docs`,
committed `[openup-skip]`, then one re-resolve that falls into the T-092
pipeline. Everything composes existing scripts; no new mechanism beyond the
consent memory.

## Structure

**Add:** *(nothing — no new files)*

**Modify:**
- `scripts/openup_agent/cycle.py` — stuck detection + consent flow +
  `REPLENISH_CONTRACT` + acceptance gate
- `scripts/tests/test_openup_agent_cycle.py` — replenishment test class (fake
  `openup-input.py` + `openup-roadmap.py` join the fixture's fake scripts)
- `docs-eng-process/reference-driver.md` — replenishment under §Recovery mode
- `docs-eng-process/script-cli-reference.md` — cycle blurb update

**Do not touch:**
- `scripts/openup-input.py`, `scripts/openup-roadmap.py` — composed as-is; a
  gap found there is its own task
- `scripts/openup-agent.py` — no new flags (`--interactive`/`--no-recover`
  already cover the surface; `--auto-replenish` is deferred by assumption)
- `docs-eng-process/procedures/` (T-091), bench harness/scenarios (T-090)

## Operations

- [x] Implement the consent state machine in `cycle.py` (stuck triggers T1/T2
      post-recovery, cycle.json memory: none→ask / pending→re-suspend /
      no→consumed-DONE / yes→proceed; TTY path behind `--interactive` with an
      `_ask` test seam; async path via `openup-input.py request` + SUSPEND
      sentinel + exit 5) with hermetic tests for Req 1, 2, 3, 5
- [x] Implement the replenishment sub-run + acceptance (product-manager box
      through `_dispatch_judgment` with `REPLENISH_CONTRACT`, deterministic
      gate `openup-roadmap.py next` + `check-docs`, `[openup-skip]` roadmap
      commit, single re-resolve chaining into T-092 recovery) with hermetic
      tests for Req 4, 6 incl. the full stuck→consent→replenish→spec→deliver
      chain
- [x] Prove invariance: full driver+bench+cycle+roadmap suites pass unmodified
      (Req 7)
- [ ] (analyst) Document replenishment (triggers, ask flow, answer semantics,
      acceptance gate, deferred `--auto-replenish`) in `reference-driver.md` +
      `script-cli-reference.md`
- [ ] (tester) Run suites + `openup-spec-scenarios.py check` on this spec +
      `check-docs.py` + `openup-fence.py check --base harness-optional`;
      record results in `docs/changes/T-094/design.md`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions
- `docs-eng-process/parallel-lanes.md` — planning-artifact edit rules the
  roadmap commit must respect
- `.claude/teammates/product-manager.md` — the role whose authority the
  consent gate protects

## Safeguards

- **No silent scope invention.** The replenishment sub-run runs only after an
  explicit human "yes" (TTY or answered request) — there is no bypass flag in
  this task.
- **T-092/T-089 invariance.** Non-stuck paths byte-equivalent; pre-existing
  suites pass unmodified.
- **One ask, one replenishment, one re-resolve** per invocation — bounded, no
  loops, no request spam (pending answers re-suspend).
- **Compose, never reimplement**; **stdlib-only**; roadmap edits append-only by
  contract (existing rows/status cells untouched — the instruction says so and
  the acceptance gate plus fence keep it honest).
- **Reversibility.** Proposed rows are `pending` roadmap text — a human edit or
  revert undoes them; the consent memory is Ring-3 (`.openup/cycle.json`).

## Success Measures

We expect **zero unrecoverable loop strandings on a roadmap-present project**:
on the owner's next live my-product session, driving `cycle` repeatedly past
the point where the roadmap drains produces an input-request (or TTY ask)
rather than a dead stop, and one approved replenishment resumes delivery to
the next `ADVANCED` sentinel — read from the driver stderr `recovery:` lines
and `docs/input-requests/`. Read-back: recorded in
`docs/changes/T-094/design.md` after that session (owner-side; no endpoint in
this sandbox — T-089/T-092 precedent).

## Rollout

Not config-flagged — the behavior activates only inside recovery mode, so
`--no-recover` is the existing kill-switch, and the ask itself is the per-use
control point (nothing happens without a human "yes"). Declining is durable
(consumed answer). No temporary debt → no flag-removal follow-up.

## Verification

- `python3 -m unittest scripts.tests.test_openup_agent_cycle
  scripts.tests.test_openup_agent scripts.tests.test_openup_agent_tools
  scripts.tests.test_openup_agent_bench scripts.tests.test_openup_roadmap` — all green
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-094/plan.md` — exit 0
- `python3 scripts/check-docs.py` — exit 0
- `python3 scripts/openup-fence.py check --base harness-optional` — exit 0
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a
  clear gap call-out.

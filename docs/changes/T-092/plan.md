---
id: T-092
title: Cycle recovery mode — degenerate plan-iteration bridge + unclosed-lane reconcile
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-089]
blocks: []
touches:
  - scripts/openup-agent.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-092 — Cycle recovery mode: rebuild what blocks the loop, then continue

## Story

> **As** a practitioner driving a real project with `openup-agent.py cycle`
> (the my-product live test, 2026-07-13)
> **I want** the engine, when it cannot proceed deterministically, to *rebuild
> the repo state that blocks it* — author the missing task spec via one bounded
> sub-run, or finish a done-but-unclosed lane's closure ceremony — and then
> continue the same cycle
> **So that** the loop runs end-to-end on a local model instead of stalling at
> a typed exit 7 the moment the board says `plan-iteration`, without
> resurrecting the 1–2M-token LLM-orchestrated `next` path.

INVEST — ✅ Independent (extends delivered T-089 only) · ✅ Negotiable (assess/milestone stay out) · ✅ Valuable (unstalls the real-project loop today) · ✅ Estimable · ✅ Small (one module extended + flag + tests) · ✅ Testable (seam + scripted-LLM tests)

## Analysis Context

- **Domain.** `scripts/openup_agent/cycle.py` (T-089) and its CLI front. Two
  recovery cases, both discovered live on `/tmp/openup-samples/my-product`:
  - **Case A — missing spec.** `resolve` returns `plan-iteration` and already
    names the next work item (`lane.task`); only `docs/changes/<id>/plan.md`
    is missing. One bounded sub-run authors it; the same cycle then picks it.
    (This is the T-077 quick-archetype *degenerate single-work-item* Plan
    Iteration — the first slice of T-090, delivered as a bridge.)
  - **Case B — done-but-unclosed lane.** A plan with a satisfied `status:`
    (`done`/`verified`) still sits in **active** `docs/changes/` with its work
    unmerged (my-product T-001: folder never archived, branch never merged to
    trunk). Invisible to `resolve` (satisfied lanes are dropped), so the loop
    plans NEW work atop an unfinished delivery. Closure is pure ceremony —
    archive → commit → sync → merge to trunk — zero LLM.
- **Scope boundaries.** Multi-item Plan Iteration (minting, objectives,
  clusters, iteration-plan instances) stays T-090. `assess-iteration` /
  `milestone-review` keep their typed exit 7 (T-091). No procedure-pack
  changes; `run` and the Claude Code path untouched; no bench scenario here
  (T-090 benchmarks planning).
- **Definition of done.** On a project whose board says `plan-iteration`,
  `cycle` (recovery on) authors the named item's spec through one sub-run,
  gates + commits it, re-resolves, and executes the lane in the same
  invocation; a done-but-unclosed lane is closed deterministically before
  planning; `--no-recover` restores today's exact behavior — all proven
  hermetically.

> **Assumption:** Recovery is **on by default**; `--no-recover` opts out (a
> stalled loop is the failure mode worth defaulting against; the bare exit 7
> stays available for callers that key on it). *(Vetoable at review.)*

> **Assumption:** Case B runs only on the `plan-iteration` and `noop` decision
> paths — a `pick`/`resume` proceeds untouched (closure debt is caught on the
> next planning cycle, and never delays ready work). *(Vetoable at review.)*

> **Assumption:** Case B's merge rule: trunk = `origin/HEAD` → `main` →
> `master` (first that exists); merge `--no-ff` only when the current branch
> differs from trunk and the tree is clean after the closure commit; a merge
> conflict exits 8 with the branch left intact for a human. On-trunk closure
> skips the merge. *(Vetoable at review.)*

> **Assumption:** The spec-authoring sub-run reuses the T-089 judgment-step
> machinery (a synthetic `analyst`-hat box; tier `authoring`; the same
> `--step-max-iterations` cap) rather than a new mechanism. *(Vetoable at
> review.)*

> **Assumption:** One recovery round per case per invocation; if the re-resolve
> does not advance to `pick`/`resume`, exit 7 as today (no loops). *(Vetoable
> at review.)*

## Requirements

1. **Case B — unclosed-lane reconcile, zero LLM.** With recovery on, a
   `plan-iteration`/`noop` decision first closes every active
   `docs/changes/<id>/` whose plan `status:` is satisfied (`done`/`verified`):
   archive the folder, commit, regenerate views (fail-open), merge to trunk
   per the merge-rule assumption, then re-resolve.
   - **Given** a fixture with an active done-status folder and a board that
     resolves `plan-iteration` **When** `cycle` runs with a seam that fails on
     any LLM use **Then** the folder is under `docs/changes/archive/`, a
     closure commit exists, and execution continued with the re-resolved
     decision — with zero sub-runs.
   - **Given** the same fixture already on trunk **When** recovery closes the
     lane **Then** no merge is attempted and closure still completes.

2. **Case A — missing-spec recovery via one bounded sub-run.** After Case B, a
   `plan-iteration` decision triggers ONE spec-authoring sub-run (synthetic
   `analyst` box) whose instruction names the work item (`lane.task`), its
   roadmap title, and the spec contract (typed frontmatter incl. `touches`,
   Given/When/Then scenarios, engine-convention `## Operations` boxes). No
   session is begun before the spec exists.
   - **Given** a `plan-iteration` decision for `T-002` and a `_subrun` seam
     that writes a valid `docs/changes/T-002/plan.md` **When** `cycle` runs
     **Then** exactly one sub-run ran, its hat is `analyst`, its instruction
     contains `T-002` and the contract pointers, and no `session begin` ran
     before the sub-run.

3. **Spec gated + committed before continue.** The authored spec must exist,
   pass `check-docs.py`, and pass `openup-spec-scenarios.py check <plan>` when
   that script is present; it is committed (`docs(<id>): …`) before the
   re-resolve. Any failure exits 8 with nothing half-claimed.
   - **Given** a sub-run that produces no `plan.md` **When** recovery gates it
     **Then** `cycle` exits 8 and no session was begun.
   - **Given** a produced spec and green gates **When** recovery finishes Case
     A **Then** a commit containing `docs/changes/T-002/plan.md` exists before
     the lane is claimed.

4. **Same-cycle continuation, bounded.** After a successful Case A the same
   invocation picks and executes the new lane; if the re-resolve does NOT
   advance to `pick`/`resume`, `cycle` exits 7 exactly as today (one recovery
   round, no loops).
   - **Given** the valid-spec seam of Req 2 whose lane then resolves to `pick`
     **When** `cycle` runs **Then** the lane's Operations execute and the run
     ends `OPENUP-NEXT: ADVANCED — T-002`, all in one invocation.
   - **Given** a sub-run that writes a spec whose status stays `proposed` (not
     pickable) **When** recovery re-resolves **Then** `cycle` exits 7.

5. **Opt-out restores T-089 behavior.** `--no-recover` (CLI) / `recover=False`
   (API) yields today's exact semantics on every path.
   - **Given** `--no-recover` and a `plan-iteration` decision with a
     done-status active folder present **When** `cycle` runs **Then** it exits
     7, no sub-run ran, and the folder is untouched.

6. **Non-recovery paths unchanged.** `pick`/`resume`/`suspend` behavior and the
   `assess-iteration`/`milestone-review` typed exit 7 are unaffected by
   recovery; the pre-existing cycle/driver/bench suites pass with exactly one
   sanctioned edit — the T-089 test that asserted the *old* `plan-iteration`
   default now passes `recover=False`, because that default is what this task
   changes (Req 5 keeps the old behavior reachable).
   - **Given** an `assess-iteration` decision with recovery on **When** `cycle`
     runs **Then** it exits 7 with no sub-run and no closure side effects.
   - **Given** the pre-existing T-089 test suite with only the
     `plan-iteration`-default assertion switched to `recover=False` **When** it
     runs **Then** it passes, and no other pre-existing test needed changes.

## Behavior Delta

**Added**
- Recovery mode (default-on): Case A missing-spec authoring sub-run; Case B
  unclosed-lane closure; `--no-recover` opt-out.

**Modified**
- `openup-agent.py cycle` on a `plan-iteration` decision: was *always* typed
  exit 7 (T-089) — now recovers by default, exit 7 only under `--no-recover`
  or when recovery cannot advance the decision —
  `docs-eng-process/reference-driver.md §The cycle engine` (the authored doc
  of record for this behavior; updated by this task).

**Removed** — none.

## Entities

- **cycle engine** (modified) — `scripts/openup_agent/cycle.py` (recovery
  orchestration, Case A/B helpers, `recover` param)
- **CLI entry** (modified) — `scripts/openup-agent.py` (`--no-recover`)
- **engine tests** (modified) — `scripts/tests/test_openup_agent_cycle.py`
- **board / session / views / gates scripts** (read-only, composed) — incl.
  `scripts/openup-spec-scenarios.py` (new composition target)
- **docs** (modified) — `docs-eng-process/reference-driver.md`,
  `docs-eng-process/script-cli-reference.md`

## Approach

Extend `run_cycle`'s decision dispatch with a bounded recovery loop: on
`plan-iteration`/`noop` (recovery on) first close satisfied-but-active lanes
(Case B — pure composition of git + sync-status, mirroring the T-089
completion helpers), re-resolve; on a persisting `plan-iteration`, author the
named work item's spec as one synthetic judgment step (Case A — reusing
`run_judgment_step` verbatim with an `analyst` hat and a spec-contract
instruction), gate it with the *existing* validators, commit, re-resolve once,
and fall through to the normal pick path. Everything else — executor,
completion, exits — is untouched T-089 code.

## Structure

**Add:** *(nothing — no new files)*

**Modify:**
- `scripts/openup_agent/cycle.py` — recovery orchestration + `recover` param
- `scripts/openup-agent.py` — `--no-recover` flag
- `scripts/tests/test_openup_agent_cycle.py` — recovery test classes
- `docs-eng-process/reference-driver.md` — recovery section under the cycle
  engine; exit-semantics update
- `docs-eng-process/script-cli-reference.md` — `cycle` signature update

**Do not touch:**
- `scripts/openup-board.py` / `openup-session.py` / `sync-status.py` /
  `openup-spec-scenarios.py` — composed, never modified; a gap found there is
  its own task
- `scripts/openup-agent-bench.py` + `scripts/bench-scenarios/` — planning
  benchmarks belong to T-090
- `docs-eng-process/procedures/` — the pack's ceremony/judgment split is T-091
- `scripts/process-manifest.txt` — `cycle.py` already ships; no new files

## Operations

- [x] Implement Case B unclosed-lane reconcile in `cycle.py` (satisfied-status
      active-folder scan on plan-iteration/noop, archive + commit + fail-open
      sync + trunk merge per assumption, re-resolve) with hermetic tests
      incl. zero-LLM and on-trunk variants (Req 1)
- [x] Implement Case A missing-spec recovery (synthetic analyst box through
      `run_judgment_step`, spec-contract instruction builder, check-docs +
      spec-scenarios gating, spec commit, single bounded re-resolve →
      same-cycle pick) with hermetic tests incl. no-spec failure and
      non-advancing exit 7 (Req 2, 3, 4)
- [x] Wire `recover` default-on through `run_cycle` + `--no-recover` CLI flag;
      prove opt-out byte-equivalence and non-recovery-path invariance; run the
      full driver+bench+cycle suites unmodified (Req 5, 6)
- [ ] (analyst) Document recovery mode (both cases, flag, merge rule, exit
      semantics) in `reference-driver.md` + `script-cli-reference.md`
- [ ] (tester) Run full suites + `openup-spec-scenarios.py check` on this spec
      + `check-docs.py` + `openup-fence.py check --base harness-optional`;
      re-run the my-product manual scenario expectation against the fixture
      tests; record results in `docs/changes/T-092/design.md`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/parallel-lanes.md` — lane surface / derived-views rules the
  closure ceremony must respect
- `docs-eng-process/model-tiers.md` — sub-run tier stays tier-map-resolved

## Safeguards

- **T-089 invariance.** With `recover=False`, behavior is byte-equivalent to
  T-089 on every decision path; the pre-existing suites pass unmodified.
- **No silent destructive git.** Recovery never force-pushes, resets, or
  deletes branches; a Case B merge conflict aborts typed (exit 8) with the
  branch intact.
- **Compose, never reimplement** (T-089 no-go zone) — validators, board,
  session, views are subprocess calls only.
- **One recovery round** per case per invocation — a non-advancing decision
  exits 7, never loops.
- **Stdlib-only** (T-072 invariant).
- **Reversibility.** `--no-recover` is the kill-switch; no config or pack
  change to unwind.

## Success Measures

We expect **an end-to-end `cycle` loop on a fresh bootstrapped project (the
my-product shape) to reach its first `OPENUP-NEXT: ADVANCED` without human
intervention** — i.e. the `plan-iteration` stall observed live on 2026-07-13
disappears — **on the first post-merge my-product retest / owner live batch**,
with the recovery round adding **≤1 bounded sub-run (≤ step cap iterations)**
over the T-089 baseline, read from the driver's stderr decision log and the
`OPENUP_AGENT_USAGE_LOG` call count. Read-back: recorded in
`docs/changes/T-092/design.md` after that retest (owner-side; this sandbox has
no endpoint — T-080/T-086/T-089 precedent).

## Rollout

Not config-flagged — **the `--no-recover` CLI flag is the kill-switch** (per
invocation, no state to unwind; in-flight lanes are unaffected since recovery
runs only before a lane is claimed). Default is recovery **on** because the
stalled loop is the observed failure mode (my-product live test); callers that
key on the bare exit 7 opt out explicitly. Permanent option, not temporary
debt → no flag-removal follow-up.

## Verification

- `python3 -m unittest scripts.tests.test_openup_agent_cycle
  scripts.tests.test_openup_agent scripts.tests.test_openup_agent_tools
  scripts.tests.test_openup_agent_bench` — all green
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-092/plan.md` — exit 0
- `python3 scripts/check-docs.py` — exit 0
- `python3 scripts/openup-fence.py check --base harness-optional` — exit 0
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` —
  every criterion must be ✅ or have a clear gap call-out.

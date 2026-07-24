# Iteration 86 Retrospective

## Iteration Overview

- **Covers**: iterations 78–86 (the cadence window since the iteration-77 retro) plus two in-session quick-track dogfooding fixes (T-125, T-126)
- **Date range**: 2026-07-15 → 2026-07-24
- **Phase**: Construction
- **Integration branch**: `harness-optional`
- **Participants**: solo agent (roles assumed as needed), owner as decision-point + endpoint operator
- **Trigger**: retro-cadence counter reached 5/5 (T-122, T-123, T-124, T-125, T-126)

## Summary

Two threads closed in this window. The **planned** thread finished the
T-120→T-123 orchestration-economics program and the T-124 lean-authoring
convergence fix — all standard-track, all merged to `harness-optional`,
all with green suites and clean fences. The **unplanned** thread was two
framework dogfooding bugs surfaced from a consuming project (kaze-webapp) and
fixed as quick tasks in this session: the on-stop commit loop (T-125) and the
sync-from-framework false self-detection (T-126).

The salient insight: both T-125 and T-126 were **invisible in the framework
repo itself** because this repo gitignores all of `.claude/`, and T-126's
marker bug only manifests in a repo that carries a stale `.claude-templates/`
tree. They were only observable through a real consumer. Our test surface
proved a fix once written, but nothing in the framework repo would have
*surfaced* either bug without an external consumer exercising the install.

## What Went Well

- **Process:** the quick-track path handled both dogfooding fixes end-to-end
  (state → fix → test → gates → archive) without ceremony, and
  `/openup-complete-task` merged both cleanly into `harness-optional` following
  the established local `--no-ff` integration pattern.
- **Technical:** each fix shipped with hermetic regression tests that pin the
  exact bug (bypass-log exempt + sweep; consumer-with-stale-tree not
  misdetected + framework still self-aborts). 48 tests green on the integrated
  branch.
- **Safety loop worked:** the automated security review caught a real command-
  injection in T-125's own sweep-commit change (naive `f'"{p}"'` over a
  git-porcelain path); fixed with `shlex.quote` + `--` guard before merge.
- **Rebase-then-merge on the experiment branch** stayed conflict-free because
  the two lanes touched disjoint surfaces; `.claude/` mirror was re-synced
  after the template hook change so the sync-check hook stayed green.

## What to Improve

- **Framework bugs hide from the framework repo.** `.claude/` is gitignored
  here, so any defect in a *tracked-in-consumers* path (bypass-log,
  `.claude-templates/` detection) can't be reproduced locally. We rely on a
  human noticing it in a downstream project.
- **Detection markers keyed on distributed artifacts.** T-126's root cause was
  a "am I the framework?" check keyed on `docs-eng-process/.claude-templates/`,
  which ships to consumers. The class of bug — *identity check on a
  non-exclusive marker* — may exist elsewhere.
- **Success measures for T-120/T-123 remain unread** — they depend on a live
  bench batch on the owner's endpoint, which is intermittently reachable
  (same blocker as the T-107 gate). The measures are write-only until a stable
  endpoint run happens.

## Measure Read-Back

| Task | Expectation | Actual | Verdict |
|---|---|---|---|
| T-124 | Inception use-case sub-run converges (turns 28+→low, zero post-write re-reads) on the weak model | Live: use-case 6 turns, 0 reads/globs/re-reads, DONE emitted | **met** |
| T-120 | Sub-runs stop `read_file`-ing inlined plan/vision; bench median ≤3 turns/sub-run | Instrumentation (OPENUP_AGENT_DEBUG_LOG/USAGE_LOG) exists; no number yet | **can't tell** — pending owner bench batch on a stable endpoint |
| T-123 | Dirty-aware gating cuts redundant `check-docs` scans; cycle-log gate lines unchanged | Instrumentation (cycle-log gate lines) exists; no batch number yet | **can't tell** — pending T-080 owner batch |
| T-122 | n/a — argued (internal process-gate correctness sweep) | — | n/a |
| T-121 | n/a — bug sweep, test-covered | — | n/a |

**Product-manager re-rank:** no re-rank. The only *met* measure (T-124)
confirms the lean-authoring direction; the two *can't-tell* verdicts are
blocked on endpoint availability, not on evidence against the current order.
The T-107 gate (≥80% / 5-run batch on a stable endpoint) remains the pending
value checkpoint and already sits where the order expects it.

## Action Items

| # | Action | Owner | Priority | Due |
|---|---|---|---|---|
| 1 | Add a lightweight "consumer smoke" check that exercises the install path (sync-from-framework detection + a tracked bypass-log dirty-stop) against a throwaway consumer fixture, so framework-only-invisible bugs surface in CI rather than in a downstream repo | framework maintainer | high | next iteration |
| 2 | Audit remaining "am I the framework repo?" / role-identity checks for markers keyed on distributed artifacts (`.claude-templates/`, `.claude/`); switch any to a framework-exclusive marker | framework maintainer | medium | next iteration |
| 3 | Run the T-120/T-123 success-measure read-back when the owner endpoint is next stable (folds into the T-107 gate batch) | owner | medium | when endpoint stable |
| 4 | Commit the kaze-webapp `sync-from-framework.sh` bump (left uncommitted for its lead) | kaze lead | low | their schedule |

## Metrics

- **Commits in window** (2026-07-15 → 2026-07-24): 94 (includes `[openup-skip]` process/audit shards)
- **Tasks completed**: 7 delivery tasks — T-118/T-119 (lean-authoring), T-120→T-124 (program), plus quick fixes T-125, T-126
- **Completion rate**: 100% of planned window tasks + 2 unplanned dogfooding fixes
- **Test posture**: 48 green on the integrated branch for the two in-session fixes; standard-track tasks reported full-suite green at their own completion

## Next Iteration Considerations

- **Carry forward:** T-107 gate still blocked on a stable-endpoint 5-run batch; the T-120/T-123 read-backs ride that same batch.
- **Change:** stand up the consumer-smoke check (action 1) — this window produced two bugs that only a consumer could reveal; that gap is the highest-leverage process fix.
- **Risk to monitor:** identity/detection checks keyed on distributed markers (action 2) — one instance (T-126) is fixed; the pattern may recur.

---
id: T-079
title: Parallel Construction iterations (non-colliding clusters)
status: done   # proposed → ready → in-progress → done → verified
priority: medium   # critical | high | medium | low
estimate: 2-3 sessions
plan: docs/explorations/2026-07-13-phase-aware-loop-redesign.md
depends-on: [T-077]
blocks: []
touches:
  - scripts/openup-board.py
  - docs-eng-process/procedures/openup-start-iteration.md
  - docs-eng-process/parallel-lanes.md
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/.claude-templates/skills/openup-start-iteration/
  - .claude/skills/openup-start-iteration/
  - docs/changes/
  - tests/
last-synced: ""
---

# T-079 — Parallel Construction iterations (non-colliding clusters)

## Story

> **As** an agent (or human) driving the OpenUP loop through a Construction phase
> with several low-dependency features queued
> **I want** Plan Iteration to partition the committed work items into
> **non-colliding clusters** and mint **one named/numbered iteration per cluster**
> — each cluster's task ids prefixed by its own iteration id — so N iterations
> whose `touches` and dependencies are disjoint can run **concurrently**
> **So that** Construction wall-clock compresses without a human hand-wiring the
> parallelism, and work from concurrent iterations stays trivially attributable
> to its iteration and can never id-collide.

INVEST — ✅ Independent (builds only on delivered T-077; nothing waits on it — last program slice) · ✅ Negotiable · ✅ Valuable (parallel Construction throughput) · ✅ Estimable · ✅ Small (one pure partition function + one Plan-Iteration wiring change + a worktree-isolation guarantee) · ✅ Testable (hermetic partition + clustering fixtures)

## Analysis Context

- **Fifth and final slice of the phase-aware-loop program** (§3.6, §5 of
  `docs/explorations/2026-07-13-phase-aware-loop-redesign.md`). T-077 made
  `/openup-start-iteration` real **Plan Iteration** — it commits a set of work
  items to **one** named iteration (`C3`), allocates their ids under that prefix
  (`C3-001…` via `openup-claims.py reserve-id --prefix`), and works them
  sequentially through the board's **iteration-scoped `pick`**. T-078 added the
  Assess-Results convergence step and the milestone gate. This task **lifts the
  existing lane-collision machinery one level**: instead of one iteration per
  plan, partition the committed work items into **non-colliding clusters** and
  mint **one iteration per cluster**, so disjoint clusters run concurrently.
- **Domain.** The OpenUP three-layer state machine (§1 of the exploration). The
  **micro-increment layer** (lanes / leases / write-fence / worktrees) is reused
  unchanged — its collision rule (`claims.touches_overlap`) is the exact
  primitive the partitioner is built from. This task operates on the **iteration
  lifecycle** (Plan Iteration), grouping work items into concurrently-runnable
  iterations.
- **What T-077 already delivered (do NOT re-spec).**
  - `openup-process-map.py mint-iteration-id <phase>` — a stable
    `<letter><ordinal>` id (`C3`), **repo-monotonic** (scans used ids, returns
    the next). Calling it N times in a row without persisting a lane yields the
    **same** id each time — the partitioner must mint distinct ids for its N
    clusters (see Approach).
  - `openup-claims.py reserve-id --prefix "${ITER}-" --pad 3` — allocates
    `C3-001`, `C3-002`, … under an iteration prefix (collision-free ids).
  - `/openup-start-iteration` §0b Plan Iteration — derives phase, mints **one**
    iteration id, chooses objectives, generates one lane per activity, authors
    the iteration-plan instance (the loop contract), starts the first lane.
  - `openup-board.py` collision + parallelism primitives: `claims.touches_overlap`
    (prefix-overlap test), `is_pickable` (READY + deps-ok + collision-free),
    `top-n` (greedy mutually-collision-free selection), and — critically —
    `_active_iteration_prefix`, which **already returns `None` (no pick-scoping)
    when several iteration prefixes are live**, with the inline note
    "*(parallel iterations — T-079)*". **So pick-time parallelism already works**:
    once two lanes from two different iteration prefixes hold live leases, the
    board picks the top collision-free lane across both. This task supplies the
    missing **front half** — the planner that *creates* those disjoint
    iterations.
- **What is genuinely new here.**
  1. A pure **partitioner**: group a set of work items into the coarsest set of
     clusters such that any two items sharing a `touches` prefix-overlap **or** a
     dependency land in the **same** cluster — i.e. connected components over the
     collision-∪-dependency graph. Distinct components are guaranteed
     disjoint-`touches` and cross-dependency-free ⇒ safe to run concurrently.
  2. **Plan Iteration mints one iteration per cluster** (not one per plan),
     allocating each cluster's ids under its **own** prefix.
  3. **Worktree-per-lane isolation** made an explicit guarantee for the
     concurrent case (live-run finding **F5**): two lanes from different clusters
     never share a worktree.
- **Scope boundary (explicit).** This task does **not** change the
  micro-increment layer, the board's pick/collision code (reused as-is), the
  Assess-Results / milestone paths (T-078), or `resolve`'s decision precedence.
  Planning is where clusters are formed; the board already consumes them.
- **Definition of done.** `openup-board.py partition` returns the
  connected-component clustering of a set of work items (pure, read-only, exit 0);
  `/openup-start-iteration` §0b, when it generates ≥2 work items, partitions them
  and mints one iteration per cluster (degenerating to today's single-iteration
  behavior when everything is one cluster); the worktree-per-lane isolation
  guarantee for concurrent clusters is documented and asserted; all gated by
  hermetic tests; fence green against `--base harness-optional`.

> **Assumption:** the partitioner lives as a new **read-only `partition`
> subcommand in `openup-board.py`** (it owns the collision primitive and
> frontmatter parsing), not a new script — mirrors `top-n`. *(Vetoable at review.)*
> **Assumption:** two work items are in the same cluster iff their `touches`
> prefix-overlap **or** either lists the other in `depends-on` (a dependency
> forbids concurrency ⇒ same cluster, run sequentially by the iteration-scoped
> pick). Clustering is the **connected components** of that undirected graph;
> "use-case dependencies" (roadmap phrasing) are read from the change-folder
> `depends-on` frontmatter. *(Vetoable at review.)*
> **Assumption:** when partition yields a **single** cluster (the common case,
> and always for the `quick` archetype's single work item), Plan Iteration
> behaves **exactly** as T-077 today — one iteration, one prefix. Parallelism is
> opt-in-by-structure: it appears only when the work is genuinely disjoint.
> *(Vetoable at review — this is the efficiency guardrail.)*
> **Assumption:** minting **distinct** ids for N clusters uses a stable rule that
> does not depend on lanes being persisted between mints — derive `C3, C4, …`
> from the base `mint-iteration-id` result by offsetting per cluster index (see
> Approach), so the partitioner is deterministic and hermetically testable.
> *(Vetoable at review.)*

## Requirements

1. **`openup-board.py partition` clusters work items into non-colliding groups.**
   A new read-only subcommand: given a set of work-item change folders (by id, or
   defaulting to the READY + proposed lanes of a named iteration), it reads each
   one's `touches` and `depends-on` and returns the **connected components** of
   the graph whose edges join any two items that `touches`-overlap or depend on
   one another. Output is a stable JSON array of clusters (each an ordered list of
   work-item ids); the call is pure (no `write_board`, no reap) and exits 0.
   - **Given** three work items where A and B share a `touches` prefix and C is
     disjoint from both with no dependencies **When** `openup-board.py partition`
     runs over them **Then** it returns two clusters `[[A, B], [C]]`.
   - **Given** two work items with disjoint `touches` but B `depends-on` A **When**
     `partition` runs **Then** it returns one cluster `[[A, B]]` (a dependency
     forbids concurrency).
   - **Given** a single work item **When** `partition` runs **Then** it returns one
     cluster `[[A]]` — the degenerate case Plan Iteration treats as today.

2. **Clusters are deterministic and order-stable.** The partition of a fixed input
   is identical across runs and independent of input ordering: clusters are
   emitted in ascending order of their lowest-ranked member (board priority /
   id order), and members within a cluster in that same order. No `Date.now()` /
   randomness.
   - **Given** the same set of work items presented in two different input orders
     **When** `partition` runs on each **Then** the two outputs are byte-identical.

3. **Plan Iteration mints one named iteration per cluster.** `/openup-start-iteration`
   §0b, after generating the iteration's candidate work items (step 6) and when
   there are **≥2** of them, calls `partition`, and for **each** returned cluster:
   mints a **distinct** iteration id (`C3`, `C4`, …), allocates that cluster's
   work-item ids under its own prefix (`C3-001…`, `C4-001…`), and authors **one
   iteration-plan instance per cluster** (each the loop contract for its
   iteration). It then starts the **first** lane of the **first** cluster through
   the single-lane flow; every other lane — in this cluster and the others — is a
   READY change folder the board picks next.
   - **Given** a Plan-Iteration run whose generated work items partition into two
     disjoint clusters **When** §0b completes **Then** two iteration ids are minted
     (`C3`, `C4`), each cluster's ids carry its own prefix, and two iteration-plan
     instances exist.
   - **Given** a Plan-Iteration run whose generated work items form a single
     cluster (all collide/depend, or there is only one) **When** §0b completes
     **Then** exactly one iteration is minted — behavior identical to T-077.

4. **The board runs disjoint clusters concurrently with no further change.** Once
   lanes from two different minted iterations hold live leases, `pick` selects the
   top collision-free lane across both (the existing `_active_iteration_prefix`
   → `None` → unscoped path). No new `resolve`/`pick` code is required; a test
   pins this behavior for the two-iteration case so a future refactor cannot
   silently re-scope it.
   - **Given** live leases on `C3-001` and `C4-001` (disjoint `touches`) **When**
     `openup-board.py resolve` / `pick` runs **Then** it is unscoped and returns
     the top collision-free pickable lane across both iterations.

5. **Worktree-per-lane isolation for concurrent clusters (live-run F5).** Each
   started lane runs in its **own** git worktree (as `openup-session.py begin`
   already creates per branch); the guarantee that two concurrently-active lanes
   from different clusters never share a worktree is **documented** in
   `parallel-lanes.md` and **asserted** by a test (two begins on distinct
   cluster lanes resolve to distinct worktree paths).
   - **Given** two lanes from different clusters begun concurrently **When** their
     sessions are active **Then** they occupy two distinct worktree paths (no
     shared checkout), so their edits cannot interleave on disk.

6. **Every new/changed path is covered by hermetic tests.** Add tests for
   `partition` (the three clustering shapes + order-stability), the two-iteration
   unscoped-pick behavior, and the worktree-distinctness assertion. The existing
   suite stays green.
   - **Given** the new test module **When** the suite runs **Then** all partition,
     concurrency, and isolation assertions pass and no prior test regresses.

## Behavior Delta

How this task changes existing behavior. The affected artifacts are **process
tooling** (a script subcommand + the neutral procedure pack + process docs), not
Ring-1 `docs/product/` use cases — this framework repo's "product" is the process
itself, whose spec lives in the procedure pack and the exploration.

**Added** — behavior that did not exist before:
- `openup-board.py partition` — connected-component clustering of work items.
- One-iteration-per-cluster minting in `/openup-start-iteration` §0b.
- A documented + tested worktree-per-lane isolation guarantee for concurrent
  clusters.

**Modified** — behavior that changes; cite the process-spec source:
- `/openup-start-iteration` §0b Plan Iteration —
  `docs-eng-process/procedures/openup-start-iteration.md` (step 6/7: partition the
  generated work items and mint one iteration per cluster instead of one per plan;
  degenerates to today when there is a single cluster).

**Removed** — none. The single-cluster path is exactly T-077's behavior; the board
pick/collision code is reused unchanged.

## Success Measures

We expect the **number of Construction iterations that can be in flight
concurrently for a batch of disjoint-`touches` work items** to move from **1
(today Plan Iteration commits everything to one sequential iteration)** to **N
(one per non-colliding cluster)**. Instrumentation: the partition fixture tests
(a batch that provably splits into ≥2 clusters), plus a live-run log line showing
two iteration prefixes (`C3-*`, `C4-*`) holding live leases and the board picking
across both. Read-back: the program's next live-run feedback pass on this repo or
a consuming project — Construction wall-clock for a disjoint batch drops toward
the slowest single cluster rather than the sum.

## Rollout

**Flagged?** No. This is internal process tooling read at invocation time:
`openup-board.py partition` is a new read-only subcommand (absent code cannot
misfire), and the Plan-Iteration change is **inert unless the generated work
items are genuinely disjoint** — a single-cluster batch (every existing flow, and
always the `quick` archetype) mints exactly one iteration, identical to T-077. So
there is no runtime surface a flag would protect and no behavior change for
non-parallel work; the capability reaches users on the next framework sync / tag.
`n/a — additive read-only subcommand; single-cluster path unchanged.`

## Entities

- **`openup-board.py partition`** (new) — `scripts/openup-board.py`; the clustering
  subcommand, built on `claims.touches_overlap`.
- **`claims.touches_overlap` / `is_pickable` / `_active_iteration_prefix`**
  (read-only, reused) — `scripts/openup-board.py`, `scripts/openup-claims.py`; the
  collision + parallelism primitives (T-077).
- **`openup-process-map.py mint-iteration-id`** (read-only, reused) — the per-phase
  iteration id source; offset per cluster for distinct ids.
- **`openup-claims.py reserve-id --prefix`** (reused) — per-iteration id allocation.
- **Iteration-plan instance** (authored per cluster) — the loop contract; one per
  minted iteration.
- **Plan Iteration procedure** (modified) —
  `docs-eng-process/procedures/openup-start-iteration.md` §0b.
- **`parallel-lanes.md`** (modified) — documents the worktree-per-lane isolation
  guarantee for the concurrent-cluster case.

## Approach

Reuse the collision primitive; add only the graph on top of it. The partitioner
is the connected components of the undirected graph whose nodes are the candidate
work items and whose edges join any pair that either `touches`-overlap
(`claims.touches_overlap`, the *exact* rule the write-fence and `top-n` already
use) or stand in a `depends-on` relation. Connected components are, by
construction, mutually **disjoint in `touches` and dependency-free across
components** — precisely the property that makes them safe to run as concurrent
iterations. A single component (the common case) degenerates to today's one
iteration, which is the efficiency guardrail: parallelism is *discovered from the
structure of the work*, never forced.

For distinct iteration ids, `mint-iteration-id` is repo-monotonic and returns the
same id until a lane persists it, so N unpersisted mints would collide. Instead,
mint the base id once (`C3`) and derive the cluster ids by offsetting the ordinal
by the cluster index (`C3`, `C4`, … for Construction) — a deterministic,
persistence-independent rule that keeps every cluster's id stable and hermetically
testable, and reuses the existing `<letter><ordinal>` scheme. Each cluster then
allocates its work-item ids under its own prefix via the unchanged
`reserve-id --prefix`, and gets its own iteration-plan instance. The board needs
no change: it already un-scopes `pick` when several iteration prefixes are live,
so the clusters run concurrently the moment their first lanes are begun. Keep the
drivers dumb and the parallelism derived — the same design law as the rest of the
program.

## Structure

**Add:**
- `scripts/openup-board.py` — `partition` subcommand (new `cmd_partition` +
  argparse wiring + a pure `partition_workitems(root, ids)` helper).
- `tests/` — hermetic tests for `partition` (three clustering shapes +
  order-stability), the two-iteration unscoped-pick behavior, and worktree
  distinctness.

**Modify:**
- `docs-eng-process/procedures/openup-start-iteration.md` — §0b step 6/7: partition
  the generated work items and mint one iteration per cluster (single-cluster path
  = T-077 unchanged).
- `docs-eng-process/parallel-lanes.md` — document the worktree-per-lane isolation
  guarantee for concurrent clusters + the partition/one-iteration-per-cluster model.
- `docs-eng-process/script-cli-reference.md` — register the `partition` subcommand
  signature (avoid `--help` round-trips).

**Do not touch:**
- The micro-increment layer — `openup-claims.py`, the write-fence, leases,
  worktree creation (reused unchanged; the isolation guarantee is *documented +
  tested*, not re-implemented).
- The board's `resolve`/`pick`/collision code — reused as-is; Requirement 4 pins
  the existing unscoped-parallel behavior with a test, it does not change it.
- The Assess-Results / milestone paths (T-078) — out of scope.
- `.claude/skills/` mirror — regenerated by `render-skills-mirror.py`; edit the
  pack, not the mirror.

## Operations

- [x] Add a pure `partition_workitems(root, ids)` helper + `cmd_partition` +
  argparse wiring to `scripts/openup-board.py` (connected components over
  `touches`-overlap ∪ `depends-on`; deterministic, order-stable output), read-only
  and exit 0.
- [x] Author hermetic tests: the three clustering shapes (disjoint→2, overlap→1,
  dependency→1), single-item→1, order-stability (Req 2), the two-iteration
  unscoped-pick behavior (Req 4), and worktree distinctness (Req 5).
- [x] Update `docs-eng-process/procedures/openup-start-iteration.md` §0b (step 6/7)
  — partition the generated work items and mint one iteration per cluster via the
  offset-`mint-iteration-id` rule + `reserve-id --prefix`; author one iteration-plan
  instance per cluster; single-cluster path stays identical to T-077.
- [x] Document the worktree-per-lane isolation guarantee + the
  one-iteration-per-cluster model in `docs-eng-process/parallel-lanes.md`.
- [x] Register the `partition` subcommand in
  `docs-eng-process/script-cli-reference.md`.
- [x] Regenerate the skills mirror (`render-skills-mirror.py --write`) +
  `sync-templates-to-claude.sh`.
- [x] (tester) Run the full suite + `check-docs.py`(+`--coverage`) +
  `openup-fence.py check --base harness-optional`; confirm green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.).
- `.claude/CLAUDE.openup.md` — derive-don't-author, edit-the-pack, stay-in-lane.
- `docs-eng-process/model-tiers.md` — procedure `tier:` frontmatter (do not
  override in prose).

## Safeguards

- **Reuse the collision primitive; do not fork it.** The partitioner is built on
  the *same* `claims.touches_overlap` the write-fence enforces — clusters cannot
  disagree with the fence about what collides.
- **Derive parallelism, never force it.** N iterations appear only when the work
  is genuinely disjoint (≥2 connected components); a single component is one
  iteration, exactly T-077. The `quick` archetype (single work item) is always one
  cluster — no new ceremony, no new token cost.
- **`partition` is read-only.** No `write_board`, no reap, no lease mutation; exit
  0 always. Planning forms clusters; the unchanged board consumes them.
- **Reversibility.** Purely additive: a new read-only subcommand + a
  single-cluster-degenerate planning branch. Nothing existing changes shape.
- **No-go zones.** The micro-increment layer (lanes/leases/fence/worktree
  creation) and the board's pick/collision/resolve code must not change.
- **Base is `harness-optional`.** Branch off and fence against it
  (`openup-fence.py check --base harness-optional`); do not run `complete-task`
  verbatim (it hardcodes `main`).

## Verification

- `python3 scripts/openup-board.py partition <ids…>` returns `[[A,B],[C]]` for the
  disjoint-plus-overlap fixture, `[[A,B]]` for the dependency fixture, `[[A]]` for
  a single item, and byte-identical output under reordered input.
- With live leases on two disjoint cluster lanes, `openup-board.py resolve`/`pick`
  is unscoped and returns the top collision-free lane across both iterations.
- Two lanes from different clusters begun via `openup-session.py begin` resolve to
  distinct worktree paths.
- Full test suite + `check-docs.py`(+`--coverage`) green; `openup-fence.py check
  --base harness-optional` green.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-079/plan.md`
  exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

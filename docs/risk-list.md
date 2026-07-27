---
title: Risk List
project: open-up-for-ai-agents
status: active
last-updated: 2026-07-27
owner: framework maintainer
authored-by: T-158
---

# Risk List

Ranked by exposure (probability × impact), highest first. Each risk names the
**evidence** it was identified from — a risk with no evidence is a worry, not a
risk, and belongs in a retrospective's *What to Improve* instead.

Instantiated by **T-158** (2026-07-27), closing carried action item `77.5`
(*"instantiate `docs/risk-list.md` or treat its absence as `n/a`"*, carried 26
iterations from iteration-77). Owner decision: instantiate — five live documents
(`getting-started.md`, `QUICK-REFERENCE.md`, `skills-guide.md`, `USER-GUIDE.md`,
and the `/openup-retrospective` skill) already referenced this path as though the
file existed.

> **Scope note.** `risk-list` is not one of the v1 spine work-product types
> (`vision · requirement · work-item · iteration-plan · use-case · test-case ·
> decision`), so this file is deliberately **untyped** and `scripts/check-docs.py`
> skips it. Labelling it with a spine type purely to attract validation would
> misdescribe it — see `docs-eng-process/doc-frontmatter.md`.

## Risks

| # | Risk | Prob. | Impact | Exposure | Owner |
|---|---|---|---|---|---|
| R1 | **No external consumer validates the framework's value.** The process machinery is designed, built and graded entirely by its own maintainer against its own repo. | high | high | **critical** | product-manager |
| R2 | **Framework-only-invisible defects reach downstream repos.** A change correct in this repo is broken in any consumer checkout until a sync runs. | medium | high | **high** | framework maintainer |
| R3 | **Ceremony outgrows the value it protects.** Each defect adds a gate; gates are never removed, so per-lane overhead grows monotonically. | medium | high | **high** | product-manager |
| R4 | **Debt items rot in bookkeeping rather than being decided.** Hand-written cross-references between items go stale within hours. | high | medium | **high** | framework maintainer |
| R5 | **Stale leases block delivery.** A completed task's claim survives its branch and worktree and silently blocks every lane sharing its surface. | high | medium | **high** | framework maintainer |
| R6 | **Measurement blocked on an unstable endpoint.** Several success measures need a reachable model endpoint the sandbox cannot always reach. | medium | medium | medium | owner |
| R7 | **Parallel lanes conflict in the derived shared views.** Every lane writes `docs/roadmap.md` and `docs/project-status.md`. | medium | low | low | framework maintainer |

## Detail

### R1 — No external consumer validates value

**Evidence.** The iteration-103 retrospective records it as a standing "risk to
monitor": *"still no external consumer validating value — fourteen consecutive"*
iterations. The two sibling repos (`kaze-webapp`, `cqecho-app`) are evidence-only
and update on their own leads' schedules.

**Why it matters.** Every other risk here is a *quality* risk about a thing that
may not be wanted. A framework graded only by its author converges on internal
consistency, which is not the same as usefulness.

**Mitigation.** Treat downstream read-backs as the primary evidence channel, not
a nice-to-have: T-152 already forces every success measure to name the
environment its number will be read in, and `/openup-complete-task` step 1b
blocks when the instrument does not exist there. **Residual: high** — that makes
measures *answerable*, not answered, and does not create a consumer.

### R2 — Framework-only-invisible defects reach downstream

**Evidence.** T-110 (consumer shipped with no self-updater), T-150 (settings
referencing hook scripts not yet on disk, which locked Bash and Write together in
a live session), T-147 (premise structurally invisible here because this repo
gitignores `/.claude/*`). Three independent occurrences.

**Mitigation.** T-153's `scripts/tests/test_consumer_smoke.py` runs the real
installer into a temp dir and asserts usability properties rather than an
inventory. T-155's `migrate_gitattributes_merge_union()` establishes that
delivery, not just the change, must be shipped. **Residual: medium** — the smoke
test covers the install path, not every downstream divergence.

### R3 — Ceremony outgrows the value it protects

**Evidence.** The graded-track system (`quick`/`standard`/`full`) exists
precisely because this was already felt. Counter-evidence that it is real: a
`full`-track solo task cannot complete at all without a team gate (recorded in
the maintainer's own working notes), and this lane's own completion required a
re-claim after a one-file scope change.

**Mitigation.** Tracks; `/openup-quick-task`; the standing rule that a project
rule may add but never waive a framework criterion. **Residual: high** — nothing
currently *removes* a gate, and there is no measure on total per-lane overhead.
The honest statement is that this risk is monitored, not mitigated.

### R4 — Debt items rot in bookkeeping

**Evidence.** T-154's cancellation note named the wrong four items — claiming two
real closures that were never part of it, and silently dropping `77.5` and `20.2`,
which remained open. `20.2` then survived **83 iterations**. Two of five items
promoted from iteration-98 were false (`A2` obsolete, `A3` wrong).

**Mitigation.** `/openup-retrospective` step 5b (retire carried items against
mechanical checks, strike in place with evidence) and **step 5c**, added by this
task, requiring every newly-authored item to carry a verified premise.
**Residual: medium** — both are graded prose checks, unenforceable by script.

### R5 — Stale leases block delivery

**Evidence.** Observed twice on 2026-07-27 alone: six dead claims (T-090, T-091,
T-096, T-098, T-100, T-103 — all completed, branches and worktrees gone) blocked
T-157 on `docs-eng-process/script-cli-reference.md`; then **T-075's claim
reappeared** with an mtime minutes old but a `claimed_at` of 2026-07-13, carrying
a repo-wide surface (`scripts/`, `docs-eng-process/`, `docs/changes/`, …) that
blocked T-158. The same T-075 claim had already been released once during
T-142/T-143.

**Mitigation.** `openup-board.py refresh` reaps heartbeat-stale claims; `begin`
warns on them. **Residual: high, and the mechanism is not understood** — a claim
file being *rewritten* for a completed task is unexplained, and the reaper
evidently did not catch it. This is the most concrete open defect on this list.

### R6 — Measurement blocked on an unstable endpoint

**Evidence.** Carried item `86.3` (T-120/T-123 read-back) is blocked on owner
endpoint stability; T-107 remains gated on a ≥80%/5-run batch against a stable
endpoint.

**Mitigation.** Prefer measures readable from the repo's own durable trail
(retrospective tables, run logs, `git log`) over measures needing a live model.
T-157's and T-158's measures both follow this. **Residual: medium.**

### R7 — Parallel lanes conflict in the derived views

**Evidence.** The iteration-103 four-PR merge wave: `## Notes` assembled from
whichever copy won, three notes on disk absent from the block, two PRs
`CONFLICTING`.

**Mitigation.** Sharded status notes (T-024), the write-fence, and — since T-157
— `sync-status.py --views-only`, so recovery is possible after a lane completes.
**Residual: low.**

## Retired Risks

None yet. When a risk is retired, strike it **in place** with the evidence that
closed it rather than deleting the row — the same rule the retrospective's
carried-item pass applies (T-141).

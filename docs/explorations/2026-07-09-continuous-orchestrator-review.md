# Exploration: Continuous multi-lane orchestrator — project review, problems, roadmap candidates

**Started:** 2026-07-09
**Question:** What stands between today's machinery (`/openup-next`, `/openup-fan-out`, `openup-loop.sh`) and the target: a **main agent that stays in a loop, dispatching lane subagents that each run `/openup-next` in their own lane, until the roadmap is drained**? And what is broken in the current implementation on the way there?

## Context — what exists today

- **Sequential loop** (T-017, T-059): `/openup-next` runs one cycle with a fixed
  resume → pick → promote precedence and a machine-readable sentinel
  (`OPENUP-NEXT: ADVANCED/DONE`); `scripts/openup-loop.sh` re-invokes it in fresh
  `claude -p` processes with a cycle cap and stall limit.
- **One-wave parallelism** (T-060): `/openup-fan-out` reaps, takes a
  collision-free partition via `openup-board.py top-n`, dispatches one background
  subagent per READY lane, collects sentinels, and **exits**.
- **Claim lifecycle** (T-009 → T-044 → T-060 → T-063): lease in
  `--git-common-dir` (shared across worktrees), remote branch-as-claim
  preflight, `last_heartbeat` stamped at claim, `reap --stale-after 1800`
  (default 30 min), and — since T-063 — auto-reap inside every
  `openup-board.py refresh`, plus atomic `openup-session.py begin|end`.
- **Planned, not yet built** (2026-07-05 efficiency plan): T-064
  (`openup-roadmap.py next|list|get`, deterministic promote selection) and
  T-065 (`openup-board.py resolve|status`, single-call state discovery + a
  no-op pre-check for `openup-loop.sh`).

The gap: nothing loops *and* parallelizes. `openup-loop.sh` and `/loop
/openup-next` are sequential; fan-out is parallel but single-shot. The
orchestrator the user wants has no home yet — and two of the problems below
would corrupt it if it were built today.

## Problems in the current implementation

### P1 — Live lanes get reaped mid-work (critical; blocks the orchestrator)

The heartbeat is stamped **exactly once**, at claim time
(`/openup-start-iteration` / `openup-session.py begin`). Nothing renews it:
no hook, no skill instruction, no wrapper (verified by grep across
`.claude/skills/`, `.claude/scripts/`, `.githooks/`, `scripts/`). The reap TTL
defaults to **1800 s**, and since T-063 the reaper runs inside **every**
`openup-board.py refresh` (default on, `--no-reap` to skip).

Consequence: any lane actively worked for more than ~30 minutes — normal for a
standard-track task — has its lease deleted by the next `board refresh` from
*any* session. Sequential solo use masks this (the one session doesn't refresh
the board mid-work); the target orchestrator triggers it by construction (the
main loop refreshes the board while subagents work). The reaped lane then looks
READY and gets dispatched **a second time**: duplicate work, write collisions
in the same `touches` surface, and a corrupted audit trail. T-060's
backward-compat invariant ("no-heartbeat claims are never reaped") protects
legacy claims, but start-iteration now always stamps a heartbeat, so every new
lane is exposed.

Fix direction: renew the heartbeat on every sanctioned progress event
(Operations box tick / `log-event` / a `session pulse` verb wired into a
PostToolUse or periodic hook inside the lane), so the invariant becomes
"an actively-worked lane is never stale". Raising the TTL alone only widens
the race.

### P2 — Half the roadmap is invisible to status stamping; completed tasks can be re-promoted (high)

`sync-status.py` flips only **table-row** Status cells (`| T-NNN | … |`). The
second sanctioned roadmap shape — manual `## T-NNN:` sections with
`**Status**: pending` — is never touched. Live evidence in this repo right
now: **T-063 was delivered 2026-07-06 (PR #61, archived change folder, status
note, iteration-34 note) yet its roadmap section still reads `pending`**.
T-059/T-060 had the same staleness and needed hand-reconciliation (iteration-33
note called it out explicitly).

This is not cosmetic for an autonomous loop: §1c promote selects "first
pending entry … with **no `docs/changes/<id>/` folder**". Completed changes
archive to `docs/changes/archive/<id>/`, so a completed-but-stale-pending entry
passes the filter and is **re-promotable** — the loop can re-author a spec for
finished work and redo it. T-064's parser will faithfully inherit this
garbage-in unless completion stamping learns both entry shapes (or entries are
normalized to table rows at plan-hook time).

### P3 — Fan-out is one wave, not a drain (high; this is the user's stated goal)

`/openup-fan-out` never re-dispatches: when a lane completes and its dependents
become READY, they sit idle until a human reinvokes; a pending roadmap task
with no change folder never enters the partition at all (fan-out has no promote
phase — `top-n` only sees existing lanes); and there is no
"until `DONE — roadmap exhausted`" stop condition. Wall-clock win today is
capped at one wave of the initially-READY set.

### P4 — Stall detection conflates progress with stalling (medium)

`openup-loop.sh` exits 2 when the same task sends `ADVANCED` `--stall-limit`
(default 3) times in a row. But a legitimate long task worked across sessions
(resume path, handoff exits) produces exactly that signature — the sentinel
carries no exit type (complete-task vs create-handoff) and no progress delta,
so no driver can distinguish "3 more Operations boxes ticked" from "same
question re-asked three times". The skill text even describes stall as
"create-handoff exits N cycles in a row on the same question", which is not
what the script measures. Long tasks get falsely killed; a genuinely spinning
lane that alternates with another task is never caught.

### P5 — `project-status.md` header self-contradicts (medium)

Current header: Iteration 34, **Iteration Goal: T-062**, Status: completed,
**Current Task: T-063**, Started 2026-06-18. Goal, current task, and start date
come from different iterations. The primary "where are we" view answering
inconsistently erodes exactly the trust the derived-view rule is meant to buy,
and it feeds the P2 confusion. Likely a header-derivation gap in
`sync-status.py` (fields sourced from a mix of stale `state.json` and notes)
— worth a failing test first.

### P6 — Parallel completion contention is unmanaged (medium)

Each `/openup-complete-task` does rebase `origin/main` → fence → `sync-status`
→ push (→ optional PR auto-merge, T-057). N lanes finishing together race on
the trunk: the loser must re-rebase and re-run sync-status, nothing orders or
retries this deterministically, and fan-out's summary doesn't track merge
outcome — a lane can report ADVANCED while its completion push actually lost
the race. Fine at N=2 with a human watching; not at N=4 unattended.

### P7 — Headless driver hardening gaps (low)

`openup-loop.sh` invokes bare `claude -p`: no permission-mode /
allowed-tools guidance (a cold headless cycle can wedge forever on a permission
prompt), no per-cycle timeout (a hung cycle blocks the loop indefinitely,
which then interacts with P1 — its lease goes stale and gets reaped while the
process still runs), and no pinned output format for the sentinel grep.

### P8 — Crash recovery is lease-deep only (low; verify)

Reaping frees the **lease**, but the crashed lane's worktree, branch, and
half-ticked boxes remain. The re-claimant path (does `start-iteration` adopt an
existing worktree/branch for the same task, or fail?) is undocumented as an
end-to-end story. Needs a test: kill a lane subagent mid-work → reap →
re-pick → resume from the ticked boxes, asserting no duplicate work and no
wedged worktree.

## Roadmap candidates (for product-manager ordering)

Order below is a *suggested* dependency-respecting sequence, not a value
ranking — value ordering stays with the product-manager role.

1. **R1 — Heartbeat renewal (`session pulse`) + safe-reap invariant.**
   Renew `last_heartbeat` on every sanctioned progress event (box tick,
   `log-event`, or a periodic in-lane hook); document the TTL rationale; add a
   test that an actively-worked lane survives a concurrent
   `board refresh`. *Value*: without it, every parallel driver (fan-out today,
   orchestrator tomorrow) can dispatch the same lane twice. **Prerequisite for
   R4.** (Fixes P1.)
2. **R2 — Roadmap status stamping covers both entry shapes + drift doctor
   check.** Teach `sync-status.py` to stamp `## T-NNN:` sections (or normalize
   them to table rows at plan-hook time — decide once), and add an
   `openup-doctor` check for "archived change folder but roadmap says pending".
   Repair T-063's row as the fixture. *Value*: the autonomous loop stops being
   able to redo finished work; T-064's parser gets clean input. (Fixes P2;
   protects T-064.)
3. **T-064 / T-065 (already planned, keep).** Deterministic promote selection
   and single-call `resolve` are load-bearing for the orchestrator: `resolve`
   is the cheap "anything to do?" tick of the main loop, `roadmap next` is its
   promote step.
4. **R4 — `/openup-drive`: the continuous multi-lane orchestrator** (the
   user-stated goal). Main-session loop:
   `reap → resolve → promote pending roadmap tasks into lanes (serially,
   ID-reserved) → top-n → dispatch one background subagent per lane
   (`/openup-next task_id: <id>`, no harness worktree isolation — T-060
   safeguard) → on each completion, classify sentinel and immediately
   re-enter the loop` — until `resolve` says noop **and** the roadmap has no
   promotable task. Budget rails: `max_lanes` per wave, `max_cycles` total,
   per-lane crash accounting, suspended-lanes report (input-requests pending) in
   the final summary instead of stopping the whole drive. Depends on R1, R2,
   T-064, T-065. (Fixes P3.)
5. **R5 — Sentinel v2: structured exit line + progress-aware stall detection.**
   Extend the sentinel to carry exit type and progress
   (e.g. `OPENUP-NEXT: ADVANCED — T-NNN exit=handoff boxes=3/7`), keep the v1
   prefix for backward compat, and rewrite `openup-loop.sh` / fan-out / drive
   stall logic on progress-delta ("no new box ticked in N cycles") instead of
   task-id repetition. (Fixes P4.)
6. **R6 — Completion serialization for parallel lanes.** Codify the
   completion-push protocol (bounded rebase-retry loop, or a completion lock in
   `--git-common-dir` claims style), and make drivers record merge outcome per
   lane. Falsifiable measure: zero lost completions in an N=4 simultaneous
   completion test. (Fixes P6.)
7. **R7 — `project-status.md` header derivation fix.** Failing test
   reproducing the current mixed-iteration header, then fix `sync-status.py`
   field sourcing. Small, restores trust in the primary view. (Fixes P5.)
8. **R8 — Headless driver hardening.** `openup-loop.sh` gains
   `--permission-mode/--allowed-tools` pass-through (documented defaults), a
   per-cycle timeout, and pinned output format; document the cron recipe.
   (Fixes P7; interacts with R1.)
9. **R9 — Crash-recovery end-to-end test.** Scripted kill of a lane mid-work →
   reap → re-pick → resume-from-boxes, asserting worktree adoption and no
   duplicate work. Guards R1 and R4 against regression. (Resolves P8.)
10. **Existing pending items to re-rank alongside these:** the 2026-06-15
    "approve on your phone" plan (suspended lanes matter *more* under a
    continuous drive — the loop should keep draining other lanes while
    questions wait, which R4's suspended-lanes report assumes) and the
    2026-07-09 advisor-consult pilot (unchanged disposition).

## Options Considered (for R4's driver seat)

- **Option A — skill-layer drive loop in the main session** (background
  subagents via the Agent tool, sentinels collected as they return).
  Pro: interactive visibility, immediate re-dispatch on completion, promote
  stays in one place (no parallel spec-authoring races), uses fan-out's proven
  dispatch constraints. Con: main-session context grows with waves; needs a
  compact per-wave summary discipline (the ≤6-bullet rule already exists).
  **Preferred.**
- **Option B — shell-layer parallel driver** (`openup-loop.sh --parallel N`,
  N concurrent `claude -p` workers pulling from `top-n`). Pro: truly cold
  context per cycle, cron-able, no main-session bill. Con: promote must be
  serialized out-of-band; P7's headless gaps become blocking; observability is
  log files. Good second step once A proves the protocol.
- **Option C — wait for T-064/T-065 and keep fan-out one-shot** (human
  reinvokes per wave). Pro: no new surface. Con: doesn't answer the goal;
  dependency waves idle between human ticks.

## Open Questions

- R1 mechanism: hook-based periodic pulse vs. pulse-on-progress-event only?
  (A lane legitimately thinking for 40 min without a tool call is possible;
  hook-based is safer but harness-coupled.)
- R2: stamp both shapes forever, or one-time normalization of section entries
  to table rows (Option-B-lite for the roadmap)? Normalization simplifies
  T-064's parser but touches PM-owned prose.
- R4: should promote author specs for *all* promotable tasks up front per wave,
  or lazily one-per-free-slot? (Up-front risks stale specs if an earlier lane's
  outcome changes scope; lazy keeps fix-spec-first honest.)
- R4 stop semantics: is "roadmap drained" per phase (stop at phase-review
  boundary and surface to the human — matches the §1c rule that phase
  advancement is a product-manager decision) — assumed **yes**.
- R6: is a completion lock over-engineering vs. a bounded retry loop?
  Measure first with the N=4 test before building the lock.

### Product-manager challenge pass

- **Pushback 1 — "build the orchestrator" is not the first shippable.** The
  drive loop without R1 actively *causes* duplicate work (P1 fires by
  construction), and without R2 it can *redo finished tasks* (P2). The value
  order is therefore safety-first even though R4 is the headline ask.
  → **Accepted**: R1 and R2 are sequenced ahead of R4 and named prerequisites;
  each is independently shippable and independently valuable (fan-out today
  already benefits).
- **Pushback 2 — how would we notice R4 paid?** "It loops" is not falsifiable.
  → **Accepted — measures attached**: (a) drain test: a fixture board with 2
  waves of dependent lanes reaches `DONE — roadmap exhausted` with zero human
  invocations after the first; (b) zero duplicate-dispatch events (P1 counter)
  and zero re-promotions of completed tasks (P2 counter) across the run;
  (c) wall-clock ≤ max(lane) per wave + promote overhead, vs. sum(lanes)
  sequential baseline.
- **Pushback 3 — R5/R6/R7/R8 risk becoming a grab-bag.** Each must ride its
  own evidence: R5 only if a real stall false-positive is observed or the
  drive needs exit-type classification (it does — handoff vs complete changes
  re-dispatch behavior); R6 only after the N=4 test shows lost completions;
  R7/R8 are small and evidenced already.
  → **Accepted**: R6 demoted to measure-first; R5 justified by R4's
  classification need, not hypothetical stalls.
- **Complement — the suspended-lane behavior is the hidden product decision.**
  A drive loop that stops on the first human question is barely better than
  sequential; one that keeps draining and batches questions is the actual
  "until finish" promise. This links the dormant "approve on your phone" plan
  into R4's value case rather than leaving it orphaned.
  → **Accepted**: folded into R4's scope (suspended-lanes report) and the
  re-rank note in candidate 10.

## Where this goes next

→ iteration — promote, in order: **R1** (heartbeat renewal + safe-reap
invariant), **R2** (roadmap stamping both shapes + doctor drift check), then
T-064/T-065 as already planned, then **R4** (`/openup-drive` continuous
orchestrator, Option A) with the drain/duplicate/wall-clock measures as
acceptance criteria; R5 rides with R4, R7 is a quick-track candidate anytime,
R6/R9 gated on their tests, R8 when the shell driver is next touched.

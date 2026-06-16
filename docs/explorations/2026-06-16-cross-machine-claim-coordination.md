# Exploration: Cross-machine claim coordination — the git remote as the substrate

**Started:** 2026-06-16
**Question:** When teammates on separate clones run `openup-next` in parallel
with little manual coordination, how can "claiming a task" become visible
*across machines* so two people don't build the same task — using pushed git
state as the only shared medium?

## Context

The local lease (`scripts/openup-claims.py`, T-009) stores claims at
`<git-common-dir>/openup/claims/T-NNN.json` — inside `.git/`, never pushed. It
coordinates **sessions/worktrees of one clone** and nothing more. This boundary
is now documented in
[parallel-lanes.md → Parallelism scope](../../docs-eng-process/parallel-lanes.md)
(T-043).

The gap bit us today: on **TallyFox**, two agents (one local, the path is the
same cross-machine) both fixed T-1102 and opened **two PRs (#462, #463)** for
one task. One had correctly claimed the local lease; the other never did — and
even a perfect local lease would not have helped a *second machine*. Resolution
was manual (merge one PR, close the other). With several teammates about to run
`openup-next` in parallel "without much coordination," PR-time collision is the
default outcome, not the exception.

Builds on
[`2026-06-12-multi-worktree-coordination.md`](2026-06-12-multi-worktree-coordination.md),
which solved the *single-clone* file-conflict half (write-fence + derived
views). This explores the *cross-clone* half it explicitly left open.

## Notes

### The constraint, stated minimally

The whole problem reduces to one precondition:

> Before `openup-next` *starts* a task, it must know whether any other machine
> has already started that same task.

Everything else (ledgers, locks, dispatchers) is just a mechanism for making
that one fact knowable over the remote. So evaluate every option against: **does
it answer "is T-NNN already taken elsewhere?" reliably and cheaply, and what is
the race window between two machines asking at the same instant?**

### What the remote already exposes (no new infra)

Two machines *already* share three signals the moment someone pushes:

1. **Branches** — `fix/T-NNN-*` naming. `git ls-remote --heads origin` /
   `git fetch` surfaces them in one network call.
2. **Change folders** — `origin/main:docs/changes/T-NNN/` (once merged) or on a
   pushed branch.
3. **Roadmap status** — `origin/main:docs/roadmap.md`.

Precedent: `reserve-id` **already** consults `origin/main:docs/roadmap.md` to
avoid ID collisions across stale checkouts (claims.py:364). So remote-aware
preflight is not a new idea in the codebase — it is one already-paved cowpath
that just needs widening from "ID allocation" to "task claiming."

### The atomic primitive that actually exists in git

Git refs support **compare-and-swap on push**. Pushing a ref with an
"expected-absent" precondition is atomic and adjudicated by the *server*:

```bash
# create-if-absent: succeeds for exactly one racer, the rest are rejected
git push origin <sha>:refs/openup/claims/T-1102 \
  --force-with-lease=refs/openup/claims/T-1102:    # empty = must not exist
```

This is the missing piece. A custom refspace `refs/openup/claims/*` is:
- **invisible to normal git** (not a branch, not fetched by default, never on
  `main`, zero working-tree footprint, zero file-merge surface);
- **atomically serialized by origin** — the loser of a race gets a non-fast-
  forward rejection and simply picks the next lane;
- **enumerable in one call**: `git ls-remote origin 'refs/openup/claims/*'`;
- a near-exact **mirror of the existing local design** — `T-NNN.json` under
  `.git/openup/claims/` becomes `refs/openup/claims/T-NNN` on origin. Same
  mental model, lifted from one clone to the shared remote.

Claim metadata (who/when/branch/touches) rides as a tiny commit or blob the ref
points to, fetched only when preflight needs to inspect a live claim.

### Abandonment is genuinely harder cross-machine

The local lease deliberately has **no expiry** (release/`rm` to free) — fine,
because a dead session's worktree is right there to clean up. Cross-machine you
**cannot see if the other machine is alive**: a teammate closes their laptop
mid-task and their claim ref strands the lane forever. So any remote scheme
needs a **TTL / heartbeat** the local one never required:
- the claim commit carries a timestamp; preflight treats a claim older than
  `T` (e.g. 2h with no branch push) as **stale** and eligible for atomic
  takeover (CAS-delete then CAS-create);
- an active lane refreshes (re-pushes) the ref on each `openup-next` cycle.

## Options Considered

- **Option A — Remote ref-lock `refs/openup/claims/*` (atomic CAS push).**
  Race window: ~0 — origin serializes; exactly one racer wins.
  Conflict surface: none (custom refspace, never touches files/branches/main).
  Preflight: `git ls-remote origin 'refs/openup/claims/*'` + inspect; claim via
  create-if-absent push; on rejection, take next lane.
  Recovery: TTL on the claim commit + atomic stale-takeover / `claims gc`.
  Ceremony: one `ls-remote` + one `push` per claim; no PR, no rebase, no
  working-tree change. **Pro:** correct, cheap at runtime, mirrors existing
  design. **Con:** new refspace + GC protocol to build and teach; needs a
  network round-trip at claim time; some hosts restrict custom refs (verify
  GitHub allows `refs/openup/*` push — it does for normal repos).

- **Option B — Branch-as-claim (read existing signals harder).** Preflight does
  `git fetch` then refuses a task that already has a `*/T-NNN-*` branch or a
  `docs/changes/T-NNN/` on origin.
  Race window: real — the gap between *my* fetch and *your* push; two starts
  within that window both see "free."
  Conflict surface: none new (reuses branches/folders).
  Recovery: trivial — the branch *is* the record; delete it to free.
  Ceremony: ~zero — reuses signals lanes already produce; one extra fetch.
  **Pro:** almost no new machinery, ships in an afternoon, captures the common
  case (starts minutes apart). **Con:** does not close the simultaneous-start
  race; advisory, not atomic.

- **Option C — Committed claims ledger (one file, e.g. on an `openup-claims`
  orphan branch).** Everyone appends a claim line and pushes.
  Race window: push-and-rebase loop; non-atomic.
  Conflict surface: **high** — single shared file; needs `merge=union` and even
  then two claims for one task both land (union keeps both). Reintroduces the
  exact shared-file conflict class T-024 spent effort eliminating.
  Recovery: edit/remove a line.
  Ceremony: pull-edit-push per claim. **Rejected** — strictly worse than A on
  conflict surface and worse than B on ceremony.

- **Option D — Roadmap status transition as the claim** (flip T-NNN to
  `in-progress` in `docs/roadmap.md` and push first).
  Conflict surface: **highest** — roadmap is a class-3/4 derived/global-mutable
  file; concurrent edits are precisely what the derived-view discipline forbids.
  **Rejected** on conflict surface alone.

- **Option E — Dispatcher model.** One owner (a human, or a cron on a server)
  runs `openup-next`/the board and assigns lanes; teammates pull their
  assignment and execute.
  Race window: none — a single claimer cannot race itself.
  Conflict surface: none.
  Recovery: dispatcher reassigns.
  Ceremony: organizational, not technical — but **reintroduces the coordinator**
  the user explicitly wants to avoid ("without much coordination"). **Pro:**
  zero new code; robust. **Con:** centralizes; a bottleneck/SPOF; against the
  stated working style. Keep as a fallback org pattern, not the default.

## Open Questions

- How often do simultaneous starts actually happen at this team size? That
  number decides whether B is sufficient or A is warranted (see challenge pass).
- Does the host (GitHub) permit pushing/listing `refs/openup/*` for all
  collaborators, and do branch-protection / ruleset configs interfere? (Spike.)
- TTL value and heartbeat cadence for A — tied to typical task duration; today's
  T-1102 lane ran ~2h.
- Should `reserve-id` and the task-claim share one refspace
  (`refs/openup/claims/ids/*` already exists locally), unifying ID-reservation
  and task-claim under one remote mechanism?
- Offline/airplane work: A needs a network round-trip to claim. What is the
  degraded-mode behavior — block, or claim-locally-and-reconcile-on-push?

### Product-manager challenge pass

*(No `.claude/teammates/product-manager.md` exists — only analyst/architect/
developer/project-manager/scribe/tester. Applied the PM role lens from
CLAUDE.openup.md: owns value ordering; challenges thin value cases with "what
changes for which user, and how would we notice?" Filing the missing-file gap
under "Where this goes next" as a separate quick-task.)*

- **Pushback:** The submitted framing leans toward the heaviest option (atomic
  ref-lock) for a failure that, so far, has happened **once** and was caught and
  fixed at PR time in minutes. "Build a distributed lock" is a large, teachable
  protocol (refspace + TTL + GC + heartbeat + offline mode) whose value is
  unproven at current team size. What changes for which user? Today: a rare
  duplicate, cheaply reversible. We would notice over-engineering if the lock
  protocol generates more support questions and edge-case bugs than the
  duplicates it prevents. → **Accepted into notes:** demote A from "the answer"
  to "the robust fast-follow," gated on measured duplicate frequency.
- **Complement:** The submission missed that the remote is **already**
  consulted (`reserve-id` reads `origin/main:docs/roadmap.md`) and that branches
  + change folders are already cross-machine-visible claim signals. The cheapest
  90% — a remote-aware preflight that *reads* those — was not in the original
  option list. → **Accepted:** added as **Option B (branch-as-claim)** and made
  the recommended first step.
- **Refine:** Narrow "cross-machine coordination" to its falsifiable core:
  *instrument how often two lanes pick the same T-NNN under a fetch-first
  preflight.* Ship B, measure the residual simultaneous-start rate, and build A
  **only if** that rate exceeds a threshold that makes PR-time cleanup more
  expensive than the lock. → **Accepted:** this becomes the iteration's success
  measure.
- Disposition per challenge: all three **accepted into notes**; none rejected.
  The value case for *some* cross-machine preflight holds (parallel work is the
  stated near-term reality); the value case for the *atomic lock specifically*
  is deferred behind a measurement.

## Where this goes next

→ **iteration** — promote to a roadmap entry: **"Remote-aware claim preflight
for `openup-next`."** First iteration ships **Option B (branch-as-claim)**:
`openup-next`/preflight does a shallow `git fetch` and refuses to start a task
that already has a live `*/T-NNN-*` branch or `docs/changes/T-NNN/` on origin,
and emits a duplicate-start counter to the run log. **Option A (atomic
`refs/openup/claims/*` ref-lock)** is a named fast-follow, gated on that counter
showing simultaneous-start duplicates persist. Option E (dispatcher) is the
documented manual fallback in the meantime. Separately, a **`→ quick-task`**
falls out of the challenge pass: create the missing
`.claude/teammates/product-manager.md` so the explore skill's mandated PM pass
has a real file to read (it currently references a non-existent teammate).

# T-009 — Test Notes (test strategy / case catalog)

Status: strategy only. No implementation or test code written yet. Reconciled against the
final PM decisions of 2026-06-11 (claims never expire; manual `rm` only; worktree
default-on; dependency check precedes collision; empty-`touches` is a no-collide foot-gun)
and against the developer's `plan.md`/`design.md` (D1–D6). This file catalogs the test
cases the implementation must satisfy and how each is exercised.

## Scope under test

T-009 = worktree-per-task + lease claims + collision pre-flight (program plan WS5c,
lines 198–216). The headline program acceptance criterion (line 266):

> Two simultaneous sessions on disjoint tasks run in separate worktrees with visible
> claims; claiming an overlapping task is refused with the owning session named.

Mechanisms in scope:
- **Claim leases**: one file per claim at `.git/openup/claims/T-NNN.json` (git common
  dir — shared across worktrees, never committed).
- **Pre-flight collision check**: refuse a claim whose `touches` overlaps a live claim;
  name the owning session. Reuses T-008 D2 path-segment prefix algorithm.
- **Dependency pre-flight**: refuse a claim with unmet `depends_on`.
- **Worktree lifecycle**: `git worktree add ../<repo>-T-NNN` on start; remove on complete.

## Source-of-truth / dependency notes for the tester

- The collision algorithm is **T-008 design.md D2** (path-segment prefix, normalise
  leading `./` and trailing `/`): `docs/changes/` collides with `docs/changes/T-002/`
  and with itself, but NOT with `docs/changesets/`. Every collision case below cites D2.
- The collision *set* is **every live claim file** under `.git/openup/claims/`, with **no
  staleness filter** (T-009 design.md D1/D5). A claim file's mere presence — regardless of
  `claimed_at` age — puts its `touches` in the live set. Tests treat "claim file present"
  as the sole membership predicate.
- **Claims never expire** (D1, resolving program Open Question #2): there is no
  `lease_ttl_hours` field and no staleness evaluation anywhere. `claimed_at` is
  audit/owner-naming only. The **sole** recovery for an abandoned claim is manual `rm
  .git/openup/claims/T-NNN.json` — no `--steal`, no TTL (D2).
- **Dependency check runs before collision** (Q4 resolved): if any `depends-on` is unmet,
  pre-flight refuses with the dep reason and **does not reach** the collision check — a
  dep-blocked task is never collision-evaluated (consistent with T-008 readiness excluding
  BLOCKED tasks).
- **Worktree is default-on** (D6): every iteration gets `../<repo>-T-NNN`; `worktree:
  false` opts out to in-place checkout. Ordering is **worktree first, then claim**; if
  `git worktree add` fails → abort, no claim; if claim write fails after the worktree
  exists → remove the worktree to roll back.

## Test environment matrix

Two ways to exercise claim coordination; most cases pick the cheaper one.

| Mode | What it is | Use for |
|---|---|---|
| **Simulated** | Write/inspect `.git/openup/claims/*.json` directly + invoke the claim/release/pre-flight code path. No second checkout. | Lease lifecycle, atomicity, all collision/dependency refusal logic, edge cases. Fast, scriptable, deterministic. |
| **Real worktree** | Actual `git worktree add` + a second process/session operating from it. | Cross-worktree claim visibility (shared common dir), worktree add/remove, the headline parallel-session scenario. |

Rule of thumb: refusal/lease *logic* is simulated; *worktree existence* and
*cross-checkout visibility* need a real second worktree.

---

## TC catalog

### A. Claim lease lifecycle

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-LEASE-01 | Claim creation writes the lease file with the documented shape | No claim for T-100; invoke claim for T-100 (session=S1) | `.git/openup/claims/T-100.json` exists and contains exactly the plan.md shape: `task_id`, `session_id=S1`, `branch`, `worktree`, `claimed_at` (ISO-8601 UTC), and **`touches`** (copied from frontmatter at claim time — D7). **No** TTL field. | Yes — script |
| TC-LEASE-02 | Claim is readable across worktrees | Claim T-100 from main checkout; `git worktree add` a second checkout | Second checkout reads the SAME `.git/openup/claims/T-100.json` via the shared common dir (`git rev-parse --git-common-dir` resolves identically) | **Real worktree** |
| TC-LEASE-03 | Release removes the lease file | T-100 claimed; invoke release(T-100) | `.git/openup/claims/T-100.json` no longer exists; sibling claims untouched | Yes — script |
| TC-LEASE-04 | Claim write is atomic (no partial read) | Concurrent reader loops on the claim path while a claim is written (write-to-temp + `rename()`) | Reader ever sees either no file or a complete valid-JSON file — never a truncated/partial file | Yes — script (tmp+rename assertion; or stress loop) |
| TC-LEASE-05 | Lease file is never committed | Claim T-100; `git status` in the worktree | `.git/openup/claims/` is under `.git/`, so it is inherently outside the work tree; `git status` shows nothing to commit from the claim | Yes — script |
| TC-LEASE-06 | Released claim frees the surface | Claim then release T-100 (touches=X); claim T-101 (touches=X) | Second claim succeeds — release truly cleared the live-claim membership | Yes — script |

### B. Pre-flight collision refusal (reuses T-008 D2)

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-COLL-01 | Identical touches → refused | Live claim T-100 touches `[".claude/settings.json"]` by S1; claim T-200 touches same | Refused; message **names S1** as owner of `.claude/settings.json` | Yes — script |
| TC-COLL-02 | Prefix collision (dir contains file) → refused | Live claim T-100 touches `["docs/changes/"]` (S1); claim T-200 touches `["docs/changes/T-002/"]` | Refused (D2: `docs/changes/` is a segment-prefix of `docs/changes/T-002/`); names S1 | Yes — script |
| TC-COLL-03 | Sibling non-prefix → allowed | Live claim T-100 touches `["docs/changes/"]`; claim T-200 touches `["docs/changesets/"]` | **Allowed** (D2 boundary: `changes/` is NOT a segment-prefix of `changesets/`) | Yes — script |
| TC-COLL-04 | Reverse prefix (file under claimed dir) → refused | Live claim T-100 touches `["docs/changes/T-002/"]`; claim T-200 touches `["docs/changes/"]` | Refused — D2 prefix relation is symmetric in either direction | Yes — script |
| TC-COLL-05 | Fully disjoint touches → allowed | Live claim T-100 touches `[".claude/scripts/hooks/"]`; claim T-200 touches `["docs/product/"]` | Allowed; two live claims coexist | Yes — script |
| TC-COLL-06 | `./` and trailing-slash normalisation | Live claim touches `["./docs/changes"]`; claim touches `["docs/changes/T-002/"]` | Refused — after D2 normalisation (strip `./`, treat dir as `/`-terminated) these collide | Yes — script |
| TC-COLL-07 | Partial overlap in multi-entry touches | Live claim T-100 touches `["a/", "b/"]`; claim T-200 touches `["c/", "b/x"]` | Refused on the `b/` ↔ `b/x` pair; message names S1 and cites the colliding path | Yes — script |
| TC-COLL-08 | Owner naming is mandatory | Any refusal from TC-COLL-01..07 | Refusal text includes the **owning `session_id`** (from the claim file), not just "conflict" — this is the explicit acceptance-criterion wording | Yes — assert on message |

### C. Dependency pre-flight

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-DEP-01 | Unmet dep → refused, dep named | T-009 plan `depends_on: [T-008]`; T-008 not done/verified | Claim refused; message names **T-008** as the blocking dependency | Yes — script |
| TC-DEP-02 | Met dep → allowed | T-008 status `done`/`verified`; claim T-009 | Allowed (dep satisfied) | Yes — script |
| TC-DEP-03 | Multiple deps, one unmet | `depends_on: [T-005, T-008]`, T-005 done, T-008 not | Refused; names **T-008** only (not the satisfied T-005) | Yes — script |
| TC-DEP-04 | Unmet dep + would-also-collide → **dep reason, collision not reached** | Task has an unmet `depends-on` AND `touches` that overlap a live claim | Refused with the **dependency** reason only; the collision check is **not run** (Q4: dep check precedes collision; a dep-blocked task is never collision-evaluated). Assert the refusal message cites the dep and does **not** mention the colliding surface/owner. | Yes — script |
| TC-DEP-05 | Empty `depends_on` | `depends_on: []` or absent | Dependency check passes (vacuously) | Yes — script |

### D. Worktree lifecycle

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-WT-01 | Worktree add succeeds **by default** | Start iteration for T-100 with no `worktree` override (default-on per D6) | `../<repo>-T-100` exists and is a valid worktree (`git worktree list` shows it on branch `feature/T-100-*`); claim file written | **Real worktree** |
| TC-WT-02 | Start writes worktree path into the claim | After TC-WT-01 | Claim file's `worktree` field = absolute path of `../<repo>-T-100` | **Real worktree** |
| TC-WT-03 | Complete removes worktree + releases claim | Completed T-100 via `/openup-complete-task` | `git worktree list` no longer shows it; `.git/openup/claims/T-100.json` gone; no orphaned dir; frontmatter `claimed-by`/`claimed-at`/`worktree` nulled | **Real worktree** |
| TC-WT-04 | No orphan on success path | Full start→work→complete cycle | Zero leftover worktrees and zero leftover claim files attributable to T-100 | **Real worktree** |
| TC-WT-05 | `worktree: false` opt-out → in-place, claim still written | Start iteration for T-100 with `worktree: false` (D6 escape hatch) | **No** new worktree created (`git worktree list` unchanged — still just the main checkout); work proceeds in-place; the claim file **is** still written (claim is independent of worktree mode); on complete, claim released and **no** `git worktree remove` attempted | **Real worktree** (negative assertion) |
| TC-WT-06 | Rollback — `git worktree add` fails → **no claim written** | Force `git worktree add` to fail (pre-create the target path so it collides) | Start aborts; **no** claim file exists for T-100 afterward (worktree-first ordering, D6: never leave a claim without a worktree) | **Real worktree** (failure-injected) |
| TC-WT-07 | Rollback — claim write fails after worktree exists → **worktree removed** | Worktree add succeeds, then force the claim write to fail (e.g. make claims dir unwritable / inject rename failure) | The just-created `../<repo>-T-100` worktree is **removed** as rollback (D6 inverse); no orphaned worktree and no claim left behind | **Real worktree** (failure-injected) |

### E. Parallel-session scenario (headline acceptance criterion)

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-PAR-01 | Two disjoint sessions both proceed | S1 claims T-100 (touches A) in worktree-100; S2 claims T-200 (touches B, disjoint) in worktree-200 | Two worktrees exist; two visible claim files; **both** sessions proceed | **Real worktree** (two sessions) |
| TC-PAR-02 | Both claims visible to each other | After TC-PAR-01 | From either worktree, `ls .git/openup/claims/` shows both T-100 and T-200 (shared common dir) | **Real worktree** |
| TC-PAR-03 | Overlapping second claim refused, owner named | S1 holds T-100 (touches A); S2 attempts to claim a task whose touches overlap A | S2's claim **refused**; message names **S1** (the owning session id). This is the literal program acceptance line. | **Real worktree** (can be reduced to simulated for the refusal-message assertion; cross-session realism prefers real) |
| TC-PAR-04 | Race: simultaneous claim of the same task | S1 and S2 both attempt to claim T-100 at once | Exactly one wins; the other is refused (atomic create — `O_CREAT|O_EXCL` / atomic rename). No two-owner state. | **Real worktree** / concurrency harness — see risk R1 |

### F. Claims-never-expire / abandoned-claim handling (D1/D2)

Claims have **no TTL** and are **never** age-evaluated. These cases assert that an old or
abandoned claim still blocks, and that manual `rm` is the only clear.

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-NOEXP-01 | Very old claim STILL blocks | Write a claim for T-100 (touches X) with `claimed_at` = now − 30 days; claim T-200 with overlapping touches | **Refused** — age is irrelevant; the old claim counts in the live set and blocks (D1). Names the owner. | Yes — script (timestamp fabricated) |
| TC-NOEXP-02 | No `lease_ttl_hours` / no staleness path | Inspect the claim shape and pre-flight logic | Claim file has **no** TTL/expiry field; pre-flight never reads `claimed_at` for an expiry decision (`claimed_at` is audit-only). Assert no code path filters claims by age. | Yes — schema + code assertion |
| TC-NOEXP-03 | Manual `rm` is the sole clear | Old/blocking claim present; `rm .git/openup/claims/T-100.json`; re-run pre-flight for the overlapping T-200 | After the `rm`, T-200's overlapping claim is **allowed** — removal of the file is what frees the surface (D2: no `--steal`, no auto-expire) | Yes — script |
| TC-NOEXP-04 | No `--steal` override exists | Attempt any documented force-reclaim path | There is **no** `--steal`/override flag in v1 (D2). If a `--steal` is ever added, this becomes the regression anchor — flag for v2 follow-up. | Yes — CLI surface assertion |

### G. Edge cases

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-EDGE-01 | Claims dir absent on first claim | `.git/openup/claims/` does not exist; invoke first claim | Directory auto-created (mkdir -p semantics); claim succeeds | Yes — script |
| TC-EDGE-02 | Crashed session leaves an abandoned claim | Claim file present, owning process gone (simulate: claim then "abandon", no release) | Claim persists indefinitely (no self-expiry, D1); **blocks** any overlapping claim until a human `rm`s it (cross-ref TC-NOEXP-01/03). Asserts the abandoned-claim → manual-recovery contract. | Yes — script |
| TC-EDGE-03 | Idempotent re-claim by same session | T-100 claimed by S1; S1 claims T-100 again | **No error** — idempotent (refresh `claimed_at` or no-op). Must NOT refuse "self" as a collision. | Yes — script |
| TC-EDGE-04 | Re-claim of same task by a DIFFERENT session | T-100 claimed by S1; S2 claims T-100 | Refused; names S1 (distinct from TC-EDGE-03 — same-task collision, not a touches overlap) | Yes — script |
| TC-EDGE-05 | Malformed / corrupt claim file | Hand-write invalid JSON into a claim file | Pre-flight fails safe (treat as occupied + warn) rather than crashing or treating the task as free — fail-closed. Confirm with design.md. | Yes — script |
| TC-EDGE-06 | Release of a non-existent / already-released claim | release(T-999) with no file present | Idempotent no-op (no error) — supports double-complete and crash-then-complete | Yes — script |
| TC-EDGE-07 | Empty `touches` → no collision (intended foot-gun) | Live claim T-100 touches X; claim T-200 with `touches: []` | **Allowed** — a task declaring no surface collides with nothing, and nothing collides with it (Q2 resolved: intended). This is a **documented foot-gun**: `parallel-work.md` must warn "declare your touches" since an empty list silently disables collision protection. Test asserts the no-collision behavior **and** flags the risk (see R3). | Yes — script |

---

## Coverage map → acceptance criteria

| Program acceptance / spec point | Covered by |
|---|---|
| Two sessions, disjoint tasks, separate worktrees, visible claims | TC-PAR-01, TC-PAR-02, TC-WT-01 |
| Overlapping claim refused with owning session named | TC-PAR-03, TC-COLL-01..08, TC-EDGE-04 |
| Claim is a lease, one file per claim, in `.git/openup/claims/` | TC-LEASE-01, TC-LEASE-05 |
| Cross-worktree coordination via shared common dir | TC-LEASE-02, TC-PAR-02 |
| Pre-flight refuses unmet `depends_on`, names blocker | TC-DEP-01, TC-DEP-03 |
| Dependency check precedes collision (dep-blocked → not collision-evaluated) | TC-DEP-04 |
| Pre-flight refuses `touches` overlap (D2 boundaries) | TC-COLL-02, TC-COLL-03, TC-COLL-04, TC-COLL-06 |
| Worktree default-on; `worktree: false` opt-out | TC-WT-01, TC-WT-05 |
| Worktree-first ordering + rollback on failure (D6) | TC-WT-06, TC-WT-07 |
| `/openup-complete-task` releases claim + removes worktree + nulls frontmatter | TC-LEASE-03, TC-WT-03, TC-WT-04 |
| No orphaned worktree/claim on success | TC-WT-04 |
| Claims never expire; old/abandoned claim still blocks (D1) | TC-NOEXP-01, TC-NOEXP-02, TC-EDGE-02 |
| Manual `rm` is the sole recovery; no `--steal` (D2) | TC-NOEXP-03, TC-NOEXP-04 |
| Empty `touches` → no collision (documented foot-gun, Q2) | TC-EDGE-07 |

## Test fixtures the implementation should make testable

1. **Injectable / discoverable claims dir** — tests resolve it via
   `git rev-parse --git-common-dir`/openup/claims so they don't hardcode `.git/`. (No
   injectable clock needed — claims never expire, so TC-NOEXP-01 just hand-writes an old
   `claimed_at` and asserts it is ignored.)
2. **`git worktree add` failure injection** for TC-WT-06 (pre-create the target path so
   the add collides).
3. **Claim-write failure injection** for TC-WT-07 (make the claims dir unwritable, or
   intercept the temp-rename) to exercise worktree rollback.
4. A tiny **disposable repo fixture** (`git init` + initial commit) so worktree tests
   don't run against the live repo.

## Risks (coverage gaps)

- **R1 — Concurrency is hard to make deterministic.** TC-LEASE-04 and TC-PAR-04 depend on
  the implementation using an atomic primitive (tmp+`rename`, or `O_CREAT|O_EXCL`). If it
  uses naive write/check-then-write, these tests are flaky and the race is real. The test
  can only *detect* non-atomicity probabilistically; design.md must commit to the atomic
  primitive so the test asserts the mechanism, not just runs a stress loop.
- **R2 — Real-worktree cases (TC-WT-*, TC-PAR-*) are slow and CI-environment-sensitive**
  (need a writable `..` sibling path, real `git`). They may be gated as a separate
  manual/integration tier rather than per-commit. Cross-checkout visibility cannot be
  faithfully simulated, so it cannot be fully shifted left.
- **R3 — Empty-`touches` is a silent collision-disabler (TC-EDGE-07).** Q2 made this
  intended, but it means a task that forgets to declare `touches` gets **zero** collision
  protection and will happily run on a surface another session owns — the exact merge
  conflict the feature exists to prevent. The test asserts the behavior, but the real
  mitigation is non-test: `parallel-work.md` must warn loudly, and a future lint could
  refuse an empty `touches` on a non-trivial task. Flagged for the PM as a process gap, not
  a code bug.
- **R4 — Owner-naming assertions (TC-COLL-08, TC-PAR-03) are string-format coupled.** If
  design.md doesn't fix the refusal-message contract, these tests over-fit wording.
  Recommend asserting *presence of the session id substring*, not exact phrasing.
- **R5 — RESOLVED (Q6 → design.md D7).** The claim file **carries its own `touches`** (copied
  from frontmatter at claim time); pre-flight unions `touches` from the claim files only, never
  joining back to frontmatter. Collision-case setups are now unambiguous: plant the colliding
  surface in the **claim file's `touches`** at `.git/openup/claims/T-NNN.json`. TC-COLL-* and
  TC-NOEXP-01 are now scriptable.
- **R6 — Corrupt/malformed claim file policy (TC-EDGE-05) still unpinned.** Fail-closed
  (treat as occupied) is the catalog's recommendation; design.md does not yet state it.
  Asserts "whatever design.md commits to" until confirmed.

## Open questions surfaced for the developer / PM

- **Q6 — RESOLVED (design.md D7): option (a).** Pre-flight reads each live claim's `touches`
  from the **claim file itself** (`touches` is copied from frontmatter at claim time), so the
  claim is self-contained and pre-flight never joins back to frontmatter. Every TC-COLL-* and
  TC-NOEXP-01 setup plants the colliding surface in the claim file's `touches`.

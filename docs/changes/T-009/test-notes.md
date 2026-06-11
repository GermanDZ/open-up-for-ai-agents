# T-009 — Test Notes (test strategy / case catalog)

Status: strategy only. No implementation or test code written yet (developer is
authoring `plan.md`/`design.md` concurrently). This file catalogs the test cases the
implementation must satisfy and how each is exercised.

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
- The collision *set* is READY ∪ IN-PROGRESS (T-008 D3). For T-009 the analogue is "a
  task with a **live claim file**" — a claim file is the runtime proof a task is
  in-progress. Tests treat "live claim" as the membership predicate.
- Lease TTL is **24h** per the program plan frontmatter comment (`claimed_at … stale
  after 24h`); v1 staleness remediation is **manual `rm`** unless `design.md` says
  otherwise — see TC-STALE-01 / open question Q3.

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
| TC-LEASE-01 | Claim creation writes the lease file | No claim for T-100; invoke claim(T-100, session=S1, touches=[…]) | `.git/openup/claims/T-100.json` exists; contains `task_id`, `session_id=S1`, `claimed_at` (ISO-8601), `touches`, `worktree` | Yes — script |
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
| TC-DEP-04 | Dep + collision both fail | Unmet dep AND overlapping touches | Refused; precedence documented (recommend: report dep first, or report both) — see open question Q4 | Yes — script |
| TC-DEP-05 | Empty `depends_on` | `depends_on: []` or absent | Dependency check passes (vacuously) | Yes — script |

### D. Worktree lifecycle

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-WT-01 | Worktree add succeeds | Start iteration for T-100 with `worktree: true` | `../<repo>-T-100` exists and is a valid worktree (`git worktree list` shows it on branch `feature/T-100-*`) | **Real worktree** |
| TC-WT-02 | Start writes worktree path into the claim | After TC-WT-01 | Claim file's `worktree` field = absolute path of `../<repo>-T-100` | **Real worktree** |
| TC-WT-03 | Complete removes worktree + releases claim | Completed T-100 via `/openup-complete-task` | `git worktree list` no longer shows it; `.git/openup/claims/T-100.json` gone; no orphaned dir | **Real worktree** |
| TC-WT-04 | No orphan on success path | Full start→work→complete cycle | Zero leftover worktrees and zero leftover claim files attributable to T-100 | **Real worktree** |
| TC-WT-05 | Worktree add failure does not leave a claim | Force `git worktree add` to fail (e.g. target path already exists) | Either no claim written, or claim is rolled back — no claim without a worktree (ordering/rollback documented in design.md) — see open question Q5 | **Real worktree** (failure-injected) |

### E. Parallel-session scenario (headline acceptance criterion)

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-PAR-01 | Two disjoint sessions both proceed | S1 claims T-100 (touches A) in worktree-100; S2 claims T-200 (touches B, disjoint) in worktree-200 | Two worktrees exist; two visible claim files; **both** sessions proceed | **Real worktree** (two sessions) |
| TC-PAR-02 | Both claims visible to each other | After TC-PAR-01 | From either worktree, `ls .git/openup/claims/` shows both T-100 and T-200 (shared common dir) | **Real worktree** |
| TC-PAR-03 | Overlapping second claim refused, owner named | S1 holds T-100 (touches A); S2 attempts to claim a task whose touches overlap A | S2's claim **refused**; message names **S1** (the owning session id). This is the literal program acceptance line. | **Real worktree** (can be reduced to simulated for the refusal-message assertion; cross-session realism prefers real) |
| TC-PAR-04 | Race: simultaneous claim of the same task | S1 and S2 both attempt to claim T-100 at once | Exactly one wins; the other is refused (atomic create — `O_CREAT|O_EXCL` / atomic rename). No two-owner state. | **Real worktree** / concurrency harness — see risk R1 |

### F. Stale-claim handling

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-STALE-01 | Claim older than 24h TTL | Write a claim with `claimed_at` = now − 25h | **Document expected behavior per design.md.** v1 expectation: claim is reported as STALE (warned) but pre-flight still treats it as live until a human `rm`s it (no auto-steal). Test asserts whatever design.md commits to. | Yes — script (time-injected) |
| TC-STALE-02 | Fresh claim within TTL | `claimed_at` = now − 1h | Treated as live; not flagged stale | Yes — script |
| TC-STALE-03 | `--steal` flag (if added) | Stale claim present; claim with `--steal` | If/when `--steal` lands: stale claim overwritten, new owner recorded. **Flag for future** — not in v1 unless design.md adds it (open question Q3). | Deferred |

### G. Edge cases

| id | scenario | setup | expected result | automatable? |
|---|---|---|---|---|
| TC-EDGE-01 | Claims dir absent on first claim | `.git/openup/claims/` does not exist; invoke first claim | Directory auto-created (mkdir -p semantics); claim succeeds | Yes — script |
| TC-EDGE-02 | Crashed session leaves a stale claim | Claim file present, owning process gone (simulate: claim then "abandon", no release) | Claim persists (leases don't self-expire); surfaced as stale once past TTL (TC-STALE-01); blocks overlapping claims until removed. Documents the manual-recovery path. | Yes — script |
| TC-EDGE-03 | Idempotent re-claim by same session | T-100 claimed by S1; S1 claims T-100 again | **No error** — idempotent (refresh `claimed_at` or no-op). Must NOT refuse "self" as a collision. | Yes — script |
| TC-EDGE-04 | Re-claim of same task by a DIFFERENT session | T-100 claimed by S1; S2 claims T-100 | Refused; names S1 (distinct from TC-EDGE-03 — same-task collision, not a touches overlap) | Yes — script |
| TC-EDGE-05 | Malformed / corrupt claim file | Hand-write invalid JSON into a claim file | Pre-flight fails safe (treat as occupied + warn) rather than crashing or treating the task as free — fail-closed. Confirm with design.md. | Yes — script |
| TC-EDGE-06 | Release of a non-existent / already-released claim | release(T-999) with no file present | Idempotent no-op (no error) — supports double-complete and crash-then-complete | Yes — script |
| TC-EDGE-07 | Empty `touches` | Claim T-100 with `touches: []` | Allowed; collides with nothing (and nothing collides with it) — confirm this is intended, not a foot-gun (open question Q2) | Yes — script |

---

## Coverage map → acceptance criteria

| Program acceptance / spec point | Covered by |
|---|---|
| Two sessions, disjoint tasks, separate worktrees, visible claims | TC-PAR-01, TC-PAR-02, TC-WT-01 |
| Overlapping claim refused with owning session named | TC-PAR-03, TC-COLL-01..08, TC-EDGE-04 |
| Claim is a lease, one file per claim, in `.git/openup/claims/` | TC-LEASE-01, TC-LEASE-05 |
| Cross-worktree coordination via shared common dir | TC-LEASE-02, TC-PAR-02 |
| Pre-flight refuses unmet `depends_on`, names blocker | TC-DEP-01, TC-DEP-03 |
| Pre-flight refuses `touches` overlap (D2 boundaries) | TC-COLL-02, TC-COLL-03, TC-COLL-04, TC-COLL-06 |
| `/openup-complete-task` releases claim + removes worktree | TC-LEASE-03, TC-WT-03, TC-WT-04 |
| No orphaned worktree/claim on success | TC-WT-04 |
| Stale-claim (24h TTL) behavior documented | TC-STALE-01, TC-EDGE-02 |

## Test fixtures the implementation should make testable

1. **Injectable clock** for `claimed_at` / TTL evaluation (TC-STALE-*), else tests must
   fabricate timestamps in the claim file directly.
2. **Injectable / discoverable claims dir** — tests resolve it via
   `git rev-parse --git-common-dir`/openup/claims so they don't hardcode `.git/`.
3. **`git worktree add` failure injection** for TC-WT-05 (pre-create the target path).
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
- **R3 — Stale-claim expectations (TC-STALE-01, TC-EDGE-02, TC-EDGE-05) are
  underspecified until design.md pins TTL remediation and corrupt-file policy.** Catalog
  marks these "assert what design.md commits to"; they are placeholders until then.
- **R4 — Owner-naming assertions (TC-COLL-08, TC-PAR-03) are string-format coupled.** If
  design.md doesn't fix the refusal-message contract, these tests over-fit wording.
  Recommend asserting *presence of the session id substring*, not exact phrasing.

# T-009 — Design Decisions (in-flight)

Decisions made while authoring the spec / during execution that the program plan and
`plan.md` did not fully pin down. D1 and D2 resolve **program Open Question #2 (claims TTL /
stale-claim override)** — **resolved by PM/user 2026-06-11**: no expiry, manual cleanup only.

## D1 — Claims do not expire; there is no lease TTL  *(Open Question #2 — RESOLVED by PM 2026-06-11)*

The program plan proposed a 24h lease expiry; Open Question #2 left it open. The team
initially adopted 24h as a default.

**Decided (PM/user 2026-06-11): no expiry.** A claim is **permanent until manually removed**.
There is **no `lease_ttl_hours` field**, no `claimed_at`-based staleness evaluation, and no
background sweeper. Every claim file present under `.git/openup/claims/` counts in the live
collision set **regardless of age** and blocks an overlapping claim until a human removes it.
`claimed_at` is still recorded (for human/audit visibility and to name the owner) but is
**never** used to expire a claim.

Rationale: the user chose maximum safety — zero auto-reclaim logic to build, test, or trust.
The accepted tradeoff is that a crashed/abandoned session blocks its task surface until a
human notices and clears the claim (see D2). No time-based code path exists to get wrong.

## D2 — Stale claims cleared by manual `rm` only; no `--steal` override  *(Open Question #2 — RESOLVED by PM 2026-06-11)*

Open Question #2 asks whether a `--steal` (with audit) override is needed for crashed
sessions, or whether manual `rm` is acceptable.

**Decided (PM/user 2026-06-11): manual `rm` only**, no `--steal` override. Because claims
never expire (D1), an abandoned claim **does block** an overlapping claim's pre-flight — it is
*not* silently excluded. The **only** recovery path is a human/agent removing the file with
`rm .git/openup/claims/T-NNN.json`. The `parallel-work.md` doc documents this recovery path
prominently, since with no expiry it is the sole unblock mechanism.

Rationale: auto-deletion of another session's claim is the dangerous operation (it could race
a session that is merely slow, not crashed); with no TTL there is no "obviously safe to steal"
signal at all, so v1 deliberately ships zero force-reclaim. If crashed-session friction proves
common in dogfooding, a `--steal` with audit-log entry (and possibly a reintroduced TTL) is a
v2 follow-up — explicitly out of scope here.

## D3 — Claim file write atomicity: write-temp-then-rename

Two near-simultaneous claims (or a claim racing a release) must never observe a
half-written JSON file.

**Decided:** write the claim to a temp file in the same directory
(`.git/openup/claims/.T-NNN.json.tmp`) and `os.rename`/`mv` it into place. `rename` within a
directory is atomic on the local filesystems we target (single-host per the Out-of-Scope
note), so a reader sees either the old state or the complete new file, never a partial. One
file per claim (no shared append) already removes most contention; atomic rename closes the
remaining window. Release is a single `unlink`.

## D4 — Claims dir created on first claim if absent

`.git/openup/claims/` does not exist in a fresh clone.

**Decided:** the claim-writing step does `mkdir -p` (resolved via
`git rev-parse --git-common-dir` so all linked worktrees share one dir) immediately before
the atomic write. No bootstrap/init step is required and no `.gitignore` entry is needed
(the path lives under `.git/`, which git never tracks). Pre-flight reading an absent dir
treats it as "no live claims" rather than an error.

## D5 — Live claim set is the source of truth for pre-flight, not frontmatter

T-008's readiness skill reads the frontmatter `claimed-by` field; T-009's pre-flight must
not rely on frontmatter, which can lag (it is written *after* the claim succeeds).

**Decided:** pre-flight collision detection reads **all live claim files** under
`.git/openup/claims/` (no staleness filter — per D1 every claim counts), takes the union of
their `touches` (each claim carries its own — see D7), and runs the T-008 D2
path-segment-prefix overlap against the new task's `touches`. Frontmatter `claimed-by`/`worktree` are written as a *human/readiness-visible
mirror* of the live claim, updated on claim and nulled on release — but the claim files, not
the frontmatter, are authoritative for the refusal decision. This keeps `/openup-readiness`
(frontmatter reader) and the pre-flight hook (claim-file reader) consistent without a
write-ordering hazard.

## D6 — Worktree-per-task is default-on  *(RESOLVED by PM 2026-06-11)*

The program plan proposed `worktree: true` as an opt-in flag, "default once stable." The team
initially specced it as opt-in.

**Decided (PM/user 2026-06-11): default-on.** `/openup-start-iteration` creates
`../<repo>-T-NNN` via `git worktree add` for **every** iteration by default; a
`worktree: false` escape hatch keeps the legacy in-place checkout for cases that need it
(e.g. an environment where a second worktree is impractical). The claim file is always
written regardless of worktree mode.

Consequence for ordering / rollback (resolves the tester's Q5): **create the worktree first,
then write the claim.** If `git worktree add` fails, abort before any claim file exists — never
leave a claim without a worktree. If the claim write fails after the worktree exists, remove
the just-created worktree to roll back. Release order is the inverse: drop the claim, then
`git worktree remove` (with `--force` only if the tree is known-clean per the developer's R1).

**Bootstrap exception:** T-009 itself implements worktree support, so iteration 6 runs
in-place (the feature does not yet exist to use on its own delivery). Default-on takes effect
for iterations started *after* T-009 merges.

## D7 — Claim file carries its own `touches` (resolves tester Q6)

The tester flagged a plan↔design gap: the claim shape omitted `touches`, but D5 unions live
claims' `touches` for collision. Either the claim embeds `touches`, or pre-flight joins each
claim's `task_id` back to its frontmatter `touches`.

**Decided: embed `touches` in the claim file**, copied from the task's frontmatter at claim
time. Rationale: it makes the claim self-contained and keeps pre-flight a **pure claim-file
read** — no frontmatter lookup at enforcement time, no dependency on frontmatter being
written/synced first. This is the direct expression of D5 ("claim files, not frontmatter, are
authoritative for the refusal decision"); option (b) would partly re-introduce the frontmatter
dependency D5 exists to avoid. Cost: `touches` is duplicated (frontmatter + claim) for the
life of the claim — acceptable, since the claim is ephemeral and the frontmatter remains the
durable source that seeds it. If a task's `touches` changes mid-claim (rare), the claim must
be re-written; documented as a known edge in `parallel-work.md`.

## D8 — Corrupt claim file is fail-closed (resolves tester R6)

The tester flagged (R6) that the corrupt/malformed-claim policy was unstated.

**Decided: fail-closed.** When pre-flight encounters a claim file it cannot parse, it
**refuses the new claim entirely** (exit 4, "REFUSED (fail-closed): corrupt claim …"),
regardless of whether surfaces appear to overlap — a corrupt claim's `touches` is unknowable,
so safety cannot be proven. The only exception is the claimant's *own* `task_id` (you may
repair/overwrite your own corrupt claim). Recovery is the same `rm` path as any other claim.
Rationale: corrupt coordination state should halt parallel starts until a human resolves it,
not be silently treated as a free surface. Implemented in `openup-claims.py` (`live_claims`
marks unreadable files `_corrupt`; `preflight` refuses on the first corrupt other-claim).

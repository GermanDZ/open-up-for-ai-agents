# T-009 — Design Decisions (in-flight)

Decisions made while authoring the spec / during execution that the program plan and
`plan.md` did not fully pin down. D1 and D2 resolve **program Open Question #2 (claims TTL /
stale-claim override)** — adopted as the plan's proposed defaults so implementation is not
blocked, and **flagged for PM confirmation**.

## D1 — Lease TTL = 24h  *(Open Question #2 — pending PM confirmation)*

The program plan proposes a 24h lease expiry; Open Question #2 leaves it open.

**Decided (default, pending PM confirm):** `lease_ttl_hours = 24`. A claim is **stale** when
`now - claimed_at > 24h`. TTL is stored *in the claim file* (`lease_ttl_hours`) rather than
hardcoded in the hook, so a future override is a data change, not a code change. Staleness is
evaluated at read time by the pre-flight check; there is no background sweeper.

Rationale: 24h covers a normal multi-session working day plus overnight without letting a
truly abandoned (crashed) session block the surface indefinitely. **Flagged for PM
confirmation** — if the PM wants a shorter/longer lease or a per-track TTL, only the default
constant changes.

## D2 — Stale claims cleared by manual `rm` in v1; no `--steal` override  *(Open Question #2 — pending PM confirmation)*

Open Question #2 asks whether a `--steal` (with audit) override is needed for crashed
sessions, or whether manual `rm` is acceptable.

**Decided (v1, pending PM confirm):** **manual `rm` only**, no `--steal` override in v1.
A stale claim is *excluded from the live collision set* (so it does not block a new claim's
pre-flight), but it is **not auto-deleted** and the stale claim file remains until a human/
agent removes it with `rm .git/openup/claims/T-NNN.json`. The `parallel-work.md` doc
documents this recovery path explicitly.

Rationale: auto-deletion of another session's claim is the dangerous operation (it could
race a session that is merely slow, not crashed); deferring `--steal` keeps v1 safe and
small. Because a stale claim already doesn't *block* anyone, the only cost of manual cleanup
is a leftover file, not a stuck pipeline. **Flagged for PM confirmation** — if crashed
sessions prove common in dogfooding, a `--steal` with audit-log entry is the v2 follow-up.

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

**Decided:** pre-flight collision detection reads the **live claim files** under
`.git/openup/claims/` (excluding stale ones per D1), takes the union of their `touches`, and
runs the T-008 D2 path-segment-prefix overlap against the new task's `touches`. Frontmatter
`claimed-by`/`worktree` are written as a *human/readiness-visible mirror* of the live claim,
updated on claim and nulled on release — but the claim files, not the frontmatter, are
authoritative for the refusal decision. This keeps `/openup-readiness` (frontmatter reader)
and the pre-flight hook (claim-file reader) consistent without a write-ordering hazard.

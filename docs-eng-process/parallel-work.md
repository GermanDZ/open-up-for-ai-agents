# Parallel Work: Worktrees + Lease Claims (T-009)

How two or more OpenUP sessions run at the same time without colliding. Introduced by
**T-009** (Process v2 WS5c), building on T-008's coordination frontmatter and collision
algorithm.

## The model in one paragraph

Each task runs in its **own git worktree** (a sibling directory `../<repo>-T-NNN`) and holds
a **live lease claim** — one JSON file per claim under `<git-common-dir>/openup/claims/`. The
git *common* dir is shared by every linked worktree of the repo but is never committed (it
lives under `.git/`), so parallel sessions coordinate through it without ever touching a
shared tracked file. (Kaze evidence: shared-markdown appends — `agent-runs.jsonl`,
`roadmap.md` — were the *only* source of merge conflicts in 77 days. Claims live outside the
tree precisely to avoid that.)

## The claim file

`<git-common-dir>/openup/claims/T-NNN.json`:

```json
{
  "task_id": "T-009",
  "session_id": "<from .openup/state.json>",
  "branch": "feature/T-009-worktree-claims",
  "worktree": "/abs/path/to/worktree",
  "claimed_at": "2026-06-11T14:32:00Z",
  "touches": [".claude/skills/openup-workflow/", ".claude/scripts/hooks/", "docs-eng-process/"]
}
```

- **`touches` is copied from the task's `plan.md` frontmatter at claim time** (design D7). The
  claim is therefore self-contained: pre-flight reads **only** the claim files, never joining
  back to frontmatter. Persist the plan before claiming, or the claim records no surface.
- **No TTL / expiry field** (design D1). `claimed_at` is audit-only.

## CLI: `scripts/openup-claims.py`

| Command | Purpose |
|---|---|
| `preflight --task-id T-NNN` | Read-only: deps + collision check. Exit `0` clear, `3` unmet dep, `4` collision. |
| `claim --task-id … --session-id … --branch … --worktree …` | Pre-flight, then atomically write the claim. |
| `release --task-id T-NNN` | Delete the claim (idempotent). |
| `list` / `get --task-id T-NNN` | Inspect live claims. |
| `dir` | Print the resolved claims directory. |

`touches`/`depends-on` are read from the task's frontmatter; override with `--touches` /
`--depends-on` (used by tests). Writes are atomic (temp file + `os.replace`, design D3) and
the claims dir is created on first claim (design D4).

## Pre-flight rules

Order matters — **dependencies are checked first** (design Q4): a dep-blocked task is never
collision-evaluated.

1. **Dependencies.** Every id in `depends-on` must resolve to `status ∈ {done, verified}`
   (from its change-folder frontmatter, or the roadmap as a fallback). Otherwise: refused,
   exit 3, naming the unmet dep.
2. **Collision.** The task's `touches` is compared against the union of **all** live claims'
   `touches` (claims never expire — every present claim counts). Overlap uses the T-008
   path-segment-prefix rule (design D2):
   - `docs/changes/` vs `docs/changes/T-002/` → **collision** (prefix on a `/` boundary)
   - `docs/changes/` vs `docs/changesets/` → no collision (`changes` ≠ `changesets`)
   - identical paths → collision
   On overlap: refused, exit 4, naming the owning task + session and the conflicting path(s).

## Cross-machine: `remote-check` (T-044)

The pre-flight above is **single-clone**: claims live at
`<git-common-dir>/openup/claims/`, inside `.git/`, never pushed. Two sessions of
one clone see the same claims; **separate clones do not** (full boundary in
[parallel-lanes.md → Parallelism scope](parallel-lanes.md)). So when teammates
run `/openup-next` in parallel from their own machines, the lease cannot stop
them claiming the same task — the collision only surfaces as two PRs (e.g.
TallyFox #462 vs #463).

`remote-check` is the cross-machine early-warning, using the one claim signal
clones already share — the **branch name**:

- It runs `git ls-remote --heads <remote>` and matches branches encoding the
  task as a delimited token (`feature/T-044-x` matches `T-044`; `T-44` does not).
- A match other than `--self-branch` → **exit 9** (`EXIT_REMOTE_DUP`), naming the
  remote branch. `/openup-start-iteration` runs this **before** claiming and, on
  exit 9, records a `duplicate_start_blocked` event (the clock-stamped counter
  that decides whether the heavier atomic `refs/openup/claims/*` ref-lock is ever
  worth building) and refuses the start. Since T-046 that event lands in the
  lane-owned run **shards**, so count it with
  `grep -h duplicate_start_blocked docs/agent-logs/runs/*.jsonl | wc -l`
  (or `openup-state.py runs build` then grep the consolidated `agent-runs.jsonl`).
- **Advisory / fail-open** — unlike the local collision check (which fail-*closes*
  on a corrupt claim), any remote error (no remote, unreachable, auth) exits `0`.
  The local lease stays the hard gate; this only adds a warning the lease cannot
  give. Rationale and the rejected heavier options:
  [`docs/explorations/2026-06-16-cross-machine-claim-coordination.md`](../docs/explorations/2026-06-16-cross-machine-claim-coordination.md).

## Recovery: claims never expire

There is **no automatic expiry and no `--steal`** (design D1/D2). A crashed or abandoned
session leaves a claim that keeps blocking its surface. The **only** way to free it:

```bash
rm "$(python3 scripts/openup-claims.py dir)/T-NNN.json"
```

A **corrupt** claim file is **fail-closed** (design D8): while one exists, pre-flight refuses
*all* overlapping-or-not claims (its surface is unknowable). Inspect and `rm` it.

## ⚠ Foot-gun: declare your `touches`

A task with **empty `touches` collides with nothing** (design Q2) — it silently opts out of
collision protection and may run on a surface another session owns, re-creating the exact
merge conflict this system prevents. **Always declare `touches`** in `plan.md` frontmatter for
any task that edits shared code. A future lint may refuse an empty `touches` on a non-trivial
task.

## Lifecycle

| Step | Skill | Action |
|---|---|---|
| Start | `/openup-start-iteration` | `git worktree add ../<repo>-T-NNN` (default-on; `worktree: false` opts out — design D6), then `preflight` → `claim`. Worktree first, claim second; roll back the worktree if the claim fails. |
| Work | — | Edit inside the worktree; the claim blocks overlapping starts. |
| Done | `/openup-complete-task` | `release` the claim, then `git worktree remove` (run from the main checkout). |

## See also

- [coordination-frontmatter.md](coordination-frontmatter.md) — the `touches` / `depends-on` /
  `claimed-by` fields and the collision algorithm (T-008).
- `docs/changes/archive/T-009/` — the T-009 spec, design decisions (D1–D8), and test notes.

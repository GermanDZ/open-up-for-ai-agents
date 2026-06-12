# Parallel Lanes: Shared Files, the Write-Fence, and Conflict-Free Views

How multiple concurrent lanes — agent sessions and humans, each in its own
worktree/branch — avoid stepping on each other. The lease machinery
(`scripts/openup-claims.py`, T-009) already prevents two lanes from claiming
overlapping **code** surfaces. This document covers the other half: the
**process documents** every lane writes, which is where parallel-PR conflicts
actually came from (T-024).

## The four classes of shared files

Every file a lane may write falls into one class, and each class has a
git-native, conflict-free discipline:

| Class | Examples | Discipline |
|---|---|---|
| **1. Lane-owned** | `docs/changes/T-NNN/**`, dated `docs/agent-logs/YYYY/MM/DD/*.md`, `docs/status-notes/*.md`, `docs/explorations/*.md` | One writer per file by construction. Write freely; never conflicts. **Maximize this class.** |
| **2. Append-only set** | `docs/agent-logs/agent-runs.jsonl` | `merge=union` in `.gitattributes` (T-023): both sides' appended lines are kept; order/duplication is tolerable for an audit trail. |
| **3. Derived view** | `docs/roadmap.md` Status cells, the whole `docs/project-status.md` header + `## Notes` | Written **only** by `scripts/sync-status.py`, **only** against a fresh trunk (rebase first). Never hand-edited on a task branch, never hand-merged: on conflict, rebase and re-run the script. |
| **4. Global mutable prose** | roadmap program sections (Context, "Next step" narrative), plan docs | Cannot be derived. Edited only by a task whose `touches` includes the file, after rebasing — i.e. serialized through the normal claim machinery, not written as a side effect of every completion. |

Two corollaries:

- **Git already versions what you are tempted to restate.** Dates, authorship,
  and "last updated" live in `git log` / `blame` for free. Hand-maintained
  copies of them inside class-3/4 files are pure conflict surface; prefer the
  generated stamp (`sync-status.py` writes `completed (YYYY-MM-DD)`) or no
  stamp at all.
- **A branch cannot know post-merge truth.** Fields like "Current Task" or
  "Iteration" are only defined after integration, which is why class-3 files
  may only be regenerated against the current trunk (the **fresh-base rule**).

## The write-fence: `scripts/openup-fence.py`

A deterministic check (stdlib-only, model-free) that a lane's committed diff
stays inside its lane. It shares frontmatter parsing, claim reading, and the
path-segment-prefix match with `openup-claims.py`, so the fence and the claim
pre-flight cannot disagree about what a task touches.

```bash
python3 scripts/openup-fence.py check [--task-id T-NNN] [--base origin/main] \
                                      [--allow-views] [--allow p1,p2]
python3 scripts/openup-fence.py allowed   # print the resolved allowlist (JSON)
```

Allowed for task `T-NNN` (vs `merge-base(base, HEAD)..HEAD`):

- its `touches` — live claim file first (the claim is authoritative at
  enforcement time, T-009 D7), else plan frontmatter;
- `docs/changes/T-NNN/` and `docs/changes/archive/T-NNN/`;
- the class-1/2 audit surfaces: `docs/agent-logs/`, `docs/status-notes/`,
  `docs/explorations/`;
- the class-3 views (`docs/roadmap.md`, `docs/project-status.md`) **only**
  when the base is an ancestor of HEAD (fresh-base rule) or with
  `--allow-views` (passed by `/openup-complete-task` immediately after it
  rebased).

Task id defaults to `.openup/state.json` → `task_id`. Exit codes: `0` pass
(or fence inapplicable — no resolvable base ref, stated on stderr), `2` usage,
`3` no task id, `8` violation (each file printed as `OUT OF LANE:` or
`STALE VIEW:` with the fix).

## Enforcement points — same rule for humans and agents

| Actor | Where the fence runs |
|---|---|
| Agent | `/openup-complete-task` step 3 (BLOCKING, right after `git rebase origin/main`) |
| Human | `.githooks/pre-push` — active after `git config core.hooksPath .githooks`; only fires when a lane is in flight (`.openup/state.json` exists); `SKIP_OPENUP_FENCE=1` to bypass |
| CI (optional) | run `openup-fence.py check --task-id <id> --base origin/main` as a required PR check to make the fence binding for contributors without local hooks |

## Sharded status notes: `docs/status-notes/`

The `## Notes` list in `docs/project-status.md` used to be prepended in place —
a shared insertion point every completing lane fought over. Now:

- each completion writes **one lane-owned file**:
  `docs/status-notes/YYYY-MM-DD-<task-id>.md` (add `-HHMM` before `.md` on a
  same-day repeat), containing the one-bullet iteration summary;
- `scripts/sync-status.py` assembles the `## Notes` section from those files,
  newest-first by filename (names are date-prefixed, so lexicographic
  descending = chronological descending). The section body between `## Notes`
  and the next `## ` heading is generated — do not edit it.

## Task-ID reservation: `openup-claims.py reserve-id` (T-031)

IDs are allocated at **planning** time — before any surface claim or fence
runs — so a "scan local files for the highest ID, add 1" rule was the one
parallel-lane collision the machinery above never saw: two planning lanes
(or one lane on a stale checkout) both allocate `T-{n+1}` and collide at
merge, forcing renumber churn. Reservation closes it:

```bash
python3 scripts/openup-claims.py reserve-id --session-id <s> --title "<t>"   # prints T-NNN
python3 scripts/openup-claims.py next-id                                     # dry-run, writes nothing
python3 scripts/openup-claims.py release-id --task-id T-NNN                  # free an abandoned ID
python3 scripts/openup-claims.py list-ids                                    # live reservations
```

- One reservation file per ID under `<git-common-dir>/openup/claims/ids/` —
  shared across worktrees like the surface claims, never committed.
- The candidate is `max(used ∪ reserved) + 1`, where *used* unions change-folder
  frontmatter ids, the full `docs/roadmap.md` text, **and**
  `origin/main:docs/roadmap.md` when that ref exists (stale-checkout guard;
  pure local read). Creation is atomic (exclusive hard-link); a lost race
  advances to the next number, so concurrent reservations always get
  distinct IDs.
- Reservation rules mirror claims: no expiry, `release-id`/`rm` to free one.
  A reservation whose ID has landed on trunk is redundant, not wrong — the
  allocator's repo scan already counts it.
- `--prefix`/`--pad` cover phase-iteration ID schemes (`C3-001` …) for
  `/openup-plan-feature`; the default `T-`/3 serves `/openup-create-task-spec`.

## Conflict recovery recipe

If a PR reports conflicts in `docs/roadmap.md` or `docs/project-status.md`:

```bash
git fetch origin main
git rebase origin/main        # take THEIRS for the view files if prompted —
                              # their content is about to be regenerated anyway
python3 scripts/sync-status.py
git push --force-with-lease
```

Never hand-merge the views. Every field they carry is derived from lane-owned
inputs (frontmatter, state, status-notes), so the re-run is always correct.

## See Also

- `scripts/openup-claims.py` — leases + collision pre-flight (T-009) and
  task-ID reservation (T-031); the fence imports its parsing and path-match
  logic.
- `scripts/openup-board.py` — the derived execution queue (T-017); same
  "derive, don't author" principle applied to scheduling.
- [state-file.md](state-file.md) — `.openup/state.json` and the gate lifecycle.
- `docs/explorations/2026-06-12-multi-worktree-coordination.md` — the analysis
  that produced this design (file-class taxonomy, options considered).

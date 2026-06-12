# Exploration: Multi-worktree / multi-branch coordination without shared-file conflicts

**Started:** 2026-06-12
**Question:** How should multiple concurrent lanes — agentic bots and humans — work
in separate worktrees/branches with guardrails that prevent them from stepping on
each other, given that the current process still produces PR conflicts in
`docs/roadmap.md`, `docs/project-status.md`, and other shared files?

## Context

The process already solved the *code* half of this problem:

- **Leases** (`scripts/openup-claims.py`, T-009): one JSON file per claim under
  `<git-common-dir>/openup/claims/T-NNN.json` — shared across all linked
  worktrees, never committed, never expiring. Pre-flight checks dependencies
  first, then a path-segment-prefix collision test against each claim's own
  `touches` list.
- **Derived board** (`scripts/openup-board.py`, T-017): `.openup/board.json` is
  regenerated from frontmatter + leases + Operations checkboxes; the model never
  authors it. Board `ready` ≡ preflight-clear by construction (shared code).
- **Append-only log fix** (T-023): `docs/agent-logs/agent-runs.jsonl` got
  `merge=union` in `.gitattributes`, so parallel branches appending records no
  longer conflict at EOF.

Yet PRs still conflict. The remaining conflicts are not in code — they are in the
**process documents themselves**, and they are caused by the process's own
bookkeeping steps, not by overlapping task scope. The leases can't help, because
their `touches` model assumes each task touches a *different* surface — while the
bookkeeping files are touched by **every** task by design.

## Notes

### Inventory of the actual conflict surfaces

Walking `scripts/sync-status.py` and `/openup-complete-task` shows exactly which
writes collide when two lanes run in parallel and both open PRs:

| File / write | Who writes it | Why parallel lanes conflict |
|---|---|---|
| `docs/project-status.md` **header** (`Iteration`, `Current Task`, `Status`, `Iteration Goal`, `Last Updated`, `Updated By`) | `sync-status.py`, every completion | Every lane rewrites the *same six lines* with different values. Guaranteed conflict; `merge=union` would produce nonsense (these are not append-only). |
| `docs/project-status.md` **Notes** list | complete-task, every completion | Both lanes prepend an entry at the same position. Entries are independent, but the insertion point is shared. |
| `docs/roadmap.md` **Status cells** | `sync-status.py` flips the task's row | Different rows *usually* merge cleanly, but adjacent rows in one markdown table conflict, and the surrounding diff context overlaps. |
| `docs/roadmap.md` **"Next step" / Notes prose** | complete-task narrative updates | Shared mutable paragraphs rewritten by each lane — classic last-writer-wins content with no merge strategy. |
| **Iteration number** (global counter in state + status header) | `openup-start-iteration` | Two parallel lanes both allocate "iteration N+1"; the duplicate surfaces as a content conflict in the status header and in log filenames. |
| `docs/agent-logs/agent-runs.jsonl` | every lane | ✅ already solved by `merge=union` (T-023). |
| `docs/changes/T-NNN/**`, `docs/agent-logs/<date>/<file>.md` | the owning lane only | ✅ never conflicts — per-task namespace, one writer. |

The pattern is crisp: **everything per-task-owned merges cleanly; everything
globally mutable conflicts.** T-023 fixed the one append-only global file; the
remaining offenders are *views of global state* that each branch tries to update
locally, pre-merge — i.e. before it can possibly know the post-merge truth.
A branch literally cannot write a correct "current iteration / current task"
line, because that truth is only defined *after* integration.

### The classification that makes this tractable

Every file a lane may write falls into one of four classes, each with a known
git-native answer:

1. **Per-lane-owned** (`docs/changes/T-NNN/`, dated log files, exploration
   files): conflict-free by construction. *Maximize this class.*
2. **Append-only set** (run-log JSONL): `merge=union` in `.gitattributes`;
   order/duplication tolerable, re-derive a sorted view if needed. Already done.
3. **Derived view** (board.json today; roadmap status cells and the whole
   project-status header *should be* this): regenerated deterministically from
   classes 1–2; **never hand-merged and never written on a task branch**.
   `.openup/board.json` already proves the pattern works — it is gitignored and
   rebuilt, so it can't conflict.
4. **Truly global mutable** (roadmap prose, plan-hook sections): cannot be
   derived; must be either serialized (one writer at a time, via lease) or
   moved out of the per-task write path (edited only in dedicated
   roadmap-editing tasks, not as a side effect of completing T-NNN).

The current failures are all "class-3 content being written as if it were
class-4, on every branch, concurrently."

### Git already versions what the headers restate

`Last Updated`, `Updated By`, `(2026-06-12)` completion stamps — these duplicate
information git records for free (`git log -1 --format='%cs %an' -- <file>`,
blame, PR merge dates). Restating them inside shared files converts zero-entropy
metadata into a permanent conflict surface. Dropping them (or moving them into
the generated view only) removes conflicts *and* a lying-data risk — the git
history can't drift; a hand-maintained "Last Updated" can.

The same applies to the global iteration counter: lane identity is already
task-scoped (`T-NNN` + branch + archived `state.json`). The iteration *number*
is only meaningful in integration order, which is exactly what `git log
--first-parent main` records. It can be derived post-merge (count of completion
records on main) instead of allocated pre-merge.

### Humans and bots need the same fence, enforced the same way

Bots follow skills; humans don't reliably. The guardrail that covers both is a
**deterministic write-fence check** on the diff itself, runnable as a pre-push
hook and as a PR/CI check:

```
git diff --name-only origin/main...HEAD
```

validated against: the lane's claim `touches` ∪ `docs/changes/<task>/**` ∪ the
lane's dated log files ∪ class-2 union files. Anything else → fail with the
class-4 escape hatch named ("this file is a derived view — it is generated on
main, don't edit it on a branch"). This is the same agreement-by-construction
move as board↔preflight: the fence imports the claims module's `touches`
parsing, so what preflight cleared is exactly what the fence allows. A human
who never runs a skill still hits the fence at push/PR time; a bot hits it
earlier via the complete-task gate.

Claims already work for humans mechanically (`python3 scripts/openup-claims.py
claim --task-id T-NNN` from any worktree — the common-dir location means every
worktree sees the same lease set); what's missing is only the *enforcement*
point that doesn't depend on voluntarily running preflight.

### Options Considered

- **Option A — Promote roadmap/status to derived views (extend the board
  pattern).** Task `status:` already lives in change-folder frontmatter (the
  board reads it); make `sync-status.py` (or a successor `openup-views.py`)
  render the roadmap task tables and the entire `project-status.md` from
  frontmatter + archived states + the union log, and run it **only on main
  post-merge** (CI or a merge hook), never on task branches. Branches stop
  writing these files entirely; the `roadmap_synced` gate becomes "frontmatter
  status updated" (per-lane-owned, conflict-free).
  Pro: eliminates the conflict class at the root; reuses a proven in-repo
  pattern; single source of truth stops dual-maintenance drift.
  Con: roadmap prose (Context, Next-step narrative) must be split out of the
  generated region or moved into plan docs; needs a migration of the current
  hand-written roadmap; "where does regeneration run" must be decided.

- **Option B — Shard the status Notes (one file per entry, view assembles
  them).** `docs/status-notes/<date>-<task>.md` per completion, like the dated
  agent-logs; the generated status doc inlines the latest N.
  Pro: trivially conflict-free; matches the existing log layout.
  Con: only fixes one of the surfaces; pointless without A (the header still
  conflicts).

- **Option C — Write-fence preflight for humans and bots.** The deterministic
  diff-vs-allowed-paths check above, as pre-push hook + PR check + complete-task
  gate, sharing the claims module's parsing.
  Pro: one guardrail covering both actor types; catches every future regression
  of A (someone hand-editing a generated file) instead of relying on rules in
  CLAUDE.md prose; cheap (stdlib, same style as existing scripts).
  Con: needs an escape hatch for legitimately-global edits (dedicated
  roadmap-editing tasks whose `touches` includes the file — which the fence
  already expresses naturally).

- **Option D — Extend `merge=union` to roadmap/status.** Rejected: union is
  only sound for unordered append-only sets. Status cells and header fields are
  last-writer-wins values; union would keep both contradictory lines.

- **Option E — Serialize completions through an integration queue** (rebase
  main + rerun sync-status before merging each PR). Workable today as a manual
  discipline and worth keeping as the interim mitigation, but it makes every
  completion contend on a global lock — exactly the friction worktree-per-task
  exists to remove. Complementary at best, not the fix.

Recommended shape: **A + B + C together** (derive the views, shard the entries,
fence the writes), with E as the stopgap until A lands. Drop the restated git
metadata (`Last Updated`, `Updated By`, inline completion dates outside the
generated view) and the pre-allocated global iteration number as part of A.

## Open Questions

- Where does view regeneration run — a post-merge CI commit to main, a
  human/bot-run `openup-views.py refresh` on main after merging, or generation
  into a gitignored file like `board.json` with `roadmap.md` reduced to prose +
  a pointer? (CI-commit is the most automatic but puts a bot commit on main;
  gitignored is the cleanest git-wise but loses the browsable-on-GitHub view.)
- How much of today's `roadmap.md` is prose that stays hand-written (plan-hook
  sections, Context paragraphs) vs table that becomes generated? Likely split:
  prose stays class-4 and is edited only by dedicated roadmap tasks; tables and
  status fields become class-3.
- Does the iteration number survive at all, or is "task + merge order on main"
  enough identity? (Retro cadence already uses its own durable counter in
  `.openup/retro.json`, so it does not depend on the iteration number.)
- Should the write-fence run server-side (required PR check) to be binding for
  humans, given local hooks are opt-in?
- Migration: regenerating the roadmap from frontmatter requires backfilling
  `status:` frontmatter for the archived/early tasks that predate it.

## Where this goes next

→ iteration — promote to a roadmap entry: **"Conflict-free shared views:
derive roadmap/status from per-lane state (frontmatter + sharded notes),
post-merge regeneration on main, and a claims-aware write-fence (pre-push + PR
check) for humans and bots"** — scoped as one standard-track iteration building
`openup-views.py` + the fence on the existing claims/board machinery, with
`merge=union`-style interim mitigation (Option E discipline) documented until
it lands.

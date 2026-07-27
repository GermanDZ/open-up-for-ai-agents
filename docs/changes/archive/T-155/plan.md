---
id: T-155
title: "merge=union for the two shared .claude/memory/ append-only files, delivered to existing consumers as well as new ones"
status: done
priority: low
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - .gitattributes
  - scripts/sync-from-framework.sh
  - scripts/lib/migrate-data.sh
  - scripts/tests/test_t155_memory_merge_union.py
  - scripts/tests/test_consumer_smoke.py
  - docs-eng-process/parallel-lanes.md
  - docs/roadmap.md
---

# T-155 — `merge=union` for the two shared `.claude/memory/` append-only files

## Story

> **As a** practitioner running parallel OpenUP lanes in a repo that *tracks*
>   `.claude/`
> **I want** the two append-only files every lane is forced to write to stop
>   requiring a hand-resolved merge
> **So that** merging trunk into a feature branch stops costing a manual
>   reconciliation of an audit log whose lines are independent anyway.

INVEST check:
✅ Independent — T-147 is merged and archived ·
✅ Negotiable — the roadmap offers three options and delegates the choice ·
✅ Valuable — removes a recurring manual reconciliation, evidenced 3× downstream ·
✅ Estimable — one attribute file, one idempotent shell patch, tests ·
✅ Small — no new module, no new CLI ·
✅ Testable — every requirement is a file's content after a real script run.

## Analysis Context

- **Domain.** Git merge behavior for the two involuntarily-shared class-2 files
  (`docs-eng-process/parallel-lanes.md`), and the two paths by which framework
  root dotfiles reach consumer repos.
- **Premise verified downstream before drafting** (action item B2; the T-147 DD4
  precedent), read-only, on 2026-07-27:

  | Check | `kaze-webapp` | `cqecho-app` |
  |---|---|---|
  | Tracks the two files? | **yes** | **no — neither is tracked** |
  | Has `.gitattributes`? | yes (3 lines, incl. the run-log union entry) | **no file at all** |
  | Commits touching `bypass-log.md` | 91 | n/a |
  | Commits touching `iteration-learnings.md` | 45 | n/a |
  | Merges where **both sides** had to be reconciled | **`bypass-log.md`: 3 of 3** · `iteration-learnings.md`: **0** | n/a |

  So the problem is **real but narrower than the roadmap assumed**: it affects
  **one** repo, and within it **one** of the two files has actually collided.
  `iteration-learnings.md` has never had a two-sided merge — one append per lane
  completion, and lanes complete serially. `bypass-log.md` is written by hooks on
  essentially every lane, which is why it collides.
- **The 3 observed collisions are all the case `merge=union` fixes.** Each is a
  *local* merge (`Merge remote-tracking branch 'origin/main' into <branch>`),
  where git runs the merge driver. The documented caveat — GitHub does not run
  merge drivers server-side — bounds the *residual*, not the observed benefit.
- **Delivery is the real finding.** `bootstrap-project.sh` copies
  `.gitattributes` (line ~148) — but **only at initial bootstrap**, and **no
  updater ships it**: `sync-from-framework.sh` patches `.gitignore` at the
  project root (T-056, ~line 703) and touches `.gitattributes` nowhere. So
  "ship it via the bootstrap" reaches **new projects only** — and the single
  repo where this actually happens is an *existing* one. An attribute added to
  `.gitattributes` alone would provably never reach it.
- **Scope boundaries.** Not covered: sharding either file (see the rejected
  option below); changing what the hooks or `openup-scribe.py learnings` write;
  the server-side PR-conflict case (unfixable by any merge driver); anything in
  a consumer repo — sibling repos are **read-only evidence** and this task
  modifies none of them.
- **Definition of done.** The two entries exist in the framework's
  `.gitattributes`, a freshly bootstrapped consumer receives them, an *existing*
  consumer receives them on its next `sync-from-framework.sh` run (idempotently,
  creating the file if absent), and the residual is written down rather than
  implied.

> **Assumption:** both files get the attribute, not just the one with observed
> collisions. `iteration-learnings.md` is the same shape and the same
> involuntary class-2 surface; a per-file split would encode "this one hasn't
> bitten yet" as design. *(Vetoable at review.)*

> **Assumption:** the sync patch **appends** the entries to an existing
> `.gitattributes` rather than overwriting the file, so a consumer's own
> attributes survive. *(Vetoable at review.)*

### Rejected: sharding (the T-046 treatment)

T-046 sharded `agent-runs.jsonl` into per-lane files precisely because union does
not fix the PR case, so sharding deserves a real hearing here. Rejected because
the two situations differ where it counts:

- **The read path has no generator.** `agent-runs.jsonl` is consumed by tooling
  that can assemble a view. These two files are read **directly, at a fixed
  path**, by an agent at session start (`.claude/CLAUDE.openup.md` → "read
  `.claude/memory/iteration-learnings.md`") and by hooks. Sharding would require
  a consolidation step that nothing currently runs, in the consumer's checkout.
- **The writers live downstream.** They are written by consumer-side hooks and
  `openup-scribe.py learnings` into fixed consumer paths. Sharding means changing
  those writers *and* migrating existing files in every consumer — a migration
  whose cost lands entirely on repos that, per the table above, have collided
  three times total.
- **The evidence does not support it.** One file, three local merges, all of
  which union resolves automatically.

Recorded here rather than silently dropped, because "why not shard?" is the
first question a reviewer of this task should ask.

## Requirements

1. The framework's `.gitattributes` carries a `merge=union` entry for **both**
   `.claude/memory/bypass-log.md` and `.claude/memory/iteration-learnings.md`.
   - **Given** the repo's `.gitattributes`
     **When** it is read
     **Then** it contains a line matching each of the two paths with
     `merge=union`, adjacent to a comment naming T-155 and stating the
     server-side residual.

2. A freshly bootstrapped consumer receives both entries.
   - **Given** a temp directory
     **When** `scripts/bootstrap-project.sh` is run into it
     **Then** the created project's `.gitattributes` contains both `merge=union`
     lines.

3. `sync-from-framework.sh` adds the entries to an **existing** consumer whose
   `.gitattributes` lacks them, preserving the file's existing content.
   - **Given** a consumer fixture whose `.gitattributes` contains only
     `* text=auto` and a project-specific line
     **When** `sync-from-framework.sh` runs against it
     **Then** both `merge=union` lines are present **and** the two pre-existing
     lines are still present, unmodified.

4. That patch is idempotent — a second run adds nothing.
   - **Given** a consumer that has already been patched once
     **When** `sync-from-framework.sh` runs again
     **Then** each of the two entries appears exactly once and the file is
     byte-identical to its post-first-run content.

5. The patch creates `.gitattributes` when the consumer has none (the
   `cqecho-app` shape).
   - **Given** a consumer fixture with no `.gitattributes` at all
     **When** `sync-from-framework.sh` runs against it
     **Then** `.gitattributes` exists and contains both entries.

6. `--dry-run` reports the change without writing it, matching the T-056
   `.gitignore` patch's behavior.
   - **Given** an unpatched consumer fixture
     **When** `sync-from-framework.sh --dry-run` runs
     **Then** stdout names the intended `.gitattributes` change and the file on
     disk is unchanged.

7. The residual is documented where the class is defined, not left implied.
   - **Given** `docs-eng-process/parallel-lanes.md`'s class-2 row
     **When** it is read after this change
     **Then** it states that the decision was `merge=union` (not sharding), why
     sharding was rejected, and that server-side PR conflicts remain.

## Behavior Delta

Ring 1 (`docs/product/`) carries no use case for the install/merge surface; the
contract lives in `docs-eng-process/`, which the citations name.

**Added**
- Two `merge=union` entries in `.gitattributes`.
- A `.gitattributes` patch step in `sync-from-framework.sh` — the first time that
  script touches this file.

**Modified**
- The class-2 row now records a **decision** instead of an open question —
  `docs-eng-process/parallel-lanes.md §Shared-file classes` (class 2 row).
- Consumer sync gains a root-dotfile side effect —
  `docs-eng-process/parallel-lanes.md` (same row) and the script's own log output.

**Removed**
- Nothing. The open question T-147 left in the class-2 row is answered, not
  deleted.

## Entities

- **Attribute file** (modified) — `.gitattributes`
- **Migration helper** (modified) — `scripts/lib/migrate-data.sh`
  (`migrate_gitattributes_merge_union`, new)
- **Consumer updater** (modified) — `scripts/sync-from-framework.sh` (call site
  only; mirrors the T-046 `migrate_untrack_agent_runs` wiring)
- **Bootstrap** (read-only — already copies the file) —
  `scripts/bootstrap-project.sh` entrypoint-file loop
- **Class-2 definition** (modified) — `docs-eng-process/parallel-lanes.md`
- **Consumer smoke test** (modified) — `scripts/tests/test_consumer_smoke.py`

## Approach

Take the cheap, precedented mitigation and be explicit that it is partial. The
attribute mirrors the run-log entry already in `.gitattributes`, so the file
gains a second instance of a pattern it already documents. The load-bearing work
is **delivery**, not the attribute: an idempotent, `--dry-run`-aware patch block
in `sync-from-framework.sh`, shaped exactly like T-056's `.gitignore` patch, so
consumers that already exist can receive it — without which the change reaches
zero of the repos where the collision occurs.

## Structure

**Add:**
- `scripts/tests/test_t155_memory_merge_union.py` — requirements 3–6 (the sync
  patch, against consumer fixtures).

**Modify:**
- `.gitattributes` — two entries plus a comment naming T-155, the decision, and
  the server-side residual.
- `scripts/lib/migrate-data.sh` — new sourceable
  `migrate_gitattributes_merge_union <root> <dry>`. The logic lives here, not
  inline in the sync script, because that file states the convention itself at
  its T-046 call site: *"logic lives in scripts/lib/migrate-data.sh so it is
  unit-testable"*. An inline block would be untestable without running the whole
  sync.
- `scripts/sync-from-framework.sh` — source the helper and call it, mirroring the
  existing T-046 `migrate_untrack_agent_runs` call site; honors `DRY_RUN`.
- `scripts/tests/test_consumer_smoke.py` — requirement 2, on the existing
  module-scoped bootstrapped `consumer` fixture.
- `docs-eng-process/parallel-lanes.md` — class-2 row: decision, rejected
  alternative, residual.
- `docs/roadmap.md` — status cell (via `sync-status.py`, never by hand).

**Do not touch:**
- `scripts/bootstrap-project.sh` — it already copies `.gitattributes`; adding
  anything there would duplicate the delivery path.
- The hooks and `openup-scribe.py learnings` — changing what they write is the
  sharding option, explicitly rejected above.
- Any sibling consumer repo (`kaze-webapp`, `cqecho-app`) — read-only evidence.
  The fix reaches them when *they* run their own updater.
- `scripts/process-manifest.txt` — no new CLI; `.gitattributes` ships through
  the bootstrap's entrypoint loop, not the manifest.

## Operations

- [x] Add the two `merge=union` entries to `.gitattributes`, with a comment
      naming T-155, the rejected sharding option, and the server-side residual.
- [x] Add `migrate_gitattributes_merge_union <root> <dry>` to
      `scripts/lib/migrate-data.sh` (idempotent, `DRY_RUN`-aware, creates the
      file when absent, appends without disturbing existing lines) and call it
      from `scripts/sync-from-framework.sh` at the existing migration call site.
- [x] Record the decision, the rejected alternative, and the residual in
      `docs-eng-process/parallel-lanes.md`'s class-2 row.
- [x] (tester) Write `scripts/tests/test_t155_memory_merge_union.py` covering
      requirements 3–6 against fixtures for both consumer shapes (has
      `.gitattributes` / has none).
- [x] (tester) Add the requirement-2 assertion to
      `scripts/tests/test_consumer_smoke.py`'s bootstrapped fixture, then run
      that module plus the new one and `test_sync_migration.py` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, script conventions.
- `docs-eng-process/parallel-lanes.md` — the shared-file class model.
- `.claude/CLAUDE.openup.md` — derived views are never hand-edited.
- `scripts/sync-from-framework.sh`'s own T-056 block — the idempotent-patch idiom.

## Safeguards

- **Consumer files are never overwritten.** The patch appends; a consumer's own
  attributes and any hand-added lines survive. Overwriting `.gitattributes`
  wholesale is a no-go.
- **Sibling repos are read-only.** No lane in this task writes to `kaze-webapp`
  or `cqecho-app`; they are evidence only.
- **Idempotence is a requirement, not a hope** — the patch is guarded by a
  content check, and requirement 4 pins it.
- **Token / size budget.** `sync-from-framework.sh` delta ≤ ~30 lines; no new
  CLI, no new module.
- **Reversibility.** Revert the commit. Entries already written into consumer
  `.gitattributes` files are inert once the framework stops shipping them, and
  a stray `merge=union` on an append-only file is harmless.
- **No-go zones.** The hooks' and scribe's write paths; `bootstrap-project.sh`'s
  entrypoint loop; `derive`/fence machinery; the run-log entry already present.
- **Honesty invariant.** This change must not be described anywhere — comment,
  doc, or commit message — as making the files conflict-free. It reduces local
  merge conflicts only.

## Verification

- `python3 -m unittest scripts.tests.test_t155_memory_merge_union` — green.
- `pytest scripts/tests/test_consumer_smoke.py scripts/tests/test_sync_migration.py -q` — green.
- Full suite green (`pytest scripts/tests -q`).
- `grep -c '^[^#].*merge=union' .gitattributes` returns 3 (run log + the two new
  entries). The `^[^#]` guard is load-bearing: a bare `grep -c 'merge=union'`
  returns 5, because the explanatory comment block names the attribute in prose.
- `python3 scripts/check-docs.py` exits 0; `python3 scripts/openup-fence.py check` exits 0.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

We expect **the number of merge commits on `.claude/memory/bypass-log.md` in
`kaze-webapp` that require reconciling both parents** to be **0** over the
**next ~10 merges** after that repo takes this update — down from the current
**3 of 3**. Instrumentation: the git-history query already demonstrated in that
repo on 2026-07-27 — for each merge commit touching the file, compare it against
both parents (`git diff --name-only <parent> <merge> -- <file>`); a merge that
differs from *both* is a two-sided reconciliation. Read-back environment:
**`kaze-webapp`** (read-only) — this is a downstream measure by necessity,
because this repo gitignores `/.claude/*` and can never produce the collision.
The query needs nothing installed there; it was run there before this spec was
written. Read-back: the next `/openup-retrospective` **after `kaze-webapp` has
run `sync-from-framework.sh`**.

**The dependency is the honest part**: until that repo runs its own updater, the
attribute is not present there and the measure cannot move. A `0` read *before*
the update has landed means "not yet delivered", not "fixed" — so the read-back
must first confirm both entries exist in `kaze-webapp/.gitattributes`, exactly
the check that made T-052's measure unanswerable when it was skipped.

## Rollout

**Flagged? No.** A git attribute is a per-repo file read by git itself; there is
nothing to toggle at runtime, and a flag would need its own delivery mechanism —
strictly more machinery than the one line it would guard. Reaching users is a
*delivery* question, not a rollout one, which is why the sync patch is the
substance of this task rather than a footnote. Kill-switch equivalent: remove the
two lines from `.gitattributes` (locally, or by reverting the commit); git falls
back to the default merge driver immediately, with no migration and no in-flight
state. No flag, therefore no flag-removal follow-up.

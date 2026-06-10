---
name: openup-readiness
description: Compute the change-folder dependency DAG and print READY/BLOCKED/collision report for PM intake
model: haiku
fit:
  great: [PM intake "what can I start next", dependency-reason lookups, collision pre-flight before claiming]
  ok: [mid-iteration "is T-NNN unblocked yet" checks]
  poor: [editing frontmatter (this skill is read-only), live worktree-claim enforcement (that is T-009)]
arguments:
  - name: task_id
    description: "Optional. If given, report only this task's readiness and the reason chain; otherwise report all tasks."
    required: false
---

# Readiness

Compute the coordination DAG from change-folder frontmatter and print a deterministic
readiness report. PM intake becomes a query — "what is READY, what is BLOCKED and why,
which READY tasks would collide" — instead of reading prose roadmap notes.

**This skill is READ-ONLY.** It parses files and prints a report. It writes nothing,
claims nothing, and creates no worktrees. Live lease claims under `.git/openup/claims/`
are out of scope (that is T-009); this skill reads only the `claimed-by` *frontmatter
field*.

> **Coordination step** — this skill is mechanical (`model: haiku`). The rules below are
> exhaustive; do **not** use judgment or infer status from prose. Read frontmatter, apply
> the rules, print the report.

## Inputs

1. **Authoritative source — change-folder frontmatter.** Every `plan.md` under
   `docs/changes/**/` *including* `docs/changes/archive/**/`. Each contributes one task
   record from its YAML frontmatter (see `docs-eng-process/coordination-frontmatter.md`).
2. **Human view — roadmap table.** The task table(s) in `docs/roadmap.md`. Used ONLY to
   list tasks that have a roadmap row but **no change folder yet** (e.g. T-009, T-010,
   T-011). These are reported in a clearly-marked "Roadmap-only" section and are NOT
   authoritative.

## Process

### 1. Collect task records

```bash
# enumerate every change-folder plan (active + archived)
find docs/changes -name plan.md
```

For each `plan.md`, parse the YAML frontmatter into a record:
`id`, `status`, `depends-on` (list, default `[]`), `blocks` (list, default `[]`),
`touches` (list, default `[]`), `claimed-by` (default `null`), `title`.
Build a map `id -> record`. This map is the **authoritative** set.

Then parse the roadmap table rows. For any roadmap `ID` **not** present in the
authoritative map, capture its `Status` and `Depends on` cells as a **roadmap-only**
record (clearly non-authoritative).

### 2. Resolve status of each dependency

A dependency id `D` is **satisfied** iff:
- `D` is in the authoritative map with `status ∈ {done, verified}`, OR
- `D` is not in the authoritative map but its roadmap-only `Status` is `completed`,
  `done`, or `verified`.

Otherwise `D` is **unsatisfied**; record *why* (`D blocked`, `D in-progress`, `D
proposed/ready`, `D deferred`, `D unknown` if it appears nowhere).

### 3. Classify each authoritative task

Apply in this exact order; each task lands in exactly one bucket:

| Bucket | Rule |
|---|---|
| **DONE/VERIFIED** | `status ∈ {done, verified}` |
| **DEFERRED** | `status == deferred` |
| **IN-PROGRESS** | `status == in-progress` |
| **READY** | `status ∈ {proposed, ready}` **AND** every id in `depends-on` is *satisfied* (step 2) |
| **BLOCKED** | `status ∈ {proposed, ready, blocked}` **AND** at least one `depends-on` id is *unsatisfied* — OR `status == blocked` regardless |

Notes:
- A task with no `depends-on` and `status ∈ {proposed, ready}` is always READY.
- `status == blocked` is always BLOCKED even if deps now resolve (the author asserted a
  block; surface it, don't silently promote it — list it with reason
  "status declared blocked").

### 4. Compute collisions

Consider the **collision set** = all READY tasks ∪ all IN-PROGRESS tasks.
For every unordered pair `(A, B)` in the collision set, compare their `touches` lists.
Flag a collision iff some path `pa ∈ A.touches` and `pb ∈ B.touches` **share a path
prefix**, i.e. after normalising (strip leading `./`, ensure a single trailing `/` on
directory-looking entries) one is a prefix of the other on a path-segment boundary:

- `docs/changes/` vs `docs/changes/T-002/` → collision (prefix on a `/` boundary).
- `docs/changes/` vs `docs/changesets/` → NO collision (`changes` ≠ `changesets`; the
  prefix must end at a `/` or be the whole segment).
- `a/b` vs `a/b` → collision (identical).

For each flagged pair, name both task ids and the overlapping path(s).

Additionally, for every task in the collision set with a non-null `claimed-by`, surface
"claimed by `<session>`" so the PM knows it is owned.

### 5. Emit the report

Print sections in **exactly this order**. Omit a section's body with `(none)` if empty,
but always print the heading.

```
# Readiness Report — <date>
Source of truth: docs/changes/**/plan.md frontmatter (authoritative).
Roadmap rows without a change folder are listed separately (human view, not authoritative).

## READY
- <id> — <title>   [deps: <satisfied dep ids, or "none">]

## BLOCKED
- <id> — <title>   blocked on: <unsatisfied dep id> (<reason>), ...

## IN-PROGRESS
- <id> — <title>

## DONE / VERIFIED
<count> task(s): <id>, <id>, ...

## DEFERRED
- <id> — <title>   (<defer-until note if present>)

## ⚠ COLLISIONS
- <idA> ↔ <idB>: overlapping touches <path>
- <id>: claimed by <session>

## Roadmap-only (no change folder yet)
Human view from docs/roadmap.md — NOT authoritative frontmatter.
- <id> — <title>   status=<roadmap status>, depends-on=<...>  → <READY|BLOCKED reason using roadmap deps>
```

If `$ARGUMENTS[task_id]` is provided, print only that task's line plus its dependency
reason chain, skipping the other sections.

## Worked Example (current repo state, 2026-06-11)

Authoritative records parsed from `docs/changes/**/plan.md`:

| id | status | depends-on | blocks | touches |
|---|---|---|---|---|
| T-001 | done | [] | [T-002] | — |
| T-002 | deferred | [T-001] | [] | .claude/skills/openup-workflow/, docs-eng-process/templates/ |
| T-003 | done | [] | [] | — |
| T-007 | done | [] | [T-008] | — |
| T-008 | in-progress | [T-007] | [T-009] | docs/changes/, .claude/skills/openup-workflow/, docs-eng-process/ |

Roadmap-only (rows with no change folder): T-009 (depends T-005,T-008), T-010 (depends
T-005,T-006), T-011 (depends T-005). T-004/T-005/T-006 are `completed` in the roadmap.

Resulting report:

```
# Readiness Report — 2026-06-11
Source of truth: docs/changes/**/plan.md frontmatter (authoritative).
Roadmap rows without a change folder are listed separately (human view, not authoritative).

## READY
(none)

## BLOCKED
(none)

## IN-PROGRESS
- T-008 — Coordination frontmatter + /openup-readiness DAG

## DONE / VERIFIED
3 task(s): T-001, T-003, T-007

## DEFERRED
- T-002 — /openup-sync-spec (defer-until: drift observed in practice after T-001 lands)

## ⚠ COLLISIONS
- T-008 (in-progress) touches docs/changes/ and .claude/skills/openup-workflow/; T-002 (deferred, not in collision set) shares those prefixes but is excluded — no active collision.
  (No two collision-set tasks overlap: T-008 is the only member.)

## Roadmap-only (no change folder yet)
Human view from docs/roadmap.md — NOT authoritative frontmatter.
- T-009 — Worktree-per-task + lease claims   status=planned, depends-on=[T-005, T-008]  → BLOCKED on T-008 (in-progress, not done; T-005 ✅)
- T-010 — Graded tracks (quick/standard/full)   status=planned, depends-on=[T-005, T-006]  → READY (T-005 ✅, T-006 ✅)
- T-011 — Retro cadence trigger + /openup-create-handoff   status=planned, depends-on=[T-005]  → READY (T-005 ✅)
```

Reading: T-008 is the actionable in-progress task; T-009 is blocked on T-008 (not yet
done); T-010 and T-011 are roadmap-ready because their only deps (T-005/T-006) are
completed — they will surface in **READY** once they get change folders. T-002 stays
deferred. No active collisions because only one task (T-008) is in the collision set.

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Task missing from report | No `plan.md` frontmatter | Check it has a change folder; roadmap-only tasks go in the last section |
| Wrong READY/BLOCKED call | Used roadmap status for an authoritative task | Frontmatter wins; roadmap is only for folderless tasks |
| Spurious collision | Substring match, not path-prefix | A prefix must end at a `/` boundary or be the whole segment |
| Promoted a `blocked` task | Ignored declared status | `status == blocked` is always BLOCKED |

## References

- Schema: `docs-eng-process/coordination-frontmatter.md`
- Field sketch: `docs/plans/2026-06-10-process-v2-claude-code-harness.md` §WS5

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) — picks the next task; readiness feeds it
- [openup-complete-task](../complete-task/SKILL.md) — flips `status` that this skill reads

# Coordination Frontmatter (WS5a)

Every change-folder `plan.md` carries YAML frontmatter that declares **machine-readable
coordination state**: where the task sits in the dependency DAG, what surface it touches,
and whether it is claimed. This is what `/openup-readiness` parses to answer "what is
READY, what is BLOCKED and why, which READY tasks would collide" without reading prose.

The frontmatter is the **authoritative** source of task status; `docs/roadmap.md` is the
human-readable view (generated/synced via `scripts/sync-status.py`).

## Field set

| Key | Type | Meaning |
|---|---|---|
| `status` | enum (below) | Lifecycle state of the task. |
| `depends-on` | list of ids | Tasks that must reach `done`/`verified` before this is READY. `[]` if none. |
| `blocks` | list of ids | Tasks this one blocks (the inverse edge; informational, for DAG cross-checks). `[]` if none. |
| `touches` | list of path prefixes | Declared collision surface — directories/files this task modifies. Used for `/openup-readiness` overlap detection. |
| `claimed-by` | string \| `null` | Session id that has claimed the task. `null` when unclaimed. **Read-only in T-008; written/enforced in T-009.** |
| `claimed-at` | ISO-8601 \| `null` | Lease timestamp; a claim is stale after 24h. `null` when unclaimed. **Written in T-009.** |
| `worktree` | string \| `null` | Path of the per-task git worktree, e.g. `../repo-T-008`. `null` until created. **Written in T-009.** |

These join the existing identity/metadata fields already on every `plan.md`: `id`,
`title`, `priority`, `estimate`, `plan` (program-plan anchor), and on completed tasks
`completed`.

## Key-naming convention — hyphens, not underscores

Coordination keys use **hyphens**: `depends-on`, `claimed-by`, `claimed-at`. Single-word
keys (`touches`, `worktree`, `status`, `blocks`) need no separator.

**Why.** The shipped change files (`T-002`, archived `T-007`) already used `depends-on`
and `blocks`. The WS5a sketch in the program plan illustrated `depends_on`/`claimed_by`
with underscores, but that was illustrative. Standardising on hyphens matches what already
ships and avoids a migration churn across existing folders. The `/openup-readiness` reader
expects hyphenated keys.

## Status enum

```
proposed → ready → in-progress → done → verified
```

- `proposed` — spec drafted, not yet rubric-passed/committed-to.
- `ready` — rubric-passed, dependencies expected to clear; eligible to start.
- `in-progress` — actively being worked.
- `done` — work complete; satisfies downstream `depends-on`.
- `verified` — done **and** independently checked (tester); also satisfies `depends-on`.

Plus one **tolerated** non-pipeline value:

- `deferred` — intentionally not being worked (e.g. YAGNI until a trigger fires). It is a
  distinct non-actionable state, **not an error**. `/openup-readiness` reports it in its
  own section and never treats it as READY/BLOCKED. A `deferred` task may carry an
  optional `defer-until:` note describing the un-defer trigger (see `T-002`).

A task may also self-declare `status: blocked` — `/openup-readiness` keeps it BLOCKED even
if its dependencies now resolve (the author asserted the block; it is surfaced, not
silently promoted).

## Minimum-required set

The required fields differ for active vs archived tasks, to avoid claim-field noise on
work that is already finished.

**Active tasks** (`docs/changes/T-NNN/plan.md` — status `proposed`/`ready`/`in-progress`/
`deferred`): the full coordination set.

```yaml
status: in-progress
depends-on: [T-007]      # [] if none
blocks: [T-009]          # [] if none
touches:                 # declared collision surface
  - docs/changes/
  - .claude/skills/openup-workflow/
claimed-by: null
claimed-at: null
worktree: null
```

`touches` should be present whenever the modified surface is knowable from the plan; omit
only when genuinely unknowable. `claimed-by`/`claimed-at`/`worktree` are `null` until
T-009's claim mechanism writes them.

**Archived tasks** (`docs/changes/archive/T-NNN/plan.md` — `done`/`verified`): the
**minimum** is the DAG-relevant fields only —

```yaml
status: done
completed: 2026-06-11
depends-on: []           # [] if none
blocks: [T-008]          # [] if none
```

Archived done/verified tasks **do not** carry `claimed-by`/`claimed-at`/`worktree` — a
finished task is never claimed, and the null triple is pure noise in the archive. They
**may** omit `touches` (collision detection only considers READY/in-progress tasks, never
archived ones, so a completed task's surface is irrelevant). `status` and
`depends-on`/`blocks` must be present and internally consistent so the DAG resolves
correctly when a downstream task names them as a dependency.

## Source of truth

- **Authoritative:** change-folder `plan.md` frontmatter. `/openup-readiness` resolves
  READY/BLOCKED from these.
- **Human view:** the `docs/roadmap.md` task table. Tasks that have a roadmap row but **no
  change folder yet** (e.g. T-009/T-010/T-011 before they are picked up) are reported by
  `/openup-readiness` in a separate "Roadmap-only (no change folder yet)" section, clearly
  marked as non-authoritative. Once such a task gets a change folder, its frontmatter
  becomes authoritative and it leaves that section.

## Claims (forward reference)

The `claimed-by` / `claimed-at` / `worktree` fields are **defined** here so the schema is
stable, but T-008 only *reads* `claimed-by` (to surface ownership in the collision
section). Writing and enforcing claims — worktree-per-task, lease files under
`.git/openup/claims/T-NNN.json`, stale-lease expiry, collision pre-flight refusal — is
**T-009 (WS5c)**. See `docs/plans/2026-06-10-process-v2-claude-code-harness.md` §WS5.

## See also

- `/openup-readiness` skill — `.claude/skills/openup-workflow/readiness/SKILL.md`
- Change-folder layout — `docs/changes/README.md`
- Program plan — `docs/plans/2026-06-10-process-v2-claude-code-harness.md` §WS5

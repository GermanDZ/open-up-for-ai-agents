# T-008 — Design Decisions (in-flight)

Decisions made during execution that the spec (`plan.md`) did not fully pin down.

## D1 — Minimum frontmatter set for archived (done/verified) tasks

The spec said "archived/done tasks need not carry claim fields if that adds noise —
document the minimum required set" but left the exact set to the implementer.

**Decided:** archived `done`/`verified` plans carry **only** the DAG-relevant fields:
`status`, `completed`, `depends-on`, `blocks`. They do **not** carry
`claimed-by`/`claimed-at`/`worktree` (a finished task is never claimed; the null triple is
pure archive noise) and **may omit `touches`** (collision detection considers only
READY/in-progress tasks, never archived ones). T-001/T-003/T-007 already matched this set,
so **no edits were made to the archived plans** — they were already consistent.

Rationale: keeps the archive clean and avoids retrofitting claim fields onto work that
predates the schema. Documented in `coordination-frontmatter.md` § "Minimum-required set".

## D2 — Collision path-prefix algorithm

The spec said "share a path prefix" without specifying matching semantics.

**Decided:** prefix match is on **path-segment boundaries**, not raw substring. After
normalising (strip leading `./`, treat directory-looking entries as ending in `/`), two
paths collide iff one is a prefix of the other ending at a `/` boundary or being the whole
segment. So `docs/changes/` collides with `docs/changes/T-002/`, but `docs/changes/` does
NOT collide with `docs/changesets/`. Identical paths collide. Documented in the skill
(step 4) with examples and in the Common Errors table.

## D3 — Collision set membership

The spec (Design Decision #5) says collisions are flagged "among READY tasks (and any
in-progress task)". 

**Decided:** the collision set is exactly READY ∪ IN-PROGRESS. `deferred`, `proposed`
(if blocked), `done`, `verified`, and BLOCKED tasks are excluded. Consequence in current
state: T-002 (deferred) and T-008 (in-progress) both touch
`.claude/skills/openup-workflow/`, but no collision is flagged because T-002 is deferred.
This is the intended scope — a deferred task isn't competing for the surface.

## D4 — `status: blocked` is sticky

The READY/BLOCKED rule in the spec keys off `depends-on` resolution. A task could in
principle declare `status: blocked` while its deps actually resolve.

**Decided:** a self-declared `status: blocked` stays BLOCKED regardless of dep state —
the author asserted the block, so the reader surfaces it (reason: "status declared
blocked") rather than silently promoting it to READY. Documented in skill step 3.

## D5 — Roadmap-only tasks reported with derived READY/BLOCKED

The spec required listing folderless roadmap tasks (T-009/T-010/T-011) under a
"Roadmap-only" section using the roadmap's status/depends-on, "clearly marked as the human
view, not authoritative frontmatter."

**Decided:** within that section we still annotate each with a derived READY/BLOCKED call
(using the roadmap deps) for PM usefulness, but the section header explicitly states it is
non-authoritative. The dependency *reasoning* in the acceptance check is satisfied here;
these tasks move into the authoritative READY/BLOCKED buckets once they get a change
folder.

## D6 — `touches` chosen for T-002

T-002 (`/openup-sync-spec`) had no `touches`. From its plan it adds a skill and modifies
artifact templates, so `touches: [.claude/skills/openup-workflow/, docs-eng-process/templates/]`.
Claim fields set to `null` (active task, per minimum set in D1). Status kept `deferred`.

## D7 — Template sync is MANUAL

`check-claude-sync.sh` is a CLI script, not wired into any hook in `.claude/settings.json`
(verified). So mirroring `.claude/skills/openup-workflow/readiness/` into
`docs-eng-process/.claude-templates/skills/openup-readiness/` was done manually via
`scripts/check-claude-sync.sh --fix-from-live`. The template tree uses a **flat** naming
convention (`skills/openup-readiness/`), while live uses nested
(`skills/openup-workflow/readiness/`) — the sync script maps between them.

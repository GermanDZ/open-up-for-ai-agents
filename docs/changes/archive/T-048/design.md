# T-048 — In-flight design decisions

## DD0 — Req 1 was already partly delivered by T-042
`/openup-complete-task`'s archive step **already flips** the spec's `status:` to
`done` before `git mv`-ing the change folder to `docs/changes/archive/` (added by
T-042, iteration 19). So the core of Req 1 ("archived plan reads satisfied") is met
in *this* framework repo. The downstream audit that seeded T-048 ran against a
pre-T-042 adopted copy. What's left for Req 1 is the **track-aware refinement** the
requirement spells out: write `verified` for a rubric-graded `full`-track completion,
else `done` (the assumption on plan.md:64). Implemented in DD4.

## DD1 — `dep_satisfied`: archived plans defer to the roadmap, active plans stay authoritative
The bug: `find_task_plan` rglob's `docs/changes/**/plan.md` (archive included) and
`dep_satisfied` trusts the found plan's body `status:`, only consulting the roadmap
when **no** plan is found. A stale archived body (`in-progress`, or a `deferred` plan
later completed) therefore false-blocks a genuinely-done dependency.

Fix: when the found plan is **archived** AND its body status is non-satisfied, fall
through to the roadmap (the human view of record) instead of returning `False`
immediately. An **active** (non-archived) plan keeps its body authoritative — an
`in-progress` *live* spec really is unmet, so we must not override it.

**Rejected: blind "archive presence ⇒ satisfied".** `docs/changes/archive/T-002/`
exists with body `status: deferred`. Archive presence alone is too weak — only a
**roadmap-completed** row flips an archived stale plan. If an archived plan has *no*
roadmap row at all, we keep trusting the (non-satisfied) body rather than guess.
(T-002's roadmap row *does* say `completed (2026-06-11)`, so it is a genuine stale
archived plan — see DD3 / the migration repairs it.)

## DD2 — `is_archived_plan(plan_path, root)` helper
Path-segment test: the plan's path relative to `docs/changes/` has first segment
`archive`. Reused by `dep_satisfied`.

## DD3 — Migration lives on `openup-claims.py` (`migrate-archived-status`)
Placed here, not on `openup-state.py`, to **reuse** `roadmap_status`,
`parse_frontmatter`, and `SATISFIED_DEP_STATUSES` (no duplication). It bumps only
archived plans that are **stale** (body non-satisfied) **and roadmap-completed** —
the exact same predicate as DD1, so the two fixes can never disagree. Leaves
`deferred`/`cancelled` (roadmap not completed) untouched. `--dry-run`, `--repo-root`
(hermetic tests), idempotent (a second run changes zero). In *this* repo it repairs
exactly **T-002** (`deferred` body, `completed` roadmap).

## DD4 — complete-task status flip is track-aware
Single python block reads `.openup/state.json` `track`; writes `verified` on `full`,
else `done`. `verified` truthfully signals the rubric ran (full track only). Both are
in `SATISFIED_DEP_STATUSES`, so dependency resolution is unaffected by the choice.

## DD5 — Bug B: start-iteration commits the spec on promote
`.openup/` is gitignored (`/.openup/`, Ring 3 ephemeral) — so the board-visible
artifact is the **spec folder** `docs/changes/{task_id}/`, not `state.json`. A new
step 6c in `/openup-start-iteration` commits the spec (+ any roadmap row) right after
the claim is written, so the lane survives in git and `openup-board.py` (which reads
the working tree / a clean checkout) can see it from trunk or another worktree. The
gitignored live `state.json` is intentionally *not* committed — "persisted state" is
satisfied by the committed spec.

## Completion verification (step 1a/1b)
- **Req 1** ✅ — `complete-task/SKILL.md` archive flip writes a satisfied status,
  track-aware (`verified` on `full`, else `done`). Core flip pre-existed (T-042).
- **Req 2** ✅ — `openup-claims.py` `dep_satisfied` + `is_archived_plan`; real-data
  check: `preflight --depends-on T-002` now READY (was blocked on `deferred`); 4 tests.
- **Req 3** ✅ — `migrate-archived-status` subcommand; ran on this repo (T-002
  `deferred`→`done`); 2nd run = 0 changes (idempotent); 2 tests.
- **Req 4** ✅ — `start-iteration/SKILL.md` step 6c commits the spec folder on promote
  (`.openup/` is gitignored, so the committed spec is the durable board-visible record).
- **Success Measures**: `n/a` — internal process/tooling fix; success is the binary
  Verification (zero false dep-blocks, zero invisible-promote recoveries). No instrumentation.
- Tests: 42/42 claims suite green; full suite 259/260 (1 pre-existing macOS `/private/var`
  path-symlink fail in `test_docs_index`, unrelated).

## Canonical tree
`.claude/` is **generated**; `docs-eng-process/.claude-templates/` is the canonical
source (`scripts/sync-templates-to-claude.sh` syncs templates → `.claude`). All skill
edits land in `.claude-templates/` first, then sync regenerates `.claude/`.
`scripts/openup-claims.py` is single-sourced (no template copy).

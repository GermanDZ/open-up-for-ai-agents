# T-049 — Design decisions & completion grade

## Design decisions

- **DD0 — Lease as the lane source, not a new registry.** The lease already lives
  in the shared `--git-common-dir` and is read by `collider_for`; the board just
  never treated it as a *lane* source. So the fix is "synthesize a lane from an
  orphan lease," not a new cross-tree registry. Cheapest correct change, all data
  already local.

- **DD1 — New `elsewhere` state, not reuse of `in-progress`.** `in-progress` means
  "plan is local and leased." An orphan lease has no local plan, so it gets a
  distinct `elsewhere` state — keeps `in-progress` semantics intact and makes the
  board legible (a trunk reader sees *where* the work is, not a phantom local lane).

- **DD2 — `classify`/`is_pickable` left untouched.** Orphan lanes set `state`
  directly in `orphan_lease_lane`; `classify` is only called for plan-derived
  lanes. `is_pickable` already gates on `state == "ready"`, so `elsewhere` is
  non-pickable for free. Minimal surface; no risk to existing classification.

- **DD3 — Routing parity preserved.** Before T-049, an elsewhere task was invisible
  from trunk → empty board → "no active lanes" → `/openup-next` §1c promote. After
  T-049 the lane is visible, so `none_pickable_reason` must STILL route an
  elsewhere-only board to promote (new "no active local lanes …" message). The
  empty-board message is byte-unchanged (existing test pins it). The real new value
  is (a) visibility in `refresh`, and (b) the §1c skip-leased guard — NOT a routing
  change.

- **DD4 — Re-promote trap fixed in the consumer (§1c), not the board.** The board
  surfaces the lease; the loop decides not to re-author. §1c gains a mechanical
  skip-filter "pending task that holds a live lease," so independent pending work
  still promotes while the in-flight task does not get re-specced into a collision.

- **DD5 — Corrupt leases excluded.** A `_corrupt` lease is already surfaced
  fail-closed as a collider; rendering it as a workable `elsewhere` lane would be
  misleading. Only well-formed orphan leases become lanes.

- **DD6 — Skill edit lands in the canonical template tree only.** `.claude/` is
  gitignored and synced from `docs-eng-process/.claude-templates/`; the committed
  change is the template. (`touches` lists `.claude/skills/openup-next/` as an
  allowed superset; it carries no diff.)

## Completion verification — requirements graded against the diff (step 1a)

- ✅ **Req 1** (orphan lease → non-pickable `elsewhere` lane w/ branch+worktree) —
  `orphan_lease_lane` + `build_board` sweep (`scripts/openup-board.py`); covered by
  `test_orphan_lease_becomes_elsewhere_lane`, `test_elsewhere_lane_is_never_pickable`.
  Live: branch board vs `--root main` shows `T-049 -> elsewhere`, `top` does not pick it.
- ✅ **Req 2** (collision parity) — `collider_for` unchanged; orphan sweep runs after
  plan lanes. `test_collision_parity_with_orphan_lease`, `test_leased_plan_not_duplicated_as_orphan`.
- ✅ **Req 3** (reason routing local vs elsewhere-only) — rewritten
  `none_pickable_reason`; `test_reason_elsewhere_only_is_promote_eligible`,
  `test_reason_local_blocked_still_stops`, `test_empty_board_message_unchanged`.
- ✅ **Req 4** (§1c skip-leased; independent work still promotes; template mirror) —
  §1b reason form + §1c skip-filter in
  `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md`. Stated as a
  mechanical selection filter (skip-for-mechanical-reason), not prose scope.

Tests: board suite 23/23 green (was 16); claims suite 36/36 green (no regression).

## Success measures / instrumentation (step 1b)

`n/a` per spec `## Success Measures` — internal tooling fix; read-back signal is the
non-recurrence of board-blindness / re-promote collisions in a future session audit.

## Rollout (step 4a)

`n/a` per spec `## Rollout` — not flagged (corrective, safe-on, additive). No
flag-removal row to enqueue.

---
id: T-147
task-id: T-147
title: Fence allowlist omits the two `.claude/memory/` files every completion writes
status: ready   # proposed → ready → in-progress → done → verified
priority: low   # critical | high | medium | low
estimate: 0.5 session
track: standard
touches:
  - scripts/openup-fence.py
  - scripts/tests/test_openup_fence.py
  - docs-eng-process/parallel-lanes.md
depends-on: []
blocks: []
last-synced: ""
---

# T-147 — Fence allowlist omits the two `.claude/memory/` files every completion writes

## Story

> **As a** developer working an OpenUP lane in a project that tracks `.claude/`
> **I want** `openup-fence.py` to treat the two framework-written `.claude/memory/`
> files as lane-owned audit surfaces
> **So that** completing a task does not report `OUT OF LANE` for files I never
> chose to edit and cannot avoid writing.

INVEST check:
✅ Independent (no deps) · ✅ Negotiable (files vs directory is open) · ✅ Valuable
(removes a per-lane workaround measured live downstream) · ✅ Estimable (one
constant + tests + one doc line) · ✅ Small · ✅ Testable (fence tests build
throwaway repos, so the defect is reproducible here despite `.claude/` being
gitignored).

## Analysis Context

- **Domain.** The write-fence (`scripts/openup-fence.py`, T-024) — the deterministic
  guardrail that a lane's committed diff stays inside its claimed surface. Specifically
  its `ALWAYS_ALLOWED` constant, the "lane-owned / append-only surfaces" category.

- **Why the framework repo cannot see this.** `.gitignore:38` is `/.claude/*`, so this
  repo tracks nothing under `.claude/` and the fence never sees those paths. The defect
  is real but **structurally invisible here** — it reproduces only in a project that
  tracks `.claude/`, which is why it arrived as a downstream hand-off finding (FD-003)
  rather than as a local failure.

- **Premise verified before drafting** (measured 2026-07-27 in
  `/Users/germandz/personal-code/kaze/kaze-webapp`, read-only sibling consumer):
  - Both files are **tracked** there: `.claude/memory/bypass-log.md` (596 lines) and
    `.claude/memory/iteration-learnings.md` (279 lines) — actively appended, not stubs.
  - Its `scripts/openup-fence.py` is byte-identical in the relevant region: the same
    three-entry `ALWAYS_ALLOWED`.
  - The workaround is **in use and costly**: `grep -rl '\.claude/memory' docs/changes/`
    returns **8 of 37 archived lanes** that hand-declared these paths in plan frontmatter
    `touches` purely to get past the fence. `openup-fence.py allowed --task-id T-048`
    there prints `.claude/memory/bypass-log.md` and `.claude/memory/iteration-learnings.md`
    in the allowlist **only** because that lane declared them.
  - `docs/framework-defects.md` §FD-003 records the observation (T-048, 2026-07-26,
    severity medium, "blocks `/openup-complete-task` for every task, every track, until
    worked around").

- **Neither file is per-lane opt-in.** `.claude/memory/bypass-log.md` is appended by three
  hooks (`gate-edits.py:159`, `check-iteration.py:94`, `validate-commit.py:87`);
  `.claude/memory/iteration-learnings.md` is appended by `openup-scribe.py:83`, which
  `/openup-complete-task` step 6 runs as a **mandatory** step on every track. A lane
  cannot avoid writing them, so requiring it to *claim* them is asking it to declare a
  surface it did not choose.

- **The framework already half-agrees with itself.** `on-stop.py:54` carries
  `EXEMPT_DIRTY_PREFIXES = ("docs/agent-logs/runs/", ".claude/memory/bypass-log.md")` —
  one component already classifies this path as a lane-agnostic auto-written surface
  alongside the run log. The fence simply never got the same entry. This is an internal
  inconsistency being closed, not a new policy.

- **Scope boundaries.** Fence allowlist only. **Not** in scope: a `merge=union`
  `.gitattributes` entry for these two files. They are *shared* append-only files (every
  lane appends to the same file), unlike the *sharded* `docs/agent-logs/` and
  `docs/status-notes/` trees where each lane owns its own file — so allowlisting them
  admits a genuine local merge-collision risk that `docs/agent-logs/runs/*.jsonl
  merge=union` already solves for the run log. That is a real, separate question about
  merge resolution, not lane surface, and it cannot be exercised in this repo at all
  (nothing under `.claude/` is tracked). Recorded in `design.md` and carried to the
  roadmap rather than silently bundled.

- **Definition of done.** `build_allowlist()` returns both paths for any task without
  the task declaring them; the module docstring and `docs-eng-process/parallel-lanes.md`
  name them in the lane-owned category; tests prove both that the paths pass and that
  the fence still blocks a genuinely out-of-lane `.claude/` file.

> **Assumption:** allowlist the **two explicit file paths**, not the `.claude/memory/`
> directory prefix. The two files are exactly what framework mechanisms write; a
> directory prefix would additionally exempt anything else a consumer project chooses to
> keep under `.claude/memory/` (project notes, scratch context), which is a lane-surface
> question the fence should still ask. This also matches the roadmap entry's wording
> ("Add both paths"). *(Vetoable at review — the counter-argument is that the other three
> allowlist entries are all directory prefixes, so files read as inconsistent.)*

> **Assumption:** the fix ships in `scripts/openup-fence.py` only; downstream projects
> receive it through their existing `sync-from-framework.sh` / `process-manifest.txt`
> path (`scripts/process-manifest.txt:19` already lists `openup-fence.py`). No consumer
> repo is modified from this lane — sibling repos are read-only evidence.
> *(Vetoable at review.)*

**Ambiguity gate:** no blocking questions. Both open questions above are non-blocking
(a default is reasonable, and being wrong costs one constant edit).

## Requirements

1. `build_allowlist()` includes `.claude/memory/bypass-log.md` and
   `.claude/memory/iteration-learnings.md` for **every** task, with no `touches`
   declaration required.
   - **Given** a lane whose plan frontmatter `touches` does not mention `.claude/`
     **When** the lane commits a change to `.claude/memory/iteration-learnings.md` and
     `openup-fence.py check` runs **Then** it exits `0` and the file is not reported
     `OUT OF LANE`.
   - **Given** the same lane **When** `openup-fence.py allowed` runs **Then** both paths
     appear in the printed `allowed` array.

2. The exemption is scoped to those two files — a different tracked file under
   `.claude/` is still fenced.
   - **Given** a lane that has not declared `.claude/` in `touches` **When** it commits
     `.claude/settings.json` **Then** `openup-fence.py check` exits `8` and names that
     file `OUT OF LANE`.
   - **Given** the same lane **When** it commits `.claude/memory/scratch-notes.md`
     **Then** the fence exits `8` and names it `OUT OF LANE` (the directory is not
     blanket-exempt — this is the assumption above made failable).

3. The existing fence contracts are unchanged: view freshness, the quick-track unfenced
   path, stamped `base_sha` resolution, and genuine out-of-lane detection all behave
   exactly as before.
   - **Given** the pre-existing `scripts/tests/test_openup_fence.py` suite **When** it
     runs after the change **Then** every previously-passing case still passes with no
     assertion weakened or deleted.

4. The documented allowlist matches the code in both places that state it.
   - **Given** `scripts/openup-fence.py`'s module docstring and
     `docs-eng-process/parallel-lanes.md` (the lane-owned class-1 row and the "Allowed
     for task `T-NNN`" list) **When** a reader compares them to `ALWAYS_ALLOWED` **Then**
     the two `.claude/memory/` files are named in all three, with the reason (written by
     non-opt-in mechanisms) stated once.

## Behavior Delta

Ring 1 for this repo is `docs/product/`, which holds only `milestones/` — no use case or
product artifact describes the write-fence, so there is no Ring-1 artifact to
back-propagate to. The fence's user-facing contract lives in `docs-eng-process/`
(process docs), updated by requirement 4.

**Added**
- Two paths are permanently in the fence's lane-owned allowlist for every task.

**Modified**
- `n/a` — no Ring-1 (`docs/product/`) artifact describes fence behavior.

**Removed**
- The *practice* of hand-declaring `.claude/memory/*` in a lane's `touches` becomes
  unnecessary. Not a Ring-1 removal — no artifact prescribes it; it was a workaround
  recorded in `docs/framework-defects.md` §FD-003 downstream.

## Entities

- **`ALWAYS_ALLOWED`** (modified) — `scripts/openup-fence.py:78`
- **`build_allowlist()`** (read-only) — `scripts/openup-fence.py:197`, consumes the constant
- **Fence module docstring** (modified) — `scripts/openup-fence.py:18-20`
- **Lane-class table + allowed-list** (modified) — `docs-eng-process/parallel-lanes.md:58,92-93`
- **`FenceRepo` test harness** (read-only) — `scripts/tests/test_openup_fence.py:42`
- **`.claude/memory/bypass-log.md`** (read-only, not tracked here) — written by
  `gate-edits.py` / `check-iteration.py` / `validate-commit.py`
- **`.claude/memory/iteration-learnings.md`** (read-only, not tracked here) — written by
  `openup-scribe.py learnings`

## Approach

Add the two paths to `ALWAYS_ALLOWED` with a comment naming *why* they belong to the
category (written by mechanisms no lane opts into) and *why they are files, not a
directory prefix* — so the next reader does not "simplify" them into `.claude/memory/`
and silently widen the exemption. Everything downstream (`build_allowlist`, `is_allowed`,
the segment-prefix match) already generalizes over the constant, so no logic changes.
The real work is the test that makes the narrow scope failable, plus aligning the two
prose statements of the allowlist with the code.

## Structure

**Add:**
- (no new files)

**Modify:**
- `scripts/openup-fence.py` — two entries in `ALWAYS_ALLOWED` + the comment above it;
  the module docstring's lane-owned bullet.
- `scripts/tests/test_openup_fence.py` — new cases for requirements 1 and 2.
- `docs-eng-process/parallel-lanes.md` — the class-1 lane-owned row and the
  "Allowed for task `T-NNN`" bullet list.

**Do not touch:**
- `.gitattributes` — the `merge=union` question for these two shared append-only files
  is real but separate (merge resolution ≠ lane surface) and unexercisable here; carried
  to the roadmap instead.
- `scripts/openup-claims.py` — the claim pre-flight's `touches` semantics are unchanged;
  a lane that *declares* these paths keeps working exactly as it does today.
- `docs-eng-process/.claude-templates/scripts/hooks/on-stop.py` — its
  `EXEMPT_DIRTY_PREFIXES` is a different mechanism (dirty-tree tolerance at session stop)
  that already covers `bypass-log.md`; widening it to `iteration-learnings.md` is not
  this task's finding and has no downstream evidence.
- Any file in `/Users/germandz/personal-code/kaze/kaze-webapp` — read-only evidence.

## Operations

- [x] Add both `.claude/memory/` paths to `ALWAYS_ALLOWED` in `scripts/openup-fence.py`
      with the why-files-not-directory comment, and update the module docstring's
      lane-owned bullet.
- [x] (tester) Add fence tests: both paths pass without a `touches` declaration; `allowed`
      lists them; `.claude/settings.json` and `.claude/memory/scratch-notes.md` still
      exit 8 as `OUT OF LANE`.
- [x] Run the full fence suite plus the whole `scripts/tests/` suite; confirm no
      pre-existing assertion changed.
- [x] Verify the fix bites: revert the constant edit, confirm the new tests fail and only
      they fail, restore, confirm green (record the observed output in `design.md`).
- [x] Update `docs-eng-process/parallel-lanes.md` (class-1 row + allowed list) to name the
      two files and state the reason once.
- [x] Record in `design.md`: the files-vs-directory decision, the deferred
      `.gitattributes merge=union` question, and the kaze-webapp baseline measurement.
- [x] Reserve an id for the deferred `.gitattributes merge=union` question
      (`openup-claims.py reserve-id`) and write the ready-to-file roadmap entry into
      `design.md`, to be appended to `docs/roadmap.md` at `/openup-complete-task` time —
      the roadmap is a fenced shared view, so a mid-lane edit would trip the stale-view
      rule rather than land cleanly.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, pre-commit housekeeping)
- `docs-eng-process/parallel-lanes.md` — the lane-surface model this task edits
- `.claude/CLAUDE.openup.md` — token-efficiency protocol, fix-spec-first, legal exits
- `docs-eng-process/tracks.md` — `standard` track ceremony

## Safeguards

- **Token / size budget.** Code change ≤ ~10 lines; whole lane ≤ 0.5 session.
- **Reversibility.** Single constant edit; reverting the commit fully restores prior
  behavior. No state, no migration, no flag.
- **No-go zones.**
  - The exemption must **not** become a directory prefix without an explicit review
    decision — a test asserts the narrow scope so this cannot be widened silently.
  - Do not weaken or delete any existing fence assertion to make a new test pass.
  - No sibling repo is written to; kaze-webapp is evidence only.
  - The fence must still exit `8` for genuinely out-of-lane files (requirement 3).
- **Invariant.** `openup-fence.py` and `openup-claims.py` must keep agreeing on path
  matching — the shared `claims.seg_prefix_collide` import stays the only matcher.

## Success Measures

We expect the number of **new** kaze-webapp lanes that must hand-declare
`.claude/memory/*` in plan frontmatter `touches` to drop from a baseline of
**8 of 37 archived lanes** (measured 2026-07-27) to **0 of the first 3 lanes completed
after the sync**. Instrumentation: `grep -rl '\.claude/memory' docs/changes/` run in
kaze-webapp, compared against the archived-lane count.
**Read-back environment: `/Users/germandz/personal-code/kaze/kaze-webapp`** — a
downstream consumer, read-only from here. The instrument was **verified to exist and
return data there on 2026-07-27** (it returned the 8 paths above), so a later `0` is
distinguishable from "not measurable" — the T-052 failure mode this rule exists to
prevent.
**Read-back:** after kaze-webapp next runs `sync-from-framework.sh` (open action item
`86.4`, on the kaze lead's schedule — this lane cannot trigger it) **plus 3 completed
lanes**. If that sync has not happened within 90 days, the read-back is reported as
*not yet readable* rather than as a pass.

Secondary check, readable in this repo immediately: `openup-fence.py allowed --task-id
<any>` prints both paths without any `touches` declaration.

## Rollout

**Flagged? No.** `ALWAYS_ALLOWED` is a module-level constant read at import time by a
short-lived CLI process; a flag would add a branch and a config read to a guardrail whose
entire value is being deterministic and identical for humans (`pre-push`) and agents
(`/openup-complete-task`). Changing what the fence permits is strictly *widening* — no
previously-passing lane can start failing — so the backout is the revert, not a toggle.

Reaches users by two paths: this repo picks it up at merge; downstream consumers on their
next `sync-from-framework.sh` (`scripts/process-manifest.txt` already ships
`openup-fence.py`). No flag-removal follow-up is owed since no flag is introduced.

## Verification

- `python3 -m pytest scripts/tests/test_openup_fence.py -q` — all cases green, including
  the new ones for requirements 1 and 2.
- `python3 -m pytest scripts/tests/ -q` — full suite green, no regression against the
  946-green baseline.
- Bite check (Operations step 4): with the constant edit reverted, exactly the new tests
  fail; restored, all green. Observed output recorded in `design.md`.
- `python3 scripts/openup-fence.py allowed --task-id T-147` prints both `.claude/memory/`
  paths.
- `git diff` shows no pre-existing assertion modified in `test_openup_fence.py`.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or an explicit
  gap call-out.

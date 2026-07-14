---
id: T-112
title: New `/openup-cycle` skill — lower-ceremony deterministic-first pick/resume entry point
status: ready
priority: medium
estimate: 1 session
plan: docs/iteration-plans/t-112-openup-cycle-skill.md
depends-on: []
blocks: []
touches:
  - docs-eng-process/procedures/openup-cycle.md
  - docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md
  - docs-eng-process/skills-guide.md
  - docs-eng-process/model-tiers.md
  - docs/iteration-plans/t-112-openup-cycle-skill.md
  - docs/roadmap.md
last-synced: ""
---

# T-112 — New `/openup-cycle` skill — lower-ceremony deterministic-first pick/resume entry point

## Story

> **As a** solo practitioner driving OpenUP delivery through Claude Code
> **I want** a cycle entry point that pays self-brief/role-hat ceremony only on
> genuinely judgment-shaped Operations steps, mirroring the box-classification
> discipline the headless `cycle.py` engine already proved
> **So that** lanes with a high proportion of mechanical script steps complete
> with less redundant context-loading, without weakening any safety check or
> touching the proven `/openup-next` path

INVEST check:
✅ Independent (new procedure file, no dependency on unmerged work) · ✅ Negotiable
(box-classification wording, routing message phrasing) · ✅ Valuable (real token/ceremony
reduction on script-heavy lanes, dogfooded by this repo's own delivery loop) ·
✅ Estimable (one procedure file + generated mirrors) · ✅ Small (single skill,
no code changes) · ✅ Testable (classification fidelity + gate/exit contract are
checkable against `cycle.py`'s own logic and existing gates)

## Analysis Context

- **Domain.** The Claude Code skill layer (`docs-eng-process/procedures/`), the
  deterministic board/gate scripts it composes (`openup-board.py`,
  `openup-fence.py`, `check-docs.py`), and the existing `/openup-next` skill this
  is an addition alongside, not a replacement for.
- **Scope boundaries.** No changes to any `scripts/*.py` file (this task ships a
  procedure doc + its generated mirrors only). No changes to
  `docs-eng-process/procedures/openup-next.md`. Does not implement
  `plan-iteration` / `assess-iteration` / `milestone-review` / consent-gated
  replenishment — those `resolve()` paths route to `/openup-next` by name.
- **Definition of done.** `docs-eng-process/procedures/openup-cycle.md` exists
  with valid frontmatter and a body implementing resolve → route → claim (incl.
  the `resumable_input` fold) → box loop (classify → execute → gate → tick) →
  exit through the two legal exits; mirrors regenerated; discoverable as
  `/openup-cycle`; classification verified against `cycle.py`'s real
  `classify_box` on real archived plans; `openup-next.md` byte-unchanged.

**Assumption:** the procedure's `fit: poor` list names `/openup-next` explicitly
by slash-command rather than describing the situation abstractly — the point is
a legible handoff between the two skills. *(Vetoable at review.)*

**Assumption:** the classification-fidelity check (Requirement 2) is a one-time
manual verification recorded in `design.md`, not a new automated test script —
this task ships no `scripts/*.py` code, so there is no natural home for one yet.
*(Vetoable at review — if `/openup-cycle` sees real use and the rule drifts from
`cycle.py`'s, that is the trigger to build a shared-source check.)*

## Requirements

1. `/openup-cycle` handles only the `pick`/`resume` `resolve()` paths; every
   other path routes to `/openup-next` by name instead of being re-derived.
   - **Given** `openup-board.py resolve` returns a path in `{plan-iteration,
     assess-iteration, milestone-review, noop}`, **When** `/openup-cycle` is
     invoked, **Then** it prints a routing message naming `/openup-next` and the
     decision's `reason`, attempts no claim or box work, and emits
     `OPENUP-NEXT: DONE — routed to /openup-next (<path>)`.

2. Operations boxes are classified script-vs-judgment using the same rule
   `cycle.py`'s `classify_box`/`extract_command` encode, and only judgment boxes
   trigger self-brief.
   - **Given** an Operations box whose body contains a backtick span starting
     with `python3 ` or `git `, or a bare `` `scripts/<name>.py ...` `` span, or
     (absent a marker override) the first `python3 .../git ...` token to end of
     line, **When** `/openup-cycle` classifies it, **Then** it is a script step:
     the command runs directly via Bash with no role-file/Ring-1/Ring-2 read.
   - **Given** an Operations box with no extractable command and no `(auto)`
     marker, **When** classified, **Then** it is a judgment step: the agent
     self-briefs (the role file's `## On Start, Read` block for the box's
     `(role)` tag, default `developer`) before doing the work.

3. Every box (script or judgment) is gated before its checkbox is ticked.
   - **Given** a box has just been executed, **When** `/openup-cycle` checks
     gates, **Then** it runs `python3 scripts/openup-fence.py check` (exit 3
     treated as inapplicable/skip) and `python3 scripts/check-docs.py`.
   - **Given** either gate fails with a non-skip exit code, **When** the gate
     check completes, **Then** the box's `- [ ]` line stays unticked and the
     cycle stops, reporting the gate output — no further boxes are attempted.

4. Claim and completion delegate to the existing skills unchanged — no
   reimplementation, no third exit.
   - **Given** `resolve()` returns `pick`, **When** `/openup-cycle` claims the
     lane, **Then** it runs `/openup-start-iteration task_id: <lane.task> track:
     <lane.track or auto>` unchanged (collision preflight, worktree/lease,
     remote duplicate-start check stay single-sourced there).
   - **Given** every Operations box in the lane's `plan.md` is ticked, **When**
     `/openup-cycle` exits, **Then** it runs `/openup-complete-task task_id:
     <task>` — never a raw commit, never any other exit.

5. A `resume` carrying an answered input-request folds the answer into the spec
   first (fix-spec-first), matching `/openup-next`'s behavior rather than
   `cycle.py`'s driver-only shortcut.
   - **Given** `resolve()` returns `resume` with `resumable_input` set, **When**
     `/openup-cycle` handles the claim step, **Then** it re-runs
     `/openup-create-task-spec task_id: <task>` so the answer lands in
     `docs/changes/<task>/plan.md` through the rubric, removes the
     `awaiting-input:` frontmatter line, and archives the request — all before
     entering the box loop.

6. `/openup-next` is preserved exactly as-is.
   - **Given** T-112 is complete, **When** `git diff -- docs-eng-process/procedures/openup-next.md`
     is run, **Then** it produces no output.

## Behavior Delta

`n/a — all Added`. This task adds a new, additional skill; it does not modify
any existing documented product behavior (Requirement 6 explicitly verifies
`/openup-next` is untouched, and no Ring-1 artifact describes the skill
inventory in a way this addition would contradict).

## Entities

- **`openup-cycle` procedure** (new) — `docs-eng-process/procedures/openup-cycle.md`
- **`openup-cycle` skill mirror** (new, generated) — `docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md`
- **`openup-cycle` local skill copy** (new, generated, gitignored) — `.claude/skills/openup-cycle/SKILL.md`
- **Skills guide** (modified, generated) — `docs-eng-process/skills-guide.md`
- **`openup-next` procedure** (read-only, verified unchanged) — `docs-eng-process/procedures/openup-next.md`
- **`cycle.py` classification logic** (read-only reference) — `scripts/openup_agent/cycle.py:254-279` (`extract_command`/`classify_box`)

## Approach

`/openup-cycle` is authored as a new procedure in the neutral pack and rendered
through the existing adapter pipeline (`render-skills-mirror.py`,
`sync-templates-to-claude.sh`) — no new tooling. Its body inlines `cycle.py`'s
proven box-classification and gate-before-tick discipline as explicit Claude
Code instructions, while delegating claim (`/openup-start-iteration`) and
completion (`/openup-complete-task` / `/openup-create-handoff`) to the existing
skills unchanged — the safety-critical machinery (collision preflight, lease,
rubric, the two-legal-exits rule) stays single-sourced there. It only owns the
`pick`/`resume` decision paths; every other `resolve()` path routes to
`/openup-next` by name, which already has full precedence-path parity. This
ships zero script code — a pure procedure-pack addition plus its generated
mirrors.

## Structure

**Add:**
- `docs-eng-process/procedures/openup-cycle.md`

**Modify (generated — regenerated by their own scripts, never hand-edited):**
- `docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md` — via `render-skills-mirror.py --write`
- `.claude/skills/openup-cycle/SKILL.md` — via `sync-templates-to-claude.sh` (gitignored)
- `docs-eng-process/skills-guide.md` — via `check-skills-guide.py --write`

**Do not touch:**
- `docs-eng-process/procedures/openup-next.md` — explicitly preserved unchanged (the user's ask)
- `scripts/openup_agent/cycle.py` / any `scripts/*.py` — this task ships no code, only a procedure doc that references the existing scripts

## Operations

- [x] (developer) Author `docs-eng-process/procedures/openup-cycle.md` per the design in `docs/iteration-plans/t-112-openup-cycle-skill.md` — frontmatter (name, description, `tier: reasoning`, capabilities, `fit` routing every non-pick/resume path to `/openup-next` by name) + full body (resolve → route → claim incl. `resumable_input` fold → box loop with script/judgment classification → gate-before-tick → tick → exit through the two legal exits).
- [x] `python3 scripts/render-skills-mirror.py --write`
- [x] `scripts/sync-templates-to-claude.sh`
- [x] `python3 scripts/check-skills-guide.py --write`
- [x] (tester) Verify classification fidelity: run `cycle.py`'s `classify_box`/`extract_command` against the Operations boxes of at least 5 archived `docs/changes/archive/T-*/plan.md` files and confirm the procedure's written classification rule produces the identical script/judgment split for each box; record the comparison in `docs/changes/T-112/design.md`.
- [x] `git diff -- docs-eng-process/procedures/openup-next.md`
- [x] `python3 scripts/render-skills-mirror.py --check && python3 scripts/check-skills-guide.py --check && python3 scripts/check-model-tiers.py && python3 scripts/check-docs.py`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/procedure-frontmatter.md` — the neutral procedure frontmatter contract this new file must satisfy
- `docs-eng-process/skills-guide.md` — generated pipeline this task's mirror regeneration feeds

## Safeguards

- **Token / size budget.** The procedure body stays scoped to the `pick`/`resume`
  paths only — no re-derivation of `plan-iteration`/`assess`/`milestone`/replenish
  logic. A short body for the common case is the whole value proposition; if it
  grows to `/openup-next`-length, the design has failed its own goal.
- **Reversibility.** Deleting `docs-eng-process/procedures/openup-cycle.md` and
  re-running `render-skills-mirror.py --write` + `sync-templates-to-claude.sh` +
  `check-skills-guide.py --write` fully reverts — no other repo state is coupled
  to this skill's existence.
- **No-go zones.** Never edit `docs-eng-process/procedures/openup-next.md`. Never
  hand-edit the generated mirror or skills guide (only via their generators).
  `/openup-cycle` must never exit through anything other than
  `/openup-complete-task` or `/openup-create-handoff` — introducing a third exit
  violates a hard project rule (`CLAUDE.openup.md` Critical Rules).

## Verification

- `python3 scripts/render-skills-mirror.py --check`
- `python3 scripts/check-skills-guide.py --check`
- `python3 scripts/check-model-tiers.py`
- `python3 scripts/check-docs.py`
- `git diff -- docs-eng-process/procedures/openup-next.md` — must be empty
- Classification-fidelity spot check recorded in `docs/changes/T-112/design.md`
- Grade against `.claude/rubrics/task-spec-rubric.md` (this spec) and manual dry
  run against a real lane before declaring the skill usable

## Success Measures

We expect the first 5 real `/openup-cycle` invocations in this repo's own
delivery loop to each report **zero** role-file/Ring-1/Ring-2 self-brief reads
on every script-classified box in their mandated Output summary (a magnitude
of exactly 0 self-brief reads per script box, vs. `/openup-next`'s current
unconditional per-cycle self-brief regardless of box kind). Instrumentation:
the procedure's own `## Output` section (`docs-eng-process/procedures/openup-cycle.md`)
mandates reporting "how many boxes ran as script steps vs. judgment steps" in
every invocation's printed summary — this is real instrumentation that exists
in this task's diff, not a claim requiring new logging infrastructure. (An
earlier draft of this measure proposed grepping `docs/agent-logs/` for
per-tool-call `read_file` records — checked at completion time and found
false: `docs/agent-logs/` records only session-level events (`session_begin`,
`task_completed`, …), not individual tool calls, so that instrumentation does
not exist. Revised to point at instrumentation that is actually in the diff.)
Read-back: after the 5th real `/openup-cycle` invocation, whenever that
occurs, by reading the printed summaries.

## Rollout

**Flagged?** No. A new skill is inherently opt-in — nothing invokes it
automatically, and no existing call site is being rewired to point at it
(`/openup-next` stays the default; Requirement 6 verifies it). There is no
existing behavior at risk that a feature flag would mitigate. If it needs to be
walked back, delete the procedure file and regenerate the mirrors (see
Safeguards → Reversibility) — that is a complete, immediate removal, so no
flag-removal follow-up is needed.

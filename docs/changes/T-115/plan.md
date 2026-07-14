---
id: T-115
title: "Queryable Development Case archetype default + track/archetype disambiguation"
status: ready
priority: medium
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-bootstrap-overhead-fixes.md
depends-on: []
blocks: []
touches:
  - scripts/check-docs.py
  - scripts/tests/test_check_docs.py
  - docs-eng-process/project-config.md
  - docs-eng-process/tracks.md
  - docs-eng-process/procedures/openup-init.md
  - docs-eng-process/.claude-templates/skills/openup-init/SKILL.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-115 — Queryable Development Case archetype default + track/archetype disambiguation

## Story

> **As an** agent bootstrapping or tailoring a project's Development Case
> **I want** one command that answers "what applies when `docs/project-config.yaml`
> is absent" and clear language distinguishing the Development Case
> **archetype** from the unrelated ceremony **track**
> **So that** I stop hunting through prose across multiple docs to answer a
> question the data already has an answer for — 4 chained grep/search calls
> observed live for exactly this question

INVEST check:
✅ Independent (one new CLI flag + doc disambiguation, no dependency) ·
✅ Negotiable (exact flag name/output shape) · ✅ Valuable (evidenced live: 4
chained searches for one answer) · ✅ Estimable (one script flag + a test +
two doc edits) · ✅ Small · ✅ Testable (hermetic CLI test)

## Analysis Context

- **Domain.** `scripts/check-docs.py` (where `PROCESS_ARCHETYPE_DEFAULTS`
  already lives and `resolve_process()` already consumes it),
  `docs-eng-process/project-config.md` and `docs-eng-process/tracks.md` (the
  two docs whose overlapping "quick" terminology caused the live conflation),
  and `docs-eng-process/procedures/openup-init.md` (which currently asserts
  "framework defaults apply" without saying what that means).
- **Scope boundaries.** Does not change what happens when `process:` is
  absent (today: no archetype tailoring at all — confirmed by research: no
  code path resolves an implicit archetype). This task only makes that fact
  **queryable and documented**, not different. Does not rename or restructure
  the existing `quick`/`standard`/`full` ceremony-track system or the
  `quick`/`mvp`/`product` archetype system — disambiguates them in prose,
  does not unify or rename either.
- **Definition of done.** `check-docs.py --show-archetype-defaults` prints,
  in one call, both (a) what applies when `docs/project-config.yaml`/`process:`
  is absent, and (b) each archetype's resolved defaults — the exact question
  the live session spent 4 tool calls answering. `project-config.md` and
  `tracks.md` each name the other concept where "quick" is first introduced.
  `openup-init.md` points at the new flag instead of the unexplained
  "framework defaults apply" assertion.

**Assumption:** the accessor lives on `check-docs.py` (where
`PROCESS_ARCHETYPE_DEFAULTS` already is) rather than a new flag on
`openup-process-map.py` or `openup-doctor.py` — avoids duplicating the dict
across files, and `check-docs.py` already has the `resolve_process()` logic
this flag reuses. *(Vetoable at review — the exploration's open question left
this genuinely open; `openup-doctor.py` was the other credible candidate
since it already aggregates read-only project health info, but it would have
to import from `check-docs.py` anyway, so the dict's actual home is the more
natural place to expose it.)*

## Requirements

1. `check-docs.py --show-archetype-defaults` answers "what applies when
   `docs/project-config.yaml` is absent" directly, without running the doc
   validator.
   - **Given** no other flags, **When**
     `python3 scripts/check-docs.py --show-archetype-defaults` runs, **Then**
     it prints (as JSON) a `default_when_absent` field stating that no
     archetype tailoring applies when `process:` is absent, distinct from the
     unrelated ceremony track, and exits 0 without attempting to load or
     validate any `docs/` tree.

2. The same command also surfaces each archetype's resolved defaults, so a
   project deciding whether to opt in can see the choices in one call.
   - **Given** the same invocation, **When** its output is inspected, **Then**
     it includes an `archetypes` field containing `PROCESS_ARCHETYPE_DEFAULTS`
     for `quick`, `mvp`, and `product` (the same dict `resolve_process()`
     already uses — not a duplicated copy).

3. `project-config.md` and `tracks.md` each name the other concept explicitly
   where "quick" is first introduced.
   - **Given** a reader opens `docs-eng-process/project-config.md`'s `process:`
     section, **When** they reach its first mention of the `quick` archetype,
     **Then** a sentence names `tracks.md`'s unrelated `quick` ceremony track
     and says the two are different axes. **Given** a reader opens
     `docs-eng-process/tracks.md`, **When** they reach its first mention of
     the `quick` track, **Then** a parallel sentence names
     `project-config.md`'s unrelated `quick` archetype.

4. `openup-init.md` points at the new accessor instead of an unexplained
   assertion.
   - **Given** `openup-init.md`'s "Project Config" subsection, **When** it
     states that leaving `process:` commented means "framework defaults
     apply," **Then** it also names
     `check-docs.py --show-archetype-defaults` as the command that shows
     exactly what that means.

## Behavior Delta

`n/a — all Added`. Adds a read-only query command and clarifying prose; does
not change what applies when `process:` is absent (confirmed unchanged by
Requirement 1's own wording) or how `resolve_process()` behaves for an
explicit archetype.

## Entities

- **`check-docs.py` CLI** (modified) — new `--show-archetype-defaults` flag
- **`PROCESS_ARCHETYPE_DEFAULTS`** (read-only, reused not duplicated) —
  `scripts/check-docs.py`
- **`scripts/tests/test_check_docs.py`** (modified) — new hermetic test class
- **`docs-eng-process/project-config.md`** (modified) — disambiguation sentence
- **`docs-eng-process/tracks.md`** (modified) — disambiguation sentence
- **`docs-eng-process/procedures/openup-init.md`** (modified) — points at the accessor
- **`docs-eng-process/script-cli-reference.md`** (modified) — new flag documented

## Approach

Add one `store_true` flag, `--show-archetype-defaults`, to `check-docs.py`'s
existing `argparse` parser (`main()`, `scripts/check-docs.py:646+`). When set,
short-circuit before any docs-dir/schema loading: print a JSON object with
`default_when_absent` (a fixed, accurate string) and `archetypes` (a direct
reference to `PROCESS_ARCHETYPE_DEFAULTS`, so it can never drift from what
`resolve_process()` actually uses), then exit 0. No new data, no new parsing
— purely exposing what's already computed. Pair it with two one-sentence doc
edits (disambiguation) and one `openup-init.md` pointer update.

## Structure

**Modify:**
- `scripts/check-docs.py` — new `--show-archetype-defaults` flag in `main()`
- `scripts/tests/test_check_docs.py` — new test class covering the flag
- `docs-eng-process/project-config.md` — disambiguation sentence
- `docs-eng-process/tracks.md` — disambiguation sentence
- `docs-eng-process/procedures/openup-init.md` — points at the new flag
- `docs-eng-process/.claude-templates/skills/openup-init/SKILL.md` — regenerated mirror
- `docs-eng-process/script-cli-reference.md` — documents the new flag

**Do not touch:**
- `PROCESS_ARCHETYPE_DEFAULTS`'s actual values — this task exposes them, does
  not change them
- `docs-eng-process/procedures/openup-next.md` — no-go zone, unaffected anyway
- `scripts/openup-process-map.py` / `scripts/openup-doctor.py` — considered
  and rejected as the accessor's home (see Assumption)

## Operations

- [ ] (developer) Add `--show-archetype-defaults` to `check-docs.py`'s `main()`: short-circuits before docs-dir/schema loading, prints `{"default_when_absent": "...", "archetypes": PROCESS_ARCHETYPE_DEFAULTS}` as JSON, exits 0.
- [ ] (tester) Add a hermetic test class to `scripts/tests/test_check_docs.py` asserting the flag's exit code, JSON shape, and that `archetypes` matches `PROCESS_ARCHETYPE_DEFAULTS` for all three archetype names.
- [ ] `python3 -m unittest scripts.tests.test_check_docs -v 2>&1 | tail -30`
- [ ] (developer) Add the disambiguation sentence to `docs-eng-process/project-config.md`'s `process:` section and `docs-eng-process/tracks.md`'s track table, each naming the other.
- [ ] (developer) Update `openup-init.md`'s "Project Config" subsection to name `check-docs.py --show-archetype-defaults`, and add the same flag's entry to `docs-eng-process/script-cli-reference.md`.
- [ ] `python3 scripts/render-skills-mirror.py --write && scripts/sync-templates-to-claude.sh && python3 scripts/check-skills-guide.py --write && python3 scripts/check-model-tiers.py --write`
- [ ] `git diff harness-optional -- docs-eng-process/procedures/openup-next.md`
- [ ] `python3 scripts/render-skills-mirror.py --check && python3 scripts/check-skills-guide.py --check && python3 scripts/check-model-tiers.py --check && python3 scripts/check-docs.py`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, Pre-Commit Housekeeping (T-116)
- `docs-eng-process/script-cli-reference.md` — the CLI documentation convention this task extends

## Safeguards

- **Token / size budget.** One new flag (~10-15 lines), one test class
  (~30-40 lines), two one-sentence doc edits, one pointer update. No
  refactor of `resolve_process()` or `PROCESS_ARCHETYPE_DEFAULTS`.
- **Reversibility.** Revert the flag, its test, and the four doc edits;
  nothing else depends on this.
- **No-go zones.** `PROCESS_ARCHETYPE_DEFAULTS`'s values must not change —
  this task exposes, it doesn't retune. The new flag must not load or
  validate a `docs/` tree (it answers a question independent of any specific
  project's docs).

## Verification

- `python3 -m unittest scripts.tests.test_check_docs -v`
- `python3 scripts/check-docs.py --show-archetype-defaults` manually inspected
  for the expected JSON shape
- `python3 scripts/render-skills-mirror.py --check`
- `python3 scripts/check-skills-guide.py --check`
- `python3 scripts/check-model-tiers.py --check`
- `python3 scripts/check-docs.py`
- `git diff harness-optional -- docs-eng-process/procedures/openup-next.md` — must be empty

## Success Measures

We expect the next agent that needs to answer "what's the default archetype
when `docs/project-config.yaml` is absent" to resolve it in **exactly 1**
tool call (`check-docs.py --show-archetype-defaults`), vs. the 4 chained
grep/search calls observed live in the T-002 bootstrap transcript this task
is fixing. Instrumentation: a re-read of the next such session's tool-call
sequence (the same method used to find the original gap). Read-back: the
next time an agent needs this answer, whenever that occurs (this repo's own
delivery loop is the only consumer).

## Rollout

**Flagged?** No — a new read-only CLI flag with no runtime toggle; nothing
to roll back except reverting the flag itself. Not applicable in the
feature-flag sense.

---
id: T-100
title: Process-map schema — per-activity requires_input + execution mode
status: done
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-deterministic-process-map-navigation.md
depends-on: []
blocks: [T-101, T-102, T-103]
touches:
  - docs-eng-process/process-map.yaml
  - scripts/openup-process-map.py
  - scripts/tests/test_openup_process_map.py
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-100 — Process-map schema: per-activity `requires_input` + `execution` mode

## Story

> **As** the deterministic navigation layer (P1),
> **I want** the process map to declare, per activity, **which human input it
>   needs** and **how it executes** (run its procedure directly vs author a lane
>   spec first),
> **So that** the cycle can drive navigation and input-requests from **data**
>   instead of the hardcoded Inception bootstrap (T-097/T-098) — the foundation
>   the rest of P1 (T-101/T-102/T-103) builds on.

INVEST — ✅ Independent (schema + parser only; no engine change) · ✅ Negotiable (single vs list input; field names) · ✅ Valuable (unblocks the whole P1 program) · ✅ Estimable · ✅ Small (parser recursion + validate + data) · ✅ Testable (new hermetic parser tests)

## Analysis Context

- **Domain.** The process map (`docs-eng-process/process-map.yaml`) + its
  stdlib reader (`scripts/openup-process-map.py`, T-077). Today an activity is a
  flow-map `{ role, skills }`; the reader's `_parse_flow_map` stores a nested
  `{...}` value as a raw string (no recursion) and a `[...]` value as a list.
  `validate` checks role/skills; `activities_for`/`activity` expose `{name, role,
  skills}`.
- **Scope boundaries.** This task adds the **schema + parser + validation +
  shipped data** only — it changes **no engine behavior** (the cycle,
  Plan Iteration, resolve are untouched; T-101/T-102 consume these fields).
  `requires_input` is a **single** optional map per activity (the real need — an
  authoring activity reads one human artifact); multiple inputs is a documented
  future extension, not built here.
- **Definition of done.** An activity may declare
  `requires_input: { path, describe }` and `execution: direct | spec-then-execute`
  (default `spec-then-execute`); the reader parses and exposes them;
  `openup-process-map.py validate` hard-gates them; the shipped map declares them
  for the inception/elaboration authoring activities; `openup-process-map.py
  activity <name> --json` returns the enriched record.

> **Assumption:** `requires_input` is one map per activity (not a list). Multiple
> declared inputs is deferred (documented). *(Vetoable at review.)*
> **Assumption:** `execution` default is `spec-then-execute` (today's behavior),
> so activities without the field are unchanged. *(Vetoable.)*

## Requirements

1. **The reader parses a nested `requires_input` map and an `execution` scalar.**
   - **Given** `activities.initiate-project = { role: analyst, skills:
     [openup-create-vision], requires_input: { path: docs/inputs/stakeholder-brief.md,
     describe: "a stakeholder brief" }, execution: direct }`, **When** `load_map`
     runs, **Then** the activity record carries `requires_input` as a dict
     `{path, describe}` and `execution` as `"direct"` (nested `{...}` values are
     recursively parsed, not stored as raw strings).

2. **`activities_for` and `activity` expose the new fields.**
   - **Given** the map above, **When** `openup-process-map.py activity
     initiate-project --json` runs, **Then** the JSON includes `requires_input`
     and `execution` alongside `name/role/skills`; an activity without the fields
     reports `requires_input: null` and `execution: "spec-then-execute"`.

3. **`validate` hard-gates the new fields.**
   - **Given** an activity whose `requires_input` lacks a `path`, or whose
     `execution` is not one of `direct`/`spec-then-execute`, or whose
     `execution: direct` activity has ≠1 skill/procedure, **When**
     `openup-process-map.py validate` runs, **Then** it reports a problem and
     exits non-zero; a well-formed map exits 0.

4. **The shipped map declares inputs + execution for authoring activities.**
   - **Given** the shipped `process-map.yaml`, **When** read, **Then**
     `initiate-project` declares `requires_input` = the stakeholder brief and
     `execution: direct`, and it passes `validate`; activities that take no human
     input and produce work via a lane keep the default (`spec-then-execute`, no
     `requires_input`).

5. **Backward compatibility — an activity without the new fields is unchanged.**
   - **Given** an activity `{ role, skills }` with neither field, **When** parsed
     and queried, **Then** its behavior is byte-equivalent to pre-T-100 (role +
     skills exposed; `requires_input` absent/null; `execution` defaults).

## Behavior Delta

Ring-1 truth for the driver/process lives in `docs-eng-process/`.

**Added:**
- Optional per-activity `requires_input: { path, describe }` and
  `execution: direct | spec-then-execute` in the process-map schema, parsed +
  validated + exposed by `openup-process-map.py`.

**Modified:**
- The shipped `process-map.yaml` — `docs-eng-process/script-cli-reference.md`
  (process-map section): authoring activities now declare their input + execution
  mode.

**Removed:** none (purely additive; defaults preserve current behavior).

## Entities

- **process map** (modified) — `docs-eng-process/process-map.yaml`
- **reader** (modified) — `scripts/openup-process-map.py` (`_parse_flow_map`
  recursion, `activities_for`/`activity` fields, `validate`)
- **tests** (new) — `scripts/tests/test_openup_process_map.py`

## Approach

Make `_parse_flow_map` recurse: a value starting with `{` is parsed as a nested
flow-map (so `requires_input` resolves to a dict), a `[` value stays a list, else
a scalar. `activities_for`/`activity` include `requires_input` (dict or None) and
`execution` (default `spec-then-execute`). `validate` adds the three gates
(input has a `path`; `execution` in the enum; `direct` ⇒ exactly one skill).
Populate the shipped map's authoring activities. Add the first hermetic test file
for the reader.

## Structure

**Add:**
- `scripts/tests/test_openup_process_map.py` — parse (nested map + execution),
  query (fields exposed + defaults), validate (each gate), backward-compat.

**Modify:**
- `scripts/openup-process-map.py` — `_parse_flow_map` recursion; `activities_for`
  + `activity` emit `requires_input`/`execution`; `validate` gates.
- `docs-eng-process/process-map.yaml` — declare `requires_input` + `execution` on
  `initiate-project` (and any other authoring activity that clearly reads a human
  artifact); leave the rest defaulted.
- `docs-eng-process/script-cli-reference.md` — document the two new fields + the
  enriched `activity --json`.

**Do not touch:**
- `openup-board.py` / `plan_iteration.py` / `cycle.py` / `navigator.py` — no
  engine consumes the fields yet (T-101/T-102 do). Purely the schema layer.
- `mint-iteration-id` / `phase_letters` — unrelated.

## Operations

- [x] Extend `_parse_flow_map` in `openup-process-map.py` to recurse on nested
  `{...}` values (so `requires_input` parses to a dict).
- [x] Have `activities_for` + `activity` emit `requires_input` (dict|None) and
  `execution` (default `spec-then-execute`); extend `validate` with the three
  gates (input `path` present; `execution` enum; `direct` ⇒ 1 skill).
- [x] Declare `requires_input` (stakeholder brief) + `execution: direct` on
  `initiate-project` in `process-map.yaml`; confirm `validate` passes.
- [x] (tester) Add `scripts/tests/test_openup_process_map.py` covering Req 1–5.
- [x] Document the new fields in `docs-eng-process/script-cli-reference.md`.
- [x] (tester) Reader tests green; `python3 scripts/openup-process-map.py
  validate` exit 0; `check-docs`, `spec-scenarios`, fence
  (`--base harness-optional`) green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format
- `scripts/openup-process-map.py` module docstring — the map contract (T-077)
- `docs/iteration-plans/2026-07-14-deterministic-process-map-navigation.md` — the
  P1 program this is the foundation of

## Safeguards

- **Backward compatibility.** Additive fields with behavior-preserving defaults;
  an activity without them is unchanged (Req 5).
- **Validation is a hard gate** (the T-099 "LLM/hand-authored data must validate"
  lesson) — a malformed `requires_input`/`execution` fails `validate`.
- **No-go zones.** No engine behavior change; consumers land in T-101/T-102.
- **Stdlib-only** (the reader stays pyyaml-free).

## Success Measures

n/a — internal schema foundation. Falsifiable acceptance = the hermetic reader
tests (Req 1–5) + `openup-process-map.py validate` green on the shipped map. The
program-level measure (zero per-cycle navigator calls) is read back at T-103.

## Rollout

`n/a — not user-facing`: framework-internal process data; no flag. Backout is a
version pin.

## Verification

- `python3 -m pytest scripts/tests/test_openup_process_map.py -q` — green.
- `python3 scripts/openup-process-map.py activity initiate-project --json` shows
  `requires_input` + `execution: direct`; `validate` exits 0; a malformed fixture
  exits non-zero.
- `openup-spec-scenarios.py check docs/changes/T-100/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

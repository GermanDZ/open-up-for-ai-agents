---
id: T-121
title: "Cycle-engine + tool bug sweep (B1–B7)"
status: ready
priority: high
estimate: 1 session
plan: docs/roadmap.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup_agent/tools.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_agent_tools.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
---

# T-121 — Cycle-engine + tool bug sweep (B1–B7)

## Story

> **As a** weak local model (or a human) driving the reference cycle engine
> **I want** the six-tool surface and the box executor to fail safe on hostile
> or unusual input, and completion to never strand a delivered lane
> **So that** a single bad tool arg, a prose-mentioned command, a wrapped
> checkbox, or a merge conflict doesn't crash the driver, misfire a step, or
> lose finished work

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** Seven concrete defects found in the 2026-07-16 orchestration-economics
  review (`docs/explorations/2026-07-16-cycle-orchestration-economics.md`, B1–B7).
  All in `tools.py` (the six-tool surface) and `cycle.py` (the box executor +
  deterministic completion). Each is small and independent; grouped as one
  correctness sweep.
- **Scope boundaries.** Correctness/robustness only — no contextualization
  change (that was T-120), no gate-frequency change (that is T-123), no
  process-gate change (B8–B9 are T-122). No new tool is added; the six-tool
  surface and its dispatch contract are unchanged in shape.
- **Definition of done.** Each of B1–B7 has a fix and a hermetic test proving
  the failure no longer occurs, with no regression to the existing tool/executor
  behavior.

## Requirements

1. **B1 — `grep` ignores VCS/vendor noise and skips oversized files.** The
   default `grep` walk must not read `.git/`, common vendor/build trees, or
   files above a size cap.
   - **Given** a repo with a matching line inside `.git/` and a matching line in
     a tracked source file **When** `grep(pattern)` runs with the default path
     **Then** the source-file match is returned and the `.git/` match is not.
   - **Given** a file larger than the per-file size cap **When** `grep` runs
     **Then** that file is skipped (not decoded line-by-line).

2. **B2 — `exec` with a `cwd` escaping the root returns an error, never crashes.**
   - **Given** `exec(command="git status", cwd="..")` **When** dispatched
     **Then** the result is an `ERROR:` string reporting the escape and the
     driver does not raise (dispatch returns a string).

3. **B3 — Operations-box classification is prose-safe.** A box whose prose only
   *mentions* a backticked command is a judgment step, not a script step.
   - **Given** a box `- [ ] (analyst) use `+"`git log`"+` to review history`
     **When** classified **Then** the kind is `judgment` (no command extracted).
   - **Given** a command-first box `- [ ] python3 scripts/x.py --flag` **When**
     classified **Then** the kind is `script` with that exact command (no
     regression).
   - **Given** an explicit `- [ ] (auto) `+"`git tag`"+`` box **When** classified
     **Then** the kind is `script` (the marker still forces it; no regression).

4. **B4 — Wrapped judgment-box bodies are preserved.** A continuation line of a
   wrapped Operations checkbox is retained in that box's body.
   - **Given** an Operations box whose text wraps onto a second indented line
     **When** `parse_boxes` runs **Then** the parsed box `body` contains the
     continuation text (not only the first line).

5. **B5 — A completion merge failure does not strand the lane.** When the
   `complete()` merge back to base fails, the base is left clean, the completed
   lane stays reachable, and a re-run finishes the merge instead of re-planning.
   - **Given** `complete()` reaches step 10 and the `--no-ff` merge fails **When**
     it handles the failure **Then** the merge is aborted (base is not left
     half-merged), the task branch is checked out, a `pending_merge` marker is
     recorded in `.openup/cycle.json`, and a distinct non-zero exit is returned.
   - **Given** a recorded `pending_merge` on the next cycle **When** the recovery
     pre-pass runs **Then** it retries the merge (and clears the marker on
     success) before any plan-iteration.

6. **B6 — `read_file` marks truncation.** A whole-file read over the byte cap
   ends with an explicit marker naming the path.
   - **Given** a file larger than the read byte cap **When** `read_file(path)` is
     called with no offset/limit **Then** the returned text ends with a marker
     that states truncation and names the path.

7. **B7 — `exec` output is capped.** Combined stdout/stderr over a cap is
   truncated with a marker; the `exit=` line is preserved.
   - **Given** an allowlisted command whose combined output exceeds the cap
     **When** `exec` returns **Then** the result begins with the `exit=<code>`
     line and the body is truncated with an explicit marker.

## Behavior Delta

**Modified** — `tools.py`: `grep` (ignore set + size/binary skip), `exec` (catch
`ToolError` from `cwd` resolution; cap output), `read_file` (truncation marker),
`dispatch` (catch `ToolError`). `cycle.py`: `extract_command`/`classify_box`
(command-first, not match-anywhere), `parse_boxes` (retain continuation lines),
`complete()` (clean, recoverable merge-fail) + the recovery pre-pass
(`pending_merge` retry). Ring-1 driver doc: a note in
`docs-eng-process/reference-driver.md` on the hardened tool + classification
behavior.

**Added** — a `pending_merge` key in the cycle meta (`.openup/cycle.json`).
**Removed** — the match-anywhere command heuristic (superseded by command-first).

## Entities

- **Tool surface** (modified) — `scripts/openup_agent/tools.py`: `grep`, `exec`,
  `read_file`, `dispatch`, plus the byte/output caps.
- **Box executor + completion** (modified) — `scripts/openup_agent/cycle.py`:
  `extract_command`, `classify_box`, `parse_boxes`, `complete`, and the recovery
  pre-pass in `_run_cycle_inner`.

## Approach

Each fix is local and additive:
- **B1** `grep`: skip a default ignore set (`.git`, `node_modules`, `vendor`,
  `.venv`, `__pycache__`, `dist`, `build`, `tmp`, `log`, `storage`) and any file
  over a size cap; keep the 500-hit cap and the invalid-regex error.
- **B2** `exec`: move the `cwd` `_resolve` inside the try/return-string path, and
  broaden `dispatch` to catch `ToolError` (→ `ERROR:` string) as well as
  `TypeError`.
- **B3** classification: `extract_command` returns a command only when the
  stripped body **starts** with `python3 `/`git `, or **is** a single
  backtick span wrapping such a command (or a `scripts/*.py` span). A backtick
  span mid-prose no longer matches. `(auto)` still forces script; `(judgment)`
  still forces judgment.
- **B4** `parse_boxes`: a non-checkbox, non-heading line inside `## Operations`
  with a current box appends (space-joined) to that box's `body`; blank lines
  are skipped.
- **B5** `complete()`: on merge failure, `git merge --abort`, `git checkout
  <branch>`, `_write_cycle_meta(..., pending_merge=branch)`, return the distinct
  exit. The recovery pre-pass reads `pending_merge`, retries `git checkout base
  && git merge --no-ff branch`, clears it on success, before resolve/plan.
- **B6** `read_file`: when the whole-file read is truncated at `_MAX_READ_BYTES`,
  append `\n… [truncated at N bytes — full file at <path>]`.
- **B7** `exec`: cap the combined output at a constant; if exceeded, keep the
  `exit=` line and append a truncation marker.

## Structure

**Modify:**
- `scripts/openup_agent/tools.py` — B1, B2, B6, B7 + the caps/ignore constants.
- `scripts/openup_agent/cycle.py` — B3, B4, B5 + recovery `pending_merge` retry.
- `scripts/tests/test_openup_agent_tools.py` — grep ignore/size, exec cwd-escape,
  read_file marker, exec output cap.
- `scripts/tests/test_openup_agent_cycle.py` — prose-vs-command classification,
  wrapped-box body, merge-fail clean+recover.
- `docs-eng-process/reference-driver.md` — hardened-behavior note.

**Do not touch:** the execution seam / sub-run mechanics, stamping, the process
map, `task-library.yaml`, the gates, and the fence (B8–B9 are T-122).

## Operations

- [ ] B1 — `grep` default-ignores `.git`/vendor/build trees and skips over-cap files; keep 500-hit + invalid-regex behavior.
- [ ] B2 — `exec` cwd-escape returns an `ERROR:` string (dispatch catches `ToolError`); no uncaught crash.
- [ ] B3 — command-first classification in `extract_command`; prose backtick mentions are judgment; `(auto)`/`(judgment)`/command-first still work.
- [ ] B4 — `parse_boxes` retains wrapped continuation lines in the box body.
- [ ] B5 — merge-fail in `complete()` aborts cleanly, returns to the branch, records `pending_merge`; recovery pre-pass retries it before planning.
- [ ] B6 — `read_file` whole-file truncation appends a path-named marker.
- [ ] B7 — `exec` caps combined output with a marker; preserves the `exit=` line.
- [ ] (tester) Hermetic tests for B1–B7 (each failure no longer occurs; no regression to existing tool/executor tests).

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-072 tool-surface contract (the six tools this hardens)
- T-089 box executor + T-091/T-108 completion (the paths B3–B5 touch)

## Safeguards

- **No behavior change to the happy path.** Command-first boxes, valid tool
  args, small files, and a clean merge all behave exactly as before — every fix
  is a guard on a failure mode.
- **No new tool, no dispatch-shape change.** The six-tool surface and its
  `DISPATCH_TOOL_NAMES` are unchanged; only their internals harden.
- **Reversibility.** Each bug's fix is independent; reverting one does not affect
  the others.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_tools.py scripts/tests/test_openup_agent_cycle.py -q` passes.
- Full suite green; fence `--base harness-optional` clean; `check-docs` clean.

## Success Measures

n/a — internal correctness sweep on harness-optional; the falsifiable check is
the seven hermetic regression tests (each reproduces the pre-fix failure and
asserts the post-fix behavior). No runtime metric or flag.

## Rollout

n/a — internal driver hardening on harness-optional; no flag, no user-facing
runtime surface.

---
id: T-134
title: "Code-artifact task-def probe (Option D) — can the driver write AND run real code?"
status: ready
priority: medium
estimate: 1 session
plan: docs/iteration-plans/t-134-code-artifact-task-def-probe.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/task-library.yaml
  - scripts/openup-process-map.py
  - scripts/openup_agent/tools.py
  - scripts/openup_agent/probe_task.py
  - scripts/probe-code-artifact.py
  - scripts/bench-scenarios/code-probe/
  - scripts/tests/test_openup_process_map.py
  - scripts/tests/test_openup_agent_tools.py
  - docs/iteration-plans/t-134-code-artifact-task-def-probe.md
---

# T-134 — Code-artifact task-def probe (Option D): can the driver write AND run real code?

## Story

> **As an** owner deciding whether to invest in a full Rails 8 + PostgreSQL
>   Construction PoC driven by a cheap hosted model
> **I want** one narrow, falsifiable data point on whether that model can
>   reliably write *and execute* real code through the driver's existing tool
>   surface
> **So that** the much larger investment (new artifact type, multi-file task
>   shape, widened `exec` allowlist) is made with evidence, not extrapolation
>   from a markdown-only result

INVEST check:
✅ Independent — additive: one new task-def, one schema exemption, one exec
allowlist entry, one new standalone runner. No dependency on unmerged work.
✅ Negotiable — the exact task-def content (Ruby vs. another minimal
language) and runner shape are explicitly open (Open Questions), not fixed.
✅ Valuable — answers a real, falsifiable question before a much larger
investment; a "no" result is exactly as valuable as a "yes" here.
✅ Estimable — every touched function/pattern was read and confirmed working
this session (see Current State citations); 1 session.
✅ Small — no change to `process-map.yaml`'s live activity wiring; no new
subsystem.
✅ Testable — deterministic schema/allowlist tests plus one live, falsifiable
probe run with a concrete pass/fail bar.

## Analysis Context

- **Domain.** The reference driver's task-def / `direct`-execution mechanism
  (T-104–T-106) and its `exec` tool surface (`scripts/openup_agent/tools.py`).
  This task adds one narrowly-scoped exception to each — a new non-spine
  `artifact: code` type and one new `exec` allowlist entry — without touching
  the shared markdown-authoring path or `docs-eng-process/process-map.yaml`'s
  live activity definitions.
- **Scope boundaries.** No Rails, Postgres, Bundler, or multi-file work — one
  file, one language (Ruby, chosen because it needs no package manager to
  run). No change to `develop-solution-increment`'s `spec-then-execute`
  default. No run against a persistent/real repository — disposable
  bench-fixture temp directories only. No further sandboxing of what a
  `.rb` script's own content can do (residual risk, named not solved).
- **Definition of done.** The new task-def, schema exemption, and allowlist
  entry all have passing unit tests; a standalone runner exists that never
  touches `process-map.yaml`; one live run against a real endpoint (owner-run)
  produces a recorded pass/fail with iteration/restart counts in `design.md`.

> **Assumption:** the probe's fixture is built via
> `openup-agent-bench.py`'s existing `build_fixture()` (framework-only
> bootstrap + a new minimal `scripts/bench-scenarios/code-probe/scenario.json`,
> no overlay needed) rather than an ad hoc `tempfile.mkdtemp()` + `git init` —
> more faithful to how the task-def is actually loaded in production (from
> `docs-eng-process/task-library.yaml` inside the fixture). *(Vetoable at
> review.)*
> **Assumption:** `max_iterations=20` for the standalone probe sub-run (vs.
> the shared default of 50) — two tool calls should complete in 2–4 turns;
> 20 leaves headroom for one retry-on-failure without masking genuine
> non-convergence. *(Vetoable at review.)*
> **Assumption:** tool-call order/count (write_file then exec, not the
> reverse; exactly one of each on the happy path) is stated in the system
> prompt but **not enforced in code** — the point of this probe is to
> observe what the model actually does; drift is a finding, not a bug to
> silently correct. *(Vetoable at review.)*
> **Assumption:** the pre-existing path-traversal gap in `Tools._allowed()`
> (`argv[1]` is never passed through `_resolve()`'s root-escape guard, so
> `python3 scripts/../../outside.py` already passes today) is **not** fixed
> by this task — the new `ruby <path>.rb` rule inherits the identical,
> pre-existing gap rather than introducing a new one, and fixing it for the
> whole `exec` surface is a separate hardening task. Blast radius stays
> bounded by the disposable-fixture-only safeguard (Safeguards, below).
> *(Flagged for owner review before merge — not silently fixed or ignored.)*

## Requirements

1. `docs-eng-process/task-library.yaml` gains one new task-def,
   `probe-code-artifact` (`artifact: code`, `output_path: probe/hello.rb`),
   whose `judgment` requires writing a small self-contained Ruby script that
   prints a specific marker string and running it via `exec` before
   finishing.
   - **Given** the updated `task-library.yaml`, **When**
     `python3 scripts/openup-process-map.py tasks --validate` runs, **Then**
     it exits 0 and every existing spine task-def still validates unchanged.

2. `scripts/openup-process-map.py`'s `validate_tasks()` accepts
   `artifact: code` as a deliberate non-spine exemption: skips the
   `SPINE_TYPES` membership check and the `.md`-only `output_path` check for
   that one value, while still rejecting an absolute path or a `.md` target
   for a `code` artifact.
   - **Given** a task-def with `artifact: code` and `output_path: probe/x.rb`,
     **When** `validate_tasks()` runs, **Then** it reports no problem for
     that def.
   - **Given** a task-def with `artifact: code` and `output_path: probe/x.md`,
     **When** `validate_tasks()` runs, **Then** it reports a problem naming
     the `.md` mismatch.

3. `scripts/openup_agent/tools.py`'s `Tools._allowed()` accepts exactly one
   new command shape, `ruby <path>.rb`, and nothing else new.
   - **Given** the command `ruby probe/hello.rb`, **When** `_allowed()` is
     called with its parsed argv, **Then** it returns `True`.
   - **Given** the command `ruby` (no argument) or `ruby probe/hello.txt`,
     **When** `_allowed()` is called, **Then** it returns `False` in both
     cases, and every previously-allowed/refused command (`git ...`,
     `python3 scripts/x.py`, `bash ...`, `rails ...`) is unaffected.

4. A new standalone runner (`scripts/openup_agent/probe_task.py` +
   `scripts/probe-code-artifact.py`) drives the `probe-code-artifact`
   task-def in isolation — no phase, no iteration, no roadmap context — with
   **zero** diff to `docs-eng-process/process-map.yaml`.
   - **Given** the completed task branch, **When** `git diff origin/main --
     docs-eng-process/process-map.yaml` runs, **Then** it produces no output.

5. One live probe run (owner-run, real endpoint) inside a disposable fixture
   confirms or refutes the reliability hypothesis, recorded in
   `docs/changes/T-134/design.md` with iteration count and restart count.
   - **Given** a real `LLM_API_URL`/`OPENUP_MODEL_MAIN` configured, **When**
     `scripts/probe-code-artifact.py` runs once, **Then** the JSON result
     records `marker_found`, `exec_confirmed`, `iterations`, and `restarts` —
     whichever way they come out — and that result is written into
     `design.md` verbatim (a failing result is a valid, complete outcome,
     not a blocker to closing this task).

## Behavior Delta

`n/a — all Added`. No Ring-1 (`docs/product/`) use-case describes the
driver's task-def schema or exec allowlist today (this repo's
`docs/product/` holds only milestone records), so there is no existing
product behavior for this task to modify or remove — every change here is a
new, additive exemption/allowlist entry with no prior Ring-1 counterpart.

**Added:**
- `probe-code-artifact` task-def in the task library
- A non-spine `artifact: code` exemption in the schema validator
  (`scripts/openup-process-map.py`) — existing spine-type validation is
  unaffected (Requirement 1's regression clause), so this is additive, not a
  change to prior validator behavior
- A new `ruby <path>.rb` case in the `exec` allowlist
  (`scripts/openup_agent/tools.py`) — every previously allowed/refused
  command's result is unchanged (Requirement 3's regression clause)
- `scripts/openup_agent/probe_task.py`, `scripts/probe-code-artifact.py`,
  `scripts/bench-scenarios/code-probe/`

## Success Measures

We expect this probe to answer, within one live run, whether `gpt-5.4-nano`
writes *and executes* real code at the same reliability bar T-106/T-107
measured for markdown authoring (zero mid-run restarts, ≤6 turns). A failing
result (restarts, >6 turns, or a fabricated/incorrect marker) is exactly as
informative as a passing one — it falsifies the "same reliability transfers
to code" hypothesis this task exists to test. Instrumentation: the probe
script's own iteration/restart count, read from `OPENUP_AGENT_USAGE_LOG` /
`OPENUP_AGENT_DEBUG_LOG` the same way `openup-agent-bench.py` already does.
Read-back: immediately after the first live run — owner-initiated, no fixed
calendar date (an infrequent, on-demand spike; same conditional-trigger
convention this repo already uses for T-080's "the owner's live batch").

## Rollout

**Flagged?** No. This is internal reference-driver tooling (a schema
exemption, one exec-allowlist entry, and a standalone test/probe script) with
no deployed user-facing surface — there is nothing to roll out to users. The
new capability is inert until a task-def actually declares `artifact: code`
(only `probe-code-artifact` does), and the new `ruby` exec path is inert
until a task-def's instruction asks a model to call it — so ordinary
markdown-authoring runs (Inception, T-107's gate) are unaffected by
construction.

## Entities

- **`docs-eng-process/task-library.yaml`** (modified) — new
  `probe-code-artifact` task-def entry
- **`SPINE_TYPES` / `NON_SPINE_ARTIFACT_TYPES`** (modified/new) —
  `scripts/openup-process-map.py:58-61` — new constant + `validate_tasks()`
  branch (`scripts/openup-process-map.py:387-410`)
- **`Tools._allowed()` / `_ALLOWED_EXEC`** (modified) —
  `scripts/openup_agent/tools.py:20-21, 195-201` — new `ruby <path>.rb` case
- **`stamp_for_task()`** (read-only, confirmed unaffected) —
  `scripts/openup_agent/stamping.py:168-181` — already returns `None` for
  any artifact not in `ID_PREFIXES`; no change needed
- **`render_task_instruction()`** (read-only, reused as-is) —
  `scripts/openup_agent/plan_iteration.py:240-303`
- **`loop.run()`** (read-only, reused as-is) —
  `scripts/openup_agent/loop.py:278-293` — `system_prompt=`/`model=` seam
- **`build_fixture()`** (read-only, reused as-is) —
  `scripts/openup-agent-bench.py:86-94`
- **`probe_task.py`** (new) — `scripts/openup_agent/probe_task.py` —
  standalone task-def runner with its own two-tool-call system prompt
- **`probe-code-artifact.py`** (new) — `scripts/probe-code-artifact.py` —
  thin CLI: build fixture, run probe, independently verify

## Approach

Add one deliberately narrow, additive exception to two existing contracts
(task-def schema, exec allowlist) rather than generalizing either — the
schema exemption is a named constant + one extra branch, and the allowlist
gains exactly one new command shape mirroring the existing `python3
scripts/*.py` pattern. The probe's own execution is fully decoupled from
`process-map.yaml`'s phase/activity machinery by calling
`render_task_instruction()` and `loop.run(system_prompt=..., model=...)`
directly — the same primitives `cycle.py`'s internal `run_task()` uses, just
invoked standalone with a purpose-built system prompt that explicitly permits
(and requires) one post-write `exec` call, since the shared
`_task_system_prompt()` explicitly forbids exactly that.

## Structure

**Add:**
- `scripts/openup_agent/probe_task.py`
- `scripts/probe-code-artifact.py`
- `scripts/bench-scenarios/code-probe/scenario.json`
- `scripts/tests/test_openup_agent_probe_task.py`

**Modify:**
- `docs-eng-process/task-library.yaml` — add `probe-code-artifact` task-def
- `scripts/openup-process-map.py` — `NON_SPINE_ARTIFACT_TYPES` constant +
  `validate_tasks()` branch
- `scripts/openup_agent/tools.py` — `_ALLOWED_EXEC` string + `_allowed()`
  `ruby` branch
- `scripts/tests/test_openup_process_map.py` — new cases for the exemption
- `scripts/tests/test_openup_agent_tools.py` — new cases for `ruby`

**Do not touch:**
- `docs-eng-process/process-map.yaml` — tempting to wire `probe-code-artifact`
  into `develop-solution-increment`'s `tasks:` list for a "more realistic"
  test, but doing so would change live Construction/Elaboration behavior for
  every future OpenUP-driven project using this framework — explicitly out
  of scope (Requirement 4)
- `scripts/openup_agent/cycle.py`'s `_task_system_prompt()` — the shared
  markdown-authoring convergence contract (T-124's fix); this probe uses its
  own sibling prompt in `probe_task.py` instead of editing the shared one
- `scripts/openup_agent/stamping.py` — already correctly no-ops for a
  non-spine artifact; confirmed by reading, not by guessing

## Operations

- [x] Add `probe-code-artifact` to `docs-eng-process/task-library.yaml`; run
      `python3 scripts/openup-process-map.py tasks --validate` and confirm
      it exits 0
- [x] Add `NON_SPINE_ARTIFACT_TYPES = ("code",)` and the `validate_tasks()`
      branch in `scripts/openup-process-map.py`; add unit tests (accept
      `code`+non-`.md`, reject `code`+`.md`, existing spine defs unchanged)
- [x] Add the `ruby <path>.rb` case to `Tools._allowed()` +
      `_ALLOWED_EXEC` in `scripts/openup_agent/tools.py`; add unit tests
      (accept/reject cases from Requirement 3, full existing
      `test_openup_agent_tools.py` suite green)
- [x] Add `scripts/openup_agent/probe_task.py` (two-tool-call system prompt +
      `run_probe_task()`) and `scripts/bench-scenarios/code-probe/scenario.json`;
      add a unit test using a fixed `_completion` seam confirming the
      system prompt and instruction reach `loop.run()` unchanged
- [x] Add `scripts/probe-code-artifact.py` (build a disposable fixture via
      `openup-agent-bench.build_fixture`, run the probe, independently
      re-run the produced file and diff its stdout against the expected
      marker); confirm `git diff origin/main -- docs-eng-process/process-map.yaml`
      is empty
- [x] (tester) Run the full existing test suite green
      (`scripts/tests/test_openup_process_map.py`,
      `test_openup_agent_tools.py`, and the new test files); confirm no
      regression in any currently-passing test
- [x] Run the live probe once (owner-run, real endpoint) and record the
      result — pass or fail — with iteration/restart counts in
      `docs/changes/T-134/design.md`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format,
  etc.)
- `scripts/openup_agent/__init__.py` — the driver package's own stated
  design rules (stdlib-only, six-tool surface)

## Safeguards

Invariants and limits that must hold:
- **Disposable-fixture-only.** The new `ruby` exec path and `probe-code-artifact`
  task-def must only ever run inside a temp fixture built by
  `openup-agent-bench.build_fixture()` (or equivalent) — never against a
  real or persistent repository. `scripts/probe-code-artifact.py` must not
  accept an arbitrary `--repo` target for the fixture itself.
- **No sandboxing of script content.** A `.rb` file's own content is not
  further restricted — it can still shell out via `Kernel#system`, backticks,
  or `IO.popen`. This is why the disposable-fixture-only safeguard above is
  load-bearing, not decorative.
- **Pre-existing path-traversal gap inherited, not introduced.**
  `Tools._allowed()` checks `argv[1]` by string prefix/suffix only, never
  through `_resolve()`'s root-escape guard — true today for
  `python3 scripts/*.py` and inherited identically by the new `ruby` rule.
  Not fixed here; flagged for owner review (Open Question 4 in the iteration
  plan).
- **No-go zone.** `docs-eng-process/process-map.yaml`'s
  `develop-solution-increment` activity stays untouched — no `execution:
  direct`, no `tasks:` entry added there. Real Construction/Elaboration
  lanes must be unaffected by this task.
- **Reversibility.** Every change is additive (new constant, new branch, new
  allowlist entry, new files); reverting is a straight revert with no
  migration to undo.

## Verification

- `python3 scripts/openup-process-map.py tasks --validate` exits 0
- `python3 -m unittest scripts.tests.test_openup_process_map
  scripts.tests.test_openup_agent_tools
  scripts.tests.test_openup_agent_probe_task -v` — all green
- `git diff origin/main -- docs-eng-process/process-map.yaml` — empty
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-134/plan.md`
  exits 0
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or
  a clear gap call-out
- Live probe result recorded in `docs/changes/T-134/design.md`

# T-134: Code-artifact task-def probe (Option D) — can the driver write AND run real code?

**Phase**: construction
**Status**: pending
**Goal**: A narrow, isolated, falsifiable probe of whether the reference driver's lean task-def mechanism can produce *and execute* real code (not just author a markdown file), before committing to a full Rails 8 + PostgreSQL Construction build.
**Priority**: medium

---

## Context

T-107's live-batch gate (this session) proved the driver's lean task-def mechanism (T-104–T-106) reliably authors bounded, single-markdown-file artifacts on a cheap hosted model (`gpt-5.4-nano`): zero mid-run restarts, all sub-runs ≤6 turns, across 5 runs. The owner then asked to extend this into a real Rails 8 + Postgres Construction PoC, still driven end-to-end by the cheap model.

`docs/explorations/2026-07-26-driver-construction-code-authoring.md` found that claim doesn't transfer directly: `develop-solution-increment` (the actual code-writing activity, in both Elaboration and Construction — `docs-eng-process/process-map.yaml:38`) has no `execution: direct` and no `tasks:` — it defaults to `spec-then-execute`, meaning real code has never gone through this bounded mechanism at all. The task-def schema is hard-restricted to one `.md` output per sub-run, and the driver's `exec` tool is deliberately allowlisted to `git`/`python3 scripts/*.py` only (a stated safety invariant). Building the full PoC would mean a new code-artifact type, a fundamentally different multi-file/multi-exec task shape, and a reviewed widening of that safety boundary — not a longer benchmark run.

The exploration's disposition (Option D, chosen by the owner over Option C) is: get one small, real, falsifiable data point — can the model write a piece of code *and run it via the driver's own exec tool* to confirm it works — before any of that larger architecture work is attempted.

---

## Current State

### The exec tool allowlist (`scripts/openup_agent/tools.py:16-21, 195-201`)

```python
"""The six-tool surface for the reference driver (T-072).

read_file, write_file, edit_file, glob (list_dir/glob), grep, exec — rooted at a
single working directory. `exec` is narrowed to an allowlist (`git <subcmd>` and
`python3 scripts/<script>.py …`) so a bare model can drive the deterministic
OpenUP scripts without being handed an arbitrary shell (safety invariant, spec
Requirement 3). Stdlib-only.
"""
...
_ALLOWED_EXEC = "git <subcmd>  |  python3 scripts/<script>.py [args]"
...
@staticmethod
def _allowed(argv):
    if argv[0] == "git":
        return True
    if argv[0] in ("python3", "python"):
        return len(argv) >= 2 and argv[1].startswith("scripts/") and argv[1].endswith(".py")
    return False
```

### The task-def schema hard-restricts output to one markdown file (`scripts/openup-process-map.py:58-61, 387-410`)

```python
SPINE_TYPES = (
    "vision", "requirement", "work-item", "iteration-plan",
    "use-case", "test-case", "decision",
)
...
def validate_tasks(tasks: dict) -> list:
    ...
    artifact = d.get("artifact")
    if artifact and artifact not in SPINE_TYPES:
        problems.append(f"task {tid!r} artifact {artifact!r} not a spine type "
                        f"({', '.join(SPINE_TYPES)})")
    out = str(d.get("output_path", ""))
    if out and (out.startswith("/") or not out.endswith(".md")):
        problems.append(f"task {tid!r} output_path {out!r} must be a relative .md path")
```

### Stamping already no-ops for a non-spine artifact (`scripts/openup_agent/stamping.py:168-181`) — no change needed here

```python
def stamp_for_task(root, task_def):
    """... Returns the stamp_file info dict, or None when the def targets a
    plain view (e.g. docs/roadmap.md), its artifact is not a stampable
    spine type, or the output file does not exist."""
    artifact = (task_def.get("artifact") or "").strip()
    out = (task_def.get("output_path") or "").strip()
    if not out or out in PLAIN_VIEW_PATHS or artifact not in ID_PREFIXES:
        return None
    ...
```

`ID_PREFIXES` (`stamping.py:28-36`) only has the 7 spine types. A `"code"` artifact is not a key in it, so `stamp_for_task()` already returns `None` — confirmed by inspection, no code change required.

### The generic system prompt explicitly forbids a post-write tool call (`scripts/openup_agent/cycle.py:1032-1046`) — this is the one real blocker

```python
def _task_system_prompt(task_def):
    """The slim generic shell for a task-def authoring sub-run (T-106) ..."""
    return (
        "You are an OpenUP authoring agent performing a single task. Produce "
        "exactly the one artifact the instruction names, writing the document "
        "BODY only — the engine stamps the typed frontmatter and validates. Read "
        "only the inputs the instruction lists; do not load procedures, rubrics, "
        "or schemas.\n"
        "Converge — do not loop (T-124): write the artifact with a SINGLE "
        "write_file call. The tool result confirms the write succeeded, so do NOT "
        "read the file back to verify it, and do NOT re-read any input you were "
        "given or have already read. The moment the artifact is written, your "
        "NEXT reply MUST be the line `OPENUP-TASK: DONE` with no tool calls."
    )
```

This is T-124's convergence-contract fix (the one that took Inception authoring from 28+ turns to ≤6). It is **exactly right for markdown authoring and exactly wrong for this probe** — it explicitly bans any tool call after the write, so reusing it verbatim would make the model write the file and stop, never calling `exec` at all. This needs its own sibling variant, not a shared function edit (touching the shared prompt would risk regressing T-106/T-107's proven Inception reliability).

### `render_task_instruction()` (`scripts/openup_agent/plan_iteration.py:240-303`) already builds a task's instruction generically from a `task_def` dict — reusable as-is, no change needed. Signature: `render_task_instruction(root, task_def, objectives, input_path=None, task_defs=None)`.

### `loop.run()` (`scripts/openup_agent/loop.py:278-293`) already supports a standalone `system_prompt=`/`model=` sub-run with no procedure file and no phase/cycle context:

```python
def run(dir, procedure, max_iterations=..., env=None, interactive=False,
        instruction=None, _completion=None, _ask=None, system_prompt=None, model=None):
    """... `system_prompt` + `model` (T-089, both additive): when `system_prompt` is
    given, the procedure-file load and its tier resolution are skipped — `procedure`
    serves only as a log label and `model` MUST be supplied. This is the cycle
    engine's step-scoped sub-run hook; absent ⇒ unchanged behavior."""
```

### `build_fixture()` (`scripts/openup-agent-bench.py:86-94`) already materializes a disposable, freshly-bootstrapped project (framework files + empty `docs/` + a scenario overlay) at a throwaway `dest` path, returning `(seed_sha, scenario)`. Reusable as-is for this probe's fixture.

---

## Proposed Design

### 1. New task-def — `docs-eng-process/task-library.yaml`

```yaml
  probe-code-artifact:
    name: Probe Code Artifact
    role: developer
    artifact: code
    output_path: probe/hello.rb
    source: driver
    inputs: []
    judgment:
      - Writes a small, self-contained Ruby script with no external dependencies.
      - The script prints the exact line `OPENUP-CODE-PROBE-OK` to stdout when run.
      - After writing the file, runs it with `exec` as `ruby probe/hello.rb` and
        confirms the marker line appears in stdout before finishing.
      - If the run fails or the marker is missing, fixes the script and re-runs it —
        does not finish until one exec call actually shows the marker.
      - Emits `OPENUP-TASK: DONE` only after a confirmed successful run.
```

`artifact: code` is new — see the schema change below. `source: driver` matches `author-initial-roadmap`'s existing convention for a task with no KB source file.

### 2. Widen `scripts/openup-process-map.py`'s schema validator

**File**: `scripts/openup-process-map.py`

```python
# One deliberately non-spine exemption: a task-def that produces and runs a
# real code artifact (not a Ring-1 traceability document). Distinct from
# SPINE_TYPES — stamping.py's stamp_for_task() already no-ops for any
# artifact not in ID_PREFIXES, so "code" needs no stamping wiring.
NON_SPINE_ARTIFACT_TYPES = ("code",)
```

```python
artifact = d.get("artifact")
if artifact and artifact not in SPINE_TYPES and artifact not in NON_SPINE_ARTIFACT_TYPES:
    problems.append(f"task {tid!r} artifact {artifact!r} not a spine type "
                    f"({', '.join(SPINE_TYPES)}) or non-spine type "
                    f"({', '.join(NON_SPINE_ARTIFACT_TYPES)})")
out = str(d.get("output_path", ""))
if out.startswith("/"):
    problems.append(f"task {tid!r} output_path {out!r} must be relative")
elif artifact in NON_SPINE_ARTIFACT_TYPES:
    if out.endswith(".md"):
        problems.append(f"task {tid!r} artifact {artifact!r} must not target a .md path")
elif out and not out.endswith(".md"):
    problems.append(f"task {tid!r} output_path {out!r} must be a relative .md path")
```

### 3. Widen the exec allowlist — `scripts/openup_agent/tools.py`

```python
_ALLOWED_EXEC = "git <subcmd>  |  python3 scripts/<script>.py [args]  |  ruby <path>.rb"
```

```python
@staticmethod
def _allowed(argv):
    if argv[0] == "git":
        return True
    if argv[0] in ("python3", "python"):
        return len(argv) >= 2 and argv[1].startswith("scripts/") and argv[1].endswith(".py")
    if argv[0] == "ruby":
        return len(argv) >= 2 and argv[1].endswith(".rb")
    return False
```

**Explicit residual-risk note** (must land in the code comment, not just this plan): the allowlist only constrains the *top-level command* the driver invokes. A `.rb` file's own content is **not** further sandboxed — it can still `` `shell out` ``, `system(...)`, or `IO.popen` to anything the OS-level user can. This is why §4's Safeguards restrict this to the disposable bench-fixture temp directory only.

**Second, pre-existing residual-risk note found during self-critique**: `_allowed()`'s check is a string prefix/suffix test on `argv[1]` — it is never passed through `_resolve()` (the root-escape guard `read_file`/`write_file`/`edit_file` use). This means today's `python3 scripts/<script>.py` rule already accepts a traversal like `scripts/../../outside.py` (`startswith("scripts/")` and `endswith(".py")` both still hold), and the new `ruby <path>.rb` rule inherits the identical gap rather than introducing a new one. Not fixed here (fixing it changes the contract for every existing allowlisted command, a broader hardening task of its own) — recorded as Open Question 4 below and left as a known, accepted, pre-existing limitation whose blast radius stays bounded by the disposable-fixture-only safeguard.

### 4. New standalone entry point — does NOT touch `process-map.yaml`'s live phase/activity wiring

**New file**: `scripts/openup_agent/probe_task.py`

```python
"""Standalone driver for ONE task-def, outside any phase/cycle/iteration
context (T-134). Reuses render_task_instruction (plan_iteration.py) for the
instruction and loop.run's system_prompt=/model= seam (T-089) for the sub-run
— the same machinery cycle.py's run_task() uses internally, called directly
so this probe never touches process-map.yaml's real activity wiring."""

from . import loop, plan_iteration

_CODE_TASK_SYSTEM_PROMPT = (
    "You are an OpenUP authoring agent performing a single code-writing task. "
    "Produce exactly the one file the instruction names.\n"
    "Converge in exactly two tool calls: (1) ONE write_file call for the "
    "source file, (2) ONE exec call that runs it and shows the expected "
    "marker in stdout. If the exec call fails or the marker is missing, you "
    "may write_file + exec again to fix it, but stop and emit "
    "`OPENUP-TASK: DONE` the moment one exec call succeeds with the marker "
    "present — do not re-run a command that already succeeded."
)


def run_probe_task(root, task_def, model, env=None, max_iterations=20):
    instruction = plan_iteration.render_task_instruction(
        root, task_def,
        objectives=["Confirm the driver can author and execute working code"])
    return loop.run(dir=str(root), procedure=task_def["name"], env=env,
                    max_iterations=max_iterations, instruction=instruction,
                    system_prompt=_CODE_TASK_SYSTEM_PROMPT, model=model)
```

**New file**: `scripts/probe-code-artifact.py` (thin CLI, mirrors `openup-agent-bench.py`'s fixture-building pattern)

```python
#!/usr/bin/env python3
"""Run the T-134 code-artifact probe once, in a disposable fixture. Prints a
JSON result: {exit_code, marker_found, exec_confirmed, iterations, restarts}."""
# Builds a fixture via openup-agent-bench.build_fixture (or an equivalent
# minimal git-init'd temp dir — a full bootstrap isn't needed since this task
# has no requires_input), loads probe-code-artifact from task-library.yaml via
# openup-process-map.py's existing task loader, calls
# openup_agent.probe_task.run_probe_task, then independently re-runs
# `ruby probe/hello.rb` in the fixture and diffs its stdout against the
# expected marker (defense in depth against a faked success).
```

---

## Acceptance Criteria

- [ ] `probe-code-artifact` task-def added to `docs-eng-process/task-library.yaml`; `openup-process-map.py tasks --validate` exits 0
- [ ] `scripts/openup-process-map.py`'s `validate_tasks()` accepts `artifact: code` as a non-spine exemption (unit test: a `.md`-targeting `code` task-def is rejected; a non-`.md`-targeting one is accepted) and every existing spine task-def still validates unchanged
- [ ] `scripts/openup_agent/tools.py`'s `_allowed()` accepts `ruby <path>.rb` and rejects `ruby` with no argument, `ruby` targeting a non-`.rb` path, and every other previously-refused command unchanged (regression: full existing `test_openup_agent_tools.py` suite green)
- [ ] `scripts/openup_agent/probe_task.py` (`run_probe_task`) drives one task-def sub-run standalone, with **zero** changes to `docs-eng-process/process-map.yaml` (verified by `git diff` scoping)
- [ ] Live probe run (owner-only, real endpoint) against `gpt-5.4-nano` inside a disposable fixture: the model writes `probe/hello.rb`, calls `exec` with `ruby probe/hello.rb`, and the marker `OPENUP-CODE-PROBE-OK` appears in the exec result's stdout, confirmed independently by re-running the file after the sub-run — recorded in `design.md` with iteration count and restart count (same measure T-106/T-107 used)
- [ ] The probe never runs against a persistent/real repo — only inside `openup-agent-bench.py`-style disposable temp fixtures (enforced by the new script always creating a `tempfile.mkdtemp()`-rooted fixture, never accepting an arbitrary `--repo` target path for the *fixture itself*)

---

## Success Measures

We expect this probe to answer, within one session, whether a cheap model
(`gpt-5.4-nano`) can reliably write-and-execute a single piece of real code
through the driver's existing tool surface, at the same reliability bar
T-106/T-107 measured for markdown (zero restarts, ≤6 turns). Instrumentation:
the probe script's own iteration/restart count, read from
`OPENUP_AGENT_USAGE_LOG`/`OPENUP_AGENT_DEBUG_LOG` the same way the bench
harness already does. Read-back: immediately after the first live run
(owner-initiated, no fixed date — this is a spike, not a scheduled release).
A failing result (restarts, >6 turns, or a faked/incorrect marker) is exactly
as valuable here as a pass: it tells us the "same reliability, applied to
code" hypothesis from the exploration is false, which is itself the falsifiable
question this task exists to answer.

---

## Testing Strategy

- Unit: `validate_tasks()` — `artifact: code` + non-`.md` path passes; `artifact: code` + `.md` path fails; unknown artifact value still fails; every current spine task-def in `task-library.yaml` still validates
- Unit: `Tools._allowed()` — `ruby probe/hello.rb` → True; `ruby` (no arg) → False; `ruby probe/hello.txt` → False; existing `git`/`python3 scripts/*.py` cases unchanged
- Unit: `probe_task.run_probe_task()` against a fixed `_completion` test seam (mirrors existing `loop.py` test patterns) — asserts the two-tool-call system prompt is passed through and the def's `output_path`/`artifact` reach `render_task_instruction()` unchanged
- Manual/live (owner-only, recorded in `design.md`): one real run against `gpt-5.4-nano` via a real `LLM_API_URL`, in a disposable fixture, per Acceptance Criteria above

---

## Dependencies

- T-106 (task-def / `direct` execution mechanism — completed; the code this probe reuses)

T-107 (live-batch gate) is referenced as context — its result is this probe's
reliability baseline to compare against — but is **not** a hard dependency:
T-107 itself is still `pending` in the roadmap (its own remaining scope, KB
compile etc., is unrelated to what this probe needs). Declaring it as a
`depends-on` would incorrectly block this task from ever being selected by
`openup-roadmap.py next` until T-107 fully closes.

---

## Key Files

| File | Change |
|------|--------|
| `docs-eng-process/task-library.yaml` | Add `probe-code-artifact` task-def |
| `scripts/openup-process-map.py` | `validate_tasks()` accepts `artifact: code` as a non-spine exemption |
| `scripts/openup_agent/tools.py` | `_allowed()` + `_ALLOWED_EXEC` gain `ruby <path>.rb` |
| `scripts/openup_agent/probe_task.py` | New — standalone task-def runner (two-tool-call system prompt) |
| `scripts/probe-code-artifact.py` | New — thin CLI: build disposable fixture, run the probe, verify independently |
| `scripts/tests/test_openup_process_map.py` | New/extended tests for the schema exemption |
| `scripts/tests/test_openup_agent_tools.py` | New/extended tests for the `ruby` allowlist entry |

---

## Out of Scope

- Rails, Postgres, Bundler, or any multi-file work — explicitly deferred to a later, separately-scoped task if this probe succeeds
- Any change to `docs-eng-process/process-map.yaml`'s `develop-solution-increment` entry (its `spec-then-execute` default is untouched — real Construction lanes are unaffected)
- Any run of the widened `exec`/`ruby` path against a real or persistent repository
- Further sandboxing of what a `.rb` script's own content can do (noted as a residual risk, not solved here)
- A second interpreter/language option — Ruby only, chosen because it needs no package manager to run a self-contained script (keeps this probe about the driver's reliability, not about dependency installation)

---

## Open Questions

1. **Should the probe's fixture be built via `openup-agent-bench.py`'s `build_fixture()` (framework-only bootstrap) or a simpler ad hoc `tempfile.mkdtemp()` + `git init`?** `build_fixture()` copies the whole framework tree (scripts/, docs-eng-process/) which this probe's task-def technically needs (it's loaded from `docs-eng-process/task-library.yaml` inside the fixture, the same way a real cycle run would read it) — so reusing `build_fixture()` is more faithful to how this would actually run in production. **Assumed: reuse `build_fixture()` with a new minimal `scripts/bench-scenarios/code-probe/scenario.json`** (no overlay needed — no stakeholder brief required). Vetoable at review.
2. **Is 20 the right `max_iterations` cap for the probe's standalone sub-run** (vs. the shared 50 used elsewhere)? Two tool calls should complete in 2-4 turns if the model behaves; 20 leaves headroom for one retry-on-failure cycle without masking a genuine non-convergence. **Assumed: 20, vetoable at review.**
3. **What should happen if the model calls `exec` before `write_file` (wrong order), or calls `write_file` twice?** The system prompt states the expected order and count but the tool surface doesn't enforce it. **Assumed: not enforced in code for this probe — the point is to observe what the model actually does; if it drifts, that's a finding, not a bug to silently correct.** Vetoable at review.
4. **Should this task also fix `_allowed()`'s pre-existing path-traversal gap** (argv[1] is never `_resolve()`-checked, so `scripts/../../outside.py` already passes today, and the new `ruby` rule inherits it)? **Assumed: no — out of scope for this narrow probe; a separate hardening task should address it for the whole `exec` surface at once, not piecemeal per allowlist entry.** Flagged for owner review before merge, not silently fixed or silently ignored.

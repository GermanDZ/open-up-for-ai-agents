---
name: openup-create-handoff
description: Produce a handoff brief (acceptance criteria, test cases, troubleshooting, open questions) for a change, so the next owner can pick it up cold
model: haiku
fit:
  great: [pausing mid-task for another owner, end-of-iteration handoff, "someone else finishes this" moments]
  ok: [recording how to exercise a finished feature before completion, capturing open questions surfaced during work]
  poor: [the durable run log (use openup-log-run), the spec itself (that is the change-folder plan.md)]
arguments:
  - name: task_id
    description: The task ID whose change folder to summarize (e.g., T-011). Required.
    required: true
  - name: audience
    description: "Optional. Who is receiving the handoff (e.g. 'next session', 'tester', 'reviewer') — tunes emphasis. Defaults to the next agent/owner."
    required: false
---

# Create Handoff

Produce a **handoff brief** for a change: the compact, self-contained document that lets the
next owner resume the work without re-deriving context. This codifies the brief that emerged
organically in Kaze T-015 (acceptance criteria, test cases, troubleshooting, open questions)
and proved itself unprompted — now a first-class, repeatable artifact (Process v2 WS6c).

A handoff is **not** the spec (that is `docs/changes/{task_id}/plan.md`) and **not** the
durable run log (that is `/openup-log-run`). It is the *receiver-facing* bridge: "here is
what done looks like, here is how to prove it, here is what bit me, here is what is still
open."

> **Assembly step** — this skill is mechanical (`model: haiku`). It collects from existing
> ring-scoped sources and formats them; it does not make design decisions. Where a section
> has no source material, say so explicitly rather than inventing content.

## Inputs (Ring 1 + the one change folder — do NOT scan all of `docs/`)

1. **The change folder** `docs/changes/{task_id}/` (or `docs/changes/archive/{task_id}/`):
   - `plan.md` — acceptance criteria, scope, out-of-scope (source for §1).
   - `design.md` — in-flight decisions and gotchas (source for §3 and §4).
   - `test-notes.md` (if present) — how the work was exercised (source for §2).
2. **The run log** `docs/agent-logs/agent-runs.jsonl` — commits/branch for this `task_id`
   (source for the header + §2 commands).
3. **Ring 1 product truth** only as needed to name the feature under test — do not summarize
   the whole product.

## Process

### 1. Locate the change folder

Resolve `docs/changes/{task_id}/`; if absent, try `docs/changes/archive/{task_id}/`. If
neither exists, stop and tell the caller the task has no change folder to hand off.

### 2. Collect, section by section

Pull each section's content from the sources above. Keep it tight — a handoff is scannable,
not exhaustive. Carry forward concrete artifacts (commands, file paths, IDs), not prose
restatements of the plan.

### 3. Write `docs/changes/{task_id}/handoff.md`

> **Scribe step** — once you have assembled the four sections, delegate the file write to the
> `openup-scribe` agent (Agent tool, subagent_type: "openup-scribe") with the exact content.

Use this structure:

```markdown
# {task_id} Handoff — {title}

**Status:** {in-progress | ready-for-review | done} · **Branch:** {branch} · **For:** {audience}
**Last commit:** {sha} — {subject}

## 1. Acceptance criteria
> What "done" means — the conditions the receiver verifies. Pulled from plan.md.
- [ ] AC1 …
- [ ] AC2 …

## 2. How to exercise it (test cases)
> Concrete steps/commands to reproduce or verify behavior. From test-notes.md + the run log.
1. `command / step` → expected result
2. …

## 3. Troubleshooting
> Failure modes hit during the work and how they were resolved. From design.md / session.
- **Symptom** → cause → fix.
- (none observed) — state this explicitly if so.

## 4. Open questions
> Unresolved decisions handed to the next owner. From design.md / plan out-of-scope.
- Q1 …
- (none) — state this explicitly if so.
```

### 4. Report

Return the handoff path and a one-line count of items per section (ACs, test cases,
troubleshooting entries, open questions).

## Output

- Path to `docs/changes/{task_id}/handoff.md`
- Per-section item counts
- Any section that had no source material (so the caller can fill the gap)

## See Also

- [openup-complete-task](../complete-task/SKILL.md) — finalize a task (the handoff often precedes review)
- [openup-log-run](../log-run/SKILL.md) — the durable run log (different artifact, different audience)
- [openup-readiness](../readiness/SKILL.md) — what the next owner can pick up next

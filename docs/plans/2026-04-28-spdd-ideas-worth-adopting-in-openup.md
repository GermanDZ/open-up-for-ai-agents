# SPDD Ideas Worth Adopting in OpenUP

## Context

Martin Fowler's "Structured Prompt-Driven Development" (SPDD) article proposes treating
structured prompts as **first-class delivery artifacts** — versioned, reviewed, and re-used
to keep AI-generated code aligned with intent at scale.

OpenUP for AI Agents already implements many SPDD principles (artifact-driven workflow,
role specialization, rubric-based assessment, hook-enforced process). This plan identifies
the **specific ideas from SPDD that fill real gaps in OpenUP** and how to integrate them
without bloating the framework.

---

## What OpenUP Already Covers (skip these)

| SPDD idea | Where OpenUP already has it |
|---|---|
| Versioned, reviewable specs | `docs/use-cases/`, `docs/plans/`, architecture notebook |
| Workflow stages with skills | `/openup-*` skills + phase teams |
| Rubrics on outputs | `.claude/rubrics/` (vision, use-case, arch, iteration, test) |
| Role specialization | `.claude/teammates/` (analyst, architect, developer, PM, tester) |
| Process enforcement | hooks (`check-iteration.py`, `on-plan-exit.py`, `on-stop.py`) |
| Lightweight vs full path | `/openup-quick-task` vs `/openup-orchestrate` |
| Iteration learnings loop | `.claude/memory/iteration-learnings.md` |

---

## Ideas Worth Adopting (ranked by value/effort)

### 1. REASONS-style task spec — the missing layer between use case and code (HIGH value, MED effort)

**Gap:** OpenUP has *project-level* artifacts (vision, use case, architecture notebook) and
*iteration-level* artifacts (iteration plan, task list), but no **executable per-task blueprint**
that a developer-role agent consumes verbatim. Tasks in `roadmap.md` and `iteration-plan.md`
are too thin; use cases are too coarse. This is exactly the gap REASONS fills.

**Proposal:** Add a `task-spec.md` template + `/openup-create-task-spec` skill (or extend
`iteration-plan.md` to include this section per task). Seven slots, mapped to OpenUP idiom:

- **Requirements** — link to use case / acceptance criteria (already exists, just reference)
- **Entities** — domain types/objects touched (new)
- **Approach** — design intent in 3–5 lines (new; today this is implicit)
- **Structure** — file/module boundaries to add or modify (new)
- **Operations** — concrete, testable steps (new; today buried in iteration plan)
- **Norms** — naming, logging, style; **inherited from `conventions.md`**, not duplicated
- **Safeguards** — invariants, perf/security limits; **inherited from architecture notebook**

The "inherit from existing artifact" framing keeps it from becoming yet-another-document.
Rubric: `.claude/rubrics/task-spec-rubric.md` (8 criteria, same shape as existing rubrics).

**Files:**
- `docs-eng-process/templates/task-spec.md` (new)
- `.claude/skills/openup-artifacts/openup-create-task-spec.md` (new)
- `.claude/rubrics/task-spec-rubric.md` (new)
- `.claude/teammates/developer.md` — update to consume task-spec verbatim

---

### 2. "Fix the spec first" rule for behavior changes (HIGH value, LOW effort)

**Gap:** When a developer-agent finds the implementation should differ from the spec,
OpenUP has no explicit rule. The risk: silent drift between use case / iteration plan
and code, exactly the failure mode SPDD calls out.

**Proposal:** Codify the bifurcated review rule in `CLAUDE.openup.md`:

> **Behavior change?** Update the use case / task spec **first**, then regenerate or
> patch code. **Refactor only?** Change code first, then run `/openup-sync-spec` to
> back-propagate non-behavioral changes to the affected artifacts.

Add this as a short section under "Critical Rules". The `developer` and `architect`
teammate prompts gain one bullet each pointing at this rule.

**Files:**
- `.claude/CLAUDE.openup.md` — add ~6 lines under Critical Rules
- `.claude/teammates/developer.md` and `developer-compact.md` — one-bullet reminder
- `.claude/teammates/architect.md` and `architect-compact.md` — same

---

### 3. `/openup-sync-spec` — refactor → artifact back-propagation (MED value, MED effort)

**Gap:** SPDD's `/spdd-sync` exists precisely because refactors invalidate prior specs.
OpenUP today has no skill to update use cases / architecture notebook to reflect a
post-merge refactor. Today this would be done ad-hoc (and likely skipped).

**Proposal:** New skill `/openup-sync-spec` that:
1. Diffs current code vs the artifact's last-synced state (git ref recorded in artifact frontmatter)
2. Identifies which sections of which artifacts are stale
3. Proposes targeted edits — **not** regeneration of the whole document
4. Updates a `last-synced: <sha>` frontmatter field on each affected artifact

Defer until after #1 and #2 prove valuable; only useful once specs are dense enough to drift.

**Files:**
- `.claude/skills/openup-workflow/openup-sync-spec.md` (new)

---

### 4. Suitability stars in skill frontmatter (LOW value, LOW effort)

**Gap:** SPDD explicitly rates itself 5★ for standardized delivery, 1–2★ for hotfixes,
spikes, one-off scripts. OpenUP has `quick-task` vs `orchestrate` vs `start-iteration`
but the boundary between them is under-documented; users guess.

**Proposal:** Add a `fit:` field to each workflow skill's frontmatter, e.g.:

```yaml
fit:
  great: [feature work, multi-role tasks]
  ok: [single-file changes]
  poor: [hotfixes, spikes, one-off scripts]
```

Surface these in the `/openup-init` flow and `QUICK-REFERENCE.md`. Cheap, helps onboarding.

**Files:**
- Each `.claude/skills/openup-workflow/*.md` — frontmatter addition
- `docs-eng-process/QUICK-REFERENCE.md` — short fit-matrix table

---

### 5. Don't hand-edit specs; converse to update them (LOW value, LOW effort)

**Gap:** SPDD warns against manually editing structured prompts because hand-edits
break internal consistency. OpenUP artifacts have the same risk (rubric criteria
silently violated by ad-hoc edits).

**Proposal:** Add one bullet to `CLAUDE.openup.md`: changes to use cases / iteration
plans / architecture notebook should go through the relevant `/openup-*` skill so
the rubric is re-checked. Trivial.

---

## Explicitly Out of Scope

- **Adopting REASONS naming verbatim.** "Operations / Norms / Safeguards" is jargon
  layered on top of existing OpenUP terms. Use OpenUP idiom and reference SPDD only
  in commit messages / docs.
- **A separate `openspdd` CLI.** OpenUP's slash-commands serve this role.
- **A prompt-quality rubric for skills themselves.** Interesting but a meta-concern;
  defer until concrete pain shows up.

---

## Recommended Sequencing

1. **First** (low-risk, high-value): adopt #2 (Fix-spec-first rule) and #5 (no
   hand-edits) — pure documentation/process changes, ~30 min total.
2. **Then**: build #1 (task-spec template + skill + rubric) — 1–2 sessions of work,
   most of the lasting value.
3. **Then evaluate**: do specs actually drift in practice? If yes, add #3
   (`/openup-sync-spec`). If no, skip it — YAGNI.
4. **Anytime**: #4 (fit stars) — low effort, do when touching the skill files for
   another reason.

---

## Critical Files (for any implementation step)

- `.claude/CLAUDE.openup.md` — central agent rules
- `.claude/skills/openup-artifacts/` — where new artifact-creation skills live
- `.claude/skills/openup-workflow/` — where new workflow skills live
- `.claude/teammates/developer.md`, `architect.md` (and `-compact` variants) — role briefs
- `.claude/rubrics/` — grading criteria for new artifacts
- `docs-eng-process/templates/` — artifact templates
- `docs-eng-process/conventions.md` — Norms inheritance source
- `.claude/hooks/` — only touch if we want enforcement (not in this plan)

---

## Verification

For doc-only changes (#2, #5): sanity-read the updated `CLAUDE.openup.md` end-to-end;
ensure it stays under the size budget the file currently respects.

For #1 (task-spec):
- Run `/openup-quick-task` end-to-end on a small change and confirm a task-spec is
  produced and consumed by the developer role.
- Run `/openup-orchestrate` on a multi-role task; confirm each specialist receives
  the task-spec verbatim and the rubric grades it.
- Manually grade one generated task-spec against the new rubric — every criterion
  should be ✅ or have a clear gap call-out.

For #3 (sync-spec): only after real drift is observed; verify by introducing a
deliberate refactor and confirming the skill proposes correct, scoped artifact edits.

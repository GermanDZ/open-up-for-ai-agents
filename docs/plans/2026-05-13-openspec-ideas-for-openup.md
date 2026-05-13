# OpenSpec Ideas Worth Adopting in OpenUP

## Context

[OpenSpec](https://github.com/Fission-AI/OpenSpec) (Fission-AI) is a spec-driven
development framework for AI coding assistants, distributed as an npm package
(`@fission-ai/openspec`) and tool-agnostic across 25+ assistants. Its current
("OPSX") workflow models a unit of work as a **change** folder containing four
artifacts on an explicit dependency DAG: `proposal → specs → design → tasks`,
with states `BLOCKED → READY → DONE` and an archive-on-complete flow.

This plan is the OpenSpec counterpart to
[`2026-04-28-spdd-ideas-worth-adopting-in-openup.md`](2026-04-28-spdd-ideas-worth-adopting-in-openup.md):
identify what OpenSpec does that **fills a real gap in OpenUP**, separate it
from what OpenUP already covers (often better), and reject jargon-import.

OpenSpec sits at the **lightweight / single-agent** end of the spec-driven
spectrum; OpenUP sits at the **governed / multi-agent** end. The interesting
question is not "should OpenUP become OpenSpec" — it shouldn't — but "which of
OpenSpec's primitives sharpen OpenUP without diluting its governance edge."

---

## What OpenUP Already Covers Better (skip these)

| OpenSpec idea | Where OpenUP already has it (and usually goes further) |
|---|---|
| Spec as a contract | Use cases + iteration plan + task spec, with rubric grading per artifact |
| Per-change folder of artifacts | `docs/use-cases/`, `docs/plans/`, `docs/tasks/T-NNN-*.md`, iteration-plan link |
| Role separation | `.claude/teammates/` — analyst, architect, developer, PM, tester, scribe (compact + full) |
| Process gates | Phase skills + `/openup-assess-completeness` + rubrics |
| Lightweight path | `/openup-quick-task` is OpenUP's equivalent of "small change, minimal ceremony" |
| Memory of past work | `.claude/memory/iteration-learnings.md` + retrospectives |
| Brownfield install | `sync-from-framework.sh` + submodule update flow (more involved than `openspec init`, but explicit) |

For each of these, OpenSpec's version is simpler; OpenUP's is more disciplined.
Replacing OpenUP's version with OpenSpec's would be a regression.

---

## What OpenSpec Does That OpenUP Doesn't (the real list)

The five items below are the only OpenSpec primitives where OpenUP has a *gap*,
not just a different idiom. Anything not on this list either already exists in
OpenUP or is out of scope (see "Explicitly Out of Scope").

### 1. Artifact dependency DAG with explicit READY/BLOCKED states (HIGH value, MED effort)

**Gap.** Readiness in OpenUP is implicit. A developer-role agent knows a task
is "ready to implement" only by reading project-status + iteration-plan + the
relevant use case and judging. The judgement is mostly correct, but it costs
context every iteration and silently degrades when artifacts drift.

OpenSpec models this with a small DAG:
`proposal → specs/<capability>/spec.md → design.md → tasks.md`, where each
node has state `BLOCKED` (deps missing), `READY` (deps DONE), or `DONE` (file
exists and rubric-equivalent passes). `/opsx:continue` deterministically picks
the next READY node.

**Proposal.** Add a minimal readiness DAG over OpenUP artifacts, expressed as
frontmatter `depends_on:` lists on each artifact:

- `task-spec.md` `depends_on: [use-case, architecture-notebook section, iteration-plan task entry]`
- `iteration-plan.md` `depends_on: [roadmap task entry, relevant use cases]`
- `use-case.md` `depends_on: [vision]`

A new `/openup-readiness` skill (or extension to `/openup-start-iteration`)
computes the DAG and reports the next ready artifact for the current task.
**This is not a state machine** — no enforcement, no blocking — just a derived
readiness view. The rubric remains the authoritative quality gate.

**Why this is worth doing.** It makes "what should I work on next" a query,
not a judgement call, which (a) reduces the PM-orchestration prompt size,
(b) makes drift detectable (a `DONE` artifact whose dependency was edited
later flips to `STALE`), and (c) is a precondition for usable
`/openup-sync-spec` (T-002) — sync needs to know which artifacts depend on
which file.

**Files.**

- `.claude/skills/openup-workflow/openup-readiness.md` (new)
- Frontmatter additions to existing templates in `docs-eng-process/templates/`
- `.claude/teammates/project-manager.md` — one bullet pointing at the new skill

**Out of scope here.** Hard-blocking BLOCKED transitions, GUI dashboard.
Keep it a textual readout.

---

### 2. Config-injected `<context>` / `<rules>` blocks (MED value, LOW effort)

**Gap.** OpenUP's standing rules live in several places: `CLAUDE.openup.md`,
per-skill SKILL.md preambles, per-teammate role briefs, and `.claude/rubrics/`.
Adding a project-wide rule means editing 3–5 files. Worse, *project-specific*
rules (tech stack, API conventions, compliance constraints) have no canonical
home — they currently leak into `CLAUDE.md` or, more often, are repeated in
every prompt.

OpenSpec solves this with `openspec/config.yaml`:

```yaml
schema: spec-driven
context: |
  Tech stack: TypeScript, React, Node.js
  API conventions: RESTful, JSON responses
rules:
  proposal:
    - Include rollback plan
  specs:
    - Use Given/When/Then format for scenarios
```

These are injected into every artifact wrapped in `<context>...</context>` and
`<rules>...</rules>` tags, so the model always sees them with the same framing
and precedence (CLI flag > change metadata > project config > default).

**Proposal.** Introduce `docs/project-config.yaml` (project-owned, not
framework-owned) with two top-level keys:

- `context:` — project-level facts the framework can't infer (stack, domain,
  compliance posture, key stakeholders).
- `rules:` — keyed by artifact type, additive to the rubric. E.g. `rules.task-spec`
  appends per-project criteria the universal rubric can't carry.

Each `/openup-create-*` skill loads `docs/project-config.yaml` and emits the
relevant section into the generated artifact's prompt as `<project-context>`
and `<project-rules>` blocks. The universal `.claude/rubrics/*-rubric.md` files
stay framework-owned; project rules layer on top.

**Why this is worth doing.** It gives projects a single place to inject the
"things that are true here that aren't true everywhere," which is currently
the most-edited content in `CLAUDE.md` files of OpenUP-derived projects.

**Files.**

- `docs-eng-process/templates/project-config.example.yaml` (new)
- `.claude/skills/openup-init/SKILL.md` — emit a starter `docs/project-config.yaml`
- `.claude/skills/openup-artifacts/*/SKILL.md` — read and inject (small edit each)
- `.claude/CLAUDE.openup.md` — document the precedence: framework rubric →
  project rules → task-spec safeguards

**Out of scope here.** A schema for `project-config.yaml` (linting it). Start
unvalidated; add a schema if it's adopted broadly.

---

### 3. Per-change folder ("everything for this work in one place") (MED value, MED effort)

**Gap.** A single OpenUP unit of work touches files in `docs/use-cases/`,
`docs/plans/`, `docs/tasks/`, `docs/test-plans/`, and `docs/architecture/`.
Reconstructing "what is the full state of T-001" requires a multi-file walk.
OpenSpec collapses this to one directory per change.

**Proposal.** Introduce a `docs/tasks/T-NNN/` folder layout (instead of the
current flat `docs/tasks/T-NNN-*.md`), containing:

```
docs/tasks/T-001-reasons-task-spec/
├── task-spec.md          # the executable per-task blueprint
├── design.md             # optional: when arch-level decisions are local to this task
├── test-notes.md         # optional: deviations from the project test plan
└── retrospective.md      # appended on /openup-complete-task
```

Cross-task artifacts (use cases, architecture notebook, project-wide test plan)
stay where they are — they outlive any single task. The change is *additive*:
the existing flat layout still works; `docs/tasks/T-NNN/` is a richer container
when a task warrants it.

**Why this is worth doing.** It localises ephemeral artifacts next to the task,
reduces grep-driven context reconstruction, and gives a natural archive unit
(see #4).

**Why this is rated MED, not HIGH.** OpenUP is consciously *not* per-change-centric
— it's iteration-centric. Forcing every artifact into a change folder
(OpenSpec's choice) loses the cross-task continuity OpenUP gets from
project-level artifacts. The folder is a container for *local* artifacts, not
a re-centring of the framework.

**Files.**

- `.claude/skills/openup-artifacts/create-task-spec/SKILL.md` — emit into folder
- `.claude/skills/openup-workflow/start-iteration/SKILL.md` — create folder if needed
- `docs-eng-process/conventions.md` — document the folder layout convention

**Out of scope here.** Migrating existing flat task files. Convention applies
to new tasks; old ones stay.

---

### 4. Archive-on-complete flow (LOW value, LOW effort)

**Gap.** `docs/tasks/` and `docs/plans/` accumulate forever. Active and
completed work live in the same listing, which slowly inflates the context a
PM-role agent loads at iteration start.

OpenSpec archives a completed change to `openspec/changes/archive/<date-name>/`.

**Proposal.** Add `/openup-archive` as an opt-in skill that, on
`/openup-complete-task`, moves a `T-NNN-*` folder (or file) to
`docs/tasks/archive/YYYY-MM-DD-T-NNN-*/`. The roadmap entry stays in
`docs/roadmap.md` with status `done` and an updated link.

**Why this is rated LOW.** It's a tidy-up, not a correctness win. Worth doing
once #3 (per-task folders) is in place, because archiving a folder is cleaner
than archiving scattered files. Without #3, skip it.

**Files.**

- `.claude/skills/openup-workflow/openup-archive.md` (new)
- `.claude/skills/openup-workflow/complete-task/SKILL.md` — optional archive step

---

### 5. Explore-mode as a first-class state (MED value, LOW effort)

**Gap.** OpenUP's CLAUDE.openup.md rule "all work must be in an iteration" has
no sanctioned home for **pre-iteration thinking** — investigating whether a
problem is real, sketching options, ruling out approaches. Today the choices
are: spin up an iteration (too much), use `/openup-quick-task` (wrong shape —
it's for small *deliverables*, not exploration), or work out-of-band and
violate the rule. In practice the third option happens.

OpenSpec models this with `/opsx:explore`: "think through ideas, investigate
problems, clarify requirements — no structure required." Exploration produces
notes that *may* later seed a proposal. It is not itself a deliverable.

**Proposal.** Add `/openup-explore` as a sanctioned pre-iteration mode:

- Creates `docs/explorations/YYYY-MM-DD-<slug>.md` (or appends to an existing one).
- No rubric, no branch (or an optional `explore/` branch), no team deployment.
- Output is freeform notes with one required end-section: **"Where this goes
  next"** — one of `→ iteration` (becomes a roadmap entry), `→ quick-task`,
  `→ dropped` (with reason).
- Update `CLAUDE.openup.md`: "all *delivery* work in an iteration; *exploration*
  work in `/openup-explore`." Closes the loophole users currently exploit.

**Why this is worth doing.** It legitimises a thing that already happens, with
a small guard (the "Where this goes next" section) that prevents exploration
notes from quietly becoming undocumented decisions. Cheap.

**Files.**

- `.claude/skills/openup-workflow/openup-explore.md` (new)
- `.claude/CLAUDE.openup.md` — refine "all work in an iteration" to
  "all delivery work"
- `docs/explorations/.gitkeep` — directory marker

---

## Explicitly Out of Scope

- **Adopting OpenSpec's artifact set verbatim** (`proposal.md` / `specs/` /
  `design.md` / `tasks.md`). OpenUP's use-case + arch-notebook + iteration-plan
  + task-spec covers the same ground with sharper role separation. Importing
  OpenSpec naming would duplicate concepts.
- **Forkable schema system** (`openspec/schemas/`, `openspec schema fork`).
  Theoretically attractive (let projects redefine artifacts), but OpenUP's
  rubrics + templates are already the customisation surface. A schema
  abstraction is a layer of indirection without a current pain point. Defer
  indefinitely; revisit only if multiple OpenUP-derived projects diverge in
  artifact set.
- **An `openup` npm CLI.** OpenUP is delivered as a project template +
  slash-commands; that's the right shape for a Claude-Code-native framework.
  Repackaging as a cross-tool CLI sacrifices the multi-agent / teammates
  primitives that are OpenUP's edge.
- **Replacing OpenUP rubrics with implicit "fix the artifact during apply"**
  (OpenSpec's quality model). Rubrics catch under-specification before code is
  written; the implicit model catches it after. Strict regression.
- **Tool-portability for 25+ assistants.** OpenUP's value depends on Claude
  Code's teammates / teams / hooks primitives. Generalising loses the edge.
- **OpenSpec's anonymous telemetry.** Not relevant to a self-hosted template.

---

## Relationship to T-002 (`/openup-sync-spec`)

T-002 (deferred) is the **destination** for OpenSpec's `/opsx:sync` idea. Two
notes:

1. **#1 (readiness DAG) is a precondition.** Sync needs to know which artifacts
   depend on which code paths and which artifacts depend on each other. The
   `depends_on:` frontmatter from #1 gives sync its input.
2. **`last-synced: <sha>` already in the T-002 spec** — keep it; combine with
   the DAG to make sync surgical (re-grade only stale dependents) rather than
   bulk-regenerative.

When T-002 is un-deferred, do #1 first, then T-002.

---

## Recommended Sequencing

1. **#5 (explore mode) first** — lowest risk, fills the "loophole already
   exploited" gap, ~1 session.
2. **#2 (project-config.yaml) second** — small surface area, immediate quality
   improvement for derived projects, ~1 session.
3. **#1 (readiness DAG)** — biggest cognitive win for PM-role coordination,
   ~1–2 sessions. Required before un-deferring T-002.
4. **#3 (per-task folders)** — convention change; do it before #4. ~1 session.
5. **#4 (archive flow)** — only after #3 lands. ~half a session.

Items #1 and #2 are independent of the existing
[2026-04-28 SPDD plan](2026-04-28-spdd-ideas-worth-adopting-in-openup.md).
Item #5 is **complementary** to that plan's "fix-spec-first" rule (it tells
users where the *pre-spec* phase lives). Items #3 and #4 are independent
hygiene improvements.

---

## Critical Files (for any implementation step)

- `.claude/CLAUDE.openup.md` — central agent rules (#2, #5)
- `.claude/skills/openup-workflow/` — new skills land here (#1, #4, #5)
- `.claude/skills/openup-artifacts/` — templates read project-config (#2)
- `.claude/skills/openup-init/SKILL.md` — emits `project-config.yaml` (#2)
- `.claude/teammates/project-manager.md` — knows about readiness DAG (#1)
- `docs-eng-process/templates/` — frontmatter additions (#1), example config (#2)
- `docs-eng-process/conventions.md` — per-task folder convention (#3)
- `.claude/rubrics/` — unchanged; project rules layer on top (#2)

No hook changes proposed in this plan; enforcement stays advisory.

---

## Verification

**#1 (readiness DAG):** generate a readiness readout for a real in-flight task
(T-002) and confirm it identifies the correct missing dependency (use case
exists? architecture notebook section exists? iteration-plan entry exists?).
Bonus: re-edit a dependency and confirm the dependent flips to STALE.

**#2 (project-config.yaml):** add a fake project rule
(`rules.use-case: ["Must reference a stakeholder by name"]`), run
`/openup-create-use-case`, confirm the rule is injected into the prompt and
the generated use case satisfies it. Then remove the rule and confirm the
behaviour reverts.

**#3 (per-task folder):** run `/openup-create-task-spec` against a fresh task
and confirm the folder layout is created; existing flat task files still
render correctly.

**#4 (archive flow):** complete a small task end-to-end with archive enabled;
verify the folder is moved and the roadmap link is rewritten.

**#5 (explore mode):** start a real exploration of a hypothetical problem,
confirm `docs/explorations/` artifact is created, confirm "Where this goes
next" section is required, confirm CLAUDE.openup.md's revised rule prevents
treating exploration as deliverable work.

---

## SPDD Self-Grading

Per the convention established by `2026-04-28-spdd-evaluation.md`, this plan
should be graded against the SPDD dimensions before it is acted on. The
companion evaluation lives in
[`2026-05-13-openspec-evaluation.md`](2026-05-13-openspec-evaluation.md).

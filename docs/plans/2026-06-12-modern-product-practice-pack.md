# Modern Product Practice Pack

**Status**: `in-progress` (2026-06-12 — T-024…T-028 delivered; T-029 pending)
**Created**: 2026-06-12
**Priority**: high
**Goal**: Layer modern product-delivery practices on top of OpenUP — a product-manager role that influences the mechanical project manager, a falsifiable success measure per feature, feature-flagged rollouts, multi-environment deployment config, and a product-manager challenge pass in `/openup-explore`.
**Exploration**: [explorations/2026-06-12-modern-product-practices-on-openup.md](../explorations/2026-06-12-modern-product-practices-on-openup.md)

---

## Hard Guardrail: Change Surface

Owner rule (2026-06-12): **we never modify the OpenUP artifacts; we modify the
claude-templates.**

- **Read-only**: `openup-knowledge-base/**` (vendored, converter-generated) and
  `docs-eng-process/templates/**` (OpenUP-derived document templates). The KB is
  *cited* as the anchor for each practice, never edited.
- **Change surface**: `docs-eng-process/.claude-templates/**` — skills,
  teammates, teams, rubrics, `CLAUDE.md` — plus `scripts/` tooling where derived
  data requires it (`openup-board.py`), and `docs-eng-process/*.md` guide docs
  as *pointer documentation only* (no process rules live there).
- **Consequence for design**: new spec sections (Success Measures, Rollout) are
  introduced through the `openup-create-task-spec` **skill instructions** and
  graded by the **task-spec rubric** — the base template file is not touched.
  Authored spec *instances* in `docs/changes/T-NNN/plan.md` carry the sections;
  the OpenUP-derived template stays pristine.

This is the existing precedence chain doing its job: framework rubric → project
rules → safeguards, where a layer adds criteria and never waives base ones.

---

## Context

OpenUP (2012) anchors three of the four practices but never operationalizes
them for modern delivery, and our claude-templates layer doesn't surface them
at all:

1. **Value-based prioritization** — the KB has a Product Owner capability
   pattern ("prioritize features according to market value", ROI
   accountability) and rules that paying stakeholders have final say; our
   teammates have only a `project-manager`, the roadmap carries a bare
   high/medium/low priority, and the iteration-plan rubric has zero
   business-value criteria.
2. **Per-feature outcome measurement** — KB metrics are process/quality
   metrics; the vision rubric requires project-level success metrics; nothing
   asks "how will we know this feature worked?" per feature, and nothing reads
   measures back after release.
3. **Feature flags** — absent from the KB entirely, but compose cleanly as a
   modern implementation of the existing "Develop Backout Plan" deployment
   task.
4. **Multi-environment deployment** — the Transition phase already sanctions
   beta testing and parallel-run; environments are just not modeled as a
   declared, ordered chain with promotion criteria.

Owner decisions already taken (recorded in the exploration, not re-litigated
here):

- The **product manager influences; the project manager executes
  mechanically.** Value ordering is an *input* to the board loop
  (`/openup-next`, `.openup/board.json`); the project-manager side sequences
  within the given order using only mechanical constraints (deps, readiness,
  collisions, risk) and never re-prioritizes.
- `/openup-explore` must make the product manager an **involved role**: a
  mandatory pushback / complement / refine pass on human-submitted ideas,
  recorded in the exploration file, each challenge acceptable or vetoable.
- Per the exploration's own challenge pass: measurement is **one falsifiable
  expectation** per feature (impact / engagement / returned value as prompts,
  not three required slots); environments are an **ordered list** with
  staging → beta → production as the documented example, not the schema; the
  measure→re-prioritize **read-back loop** is core scope; every flag enqueues
  its own removal task.

---

## Current State

- `.claude-templates/teammates/` — analyst, architect, developer,
  project-manager, scribe, tester. No product-facing role. The
  project-manager file already defines the mechanical orchestrator protocol
  (decompose → pointer-brief → collect → synthesize) this pack feeds into.
- `docs/roadmap.md` tables — `| ID | Title | Status | Priority | Depends on |`.
  No value rationale; ordering is implicit.
- `.claude-templates/rubrics/task-spec-rubric.md` — 11 criteria, ending at
  "10. Behavior Delta Completeness" and "11. Scenario Coverage" (with the
  track-exemption idiom this pack reuses). Nothing on value, measures, or
  rollout.
- `.claude-templates/rubrics/iteration-plan-rubric.md` — 7 execution-focused
  criteria; no business value.
- `.claude-templates/skills/openup-explore/SKILL.md` — explicitly "no team, no
  rubrics"; freeform notes + a disposition. No challenge step.
- `.claude-templates/skills/openup-transition/SKILL.md` — single-hop
  transition; no environment chain awareness.
- `scripts/openup-board.py` — derives `.openup/board.json` from change-folder
  frontmatter + roadmap + leases; selection takes the top READY lane.
- `docs/project-config.yaml` mechanism (T-018) — `context:` + `rules:` keys
  injected into every `/openup-create-*` skill; the natural home for
  project-specific environment names, flag tooling, and value-scale wording.

---

## Proposed Design

Six tasks. Letters reference the exploration's sketch deltas.

### T-024 (delta 1) — `product-manager` teammate: value authority over a mechanical PM `HIGH / MED`

Add `.claude-templates/teammates/product-manager.md` (+ `-compact` variant),
grounded in the KB Product Owner pattern (cite it; don't copy it). The role:

- Owns the **value ordering** of `docs/roadmap.md` and writes a one-line value
  rationale per entry (new `Value` column or a `**Value**:` line per plan
  block — pick whichever survives `openup-board.py` parsing untouched).
- Self-briefs per the T-016 idiom (`## On Start, Read` block: status, roadmap,
  vision, and the measures read-back input once T-028 lands).
- **Influences, never executes**: the project-manager teammate and
  `/openup-next` consume roadmap order as given. Add one sentence to
  `project-manager.md` and `CLAUDE.md` codifying the boundary: the PM/board
  may *skip* an item only for mechanical reasons (deps, collisions, lease)
  and must surface — not resolve — value disagreements to the
  product-manager role.
- Register the role: `CLAUDE.md` roles list, and add product-manager to
  `teams/openup-planning-team.md` + `teams/openup-full-team.md` (teams stay
  opt-in per current policy).

**Files**: `teammates/product-manager.md` (new), `teammates/product-manager-compact.md`
(new), `teammates/project-manager.md`, `CLAUDE.md`,
`teams/openup-planning-team.md`, `teams/openup-full-team.md`,
`skills/openup-plan-feature/SKILL.md` + `skills/openup-start-iteration/SKILL.md`
(read/write the value rationale), `scripts/openup-board.py` **only if** the
roadmap-format change breaks its parsing (verify first).
**Verify**: cold-start a product-manager-hat session; confirm it can re-order
the roadmap with rationale and that `/openup-next` then claims tasks in the new
order without re-judging value. Confirm the PM role refuses to re-prioritize.
**Depends on**: none.

> **Delivered 2026-06-12.** `teammates/product-manager.md` + compact variant
> created; influence boundary codified in `project-manager.md` (Planning
> Approach + When-to-Involve), `CLAUDE.md` (new rule + roles list), planning +
> full team configs; `plan-feature` writes the `**Value**:` rationale on new
> roadmap entries; `start-iteration` consumes the order as given (mechanical
> skip reasons only). `scripts/openup-board.py` verified untouched-safe: it
> derives lanes from change-folder frontmatter only and never parses the
> roadmap, so the `Value` field cannot break it — no script change shipped.

### T-025 (delta 2) — Per-feature success measure: one falsifiable expectation `HIGH / LOW–MED`

`openup-create-task-spec` skill gains a required authoring step: every
`standard`/`full`-track spec includes a `## Success Measures` section with **one
falsifiable expectation** — "we expect *measure X* to move by *Y* within *Z* of
release" — using impact / engagement / returned value as prompts. `quick` track
may write `n/a — <reason>` (mirrors criterion 11's track-exemption idiom).
`openup-complete-task` verifies the *instrumentation* for the measure exists
(an event, metric, query — named in the section), not just the feature code.

**Files**: `skills/openup-create-task-spec/SKILL.md`,
`rubrics/task-spec-rubric.md` (new criterion 12: Success Measure
falsifiability — measure named, direction+magnitude stated, read-back date
stated, or argued n/a on quick track),
`skills/openup-complete-task/SKILL.md` (instrumentation check),
`skills/openup-plan-feature/SKILL.md` (plan-level prompt).
**Verify**: author a spec without a measure → rubric fails criterion 12; with a
vanity measure ("users will like it") → fails falsifiability; with "expect
weekly active editors +10% within 30 days, event `editor_active`" → passes;
complete-task blocks if `editor_active` instrumentation is absent from the diff.
**Depends on**: none. Per the guardrail, the section ships via skill+rubric —
`docs-eng-process/templates/task-spec.md` is **not** edited.

> **Delivered 2026-06-12.** `create-task-spec` Round 1 (analyst) now drafts
> `## Success Measures` with the falsifiable-expectation format (measure,
> direction+magnitude, window, instrumentation, read-back date) — explicitly
> noting the section is added at drafting time because the OpenUP-derived
> template is read-only. Rubric criterion 12 (Success Measure Falsifiability)
> grades it, incl. unargued-`n/a` and instrumentation-nothing-creates gaps;
> criteria counts in the skill bumped 11→12. `complete-task` gains BLOCKING
> step 1b: instrumentation must exist in the diff (or demonstrably pre-exist),
> grade + read-back date recorded in `design.md` for the retrospective (T-028
> consumes this). `plan-feature` plan template gains a `## Success Measure`
> section as the upstream prompt.

### T-026 (delta 3) — Rollout & feature-flag strategy `MED / LOW–MED`

`openup-create-task-spec` gains a `## Rollout` authoring step for
`standard`/`full` user-facing changes: flagged or not (with reason), default
state per environment, kill-switch, and — **mandatory if flagged** — a named
flag-removal follow-up. `openup-complete-task` enforces the debt rule: completing
a flagged feature **enqueues the flag-removal task into `docs/roadmap.md`**
(maintenance section) before "done" is legal. Flag hygiene guidance (naming,
expiry, cleanup) lives inside the skill instructions — KB framing: a flag is the
modern implementation of OpenUP's "Develop Backout Plan" task, cheaper than a
redeploy.

**Files**: `skills/openup-create-task-spec/SKILL.md`,
`rubrics/task-spec-rubric.md` (new criterion 13: Rollout strategy stated;
flagged ⇒ removal task named), `skills/openup-complete-task/SKILL.md`
(enqueue removal task).
**Verify**: spec a flagged feature; confirm rubric requires the removal task;
complete it; confirm a `T-NNN flag removal` row appears in the roadmap
maintenance table.
**Depends on**: none.

> **Delivered 2026-06-12.** `create-task-spec` Round 1 (architect) drafts
> `## Rollout` — flagged-or-not with reason, flag name, per-environment
> default states (project-config `environments:` names when defined — the
> T-027 hook), kill-switch behavior, and a mandatory named flag-removal
> follow-up; KB-framed as the modern *Develop Backout Plan*. Rubric
> criterion 13 (Rollout Strategy) grades it; criteria counts 12→13.
> `complete-task` gains BLOCKING step 3a: a flagged feature cannot complete
> until its flag-removal row exists in the roadmap Maintenance table (new
> task ID recorded in `design.md`).

### T-027 (delta 4) — `environments:` in project config, consumed by transition `MED / LOW`

Document and consume a project-owned `environments:` key in
`docs/project-config.yaml`: an **ordered list** of environments, each with
`name` and `promotion:` criteria (free-text, checkable). Example — not schema —
is `staging → beta → production`. `openup-transition` maps its KB beta-test
objective onto the configured pre-production environment(s) and walks the chain
hop by hop (promotion criteria become the hop's checklist) instead of a single
hop to prod. `openup-create-task-spec`'s Rollout section (T-026) references
environment names from config when present.

**Files**: `skills/openup-transition/SKILL.md`,
`skills/openup-init/SKILL.md` (emit commented `environments:` starter in the
generated project config), `skills/openup-create-task-spec/SKILL.md` (consume
names), `docs-eng-process/project-config.md` (document the key — guide doc,
pointer documentation per the guardrail).
**Verify**: with a 3-env config, run transition planning; confirm one
promotion checklist per hop and beta-test objectives land on `beta`. With no
`environments:` key, confirm unchanged single-hop behavior (additive layer).
**Depends on**: T-026 (Rollout section is the consumer in specs); transition
side can land independently.

> **Delivered 2026-06-12.** `openup-transition` gains step 0 (Load the
> Environment Chain): walks the configured ordered `environments:` hop by hop
> with one promotion checklist per hop, maps OpenUP's beta-test objective onto
> the pre-production entries, and `check-status` reports which environment the
> release sits in; absent key → unchanged single-hop default. `openup-init`
> **appends** a commented `environments:` starter after copying the example
> config (the OpenUP-layer template stays read-only per the guardrail).
> `environments:` documented as the third top-level key in
> `docs-eng-process/project-config.md` (guide doc — the mechanism's single
> source). Spec-side consumption (Rollout default states per environment)
> already landed in T-026.

### T-028 (deltas 1+2 closing the loop) — Measure read-back → re-prioritization `HIGH / LOW`

The loop that makes T-024 and T-025 more than paperwork: each feature's
Success Measure carries a read-back date; `openup-retrospective` gains a
**measure read-back step** — list completed features whose read-back date has
passed, record actual vs expected in the retro doc — and the product-manager
role's duties include consuming that section to re-rank the roadmap (with
rationale updates). Without this, value prioritization stays opinion-based.

**Files**: `skills/openup-retrospective/SKILL.md`,
`teammates/product-manager.md` (read-back duty in On Start, Read),
`skills/openup-complete-task/SKILL.md` (carry the read-back date into the
completion record so retro can find it).
**Verify**: complete a feature with a 0-day read-back window; run
`/openup-retrospective`; confirm the actual-vs-expected entry appears and the
product-manager pass updates the roadmap value rationale citing it.
**Depends on**: T-024, T-025.

> **Delivered 2026-06-12.** `openup-retrospective` gains step 4b (Measure
> Read-Back): scans `docs/changes/archive/*/design.md` for the grades +
> read-back dates `/openup-complete-task` step 1b records (T-025), reads the
> named instrumentation for entries whose date passed, writes
> expectation/actual/verdict into a new **Measure Read-Back** retro section,
> and hands it to the product-manager role for the re-rank (evidence-citing
> `Value` updates; "no re-rank" recorded when honest). Read-backs due before
> the next retro become owned action items. Product-manager role (full +
> compact) gains the measure-evidence reading duty in On Start, Read and the
> consume-read-back responsibility. Complete-task side needed no change —
> T-025 already persists the date.

### T-029 (delta 5) — Product-manager challenge pass in `/openup-explore` `MED / LOW`

`openup-explore` gains a mandatory step between Notes and disposition: assume
the product-manager **role hat** (read `teammates/product-manager.md` — *not* a
team deployment; the skill's "no team, no rubrics" stance is preserved) and
write a `### Product-manager challenge pass` section — pushback (which
submitted ideas are weak and why), complement (what the human missed), refine
(sharpen question/options). Each challenge is accepted into the notes or
explicitly rejected with a reason. Success criteria gain the matching checkbox.
The 2026-06-12 exploration's own challenge pass is the reference example.

**Files**: `skills/openup-explore/SKILL.md`, `teammates/product-manager.md`
(challenge-pass duty).
**Verify**: run an exploration from a deliberately thin human idea; confirm the
challenge pass produces ≥1 pushback and the disposition reflects accepted
refinements; confirm no team is deployed.
**Depends on**: T-024 (the role file must exist).

---

## Dependencies

```
T-024 ──► T-028 ◄── T-025      [role + measures close into the read-back loop]
T-024 ──► T-029                [explore challenge pass needs the role file]
T-026 ──► T-027 (spec-side consumption only; transition side independent)
```

T-024 and T-025 are the headline pair; T-026/T-027 can run in a parallel lane;
T-028 and T-029 are short closers.

---

## Out of Scope

- Any edit to `openup-knowledge-base/**` or `docs-eng-process/templates/**`
  (hard guardrail above).
- Replacing the project-manager role — product-manager sits alongside and
  influences it (owner decision).
- Implementing actual flag tooling or analytics pipelines — the framework
  requires the *sections and gates*; tooling is project-owned
  (`project-config.yaml` `context:` names it).
- Gating `/openup-complete-task` on production deployment — "done" semantics
  unchanged (see Open Questions / assumptions).
- Numeric value-scoring schemes (RICE, WSJF) — qualitative rationale + explicit
  ordering only, until measure read-back (T-028) gives numbers a basis.

---

## Open Questions

Ambiguity-gate output — all classified non-blocking; defaults recorded as
vetoable assumptions:

1. **Assumed:** `docs-eng-process/templates/task-spec.md` counts as an OpenUP
   artifact under the new guardrail (even though the REASONS canvas is
   framework-authored and T-015/T-019/T-020 edited it). New sections therefore
   ship via skill instructions + rubric criteria only. *Vetoable — if the owner
   scopes the rule to the KB + KB-derived templates only, T-025/T-026 simplify
   to template edits.*
2. **Assumed:** value scale is a qualitative one-line rationale + explicit
   roadmap ordering — no numeric scoring column. *Vetoable at review.*
3. **Assumed:** Success Measures / Rollout are required on `standard`+`full`
   tracks, `n/a — reason` on `quick` (mirrors criterion 11's idiom).
4. **Assumed:** measure read-back lives in `/openup-retrospective` (T-028), not
   a new `/openup-measure-impact` skill — fewest moving parts; revisit if retro
   cadence proves too coarse.
5. **Assumed:** "done" stays at merged + verified + first-environment deploy;
   promotion through the chain is transition-phase work, not a complete-task
   gate.

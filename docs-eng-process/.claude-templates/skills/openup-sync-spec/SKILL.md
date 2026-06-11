---
name: openup-sync-spec
description: Back-propagate pure refactors to stale artifacts; classify the diff, refuse behaviour-changes, propose targeted edits for approval (read-only by default)
model: inherit
fit:
  great: [reconciling artifacts after a rename/extract/move refactor, "did my cleanup leave the spec stale", detecting + routing behaviour-changes back to spec-first]
  ok: [setting a fresh last-synced baseline on a never-synced artifact, single-artifact sync after a targeted diff]
  poor: [authoring new behaviour spec-first (use the originating /openup-create-* skill), wholesale doc regeneration, applying writes without user approval]
arguments:
  - name: since
    description: "Optional. Diff baseline — a git ref or \"last commit\". Defaults to each artifact's own last-synced front-matter SHA; falls back to never-synced handling when unset."
    required: false
  - name: artifact
    description: "Optional. Restrict the run to one artifact type (use-case-specification | architecture-notebook | iteration-plan | task-spec). Defaults to all four candidates."
    required: false
---

# Sync Spec

Back-propagate **pure refactors** into the artifacts they touched. This skill is the
refactor-only half of the **"Fix the spec first"** rule: behaviour changes go
*spec-first* through the originating `/openup-create-*` skill; pure refactors go
*code-first* and then reconcile here. It diffs code against each artifact's
`last-synced` git ref, classifies the diff, and — **only** for refactor diffs —
proposes targeted section edits for the user to approve, then bumps the ref.

**This skill is READ-ONLY BY DEFAULT.** Steps 1–5 read and propose only. The single
write point (step 6) is gated on explicit user approval and executed by the
`openup-scribe` agent. It never regenerates a whole document and never auto-writes.

> **Refactor-only skill (`model: inherit`).** Classification needs judgment — unlike the
> mechanical readiness skill, this one reasons about whether a diff changes behaviour.
> When in doubt it **refuses** and routes spec-first. The cost asymmetry below is
> load-bearing: refusing a true refactor costs one re-run; silencing a behaviour change
> reintroduces exactly the drift this skill exists to prevent.

## Inputs

1. **Per-artifact baseline — `last-synced` front-matter.** Each of the four artifact
   types carries an optional `last-synced` key (full 40-char git SHA, or `""`). This is
   the diff base for that artifact. Empty / absent = **never synced**.
2. **The diff range.** `git diff <last-synced>..HEAD` per artifact, or the `since`
   argument if supplied (a git ref, or `"last commit"` → `HEAD~1..HEAD`).
3. **The artifacts themselves.** The four bounded types and their headings:
   `use-case-specification.md`, `architecture-notebook.md`, `iteration-plan.md`,
   `task-spec.md`. An unknown artifact type is reported and skipped, never guessed at.

## Diff classification (drop-in heuristic)

Run `git diff <last-synced>..HEAD` (use `--stat` first for the file map, then full
hunks for changed files). Classify the **whole diff** as **REFACTOR** only if
*every* hunk matches a refactor signal and *no* hunk matches a behaviour signal.
If any behaviour signal fires, or the diff is ambiguous, classify as
**BEHAVIOUR-CHANGE**. This asymmetry is intentional: refusing a true refactor costs
one re-run; mislabelling a behaviour change silences exactly the drift SPDD warns
against.

**REFACTOR signals (safe to back-propagate):**
- Symbol **rename** with all call sites updated in the same diff (identifier churn,
  no new branches).
- **Extract / inline** method or variable — same inputs/outputs, control flow
  preserved.
- **Move** a file/symbol across modules with no signature change (path churn only).
- **Formatting / whitespace / import reordering**; comment or docstring edits.
- Type-only annotations that do not change runtime behaviour.
- Test-only changes that track a rename (no new assertions on new behaviour).

**BEHAVIOUR-CHANGE signals (refuse — go spec-first):**
- **Public API signature change**: added/removed/reordered parameters, changed
  return type, changed exported/visibility surface, renamed *public* endpoint/route.
- **Business-logic / conditional change**: added or altered `if`/`switch`/loop
  conditions, changed constants/thresholds, new/removed early returns, changed error
  handling or validation rules.
- **Acceptance-criteria-affecting change**: anything that would alter what a use-case
  scenario, an iteration-plan objective, or a task-spec requirement asserts as the
  observable end state.
- **New or deleted feature surface**: new functions/endpoints/flags that did not
  exist at `last-synced`, or removed capability.
- **Data-shape / schema / contract change**: persisted format, serialized payload,
  config keys, migration.

**Ambiguity rule:** if a diff mixes refactor and behaviour hunks, or you cannot
confidently place a hunk, classify the **whole run** as BEHAVIOUR-CHANGE and refuse.
Do not partially sync a mixed diff.

## Process

Run this linear, read-only pipeline. Treat all four artifact types as candidates (or
the single type named by `artifact`); skip any whose `touches`/content is unrelated to
the diff.

### 1. Resolve baseline

Read each artifact's `last-synced`. If empty / absent → **never-synced handling**:
report `no baseline (last-synced unset) — set a baseline by approving the current HEAD
as the reference, or run the originating /openup-create-* skill` and take **no** edit
action unless the user explicitly asks to set the baseline to `HEAD`. Do not invent a
baseline or diff the whole history. Otherwise use the SHA (or the `since` argument) as
the diff base.

### 2. Diff

`git diff <last-synced>..HEAD` — `--stat` first for the file map, then full hunks for
the changed files.

### 3. Classify

Apply the **Diff classification heuristic** above. A **BEHAVIOUR-CHANGE** verdict
(including ambiguous) short-circuits the flow — **no** section detection, **no** edit
proposal, **no** scribe call, **no** `last-synced` bump. Emit the refusal (below) and
STOP for that run.

### 4. Detect stale sections (refactor only)

Build the set of changed **files and symbols** from the diff (renamed-from/to pairs,
moved paths, extracted names). A section is **likely stale** iff its prose names one of
those files or symbols — the *old* name on the left of a rename is the strongest
signal. Scope the match to the artifact's own headings. Report each candidate as:

```
<artifact> › <section heading> — names <symbol/file>, changed by <rename|move>
```

Sections that name nothing in the changed set are left **untouched**.

### 5. Propose targeted edits

For each stale section, draft the **minimal** edit (old symbol → new symbol, old path →
new path). Present all proposals across all artifacts as **one unified review block**
before any write. **Never regenerate a whole document; never auto-write.**

### 6. Apply on approval (write path)

Only after **explicit user approval**, delegate the writes to the **`openup-scribe`**
agent (Agent tool, `subagent_type: "openup-scribe"`) — the orchestrator decides the
values, the scribe only writes. The same approved batch applies the section edits
**and** bumps `last-synced` to the current `HEAD` SHA. One scribe brief per touched
artifact; the scribe reports the exact lines changed.

- The bump and the section edits are **one atomic, user-approved write per artifact** —
  never a silent or standalone bump.
- Bump `last-synced` **only** on artifacts whose edits were applied this run; never
  bump an artifact the user deferred (avoids divergent baselines on the next run).
- If the working tree is dirty/uncommitted, resolve `HEAD` after the user commits, or
  record the SHA the diff was computed against — never bump to a SHA the edits were not
  validated against.

> **Commit hygiene note.** The refactor-vs-behaviour split is only meaningful when
> refactors and behaviour changes land in *separate* commits/ranges. A mixed commit
> forces a whole-run refusal (correct, but blocking). Commit refactors separately so
> this skill can act on a clean range.

## Behaviour-change refusal (drop-in)

On BEHAVIOUR-CHANGE (including ambiguous), stop before any edit, name the offending
signal, and route the user to the originating skill. Never offer a "force / sync
anyway" escape hatch.

**Artifact → originating skill routing map:**

| Artifact | Originating skill |
|---|---|
| `use-case-specification.md` | `/openup-create-use-case` |
| `architecture-notebook.md` | `/openup-create-architecture-notebook` |
| `iteration-plan.md` | `/openup-create-iteration-plan` |
| `task-spec.md` | `/openup-create-task-spec` |

**Refusal message (print verbatim, filling in the concrete signal and file/symbol):**

> **`/openup-sync-spec` refused — this diff changes behaviour, not just structure.**
>
> `<last-synced>..HEAD` contains a behaviour signal: **`<signal name, e.g. "public
> API signature change in src/foo.py:bar()">`**. Back-propagation is only for pure
> refactors; a behaviour change must update the spec **first** (the "Fix the spec
> first" rule), then the code.
>
> Re-run the originating skill for each affected artifact, then bring the code in
> line:
> - use-case → `/openup-create-use-case`
> - architecture notebook → `/openup-create-architecture-notebook`
> - iteration plan → `/openup-create-iteration-plan`
> - task spec → `/openup-create-task-spec`
>
> If you believe this is genuinely a refactor, narrow the diff (commit the
> behaviour change separately) and re-run `/openup-sync-spec` on the
> refactor-only range.

The refusal always lists all four routes (the skill does not assume which artifact the
user cares about).

## Safeguards

- **Read-only by default.** Steps 1–5 read and propose only. The single write point is
  step 6, gated on explicit user approval and executed by the scribe.
- **Targeted, never wholesale.** No full-doc regeneration; edits are confined to
  flagged sections.
- **Bounded scope.** Only the four known artifact types
  (`use-case-specification`, `architecture-notebook`, `iteration-plan`, `task-spec`).
  An unknown artifact type is reported and skipped, not guessed at.
- **No false-positive silencing.** Ambiguous → BEHAVIOUR-CHANGE → refuse.

## Success Criteria

After this skill runs, ALL of these must be true:

- [ ] The diff was classified REFACTOR or BEHAVIOUR-CHANGE by the documented heuristic.
- [ ] A BEHAVIOUR-CHANGE (or ambiguous) verdict produced the refusal + routing and
      wrote nothing.
- [ ] For a REFACTOR, only sections naming changed files/symbols were flagged; no whole
      document was regenerated.
- [ ] No artifact was written without explicit user approval.
- [ ] `last-synced` was bumped to `HEAD` **only** on artifacts whose edits were applied
      this run, in the same approved scribe batch as the section edits.
- [ ] Never-synced artifacts were reported (no auto-edit) unless the user asked to set a
      baseline.

## See Also

- [openup-complete-task](../complete-task/SKILL.md) — closes the task whose code these
  artifacts describe; run sync-spec before completing if a refactor left specs stale
- [openup-readiness](../readiness/SKILL.md) — sibling read-only skill; reads the same
  change-folder frontmatter this skill keeps in sync
- `/openup-create-use-case`, `/openup-create-architecture-notebook`,
  `/openup-create-iteration-plan`, `/openup-create-task-spec` — the spec-first path for
  behaviour changes this skill refuses

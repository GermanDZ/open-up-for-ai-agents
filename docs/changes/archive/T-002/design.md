# T-002 Design — `/openup-sync-spec`

> Decisions doc (architect, construction). The generic UML `templates/design.md`
> is a poor fit for a single read-only skill; this is a clean decisions doc keyed
> to the four design decisions a developer must implement. Authoritative spec:
> [`plan.md`](./plan.md). Sibling shape to match:
> [`readiness/SKILL.md`](../../../.claude/skills/openup-workflow/readiness/SKILL.md)
> (read-only analysis skill, exhaustive mechanical rules, no judgment).

## Context & altitude

`/openup-sync-spec` is a **read-only-by-default, architect-led** skill that lives at
`.claude/skills/openup-workflow/openup-sync-spec/SKILL.md`. It is the *refactor-only*
half of the "Fix the spec first" rule in `CLAUDE.openup.md`: behaviour changes go
spec-first through the originating `/openup-create-*` skill; pure refactors go
code-first and then back-propagate to artifacts here. The skill diffs code against
each artifact's last-synced git ref, classifies the diff, and — only for refactor
diffs — proposes targeted section edits for user approval, then bumps the ref.

It writes nothing without explicit user approval (Safeguard: read-only by default).
When classification is uncertain it **refuses** (Safeguard: no false-positive
silencing — default to behaviour-change). The skill never regenerates whole docs.

`model:` should be `inherit` (classification needs judgment, unlike the mechanical
`haiku` readiness skill). Writes are delegated to the `openup-scribe` agent, matching
`complete-task`'s scribe pattern.

---

## DD1 — `last-synced` front-matter convention

**Verdict: a single optional `last-synced` YAML field holding a full git SHA (or
empty), present on all four artifact types, updated by the scribe to `HEAD` after an
approved sync.**

- **Field name:** `last-synced` (kebab-case, matches existing `task-spec.md` and the
  coordination frontmatter style).
- **Value format:** the **full 40-char git commit SHA** of the code state the artifact
  was last reconciled against — *not* a short SHA (short SHAs collide and are
  ambiguous across `git diff` invocations). Empty string `""` = never synced.
- **Carried by all four artifacts:**
  `use-case-specification.md`, `architecture-notebook.md`, `iteration-plan.md`,
  `task-spec.md`.
- **Placement caveat (developer must handle):** `task-spec.md` already declares
  `last-synced: ""` inside a clean YAML frontmatter block (line 10). The other three
  templates carry a **legacy metadata block** (`title:`/`source_url:`/`uma_name:`…),
  not a coordination frontmatter block. The developer adds `last-synced: ""` as a new
  key **into that existing YAML block** (append after `keywords:`/`related:`); do NOT
  introduce a second frontmatter fence. One commented line documenting the field:
  `last-synced: ""   # full git SHA of last code↔spec sync (set by /openup-sync-spec)`.
- **Optional / absent semantics:** the field is **optional**. An artifact with no
  `last-synced` key, or `last-synced: ""`, is treated as **never synced** and still
  validates (no rubric/gate may require it). For a never-synced artifact the skill
  does NOT invent a baseline or diff the whole history — it reports
  `no baseline (last-synced unset) — set a baseline by approving the current HEAD as
  the reference, or run the originating /openup-create-* skill` and takes no edit
  action unless the user explicitly asks to set the baseline to `HEAD`.
- **How the skill updates it (write path):** after the user approves a refactor sync
  for an artifact, the **scribe** rewrites that artifact's `last-synced` value to the
  current `HEAD` SHA *in the same approved edit batch* as the section edits. The bump
  and the section edits are one atomic, user-approved write per artifact — never a
  silent or standalone bump. If section edits are approved but the artifact is in a
  dirty/uncommitted state, the skill resolves `HEAD` after the user has committed, or
  records the SHA the diff was computed against; it must not bump to a SHA the edits
  were not validated against.

---

## DD2 — Diff-classification heuristic (refactor vs behaviour-change)

**Verdict: an inspectable signal table the model applies to
`git diff <last-synced>..HEAD`; ANY behaviour signal → behaviour-change; ambiguous →
behaviour-change. This prose is dropped verbatim into the SKILL.md (Norms: the
heuristic must be documented in the skill for transparency).**

> ### Diff classification (drop-in skill prose)
>
> Run `git diff <last-synced>..HEAD` (use `--stat` first for the file map, then full
> hunks for changed files). Classify the **whole diff** as **REFACTOR** only if
> *every* hunk matches a refactor signal and *no* hunk matches a behaviour signal.
> If any behaviour signal fires, or the diff is ambiguous, classify as
> **BEHAVIOUR-CHANGE**. This asymmetry is intentional: refusing a true refactor costs
> one re-run; mislabelling a behaviour change silences exactly the drift SPDD warns
> against.
>
> **REFACTOR signals (safe to back-propagate):**
> - Symbol **rename** with all call sites updated in the same diff (identifier churn,
>   no new branches).
> - **Extract / inline** method or variable — same inputs/outputs, control flow
>   preserved.
> - **Move** a file/symbol across modules with no signature change (path churn only).
> - **Formatting / whitespace / import reordering**; comment or docstring edits.
> - Type-only annotations that do not change runtime behaviour.
> - Test-only changes that track a rename (no new assertions on new behaviour).
>
> **BEHAVIOUR-CHANGE signals (refuse — go spec-first):**
> - **Public API signature change**: added/removed/reordered parameters, changed
>   return type, changed exported/visibility surface, renamed *public* endpoint/route.
> - **Business-logic / conditional change**: added or altered `if`/`switch`/loop
>   conditions, changed constants/thresholds, new/removed early returns, changed error
>   handling or validation rules.
> - **Acceptance-criteria-affecting change**: anything that would alter what a use-case
>   scenario, an iteration-plan objective, or a task-spec requirement asserts as the
>   observable end state.
> - **New or deleted feature surface**: new functions/endpoints/flags that did not
>   exist at `last-synced`, or removed capability.
> - **Data-shape / schema / contract change**: persisted format, serialized payload,
>   config keys, migration.
>
> **Ambiguity rule:** if a diff mixes refactor and behaviour hunks, or you cannot
> confidently place a hunk, classify the **whole run** as BEHAVIOUR-CHANGE and refuse.
> Do not partially sync a mixed diff.

---

## DD3 — Behaviour-change guard + refusal

**Verdict: on BEHAVIOUR-CHANGE (including ambiguous), the skill stops before any edit,
prints a fixed refusal naming the offending signal, and routes the user to the
originating `/openup-create-*` skill per the map below.**

- **Guard placement:** classification (DD2) runs *before* stale-section detection.
  A BEHAVIOUR-CHANGE verdict short-circuits the flow — no section detection, no edit
  proposal, no scribe call, no `last-synced` bump.
- **Routing map (artifact → skill):**

  | Artifact | Originating skill |
  |---|---|
  | `use-case-specification.md` | `/openup-create-use-case` |
  | `architecture-notebook.md` | `/openup-create-architecture-notebook` |
  | `iteration-plan.md` | `/openup-create-iteration-plan` |
  | `task-spec.md` | `/openup-create-task-spec` |

  (Command names verified against `.claude/skills/openup-artifacts/*/SKILL.md`
  `name:` frontmatter.)

- **Refusal message (drop-in wording):**

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

- The refusal **names the concrete signal and file/symbol** so the user can act, and
  always lists all four routes (the skill does not assume which artifact the user
  cares about). It never offers a "force / sync anyway" escape hatch.

---

## DD4 — Skill flow & stale-section detection

**Verdict: a linear read-only pipeline — resolve ref → diff → classify (DD2) →
[refuse on behaviour, DD3] → detect stale sections by symbol/file match → propose
targeted edits → on approval, scribe applies edits + bumps `last-synced` to HEAD.**

**Flow (per artifact, all four are candidates; skip any whose `touches`/content is
unrelated to the diff):**

1. **Resolve baseline.** Read the artifact's `last-synced`. If empty/absent → DD1
   never-synced handling (report, no auto-edit). Else use it as the diff base.
2. **Diff.** `git diff <last-synced>..HEAD` (`--stat`, then hunks for changed files).
3. **Classify** with the DD2 heuristic. BEHAVIOUR-CHANGE / ambiguous → emit the DD3
   refusal and STOP for that run.
4. **Detect stale sections (refactor only).** Build the set of changed
   **files and symbols** from the diff (renamed-from/to pairs, moved paths, extracted
   names). A section is **likely stale** iff its prose names one of those files or
   symbols (old name on the left of a rename is the strongest signal). Scope the match
   to the artifact's own headings; report each candidate as
   `<artifact> › <section heading> — names <symbol/file>, changed by <rename|move>`.
   Sections that name nothing in the changed set are left untouched.
5. **Propose targeted edits.** For each stale section, draft the **minimal** edit
   (e.g. old symbol → new symbol, old path → new path). Present all proposals across
   all artifacts as **one unified review block** before any write. **Never regenerate
   a whole document; never auto-write.**
6. **Apply on approval (write path).** Only after explicit user approval, delegate the
   writes to the **`openup-scribe`** agent (Agent tool, `subagent_type:
   "openup-scribe"`) — the orchestrator decides the values, the scribe only writes.
   The same approved batch applies the section edits **and** bumps `last-synced` to the
   current `HEAD` SHA (DD1). One scribe brief per touched artifact; scribe reports the
   exact lines changed.

**Safeguards (restate in skill):**
- **Read-only by default.** Steps 1–5 read and propose only. The single write point is
  step 6, gated on explicit user approval and executed by the scribe.
- **Targeted, never wholesale.** No full-doc regeneration; edits are confined to
  flagged sections.
- **Bounded scope.** Only the four known artifact types; an unknown artifact type is
  reported and skipped, not guessed at.

---

## Architecture risks (PM attention)

- **False-classification cost asymmetry is load-bearing — protect it.** The whole
  design leans on "ambiguous → refuse." If a future tweak makes the heuristic
  *lenient* to reduce annoying refusals, it silently reintroduces the drift the skill
  exists to prevent. Any change to DD2 should be reviewed as a safety regression, not
  a UX tweak.
- **Multi-artifact partial sync / atomicity.** A single diff can flag several
  artifacts; if the user approves some and rejects others (or a scribe write fails
  mid-batch), `last-synced` refs diverge across artifacts and the next run sees an
  inconsistent baseline. Mitigation: bump `last-synced` **only** on artifacts whose
  edits were applied this run; never bump an artifact the user deferred.
- **`last-synced` accuracy depends on commit hygiene.** The refactor-vs-behaviour
  split is only meaningful if refactors and behaviour changes land in *separate*
  commits/ranges. A mixed commit forces a whole-run refusal (correct but blocking).
  Worth a one-line note in the skill steering users to commit refactors separately —
  and a flag if T-001's spec-first rule isn't producing clean ranges in practice
  (this is the same drift trigger that un-defers T-002).

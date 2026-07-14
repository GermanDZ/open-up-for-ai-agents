# Exploration: the process map as the compiled navigator

**Started:** 2026-07-14
**Question:** Should loop navigation be the **deterministic execution of an
LLM-compiled process map** — the LLM compiles the (possibly customized) process
once at bootstrap into a machine-readable navigation artifact, and scripts drive
every cycle from it — replacing both the per-cycle LLM navigator (T-096) and the
hardcoded Inception bootstrap (T-097/T-098)?

## Context

Follows the deterministic-cycle-engine program
([2026-07-13-deterministic-cycle-engine.md](2026-07-13-deterministic-cycle-engine.md),
T-089/T-090/T-091) and the navigator arc (T-096 → T-097 → T-098 → T-099), all on
`harness-optional`. Prompted by a live driver of a fresh project (`my-product`,
qwen/qwen3.6-35b-a3b local model, 2026-07-13/14) that surfaced a series of seams
at the boundary between *"the LLM authors an artifact"* and *"deterministic
tooling parses/navigates it"*:

- **T-097** — the navigator raised an *input-request* for a missing stakeholder
  brief, which a text answer can't satisfy → non-converging loop. Fixed by
  scaffolding a fillable template.
- **T-098** — on a weak model the navigator sub-run sometimes finished without
  writing its decision file (exit 8). Fixed by a **hardcoded** deterministic
  bootstrap (no vision + no brief → scaffold brief; filled brief → run
  create-vision).
- **T-099** — create-vision authored a roadmap with the model's own `RDM-NNN`
  ids that `openup-roadmap.py` (`T-\d+`) skipped → "roadmap exhausted". Fixed by
  pinning the id format in the instruction. Also: a successful authoring run
  reported the sub-procedure's `DONE`, mis-guiding the wrapper.

The owner's observation (2026-07-14): the T-098 bootstrap **hardcodes** "inception
needs a brief → create-vision," which (a) is non-agnostic (breaks for a
customized OpenUP) and (b) duplicates what the process map + T-090 Plan Iteration
already know — the symptom being the redundant `initiate-project` lane that
re-authors the vision the bootstrap already made.

Two owner proposals, in sequence:
1. **Process-driven navigation** — inspect init state without requiring the brief
   upfront; let the process map drive the next activity; let the *activity*
   (create-vision) stop and ask for its input if missing. More agnostic.
2. **Compiled process map** — at bootstrap, use the LLM + scripts to read the
   process and emit a **custom mapping of phases/iterations/activities** that
   guides navigation **deterministically** on every subsequent cycle.

This exploration argues (2) subsumes (1) and is the right architecture.

## Notes

### The three positions we've oscillated between — all flawed

| Position | Agnostic? | Robust on a weak model? | Per-cycle cost |
|---|---|---|---|
| Framework-fixed `process-map.yaml` (T-077) | ✗ (one fixed process) | ✓ | ~0 (deterministic) |
| LLM navigator every cycle (T-096) | ✓ | ✗ (flaky decision file) | high (an LLM call to *decide*) |
| Hardcoded bootstrap (T-097/T-098) | ✗ (bakes brief→vision) | ✓ | ~0 |

Each trades away one of {agnostic, robust, cheap}. The synthesis keeps all three.

### The synthesis: compile once (LLM), execute deterministically (scripts)

The LLM is put where it is *reliable and cheap-amortized*: a **one-time compile**
of the process into a navigation artifact, reviewable by a human, validated by a
script. Thereafter navigation is a deterministic walk of that artifact — no
per-cycle LLM decision, no hardcoded process knowledge.

```
bootstrap (LLM, once):  read process (KB or custom) ─► emit process-map
                        (phases → iterations → activities → procedure → required-inputs)
                        ─► validate (script, hard gate) ─► human review
every cycle (scripts):  derive phase ─► Plan Iteration from activities-for(phase)
                        ─► run each activity's procedure
                        ─► if a declared input is missing: scaffold template + suspend
                        ─► LLM ONLY authors artifacts
```

The LLM's total responsibilities collapse to **two**: (a) compile the process
once, (b) author artifacts. It is **never** in the per-cycle navigation seat —
the purest expression of the T-080 thesis ("models author fine; they drown in
orchestration"; so never make orchestration an LLM job).

### It slots into existing infrastructure, doesn't replace it

`docs-eng-process/process-map.yaml` + `openup-process-map.py` (T-077) already are
the deterministic navigation source that T-090 Plan Iteration consumes. This
proposal **generalizes** that file from *framework-shipped-fixed* to
*project-compilable*, keeping `openup-process-map.py` as the sole consumer and the
existing schema as the base. Standard OpenUP projects can **use the shipped map
and skip compilation entirely**; the compile step earns its keep for (a)
*customized* processes and (b) the *input declarations* (below).

### The compiled map is where "activities declare their inputs" lives (finishes proposal 1)

The owner's proposal-1 ("let create-vision ask for the brief") is best realized as
**data in the compiled map**, not code and not a per-cycle LLM `ask_user`:

```yaml
activities:
  initiate-project:
    role: analyst
    procedure: openup-create-vision
    requires_input:
      path: docs/inputs/stakeholder-brief.md
      describe: "a stakeholder brief (who/problem/outcomes/constraints)"
    execution: direct        # run the procedure directly, no intermediate spec
```

Deterministic cycle: about to run `initiate-project` → its `requires_input.path`
is absent → scaffold a template there (the T-097 affordance, now **map-driven**)
and suspend (exit 5) with guidance. No "brief"/"vision" literal anywhere in code —
works for any first activity of any process.

`ask_user` (T-074) remains the *fallback* for inputs the map didn't anticipate
(the authoring sub-run can still suspend on a surprise), but the **common**
required inputs are declared, so the deterministic layer handles them without an
LLM turn.

### What this lets us delete (net-negative code)

- **T-098 `_bootstrap_step`** hardcoding (brief/vision knowledge) → replaced by
  map-driven activity execution.
- **T-097 scaffold-specific-to-brief** logic → generalized to "scaffold any
  activity's declared `requires_input`."
- **T-096 per-cycle LLM navigator** → retired to a genuine last-resort (a state
  the compiled map doesn't cover) or removed entirely; the `.openup/navigator-decision.json`
  reliability problem (T-098's root cause) *disappears* because navigation no
  longer depends on the model emitting a decision file per cycle.

The remaining gap is small and already half-built: **fire T-090 Plan Iteration on
a fresh project from `activities-for(phase)`** even with no roadmap (today
`resolve §1d` only emits `plan-iteration` when a promotable roadmap entry exists).

### Why "compile once" beats "hand-author the map"

For *standard* OpenUP the shipped map suffices — no LLM needed. The compile step's
value is precisely **customization**: a team running a tailored OpenUP (extra
phases, different activities, a non-OpenUP methodology) points the compiler at
*their* process description and gets a valid navigation map without editing YAML
by hand or forking the framework. A one-time, reviewable, script-validated
artifact is a far better place for "the LLM understood the process" than a
per-cycle re-derivation that can drift call-to-call.

## Options Considered

- **Option A — Compiled process map (this proposal).** LLM compiles process →
  map (once); scripts navigate deterministically; inputs declared as data;
  delete bootstrap + retire navigator. Pro: keeps {agnostic, robust, cheap};
  net-negative code; one reviewable artifact; slots into T-077. Con: a real
  program (schema extension + compile step + fresh-project Plan Iteration +
  deletions); the compile step is a new LLM-output-must-validate surface.
- **Option B — Process-driven navigation, map stays framework-fixed (proposal 1
  only).** Fire Plan Iteration from the shipped map; activities `ask_user` for
  inputs; delete the bootstrap. Pro: smaller; no compile step. Con: not agnostic
  to a *customized* process (the map is still framework-fixed); relies on the
  per-cycle LLM `ask_user` for inputs rather than declaring them.
- **Option C — Keep the hardcoded bootstrap + per-cycle navigator (status quo,
  T-096..T-099).** Pro: works today for standard OpenUP. Con: non-agnostic,
  hardcodes process knowledge, per-cycle LLM navigation is flaky/expensive — the
  thing that generated four consecutive live bug reports.

### Product-manager challenge pass

Assuming the product-manager role hat (`.claude/teammates/product-manager.md`):
value = order pending work by falsifiable user impact; kill ceremony that no one
will read back.

- **Pushback — "who is the customized-process user, and would we notice?"** The
  headline value (support a *customized* OpenUP) is currently **hypothetical** —
  every live driver so far runs *standard* OpenUP, where the shipped map already
  works. If the only benefit were customization, this is a speculative
  generalization and should be dropped. *Disposition: partially accepted — the
  customization case is deferred, NOT the reason to build.* The **real, evidenced**
  value is different and immediate: it **deletes the hardcoded bootstrap and
  retires the per-cycle navigator that produced T-096→T-099 — four consecutive
  live failures on the one driver we have.** That is a maintainability +
  reliability win measurable today (see refined measure), independent of whether a
  customized-process user ever appears. Build it for *that*; customization is a
  free option it happens to unlock.
- **Complement — the compile step needs the same discipline as the roadmap-id
  and RDM lessons.** T-099 proved an LLM authoring a machine-consumed artifact
  invents formats the parser rejects. The compiled map is exactly that class of
  artifact, so it MUST have: a strict output schema in the compile instruction,
  a deterministic `validate` hard-gate, and human review before the loop trusts
  it. Without those it reproduces the RDM-id bug at the navigation layer. Fold
  this into open question 3 as a *requirement*, not an option.
- **Complement — don't regenerate the standard map.** Compilation must be
  *opt-in / only-when-customized*; regenerating a valid shipped map on every
  standard project is pure cost and a fresh drift surface. Default = use the
  shipped map; compile only when a project declares a custom process.
- **Refine — the falsifiable measure.** Not "supports customization" (unfalsifiable
  today). Instead: **on the existing benchmark (T-080) + the my-product fixture, a
  fresh Inception-through-delivery run completes with (a) ZERO per-cycle navigator
  LLM calls, (b) the `navigator.py` bootstrap/decision code deleted, and (c)
  ≤ the current LLM-call count** — i.e. we removed an entire class of per-cycle
  LLM navigation and its four-bug failure mode without regressing convergence or
  token cost. Read back via the T-080 usage log + a call-count assertion.
- **Refine — sequence to keep each step shippable.** The deletion (retire the
  per-cycle navigator; fire Plan Iteration on a fresh project from the *shipped*
  map; declare inputs as data) is Option B and is independently valuable and
  lower-risk. The *compile step* (Option A's LLM generation) is a second slice
  that only matters once a customized process appears. **Ship B first, keep the
  map schema forward-compatible for the compiler, add A when a real custom-process
  need lands.** This de-risks the speculative part.

Net PM disposition: **accepted, re-justified and re-sequenced.** Build it to
*delete the flaky navigator + hardcoded bootstrap* (evidenced value now), not to
*support customization* (deferred option). Ship the deterministic-navigation slice
(Option B shape) first; gate the LLM-compile slice behind an actual custom-process
need. Compile output must be schema-strict + validated + reviewed (the T-099
lesson).

## Open Questions

1. **What the LLM reads to compile** — the vendored OpenUP KB
   (`openup-knowledge-base/`) for a tailored-but-OpenUP process, or a project-
   supplied process description for a non-OpenUP one? (Standard = no compile.)
2. **Output schema + override** — extend the existing `process-map.yaml` schema
   with `iterations` cadence + per-activity `requires_input` + `execution`
   (direct | spec-then-execute); a project-local map (`docs/process-map.yaml` or
   `.openup/`) overrides the framework default; `openup-process-map.py` stays the
   only consumer.
3. **Validation as a hard gate (REQUIREMENT, per PM pass)** — the compiled/edited
   map must pass `openup-process-map.py validate` (structural: every activity has
   a known procedure/role; every `requires_input.path` well-formed) before the
   loop trusts it; strict output schema in the compile instruction; human review.
4. **Direct-procedure vs spec-then-execute for authoring activities** — does an
   authoring activity (create-vision, create-architecture) run its procedure
   directly (efficient; the map marks `execution: direct`) or get a lane spec
   authored first then executed (uniform with feature lanes)? This also resolves
   the redundant-`initiate-project`-lane smell.
5. **Fresh-project Plan Iteration trigger** — how `resolve` (or a pre-step) fires
   `plan-iteration` from `activities-for(phase)` when there is no roadmap yet
   (today §1d requires a promotable entry). Reuses T-090 machinery.

## Where this goes next

→ **iteration** — promote a small program **"Deterministic process-map
navigation"** on `harness-optional`, sequenced per the PM pass: **(P1)** fire
T-090 Plan Iteration on a fresh project from the *shipped* map + declare
per-activity `requires_input` in the schema + map-driven scaffold/suspend +
`execution: direct` for authoring activities + **delete the T-097/T-098 hardcoded
bootstrap and retire the T-096 per-cycle navigator** (the evidenced value: remove
the four-bug failure mode; falsifiable via the T-080 zero-navigator-call +
deleted-code measure); **(P2, deferred until a real custom-process need lands)**
the LLM **compile step** that generates a project-local map from a process
description, schema-strict + `validate`-gated + human-reviewed. Author the full
iteration plan on promote.

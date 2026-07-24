# Milestone decision records

Each file here records a **human go/no-go decision** at an OpenUP phase boundary
(a lifecycle *milestone*). The record is the **source of truth for "the project
advanced to the next phase"** — `scripts/openup-lifecycle.py status` reads these
records to derive the current phase; it never writes them.

Records are authored only by `/openup-phase-review` (the human milestone review).
They are the deliberate hand-authored exception to the derive-don't-author rule,
exactly like a ticked `## Operations` checkbox: they encode a decision a script
cannot make.

## Filename

```
docs/product/milestones/<phase>-<cycle>.md
```

- `<phase>` — `inception` | `elaboration` | `construction` | `transition`
- `<cycle>` — integer, `1` for the first pass. A later cycle (e.g. returning to
  Construction after a partial Transition — OpenUP's "start another development
  cycle") uses the next integer: `construction-2.md`.

## Frontmatter

```yaml
---
phase: elaboration            # inception | elaboration | construction | transition
cycle: 1                      # integer
milestone: Lifecycle Architecture (LCA)
decision: GO                  # GO | NO-GO | CONDITIONAL
date: 2026-07-13
decided-by: <stakeholder / role>
---
```

The four phase milestones are:

| Phase | Milestone | Exit question |
|---|---|---|
| Inception | Lifecycle Objectives (LCO) | Agree on scope + objectives; proceed? |
| Elaboration | Lifecycle Architecture (LCA) | Executable architecture validated; risk acceptable? |
| Construction | Initial Operational Capability (IOC) | Close enough to release; ready for beta? |
| Transition | Product Release (PR) | Application ready to release; accepted? |

## How the phase is derived

- **`decision: GO`** on the latest record advances the current phase to the
  **next** phase (Transition GO → `released`).
- A `NO-GO` / `CONDITIONAL` (or no GO yet) keeps the current phase at the
  most-recent record's phase.
- **No records at all** → `openup-lifecycle.py` falls back to the `phase` already
  in `.openup/state.json` and flags `source: state-fallback`. It does **not**
  invent retroactive records for a project that predates them.

Below the frontmatter, record the evidence links (iteration assessments, demos,
acceptance-test results) and any conditions attached to a `CONDITIONAL` decision.

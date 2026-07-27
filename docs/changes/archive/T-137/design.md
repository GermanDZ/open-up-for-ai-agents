# T-137 — design notes

**Parent task**: T-107 (split into T-137 / T-138 / T-139 once T-106's live-batch
gate cleared via T-136 — see `docs/changes/T-107/design.md`).

## Finding: Requirement 1 is already satisfied — no compilation needed

T-107's Requirement 1 was: "The committed `task-library.yaml` covers every
authoring task the process map can reference... `--check` stays green."

Verified 2026-07-27, before writing any code:

```
$ python3 scripts/build-task-library.py --check
[task-library] ✓ skeletons in sync with KB sources

$ python3 scripts/openup-process-map.py tasks --validate
[task-library] ✓ valid — 9 task def(s)
```

Every task-def any `docs-eng-process/process-map.yaml` activity's `tasks:`
list references is already compiled in `docs-eng-process/task-library.yaml`:

| process-map.yaml activity | tasks: | compiled? |
|---|---|---|
| `initiate-project` | `develop-technical-vision`, `author-initial-roadmap` | ✅ |
| `agree-technical-approach` | `envision-the-architecture` | ✅ |
| `identify-refine-requirements` | `identify-and-outline-requirements`, `detail-use-case-scenarios` | ✅ |
| `develop-architecture` | `refine-the-architecture` | ✅ |
| `test-solution` | `create-test-cases` | ✅ |
| `plan-manage-iteration` | `plan-iteration` | ✅ |

(The library's 9th def, `probe-code-artifact`, is T-134's — deliberately
**not** wired into `process-map.yaml`, so it's outside this scope entirely.)

The KB has 39 total task files across 13 practice areas; only 9 are
compiled. The other 30 (`doc_trng`, `production_release`, `release_planning`,
`team_change_mgmt`, `project_process_tailoring`, `iterative_dev`, and the
`practice-technical` categories beyond what's already covered) are **not
referenced by any process-map activity today** — `develop-solution-increment`
and `ongoing-tasks` have no `tasks:` list at all (they stay `spec-then-execute`
by design, unrelated to this compiler).

## Disposition (owner decision, this session)

Compiling the remaining ~30 KB task files now would be speculative: nothing
in `process-map.yaml` would consume them, and adding new activity/tasks
wiring is itself a process-design decision (which activities should move to
`execution: direct`, and for which phases) — not something this task should
decide as a side effect of "compile more of the KB."

**T-137 closes here, already-satisfied, with zero new compilation.** The
KB-compile lane of T-107's split needed no work beyond this verification.
If a future task wires a new process-map activity to `execution: direct`,
*that* task compiles its own task-defs at the point of need — the same
incremental pattern T-104-T-106 already established, not a batch-ahead-of-need
compile.

## Follow-on

- T-138 — doctor `--check` wiring + re-distill runbook (does not depend on
  further compilation; operates on whatever's compiled at any given time)
- T-139 — customized process sources (independent of KB compile scope)

# Agent Run — T-139

- **Branch**: feat/T-139-customized-process-sources
- **Task**: T-139 — customized process sources: a project-owned override path, documented and pinned
- **Phase**: construction · **Iteration**: 107 · **Track**: standard
- **Start**: 2026-07-27T15:16:51Z
- **End**: 2026-07-27T16:23:23Z

## Commits

  - 9e90e07 feat(process-map): project-owned docs/process/ override for the map + task library [T-139]
  - bb45b66 docs(T-139): promote lane — author spec, board-visible [T-139]

## Files changed

     docs-eng-process/project-config.md          |  75 +++++++
     docs-eng-process/reference-driver.md        |   7 +
     docs/agent-logs/runs/2026-07-27-T-139.jsonl |   2 +
     docs/changes/T-139/design.md                | 163 +++++++++++++++
     docs/changes/T-139/plan.md                  | 309 ++++++++++++++++++++++++++++
     docs/roadmap.md                             |  18 +-
     docs/status-notes/2026-07-27-T-139.md       |   1 +
     scripts/openup-process-map.py               |  23 ++-
     tests/test_process_map.py                   | 116 +++++++++++
     9 files changed, 709 insertions(+), 5 deletions(-)

## Decisions

- **Premise checked before drafting** (action item B2, T-137 precedent): 2 of T-107 R4's
  4 acceptance bullets were already satisfied — `--repo-root` since T-105, and the
  vendored copy already overriding by first-match-wins with `sync-from-framework.sh`
  never overwriting it. Task narrowed accordingly.
- **Scope decided by the owner before code**: document + make honest, not the compiler
  emitter. Emitter deferred as T-156 with its unverified UMA-shape premise named.
- **New project-owned path** `docs/process/` rather than documenting the vendored one —
  the latter would promote a sync-script implementation detail to a public contract.
- **Kept the dead `scripts/*.yaml` candidates** as an honestly-labelled escape hatch;
  removing them would be a behavior change for any repo already using them.
- **Compiler untouched** — verified it inherits resolution through `_pm.load_tasks`.
- **Test order followed the safeguard over the Operations list**: R2's no-override guard
  written and passing against unmodified code before the tuples changed.

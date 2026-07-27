# Agent Run — T-155

| | |
|---|---|
| **Task** | T-155 — `merge=union` (or sharding) for the two shared `.claude/memory/` append-only files |
| **Branch** | `chore/T-155-memory-merge-union` |
| **Phase** | construction |
| **Track** | standard (solo — no team) |
| **Iteration** | 106 |
| **Start** | 2026-07-27T14:36:30Z |
| **End** | 2026-07-27T14:45:36Z |

## Commits

- `2216ae0` — docs(T-155): promote lane — author spec, board-visible [T-155]
- `38428d2` — chore(T-155): merge=union for the shared .claude/memory/ files, delivered to existing consumers too [T-155]

## Files Changed

**Behavior:**
- `.gitattributes` — `merge=union` for both `.claude/memory/` files, with the decision, the downstream evidence, and the server-side residual
- `scripts/lib/migrate-data.sh` — new `migrate_gitattributes_merge_union()`
- `scripts/sync-from-framework.sh` — call site (the path that reaches *existing* consumers)

**Docs:**
- `docs-eng-process/parallel-lanes.md` — class-2 row: decision, rejected alternative, residual

**Tests:**
- `scripts/tests/test_t155_memory_merge_union.py` (new, 9 tests) — requirements 3–6
- `scripts/tests/test_consumer_smoke.py` — requirement 2, on the real bootstrapped fixture

**Spec:**
- `docs/changes/T-155/plan.md`, `docs/changes/T-155/design.md`

## Decisions

- **Union, not sharding.** These two files are read directly at a fixed path by
  an agent at session start; sharding would need a consolidation step nothing
  runs, in the consumer's checkout, with the writers living downstream.
- **Both files**, though only `bypass-log.md` has actually collided — a per-file
  split would encode "hasn't bitten yet" as design.
- **Delivery was the substance.** Bootstrap copies `.gitattributes` only at first
  install, so the attribute alone would have reached none of the affected repos.
- **Match on the path, not the line**; append, never overwrite.

## Verification

- Full suite: **873 passed, 1 skipped, 20 subtests passed**.
- Bootstrap assertion verified to bite: stripping the two lines from
  `.gitattributes` failed exactly that test and nothing else.
- `check-docs.py` exits 0; write-fence exit 0 (10 files, all in lane).

## Premise check (before drafting)

Read-only, in both consumer repos, per action item B2:

| | `kaze-webapp` | `cqecho-app` |
|---|---|---|
| Tracks the two files | yes | no |
| `.gitattributes` | yes | none |
| Two-sided merges, `bypass-log.md` | 3 of 3 | n/a |
| Two-sided merges, `iteration-learnings.md` | 0 | n/a |

No sibling repo was modified.

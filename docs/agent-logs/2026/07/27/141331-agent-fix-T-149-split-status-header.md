# Agent Run — T-149

| | |
|---|---|
| **Task** | T-149 — `project-status.md`'s `Status` header conflates last-completed-iteration with active-lane status |
| **Branch** | `fix/T-149-split-status-header` |
| **Phase** | construction |
| **Track** | standard (solo — no team) |
| **Iteration** | 105 |
| **Start** | 2026-07-27T13:45:25Z |
| **End** | 2026-07-27T14:13:31Z |

## Commits

- `dfb7c96` — docs(T-149): promote lane — author spec, board-visible [T-149]
- `df7f414` — fix(T-149): split project-status Status header — Status is the iteration's, Lane Status is the lane's [T-149]

## Files Changed

**Behavior:**
- `scripts/sync-status.py` — new `upsert_field()`; `**Status**` moved inside the truthy-`iteration` guard; unconditional `**Lane Status**` write
- `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py` — reads `Lane Status`, falls back to `Status`

**Header shape:**
- `docs-eng-process/templates/project-status.md` — `**Lane Status**` seeded + the two-field note
- `docs-eng-process/QUICKSTART.md` — sample bootstrap header kept identical to the template

**Contract docs:**
- `docs-eng-process/state-file.md` — new § *How state reaches `docs/project-status.md`'s status fields*
- `docs-eng-process/procedures/openup-retrospective.md` (+ rendered skill mirror) — step 2 names the field it means

**Tests:**
- `scripts/tests/test_t149_status_split.py` (new, 11 tests) — requirements 1–4
- `scripts/tests/test_on_task_request_hook.py` — requirements 5–6 (4 new tests)
- `scripts/tests/test_sync_status_notes.py` — T-146's assertion re-pointed at `**Lane Status**`

**Spec:**
- `docs/changes/T-149/plan.md`, `docs/changes/T-149/design.md`

## Decisions

- **(a) split the field, not (b) skip-on-quick.** The deciding evidence was a
  second live reader T-146's note did not account for: `on-task-request.py`
  reads `**Status**` as "is a lane live?" to choose between blocking a
  task-request and the advisory branch. (b) would have removed that signal
  without replacing it.
- **`**Status**` keeps the iteration meaning**, bound to `**Iteration**` by the
  *same* guard — an invariant, not a convention.
- **`set_field()` stays replace-only**; insertion is a separate `upsert_field()`
  used by exactly one caller.
- **A missing anchor is a no-op**, not an append — the generator does not
  restructure a header shape it does not recognize.

## Verification

- Full suite: **863 passed, 1 skipped, 20 subtests passed**.
- New tests run against the pre-change generator: **9 of 11 fail**, 11/11 pass
  after (the 2 that pass both ways are deliberate no-regression guards).
- `check-docs.py` and `check-docs.py --coverage` exit 0; write-fence exit 0
  (15 files, all in lane).
- Live confirmation: this completion's own `sync-status.py` run inserted
  `**Lane Status**: completed` into `docs/project-status.md`.

## Incident

`openup-claims.py claim --force` (the documented recovery for a stale `touches`
list) deleted the existing claim, then refused against the lane's *own* session
id, leaving the lane unleased. The fence then read **green** by falling back to
plan frontmatter — a lost lease looking like success. Recovered with explicit
`release` → `claim` → `heartbeat`. Detail in `docs/changes/T-149/design.md`.

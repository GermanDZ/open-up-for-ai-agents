# Agent Run — T-147

| Field | Value |
|---|---|
| Task | T-147 — Fence allowlist omits the two `.claude/memory/` files every completion writes |
| Branch | `fix/T-147-fence-claude-memory-allowlist` |
| Phase | construction |
| Iteration | 104 |
| Track | standard (solo, no team) |
| Start | 2026-07-27T13:11:44Z |
| End | 2026-07-27T13:20:32Z |

## Commits

- `243a20a` docs(T-147): promote lane — author spec, board-visible [T-147]
- `8260ade` fix(T-147): fence allowlist exempts the two .claude/memory/ files every lane writes [T-147]
- `7e49012` docs(T-147): completion grade — requirements + success-measure instrumentation [T-147]

## Files Changed

- `scripts/openup-fence.py` — two entries added to `ALWAYS_ALLOWED` + the why-files-not-prefix comment; module docstring's lane-owned bullet
- `scripts/tests/test_openup_fence.py` — +4 tests (2 positive, 2 scope guards); no pre-existing assertion modified
- `docs-eng-process/parallel-lanes.md` — class-2 row re-populated; "Allowed for task T-NNN" list
- `docs/changes/T-147/plan.md`, `design.md` — spec + decisions
- `docs/roadmap.md` — new T-155 entry (deferred merge-driver question); Status cell via `sync-status.py`

## Decisions

- **DD1** — allowlist the two explicit files, not the `.claude/memory/` prefix; asserted by a test in the widening direction.
- **DD2** — these are **class 2** (shared append-only), not class 1 (sharded, one writer per file). The convenient doc edit would have been wrong; `parallel-lanes.md` now says class 2 is involuntarily re-populated.
- **DD3** — `merge=union`/sharding for the two files deferred to **T-155**: merge resolution, not lane surface, and unexercisable in a repo that gitignores `/.claude/*`.
- **DD4** — premise verified in kaze-webapp (read-only) **before** drafting, per action item B2: 8 of 37 archived lanes carry the workaround.
- **DD5** — test-count baseline checked (845 → 849 collected), not assumed from the "946" in a status note.
- **DD6** — bite-checked both directions; removal fails only the 2 new positive tests, confirming a pure widening.

## Verification

- `scripts/tests/test_openup_fence.py` — 33 passed (29 pre-existing + 4 new)
- Full suite — 848 passed, 1 skipped; `--collect-only` 845 on `main` → 849 here
- `openup-fence.py check` — exit 0, 18 files within lane
- `check-docs.py` and `--coverage` — OK, 8 instances, no failures

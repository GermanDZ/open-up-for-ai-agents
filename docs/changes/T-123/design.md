# T-123 — design & completion notes

## Implementation-vs-spec grade (complete-task step 1a) — 2026-07-16

Graded against the actual diff (`git diff harness-optional...HEAD`) + green tests.

**Req 1 — `check-docs.py --changed-only` skips an unchanged rescan.**
- ✅ unchanged after a pass → skip (exit 0, no re-validate) —
  `ChangedOnlyTests.test_skips_when_unchanged`; verified live (run 1 full, run 2
  "no docs delta … skipping").
- ✅ any docs/schema/model delta → full check — `test_reruns_on_delta`;
  signature stats `docs/**/*.md` + schema + trace-model.
- ✅ prior failure → no skip — `test_no_skip_after_failure` (cache stores
  `ok:false`; only `ok:true` skips).
- ✅ `--coverage` keyed separately — `test_coverage_keyed_separately`.
- ✅ default path untouched / never caches — `test_default_path_never_caches`;
  the `--changed-only` block is guarded by `if args.changed_only`.

**Req 2 — `run_gates` can skip a named gate.**
- ✅ `run_gates(root, skip={"check-docs"})` runs the fence, not check-docs, and
  reports the skip — `loop.py` `run_gates(skip=None)`; exercised by every
  DirtyGatingTest that skips (code-only box, completion dedup).

**Req 3 — engine runs per-box check-docs only on a relevant-docs delta.**
- ✅ code-only box skips check-docs; doc box runs it —
  `DirtyGatingTest.test_code_only_box_skips_check_docs_and_completion_dedups`
  (check-docs runs exactly once for a doc-box + code-box lane).
- ✅ a check-docs failure on a later doc-changing box is still caught (exit 6,
  box unticked) — `test_gate_failure_on_later_doc_box_still_caught`.
- ✅ git unavailable → None → fail-open — `test_relevant_docs_sig_fail_open_without_git`.
- ✅ signature excludes change folder/views/audit trees, includes instances +
  schema — `test_relevant_docs_sig_excludes_noise_includes_instances` +
  `test_relevant_docs_sig_includes_schema_and_model_outside_docs`.

**Req 4 — completion check-docs re-run deduped.**
- ✅ completion writes only irrelevant docs (status flip/note/views) → check-docs
  not re-run — proven by the code-only test above running check-docs exactly once
  (box1 baseline; completion deduped). `complete()` takes `last_docs_sig`.

No ❌. All requirements satisfied by the diff and green hermetic tests.

## Success-measure instrumentation (step 1b)

`## Success Measures` names the existing cycle-log gate lines (`check-docs: OK`
vs `check-docs: skipped (dirty-aware …)`) as the falsifiable instrument — no new
telemetry. ✅ present: `loop.run_gates` emits both lines; the hermetic proof is
the code-only-skip + completion-dedup test (check-docs runs once, not 3×). Bench
read-back is the T-080 owner batch (no endpoint here). Recorded per step 1b.

## Notes / gotchas

- **`git status --porcelain` collapses a brand-new untracked directory** to a
  single `?? docs/product/` entry, which the `.md` filter misses — so a box that
  creates a whole new docs subtree would have been invisible to the signature.
  Fixed with `--untracked-files=all` (found by the first test run failing). Real
  correctness fix, not just a test artifact.
- **Two baselines, deliberately.** The harness `--changed-only` uses a
  stat-signature cache ("since last pass") to catch back-to-back defensive
  re-runs; the engine uses a git-delta of relevant docs ("since last gate pass,
  minus change-folder/view noise") to catch code-only boxes. They serve different
  flows; unifying them would break one.
- **First box always runs the full gate** (`last_docs_sig is None`), so a
  pre-existing docs problem is caught; the fence runs every box unchanged.

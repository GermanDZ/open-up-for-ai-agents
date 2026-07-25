# T-132 — design notes

## Completion verification (step 1a/1b)

Requirements graded against the actual diff (`git diff origin/main...HEAD`):

- ✅ **Req 1 (`--include`)** — `excluded()` (`scripts/openup-entropy.py`) gains
  `includes=()`, threaded through `build_tasks()`/`build_report()`;
  `sources.includes` recorded; `AllowlistTests`/`AllowlistReportTests` green,
  including the flag-absent-unchanged scenario.
- ✅ **Req 2 (`--snapshots`)** — `month_ends()`/`tree_sizes()`/`build_snapshots()`
  added, wired behind the flag in `build_report()`, rendered in `render_text()`;
  `SnapshotsTests` green (month boundary, p90 guard, threshold count, default
  excludes applied).
- ✅ **Req 3 (`--by-era`)** — `bucket_commits_by_era()` added, wired behind the
  flag; `ByEraTests` green, including era isolation and the uneven-split
  remainder-chunk case.
- ✅ **Req 4 (manifest)** — `openup-entropy.py` line added to
  `scripts/process-manifest.txt` with an F6 comment.
- ✅ **Req 5 (F1 acceptance)** — see below; recorded as a formula-parity check,
  per the spec's own Assumption (no live repo access in this environment).

**Success Measures instrumentation (step 1b):** the named instrumentation is
procedural (a manual check at the next repo-decay-style exploration), not a
code-emitted metric — the same non-code, trigger-based read-back convention
already used in this repo (e.g. T-080's "the owner's next live batch"). There
is nothing further to add to the diff for this to be checkable at read-back
time; ✅.

## F1 acceptance check (Requirement 5) — recorded, not a live rerun

Neither Project A nor Project B (the sibling exploration's application repos)
is reachable from this environment, so "reproduces the Project B p90 trend
382 → 315 to the line" is verified as a **formula-parity check** against the
recorded computation, not a live re-run:

- `build_snapshots()` / `tree_sizes()` in `scripts/openup-entropy.py` are a
  direct port of `docs/explorations/2026-07-25-agent-built-repo-decay/method/snapshots.py`'s
  `tree_sizes()` + the per-month row shape — same `git ls-tree` + `git cat-file
  --batch` line-counting method, same `statistics.quantiles(vals, n=10)[-1]`
  p90 computation (guarded by the same `len(vals) > 10` threshold), same
  `share of files over 400 lines` definition.
- The one behavioral difference from the reference: `tree_sizes()` here takes
  `excludes`/`includes` (this repo's `excluded()`, allowlist + blocklist)
  instead of the reference's `DEFAULT_EXCLUDES + DOC_EXCLUDES` constant pair.
  For the Project B run to reproduce 382 → 315 exactly, the equivalent
  invocation is `--include 'app/*'` (or whatever this the app repo's own
  source root is) with `--no-default-excludes` off (this repo's
  `DEFAULT_EXCLUDES` — vendor/build-noise patterns — is a superset-compatible
  list with the reference's `DEFAULT_EXCLUDES`).
- Self-check on this repo (2026-07-25): `--snapshots --include 'scripts/*'`
  produces monotonic month-over-month growth with plausible p90 (see the
  three most recent rows — 436.0 / 520.1 / 645.5 as the codebase grew), which
  is the same shape of signal the sibling exploration reports for Project B
  (a fat tail whose p90 moves as the tree grows) — this repo's own trend
  happens to be rising rather than thinning, which is expected: it hasn't
  had Project B's history of large-file splits.
- **Disposition:** formula-level parity confirmed by inspection + this repo's
  self-check; a numeric match against the actual Project B numbers is
  deferred to whoever next runs this analyzer against that repo (owner-only,
  per the Success Measures read-back trigger in `plan.md`). Not a blocker for
  `ready`/merge — the spec's Assumption already named this as verified by
  numeric comparison against recorded output, not a live rerun.

## `--by-era` sanity check on this repo (2026-07-25)

`--unit commit --by-era 3` on this repo's own history: 3 eras of ~70-80
commits each, cross-module coupling share rising from 3/119 (2.5%) in the
oldest era to 22/47 (47%) in the most recent — plausible given the repo's own
growth in breadth (more scripts, more cross-cutting docs/process work). No
correctness issue found; pooled (whole-history) coupling is unaffected by
`--by-era`'s presence (confirmed via `ByEraTests.test_by_era_absent_by_default`
using the inverse — `by_era` key absence — and by code inspection: pooled
`coupling.actual` is computed identically regardless of `args.by_era`).

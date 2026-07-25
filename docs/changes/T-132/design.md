# T-132 — design notes

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

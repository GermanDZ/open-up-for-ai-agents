# T-132: `openup-entropy.py` — `--include` allowlist scoping, `--snapshots`, `--by-era` coupling + manifest registration (F1 + F6)

**Phase**: construction
**Status**: pending
**Goal**: Fold the three measures that actually mattered in the Project A/Project B decay run into the shipped analyzer, and register it in `process-manifest.txt` so the repos that need it receive it.
**Priority**: high

---

## Context

`docs/explorations/2026-07-25-measurement-tooling-and-lane-hygiene.md` (F1, F6)
found that `scripts/openup-entropy.py` (T-127/T-128) produced this repo's
baseline fine but produced **nothing usable** on the two application repos in
the sibling decay run (`docs/explorations/2026-07-25-agent-built-repo-decay.md`).
That run had to write 836 lines of throwaway analysers under
`docs/explorations/2026-07-25-agent-built-repo-decay/method/` to get its
findings at all.

Three of those throwaway measures changed or produced the run's actual
conclusions and are worth folding into the supported tool (the PM pass in the
exploration explicitly rejected productizing the fourth, line survival — not
identifiable, sign flips on removing one commit):

- **`--include` (allowlist scoping)** — with blocklist-only `--exclude`, both
  app repos' 100%-vendored copy of this framework's `scripts/` tree stayed
  admitted into every metric. Project A's 168 `chore(process): sync OpenUP
  framework` commits (19.5% of its history) were counted as large,
  high-survival *human* commits — **the tool would have reported the opposite
  conclusion on Project A** without an allowlist.
- **`--snapshots` (structural series)** — the single most direct test of "god
  objects accumulate" the whole exploration used; it is what showed Project
  B's file-size fat tail *thinning* (p90 382 → 315) across 14× growth, the
  opposite of the decay thesis.
- **`--by-era` (coupling sliced by history era)** — coupling is currently
  reported pooled over all history; without era slicing, "did coupling get
  worse as the repo aged" is uncomputable.

**F6** — `openup-entropy.py` is absent from `scripts/process-manifest.txt`
(verified: 0 hits). T-127 deliberately excluded it under the manifest's
stated criterion ("scripts the workflow skills invoke"). That looks wrong
now: both application repos already vendor this framework's `scripts/`
wholesale, so manifest registration *is* the distribution channel that would
have put the analyzer where the baseline programme needed it. The exploration's
product-manager pass is explicit that ordering F1 before F6 "would ship an
improvement nobody receives" — they ship together, in this lane.

This is the second of two lanes the exploration's disposition named (the
first, F2+F3 lane hygiene, shipped as T-131, merged PR #86, 2026-07-25).

---

## Current State

### `scripts/openup-entropy.py` — no allowlist, no snapshots, no era slicing

Argument parser (`scripts/openup-entropy.py:686-715`) has `--exclude`
(blocklist only) and no `--include`:

```python
parser.add_argument("--exclude", action="append", default=[],
                    help="extra fnmatch pattern to exclude (repeatable)")
parser.add_argument("--no-default-excludes", action="store_true",
                    help="drop the built-in process-noise exclusions")
```

`excluded()` (`scripts/openup-entropy.py:124-125`) takes only a blocklist:

```python
def excluded(path, patterns):
    return any(fnmatch(path, pat) for pat in patterns)
```

`build_report()` (`scripts/openup-entropy.py:556-598`) computes cost, drift,
and coupling — there is no structural (tree-shaped, per-month) pass, and
`compute_coupling()` (`scripts/openup-entropy.py:507-550`) is always called
once over the whole-history graph, never sliced by era.

### `docs/explorations/.../method/decay.py` — the allowlist reference (throwaway, untested as a supported surface)

```python
DEFAULT_EXCLUDES = (
    "docs-eng-process/*", ".claude/*", ".cursor/*", ".github/*",
    "coverage/*", "log/*", "node_modules/*", "vendor/*", "tmp/*",
    "*.lock", "package-lock.json", "Gemfile.lock", "yarn.lock",
    "openup-knowledge-base/*", ".openup/*",
)

def excluded(path, patterns, includes=()):
    """True if `path` is out of scope: outside the allowlist, or blocklisted."""
    if includes and not any(fnmatch.fnmatch(path, i) for i in includes):
        return True
    return any(fnmatch.fnmatch(path, p) for p in patterns)
```

### `docs/explorations/.../method/snapshots.py` — the structural-series reference

```python
def month_ends(repo):
    """Last commit sha of each calendar month, oldest first."""
    ...

def tree_sizes(repo, sha, pats, includes):
    """path -> line count for every in-scope code file at `sha`."""
    ...  # git ls-tree + git cat-file --batch at that sha

# per month: code_files, code_lines, med/p90/max file_lines, files_gt_400,
# share_gt_400, modules, files_per_module, largest_module_files,
# test_files, test_to_src_lines
```

### `docs/explorations/.../method/coupling_trend.py` — the era-slicing reference

```python
def main(argv):
    ...
    ap.add_argument("--eras", type=int, default=4)
    ...
    size = max(1, len(commits) // args.eras)
    eras = []
    for i in range(0, len(commits), size):
        chunk = commits[i:i + size]
        ...
        r = coupling(chunk, args.min_support, args.max_files, args.depth)
        r.update({"era": f"{chunk[0]['date'][:10]}..{chunk[-1]['date'][:10]}", ...})
        eras.append(r)
```

Equal-**commit-count** eras (not explicit date ranges) — this is what the
exploration's disposition names as the reference implementation, and it
reuses a pattern `openup-entropy.py` already has for cost bucketing
(`bucket_by_index`, `scripts/openup-entropy.py:424-439`), just applied to the
coupling graph instead of the cost rows.

### `scripts/process-manifest.txt` — analyzer absent

```
openup-doctor.py
# T-058 — periodic framework version staleness check ...
openup-version-check.py
```

No `openup-entropy.py` line anywhere in the file (verified: `grep -c entropy`
→ 0).

---

## Proposed Design

### 1. `--include GLOB` (repeatable allowlist, applied before excludes)

**File**: `scripts/openup-entropy.py`

```python
def excluded(path, patterns, includes=()):
    if includes and not any(fnmatch(path, inc) for inc in includes):
        return True
    return any(fnmatch(path, pat) for pat in patterns)
```

Every existing `excluded(p, excludes)` call site (`build_tasks`,
`compute_coupling`'s callers via `declared_graph`/`actual_graph` filtering)
threads `args.include` through the same way `excludes` already flows via
`build_report`. New flag:

```python
parser.add_argument("--include", action="append", default=[],
                    help="allowlist fnmatch pattern (repeatable); when given, "
                         "only matching paths are in scope, applied BEFORE "
                         "--exclude (default: everything is in scope)")
```

`report["sources"]["includes"]` records the allowlist actually used, same
transparency contract as `excludes` (`scripts/openup-entropy.py:580`).

### 2. `--snapshots` (month-end structural series)

**File**: `scripts/openup-entropy.py`

New functions ported from `method/snapshots.py`, adapted to this script's
existing `_git()` helper and `excluded()` (with the new allowlist):

```python
def month_ends(root):
    """Last commit sha of each calendar month, oldest first."""
    out = _git(root, ["log", "--reverse", "--format=%H %aI"])
    ...

def tree_sizes(root, sha, excludes, includes):
    """path -> line count for every in-scope file at `sha` (ls-tree + cat-file --batch)."""
    ...

def build_snapshots(root, excludes, includes, threshold=400):
    """One row per calendar month: file/line counts, med/p90/max file length,
    share over `threshold`, module spread, test/src line ratio."""
    ...
```

Wired into `build_report()` behind the flag (report-only cost — this is a
`git cat-file --batch` per in-scope file per month-end, so it only runs when
asked):

```python
if args.snapshots:
    report["snapshots"] = build_snapshots(root, excludes, args.include)
```

`render_text()` gains a "Structural snapshots" section (same table-row style
as the existing cost-bucket tables) when `report.get("snapshots")` is present.

### 3. `--by-era N` (coupling sliced into N equal-commit eras)

**File**: `scripts/openup-entropy.py`

Reuses `compute_coupling()` unchanged, sliced the same way
`bucket_by_index()` already slices `rows` for cost — applied here to the
**commit stream** (not the per-task rows), since era slicing is meaningful
even under `--unit commit`/`--unit pr` where there is no task ordinal:

```python
def bucket_commits_by_era(root, excludes, includes, n):
    """N equal-commit-count chronological slices of `git log --numstat`,
    each returned as a {unit_key: {files}} graph ready for compute_coupling()."""
    ...

parser.add_argument("--by-era", type=int, default=None, metavar="N",
                    help="slice coupling into N equal-commit-count eras "
                         "(default: off — pooled over all history)")
```

```python
if args.by_era:
    report["coupling"]["by_era"] = [
        {"era": label, **compute_coupling(graph, args.min_support, args.top,
                                           args.module_depth, args.max_files)}
        for label, graph in bucket_commits_by_era(root, excludes, args.include, args.by_era)
    ]
```

### 4. Manifest registration (F6)

**File**: `scripts/process-manifest.txt`

```
openup-doctor.py
# T-058 — periodic framework version staleness check ...
openup-version-check.py
# T-132 — read-only codebase-entropy report (F6: both app repos already
# vendor scripts/ wholesale; the manifest is the distribution channel).
openup-entropy.py
```

The manifest's stated criterion ("scripts the workflow skills invoke")
widens to cover maintainer-invoked read-only diagnostics — `openup-doctor.py`
is already there on effectively that basis, so this is precedent, not a new
exception.

---

## Acceptance Criteria

- [ ] `--include GLOB` is repeatable, applied before `--exclude`/default
      excludes, and `report["sources"]["includes"]` records what was used
- [ ] `--snapshots` emits one row per calendar month with code_files,
      code_lines, med/p90/max file_lines, share over 400 lines, module
      spread, and test/src line ratio — both in `--json` and text output
- [ ] `--by-era N` slices coupling into N equal-commit-count eras and reports
      each era's pair count, cross-module share, and median Jaccard
      alongside the existing pooled (whole-history) coupling
- [ ] **Falsifiable acceptance test (from the exploration's PM pass)**:
      running `openup-entropy.py --include 'app/*' ... --snapshots` on a
      repo that vendors this framework excludes the vendored `scripts/` tree
      from every metric, and the resulting structural series reproduces the
      published Project B p90 trend — **382 → 315** — to the line, checked
      against the numbers already recorded in
      `docs/explorations/2026-07-25-agent-built-repo-decay.md` (§ "2025-06 →
      2026-07" table). Neither Project A nor Project B is reachable from this
      sandbox, so this is a numeric comparison against recorded output, not a
      live re-run — recorded in `design.md` at review.
- [ ] `openup-entropy.py` is listed in `scripts/process-manifest.txt`
- [ ] `docs-eng-process/script-cli-reference.md`'s `openup-entropy.py` section
      documents the three new flags
- [ ] All existing `scripts/tests/test_openup_entropy.py` tests stay green
      (byte-identical output on the flags' absence — additive only)

---

## Success Measure

We expect the next codebase-decay measurement on a repo outside this one to
need **zero throwaway `method/`-style analysis scripts** — `--include` +
`--snapshots` + `--by-era` cover the three measures that produced this run's
actual findings. Falsifiable read-back: the first time this analyzer is
pointed at a third repo (owner-initiated, no fixed date), check whether a
new one-off script gets written for a measure this lane claims to cover; if
so, this success measure is not met for that measure.

---

## Testing Strategy

- Unit: `excluded()` allowlist-before-blocklist precedence (include present +
  no match → excluded even with an empty blocklist; include absent →
  blocklist-only behavior unchanged, matching every existing test)
- Unit: `build_snapshots()` / `tree_sizes()` against a small git fixture with
  commits spanning 2+ calendar months and a mix of in-scope/excluded files —
  assert month boundaries, p90 computation (needs >10 files per
  `statistics.quantiles(..., n=10)`, same guard as the reference), and
  share-over-threshold math
- Unit: `bucket_commits_by_era()` — N equal-commit slices on a fixture with a
  non-multiple-of-N commit count (last chunk gets the remainder, matching the
  `method/coupling_trend.py` reference's `chunk[i:i+size]` behavior)
- Regression: full `scripts/tests/test_openup_entropy.py` green; new flags
  default to current behavior (no `--include`/`--snapshots`/`--by-era` →
  identical JSON to pre-T-132, the same byte-identical contract T-128 held
  for `--unit`)
- Manual (recorded in `design.md`, not automated — no live repo access):
  numeric comparison of a local `--snapshots` run's p90 series shape against
  the recorded Project B table, confirming the metric computation matches
  even though the source repos differ

---

## Dependencies

- T-127 (`openup-entropy.py` M1 — completed)
- T-128 (`--unit {task,commit,pr}` — completed)

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-entropy.py` | `--include`, `--snapshots` (+ `build_snapshots`/`tree_sizes`/`month_ends`), `--by-era` (+ `bucket_commits_by_era`), `render_text()` sections |
| `scripts/tests/test_openup_entropy.py` | New test classes for allowlist, snapshots, era-bucketing |
| `scripts/process-manifest.txt` | Add `openup-entropy.py` (F6) |
| `docs-eng-process/script-cli-reference.md` | Document the three new flags |

---

## Out of Scope

- Line survival (F1's fourth measure) — explicitly rejected by the
  exploration's PM pass as not identifiable (sign flips on removing one
  commit); stays exploration-grade in `method/survival.py`
- Deleting or migrating `docs/explorations/2026-07-25-agent-built-repo-decay/method/*.py` — they stay as the historical reference implementation
- A live re-run against Project A/Project B — neither is reachable from this
  environment; verification is against recorded numbers only
- Any change to `--unit {task,commit,pr}` semantics (T-128, already shipped)

---

## Open Questions

1. **Should `--by-era` slice by explicit date ranges or equal-commit-count
   eras?** The exploration's prose names both (`--era FROM:TO` and
   `--by-era`) but its own reference implementation
   (`method/coupling_trend.py`) only does equal-commit-count eras.
   **Assumed: equal-commit-count (`--by-era N`, default 4)** — matches the
   reference implementation, needs no date bookkeeping, and mirrors the
   existing `--buckets` cost-bucketing pattern. Vetoable at review.
2. **Should `--snapshots` live inside `openup-entropy.py` or a sibling
   script?** The exploration flags this as an open question (analyzer is
   commit-history-shaped; snapshots are tree-shaped, need a checkout per
   sample point). **Assumed: same file, gated behind the flag** — matches
   the exploration disposition's literal instruction to "fold three of the
   four measures into the analyzer." Vetoable at review.
3. **Does F2 (from the sibling correctness lane, already shipped as T-131)
   need anything from this lane?** No — confirmed independent; T-131 already
   covers id re-issue, this lane only touches `openup-entropy.py` and the
   manifest.

# T-160 — design decisions

## DD1 — C2: a wrapper, not a pytest config change

Rejected setting `testpaths`/rootdir in `pytest.ini`/`pyproject.toml`. That would
silently change what every *existing* bare `pytest` invocation does — in this repo and in
every consumer that inherits the config — which is a far wider blast radius than the
problem. `scripts/run-tests.sh` is additive: existing `pytest <dir>` calls keep working
exactly as before, and nothing breaks if a lane ignores the runner.

## DD2 — C2: enumerated directories, plus a guard that fires

Runtime discovery was rejected: `venv/` and `.claude/worktrees/` both contain `test_*.py`,
so discovery needs a denylist, and a denylist rots invisibly — the same failure shape as
the problem being fixed.

So the list is explicit, and `test_every_project_test_dir_is_covered` fails when a new
top-level project test directory is not in it. **Bite-checked for real, not just in a
fixture**: creating `integration_tests/test_probe.py` in the repo made it fail with
`these directories contain tests but are not in run-tests.sh's TEST_DIRS:
['integration_tests']`; removing the directory returned it to green. A guard nobody has
seen fail is not a guard.

`test_does_not_mask_failures` additionally pins the aggregation — no `|| true`, and the
script must `exit "$overall"` — because a runner that returns 0 over a red directory is
strictly worse than no runner. Same reasoning T-150 recorded for hook guards.

The runner also picks its interpreter (`asdf exec python3` when that is the one with
pytest), because a bare `python3` on this machine lacks pytest — itself a silent-failure
trap that has cost time in this session.

## DD3 — C4: extend criterion 12, do not add a criterion

T-152 established *name where the number is read*, and it worked: every measure authored
after it names an environment. The gap iteration-109 found is one step further out —
**naming is not access.** So this is a refinement of the same criterion, conditional on the
environment being non-local, rather than a new criterion competing with it.

**The new elements fire only for non-local environments.** A measure read back here has an
implicit reader (whoever runs the next retrospective), so requiring a name in the common
case would add ceremony to fix the rare one. The discrimination check below shows the
conditional is doing real work rather than being vacuously true.

**No validator**, for the reason T-152 recorded and this task inherits: "is this reader
real?" is not mechanically parseable, and a name-matcher would pass any phrasing while
answering nothing.

## DD4 — The blocked-read-back clause matters as much as the reader

A missing number is **not** evidence of failure. T-155's own note said plainly that a `0`
in its measure would mean "not delivered", not "not fixed" — and iteration-109's read-back
table had to reason its way to that conclusion for T-153 independently ("0 breakages, but
no consumer synced, so 0 is indistinguishable from not-exercised"). Requiring the spec to
state it up front moves that reasoning from the reader to the author, who actually knows.

## DD5 — Discrimination check (requirement 9)

Across **122** archived specs:

| Category | Count | Effect of the new elements |
|---|---|---|
| No read-back environment stated | 112 | n/a — pre-T-152 or `n/a` measures |
| Environment = **this repo** | 7 | **not required** — confirms no added ceremony in the common case |
| Environment **non-local** | **3** (T-139, T-147, T-155) | required |
| …of those, naming a Reader | **0 of 3** | the criterion distinguishes rather than passing by construction |

So it discriminates, and it is **forward-looking rather than retroactive debt** — the
element did not exist when those three were written.

**Found while measuring: there are three at-risk measures, not two.** Iteration-109 named
T-147 and T-155. **T-139** also names a non-local environment, with a read-back due
**2026-10-25** in consumer repos, and it is the one whose entry says to *retire T-156* if
the read-back finds nothing. It is therefore the highest-consequence of the three and the
one most likely to go unread. Not fixed here — amending an archived spec's measure would be
rewriting history — but flagged for the next retrospective's step 4b.

## DD6 — This task satisfies its own extended criterion

Reflexively checked: T-160's measure names its read-back environment (this repo), and names
a Reader anyway ("whoever runs the next retrospective") plus the insufficient-window caveat.
Had the environment been non-local, the spec would have passed the new grading.

## DD7 — Verification

- `scripts/run-tests.sh` → **`scripts/tests/` 899 passed** (891 + 8 new guards), 1 skipped,
  20 subtests; **`tests/` 118 passed**; aggregate PASSED across 2 directories. Stated per
  directory, which is the convention this lane introduces.
- Coverage guard bite-checked against a real third directory (DD2).
- Both rubric copies `diff`-identical; `check-claude-sync` exits 0; the new texts are
  present in `.claude/skills/openup-complete-task`, `.claude/skills/openup-create-task-spec`
  and `.claude/rubrics/task-spec-rubric.md`.

### Step 1a — requirements graded against the diff

| # | Verdict | Evidence |
|---|---|---|
| 1 | ✅ | `run-tests.sh` TEST_DIRS covers both; per-directory summary; `test_declares_both_known_dirs`, `test_runs_and_reports_both_directories` |
| 2 | ✅ | `NOT_OURS` exclusions; `test_guard_detects_a_synthetic_uncovered_dir` asserts vendored tests stay ignored |
| 3 | ✅ | `test_every_project_test_dir_is_covered`, bite-checked live with `integration_tests/` |
| 4 | ✅ | `openup-complete-task.md` §1 names the runner and cites the T-155/157/158 drift |
| 5 | ✅ | criterion 12's new conditional block, both copies; template + step 1b updated |
| 6 | ✅ | blocked-read-back clause required in criterion 12 and prompted in the template |
| 7 | ✅ | `openup-create-task-spec.md` measure template gains `Reader:` + the clause, marked non-local-only |
| 8 | ✅ | `diff` of the two rubric copies empty; `check-claude-sync` 0; mirrors re-rendered (2 updated) |
| 9 | ✅ | DD5 — 0 of 3 non-local specs name a reader; 7 local specs unaffected |

**Result: 9/9 ✅.**

### Step 1b — success-measure instrumentation

`✅ instrumentation` — both instruments already exist and are committed here: the completion
notes assembled into `docs/project-status.md` `## Notes` (greppable for a suite figure), and
the **Measure Read-Back table** each retrospective produces. `✅ reader` — named as whoever
runs the next retrospective, which creates no new duty since `/openup-retrospective` step 4b
already walks those tables. Read-back environment: **this repo**. Read-back: **the second
retrospective after landing**, backstop **2026-11-30**, reporting the lane count alongside
the number so a `0` over an empty window is not mistaken for success.

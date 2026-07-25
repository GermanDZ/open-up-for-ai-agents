# Maintainability baselines — first run (T-127, 2026-07-25)

First execution of `scripts/openup-entropy.py` (M1) against this repo, producing
the M3 baseline. Purpose: replace opinion about agent-driven codebase decay with
this project's own numbers, **before** deciding whether any anti-decay gate is
justified.

Reproduce with:

```bash
python3 scripts/openup-entropy.py --repo .            # text
python3 scripts/openup-entropy.py --repo . --json     # machine-readable
```

Measured at `4713e58` + this lane's working tree, on **full** history (820
commits) — see "Measurement traps" below, this detail is load-bearing.

---

## 1. Result: no decay signal in this repo

Medians per task-index window (29 tasks each):

| Window | n | declared touches | actual files | minutes | commits | modules | coverage | jaccard |
|---|---|---|---|---|---|---|---|---|
| T-001..T-038 | 29 | 2.5 | 7 | – | 1 | 2 | 0.83 | 0.61 |
| T-039..T-067 | 29 | 3.5 | 4 | 14.47 | 3 | 2 | 1.0 | 0.71 |
| T-068..T-097 | 29 | 4 | 4 | 8.12 | 4 | 2.0 | 1.0 | 1.0 |
| T-098..T-127 | 29 | 5.5 | 2 | 9.48 | 3 | 2 | 1.0 | 1.0 |

By calendar month:

| Month | n | declared | actual | minutes | commits | modules | coverage | jaccard |
|---|---|---|---|---|---|---|---|---|
| 2026-04 | 2 | 0.0 | 14.5 | – | 2.0 | 2.0 | 0.0 | 0.0 |
| 2026-06 | 45 | 4.0 | 5 | 14.57 | 1 | 2 | 0.9 | 0.61 |
| 2026-07 | 65 | 5 | 3 | 9.8 | 4 | 2.0 | 1.0 | 1.0 |

**Reading it:**

- **Actual files changed per task falls** (7 → 4 → 4 → 2). Changes are getting
  *smaller*, not more sprawling. This is the direct opposite of the shotgun-surgery
  pattern the decay thesis predicts.
- **Module spread is flat at 2** across all four windows and all months. The
  shotgun-surgery index — the metric most likely to move under decay — does not move.
- **Duration falls** (14.47 → ~9 min) and holds.
- **Declared touches rise** (2.5 → 5.5) *while* actual files fall. Lanes are
  declaring more and changing less: the planning step got more conservative, not
  the code more tangled. §5's "subtle case" (drift rising while touches stays flat)
  is **not** what happened — drift fell to zero.

The 3–6 month decay window is not visible here. The repo is four months old, which
covers the front of that window but not its far end.

## 2. Declared `touches` are a usable coupling proxy — as of now

Success Measure read-back (T-127): **median coverage ≥ 0.5 — PASSES at 1.0.**

Over the 90 tasks carrying both a declared surface and matched commits:

| metric | value | meaning |
|---|---|---|
| median coverage | **1.0** | share of actually-changed files the lane declared |
| median precision | **1.0** | share of declarations that matched a real change |
| median Jaccard | **0.81** | combined agreement |
| median undeclared files | **0.0** | files changed but never declared |

But bucketed, the agreement is *earned*, not inherent: coverage 0.83 → 1.0 → 1.0
→ 1.0 and Jaccard 0.61 → 0.71 → 1.0 → 1.0. Every remaining zero-coverage task
(T-001, T-003, T-015, T-032, T-033) declared **nothing** — they predate the
write-fence. Once `touches` became load-bearing for the fence, it became accurate.

**This answers open question §8.2 for this repo:** declared touches track actual
diffs closely enough to use as a coupling proxy — *in the fence era*. Anyone
applying M1 to a project without an enforced declaration should verify coverage
before trusting the declared graph.

## 3. Coupling: the top pairs are healthy, and mostly process-made

Declared graph: 77 tasks, 61 pairs at support ≥3, 31 cross-module.
Actual graph: 87 tasks, 109 pairs at support ≥3, 41 cross-module.

Strongest actual-graph pairs:

| sup | jaccard | lift | pair |
|---|---|---|---|
| 8 | 1.0 | 10.9 | `scripts/openup_agent/cycle.py` ↔ `scripts/tests/test_openup_agent_cycle.py` |
| 8 | 0.47 | 5.1 | `docs-eng-process/reference-driver.md` ↔ `scripts/openup_agent/cycle.py` |
| 8 | 0.40 | 3.6 | `…/skills/openup-complete-task/SKILL.md` ↔ `…/skills/openup-start-iteration/SKILL.md` |
| 6 | 1.0 | 14.5 | `scripts/openup-agent-bench.py` ↔ `scripts/tests/test_openup_agent_bench.py` |

Two clusters, both explainable and neither pathological:

1. **Module ↔ its own test file** (Jaccard 1.0). This is the coupling you want;
   flagging it would be a false positive in any future gate.
2. **Doc ↔ the code it documents** — `reference-driver.md` co-changes with
   `cycle.py`, `loop.py`, `plan_iteration.py`. This is **fix-spec-first working as
   designed**: the process *requires* the spec and the code to move together. Most
   `cross_module` flags here are `docs-eng-process/ ↔ scripts/`, which is the
   framework's intended shape (procedure pack + runtime are one product), not
   accidental entanglement.

**Consequence for D1:** a naive coupling-delta gate would fire mostly on
process-mandated doc↔code pairs and on module↔test pairs. Any threshold must be
set against the *residual* after those two classes are accounted for, or it will
be bypassed within a week — exactly the failure mode §6.5 warned about.

## 4. Measurement traps found (both would corrupt a repeat of this study)

**T1 — Shallow clones silently destroy the dataset.** This session's checkout was
shallow (310 commits). Under it, git matched only **34 of 126** tasks, and the
shallow-boundary commit attributed the **entire tree — 2560 files — to T-056**,
which then dominated any per-task file-count statistic. After `git fetch
--unshallow` (820 commits), git matched 110 tasks and the artifact vanished.
A CI-hosted entropy job on a default `actions/checkout` (depth 1) would produce
confident garbage. Always verify `.git/shallow` is absent first.

**T2 — Declared `touches` cannot be matched by string equality.** Entries are
legitimately directory prefixes (`docs-eng-process/`) and legitimately carry
inline YAML comments (`scripts/    # claims + tests`). Matching naively gives
**median Jaccard 0.06**; matching with the fence's own `seg_prefix_collide` and
stripping comments gives **0.81** — a 13× error in the headline number, in the
direction that would have "confirmed" decay. `openup-entropy.py` now imports the
matcher from `openup-claims.py` rather than reimplementing it, the same
agreement-by-construction rule `openup-board.py` follows.

## 5. Caveats

- **This is a docs-and-scripts repo, not an application.** It is the weakest
  available test of the decay thesis; that was known going in.
- **Four months of history**, ~29 tasks per bucket, heterogeneous task sizes (no
  track-based normalization yet — `quick` and `full` lanes are pooled).
- **Source coverage differs**: 97 tasks declare touches, 110 match commits, 77
  have run logs. Each median is computed over the tasks that have that metric, and
  the per-bucket `_n` fields in `--json` record how many that was.
- **Duration** counts only paired `session_begin`/`session_end` events, so lanes
  whose logs are unpaired report no duration rather than a wrong one.
- **The declared coupling graph mixes granularities** — a directory entry
  (`scripts/`) appears as one node alongside file entries. The actual graph has no
  such problem and should be preferred where both exist.
- **2026-04's two tasks** are converter-era commits predating the process; they
  are noise at n=2.

## 6. What this licenses building next — and what it does not

| Item | Status after this baseline |
|---|---|
| **M1** entropy script | **Done** — this task. |
| **M3** baselines | **Partial** — this repo done; see §7 for what's blocked. |
| **M2** fence-violation logging | Still cheap, still worth doing; independent of these numbers. |
| **P1** architecture constraints | Unchanged — worth doing on its own merits (an unenforced architecture doc is decoration). |
| **P3** verify gate + CI | Unchanged and now *more* pointed: a green run still never runs the build. T1 above is a second reason CI needs care. |
| **P2** touches budget | Has a basis at last (median declared 5.5 in the current window) but **no urgency** — actual files per task are *falling*. |
| **D1** entropy regression gate | **Not licensed.** Nothing is trending badly; a gate would have nothing to catch, and §3 shows a naive threshold would fire on healthy pairs. |
| **V1** mutation testing | Unchanged — gated on evidence not produced here. |
| **R1** refactor emission | **Not licensed** — no threshold breach exists to emit against. |

The §7 discipline holds and the data enforces it: **build the measurement, add
gates only for failure modes the data shows.** This repo's data shows none. The
honest output of this task is a working measurement plus a "no" to four of the
queue's ten items, for now.

## 6b. Second baseline: a human-authored codebase (added by T-128)

The brief's sharpest criticism of the decay thesis is the **missing baseline** —
human-only teams also degrade codebases, and the claim needing support is a *rate
comparison*, which none of the cited evidence provides. T-128's `--unit commit`
makes any repo measurable, so here is one.

**What this repo is — read before using the number.** `TallyFoxAI/ruby_llm` is a
**fork** of Carmine Paolino's `ruby_llm` gem: 601 of its 672 commits are by the
upstream maintainer, and the history runs 2025-01 → 2025-09. It is **not**
TallyFox's own application, and nothing here measures TallyFox's engineering. It
is useful for exactly one thing: a **human-authored, non-agent, open-source**
comparison point. (The other reachable TallyFox repo, `usage-guides`, is an empty
repository — nothing to measure.)

Median files changed per **commit**, nine months, 672 commits:

| Window (168 commits each) | actual files | modules (depth 2) |
|---|---|---|
| 1st quarter | 2.0 | 1.0 |
| 2nd quarter | 2.0 | 1.0 |
| 3rd quarter | 2.0 | 2.0 |
| 4th quarter | 2.0 | 2.0 |

By month: 2 · 2 · 1 · 2 · 2 · 2 · 2 · 2 · 3 (Jan→Sep 2025).

**Flat**, across a window that fully contains the 3–6 month mark. Module spread
drifts 1 → 2 at depth 2; files per commit does not move at all.

Its coupling profile is also *shaped* like this repo's — docs and config on top,
module↔test below:

| sup | jaccard | lift | pair |
|---|---|---|---|
| 36 | 0.53 | 5.3 | `README.md` ↔ `docs/index.md` |
| 32 | 0.40 | 4.1 | `docs/guides/available-models.md` ↔ `lib/ruby_llm/models.json` |
| 26 | 1.00 | 14.7 | `gemfiles/rails_7.2.gemfile.lock` ↔ `gemfiles/rails_8.0.gemfile.lock` |
| 20 | 0.38 | 6.1 | `lib/ruby_llm/active_record/acts_as.rb` ↔ `spec/…/acts_as_spec.rb` |

The strongest pairs are mechanical (lockfiles regenerated together by Appraisal),
documentation duplication (`README.md` ↔ `docs/index.md`), and module↔its-spec.
Same three classes this repo shows. 24 commits exceeded `--max-files` and were
reported as skipped rather than silently dropped.

**The comparison, stated carefully.** Two codebases, one agent-driven and one
human-driven, over 4 and 9 months: **neither shows a rising per-change footprint.**
That is a trend comparison, not a level comparison — and levels here are *not*
comparable, for a reason worth recording:

> Running this repo with `--unit commit` gives a median of **0 files** per commit
> in three of four windows. That is not a bug: after process-noise exclusions, a
> large share of this repo's commits are housekeeping (`chore(process): sweep
> run-log shard`) touching only excluded paths. The task unit is the right unit
> here; the commit unit is the right unit for a repo with no task ids. Comparing
> their *levels* would be meaningless, so only the **shape of the trend** is
> compared above.

**What this does and does not support.** It is one human-authored repo, in a
different language, by a different team size, measured on a different unit. It
does not establish a rate. It does establish that "flat" is what the instrument
reports for a healthy human codebase too — i.e. the flat reading on this framework
is not obviously an artifact of the instrument being blind.

## 7. Blocked: the interesting repos

`kaze-webapp` and FacturaSimple are the cases that would actually test the thesis
— real applications, one of them entering the 3–6 month window. Neither was
measurable from this session:

- **`kaze-app/kaze-webapp`** — visible via `list_repos` but unreachable by **all
  three** access paths, re-verified 2026-07-25: `add_repo` refuses the cross-owner
  add (this session's sources are `germandz`); the GitHub MCP tools refuse it
  (`not configured for this session`); and a direct `git clone` fails auth because
  the repo is private. Unblock by starting a session with `kaze-app/kaze-webapp`
  as the initial source, then:

  ```bash
  git clone <kaze-webapp> /tmp/kaze && git -C /tmp/kaze fetch --unshallow   # trap T1
  python3 scripts/openup-entropy.py --repo /tmp/kaze --json > kaze-baseline.json
  ```

  The analyzer needs nothing from the OpenUP layout: with no `docs/changes/` tree
  it degrades to git-only (actual-diff cost + coupling), and it falls back from
  `[T-NNN]` trailers to conventional-commit scopes automatically. Both paths are
  covered by hermetic tests (`test_degrades_to_git_only`,
  `test_conventional_scope_fallback_when_no_bracket_tag`) — but neither has been
  exercised against kaze-webapp's real history, so treat the tool as *untested on
  that repo* until it runs there.

- **FacturaSimple** — not reachable at all; `list_repos` returns no match.

Until at least one of those runs, the standing note in the brief — "the strongest
position is having the number" — is only half-satisfied: there is now a number,
but it is from the least interesting of the three codebases.

# Exploration: does agent-built application code actually decay?

**Started:** 2026-07-25
**Question:** In two real, long-lived, agent-built applications — does the maintainability decay the "software factories fail" thesis predicts at 3–6 months actually show up in the data?

## Context

§5 of the agent-maintainability brief was the immediate work item and it was
**blocked**: the analysis had no access to Project A, and the T-127 run could
only measure this framework repo — which is a docs/process repo, not an
application, and only four months old. The brief's own §7 discipline is
*"build the measurement, run it against the repos, add gates only for failure
modes the data shows."* Without application data, no gate in the design queue
(D1 coupling thresholds, R1, P1 architecture constraints) had an evidence base.

Both repos are now readable locally, so §5 is unblocked:

| repo | span | commits (app code) | agent-authored | tests the claim |
|---|---|---|---|---|
| Project A | 2026-02-23 → 2026-07-25 (5 mo) | 379 | **97.1%** | is agent-built code fragile? |
| Project B | 2025-06-18 → 2026-07-24 (**13 mo**) | 1286 | 46.7% | does it decay *past* the 3–6 mo window? |

These are complementary, and better than the brief assumed. Project A is a
near-pure agent artifact — its 11 human commits are ops/config only (secrets,
domain, Kamal, SMTP), so nothing dilutes the signal. Project B runs **13
months**, well past the far end of the predicted decay window, and contains
both a 7-month human-only era and a 6-month agent-heavy era in one codebase,
which allows a within-repo comparison.

Prior run for this repo: [2026-07-25-maintainability-baselines.md](2026-07-25-maintainability-baselines.md).

## Notes

### Method

Five throwaway analysers in [`method/`](2026-07-25-agent-built-repo-decay/method/)
(exploration-grade: no tests, not part of the framework's supported surface).
`scripts/openup-entropy.py` could not produce any of these findings — it is
keyed on OpenUP task ids, and only 54/181 commits in these repos carry one.

``bash
M=docs/explorations/2026-07-25-agent-built-repo-decay/method
APP=(--include 'app/*' --include 'lib/*' --include 'db/*' --include 'config/*' --include 'test/*')
python3 $M/decay.py          --repo <path> "${APP[@]}"   # monthly behavioural series
python3 $M/snapshots.py      --repo <path> "${APP[@]}"   # structure at each month end
python3 $M/survival.py       --repo <path> "${APP[@]}"   # line survival, message-independent
python3 $M/paired.py         --repo <path> "${APP[@]}"   # agent-vs-human, same month
python3 $M/coupling_trend.py --repo <path> "${APP[@]}"   # coupling per era
``

### 1. Structure — the direct test, and the clearest result

Rebuilding the tree at each month end (`snapshots.py`) tests "god objects
accumulate / structure stops keeping pace" by measuring the codebase as it
actually stood, rather than inferring it from commit behaviour.

Project B, over 13 months and **14× growth** (7,926 → 110,464 lines):

| month | files | lines | med | p90 | max | share >400 | test/src |
|---|---|---|---|---|---|---|---|
| 2025-06 | 69 | 7,926 | 45 | 382 | 675 | 0.087 | 0.00 |
| 2025-09 | 143 | 20,073 | 58 | 393 | 810 | 0.091 | 0.01 |
| 2025-12 | 200 | 28,069 | 70 | 392 | 774 | 0.095 | 0.007 |
| 2026-02 | 753 | 104,512 | 77 | 333 | 1865 | 0.076 | 0.43 |
| 2026-07 | 813 | 110,464 | 75 | **315** | 1865 | **0.074** | 0.48 |

**The fat tail got thinner while the codebase grew 14×.** p90 file length falls
382 → 315; the share of files over 400 lines falls 0.087 → 0.074. Median rises
45 → 75 and then goes flat from 2026-02. This is the single most direct
measurement of the decay claim available, and it points the other way.

Project A (97% agent) is flat on every structural measure across its life:
median 53 → 52, p90 168.5 → 169.4, share >400 lines 0.012 → 0.028. Its files
are dramatically *smaller* than Project B's human-era files (p90 169 vs 315).

The one metric that rises in both is files-per-module (4.9 → 23.9 and
12.4 → 23.1) — but see trap T5: in a Rails app that measures framework
convention, not entropy.

### 2. Behaviour — no 3–6 month cliff

Monthly blast radius (`decay.py`, application code only):

- Project B files/commit by month: 4.78, 3.29, 3.73, 2.40, 2.54, 3.46,
  3.15, 2.61, 3.14, 2.74, —, 2.40, 3.73, 3.39. **Flat across 13 months.**
  Modules touched per commit *falls*, 2.85 → 1.98. Months 4–6 (the predicted
  onset) are the calmest in the series.
- Project A: 9.63 → 5.69 → … → 7.16, with churn (deletions per line added)
  falling 0.269 → 0.05. The July rise follows a 3-month dormancy, not
  accumulation — which is also why Project A cannot test the 3–6 month window: it is
  5 months *calendar*, but only ~2.5 months active.

**Project B is the load-bearing repo for the thesis** — it is the only one of the
three that runs past the far end of the predicted window, and it shows no cliff.

### 3. Coupling — high, stable, and structural by design

Cross-module co-change share per era (`coupling_trend.py`):

- Project B: 0.645 → 0.411 → 0.654 → 0.490. No trend over 13 months; the
  agent era is *lower* than the human era.
- Project A: 0.429 → 0.957 → 0.941 → 0.922 — high, but flat after the
  scaffolding burst.

Project A's top pair is `config/locales/en.yml ~ config/locales/es.yml`, support 109,
**Jaccard 0.98** — a bilingual app whose translation files must move together.
The rest are `locales ~ routes.rb`, `model ~ db/schema.rb`,
`controller ~ routes.rb`: the Rails "every feature touches routes, schema and
locales" pattern.

This independently reproduces T-127's finding on two real applications: **the
strongest coupling pairs are correct-by-design, not decay.** A D1 threshold on
cross-module coupling would fire hardest on the i18n pair it is most important
not to break.

### 4. Line survival — where the interesting mistake was

Survival (of the lines a commit added, how many still exist at HEAD) is
message-independent, so it dodges the commit-subject confound in T3 below.
Compared within the same calendar month, so both cohorts share one exposure
window and one endpoint.

The first clean run said **agents churn more**: pooled agent survival 0.711 vs
human 0.761, delta −0.050. That confirms the thesis. It is an artifact.

| variant | agent | human | delta |
|---|---|---|---|
| all commits | 0.7112 | 0.7613 | **−0.0502** |
| exclude test-only commits | 0.7010 | 0.6221 | **+0.0789** |
| **exclude the single largest commit** | 0.7112 | 0.6360 | **+0.0751** |
| exclude top-5 largest | 0.7036 | 0.6217 | +0.0819 |
| commits < 1000 added lines | 0.7079 | 0.5918 | +0.1162 |
| commits < 500 added lines | 0.7317 | 0.6433 | +0.0884 |

**The sign flips on removing one commit** — `e34cd68` "Create minitest tests",
24,910 lines, 71% of all human lines added that month, surviving 97.9% because
generated tests are rarely edited afterwards. Every robustness variant reverses
the result: agent-written lines survive **+0.08 to +0.12 better** than
human-written lines.

The honest reading is *not* "agents write more durable code". It is that this
comparison is **not identifiable in these repos** — the commit that decides the
answer is bulk-generated test code, almost certainly agent-produced, that
carries no `Co-Authored-By` trailer and is therefore counted as human.

### 5. The agent era is when the tests arrived

`test/src` line ratio in Project B is **0.00 for the first seven human-built
months** (0.000, 0.000, 0.000, 0.010, 0.009, 0.007, 0.007), then jumps to 0.43
in 2026-02 and reaches 0.48 by 2026-07. Project A — 97% agent — is born at
0.70 and rises to 0.85.

On the evidence available, agent involvement in these two codebases *coincides
with the arrival of the test suite*, which is the main defence against exactly
the decay the thesis predicts.

### Measurement traps found

The previous run recorded traps T1 (shallow clone) and T2 (directory-prefix
`touches`). This run found three more, all of which produced results that
**falsely confirmed** the decay thesis before being caught.

- **T3 — commit subjects cannot compare agent and human defect rates.** Agents
  write conventional-commit prefixes 97–100% of the time; humans 21–82%. A
  `fix:`-prefix defect rate therefore measures *labelling discipline*, not
  defects. Tell: loosening the pattern shrank the gap (1.60× strict → 1.30×
  loose) — the signature of an artifact.
- **T4 — vendored framework code is attributed to whoever ran the sync.**
  100% of `scripts/` in both app repos is a copy of *this* framework, and
  Project A's 168 `chore(process): sync OpenUP framework` commits are 19.5% of its
  history. They were counted as large, high-survival "human" contributions.
  Blocklist scoping kept admitting them; only an **allowlist** of real
  application directories (`app/ lib/ db/ config/ test/`) fixed it. This is why
  every number above is allowlist-scoped.
- **T5 — files-per-module measures framework convention in a Rails app.** With
  module depth 2, `app/models` is one module holding hundreds of files by
  Rails' own design. Its rise is the app growing inside a fixed skeleton, not
  structure failing to subdivide. It is the only metric that rises in both
  repos, and it should not be read as entropy.

The recurring shape: **large, machine-generated, rarely-edited commits
masquerade as high-quality human work.** All three traps are instances of it.

## Options Considered

- **Option A — treat this as sufficient evidence to close the decay question.**
  Pro: two independent applications, one at 13 months, agree with the framework
  repo's own baseline; three structural measures and the coupling trend all
  point away from decay. Con: n=3 repos, one owner, one stack (Rails), one
  agent vendor; Project A's dormancy means only Project B truly probes past 6 months.
- **Option B — productize the measures that changed the answer.** Fold
  allowlist scoping, monthly structural snapshots, line survival and era-sliced
  coupling into `scripts/openup-entropy.py`. Pro: the existing M1 tool could not
  have produced a single finding here, and would have reported the *opposite*
  conclusion on Project A via T4. Con: real delivery cost on a tool with one user.
- **Option C — build D1/R1 gates now anyway.** Rejected below.

## Open Questions

- Does the decay signal require a **team** rather than a solo operator? All
  three repos have one primary owner. Horthy's failure mode may be a
  coordination effect that a single-owner repo cannot exhibit.
- Project A has never been past ~2.5 active months. Re-measuring it after a
  sustained Q4 would be the first genuine test of the 3–6 month window on a
  97%-agent codebase.
- Is `test/src ≥ 0.4` the actual mechanism protecting these repos? That is a
  testable prediction: an agent-built repo *without* a test suite should decay.
  None of the three repos can answer it — all three have tests.
- What would make authorship identifiable? A trailer on generated bulk commits
  would have prevented the §4 sign flip outright.

### Product-manager challenge pass

- **Pushback — on the brief's own design queue, which this data does not
  support.** D1 (coupling thresholds) is now refuted on three independent
  codebases: the top pairs are `en.yml ~ es.yml` (J=0.98), `model ~ schema`,
  `controller ~ routes`. A D1 gate's first act would be to flag the i18n
  invariant. R1 likewise has no failure mode to point at. Building either now
  means paying permanent ceremony cost to defend against a decay pattern that
  three repos and 2,500 commits decline to exhibit. *Disposition: rejected —
  the evidence killed it, per §7's own discipline ("gates only for failure
  modes the data shows").*
- **Pushback — on my own §4 result.** The +0.08 survival advantage is *not*
  license to claim agents write more durable code, and should not be quoted as
  such. The measure is unidentifiable here for the reason given. *Disposition:
  accepted — stated inline in §4 rather than reported as a finding.*
- **Complement — the brief asked the wrong question.** It framed the work as
  "measure decay". The measurable thing that actually separates these repos is
  **test ratio**, not entropy: 0.00 for seven human-built months, 0.43+ once
  agents arrive. If maintainability is the goal, the evidence points at test
  coverage as the live variable, and P3 (verify gate + CI) — already in the
  queue — is the item that acts on it. *Disposition: accepted — recorded as the
  strongest surviving candidate in the queue.*
- **Refine — make the remaining claim falsifiable.** "Agent codebases decay"
  is not testable as stated. The version this data can be held to:
  *an agent-built repo with `test/src < 0.1` will show rising p90 file length
  and rising cross-module coupling share within 6 active months.* All three
  repos hold `test/src ≥ 0.43` and none show either. That is a prediction a
  future repo can refute. *Disposition: accepted — replaces the vague framing
  as the question any follow-up must answer.*
- **Refine — name what "no decay" is licensed to mean.** It means: on these
  three repos, at 4/5/13 months, one stack, one owner. It does **not** mean the
  thesis is false in general, and no roadmap entry should cite it that way.
  *Disposition: accepted — scoped in §1 and in the Open Questions.*

## Where this goes next

→ **iteration** — promote one roadmap entry, *"Fold the four measures that
changed the answer (allowlist scoping, structural snapshots, line survival,
era-sliced coupling) into `scripts/openup-entropy.py`"*, because the shipped M1
tool would have reported the opposite conclusion on Project A via trap T4
and cannot measure a repo without OpenUP task ids at all; D1 and R1 stay
unbuilt as explicitly refused, and P3 inherits the test-ratio evidence.

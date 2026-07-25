# Exploration: measurement tooling + lane hygiene — findings and proposed fixes

**Started:** 2026-07-25
**Question:** The maintainability-measurement work (T-127, T-128) and the two-application decay run each exposed defects in the framework's own tooling rather than in the codebases under study — which of them are worth fixing, and in what order?

## Context

Three runs happened in sequence:

1. **T-127** — built `scripts/openup-entropy.py` (M1) and produced this repo's
   baseline: [2026-07-25-maintainability-baselines.md](2026-07-25-maintainability-baselines.md).
2. **T-128** — added `--unit {task,commit,pr}` after the analyzer exited `3` on a
   repo with no task ids.
3. **The application run** — measured Project A and Project B:
   [2026-07-25-agent-built-repo-decay.md](2026-07-25-agent-built-repo-decay.md).
   Its verdict on the decay thesis is settled there and is **not** re-litigated
   here.

That third run reached its conclusions with **836 lines of throwaway analysers**
under [`method/`](2026-07-25-agent-built-repo-decay/method/) because the shipped
M1 tool could not produce a single one of its findings. This exploration
separates that — plus four smaller defects found along the way — from the
research question, so the *fixes* can be planned on their own merits.

Every finding below was re-verified against the working tree at `2c44b1a` on
2026-07-25 before being written down.

## Notes

### F1 — The shipped analyzer cannot do the analysis that mattered

`scripts/openup-entropy.py` (721 lines, 29 tests) produced this repo's baseline
fine and produced **nothing** usable on the two application repos.

| gap | evidence | consequence |
|---|---|---|
| no allowlist scoping — `--exclude` only, no `--include` (verified: `--include` → `unrecognized arguments`) | trap T4: 100% of `scripts/` in both app repos is a vendored copy of *this* framework, and Project A's 168 `chore(process): sync OpenUP framework` commits are 19.5% of its history | blocklist scoping "kept admitting them"; they were counted as large high-survival human commits. **The tool would have reported the opposite conclusion on Project A.** |
| no structural snapshots | `snapshots.py` (118 lines) rebuilds the tree at each month end — p90 file length, share >400 lines, test/src ratio | the single most direct test of "god objects accumulate" is absent; it is what showed Project B's fat tail *thinning* across 14× growth |
| no era slicing on coupling | `coupling_trend.py` (104 lines) | coupling is reported pooled over all history, so "agent era vs human era" is uncomputable |
| task-id keying | only **54/181** app-repo commits carry an OpenUP id | T-128's `--unit commit` mitigates this but does not fix scoping |

**Proposed solution.** Fold three of the four measures into the analyzer, with
`method/` as the reference implementation:

- `--include GLOB` (repeatable), applied **before** excludes, defaulting to
  everything when absent. Cheapest of the three and the one that changed a
  conclusion.
- `--snapshots` — month-end structural series (files, lines, median/p90/max file
  length, share over a threshold, test/src ratio).
- `--era FROM:TO` (repeatable) or `--by-era` — slice coupling by date range.

Deliberately **not** folded in: line survival — see the PM pass.

### F2 — The id allocator can re-issue a live task id (correctness bug)

`used_seqs_in_repo()` (`scripts/openup-claims.py:476`) unions exactly three
sources, per its own docstring: change-folder `plan.md` frontmatter ids,
`docs/roadmap.md` text, and `origin/main:docs/roadmap.md`. Plus live
reservations from `reserved_seqs()`.

**Run-log shards, status-note filenames, and git commit subjects are not
scanned.** A `quick`-track task creates no change folder (by design — "state
file + auto-log only, no plan gate") and need not add a roadmap row. Verified for
T-125 and T-126: no change folder, **0 roadmap hits**, 1 run-log shard each.

That is why `next-id` returned `T-125` during T-127 while T-126 already existed.
It reads correctly *now* (`T-129`) only because T-127/T-128 left archive folders.
The blind spot is intact: **the next quick task's id is re-issuable.**

**Proposed solution.** Add the lane-owned audit trees as scan sources — the
`task_id` field in `docs/agent-logs/runs/*.jsonl` and the `<id>` in
`docs/status-notes/YYYY-MM-DD-<id>.md` filenames. Both are committed, both are
written by every task on every track, and neither can be skipped the way a
roadmap row can. Cheap and closes the class, not just the instance.

### F3 — The fence cannot see two sequential lanes on one branch

`resolve_base()` (`scripts/openup-fence.py:98`) tries `--base`, then
`origin/main`, then `main`. It has no notion of *where this lane started*.

Verified: `openup-fence.py check --task-id T-128 --base origin/main` reports
three `OUT OF LANE` violations — all of them T-127's archived files, which T-128
never touched. Passing `--base <T-127's completion sha>` clears it.

This never fires under worktree-per-lane (one lane per branch). It fires whenever
two lanes run sequentially on one branch, which is exactly what a harness-managed
single designated branch forces. The failure mode is bad: **completion is
blocked**, the message accuses the current lane of an escape it did not commit,
and the workaround requires knowing the prior lane's sha — which an autonomous
loop has no way to discover.

**Proposed solution.** Stamp the lane's base at acquisition: `openup-session.py
begin` records `base_sha` (the `HEAD` it branched from, or the current `HEAD` for
an in-place start) into `.openup/state.json` and the claim file; `resolve_base`
prefers it, falling back to today's chain when absent. Deterministic, additive,
and consistent with "if a step is deterministic, the harness does it."

### F4 — `docs/INDEX.md` has been stale on trunk since before this work

`docs-index.py --check` reports drift; regenerating adds a missing T-071
iteration-plan entry. It predates T-127 and is unrelated to any of these lanes —
which is why T-127 reverted the regeneration rather than smuggle an out-of-lane
view fix into its diff. `openup-doctor.py` has been reporting it as a warning the
whole time.

**Proposed solution.** Regenerate on trunk (`python3 scripts/docs-index.py`) as a
standalone quick task. One command; the only reason it is still here is that
every lane correctly refused to adopt it.

### F5 — No runtime shallow-clone guard, despite T1 corrupting the first baseline

Verified: no `shallow` check anywhere in `openup-entropy.py`. Trap T1 is
documented in prose in the CLI reference and in the baseline note, and nothing
enforces it.

The failure is silent and severe: on the shallow checkout, git matched 34 of 126
tasks and the boundary commit attributed the **entire 2560-file tree** to T-056.
A CI-hosted entropy job on a default `actions/checkout` (depth 1) would emit
confident garbage.

**Proposed solution.** At startup, if `.git/shallow` exists (or
`git rev-parse --is-shallow-repository` returns true), print a prominent warning
naming `git fetch --unshallow`, and carry `sources.shallow: true` in the `--json`
payload so a downstream consumer can refuse the data. Warn, not fail — a shallow
report is still valid for recent history, and the tool is report-only.

### F6 — The analyzer never reaches the projects that need it

`openup-entropy.py` is absent from `scripts/process-manifest.txt` (verified: 0
hits). T-127 decided this deliberately: the manifest's stated criterion is
"runtime scripts the workflow skills invoke", and nothing invokes the analyzer.

That decision now looks wrong for a reason T-127 could not see. Trap T4
established that **both application repos already vendor this framework's
`scripts/` wholesale** — so manifest registration *is* the distribution channel
that would have put the analyzer on the repos the baseline programme is about.
Its absence is why the application run had to write throwaway analysers.

**Proposed solution.** Register it, and widen the manifest's stated criterion to
cover maintainer-invoked read-only diagnostics (`openup-doctor.py` is already
there on effectively that basis).

## Options Considered

- **Option A — fix all six as one "measurement hardening" program.** Pro: they
  share a theme and two share a file. Con: bundles a 1-command doc regeneration
  with a multi-measure feature; the bundle's slowest item gates its cheapest.
- **Option B — split by kind: two quick tasks (F4, F5), one correctness lane
  (F2 + F3), one feature lane (F1 + F6).** Pro: each lands on its own merits, and
  the cheap high-value guards ship without waiting on the feature work. Con: four
  intake events instead of one.
- **Option C — productize all four exploration measures verbatim, including line
  survival.** Rejected in the PM pass below.
- **Option D — drop F1 and keep `method/` as the permanent home for
  application-repo analysis.** Pro: zero delivery cost; the scripts work and are
  committed. Con: 836 lines of untested code with no supported surface is exactly
  the "green run that never ran the build" problem one level up — and the next
  measurement will re-derive it from scratch.

## Open Questions

- Does F3 matter under the project's *intended* workflow? Worktree-per-lane is
  the documented default and never triggers it. The answer decides whether F3 is
  a real fix or an accommodation of one harness's constraint.
- Should `--snapshots` be a mode of `openup-entropy.py` or a sibling script? The
  analyzer is commit-history-shaped; snapshots are tree-shaped and need a
  checkout per sample point. Folding them in may be the wrong seam.
- What is the acceptance test for F1 — is "reproduces `method/`'s published
  Project A/Project B numbers" checkable without those repos in the session? (Neither
  is reachable from every machine; this session could not reach Project A at all.)
- Does F2 warrant a validator (`openup-doctor.py` check for ids present in run
  logs but absent from the allocator's sources) rather than only widening the
  scan?

### Product-manager challenge pass

- **Pushback — do not productize line survival (F1's fourth measure).** The
  exploration's own §4 concluded the measure is *not identifiable* in these
  repos: the sign flips on removing a single commit, and the deciding commit is
  bulk-generated test code miscounted as human. Shipping it as a supported
  feature would give a confounded metric the authority of the framework's
  toolchain, and its first output would be the "agents churn more" artifact that
  took a robustness sweep to catch. *Disposition: accepted — F1 folds three
  measures, not four; survival stays in `method/` as exploration-grade.*
- **Pushback — F1 as a single roadmap entry hides four different value cases.**
  Allowlist scoping changed a *conclusion*; structural snapshots produced the
  clearest *result*; era-sliced coupling is a convenience. They should not share
  one entry, and `--include` should land first because it is the cheapest and the
  only one that prevents a wrong answer. *Disposition: accepted — folded into
  Option B, with `--include` sequenced ahead of the rest.*
- **Complement — F6 is a prerequisite for F1, not a tidy-up.** Improving the
  analyzer changes nothing for the application repos unless it reaches them, and
  the manifest is the channel that does it (they already vendor `scripts/`).
  Ordering F1 before F6 would ship an improvement nobody receives.
  *Disposition: accepted — F6 rides with F1 in the same lane.*
- **Complement — F5 is the cheapest defect on this list and the only one with a
  demonstrated wrong answer already attached.** It was recorded as a "gotcha" in
  T-127's learnings and never became work. A prose warning in a CLI reference is
  not a guard. *Disposition: accepted — F5 is a quick task, sequenced first.*
- **Refine — F1's value claim needs a falsifiable acceptance test, not "parity
  with `method/`".** The version this can be held to: *`openup-entropy.py
  --include 'app/*' …` on a repo that vendors this framework must exclude the
  vendored `scripts/` tree from every metric, and its structural series must
  reproduce the published Project B p90 trend (382 → 315) to the line.* That is
  checkable from the numbers already recorded in the sibling exploration, without
  needing the private repos in-session. *Disposition: accepted — recorded as
  F1's acceptance criterion and as the answer to the third open question.*
- **Refine — F2 is a correctness bug, not a papercut, and should be stated as
  such in its roadmap `Value`.** Two lanes issued the same id is data loss with a
  manual recovery (the T-024→T-030 renumber is the precedent already cited in the
  create-task-spec skill). Its ordering should not sit behind a feature.
  *Disposition: accepted — F2 leads the correctness lane.*
- **Pushback on my own framing — "six findings" overstates the delivery.** F4 is
  one command, F5 is ~15 lines, F2 is a scan-source addition. Only F1+F6 is real
  feature work. Presenting this as a six-item program would inflate a half-day of
  fixes into a program. *Disposition: accepted — the disposition below names one
  lane and two quick tasks, not six entries.*

## Where this goes next

→ **iteration** — promote one correctness lane, *"Lane-hygiene fixes: scan
lane-owned audit trees for used task ids (F2) and stamp the lane's `base_sha` at
`begin` so the fence resolves its own base (F3)"*, with **F5 (shallow-clone
guard) and F4 (regenerate `docs/INDEX.md`) taken first as `/openup-quick-task`
items**, and the analyzer feature work (F1 `--include` → `--snapshots` →
`--by-era`, shipped together with F6 manifest registration) queued behind them as
a second entry whose acceptance criterion is the Project B p90 reproduction named
above; line survival is explicitly **not** productized.

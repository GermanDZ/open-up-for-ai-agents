# Exploration: Advisor-tool pattern at OpenUP gates

**Started:** 2026-07-09
**Question:** Should OpenUP embed an "advisor consult" (a stronger model reviewing the executor's plan/result at existing gates), and if so where, how, and how would we know it paid for itself?

## Context

Anthropic shipped the **advisor tool** (Messages API beta, `advisor_20260301`,
header `advisor-tool-2026-03-01`): a fast/cheap *executor* model can consult a
stronger *advisor* model mid-turn; the advisor sees the full transcript and
returns a plan or course-correction as text. Anthropic's measured guidance:
the biggest lift comes from (1) one consult early, before committing to an
approach, and (2) one consult before declaring done. Docs:
<https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool>.

Two facts frame this exploration:

- **The advisor call points map one-to-one onto gates OpenUP already has.**
  "Consult before substantive work" ≈ the plan gate at `/openup-start-iteration`;
  "hard rule: first state-changing write follows an advisor call" ≈
  fix-spec-first; "consult before declaring done, after making the deliverable
  durable" ≈ `/openup-complete-task` (persist first, then gate); "consult when
  stuck" ≈ `/openup-create-handoff`. The process structure is already
  advisor-shaped — only the *model seating* at each gate is undecided.
- **Claude Code does not expose the advisor tool.** It is an API/SDK feature.
  `model:` frontmatter (docs-eng-process/model-tiers.md) cannot declare an
  advisor today. Any adoption now is an *emulation*: a higher-tier read-only
  subagent consulted at a gate.

Related artifacts: `docs-eng-process/model-tiers.md` (five tiers; rule: "a
gate must never run on a weaker model than the work it judges"),
`docs/explorations/2026-07-05-next-loop-efficiency.md` (loop cost),
token-efficiency protocol in `.claude/CLAUDE.openup.md`.

## Notes

### What the advisor tool actually buys (per Anthropic's docs)

- Sonnet executor + Opus advisor ≈ Sonnet-solo-at-default-effort quality or
  better, at similar or lower total cost, on long agentic tasks.
- Advisor output is the cost driver; `max_tokens: 2048` on the tool cut mean
  advisor output ~7x with near-zero truncation and no measured quality loss.
- Advisor-side prompt caching breaks even at ~3 consults per conversation.
- Executors under-call without steering; the measured fix is prompt blocks
  that anchor consults to *checkpoints* ("before first write", "before
  declaring done") rather than to self-assessed difficulty. Over-prompting
  Opus executors made them worse.

The checkpoint insight is the transferable part: **timing rules beat judgment
rules**. OpenUP's gates are exactly such checkpoints, already enforced by
process rather than by the agent's self-assessment.

### Where an advisor consult could seat in OpenUP

| Gate | Advisor analog | Standing today |
|---|---|---|
| `/openup-start-iteration` plan gate (standard/full) | "consult before committing to an approach" | Plan persisted, no independent review unless full-track team deployed |
| Fix-spec-first | "advisor call before first state-changing write" | Enforced as a rule, no second model involved |
| `/openup-complete-task` step 3a + rubric | "consult before declaring done" | Rubric graded by the session model (self-review) |
| `/openup-create-handoff` | "consult when stuck" | Handoff is written, not reviewed |

The two Anthropic measured as highest-value are the first and third rows.

### Interaction with the model-tiers rule

`model-tiers.md` rule: *"The gate must never run on a weaker model than the
work it judges"* — which forces quality gates to `inherit`. The advisor
pattern creates a third option the rule doesn't anticipate: the gate's
*executor* can be cheap if the *judgment* comes from a stronger advisor.
Whether that satisfies the rule's intent (judgment strength ≥ author
strength) is a wording question for `model-tiers.md` if adoption happens —
but only then; see challenge pass.

### The emulation available today

A read-only consult subagent (shape of `openup-explorer`: Read/Glob/Grep/Bash,
never modifies) pinned to a strong model, given the change folder + plan, and
asked for a ≤6-bullet critique: risks the plan misses, cheaper alternatives,
spec/plan mismatches. Differences from the real advisor tool: it does not see
the executor's live transcript (only what the repo persists — which OpenUP's
"no state outside the repo" rule makes unusually complete), and it costs a
subagent spawn rather than an in-turn sub-inference. The repo-persistence rule
is what makes the emulation viable at all: the plan, spec, and design notes
*are* the transcript that matters.

### When the consult is worthless

If the session already runs on the top-tier model, an "advisor" of the same
tier adds an independent-perspective benefit at best, a token bill at worst.
The value case exists only when (a) sessions run on sonnet/haiku, or (b) the
independent-reviewer effect (fresh context, no sunk-cost bias) is itself the
point. (b) is plausible — it is the same argument as full-track team review —
but it is unmeasured here.

## Options Considered

- **Option A — do nothing until the harness exposes the advisor tool.**
  Pro: zero speculative work; frontmatter-declared adoption becomes trivial
  later. Con: forgoes the (possibly real) independent-review benefit now;
  no evidence gathered for the later decision.
- **Option B — pilot one consult at the `/openup-start-iteration` plan gate
  (standard track), emulated via a strong-model read-only subagent.**
  Pro: matches Anthropic's highest-value call point; bounded (one consult,
  ≤6 bullets, capped output); measurable per-iteration ("did the consult
  change the plan / catch a defect?"). Con: adds a spawn + tokens to every
  standard iteration; risks ritual advice nobody acts on.
- **Option C — full adoption: consults at plan gate + complete-task, plus an
  "Advised" tier in model-tiers.md and prompt blocks in the `inherit` skills.**
  Pro: captures the whole pattern. Con: builds process around an unshipped
  harness feature; doubles the per-iteration consult cost before any evidence
  that one consult pays.
- **Option D — consult at `/openup-complete-task` only (pre-rubric).**
  Pro: targets the self-review weakness (author grading own work). Con:
  catches defects *after* the work is done — the plan-gate consult prevents
  them earlier and is where Anthropic measured the larger lift.

## Open Questions

- Measurement: what counts as "the consult paid"? Proposed falsifiable form:
  over N pilot iterations, the consult either (a) produced a plan change the
  executor adopted, or (b) flagged a defect later confirmed — in ≥ some
  threshold of iterations. Threshold TBD at iteration scoping.
- Which model pins the consult agent when the session is already top-tier —
  skip the consult, or run it anyway for the fresh-context effect?
- Does the consult replace the full-track team's independent-review function
  for some tasks (a cost *reduction*), or only add to standard track (a cost
  *increase*)? The former is the stronger value case and should be tested.
- Track applicability: quick track should never consult (ceremony rule);
  is full track already covered by team review, making standard the only
  candidate?
- Consult output budget: Anthropic's `max_tokens: 2048` maps to "≤6 bullets"
  here — is that cap right for plan critique?

### Product-manager challenge pass

- **Pushback 1 — "prepare model-tiers.md for a future advised tier" is
  speculative work.** No harness support exists; a tier nobody can declare
  will rot, and the doc's own history (Kaze audit) shows unenforceable
  guidance gets ignored. What changes for which user today? Nothing.
  → **Accepted (submission narrowed):** the model-tiers.md change is dropped
  from any near-term scope; at most, this exploration is linked from a
  one-line "future: advisor tier" remark *if* the pilot proceeds. Option C
  is rejected on the same ground.
- **Pushback 2 — the consult risks degrading into ritual.** A ≤6-bullet
  critique appended to every plan that nobody acts on is pure token cost plus
  false confidence. How would we notice? Only with a per-iteration measure.
  → **Accepted:** the pilot is defined *with* the falsifiable measure (consult
  adopted-or-confirmed rate over N iterations, read back at retrospective via
  the existing Measure Read-Back mechanism) or it doesn't run. An unmeasured
  pilot is rejected.
- **Pushback 3 — value is conditional on session model.** When the session
  runs top-tier, "stronger advisor" is impossible and the claim reduces to
  "fresh independent context helps," which this repo already gets from
  full-track team review. The pilot must record the session model per consult
  so the read-back can split the two effects.
  → **Accepted:** added to the pilot's data capture.
- **Complement — the stronger value case is substitution, not addition.**
  The submission framed the consult as a new step; the better business
  framing is that a single bounded consult may *replace* deploying a
  full-track team purely for independent review — a cost reduction aligned
  with the token-efficiency protocol, not a ceremony increase.
  → **Accepted:** folded into Open Questions and the pilot's read-back
  questions.
- **Refine — narrow "adopt the advisor pattern" to one falsifiable pilot.**
  One consult, one gate (start-iteration plan gate, standard track), one
  measure, N iterations, then a retrospective read-back decides extend /
  keep / drop. Option D (complete-task consult) is deferred, not rejected:
  it only enters if the plan-gate pilot's evidence supports a second consult.
  → **Accepted:** this is the disposition below.

## Where this goes next

→ iteration — add a roadmap entry "Advisor-consult pilot at the
start-iteration plan gate": a strong-model read-only consult subagent
critiques the persisted plan (≤6 bullets) on standard-track iterations,
with per-iteration adoption/defect-caught capture and a retrospective
read-back after ~5 iterations deciding extend, keep, or drop.

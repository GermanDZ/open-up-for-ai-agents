# Exploration: DSLs for LLM reliability, mapped onto the OpenUP process

**Started:** 2026-07-14
**Question:** Which claims in Fowler-site article "DSLs Enable Reliable Use of LLMs" (Unmesh Joshi, <https://martinfowler.com/articles/llm-and-dsls.html>) translate into concrete error-reduction or implementation-quality improvements for this process — and which are already implemented here?

## Context

The article argues that LLMs become *reliable* generators when pointed at a
constrained, domain-specific surface instead of a general-purpose one. Its
load-bearing claims:

1. **Upfront specs are hypotheses** — design is discovered through
   implementation; the loop is spec → generate → review → revise.
2. **DSLs strip variation** — a constrained vocabulary responds well to a few
   in-context examples; less room to hallucinate; a reviewer reads the result
   as a description of intent, not code to audit line by line.
3. **A DSL ships with a deterministic validator** (parser, JSON schema, type
   checker). An agent can generate → validate → repair *without a human in the
   loop*, and — crucially — the errors are phrased **at the level of the
   domain** ("you cannot select an action before choosing a client"), not as
   stack traces.
4. **Semantic model as fixed substrate** — good abstractions (even without new
   syntax) remove whole decision classes (threading, timing, plumbing) from
   every prompt; the LLM only fills in the domain logic.
5. **Two phases of LLM use** — phase 1: co-designer while the
   vocabulary/DSL is being shaped (iterative, human in the driver's seat);
   phase 2: natural-language interface to the finished vocabulary.
6. **The DSL artifact, not the prompt, is the source of truth** — the
   generated program in domain vocabulary stays readable and maintainable;
   no need to recover the original prompt.
7. **Caveats the author states**: the advantage holds only while the DSL stays
   small enough for few-shot conveyance; there is real upfront design +
   maintenance cost; payoff concentrates in well-factored, genuinely
   constrained DSLs *backed by a validator*.

Related artifacts: `scripts/check-docs.py`, `scripts/openup-spec-scenarios.py`,
`scripts/openup-fence.py`, `scripts/openup-board.py`,
`scripts/docs-meta.schema.json`, `scripts/openup-state.schema.json`,
`docs-eng-process/coordination-frontmatter.md`, `.claude/rubrics/`,
prior exploration `2026-06-12-openspec-clarity-waste.md` (ritual-risk
precedent).

## Notes

### What the process already implements (the article validates, not informs)

Much of the article reads as a post-hoc justification of decisions this repo
has already made. Worth naming explicitly so we don't re-buy what we own:

- **Deterministic validators with domain-phrased errors** (claim 3): the
  process has a full harness of model-free, stdlib-only checkers —
  `check-docs.py` (frontmatter schema + trace-ref resolution + coverage),
  `openup-spec-scenarios.py` (Given/When/Then presence), `openup-fence.py`
  (lane surface), `check-model-tiers.py`, `openup-doctor.py`. All are
  deterministic ("identical input → identical output"), and their findings are
  phrased in process vocabulary, which is exactly what enables the
  generate → check → repair loop the article describes.
- **Semantic model as substrate** (claim 4): the skills are the constrained
  verb set; roles are constrained hats; `script-cli-reference.md` exists
  precisely to keep the CLI vocabulary in context instead of re-derived;
  coordination frontmatter (`touches`, `track`, `depends-on`) is a mini-DSL.
  The "custom briefing is a symptom of an incomplete spec" rule is the
  article's claim 6 stated as process law: the persisted artifact, never the
  conversation, is the source of truth.
- **Two-phase division** (claim 5): `/openup-explore` *is* phase 1 (design the
  vocabulary; notes, not deliverables); the delivery skills are phase 2 (the
  agent as NL interface to an established vocabulary). This framework repo as
  a whole is a phase-1 product whose consumers run phase 2.

### Where the article exposes real gaps (error-reduction candidates)

**Gap A — the scenario check validates ritual, not structure.**
`openup-spec-scenarios.py` checks that bold `**Given**/**When**/**Then**`
markers *exist* in each requirement. It cannot see whether the scenario names
an actor, a concrete action, or an observable outcome — a vacuous scenario
passes. The article's lever: make the scenario a *parseable structure* (a
fenced block with a tiny grammar) so the validator checks shape, and so
`/openup-create-test-plan` can mechanically derive test-case stubs and
`verified-by` ids from it. That converts spec→test drift from a rubric
judgement into a schema failure.

**Gap B — rubrics are non-deterministic validators.**
Rubric grading (`.claude/rubrics/*.md`) is an LLM judging prose — exactly the
kind of check the article says to push into deterministic tooling *where the
criterion is mechanical*. Run-to-run variance in rubric grading is a direct
error source at the complete-task gate. An audit pass over the seven rubrics,
splitting each criterion into **mechanizable** (migrate to a checker:
presence, structure, link resolution, enum membership, length bounds) vs
**judgement-only** (stays in the rubric), would shrink the LLM-graded surface
and make the gate cheaper and more consistent.

**Gap C — one concept, two grammars.**
The roadmap accepts two entry shapes (table rows and free-form `## T-NNN:`
sections with `**Status**:` lines), and `sync-status.py` only stamps the first
— producing the observed status-rot (see the pending roadmap entry describing
T-063/T-064/T-066 rotting to `pending` despite being merged). This is the
article's carrier-syntax point made concrete: a DSL with two dialects and a
validator that speaks only one *guarantees* silent drift in derived views.
Either unify the grammar or teach every parser both dialects — the current
half-coverage is the worst point on the curve. (A pending roadmap entry
already targets the sync side; the grammar-unification framing is the more
durable fix.)

**Gap D — coordination frontmatter has docs but no schema.**
`docs-meta.schema.json` covers *instance* frontmatter, but the coordination
block (`touches`, `track`, `depends-on`) that the board, claims, and fence all
parse is specified only in prose (`coordination-frontmatter.md`) and parsed by
regex. A misdeclared `touches` surfaces late — as a fence failure at push —
instead of immediately at spec-creation with a domain-phrased error the agent
could self-repair from. A small JSON schema + validation at
`/openup-create-task-spec` exit shifts that error left.

### What the article warns against (and this repo has prior art on)

The author's own caveat — DSLs pay off only while small, validated, and
genuinely constrained — matches the `2026-06-12-openspec-clarity-waste.md`
finding: structure that no tool consumes degrades into ritual. Every candidate
above therefore has to name the *consumer* of the new structure (a script, a
gate) before it earns syntax. Structure without a validator-consumer is
ceremony; that is the line.

## Options Considered

- **Option A — Structured scenario blocks + mechanical test-plan derivation.**
  Replace the presence-check with a small fenced grammar; test-plan skill
  consumes it. Pro: closes spec→test drift deterministically. Con: largest
  build cost; risk of Gherkin-style ritual if scenarios aren't actually
  consumed downstream; this repo's own deliverables are mostly docs/scripts,
  so the executable-test payoff is thinner here than in consumer projects.
- **Option B — Rubric mechanization audit.** Classify every rubric criterion
  mechanizable vs judgement; migrate the former into `check-docs.py`-style
  checks. Pro: reduces gate variance at the exact enforcement point; shrinks
  LLM-graded surface (cheaper, consistent). Con: some criteria will be
  borderline; needs care not to freeze prose style into lint rules.
- **Option C — Grammar unification for roadmap entries.** One entry shape (or
  full dual-dialect parser coverage). Pro: kills an *observed*, recurring
  drift bug class. Con: partially overlaps a pending roadmap entry (sync-side
  fix); migration touches a shared view.
- **Option D — Schema for coordination frontmatter, validated at spec
  creation.** Pro: cheapest; shifts fence failures left to a self-repairable
  moment; direct instance of the article's validator pattern. Con: small win
  on its own; fence already catches the error eventually.

## Open Questions

- How often has rubric grading actually flip-flopped (same artifact, different
  verdicts)? No telemetry exists; the audit (Option B) would need a quick
  retrospective sample from `docs/agent-logs/` to size the problem.
- For Option A: in *consumer* projects (not this framework repo), do
  `/openup-create-test-plan` outputs today trace back to plan scenarios at
  all, or is the linkage purely nominal via `verified-by`?
- Do the artifact skills carry enough few-shot examples of our bespoke
  frontmatter/scenario forms for lower-tier models (the article's
  novel-DSL caveat)? Worth a spot-check of `model: haiku`-tier skills.

### Product-manager challenge pass

- **Pushback:** "Adopt DSLs to reduce errors" as a general directive is
  already this repo's architecture — the article mostly *confirms* T-024,
  T-034–T-039, and the validator harness. A generic "add more DSL" entry would
  be ritual. Option A's full version (executable scenario grammar) has a thin
  value case *in this repo*: the falsifiable question is "what fraction of
  completed tasks show spec→test drift today?", and nobody has measured it.
  **Disposition: accepted** — Option A is deferred until that measure exists;
  it is not promoted.
- **Pushback:** Option C overlaps the pending status-rot roadmap entry; a
  second entry doing grammar unification would collide with it.
  **Disposition: accepted** — Option C folds into the existing pending entry
  as a design consideration (note in that entry's future change folder), not a
  new entry.
- **Complement:** the submission asked about "performance (less errors, better
  implementation)" — the only *observed, recurring* error classes in the repo
  record are (1) status-rot from dual grammar (Gap C, already on the roadmap)
  and (2) late fence/check-docs failures caught at gate time rather than
  authoring time (Gaps B/D). Evidence should drive the pick: B+D target the
  observed class; A targets a hypothetical one. **Disposition: accepted** —
  the promoted work is B+D, scoped as one standard-track task.
- **Refine:** from "how could DSLs help our process" to the falsifiable form:
  "which gate-time failures (fence at push, check-docs at 3a, rubric
  flip-flops) would a schema or mechanized check have converted into an
  immediate, self-repairable authoring-time error — and does the count drop
  after shipping B+D?" Measure: gate-time failure count per completed task,
  before vs after, readable from `docs/agent-logs/`. **Disposition: accepted**
  — recorded as the success measure for the proposed entry.

## Where this goes next

→ iteration — add a pending roadmap entry "Deterministic-validator expansion:
schema-validate coordination frontmatter at spec creation (Gap D) + migrate
mechanizable rubric criteria into deterministic checks (Gap B)", standard
track, with the gate-time-failure count as its success measure; Options A and
C are explicitly not promoted (A awaits evidence of spec→test drift; C folds
into the existing status-rot entry).

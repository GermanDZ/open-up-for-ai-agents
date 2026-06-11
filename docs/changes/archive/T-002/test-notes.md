# T-002 Test Notes — `/openup-sync-spec`

> Role: tester (construction). Subject under test: `.claude/skills/openup-workflow/sync-spec/SKILL.md`
> (PROSE skill — "tests" = structural checks + dry-run scenario walkthroughs of the skill's own instructions).
> Oracle: `plan.md` (## Verification, ## Requirements, ## Safeguards) and `design.md` (DD2 heuristic, DD3 refusal/routing).
> Date: 2026-06-11. Verdict: **PASS** (7/7 checks pass; 1 cosmetic observation, no defects).

## A. Structural checks

| # | Check | Result | Evidence |
|---|---|---|---|
| A1 | Skill exists with valid YAML frontmatter; `name: openup-sync-spec`, `model: inherit`; shape matches sibling `readiness/SKILL.md` | **PASS** | `sync-spec/SKILL.md` L1 `---`, L2 `name: openup-sync-spec`, L4 `model: inherit`, L16 `---`. Same fence+`name:`+`model:` shape as `readiness/SKILL.md` (L1/L2 `name: openup-readiness`/L4 `model: haiku`/L13). Both add a `fit:`/`arguments:` block — consistent. |
| A2 | All 4 templates have exactly ONE valid YAML frontmatter block containing `last-synced: ""`; task-spec unchanged | **PASS** | Each of the 4 templates: exactly one frontmatter block found, `last-synced` present inside it, and exactly one `last-synced` occurrence in the whole file (no second fence introduced). The 3 edited templates carry a leading `<!-- Source: … -->` comment (L1-3) before the `---` fence (L5); `last-synced: ""` was appended after `related:` at L17, closing fence L18 — exactly the DD1 "append into the existing legacy YAML block" instruction. task-spec.md keeps its single clean frontmatter block with `last-synced` at L10. |
| A3 | DD2 classification heuristic AND DD3 refusal message + routing table are present in the SKILL.md (inlined, not referenced) | **PASS** | DD2 dropped verbatim at `SKILL.md` L48-84 ("Diff classification (drop-in heuristic)" — REFACTOR signals, BEHAVIOUR-CHANGE signals, Ambiguity rule). DD3 at L153-189: routing table (L161-166) + verbatim refusal message (L168-186) + "always lists all four routes" note (L188-189). |
| A4 | Routing target skills actually exist | **PASS** | `grep '^name:'` under `.claude/skills/openup-artifacts/*/SKILL.md` resolves all four: `openup-create-use-case`, `openup-create-architecture-notebook`, `openup-create-iteration-plan`, `openup-create-task-spec`. Routing table targets all resolve. |

## B. Scenario dry-runs

Each scenario walks the SKILL.md instructions by hand against a synthetic diff and judges whether an agent
following the skill reaches the right verdict.

| # | Scenario | Result | Walkthrough vs skill instructions |
|---|---|---|---|
| S1 | REFACTOR — rename `foo()`→`compute_total()` with all call sites updated + a file move, no signature/logic change | **PASS** | Step 3 (Classify, L106-111 → heuristic L58-66): "Symbol **rename** with all call sites updated" and "**Move** a file/symbol … no signature change" are both REFACTOR signals; no behaviour signal fires → classify REFACTOR. Step 4 (L113-124): builds the changed file/symbol set (rename `foo`→`compute_total`, moved path) and flags a section **only if its prose names** one of those — "Sections that name nothing in the changed set are left untouched." Step 5 (L126-130): drafts the **minimal** old→new edit and "Never regenerate a whole document; never auto-write." Step 6 (L132-146): `last-synced` bump happens only on approval, in the same scribe batch as the edits. Matches plan Requirements 2-4 and Verification line 1. |
| S2 | BEHAVIOUR-CHANGE — add a new `if` branch + a new parameter to a public function | **PASS** | Heuristic L68-73: "added/removed/reordered parameters" = **Public API signature change**; "added or altered `if`/`switch`/loop conditions" = **Business-logic/conditional change** — two behaviour signals fire. Step 3 (L108-111): a BEHAVIOUR-CHANGE verdict "short-circuits the flow — **no** section detection, **no** edit proposal, **no** scribe call, **no** `last-synced` bump … Emit the refusal and STOP." Refusal block (L168-186) names the concrete signal/file-symbol and routes to the originating `/openup-create-*` skill; "Never offer a force/sync-anyway escape hatch" (L156-157). Matches plan Requirement 5, Safeguard "no false-positive silencing", and Verification line 2. |
| S3 | AMBIGUOUS/MIXED — diff mixing a rename hunk and a changed conditional | **PASS** | Ambiguity rule L82-84: "if a diff mixes refactor and behaviour hunks … classify the **whole run** as BEHAVIOUR-CHANGE and refuse. Do not partially sync a mixed diff." The changed conditional alone also independently fires the business-logic signal. Whole-run refusal (no partial sync), per design risk "Multi-artifact partial sync / atomicity" and Safeguard. Correctly blocking. |

## Defects

None. No structural or logic defects found; the developer must fix nothing.

## Observations (non-blocking, severity: trivial)

- **OB-1 (cosmetic, comment-wording drift).** DD1 specified the documenting comment as
  `last-synced: ""   # full git SHA of last code↔spec sync (set by /openup-sync-spec)`. The 3 developer-edited
  templates match this exactly. `task-spec.md` (pre-existing, *not* edited this task) reads
  `# git ref of last code↔spec sync` — "git ref" vs "full git SHA". Purely cosmetic comment text;
  no structural or behavioural impact. Optional alignment if a future edit touches task-spec.md.
- **OB-2 (informational).** The skill's `arguments.since` description says `"last commit" → HEAD~1..HEAD`,
  matching design Inputs §2. Not in the required check set; noted as consistent.

## Coverage vs plan ## Verification

- ✅ Synthetic refactor test (rename + move) → S1.
- ✅ Synthetic behaviour-change test, must refuse with clear message pointing at the right `/openup-create-*`
  skill → S2 (refusal wording + routing table verified against A3/A4).
- Plan's third item ("audit one real iteration's diff") is an operational sanity check requiring a live diff +
  approval loop; out of scope for prose-skill structural verification and left for first real use.

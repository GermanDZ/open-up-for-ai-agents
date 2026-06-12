# T-018 — Design Decisions (in-flight)

Decisions made while executing T-018. Keeps `plan.md` from going stale.

## DD1 — Single-source the mechanism; skills carry a compact pointer step
Rather than paste the full injection mechanism into each of the seven artifact
create skills, the mechanism (location, schema, artifact-type keys, wrappers,
precedence, consuming-skill list) lives once in `docs-eng-process/project-config.md`.
Each skill gets a uniform ~15-line "Load Project Config" step that points there and
names only **its own** artifact-type key. Keeps nine edits small and drift-resistant
(matches Norms: reference, don't duplicate).

## DD2 — Step is unnumbered, inserted before `### 1.`
The new step is headed `### Load Project Config (context + rules — do this first)`
and placed immediately after `## Process`, ahead of the existing `### 1.` step. Chosen
over inserting `### 0.` or renumbering every existing step across seven files —
non-invasive, and "do this first" makes ordering explicit without touching the rest.

## DD3 — `rules:` keyed by the `/openup-create-<type>` suffix
Artifact-type keys (`use-case`, `task-spec`, `architecture-notebook`, …) equal the
create-skill suffix, so a reader maps a rule block to its skill by name (resolves the
plan's keying ambiguity; recorded as a plan Assumption). The example yaml and the
mechanism doc's table both enumerate the seven.

## DD4 — Injection covers the seven *spec* artifacts, not workflow outputs
`create-pr`, `create-handoff`, `create-documentation` emit workflow outputs, not
project specs graded against a rubric, so they do **not** consume project rules
(listed under Structure → "Do not touch"). The seven that do are exactly those with a
work-product/rubric: vision, use-case, architecture-notebook, iteration-plan,
task-spec, test-plan, risk-list.

## DD5 — Additive precedence, no rubric edits, no schema
Precedence is `framework rubric → project rules → task-spec safeguards`: a project
rule may *add* a criterion but may not waive a framework one or a safeguard. No
`.claude/rubrics/*` file is touched (they stay framework-owned), and the YAML ships
unvalidated (no schema/linter) — both explicit no-go zones from the source plan.

## DD6 — This framework repo ships no live `docs/project-config.yaml`
The framework has no project-specific stack/domain to inject. Deliverables are the
example template + the `/openup-init` emitter; injection is exercised by a temporary
fixture at verification time (created, asserted, deleted — no tracked residue).

---

## Implementation-vs-Spec Verification (complete-task §1a)

Graded each `plan.md` requirement against the actual diff:

1. `project-config.example.yaml` exists, valid YAML, `context:` + `rules:` keyed by the seven types — ✅ (`yaml.safe_load` ok; keys ⊆ seven).
2. `project-config.md` documents location, keys, wrappers, precedence, consuming skills — ✅ (all present; precedence string + both wrappers grep-confirmed).
3. Seven artifact skills carry the Load Project Config step naming their own key — ✅ (all seven matched; per-key assertion OK for each).
4. Absence-safe / revert — ✅ (step says "if absent, skip"; fixture create→delete left no residue).
5. `/openup-init` emits a starter `docs/project-config.yaml` — ✅ (new "Project Config" sub-section under Generate Initial Documents).
6. `CLAUDE.md` documents precedence + points to the mechanism doc — ✅ (Quality section addition).

Scenario validator: `openup-spec-scenarios.py check` → exit 0 (6/6 requirements carry Given/When/Then).

**Result:** all requirements ✅ — no ❌, completion unblocked.

## Self-grade against task-spec-rubric.md
1 Front-matter ✅ · 2 Story INVEST ✅ · 3 Requirements testability ✅ · 4 Entities ✅ ·
5 Approach ✅ · 6 Structure scope-fit ✅ · 7 Operations ✅ · 8 Norms/Safeguards ✅ ·
9 Ambiguity (3 assumptions named) ✅ · 10 Behavior Delta (n/a — all Added, justified) ✅ ·
11 Scenario coverage (validator exit 0) ✅. **Result: satisfied.**

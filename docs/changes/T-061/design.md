# T-061 — Design & Verification Notes

## In-flight decisions

- **Seeded by a three-lane tier review** (haiku / sonnet / inherit subagents) of all 35
  template skills against Opus 4.8 / Sonnet 5 migration guidance, run 2026-07-02.
- **Scope hardened mid-iteration by owner**: R2 upgraded from "plan-feature is
  stack-agnostic" to "no skill names any language/framework/stack, even as example" —
  OpenUP is a generic development process. Spec updated first (fix-spec-first), then the
  sweep extended to shared-vision example tables, sync-spec's example path, and
  quick-task's example.
- **Kept at full strength deliberately**: complete-task BLOCKING tags, two-legal-exits,
  trunk guard, retro-cadence REFUSE gate, sync-spec refusal, fan-out worktree
  constraint — all guard destructive/irreversible actions or hard process gates.
- **Deferred (follow-up candidates, out of scope)**: scripting readiness's DAG/collision
  computation; splitting start-iteration and the four phase skills into mechanical +
  judgment halves; re-tiering the phase skills' check-status/next-steps activities.

## Step 1a — Requirements graded against the diff (2026-07-02)

- ✅ R1 — quick-task SKILL.md commit template no longer carries `Co-Authored-By: Claude
  Opus 4.6`; grep for `Claude Opus 4.`/`Claude Sonnet 4.` across skill bodies = 0 matches.
- ✅ R2 — plan-feature step 3 rewritten to detect language/stack from the project's own
  manifest/build files, stack-neutral category list, conditional `## i18n`, `{language}`
  fences; shared-vision/sync-spec/quick-task examples neutralized; stack grep
  (ruby|rails|postgres|serverless|microservice|gemfile…) = 0 matches.
- ✅ R3 — report-then-rank wording in 9 authoring skills + task-spec variant + shared SOP
  (`sops/self-critique.md` steps 1/4/5); grep for `genuine weakness`/`the weakest point`
  = 0 matches.
- ✅ R4 — MANDATORY grep = 0 across skills; softened: plan-feature §4, create-task-spec §2,
  explore §3 + "silence" line, start-iteration "has FAILED"→"stop and report".
  complete-task retains all 10 BLOCKING tags; fan-out worktree constraint untouched.
- ✅ R5 — log-run (callout is sole full statement; steps 2/4 point back), init (Gate
  awareness canonical; steps 2/3 pointers; `--no-git` row fixed), sync-spec (heuristic
  points to top note), next (context-model points to top rule), six create-* skills
  (Validate steps re-check canonical Success Criteria; missing items absorbed into SC),
  Process Summary removed from plan-feature/detail-use-case/shared-vision, readiness
  worked example now synthetic/dateless, quick-task time metrics deleted.
- ✅ R6 — retrospective frontmatter `model: sonnet`; `check-model-tiers.py --check` exit 0
  (11 haiku / 13 sonnet / 11 inherit); prose tiers updated (retrospectives moved to
  Authoring).
- ✅ R7 — `sync-templates-to-claude.sh` run; `check-claude-sync.sh` exit 0 (66 files);
  `check-skills-guide.py --write` regenerated skills-guide.md.

## Step 1b — Success-measure instrumentation

- ✅ instrumentation — the measure is the grep itself (stated in plan.md §Success
  Measures); executed at completion: match count for
  `Claude Opus 4.\|Claude Sonnet 4.\|genuine weakness\|the weakest point` over
  `docs-eng-process/.claude-templates/skills/` = **0** (was >10 at review time).
  Read-back: performed 2026-07-02 at completion (same session, as specified).

## Known pre-existing issue (out of this lane)

`python3 scripts/check-docs.py` reports 3 failures that are byte-identical on trunk
(verified against the main checkout before any T-061 edit): archived T-056 plan
`status: done` vs schema enum, T-060 design/iteration-plan duplicate-id, t-059
iteration plan `status: pending` vs enum. All three files are outside T-061's claimed
surface (write-fence would reject edits). Needs its own maintenance task.

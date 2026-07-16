# Exploration: cycle-engine orchestration economics — bugs and enhancement opportunities

**Started:** 2026-07-16
**Question:** Where does the harness-optional cycle engine (and the surrounding process) spend tool calls, tokens, and commits that better task contextualization or tooling could eliminate — and which fixes are worth delivering?

## Context

Owner-requested critical review of the new cycle engine, process mapping, and
tooling on `harness-optional`, focused on faster / more economic agent
orchestration. Evidence base:

- Engine code read end-to-end (`scripts/openup_agent/` — cycle, loop, tools,
  llm, plan_iteration, assess, tiers, stamping; `build-task-library.py`,
  `openup-process-map.py`, `task-library.yaml`, `process-map.yaml`).
- Forensic audit of `/tmp/openup-samples/my-product-2` (T-001→T-009 ShareShed
  run, 80 commits). `/tmp/openup-samples/my-product` holds **no results** —
  bootstrap only, no `.openup/`, no cycle ever ran there.
  `my-product-2-T-009` is an orphaned bootsnap cache, safe to delete.
- Transcript analytics over 18 Claude Code sessions (~3,100 turns, ~2.6M
  output tokens): my-product-2 orchestration + per-task worktrees, plus two
  large framework-repo sessions. Analysis script + per-session CSV were
  produced in session scratch; method: classify Bash calls by anchored script
  names/paths, count re-reads, sum `message.usage`.

Related: T-104→T-118 lean-authoring program (this exploration extends its
thesis), T-080 bench harness (the measurement instrument), gated T-107.

## Notes

### Measured baseline (harness flow, my-product-2 + framework sessions)

- **60% of Bash tool calls are process ceremony** (610/1,024); product
  verification (tests/app-run) ≈ 5%. Ceremony:product-code ≈ 14:1.
- Validator guess-and-check: 187 re-runs (`check-docs.py` 107,
  `openup-fence.py check` 51, `openup-spec-scenarios.py check` 29).
- "Where am I" polling: `git status` 211× + `git rev-parse` 106×.
- State round-trips: ~129 `openup-state.py`-family subprocess calls.
- Re-read files (context that should be pre-packed): `docs/roadmap.md` 8×,
  `vision.md` 3×, active `plan.md` 3×, `navigator.py` 3× per worktree.
- Commit traffic (my-product-2, all 80 classified): ~15% carry deliverable
  content; **26% of the entire history services the run log** (21 commits →
  55 net JSONL lines); a single doc deliverable costs 8 commits (1 product +
  7 ceremony), e.g. T-006.
- The run itself was **clean**: zero retry loops, zero gate-failure churn.
  The waste is fixed ceremony, not rework. Only two rework episodes, both
  self-logged: INDEX.md-not-in-fence-allowlist (T-003) and prose-roadmap
  parser mismatch (T-009).

### Contextualization gaps (driver sub-runs get paths, not content)

1. **Judgment boxes — weakest briefing.** `build_step_instruction`
   (cycle.py:374-393) inlines only the box's one-line body; plan.md/design.md
   are handed as paths although the engine already read plan.md to parse the
   boxes (cycle.py:1352). Every judgment box burns 2-4 read round-trips
   re-fetching engine-held text.
2. **Unresolvable KB display-name inputs.** `render_task_instruction`
   (plan_iteration.py:187-193) emits "Additional inputs to consider: Vision"
   — not a path. The library already knows Vision → `docs/product/vision.md`
   (another def's `output_path`); a name→path map can be compiled in
   `build-task-library.py`. T-118 proved the payoff (5 globs / 4 turns
   eliminated by naming one path).
3. **N spec lanes re-read the same vision** (`LANE_SPEC_CONTRACT`,
   plan_iteration.py:69-86). Engine should read once, inline into all N
   instructions.
4. **Assess grades without pre-packed evidence** (assess.py:45-46, 80-87):
   instance text is inlined but the "repo evidence" must be grepped for.
5. **`parse_boxes` drops continuation lines** of wrapped judgment boxes
   (cycle.py:234-235) — context lost before briefing starts.

### Engine round-trip economics

- **Gate over-running dominates deterministic cost**: `run_gates` after every
  Operations box (cycle.py:1404) + again at complete (cycle.py:838);
  `check-docs.py` rglobs all docs each time. 6-box lane = 13 full-doc scans.
- **Model tiers misassigned; MAIN never used**: everything resolves through
  `DEFAULT_STEP_TIER="authoring"`/MID (cycle.py:88, tier-map.yaml:28) while
  `openup-cycle.md:4` declares `tier: reasoning`. Assess grading and spec
  authoring are the reasoning-shaped steps.
- **Turn caps inverted**: task-def authoring gets 50 turns (cycle.py:1041),
  judgment boxes 10 (cycle.py:87).
- **loop.py never compacts history**: full message list re-POSTed each turn;
  a 400KB read rides along forever; no `max_tokens`; a transient endpoint
  error discards the whole sub-run (llm.py:54-67, exit 3, no retry).

### Confirmed bugs

- **B1** `grep` walks `.git`/binaries/vendor: default `path="."` rglobs the
  whole tree and text-decodes everything (tools.py:119-125).
- **B2** `exec` with escaping `cwd` crashes the driver: `_resolve` raises
  `ToolError` (tools.py:148) but dispatch catches only `TypeError`
  (tools.py:176-178) → uncaught, exit 1.
- **B3** Prose containing `git …`/backticked commands classified as a command
  box and exec'd (CMD_START_RE cycle.py:101, extract_command cycle.py:254-266)
  — risk grows now that specs are LLM-authored.
- **B4** Wrapped judgment-box bodies truncated to first line (cycle.py:234-235).
- **B5** Merge failure at completion strands the lane: folder archived +
  status `done` before merge; `unclosed_lanes` can't see it (cycle.py:862-870).
- **B6** `read_file` silently truncates at 400KB, no marker (tools.py:22,55).
- **B7** `exec` returns unbounded output — a failing gate dumps its full
  report into history permanently (tools.py:157).
- **B8** Fence allowlist omits `docs/INDEX.md` (caused T-003 revert-rework).
- **B9** `openup-claims.py roadmap_status()` requires table format; prose
  `## T-NNN:` roadmaps break `session begin` preflight (T-009 hand-replicated
  the session flow around it).

### Enhancement opportunities (ranked by measured leverage)

- **E1 Inline engine-held context into sub-run briefings** — plan.md
  (or its Requirements/Safeguards sections), design.md, resumable-input
  content, vision for spec lanes, resolved input paths (name→path map from
  the task library; inline small files with a size cap + truncation marker).
  Cheapest change, largest turn reduction; extends T-118's proven mechanism.
- **E2 Dirty-aware gating** — skip `check-docs` when `git status --porcelain
  -- docs` shows no `.md` delta since last pass; drop the duplicate
  completion re-run; add `--changed-only` to `check-docs.py` (also serves the
  harness flow's 187 re-runs).
- **E3 Tool surface v2** — `read_files(paths[])` batch read; `apply_patch`
  (unified diff, multi-file); `grep` hygiene (ignore set, size cap, glob
  filter, `context=N`, `count_only` — the grep→sed pair appeared ~157× in
  transcripts); truncation markers everywhere; `repo_status()` or a
  deterministic one-line tree-state suffix on tool results; `validate()`
  structured gate runner.
- **E4 Tier + cap corrections** — assess/spec → `reasoning`; unify turn caps
  (~10-12); align engine defaults with `openup-cycle.md`'s declaration.
- **E5 loop.py history hygiene** — evict stale tool results beyond N turns,
  set `max_tokens`, one retry with backoff on transient endpoint errors.
- **E6 Ceremony commit batching (harness flow)** — one `chore(process)`
  commit per lane at completion; run-log folding only in `_sweep_run_logs`
  (cycle.py:1097-1121); content-hash short-circuit in
  `sync-templates-to-claude.sh` / `render-skills-mirror.py` (27× + 26×
  observed per-lane re-runs).

### Worth keeping (do not optimize away)

REASONS-canvas task specs (archived T-009 plan.md is the gold standard —
executor gets scope, Given/When/Then ACs, Add/Do-not-touch structure, ticked
Operations, declared touches); the human milestone gate (caught a
mechanically-"met" `functionality_complete` with zero app code → NO-GO);
value-ordered roadmap with Depends-on edges; the
fresh-bounded-sub-run-per-judgment-point design itself.

## Options Considered

- **Option A — inline-context first (E1), then re-measure before any tool work.**
  Pro: engine already holds the text; zero new surface; T-118 precedent.
  Con: bigger prompts per sub-run (mitigated by size caps; net tokens still
  drop because history stops accumulating re-reads).
- **Option B — tool surface v2 first (E3).** Pro: helps every future sub-run
  regardless of briefing. Con: driver-side evidence is thin until the T-107
  live batch runs; inlining may erase most of the reads the new tools would
  batch — risk of building unneeded surface.
- **Option C — gates first (E2).** Pro: dominant deterministic cost, benefits
  both flows, independent of the gated T-107. Con: doesn't touch LLM-side
  round-trips at all.

## Open Questions

- Does inlining plan.md wholesale blow the context of `local-mid` models, or
  do we need per-section extraction? (Decide with bench data.)
- Ceremony commit batching changes audit granularity — is per-event commit
  traceability a requirement or a habit? (Owner decision.)
- Should `reasoning`-tier routing wait for live evidence that MID quality is
  insufficient? Zero rework was observed — but on the harness flow with
  Sonnet, not on `local-mid`.
- B9: enforce table-format roadmaps at authoring (the
  `author-initial-roadmap` def already pins it) or teach the parser prose?

### Product-manager challenge pass

- **Pushback 1 — tool surface v2 (E3) is partially speculative.** The 60%
  ceremony share and the grep→sed count come from *harness* sessions, not the
  driver; only one live driver observation exists (the T-118 5-glob episode).
  Building six new tools before the T-107 live batch measures the driver is
  premature scope. **Disposition: accepted** — E3 is sequenced *after* E1 +
  a bench re-measure; only the two tool *bugs* (B1, B2) go early because they
  are correctness, not capability.
- **Pushback 2 — tier promotion (E4→reasoning) raises cost per call**, which
  cuts against the stated goal, and observed quality at MID showed zero
  rework. **Disposition: accepted with narrowing** — promote only assess
  grading (one sub-run per iteration, judgment-dense, cheap in aggregate);
  hold spec-authoring promotion until a live batch shows MID spec quality
  failing gates.
- **Pushback 3 — commit batching (E6) has an unpriced cost**: the audit trail
  is a stakeholder-facing property (the run log *is* the evidence trail this
  framework sells). **Disposition: accepted** — E6 is gated on an explicit
  owner decision (open question above), not bundled into the efficiency lane.
- **Complement — the review under-used the measurement instrument we already
  shipped.** T-080's `openup-agent-bench.py` + `OPENUP_AGENT_USAGE_LOG` make
  every claim here falsifiable per cycle. Fold in: every enhancement lands
  with a before/after bench delta in its spec. **Disposition: accepted** —
  added to the iteration scope below.
- **Refine — falsifiable success measure for E1** (was: "reduce tool usage"):
  *median turns per authoring/judgment sub-run drops from the current
  observed ~4-10 to ≤3, and no sub-run re-reads a file the engine inlined*,
  measured by the bench on the same scenario before/after. **Disposition:
  accepted** — this is the acceptance criterion for the first roadmap entry.

## Where this goes next

→ **iteration** — promote **"E1: inline engine-held context into sub-run
briefings (+ name→path input map)"** as the next roadmap entry (scope: cycle.py
`build_step_instruction`, plan_iteration.py `render_task_instruction` /
`LANE_SPEC_CONTRACT`, assess.py evidence bundle, `build-task-library.py`
name→path map; acceptance = the bench-measured ≤3-turn median above), with the
bug lane (B1-B9) and E2 gating as the follow-on entries in value order.

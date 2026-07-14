# T-112: `/openup-cycle` — lower-ceremony deterministic-first entry point

**Phase**: construction
**Status**: pending
**Goal**: A new Claude Code skill that executes an already-claimed lane's Operations boxes with cycle.py's script-vs-judgment discipline — zero self-brief overhead on mechanical steps — while `/openup-next` stays untouched as the full-precedence entry point.
**Priority**: medium

---

## Context

The headless reference driver (`scripts/openup_agent/cycle.py`, T-089→T-091) proved that most of a delivery cycle is deterministic: `resolve` → claim → per-Operations-box executor → gates → completion, composing the existing scripts, with the LLM dropping in only at genuine judgment boxes. `/openup-next` (`docs-eng-process/procedures/openup-next.md`) is the harness-side (Claude Code) equivalent, and it already consumes the same `openup-board.py resolve` decision `cycle.py` does — the two aren't rival philosophies, they're two substrates (Python subprocess orchestration vs. a Claude Code agent) implementing the same deterministic core.

But `/openup-next`'s prose treats every Operations box uniformly — "work the lane's Operations steps in order," self-briefing (reading the role file + Ring 1 + Ring 2 docs) as part of its per-cycle step 3, before working *any* box, script or prose. `cycle.py` never pays that cost for a box that's just `` `python3 scripts/sync-status.py` `` — it classifies the box (`classify_box`/`extract_command` in `cycle.py:254-279`) and runs script-steps as a bare subprocess call, reserving the LLM (there, a fresh `loop.run()` sub-run; in Claude Code, the current agent's own judgment) for boxes with no extractable command. Lanes with a high proportion of mechanical Operations steps (script-driven scaffolding, gate runs, sync calls) pay full self-brief ceremony on every one of them today.

`/openup-cycle` ports that classification discipline into Claude Code, scoped tightly: it only handles the `pick`/`resume` decision paths (claim an already-specced lane, execute its Operations boxes, gate before each tick, exit through the two legal exits) — the common case in a healthy backlog. Every other `resolve` path (`plan-iteration`, `assess-iteration`, `milestone-review`, a stuck/noop needing replenishment) needs real planning or grading judgment that `/openup-next` already implements at full parity (T-078/T-091); `/openup-cycle` explicitly routes those to `/openup-next` rather than re-deriving them — the same fallback `cycle.py` itself prints today (`cycle.py:1284-1285`: *"Use the `next` procedure (or the Claude Code skills) for this path meanwhile"*).

`/openup-next` is preserved byte-unchanged (explicit ask). This is an additional entry point, not a replacement.

---

## Current State

### `cycle.py`'s box classification (`scripts/openup_agent/cycle.py:254-279`)

```python
def extract_command(body):
    """The script command a box carries, or None (⇒ judgment step)."""
    for span in BACKTICK_RE.findall(body):
        span = span.strip()
        if span.startswith(("python3 ", "git ")):
            return span
        if re.match(r"^scripts/[\w./-]+\.py(\s|$)", span):
            return "python3 " + span
    m = CMD_START_RE.search(body)
    if m:
        return m.group(0).rstrip(" .`")
    return None


def classify_box(box):
    """Return ('script', command) or ('judgment', None) for one parsed box."""
    if box["marker"] == "judgment":
        return "judgment", None
    cmd = extract_command(box["body"])
    if box["marker"] == "auto":
        if cmd is None:
            raise CycleError("(auto) box has no extractable command: %s" % box["body"])
        return "script", cmd
    if cmd is not None:
        return "script", cmd
    return "judgment", None
```

### `cycle.py`'s claim + gate-before-tick + completion (`scripts/openup_agent/cycle.py:330-368`, `1364-1382`, `815-872`)

Claim (`acquire`) checks out an in-place task branch and runs `openup-session.py begin` with the lane's task/track/phase, then `openup-state.py set-gate plan_persisted <plan path>`. The box loop (`_run_cycle_inner`) runs **gates before every tick** — `loop.run_gates` (`scripts/openup_agent/loop.py:31-34,161-183`: `openup-fence.py check` then `check-docs.py`, with fence exit 3 treated as *inapplicable* not failing) — so a failure leaves the box unticked for a clean retry, rather than compounding across several boxes before the lane's next `/openup-complete-task` gate catches it. `complete()` then mirrors `/openup-complete-task`'s per-track ceremony as direct script calls.

### `/openup-next`'s current per-box handling (`docs-eng-process/procedures/openup-next.md:191-215`)

```markdown
### 3. Self-brief and assume the lane's hat

Do **not** ask for a briefing — self-brief from the repo (T-016). Read the
`## On Start, Read` block of the role file named by `lane.hat` (default
`developer`) and load exactly its ring-scoped docs: status, the one change
folder `docs/changes/<task>/`, and that role's guideline docs. ...

### 4. Execute one cycle under the track's ceremony

Work the lane's Operations steps in order, under the track recorded in state
...

### 5. Persist progress — tick the boxes

As each Operations step lands, tick it in `plan.md`: `- [ ]` → `- [x]`. ...
```

No box-kind distinction, no per-box gate — gating happens once, inside `/openup-complete-task`'s step 3a (`check-docs.py`, BLOCKING per `CLAUDE.openup.md`) and at push (`.githooks/pre-push` → `openup-fence.py`).

### Procedure frontmatter contract (`docs-eng-process/procedure-frontmatter.md:14-33`)

```yaml
---
name: openup-next
description: Run ONE OpenUP …
tier: reasoning
capabilities:
  required: [read_write_files, exec]
  optional: [subagents]
arguments: [...]
fit: {great: [...], ok: [...], poor: [...]}
---
```

`tier` is a name resolved via `docs-eng-process/tier-map.yaml`, never a raw model string (owner decision 6).

---

## Proposed Design

### 1. New procedure: `docs-eng-process/procedures/openup-cycle.md`

```markdown
---
name: openup-cycle
description: Execute an already-claimed lane's Operations boxes with script/judgment classification — script steps run directly with zero self-brief, judgment steps self-brief and execute. Handles only pick/resume; every other resolve path routes to /openup-next.
tier: reasoning
capabilities: {required: [read_write_files, exec], optional: []}
fit:
  great: [advancing a lane whose Operations boxes are mostly mechanical script calls, an outer loop repeating pure delivery cycles once planning is done, minimizing self-brief overhead on gate/sync/scaffold-heavy lanes]
  ok: [a lane with a mix of script and judgment boxes]
  poor: [no active lane and nothing pickable (needs plan-iteration), an iteration needing assess-iteration or milestone-review, a stuck backlog needing replenishment — use /openup-next for all of these]
arguments:
  - name: task_id
    description: "Optional. Force a specific lane instead of the board's top pick (must still be pickable)."
    required: false
---
```

Body (condensed — full body is the deliverable):

1. **Resolve.** `python3 scripts/openup-board.py resolve` — identical single call to `/openup-next` §0–1 and `cycle.py:resolve_decision`.
2. **Route.** `path == "pick"` or `"resume"` → continue. Any other path → print `cycle.py`'s own fallback framing ("this decision needs planning/grading judgment `/openup-cycle` doesn't carry — run `/openup-next`") naming `.reason`, emit `OPENUP-NEXT: DONE — routed to /openup-next (<path>)`, stop. No re-derivation of plan-iteration/assess/milestone logic — `/openup-next` already has it at parity.
3. **Claim.** `resume` with `resumable_input` set (an answered input-request resumed this lane) → **fold the answers into the spec first**, identical to `/openup-next` §0's resume/resumable_input sub-case: read the named request, re-run `/openup-create-task-spec task_id: <task>` so the answers land in `docs/changes/<task>/plan.md` through the rubric, drop the `awaiting-input:` frontmatter line, archive the request. This is inherently judgment-shaped (spec authoring) — no self-brief-skip optimization applies. (`cycle.py` takes a different, driver-only shortcut here — it hands the answered request path straight into the next judgment box's instruction rather than folding it into the spec — but that bypasses fix-spec-first, which is a hard rule for the Claude Code path; `/openup-cycle` follows `/openup-next`'s behavior here, not `cycle.py`'s.) `resume` with no `resumable_input` → lease already exists, skip straight to step 4. `pick` → delegate to `/openup-start-iteration task_id: <lane.task> track: <lane.track or auto>` **unchanged** (same as `/openup-next` step 2) — collision preflight, worktree/lease, remote duplicate-start check stay single-sourced; `/openup-cycle` does not reimplement them (same "hand it to the existing machinery" rule `/openup-next` follows).
4. **Box loop.** Parse `docs/changes/<task>/plan.md`'s Operations section (same shape `cycle.py:parse_boxes` reads: `- [ ]`/`- [x]`, `(role)`/`(auto)`/`(judgment)` prefix). For the first unchecked box, classify it using the **same rule** `cycle.py:extract_command`/`classify_box` encode, spelled out in the procedure body so a Claude Code agent applies it without importing Python:
   - An explicit `(judgment)` marker → judgment step, regardless of content.
   - Otherwise: a backtick span starting with `python3 ` or `git `, or a bare `` `scripts/<name>.py ...` `` span (implicitly `python3`-prefixed), or (failing that) the first `python3 ...`/`git ...` token run to end of line → **script step**: run it directly via Bash. No self-brief, no role-hat framing — just the command.
   - An explicit `(auto)` marker with no extractable command is an authoring error in the spec (mirror `cycle.py`'s `CycleError` there) — flag it and stop rather than guessing.
   - No extractable command and no `(auto)` marker → **judgment step**: self-brief (role file's `## On Start, Read` block, per `lane.hat`/box's `(role)` tag, default `developer`) — but only now, only for this box — then do the work, persisting output to files (identical execution model to `/openup-next` step 3–4, just deferred until a box actually needs it).
5. **Gate before tick.** After executing either kind of box: `python3 scripts/openup-fence.py check` (exit 3 = inapplicable, skip) then `python3 scripts/check-docs.py`. Either failing (non-inapplicable) → stop, box stays unticked, report the gate output — do not tick and do not continue to the next box. This is the one genuine behavior addition over `/openup-next` (which only gates at completion/push), lifted directly from `cycle.py:1364-1382`.
6. **Tick.** Flip the exact `- [ ]` → `- [x]` line (the sanctioned direct plan.md edit, unchanged rule). Loop to step 4 while boxes remain.
7. **Exit.** All boxes ticked → `/openup-complete-task task_id: <task>` — **unchanged, delegated**, same as `/openup-next`. `/openup-cycle` never inlines completion ceremony itself (that would be the third exit path the project's Critical Rules explicitly forbid). A mid-lane stop (gate failure, or a judgment box that can't finish this session) → `/openup-create-handoff task_id: <task>`.

Sentinel line: same vocabulary as `/openup-next` (`OPENUP-NEXT: ADVANCED — <task>` / `OPENUP-NEXT: DONE — <reason>`), so an outer loop (`openup-loop.sh`, `/loop`) can drive either skill interchangeably without new stop-rule logic.

### 2. Regenerate the mirror + guide

```bash
python3 scripts/render-skills-mirror.py --write   # docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md
scripts/sync-templates-to-claude.sh                # .claude/skills/openup-cycle/SKILL.md (gitignored, local)
python3 scripts/check-skills-guide.py --write      # docs-eng-process/skills-guide.md gains the entry
python3 scripts/check-model-tiers.py               # confirms tier: reasoning → model: inherit is correct
```

### 3. `/openup-next` — untouched

No edit to `docs-eng-process/procedures/openup-next.md`. This is the explicit ask and is verified as an acceptance criterion (diff must be empty on that file).

---

## Acceptance Criteria

- [ ] `docs-eng-process/procedures/openup-cycle.md` exists with valid neutral frontmatter (`name`, `description`, `tier: reasoning`, `capabilities`, `fit` routing every non-pick/resume path to `/openup-next` by name) per `docs-eng-process/procedure-frontmatter.md`.
- [ ] The body's box-classification rule is a **verbatim-equivalent restatement** of `cycle.py:extract_command`/`classify_box` (verified by running `classify_box` from `scripts/openup_agent/cycle.py` against the Operations boxes of ≥5 archived `docs/changes/archive/T-*/plan.md` files and confirming the procedure's written rule would classify each box identically — no silent divergence from the proven logic).
- [ ] Claim (`pick`) delegates to `/openup-start-iteration` unchanged; completion delegates to `/openup-complete-task` or `/openup-create-handoff` unchanged — `/openup-cycle` introduces no third exit and no reimplementation of collision/lease/rubric logic.
- [ ] A `resume` with `resumable_input` set folds the answer into the spec via `/openup-create-task-spec` (fix-spec-first) before the box loop starts, exactly as `/openup-next` does — `/openup-cycle` does not shortcut this the way `cycle.py` does.
- [ ] Gate-before-tick (fence + check-docs, fence-exit-3-as-skip) runs after every box, script or judgment, before that box's `- [x]` flip.
- [ ] `docs-eng-process/procedures/openup-next.md` is byte-identical to its pre-T-112 content (`git diff` empty on that path).
- [ ] `render-skills-mirror.py --check`, `check-skills-guide.py --check`, `check-model-tiers.py`, and `check-docs.py` all pass with `openup-cycle` present.
- [ ] `.claude/skills/openup-cycle/SKILL.md` exists after `sync-templates-to-claude.sh` and is discoverable as `/openup-cycle`.
- [ ] Manual dry run: on a lane with at least one script-shaped box (e.g. a `` `python3 scripts/sync-status.py` `` step) and one prose/judgment box, `/openup-cycle` executes the script box with no self-brief narration and the judgment box with self-brief narration, gates before each tick, and completes through `/openup-complete-task`.

---

## Success Measure

We expect lanes whose Operations boxes are majority script-shaped (the common case for maintenance/quick-track work per the existing roadmap history — T-062, T-093, T-110, T-111 are all script-heavy) to complete under `/openup-cycle` with visibly less self-brief narration and fewer full Ring-1/Ring-2 doc reads than the same shape of lane run under `/openup-next`, read back informally after the first 5 real `/openup-cycle` invocations in this repo's own delivery loop (compare `docs/agent-logs/` run-log entries for box-count vs. self-brief-read-count between the two skills). This is a within-repo dogfooding measure, not an external metric — the repo's own delivery loop is the only consumer of its own skills.

---

## Testing Strategy

- **Classification fidelity**: script-check `cycle.py`'s `classify_box`/`extract_command` against a sample of real archived plans' Operations boxes; the procedure's written rule must produce the identical script/judgment split (see Acceptance Criteria).
- **Gate contract**: verified via `render-skills-mirror.py --check` / `check-skills-guide.py --check` / `check-model-tiers.py` / `check-docs.py` (no test suite changes — this task ships no `scripts/*.py` code, only a procedure doc + its generated mirrors).
- **Manual dry run**: one real lane worked end-to-end through `/openup-cycle`, as described in Acceptance Criteria.
- **No-regression check**: `git diff -- docs-eng-process/procedures/openup-next.md` must be empty.

---

## Dependencies

- None. Builds conceptually on the completed deterministic-cycle-engine program (T-089→T-091, T-100→T-103) but has no code dependency on it — it reads the same scripts those tasks already ship.

---

## Key Files

| File | Change |
|------|--------|
| `docs-eng-process/procedures/openup-cycle.md` | New procedure — the single editable source |
| `docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md` | Generated mirror (`render-skills-mirror.py --write`) — never hand-edited |
| `.claude/skills/openup-cycle/SKILL.md` | Generated local copy (`sync-templates-to-claude.sh`, gitignored) |
| `docs-eng-process/skills-guide.md` | Auto-regenerated to list `openup-cycle` |
| `docs-eng-process/procedures/openup-next.md` | **Unchanged** — verified, not edited |

---

## Out of Scope

- Any change to `/openup-next` itself, including adding a "See Also" cross-link to `/openup-cycle` — the explicit ask was to preserve it untouched; a future task can revisit cross-linking once `/openup-cycle` has live usage to point to.
- Handling `plan-iteration` / `assess-iteration` / `milestone-review` / consent-gated replenishment in `/openup-cycle` — these stay `/openup-next`'s job; duplicating them here would re-fork logic T-078/T-090/T-091/T-094 already converged.
- A "describe the next deterministic action without executing it" mode on `cycle.py` itself (would let `/openup-cycle` call out to the headless driver for its *classification* logic instead of restating it in prose) — real idea, but touches the headless driver's CLI surface and is a separate task if the duplication in Acceptance Criteria's fidelity check proves painful to maintain.
- A `UserPromptSubmit`/`SessionStart` hook that injects `resolve` output as ambient context — discussed as a complementary idea, not part of this task.

---

## Open Questions

1. Should `/openup-cycle`'s `fit: poor` list explicitly name `/openup-next` by slash-command, or just describe the situation? **Assumed**: name it explicitly (`"use /openup-next for ..."`) — vetoable at review; the whole point is a legible handoff between the two skills, not a guessing game.
2. Should the classification-fidelity acceptance check be a one-time manual verification (this task) or a small hermetic test script comparable to `spec-scenarios`? **Assumed**: one-time manual verification for this task (no `scripts/*.py` changes ship here, so there's no natural home for a new automated check yet) — vetoable; if `/openup-cycle` sees real use and the classification rule drifts from `cycle.py`'s, that's the trigger to build the shared-source idea noted in Out of Scope.

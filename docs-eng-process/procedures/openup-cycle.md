---
name: openup-cycle
description: Execute an already-claimed lane's Operations boxes with script/judgment classification — script steps run directly with zero self-brief, judgment steps self-brief and execute. Handles only pick/resume; every other resolve path routes to /openup-next.
tier: reasoning
capabilities: {required: [read_write_files, exec], optional: []}
fit:
  great: [advancing a lane whose Operations boxes are mostly mechanical script calls, an outer loop repeating pure delivery cycles once planning is done, minimizing self-brief overhead on gate/sync/scaffold-heavy lanes]
  ok: [a lane with a mix of script and judgment boxes]
  poor: [no active lane and nothing pickable — use /openup-next (needs plan-iteration), an iteration needing assess-iteration or milestone-review — use /openup-next, a stuck backlog needing consent-gated replenishment — use /openup-next]
arguments:
  - name: task_id
    description: "Optional. Force a specific lane instead of the board's top pick (must still be pickable). Omit to take the top READY collision-free lane."
    required: false
---

# Cycle (deterministic-first pick/resume entry point)

**A leaner sibling of `/openup-next`**, not a replacement. It owns exactly the
two most common `resolve()` paths — `pick` and `resume` — and classifies each
Operations box the same way the headless reference engine
(`scripts/openup_agent/cycle.py`) does: a box that carries an extractable
script command runs directly, with **zero self-brief**; only a box with no
extractable command pays the role-file/Ring-1/Ring-2 read. Every other
`resolve()` path (planning, assessment, a milestone gate, a stuck backlog) is
handed to `/openup-next`, which already implements it at full precedence
parity — this skill does not re-derive that logic.

> `/openup-next` stays exactly as it is. This is an additional entry point for
> the common case, not a change to the comprehensive one.

## Success Criteria

After this skill completes, ALL of these must be true:
- [ ] `openup-board.py resolve` was called once. If `.path` is not `pick` or
      `resume`, the cycle routed to `/openup-next` and stopped — it did not
      attempt to plan, assess, or replenish.
- [ ] A `resume` carrying `resumable_input` folded the answer into the spec via
      `/openup-create-task-spec` (fix-spec-first) before any box ran.
- [ ] Every Operations box that ran was gated (fence + check-docs) before its
      checkbox was ticked; a gate failure left the box unticked and stopped the
      cycle.
- [ ] The cycle exited through `/openup-complete-task` or
      `/openup-create-handoff` — never a raw commit, never a third path.

## Process

### 1. Resolve

```bash
python3 scripts/openup-board.py resolve
```

One read-only call, identical to `/openup-next` §0–1 and to `cycle.py`'s
`resolve_decision`. It returns `{path, lane, resumable_input, active_iteration,
phase, cycle, legacy_path, reason}`.

### 2. Route

`path == "pick"` or `path == "resume"` → continue to step 3.

Anything else (`plan-iteration`, `assess-iteration`, `milestone-review`,
`noop`) → this decision needs planning or grading judgment this skill doesn't
carry. Do all three of the following, **in order, in the same turn, with
nothing else in between**:

1. Print the handoff explanation, naming the `reason`:

   > This cycle needs `/openup-next` — `resolve()` returned `<path>` (`<reason>`),
   > which `/openup-cycle` doesn't implement. Run `/openup-next` to handle it.

2. Print this **exact** line, verbatim, substituting `<path>`, as the literal
   last line of output:

   ```
   OPENUP-NEXT: DONE — routed to /openup-next (<path>)
   ```

   This is not optional narration — it is the machine-readable stop signal
   every other OpenUP skill's outer-loop contract depends on. Printing only
   the prose explanation above and skipping this line is a spec violation,
   not a harmless shortcut.

3. **End the session now.** Do not invoke `/openup-next` yourself in this
   turn, even though you now know it's the right next step — that is what the
   sentinel is *for*: the outer loop (`/loop`, `openup-loop.sh`, cron, or the
   human reading your output) re-invokes with `/openup-next` next. The one
   exception: the user is present interactively and explicitly asks you to
   continue into `/openup-next` right now — chaining only on an explicit,
   in-the-moment request, never by default. Do not attempt to plan, assess, or
   replenish here either way — `/openup-next` already has that logic at full
   parity; re-deriving it here would fork it.

### 3. Claim

- **`resume` with `resumable_input` set** — a human answered a question that
  suspended this lane. Fold the answer into the spec first (fix-spec-first),
  exactly like `/openup-next` §0: read the named request, re-run
  `/openup-create-task-spec task_id: <task>` so the answer lands in
  `docs/changes/<task>/plan.md` through the rubric, remove the
  `awaiting-input:` frontmatter line, and archive the request (`status:
  processed` → `docs/input-requests/archive/`). This is inherently
  judgment-shaped work — no self-brief-skip optimization applies to it. (Note:
  `cycle.py` takes a different, driver-only shortcut here — it hands the
  answered request straight into the next judgment box's instruction instead
  of folding it into the spec. That bypasses fix-spec-first, which is a hard
  rule for the Claude Code path, so `/openup-cycle` follows `/openup-next`'s
  behavior, not `cycle.py`'s.) Then continue to step 4.
- **`resume` with no `resumable_input`** — the lane is already claimed and
  mid-work. Skip straight to step 4.
- **`pick`** — delegate to the existing machinery unchanged, exactly like
  `/openup-next` §2:
  ```
  /openup-start-iteration task_id: <lane.task> track: <lane.track or auto>
  ```
  Collision preflight, worktree/lease, and the remote duplicate-start check
  stay single-sourced there — this skill does not reimplement them.

### 4. The box loop

Read the Operations section of `docs/changes/<task>/plan.md` (same shape
`/openup-next` and `cycle.py` both read: `- [ ]`/`- [x]` lines, an optional
leading `(role)`/`(auto)`/`(judgment)` tag). Repeat until every box is checked:

1. Take the first unchecked box.
2. **Classify it** — the same rule `cycle.py`'s `classify_box`/`extract_command`
   encode (`scripts/openup_agent/cycle.py:254-279`):
   - An explicit `(judgment)` tag → judgment step, regardless of content.
   - Otherwise, a **script step** if the box's body contains: a backtick span
     starting with `python3 ` or `git `; or a bare `` `scripts/<name>.py ...` ``
     backtick span (treat it as `python3`-prefixed); or, failing either, the
     first `python3 ...` / `git ...` token run to the end of the line. An
     explicit `(auto)` tag with **no** extractable command is a spec-authoring
     error — stop and flag it rather than guessing what command was meant.
   - Otherwise → **judgment step**.
3. **Execute it:**
   - *Script step* → run the extracted command directly (Bash/`exec`). No
     role-file read, no Ring-1/Ring-2 read, no self-brief narration — just the
     command.
   - *Judgment step* → **now** self-brief: read the `## On Start, Read` block
     of the role file named by the box's `(role)` tag (default `developer`),
     load its ring-scoped docs (status, the one change folder, that role's
     guideline docs), then do the work and persist the output to files.
4. **Gate before tick** — after either kind of step:
   ```bash
   python3 scripts/openup-fence.py check   # exit 3 = inapplicable, treat as skip
   python3 scripts/check-docs.py
   ```
   If either gate fails with a non-skip exit code, **stop** — leave the box's
   `- [ ]` line unticked and report the gate output. Do not attempt the next
   box; a resumed cycle will retry this one. (This is the one behavior this
   skill adds beyond `/openup-next`, which only gates at completion/push —
   lifted directly from `cycle.py`'s "gates before the tick" ordering, so a
   failure is caught before it compounds across several boxes.)
5. Gates clean → tick the box (`- [ ]` → `- [x]`, the sanctioned direct
   `plan.md` edit) and go to step 1.

### 5. Exit — the same two legal exits, and only these two

- All Operations boxes ticked → `/openup-complete-task task_id: <task>`.
- A gate failed, or a judgment box can't finish this session → `/openup-create-handoff task_id: <task>`.

Never a raw commit; never any third path. This skill delegates completion
ceremony rather than inlining it — the collision/lease/rubric machinery those
skills own stays single-sourced there.

## Output

A compact summary (≤6 bullets): which path `resolve()` returned and whether it
routed to `/openup-next`; the lane and hat (if worked); how many boxes ran as
script steps vs. judgment steps; which boxes are now ticked; which legal exit
was taken.

### Sentinel line (machine-readable, always last)

Same vocabulary as `/openup-next`, so an outer loop can drive either skill
interchangeably without new stop-rule logic:

```
OPENUP-NEXT: ADVANCED — <task-id>
OPENUP-NEXT: DONE — <reason>
```

`DONE — routed to /openup-next (<path>)` is this skill's own addition to the
reason vocabulary — it tells an outer loop the *next* invocation should call
`/openup-next`, not retry `/openup-cycle`.

## See Also

- [openup-next](../next/SKILL.md) — the full-precedence sequential continue-loop; handles every `resolve()` path this skill routes away from.
- [openup-start-iteration](../start-iteration/SKILL.md) — the claim/worktree/state machinery the `pick` path delegates to.
- [openup-complete-task](../complete-task/SKILL.md) — legal exit #1.
- [openup-create-handoff](../create-handoff/SKILL.md) — legal exit #2.
- [openup-create-task-spec](../create-task-spec/SKILL.md) — how a `resume` with `resumable_input` folds its answer into the spec.
- `scripts/openup_agent/cycle.py` — the headless reference engine this skill's box-classification and gate-before-tick discipline are ported from (`extract_command`/`classify_box` at lines 254-279; `run_gates` in `scripts/openup_agent/loop.py:161-183`).

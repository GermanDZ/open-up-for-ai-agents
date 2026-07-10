# Exploration: validate-commit rejects the very tag it tells you to add

**Started:** 2026-07-10
**Question:** Why can a `/openup-quick-task` lane become uncommittable without `[openup-skip]`, and what is the smallest correct fix?

## Context

Hit live this session while removing a mis-filed plan via `/openup-quick-task`.
The quick task initialized state with `task_id = quick-remove-approve-plan`
(a non-numeric id). Every attempt to commit was blocked by the
`validate-commit.py` PreToolUse hook with:

```
❌ Missing required task tag.
  ... Append [quick-remove-approve-plan]:
    docs: remove ... [quick-remove-approve-plan]
```

But appending exactly that tag was *also* rejected. The only way through was
`[openup-skip]` (audited in `.claude/memory/bypass-log.md`) — used twice.

## Notes

The defect is a **contradiction between the hook's error message and its own
check**, not merely "quick-task ids aren't numeric":

- `.claude/scripts/hooks/validate-commit.py:63`
  `TASK_TAG_RE = re.compile(r"\[T-\d+\]", re.IGNORECASE)` — only matches a
  numeric `[T-NNN]` tag.
- Line 185–186: when an iteration is active, the subject must match `TASK_TAG_RE`.
- Line 191–192: the failure message instructs `Append [{task_id}]` where
  `{task_id}` is the *actual* active id (here `quick-remove-approve-plan`).

So the hook interpolates the real active id into its suggestion, then validates
against a hardcoded `T-\d+` pattern that the suggestion can't match. **The
printed remedy is unsatisfiable** whenever `task_id` ≠ `T-<digits>`.

Who produces non-numeric ids: `.claude/skills/openup-quick-task/SKILL.md:69`
`--task-id "{task_id or generated id}"` — the quick-task entry point has no
requirement that the id be `T-NNN`, and I passed a descriptive slug. `T-031`'s
`openup-claims.py reserve-id` (which *does* mint `T-NNN`) is wired into
`create-task-spec` / `plan-feature`, **not** into quick-task.

Scope of blast radius: the live hook is byte-identical to its template
(`docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py`,
verified `LIVE==TEMPLATE`), so any consuming project inherits the same trap the
moment a quick task (or any hand-run `openup-state.py init`) sets a non-numeric
id. `check-iteration.py` only references `T-XXX` in *guidance* text — it is not a
second enforcement of the numeric shape, so the fix is localized to
`validate-commit.py`.

Why it stayed latent: almost all delivery flows go through `create-task-spec` /
`plan-feature`, which allocate `T-NNN`. Quick-task is the one sanctioned path
that both (a) sets an active `task_id` and (b) doesn't force it numeric — so it's
the only lane that trips the contradiction, and only when the operator supplies a
descriptive id.

## Options Considered

- **Option A — validate against the *active* `task_id`, not a hardcoded pattern.**
  Keep `TASK_TAG_RE` as the fallback shape, but when `state_task_id()` returns an
  id, require the literal `[{task_id}]` (regex-escaped) in the subject. Pro: makes
  the error message's own suggestion truthful; honors whatever id the lane
  actually holds; one-file change. Con: a quirky id yields a quirky required tag
  — but that's *correct*, it's the lane's real id.
- **Option B — quick-task mints a `T-NNN` (or `Q-NNN`) id.** Route quick-task
  through `openup-claims.py reserve-id`. Pro: uniform numeric tag scheme
  everywhere. Con: implies a roadmap/claims allocation for throwaway work,
  reservation churn, heavier quick path — fights the point of "quick"; doesn't
  fix the latent contradiction for anyone hand-running `state.py init`.
- **Option C — relax the regex to any `[A-Za-z][\w-]*` tag.** Pro: trivial. Con:
  too loose — `[wip]`, `[fixme]`, any bracketed word would satisfy "the required
  task tag", defeating the check's purpose.
- **Option D — skip tag enforcement when the active id is non-numeric.** Pro:
  one line. Con: silently drops enforcement for the exact lanes (quick tasks)
  that most benefit from an audit tag; weakens the gate instead of fixing it.

## Open Questions

- Should the required tag be the *exact* `task_id` (Option A, strict) or should a
  numeric `[T-NNN]` still be accepted as an alternative for lanes whose id
  happens to be numeric? (Lean: accept the active id, and additionally still
  accept any `[T-NNN]` so specs that reference a related task id don't break.)
- Regression test placement: the T-006 hook test suite is the natural home —
  add cases (numeric id + `[T-NNN]` passes; non-numeric id + `[{id}]` passes;
  non-numeric id + no tag fails; `[openup-skip]` still bypasses).

### Product-manager challenge pass

- **Pushback:** none on *whether* to fix — a gate whose printed remedy can't
  satisfy it is a correctness bug in an enforcement hook, and it forced two
  audited `[openup-skip]` bypasses in one trivial cleanup (bypasses are supposed
  to be rare signals, not the routine quick-task exit). The value case holds: the
  user-visible symptom is "the tool told me to do X, I did X, it refused." What I
  *would* push back on is any temptation to scope-creep this into "redesign the
  tag scheme" — the defect is one unsatisfiable branch, and the fix should stay
  that small.
- **Complement:** the human framed it as "the error on numeric tag"; the missing
  connection is that this is a *template* defect (live==template), so it ships to
  every consuming project — raising priority from "annoyed me once" to "latent in
  the distributed framework." Also worth noting the cheaper-alternative trap:
  Option B (mint numeric ids) looks tidy but doesn't fix the underlying
  contradiction for hand-run state inits, so it's more work for less coverage.
- **Refine:** narrow the falsifiable success measure to: *the exact tag the hook
  tells you to append makes the commit pass* — i.e. for any active `task_id`,
  a subject ending `[{task_id}]` is accepted, and a subject with no tag is still
  rejected. That is directly testable and is the real contract, sharper than
  "support non-numeric ids."
- Disposition per challenge: pushback **accepted** (fix, keep it minimal — reject
  scope-creep into tag-scheme redesign); complement **accepted** (treat as a
  template/framework fix, sync live+template, note the distribution impact);
  refine **accepted** (success measure = the printed remedy is satisfiable).
  Option B **rejected** — heavier and doesn't cover hand-run inits. Options C/D
  **rejected** — they weaken the gate rather than fix the contradiction.

## Where this goes next

→ iteration — Promote a roadmap entry (proposed **T-070: validate-commit accepts
the active `task_id` as the required tag**): make `validate-commit.py` require the
lane's real `[{task_id}]` (regex-escaped) while still accepting any `[T-NNN]`,
sync live+template, and add T-006 hook tests proving the hook's own printed
remedy now satisfies the check (numeric + non-numeric ids pass with their tag;
no-tag still fails; `[openup-skip]` still bypasses). Standard track, single file
+ template + tests.

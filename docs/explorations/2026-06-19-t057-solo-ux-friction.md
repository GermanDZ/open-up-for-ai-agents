---
id: T-057-exploration
type: exploration
status: draft
title: "T-057: Solo UX Friction — plan artifact (written to explorations/ because gate-edits.py blocks docs/iteration-plans/ pre-iteration)"
---

# T-057: Solo UX Friction — Free Exploration, Gate-at-Commit, Auto-Merge

**Phase**: construction  
**Status**: pending  
**Goal**: Remove the three friction points that hurt the single-user local workflow — pre-work blocking hook, stranded branches after task completion, and missing gate at merge time.  
**Priority**: high  

> **Note on location**: This plan was written to `docs/explorations/` because
> `gate-edits.py` blocks writes to `docs/iteration-plans/` and `docs/roadmap.md`
> when no iteration is active. That blocking behavior is itself a fourth friction
> point this task should fix — planning artifacts created by `/openup-plan-feature`
> are not source code and must not require a prior iteration.

---

## Context

Three pain points observed during real downstream use (`bienestarsinfin.com` session,
2026-06-19), plus one discovered while writing this plan:

1. **on-task-request.py blocks freely** — the `UserPromptSubmit` hook fires exit 2
   (block) whenever it detects task-start language. This prevents casual exploration,
   questions, and local experimentation unless the user first starts an iteration.

2. **Completed branches strand** — `/openup-complete-task` creates a PR but stops
   there. For a solo local user, the PR sits unmerged; `main` stays stale; the next
   `/openup-next` cycle starts from an outdated base and causes JSONL rebase conflicts.

3. **Hook gate placement is wrong** — process enforcement should happen at the point
   where work is persisted. `check-iteration.py` already does this correctly (warns at
   `git commit`, exit 0). `on-task-request.py` blocks too early (UserPromptSubmit).

4. **gate-edits.py blocks planning artifacts** — `docs/iteration-plans/` and
   `docs/roadmap.md` are not in the gate's exempt list, so `/openup-plan-feature`
   cannot write its outputs without an active iteration. This is circular: you need
   a plan to start an iteration, but the gate blocks writing the plan.

---

## Current State

### Hook: on-task-request.py

Lines 179–202 — both branches exit 2 (block):

```python
    if status != "in-progress":
        ...
        sys.exit(2)   # ← BLOCKS the user prompt entirely

    else:
        ...
        sys.exit(2)   # ← BLOCKS even for active iterations
```

Hook event: `UserPromptSubmit` — fires before the user's message is processed.

### Hook: check-iteration.py

Already correct — fires at `git commit`, always exits 0 (warn, never block):

```python
    sys.exit(0)  # Warn but do not block
```

### Skill: openup-complete-task, Step 8

Creates a PR but does not merge it. No auto-merge, no pull to main, no worktree cleanup in the PR step.

### Hook: gate-edits.py — exempt list

Exempt paths: `docs/explorations/`, `.openup/`, `.claude/memory/`, `docs/agent-logs/`,
`docs/iteration-retrospectives/`, `docs/project-status.md`, `docs/changes/`.

**Not exempt**: `docs/iteration-plans/`, `docs/roadmap.md`, any other `docs/` path.

---

## Proposed Design

### Change A: on-task-request.py — advisory, not blocking

Change both `sys.exit(2)` → `sys.exit(0)`. The hook continues emitting its informational
stderr message (track suggestion, iteration reminder), but no longer blocks the prompt.

```python
# Both occurrences:
    sys.exit(0)  # Inform, never block — user is free to explore first
```

### Change B: complete-task skill — auto-merge after PR creation

Add **Step 9** after the existing Step 8 (PR creation):

```markdown
### 9. Auto-Merge and Pull to Local Main

After the PR is created, merge it immediately so local `main` is not left stale.

```bash
# Merge the PR (squash by default — keeps trunk history clean)
gh pr merge --squash --delete-branch

# Pull the merge commit to local main
git checkout main
git pull origin main
```

Skip ONLY if `$ARGUMENTS[auto_merge]` is explicitly `"false"`.

If `gh pr merge` fails (e.g. branch protection requires review), log the PR URL
and inform the user to merge manually before running the next cycle.
```

### Change C: gate-edits.py — exempt planning artifact paths

Add `docs/iteration-plans/` and `docs/roadmap.md` to the exempt list. These are
planning/coordination artifacts produced by `/openup-plan-feature` and related
planning skills — they are not source code and do not need an active iteration to be written.

```python
EXEMPT_PREFIXES = [
    "docs/explorations/",
    "docs/iteration-plans/",   # ← ADD
    ".openup/",
    ".claude/memory/",
    "docs/agent-logs/",
    "docs/iteration-retrospectives/",
    "docs/changes/",
]

EXEMPT_FILES = [
    "docs/project-status.md",
    "docs/roadmap.md",         # ← ADD (planning artifact, not source code)
]
```

### Change D: CLAUDE.openup.md — update hook-behavior note

Add to Critical Rules:

```markdown
**Hooks gate at commit, not at prompt.** `on-task-request.py` is advisory —
it emits a track suggestion and iteration reminder but never blocks. The
enforcement gate is `check-iteration.py` at `git commit`.
```

---

## Acceptance Criteria

- [ ] `on-task-request.py` never exits 2 — user can ask questions and explore freely
- [ ] `on-task-request.py` still emits its informational stderr message
- [ ] `/openup-complete-task` auto-merges the PR and pulls to local `main` by default
- [ ] Auto-merge is skippable with `auto_merge: false`
- [ ] If auto-merge fails, user is informed with the PR URL and manual steps
- [ ] `gate-edits.py` allows writes to `docs/iteration-plans/` and `docs/roadmap.md` without an active iteration
- [ ] `/openup-plan-feature` can run end-to-end without hitting the gate
- [ ] Both `.claude/` files and their `docs-eng-process/.claude-templates/` counterparts updated (parity)
- [ ] `check-claude-sync.sh` exits 0

---

## Success Measure

`/openup-plan-feature` runs without gate interference; the next downstream session
after a completed task finds local `main` current without manual merge.
Instrumentation: observed behavior in next downstream session.
Read-back: first downstream session after merge.

---

## Testing Strategy

- **Unit — on-task-request.py**: assert all paths exit 0; stderr message still emitted
- **Unit — on-task-request.py**: existing `suggest_track()` tests still pass
- **Unit — gate-edits.py**: assert `docs/iteration-plans/x.md` and `docs/roadmap.md` are exempt
- **Integration — complete-task**: `git log --oneline main` contains task commit after skill
- **Parity**: `check-claude-sync.sh` exits 0

---

## Dependencies

None.

---

## Key Files

| File | Change |
|------|--------|
| `.claude/scripts/hooks/on-task-request.py` | Both `sys.exit(2)` → `sys.exit(0)` |
| `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py` | Same |
| `.claude/scripts/hooks/gate-edits.py` | Add `docs/iteration-plans/` + `docs/roadmap.md` to exempt list |
| `docs-eng-process/.claude-templates/scripts/hooks/gate-edits.py` | Same |
| `.claude/skills/openup-complete-task/SKILL.md` | Add Step 9: auto-merge + pull |
| `docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md` | Same |
| `.claude/CLAUDE.openup.md` | Add hook-behavior note to Critical Rules |

---

## Out of Scope

- Removing check-iteration.py warning at commit (correctly placed, non-blocking)
- Changing the pre-push write-fence (correctly placed, correctly blocking)
- Worktree-per-task overhead for single-user use (separate concern)

---

## Open Questions

1. **Squash vs merge commit**: Assumed `--squash` — vetoable at review.
2. **Auto-merge default**: Assumed default-on for quick/standard tracks — vetoable.
3. **on-task-request active-iteration branch**: Assumed this also becomes exit 0 — vetoable.

---

## Proposed Roadmap Entry

```markdown
---

## T-057: Solo UX Friction — Free Exploration, Gate-at-Commit, Auto-Merge
**Status**: pending
**Priority**: high
**Value**: Solo users and downstream project leads can explore freely without process gates, and completed work lands on local `main` automatically — eliminating the stranded-branch rebase conflicts seen in real downstream sessions.
**Description**: Three hook/skill fixes that remove friction in the single-user local workflow: (1) on-task-request.py becomes advisory (exit 0, not blocking); (2) gate-edits.py exempts planning artifacts (docs/iteration-plans/, docs/roadmap.md) so /openup-plan-feature can run without an active iteration; (3) /openup-complete-task auto-merges its PR and pulls to local main after completion.
- on-task-request.py: both exit 2 → exit 0 (inform, never block)
- gate-edits.py: add docs/iteration-plans/ and docs/roadmap.md to exempt list
- openup-complete-task: Step 9 — gh pr merge --squash + git pull origin main

**Dependencies**: —

**See**: `docs/explorations/2026-06-19-t057-solo-ux-friction.md`
```

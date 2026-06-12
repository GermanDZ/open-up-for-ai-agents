---
id: T-022
title: Fix template→.claude sync (flat skills + full coverage) and auto-commit the log tail at session stop
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: high
estimate: 1 session
plan: ""   # standalone fix surfaced 2026-06-12 while fixing skill discovery (no program plan)
depends-on: []
blocks: []
touches:
  - scripts/sync-templates-to-claude.sh                                       # flat skill loop + rubric/hook/config/agent coverage
  - docs-eng-process/.claude-templates/scripts/hooks/on-stop.py               # auto-commit log tail (canonical/tracked copy)
  - .claude/scripts/hooks/on-stop.py                                          # live copy (gitignored) — kept in step with template
  - docs-eng-process/.claude-templates/scripts/hooks/check-unfinished-tasks.py # back-propagate live→template drift
  - docs-eng-process/.claude-templates/scripts/hooks/gate-edits.py            # back-propagate live→template drift
  - docs/roadmap.md                                                           # T-022 status
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-022 — Fix template→.claude sync + auto-commit the log tail at stop

## Story

> **As a** framework maintainer regenerating `.claude/` from `docs-eng-process/.claude-templates/`
> **I want** `sync-templates-to-claude.sh` to produce the flat, discoverable skill layout and to cover rubrics + hooks (not just skills/teammates/teams), and `on-stop.py` to commit the `agent-runs.jsonl` tail before stopping
> **So that** a sync from templates yields immediately-usable slash commands and current hooks, and no session ends with a dirty working tree.

INVEST check:
✅ Independent (no deps) · ✅ Negotiable · ✅ Valuable (sync correctness was the root cause of the nested-skill discovery break) · ✅ Estimable (1 script + 1 hook + 2 back-props) · ✅ Small (no architecture change) · ✅ Testable (`--dry-run` path assertions + hook unit behavior)

## Analysis Context

- **Domain.** The framework's *self-maintenance* sync — `scripts/sync-templates-to-claude.sh`
  (templates → live `.claude/`) and the `on-stop` traceability hook. `.claude/` is gitignored;
  `docs-eng-process/.claude-templates/` is the tracked/shipped source of truth.
- **Scope boundaries.** Does NOT touch `check-claude-sync.sh` (per review scoping — its
  both-layouts tolerance stays). Does NOT touch `sync-from-framework.sh` (already correct —
  it is the reference implementation we mirror). Does NOT change skill/rubric *content*.
- **Definition of done.** `sync-templates-to-claude.sh --dry-run` shows every
  `templates/skills/openup-*/SKILL.md` mapping to a flat `.claude/skills/openup-*/SKILL.md`
  (no `openup-{phases,artifacts,workflow}/` grouping dirs), plus rubric + hook copies; the two
  drifted hooks are reconciled (templates match the corrected live versions); `on-stop.py`
  commits a lone dirty `agent-runs.jsonl` as a log-only commit, leaving a clean tree, and
  blocks unchanged on any non-log dirty file.

**Assumption:** Canonical direction for the existing hook drift is **live → template**
(live `check-unfinished-tasks.py` blocks with `exit 2`; live `gate-edits.py` exempts
`docs/iteration-retrospectives/`) — the live versions are the intended behavior, templates
are stale. *(Vetoable at review.)*

**Assumption:** The sync rewrite mirrors `sync-from-framework.sh`'s coverage set (skills,
rubrics, hooks, config, agents, teammates, teams, CLAUDE) rather than inventing a new one.
*(Vetoable at review.)*

**Assumption:** Verification of the destructive templates→live copy uses `--dry-run` (running
it for real on this branch would overwrite the gitignored live `.claude/` that currently
carries unmerged T-019 edits). *(Vetoable at review.)*

## Requirements

1. `sync-templates-to-claude.sh` copies each `templates/skills/openup-*/SKILL.md` to a **flat**
   `.claude/skills/openup-*/SKILL.md`; it creates **no** `openup-phases/`, `openup-artifacts/`,
   or `openup-workflow/` grouping directory.
2. `sync-templates-to-claude.sh` syncs **rubrics** (`templates/rubrics/*.md` →
   `.claude/rubrics/`) and **hooks** (`templates/scripts/hooks/*` → `.claude/scripts/hooks/`).
3. `sync-templates-to-claude.sh` also covers **config** and **agents** when present (parity with
   `sync-from-framework.sh`).
4. The two drifted hooks (`check-unfinished-tasks.py`, `gate-edits.py`) are reconciled so the
   tracked template copy byte-matches the corrected live copy.
5. `on-stop.py`, when the **only** dirty path is `docs/agent-logs/agent-runs.jsonl`, commits it
   as a log-only `[openup-skip]` commit (which `auto-log-commit.py`'s `commit_only_touches_logs`
   guard does not re-log), then proceeds — leaving a clean tree at session end.
6. `on-stop.py` still **blocks** stop (exit 2) when any **non-log** file is dirty (existing
   behavior unchanged); the auto-commit fires only for the lone-jsonl case.
7. The `on-stop.py` change is applied to **both** the tracked template copy and the live copy.

## Behavior Delta

How this task changes existing product behavior (Ring 1: `docs/product/`).

**n/a — all Added/Modified to process tooling** (a sync script + the `on-stop` hook). No Ring-1
product use case, vision, or architecture statement changes.

## Entities

- **within-repo sync** (modified) — `scripts/sync-templates-to-claude.sh`
- **on-stop hook** (modified) — `docs-eng-process/.claude-templates/scripts/hooks/on-stop.py` (+ live `.claude/scripts/hooks/on-stop.py`)
- **drifted hooks** (modified, back-prop) — `…/.claude-templates/scripts/hooks/{check-unfinished-tasks,gate-edits}.py`
- **reference sync** (read-only) — `scripts/sync-from-framework.sh` (correct flat impl we mirror)
- **log-commit guard** (read-only) — `.claude/scripts/hooks/auto-log-commit.py` (`commit_only_touches_logs` makes the log-only commit terminal)
- **parity oracle** (read-only) — `scripts/check-claude-sync.sh`

## Approach

Mirror `sync-from-framework.sh`'s correct shape inside `sync-templates-to-claude.sh`: replace
the hard-coded `openup-phases/openup-artifacts/openup-workflow` category loop with a flat
iteration over `templates/skills/openup-*/`, and add the missing rubric / hook / config / agent
sync blocks. Reconcile the two stale template hooks by back-propagating the corrected live
copies. For the log tail, add a guarded pre-stop step in `on-stop.py`: if the sole dirty path is
the exempt `agent-runs.jsonl`, make a log-only `[openup-skip]` commit (terminal by virtue of the
existing `commit_only_touches_logs` guard) before the gate checks; any non-log dirt blocks as
today.

## Structure

**Add:**
- (none)

**Modify:**
- `scripts/sync-templates-to-claude.sh` — flat skill loop; add rubric/hook/config/agent sync
- `docs-eng-process/.claude-templates/scripts/hooks/on-stop.py` — lone-jsonl auto-commit (canonical)
- `.claude/scripts/hooks/on-stop.py` — same change in the live copy
- `docs-eng-process/.claude-templates/scripts/hooks/check-unfinished-tasks.py` — back-prop live
- `docs-eng-process/.claude-templates/scripts/hooks/gate-edits.py` — back-prop live
- `docs/roadmap.md` — add/track T-022

**Do not touch:**
- `scripts/check-claude-sync.sh` — both-layout tolerance stays (review scoping); not extended to hooks here.
- `scripts/sync-from-framework.sh` — already correct; it is the reference, not a target.
- skill/rubric *content* — this task is sync plumbing, not content.

## Operations

- [x] Rewrite the skill-sync loop in `scripts/sync-templates-to-claude.sh` to iterate flat
      `templates/skills/openup-*/SKILL.md` → `.claude/skills/openup-*/SKILL.md` (no category dirs).
- [x] Add rubric, hook, config, and agent sync blocks to `sync-templates-to-claude.sh`
      (mirroring `sync-from-framework.sh`).
- [x] Back-propagate the corrected live `check-unfinished-tasks.py` and `gate-edits.py` into
      their `.claude-templates/` copies so template == live.
- [x] Add the lone-`agent-runs.jsonl` auto-commit step to `on-stop.py` (template copy), then
      copy it to the live `.claude/scripts/hooks/on-stop.py`.
- [x] (tester) Verify: `sync-templates-to-claude.sh --dry-run` lists only flat skill targets +
      rubric/hook copies; `diff` shows template hooks == live for the three touched hooks; and a
      lone dirty `agent-runs.jsonl` is auto-committed to a clean tree while a non-log dirty file
      still blocks stop.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, `[openup-skip]`).
- `scripts/sync-from-framework.sh` — the canonical sync shape this mirrors.

## Safeguards

- **Token / size budget.** Script + hook edits only; no new files. on-stop addition ≤ ~25 lines.
- **Reversibility.** All edits are localized to one script + one hook (×2 copies) + 2 back-props;
  revert by restoring the prior versions. No data migration.
- **No-go zones.** Do not change `on-stop.py`'s non-log dirty-block or gate-block behavior; do
  not run the destructive templates→live sync against the real `.claude/` (use `--dry-run`),
  which currently holds unmerged T-019 live edits.
- **Reversibility of the log-commit.** The auto-commit is a normal `[openup-skip]` commit on the
  task branch — droppable like any commit.

## Verification

- `bash scripts/sync-templates-to-claude.sh --dry-run` → every skill target is
  `.claude/skills/openup-<name>/SKILL.md` (flat); rubric + hook copies appear; no
  `openup-{phases,artifacts,workflow}/` path printed.
- `diff` of each of the three touched hooks (template vs live) → identical.
- on-stop behavior: with only `agent-runs.jsonl` dirty, the hook commits it and the tree is
  clean (`git status --porcelain` empty); with a non-log file also dirty, the hook exits 2.
- Grade this spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

# T-007 — Design Decisions (living)

Decisions made during execution. This file is the sanctioned home for choices that
deviate from or refine the program plan, so `plan.md` and the program plan don't go stale.

## D1 — `docs/agent-logs/` stays in `docs/` (not Ring 3)

**Context:** WS4's sketch labelled Ring 3 "session debris... never in `docs/`" and listed
`.openup/ + .claude/memory/`. Read literally, that implied moving `docs/agent-logs/` out.

**Decision:** Keep `docs/agent-logs/` in `docs/`. It is the **durable, committed audit
trail** that `auto-log-commit.py` appends to and `on-stop.py` exempts from the dirty-block
(both shipped in T-006). Ring 3 means only *ephemeral* state: `.openup/state.json` and
`.claude/memory/`.

**Why:** Moving it would require rewriting `auto-log-commit.py` + `on-stop.py` (and their
template mirrors) and re-open the 39% unlogged-run gap that WS3 just closed. The audit
trail is product history, not debris.

**Confirmed:** user, 2026-06-11.

## D2 — `docs/plans/` stays in place

**Context:** `docs/plans/` is absent from the WS4 target tree; `on-plan-exit.py` hardcodes
saving plans there.

**Decision:** Keep `docs/plans/` for **program-level / multi-task plans** (the Process v2
program seeds T-004…T-011). Per-change planning lives in `docs/changes/T-NNN/plan.md`.

**Why:** Program plans *seed* change folders but are not a single change. Folding them into
`changes/` would break the program-vs-change distinction and force a `on-plan-exit.py` edit.

**Confirmed:** user, 2026-06-11.

## D3 — `project-status.md` and `roadmap.md` stay in place

**Decision:** Both stay (project-status as a generated view, per program plan Open Question #3).

**Why:** They don't move, so the recon's 150+/50+ reference counts are **inert** — the real
migration surface is `docs/tasks/` (~10 refs) plus skill context-loading guidance. This is
what made the iteration tractable in one pass.

**Confirmed:** user, 2026-06-11.

## D4 — Migration scope: structure + clear moves + note; defer cosmetic prose churn

**Decision:** Build the rings, migrate `docs/tasks/`, fix references that point at *moving*
paths, update context-loading guidance, ship a consumer migration note. Do **not** rewrite
every incidental `docs/` mention across 100+ files.

**Why:** Most prose refs point at files that stay put (D3); rewriting them would be churn with
no correctness payoff and a large review burden for a medium-priority task.

**Confirmed:** user, 2026-06-11.

## D5 — `done`/`verified` tasks archive immediately; `deferred`/active stay in `changes/`

**Decision:** T-001 (`done`) and T-003 (`done`) → `docs/changes/archive/`; T-002 (`deferred`)
→ `docs/changes/T-002/` (active). `deferred` is "not yet done", so it belongs in the live ring.

# T-011 — Design decisions (living)

## DD1 — Durable counter in `.openup/retro.json`, not in `state.json`

**Context:** WS6b says "`iterations_since_retro` increments in state on each completion."
Taken literally that means the counter lives in `.openup/state.json`. But
`/openup-complete-task` runs `openup-state.py archive`, which copies `state.json` into the
change folder and **deletes the live file**; `/openup-start-iteration` then `init`s a brand
new state. A counter that lives only in `state.json` therefore resets to whatever `init`
seeds every single iteration — it can never accumulate.

**Decision:** The authoritative counter lives in `.openup/retro.json`
(`{"iterations_since_retro": N}`). `archive` does not touch it, so it survives the
completion→start cycle. `state.json.iterations_since_retro` (schema-required) is retained as
an **init-time mirror** seeded from `retro.json` for audit/visibility; `retro check` also
keeps `gates.retro_due` in the live state in sync.

**Why not commit the counter** (e.g. to `project-status.md`): that would push ephemeral
session/cadence state into `docs/` (Ring 1), violating three-ring scoping (WS4). The cadence
nudge is local and **fail-safe** — if `.openup/retro.json` is lost to `git clean`, the count
restarts at 0 and the next retrospective merely fires sooner, never later in a way that skips
one silently on the heavy track (the gate re-arms as soon as 5 completions accrue again).

**Why a subcommand, not scribe edits:** `openup-state.py`'s contract is "skills MUST write
state through this CLI, never hand-edit JSON." A `retro` subcommand keeps the three skill
touch points as single deterministic commands and gives the boundary logic one unit-tested
home (`scripts/tests/test_t011_retro.py`).

## DD2 — Refusal targets the `full` track only

Per WS6b ("refuses `full`-track starts until `/openup-retrospective` runs"), an overdue retro
**blocks** only `full`-track starts. `quick`/`standard` starts proceed with a non-blocking
reminder. Rationale: the heavy track is where skipping reflection is most costly, and hard-
blocking every start would re-introduce the friction the graded-tracks work (T-010) removed.

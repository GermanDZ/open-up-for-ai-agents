# OpenUP Iteration State File

`.openup/state.json` is the single **machine-readable** record of the current
OpenUP iteration. Skills write it (via the helper CLI) and hooks read it to
enforce process gates. It is the deterministic counterpart to the prose status
docs in `docs/`.

- **Location:** `<repo-root>/.openup/state.json` (the `.openup/` directory is
  gitignored — it is runtime state, regenerated each iteration).
- **Tracked source of truth:** the schema (`scripts/openup-state.schema.json`)
  and the helper (`scripts/openup-state.py`) live under `scripts/` and *are*
  committed.
- **Golden rule:** skills write state **through the helper CLI**, never by
  hand-editing the JSON. Hand edits bypass schema validation and silently drift.

## Schema (v1)

| Field | Type | Notes |
|-------|------|-------|
| `schema` | int | Always `1`. |
| `task_id` | string | Roadmap task id, e.g. `"T-005"`. |
| `iteration` | int | Iteration number. |
| `phase` | string | `inception` \| `elaboration` \| `construction` \| `transition`. |
| `track` | string | `quick` \| `standard` \| `full`. |
| `branch` | string | Git branch for the iteration. |
| `worktree` | string | Absolute path to the working tree. |
| `session_id` | string \| null | Claude Code session id, or `null`. |
| `started_at` | string | ISO-8601 UTC, e.g. `2026-06-10T12:00:00Z`. |
| `gates` | object | Process gates — see below. |
| `gates.team_deployed` | bool | Team deployed for the iteration. |
| `gates.plan_persisted` | string \| false | `false` = not done; string = path to the persisted plan. |
| `gates.log_written` | bool | Run log written. |
| `gates.roadmap_synced` | bool | Roadmap updated. |
| `gates.retro_due` | bool | A retrospective is due. |
| `iterations_since_retro` | int | Iterations completed since the last retro. |

All fields are required; `additionalProperties` is forbidden at the top level
and inside `gates`. The schema is JSON Schema draft 2020-12; the helper ships a
small focused validator so no third-party libraries are needed.

## Helper CLI

Run as `python3 scripts/openup-state.py <subcommand> ...`. Use `--state-dir` to
point at an alternate `.openup` directory (tests do this).

| Subcommand | Purpose |
|------------|---------|
| `init --task-id … --iteration … --phase … --track … --branch … --worktree … [--session-id] [--plan PATH] [--iterations-since-retro N] [--force]` | Create `state.json`; stamps `started_at`; seeds gates (all false, `plan_persisted` = plan path or false). Exit 4 if it exists without `--force`. |
| `get [dotted.key]` | Print whole state (indent 2) or a dotted-path value. Exit 3 if no state, 5 if key missing. |
| `set <dotted.key> <value>` | Set a value with typed coercion (`true`/`false`→bool, ints→int, `null`→None, else string). Re-validates. |
| `set-gate <name> <value>` | Convenience for `gates.<name>`; same coercion (pass a path string for `plan_persisted`). |
| `check-gates [--require a,b,c]` | Exit 0 if required gates truthy; else exit 6 and print each unmet gate to stderr. Default required: `team_deployed,log_written,roadmap_synced`. |
| `archive <dest_path>` | Validate, copy state to `dest_path` (mkdir parents), then remove `state.json`. Exit 3 if no state. |
| `retro {get\|increment\|reset\|check} [--threshold N]` | Manage the durable retro-cadence counter (`.openup/retro.json`). See [retro cadence](#retro-cadence-t-011). |
| `validate` | Validate `state.json`; exit 0 ok, exit 7 invalid (prints reasons). |

Exit codes: `0` ok, `2` usage, `3` no state, `4` already exists, `5` key
missing, `6` gates unmet, `7` invalid.

## Gate lifecycle

Which skill flips which gate:

| Gate | Set by | When |
|------|--------|------|
| `plan_persisted` | `openup-start-iteration` (`init --plan`) | At iteration start, if a plan was persisted. |
| `team_deployed` | `openup-start-iteration` | After the team is deployed (`set-gate team_deployed true`). |
| `log_written` | `openup-log-run` | After the run log is written. |
| `roadmap_synced` | `openup-complete-task` | After the roadmap is updated. |
| `retro_due` | `openup-start-iteration` (`retro check`) | Set to `count >= 5` at iteration start; see [retro cadence](#retro-cadence-t-011). |

`openup-complete-task` runs `check-gates` before marking complete (blocking on
any unmet gate) and, as its final step, `archive`s the state to
`docs/agent-logs/<YYYY>/<MM>/<DD>/state-<task_id>.json`.

### Track-dependent gates

`check-gates` defaults to `team_deployed,log_written,roadmap_synced`.
`plan_persisted` and `retro_due` are **not** in the default set because they are
track-dependent. The **quick** track requires only `log_written,roadmap_synced`
and calls `check-gates --require log_written,roadmap_synced`.

See [tracks.md](tracks.md) for the full quick / standard / full ceremony matrix and how
`track` wires to the gates, team deployment, and the complete-task rubric.

## Retro cadence (T-011)

The retrospective cadence is enforced by a **durable counter**, not a convention. Because
`archive` deletes `state.json` on every completion, the counter cannot live there — it lives
in a sibling `.openup/retro.json` (`{"iterations_since_retro": N}`) that `archive` never
touches. `state.json.iterations_since_retro` is an **init-time mirror** of that durable value
(seeded via `init --iterations-since-retro "$(… retro get)"`), kept for audit/visibility.
Both files are local (`.openup/` is gitignored); the cadence nudge fails safe — if the file
is lost, the count restarts at 0 and the next retro simply fires sooner.

| Action | Run by | Effect |
|--------|--------|--------|
| `retro get` | `openup-start-iteration` (seeds `--iterations-since-retro`) | Print N (0 if absent). |
| `retro increment` | `openup-complete-task` (step 7a) | N += 1. Independent of archive ordering. |
| `retro check [--threshold N]` | `openup-start-iteration` (step 6) | Set `gates.retro_due = (count >= N)` in the live state; threshold default 5. Prints `due N` / `ok N`. |
| `retro reset` | `openup-retrospective` (step 8) | N = 0; clears `gates.retro_due` in any live state. |

**The gate's teeth:** when `iterations_since_retro >= 5`, `/openup-start-iteration`
**refuses a `full`-track start** until `/openup-retrospective` runs; `quick`/`standard`
starts proceed with a non-blocking reminder. The hard block targets only the heavy track
(WS6b) so the cadence trigger never re-imposes the friction T-010 removed. See
`docs/changes/T-011/design.md` (DD1/DD2).

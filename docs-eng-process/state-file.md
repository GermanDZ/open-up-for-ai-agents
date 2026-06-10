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
| `retro_due` | retrospective tooling | Driven by `iterations_since_retro`. |

`openup-complete-task` runs `check-gates` before marking complete (blocking on
any unmet gate) and, as its final step, `archive`s the state to
`docs/agent-logs/<YYYY>/<MM>/<DD>/state-<task_id>.json`.

### Track-dependent gates

`check-gates` defaults to `team_deployed,log_written,roadmap_synced`.
`plan_persisted` and `retro_due` are **not** in the default set because they are
track-dependent. The **quick** track requires only `log_written,roadmap_synced`
and calls `check-gates --require log_written,roadmap_synced`.

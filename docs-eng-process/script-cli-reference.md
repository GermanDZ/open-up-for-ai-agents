# Script CLI reference

Quick signatures for the deterministic helper scripts skills call most often.
Goal: stop the `usage:` / `unrecognized arguments` round-trips agents otherwise
burn on `--help` discovery (T-041, from the es-invoices audit). Authoritative
source is always `python3 scripts/<name>.py [<sub>] --help`; this page mirrors it.
All scripts are stdlib-only, deterministic, and never invoke a model.

## openup-state.py — iteration state (`.openup/state.json`)

```
init         --task-id --iteration --phase {inception|elaboration|construction|transition}
             --track {quick|standard|full} --branch --worktree
             [--session-id] [--plan PATH] [--iterations-since-retro N] [--force]
get          [KEY]                       # dotted path, e.g. gates.plan_persisted; whole state if omitted
set          KEY VALUE                   # typed coercion (true/false/int/null/string)
set-gate     NAME VALUE                  # gates.<name>
check-gates  [--require g1,g2,…]         # exit 6 if any required gate is falsy
archive      DEST_PATH                   # validate → copy → remove live state
retro        {get|increment|reset|check} [--threshold N]
validate
log-event    --event E [--task-id] [--run-id] [--goal] [--branch] [--phase]
             [--track] [--sha] [--log-dir]
```
- `log-event` stamps `ts` from the system clock and appends one record to
  `docs/agent-logs/agent-runs.jsonl`. **Use it for every `iteration_start` /
  `iteration_complete` / `commit` / `run_log` event — never hand-author a JSONL
  line or a `[ts]` placeholder.** Common events: `iteration_start`,
  `iteration_complete`, `run_log`.
- Exit codes: `0` ok · `2` usage · `3` no state · `4` state exists (init) ·
  `5` key missing (get) · `6` gates unmet · `7` invalid.
- All subcommands accept `--state-dir DIR` to override `<repo>/.openup`.

## openup-claims.py — live leases for parallel work

```
preflight    --task-id            # deps + collision check, writes nothing (exit 3 dep, 4 collision)
remote-check --task-id [--remote origin] [--no-fetch] [--self-branch B]  # cross-machine (exit 9 dup; 0 clear/skip)
claim        --task-id --session-id --branch --worktree
release      --task-id            # idempotent
list | dir
get          --task-id
reserve-id   [--task-id] --session-id   # atomically reserve next free T-NNN
next-id | release-id | list-ids
```
- Always `preflight` before `claim`. Claims never expire — a stale claim blocks
  its surface until a human removes `<git-common-dir>/openup/claims/<id>.json`.
- `remote-check` (T-044) is the **cross-machine** branch-as-claim early-warning:
  the local lease lives under `.git/` and is never pushed, so it can't see a
  teammate's clone. This lists `origin`'s branches and exits `9` if another
  branch already encodes the task (excluding `--self-branch`). **Advisory /
  fail-open**: no remote, unreachable remote, or auth error all exit `0` — it
  never blocks solo/offline work. `/openup-start-iteration` runs it before
  claiming and logs a `duplicate_start_blocked` event on exit 9.

## openup-board.py — derived execution board

```
top      [--root] [--claims-dir]        # top pickable lane as JSON; exit 3 = none pickable
refresh  [--root] [--claims-dir] [--out]  # rewrite .openup/board.json; print full board
```
- The board is **derived** from `docs/changes/*/plan.md` — never authored by the
  model. Exit 3 from `top` is a clean no-op, not a failure (see `/openup-next`).

## check-docs.py — work-product validator

```
check-docs.py [--docs DIR] [--schema PATH] [--model PATH] [--json] [--coverage]
```
- Flat args, **no subcommand** (a frequent friction point — do not write
  `check-docs.py check …`). `--coverage` adds required-coverage rules; required
  gaps fail the run.

## openup-scribe.py — deterministic scribe writes

```
status-note   …   # write a dated status-note shard
learnings     …   # append a dated iteration-learnings entry
```
- Run `--help` on each subcommand for its fields. The scribe only ever writes
  fully-specified content; it never authors timestamps or decisions.

## See also

- `scripts/README.md` — what each script is for.
- `docs-eng-process/state-file.md`, `parallel-work.md`, `tracks.md` — the
  processes these CLIs implement.

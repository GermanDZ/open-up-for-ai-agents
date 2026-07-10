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
runs         build [--log-dir]            # derive agent-runs.jsonl from shards (T-046)
```
- `log-event` stamps `ts` from the system clock and appends one record to the
  **lane-owned shard** `docs/agent-logs/runs/<UTC-date>-<task_id-or-branch>.jsonl`
  (T-046 — not the shared `agent-runs.jsonl`, which is now a gitignored derived
  view). **Use it for every `iteration_start` / `iteration_complete` / `commit` /
  `run_log` event — never hand-author a JSONL line or a `[ts]` placeholder.**
- `runs build` regenerates the consolidated `docs/agent-logs/agent-runs.jsonl`
  (ts-sorted) from the shard glob for local querying — a derived view, never
  hand-edited. The shards are the committed source of truth and are conflict-free
  (lane-owned), which `merge=union` on the old shared file could not guarantee on
  GitHub.
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

## openup-session.py — atomic session lifecycle (claim + state + log)

```
begin  --task-id --iteration N --phase P --track T [--branch B] [--worktree W]
       [--session-id S] [--plan P] [--goal G] [--run-id R] [--touches ...]
       [--depends-on ...] [--iterations-since-retro N] [--reap] [--stale-after S]
       [--no-push] [--force]              # acquire: reap-warn→remote-check→claim→
                                          #   heartbeat→state-init→session_begin log
end    --task-id --archive-to PATH [--status done] [--branch B] [--no-push]
                                          # teardown: archive state→session_end log→release
```
- `begin` folds `/openup-start-iteration` §6/§6b into one call. It runs the
  T-044 remote-check (exit **9** = another clone owns the task) and pre-flight
  (exit **3** unmet dep / **4** collision) via the composed `claim`. Any failure
  **after** the claim rolls it back (release) so no half-acquired session remains
  (Requirement 2). By default the stale-lease sweep is **dry-run + warn**; `--reap`
  makes it live (the loop's live self-heal lives in `openup-board.py refresh`, not here).
- `end` is `/openup-complete-task` §7b's teardown: archive `.openup/state.json`
  into `--archive-to`, log `session_end`, release the claim (idempotent — a no-op
  for an in-place task with no claim). Worktree removal stays in the skill.
  `/openup-create-handoff` does **not** call `end` — a handoff keeps its lease +
  state so `/openup-next` resumes the lane.
- Pure **composition** over `openup-claims.py` + `openup-state.py` (imported,
  driven through their `main(argv)`); it adds no new claim/state semantics.

## openup-board.py — derived execution board

```
top      [--root] [--claims-dir]        # top pickable lane as JSON; exit 3 = none pickable
refresh  [--root] [--claims-dir] [--out] [--reap-stale-after S] [--no-reap]
                                        # reap stale leases, then rewrite .openup/board.json
```
- The board is **derived** from `docs/changes/*/plan.md` — never authored by the
  model. Exit 3 from `top` is a clean no-op, not a failure (see `/openup-next`).
- `refresh` **reaps heartbeat-stale leases before deriving** (T-063): a crashed
  session's lane self-heals from `in-progress` to `ready` within one refresh.
  Default threshold 1800s (`--reap-stale-after`); `--no-reap` skips it. The T-060
  invariant holds — a claim with **no** `last_heartbeat` is never reaped.

## openup-roadmap.py — deterministic roadmap interface

```
list  [--status pending|planned|completed|all] [--root] [--claims-dir]
                                        # matching entries as JSON, document order (default: pending+planned)
get   T-NNN [--root] [--claims-dir]     # one entry as JSON; exit 3 if absent
next  [--root] [--claims-dir]           # next promotable task as JSON; exit 3 = none (reason on stderr)
```
- **Read-only** — parses `docs/roadmap.md` (both entry shapes: table rows **and**
  manual `## T-NNN:` sections) and never writes. Document order is the
  product-manager's value order, consumed as-is (never re-ranked).
- `next` is the deterministic promote-step selector for `/openup-next` §1c: first
  `pending`/`planned` entry whose deps are satisfied, with **no change folder**
  (active `docs/changes/<id>/` **or** archived `docs/changes/archive/<id>/`) and
  **no live lease**. The archived-folder skip stops a delivered-but-stale-`pending`
  task from being re-promoted (status-rot guard); deps count as satisfied on true
  delivery evidence (`completed` status **or** archived folder). Exit-3 reasons
  mirror `openup-board.py top` (`roadmap exhausted` / `next pending <id> blocked on
  <dep>` / `all pending tasks in flight`). Track selection stays a model call.

## check-docs.py — work-product validator

```
check-docs.py [--docs DIR] [--schema PATH] [--model PATH] [--json] [--coverage]
```
- Flat args, **no subcommand** (a frequent friction point — do not write
  `check-docs.py check …`). `--coverage` adds required-coverage rules; required
  gaps fail the run.

## openup-doctor.py — read-only project health diagnostic

```
openup-doctor.py [--repo-root DIR] [--framework-path DIR] [--json]
```
- **Read-only** — never writes/fixes; diagnoses only. Three checks: (1)
  framework/manifest drift (`--framework-path` enables byte-level CLI drift;
  offline-degraded to version-only without it), (2) `.openup/state.json`
  integrity (reuses `openup-state.py validate`), (3) aggregation over the
  existing read-only / `--check` validators (it *invokes* them, never
  reimplements). Severity: **error** (corrupt state, missing shipped CLI,
  failed read-only validator) → **exit 1**; **warning** (behind on version,
  modified CLI, stale derived view) / **info** → exit 0. Unresolvable root →
  exit 2. `sync-status.py` is intentionally excluded (it writes; no read-only
  mode).

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

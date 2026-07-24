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
             [--session-id] [--iteration-id C3] [--cycle N] [--plan PATH]
             [--iterations-since-retro N] [--force]
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
- **Schema 2 (T-078).** State carries `iteration_id` (pointer to the iteration-plan
  instance, e.g. `C3`; `null` for a single-lane/promote-degenerate start) and
  `cycle` (project lifecycle cycle, default 1). `phase` is a **derived cache**
  stamped from `openup-lifecycle.py status` (source of truth = the milestone
  records), not hand-set. A schema-1 file is **auto-migrated on read** (additive:
  backfills `iteration_id: null`, `cycle: 1`, bumps `schema`) and persisted in
  place — no manual re-init. Set them post-init with `set iteration_id C3` /
  `set cycle N`.

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
top-n N  [--root] [--claims-dir]        # up to N collision-free READY lanes as JSON array; exit 3 = none
partition [ID …] [--stdin] [--root]     # cluster work items into non-colliding iteration groups; JSON array of clusters; exit 0
resolve  [--root] [--claims-dir]        # §0–§1 /openup-next decision as ONE JSON object; always exit 0
status   [--root] [--claims-dir]        # read-only diagnostic superset (active + leases + pickable + promotable)
refresh  [--root] [--claims-dir] [--out] [--reap-stale-after S] [--no-reap]
                                        # reap stale leases, then rewrite .openup/board.json
```
- The board is **derived** from `docs/changes/*/plan.md` — never authored by the
  model. Exit 3 from `top` is a clean no-op, not a failure (see `/openup-next`).
- `resolve` (T-065) folds the whole §0–§1 precedence into one **read-only** call:
  returns `{path, lane, resumable_input, active_iteration, phase, cycle,
  legacy_path, reason}` with `path ∈ {resume, pick, assess-iteration,
  milestone-review, plan-iteration, noop}` (resumable-input → active-iteration →
  top-pickable → **iteration-exhausted (assess)** → **phase-exit + drained
  (milestone)** → plan-iteration → noop; T-077 relabelled promote→plan-iteration
  with `legacy_path: "promote"`; T-078 added the two lifecycle paths + `cycle`).
  `/openup-next` §0–§1 is a single `resolve` call. Its plan-iteration/promote pick
  is **identical** to `openup-roadmap.py next`.
  `status` is the human diagnostic superset. Neither writes anything (only
  `refresh` writes `board.json` / runs the reap) — safe in doctor-style contexts.
- `refresh` **reaps heartbeat-stale leases before deriving** (T-063): a crashed
  session's lane self-heals from `in-progress` to `ready` within one refresh.
  Default threshold 1800s (`--reap-stale-after`); `--no-reap` skips it. The T-060
  invariant holds — a claim with **no** `last_heartbeat` is never reaped.
- `partition` (T-079) clusters work items into **non-colliding iteration groups**
  — the connected components of the `touches`-overlap ∪ `depends-on` graph (the
  same `claims.touches_overlap` the write-fence uses). Positional `ID`s read
  `touches`/`depends-on` from each `docs/changes/<id>/plan.md`; `--stdin` reads a
  JSON array of `{id, touches, depends-on}` instead (Plan Iteration partitions
  *planned* items before assigning cluster-prefixed ids). Output is a
  deterministic, order-stable JSON array of clusters (each a list of ids);
  read-only, always exit 0. Distinct clusters are disjoint in `touches` and
  dependency-free, hence safe to run as **concurrent iterations** (one per
  cluster; see [parallel-lanes.md](parallel-lanes.md)). A single cluster
  degenerates to today's one sequential iteration.

## openup-roadmap.py — deterministic roadmap interface

```
list  [--status pending|planned|completed|all] [--root] [--claims-dir]
                                        # matching entries as JSON, document order (default: pending+planned)
get   T-NNN [--root] [--claims-dir]     # one entry as JSON; exit 3 if absent
next  [--root] [--claims-dir] [--remote origin] [--no-remote-check]
                                        # next promotable task as JSON; exit 3 = none (reason on stderr)
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
- **Remote delivered-but-unmerged guard (T-066)**: before promoting a candidate,
  `next` also consults `origin` for a branch encoding the task id (reuses the
  T-044 branch-as-claim matcher) and **skips it** if one exists — a task finished
  in an open, unmerged PR archives its change folder *on the branch* and releases
  its lease, so it is invisible to the local guards and would otherwise be
  re-implemented. The exit-3 reason then reads `<id> delivered-but-unmerged —
  origin branch '<branch>' exists; merge its PR instead of re-promoting.`
  **Fail-open**: no remote / unreachable / not a git repo → promotion behaves
  exactly as without the guard (offline work is never blocked). One `ls-remote`
  per invocation (cached across candidates). `--no-remote-check` disables it
  (hermetic/offline callers); `--remote` overrides the remote name. Inherited by
  `openup-board.py resolve`'s promote branch (it calls `cmd_next`), so `resolve`
  returns `noop` (not `promote`) for a delivered-but-unmerged task.

## sync-status.py — derived-view generator (roadmap + project-status)

```
sync-status.py [--state-dir] [--roadmap] [--project-status] [--notes-dir] [--no-gate]
                                        # default: derive current task's status from state, regen both views
sync-status.py --reconcile [--dry-run] [--roadmap]
                                        # self-heal: stamp completed(<archival-date>) on section-style entries
```
- **Writes** `docs/roadmap.md` + `docs/project-status.md` — the sole writer of
  those derived shared views (never hand-edit them; re-run this instead).
- Default mode flips the current task's Status (from `.openup/state.json`).
  `update_roadmap()` handles **both** entry shapes: markdown **table rows** and
  the free-form `## T-NNN:` **section** `**Status**:` lines emitted by
  `/openup-plan-feature` (the section path is a fallback taken only when no table
  row matches — T-067).
- `--reconcile` is a **state-free sweep**: for every `## T-NNN:` section whose
  change folder is archived under `docs/changes/archive/<id>/` but whose Status
  is not yet `completed`, it stamps `completed (<archival-date>)` (the archival
  commit's date via `git log`, falling back to today). Idempotent; writes only on
  change. This heals plan-feature status-rot regardless of when it happened.
  `--dry-run` reports drift as machine-readable `DRIFT <id> <status>` lines
  without writing — this is what `openup-doctor`'s read-only
  `roadmap-status-drift` check invokes.

## check-docs.py — work-product validator

```
check-docs.py [--docs DIR] [--schema PATH] [--model PATH] [--json] [--coverage] [--changed-only]
check-docs.py --show-archetype-defaults
```
- Flat args, **no subcommand** (a frequent friction point — do not write
  `check-docs.py check …`). `--coverage` adds required-coverage rules; required
  gaps fail the run.
- `--changed-only` (T-123): skip the full validation and exit 0 when the docs
  tree + schema + trace-model are byte-identical (by a cheap stat signature) to
  the last **successful** `--changed-only` pass; any delta — or a prior failure —
  runs the full check. The signature is cached in `.openup/check-docs-cache.json`
  (Ring-3, gitignored), keyed by docs dir + `--coverage`. Cuts the harness flow's
  repeated defensive re-runs; the default (no-flag) path is untouched.
- `--show-archetype-defaults` (T-115): prints the Development Case archetype
  defaults (`quick`/`mvp`/`product`) plus what applies when
  `docs/project-config.yaml`'s `process:` block is absent (today: no
  archetype tailoring). Short-circuits before loading any `docs/` tree — safe
  to run with no project docs at all. A different axis from the ceremony
  track (`tracks.md`); don't conflate the two.

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

## openup-lifecycle.py — derived project-lifecycle status (phase + milestones)

```
openup-lifecycle.py [--repo-root DIR] [--state-dir DIR] status [--json]
openup-lifecycle.py [--repo-root DIR] [--state-dir DIR] stamp-phase
```
- **Read-only `status`** — derives the current **phase** + **cycle** and each
  milestone-exit **criterion** state (`met` | `unmet` | `human-judgment`).
  Sibling to `openup-board.py`: same never-hand-edit rule. Phase authority is the
  **milestone decision records** in `docs/product/milestones/<phase>-<cycle>.md`
  (human go/no-go, authored only by `/openup-phase-review`); with **no records**
  it falls back to `.openup/state.json`'s `phase` and flags `source:
  state-fallback` (no fabricated history). Criteria are marked `met`/`unmet` only
  when mechanically verifiable (a typed work-product instance exists, per T-038);
  judgment criteria (architecture *validated* = tested skeleton, stakeholder
  concurrence) are reported `human-judgment`, never auto-`met`. A malformed
  milestone record → **exit 2** naming the file.
- **`stamp-phase`** — writes the derived phase into `.openup/state.json`
  (idempotent; `phase` is a derived cache, no longer hand-set via
  `project-status.md`). Exit 3 when there is no state file.

## openup-process-map.py — process map loader (phase→activity→role→skill)

```
openup-process-map.py [--repo-root DIR] activities-for <phase> [--json]
openup-process-map.py [--repo-root DIR] activity <name> [--json]
openup-process-map.py [--repo-root DIR] phase-letter <phase>
openup-process-map.py [--repo-root DIR] mint-iteration-id <phase>
openup-process-map.py [--repo-root DIR] validate
openup-process-map.py [--repo-root DIR] tasks [--validate] [--json]
```
- **Read-only.** Loads the vendored `docs-eng-process/process-map.yaml` (KB §4:
  phase → ordered activities, activity → `{role, skills}`, phase → iteration-id
  prefix letter) with a stdlib-only parser (no pyyaml). Preferred path is
  `docs-eng-process/process-map.yaml`; falls back to `scripts/process-map.yaml`
  (shipped-into-a-project layout). Exit 3 if the map file is absent.
- **`activities-for <phase>`** — the ordered activity list for a phase, each
  resolved to its `{name, role, skills, requires_input, execution}`. This is what
  Plan Iteration (`/openup-start-iteration`) reads to generate phase-appropriate
  lanes.
- **`activity <name>`** / **`phase-letter <phase>`** — one activity's
  `{role, skills, requires_input, execution}`; the iteration-id prefix letter
  (e.g. `construction` → `C`, for `C3-001` minting).
- **Per-activity `requires_input` + `execution` (T-100, P1)** — an activity MAY
  declare `requires_input: { path, describe }` (a human-authored file it reads)
  and `execution: direct | spec-then-execute` (default `spec-then-execute`;
  `direct` runs the activity's single skill/procedure without an intermediate lane
  spec). `validate` hard-gates them (input has a `path`; `execution` in the enum;
  `direct` ⇒ exactly one skill). The deterministic navigation layer (T-101/T-102)
  reads these to drive input scaffolding + how each activity runs, replacing the
  hardcoded Inception bootstrap. Fields absent ⇒ pre-T-100 behavior unchanged.
- **`mint-iteration-id <phase>`** — the stable iteration id `<letter><ordinal>`
  (`C3`) for the phase; the ordinal is repo-monotonic per letter (max existing
  `C<n>-*` id + 1) so it stays globally unique across cycles — the ordinal is
  derived from existing ids, never from state. Plan Iteration records it in the
  iteration-plan instance and reserves lanes under it via `openup-claims.py
  reserve-id --prefix "C3-"`; schema 2 (T-078) also caches it into
  `.openup/state.json` `iteration_id` for the active lane.
- **`validate`** — every activity named in `phases:` has an `activities:` entry,
  each role is known, each phase has a prefix letter. Exit 2 (naming the problem)
  on any structural fault; the map is the single source the thin phase skills front.
- **`tasks [--validate] [--json]` (T-105)** — reads the committed task library
  `docs-eng-process/task-library.yaml` (lean authoring task defs) with the same
  stdlib parser. `--validate` hard-gates every def: all fields present, `artifact`
  in the v1 spine enum, `role` known, `judgment` 3–8 bullets, `output_path` a
  relative `.md` path — exit 2 on any fault. `--json` dumps the parsed defs. The
  library is unconsumed by the engine until T-106.

## build-task-library.py — task-library compiler (T-105)

```
build-task-library.py [--repo-root DIR]              # online compile (needs endpoint)
build-task-library.py [--repo-root DIR] --offline DIR # emit distillation prompts, no LLM
build-task-library.py [--repo-root DIR] --check       # skeleton drift vs KB sources
```
- **Sibling of `build-trace-model.py`.** Compiles the vendored KB authoring task
  files into `docs-eng-process/task-library.yaml`. Two stages: (1) deterministic
  extraction of the def *skeleton* (`name`, `role` = primary performer, `inputs`)
  from each KB task's UMA structure; (2) LLM distillation of the task prose into
  the 3–8 `judgment` bullets via `openup_agent/llm.py` (compile with a **strong**
  model; output human-reviewed before commit).
- **`--offline DIR`** — writes each KB-sourced task's distillation prompt to
  `DIR/<task-id>.prompt.txt` and makes no network call; complete/review out of band.
- **`--check`** — re-extracts the skeleton from each def's `source` and diffs
  against the committed library; exit 1 on skeleton drift (`name`/`role`/`inputs`).
  Prose (`judgment`) drift is advisory — regeneration is a reviewed act. Driver-native
  defs (`source: driver`, e.g. `author-initial-roadmap`) have no KB skeleton and are
  skipped. Online compile needs `LLM_API_URL` + `OPENUP_COMPILE_MODEL` (or `LLM_MODEL`).
- Exit codes: 0 ok / in-sync · 1 `--check` drift · 2 usage / could-not-run.

## openup-scribe.py — deterministic scribe writes

```
status-note   …   # write a dated status-note shard
learnings     …   # append a dated iteration-learnings entry
```
- Run `--help` on each subcommand for its fields. The scribe only ever writes
  fully-specified content; it never authors timestamps or decisions.

## next-cycle — guided single entry point (T-095, thinned in T-096)

```
./scripts/next-cycle [--dir .] [driver flags…]
                                   # env config -> one driver cycle;
                                   #   guidance on stderr, sentinel passthrough,
                                   #   exit code = the driver's
                                   # unknown flags forward to `openup-agent.py
                                   #   cycle` verbatim (T-111), e.g.
                                   #   ./scripts/next-cycle --step-max-iterations 15
```
- Composes `openup-agent.py` only and knows **no process** (T-096): loads
  `.openup/agent.env`, guides missing endpoint config, then runs ONE `cycle`
  (`--interactive` auto-added on a TTY). What a fresh project needs next is
  decided by the driver's **deterministic** navigation (the process map — a fresh
  authoring phase → `plan-iteration`; T-101/T-103), not the wrapper.
  Scriptable exactly like `cycle`.

## openup-agent.py — reference driver (T-072 `run` · T-089 `cycle`)

```
run    --dir PATH --procedure NAME [--max-iterations 50] [--instruction TEXT]
       [--interactive]                  # LLM drives the whole procedure; exits 0/2/3/4/5
cycle  --dir PATH [--step-max-iterations 10] [--step-tier authoring]
       [--interactive] [--no-recover]   # deterministic engine: resolve → begin →
                                        #   per-Operations-box executor (scripts as code,
                                        #   judgment as bounded sub-runs) → gates →
                                        #   completion; exits 0/2/3/4/5/6/7/8
```
- `cycle` (T-089) runs ONE delivery cycle with ceremony as code and the LLM only
  at judgment boxes — sentinel parity with `/openup-next` (`OPENUP-NEXT:
  ADVANCED/DONE`). Recovery (T-092, default on; `--no-recover` opts out): a
  done-but-unclosed lane is archived/merged before planning (zero LLM), and a
  construction/transition `plan-iteration` decision's missing spec is authored by
  one bounded analyst sub-run, gated + committed, then picked in the same
  invocation. Plan Iteration (T-090): an **authoring-phase**
  (`inception`/`elaboration`) `plan-iteration` decision instead plans a full
  named iteration — mint id, one objectives sub-run, one lane per
  `activities-for(phase)` (iteration-prefixed ids, partitioned via T-079), one
  spec sub-run per lane (gated + committed), and a `type: iteration-plan` instance
  under `docs/phases/<phase>/` tracing the lanes — then re-resolves to the first
  lane (Inception through `cycle`). When nothing
  is promotable at all, the engine asks for consent (TTY under
  `--interactive`, else input-request + suspend exit 5) before ONE
  product-manager replenishment pass proposes new pending roadmap entries
  (T-094 — accepted only if `openup-roadmap.py next` then succeeds; an
  answered `no` is durable). Fresh-project navigation is **deterministic**
  (T-101/T-103): a fresh authoring phase resolves to `plan-iteration` from the
  process map (no roadmap needed); each activity's declared `requires_input`
  (T-100 data) is scaffolded as a marker-guarded template and the cycle suspends
  until the human fills it; an `execution: direct` activity runs its procedure
  directly. The per-cycle LLM **navigator** + hardcoded bootstrap were **retired**
  (T-103) — the LLM only authors, never navigates. Assess + milestone (T-091 — full `/openup-next`
  parity): `assess-iteration` grades the exhausted iteration's non-derivable
  criteria in one bounded sub-run and appends a deterministic `## Assessment`
  section to its iteration-plan instance (`ADVANCED` sentinel; discovered work
  recorded, not auto-enqueued); `milestone-review` prepares evidence and raises
  the human go/no-go as an input-request (zero LLM, `SUSPEND` exit 5, no dup,
  never advances the phase). Exit 6 =
  gate failed after a step (box left unticked, re-run retries), 7 = decision
  path not supported (`plan-iteration` only under `--no-recover`; every path is
  otherwise handled), 8 = a script-step /
  session / recovery command failed. Full model + step
  classification: [reference-driver.md](reference-driver.md).

## openup-agent-bench.py — reference-driver benchmark harness (T-080)

```
[--repo .] [--runs N] [--procedure next] [--command run|cycle] [--scenario DIR]
[--out DIR] [--workdir DIR] [--max-iterations 50] [--timeout 1800]
[--include-working-tree] [--keep]
```
- Runs the T-072 reference driver (`openup-agent.py run --procedure next`, or
  `openup-agent.py cycle` when the scenario / `--command` says so — T-089's
  `cycle-quick-doc` scenario benchmarks the engine against the `quick-doc`
  baseline on the same lane) N times
  against an **isolated fresh-`git init` fixture** (built with `git archive HEAD`
  outside the repo, seeded with a deterministic micro-task so `resolve` picks it),
  recording **outcome + gate re-check + tokens + latency + iterations + work-delta**
  and aggregating to `results.jsonl` + `summary.md`. The repo under test is never
  written to. Endpoint/model come from the driver's env (`LLM_API_URL`,
  `OPENUP_MODEL_MAIN`, …). Reads token/latency via the driver's opt-in
  `OPENUP_AGENT_USAGE_LOG`. Full runbook + metric definitions:
  [reference-driver-benchmark.md](reference-driver-benchmark.md).
- **`OPENUP_AGENT_DEBUG_LOG`** (T-098): set to a path to append the **full LLM
  transcript** (one JSON line per call: `request` messages + `response`
  content/tool_calls/finish_reason) — the way to see *why* a weak local model
  misbehaved (skipped `write_file`, early sentinel). Opt-in; unset ⇒ unchanged.

## See also

- `scripts/README.md` — what each script is for.
- `docs-eng-process/state-file.md`, `parallel-work.md`, `tracks.md` — the
  processes these CLIs implement.
- `docs-eng-process/reference-driver.md` + `reference-driver-benchmark.md` — the
  harness-optional driver and its benchmark harness.

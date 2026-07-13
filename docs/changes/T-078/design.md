# T-078 — In-flight design decisions

## DD1 — State schema 2 (Operations step 1, delivered)

**What.** `.openup/state.json` `schema` 1→2; added `iteration_id`
(nullable pointer to the iteration-plan instance, e.g. `C3`) and `cycle`
(project lifecycle counter, default 1); documented `phase` as a **derived
cache** stamped from `openup-lifecycle.py status`.

**Migration is in-memory-on-read + persist-in-place.** `read_state()` calls a
pure `migrate_state(state) -> (state, changed)` that additively backfills the two
new fields and bumps `schema`; if changed it best-effort persists the upgrade
(wrapped in `try/except OSError` so a read-only fixture still yields the upgraded
dict in memory). Rationale: every hook calls `openup-state.py get`, so an
in-flight schema-1 lane must not error on the bump, and `migrate_state` must stay
cheap — it does **not** shell out to `openup-lifecycle.py` (that would put a
subprocess in every hook read). `cycle` therefore defaults to `1` on migration
and is authoritatively (re)derived at init / plan-iteration time.

**`begin` needs no change.** `openup-session.py begin` shells `openup-state.py
init` via argv, and `init` now emits schema 2 with defaults (`iteration_id` null,
`cycle` 1) — so the atomic session path upgrades for free. Later slices (the
plan-iteration wiring) will pass `--iteration-id` / `--cycle` explicitly.

**Get/set.** No new subcommands — the generic `set iteration_id C3` / `set cycle
N` and `get iteration_id` already cover R5's "set/get" via the dotted-path
helpers, and both keys are now in-schema so `additionalProperties:false` accepts
them.

**Tests.** `tests/test_state_schema2.py` (7 hermetic): init-schema2-defaults,
init-carries-id+cycle, schema1→2 migrate-in-place (fields preserved),
migrated-schema1-validates, migrate pure+idempotent, migrate preserves explicit
id/cycle, invalid-schema2 (missing keys) still rejected. Full python suite 71
passed (64 + 7), no regression.

## DD2 — resolve paths: assess-iteration + milestone-review (Operations step 2, delivered)

**Precedence.** New order in `resolve_decision`: resume → pick → **assess-iteration**
→ (compute promote entry) → **milestone-review** → plan-iteration → noop.

**assess-iteration** fires when a minted phase-aware iteration is exhausted and
unassessed. "Minted iteration" is detected purely from data with **no new
frontmatter**: an iteration-plan instance (`type: iteration-plan` under
`docs/iteration-plans/` or `docs/phases/`) whose `traces-from` contains at least
one **iteration-prefixed** lane id (`C3-001`, matching `^[A-Z]\d+-\d+$`). Legacy
per-task plans trace to `T-NNN`/requirement ids and never match — so single-lane /
promote flows (and this very repo) never trigger it. "Exhausted" = every committed
lane done (archived change folder, or active plan `status ∈ {done,verified,
completed}`); "assessed" = the plan body carries a `## Assessment` section.

**milestone-review** fires only when the roadmap is **drained** (`_promote_next`
returns nothing), the phase's exit criteria are met (no criterion `unmet`;
`human-judgment` ones are what the review resolves), and no milestone record
exists for the current phase+cycle. Gating on "nothing promotable" — the *same*
check plan-iteration uses — was the key fix: lifecycle's `roadmap-clear`
criterion only sees table rows, so without this gate a manual-`## T-NNN`-section
pending task would be milestone-reviewed instead of planned. The `phase`/`cycle`
come from `openup-lifecycle.py compute_status` (T-075); `resolve` now carries
`cycle` on every decision (additive field).

**Zero behavior change for existing flows** — verified: the live repo still
resolves `resume T-078`, and the full suite is green. Both paths are covered by
`tests/test_board_assess_milestone.py` (14: helper units + both fires + the
work-remains / already-assessed / recorded / pending-work negatives).

**Deferred to later steps (not this one):** consuming these paths in
`openup-next` (step 5), the `/openup-assess-iteration` procedure that writes the
`## Assessment` section (step 3), and `/openup-phase-review` writing the milestone
record on GO (step 4). Step 2 is detection only.

**Note (framework flaw surfaced at start).** Committing the spec fired the
auto-log hook → `log_written=true`; with `roadmap_synced=true` both standard-track
gates were true and `sync-status.py` derived **completed** for a just-started
task. Corrected by `set-gate log_written false` + re-sync → in-progress. Not
fixed here (out of lane); logged to memory for the program.

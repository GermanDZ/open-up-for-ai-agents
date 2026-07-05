# Exploration: openup-next loop efficiency — state discovery, promote determinism, claim ceremony

**Started:** 2026-07-05
**Question:** Can we make one `/openup-next` cycle cheap (tokens), deterministic (selection), and low-friction (round-trips) by extending the script layer, without duplicating the skill machinery?

## Context

User feedback on the continue-loop (2026-07-05 session):

1. Many tokens are spent just to know the project (roadmap) state.
2. Planning the next step is not always deterministic.
3. There is a lot of back-and-forth getting the next iteration selected.
4. The lock/release mechanism for sessions doesn't look efficient.

Ask: scripts invokable as tools that answer "what's the plan / what's the
current session in work" exactly, in one call.

Related artifacts: `/openup-next` (`.claude/skills/openup-next/SKILL.md`),
`scripts/openup-board.py` (T-017), `scripts/openup-claims.py` (T-009, T-044,
T-056, T-060), `scripts/openup-state.py`, `scripts/openup-loop.sh` (T-059),
[parallel-lanes.md](../../docs-eng-process/parallel-lanes.md).

## Notes

### Where each complaint actually comes from (evidence from this repo)

**1. Token-heavy state discovery.**
- `openup-board.py` covers only *lanes* (`docs/changes/*/plan.md` + leases).
  The roadmap has no machine-readable interface: `board.py` never reads
  `docs/roadmap.md` (the word appears only in a stderr reason string). So the
  moment `top` exits 3 with "roadmap may have promotable work", the model must
  read `docs/roadmap.md` (219 lines — tables interleaved with multi-paragraph
  Value/Context prose) and `docs/project-status.md` (82 lines, mostly long
  iteration notes) into context.
- Double reads: `/openup-next` resolves the lane, then `/openup-start-iteration`
  steps 1–2 re-read project-status + roadmap anyway.
- Instruction overhead: a promote cycle loads `openup-next` (295 lines) +
  `create-task-spec` (254) + `start-iteration` (351) + `complete-task` (443)
  ≈ 1,350 lines of skill text before any work happens.
- `board.py refresh` prints the full pretty-printed board even when one lane
  matters; `top` is better but skills still reach for `refresh` for diagnostics.

**2. Non-deterministic promote.** §1c of `/openup-next` is the one
model-executed selection in an otherwise deterministic pipeline: "read
`docs/roadmap.md` and select the first pending entry whose depends-on are
satisfied, with no change folder and no live lease" is executed by the model
against markdown tables, plus two more judgment calls (task shape:
implementation vs. inception artifact; track selection). Three places where two
sessions can diverge on identical inputs — the "if a step is deterministic, the
harness does it" rule, unapplied to the roadmap.

**3. Round-trips.** A promote cycle chains ~12 sequential Bash invocations:
`openup-input.py resumable` → `openup-state.py get` → `openup-board.py top` →
roadmap read → (spec authoring) → `retro get` → `state init` → `retro check` →
`remote-check` → `preflight` → `claim` → `heartbeat` → `set-gate` →
`log-event`. Some are redundant by construction: `claim` already runs preflight
internally, yet the skill calls `preflight` separately; a board-`ready` lane is
already guaranteed to pass preflight (agreement-by-construction), yet it is
re-checked twice more.

**4. Lock/release.** Two distinct issues:
- *Ceremony*: acquiring a lease is 4 calls (`remote-check`, `preflight`,
  `claim`, `heartbeat`); release is spread across `complete-task` §7b. Five
  overlapping claim signals exist: lease file, `state.json`, branch, worktree,
  remote branch-as-claim.
- *Recovery*: claims never expire (T-009 D1). The T-060 heartbeat/reaper fixes
  this but is wired **only** into `/openup-fan-out` — in the sequential loop a
  crashed session leaves a stale lease blocking its whole `touches` surface
  until a human `rm`s it; the board reports `in-progress` forever.

### Candidate direction — extend the script layer (three verbs)

1. **`openup-roadmap.py`** — deterministic roadmap interface: `next`
   (implements §1c's selection rule mechanically), `list --status pending`,
   `get T-NNN`. Parses the existing markdown tables (format is already
   regular). Closes the determinism hole and removes the roadmap-in-context
   read.
2. **`openup-board.py status` / `resolve`** — one call, compact JSON answering
   "where are we": active iteration (state.json), live leases, top pickable
   lanes, promotable roadmap queue (via #1), answered-input check folded in.
   `resolve` returns the whole precedence as data:
   `{path: "resume"|"pick"|"promote"|"noop", lane: {…}, reason: …}` — the
   skill's §0–§1 collapse into one invocation, and the skill text shrinks
   accordingly.
3. **`openup-session.py begin|end`** — atomic claim lifecycle: `begin
   --task-id` = remote-check + preflight + claim + heartbeat + state init +
   log-event in one process; `end` = release + state archive + log-event. All
   stdlib composition of existing functions, no new logic. Wire `claims reap`
   into `begin` / `board refresh` so stale leases self-heal in the sequential
   loop (keeping the T-060 invariant: heartbeat-less claims are never reaped).

Cheaper co-wins: start-iteration skips its status/roadmap re-read when invoked
with a resolved lane; prefer `top` over `refresh` output everywhere except
explicit diagnostics.

## Options Considered

- **Option A — three script verbs (above), skills slimmed to call them.**
  Pro: attacks all four complaints; consistent with the derived-board
  philosophy; skill text shrinks (token win compounds every cycle).
  Con: `openup-session.py` risks becoming a second implementation of the
  start-iteration/complete-task lifecycle that drifts from the skills — must be
  composition-only (import existing modules), never re-implementation.
- **Option B — structured roadmap source (YAML/JSON) with markdown as derived
  view.** Pro: kills the parsing problem at the root, fully consistent with
  T-024 derived-views. Con: migration touches every roadmap consumer
  (sync-status.py, plan-hook, humans editing tables, PM role docs); big-bang
  risk for a problem a parser solves today. Defer until the Option-A parser
  proves brittle.
- **Option C — skill-text-only slimming (no new scripts).** Pro: cheapest;
  some token win. Con: leaves the promote step non-deterministic and the
  stale-lease recovery manual — doesn't answer the feedback.

## Open Questions

- Should `resolve` *write* anything (e.g., refresh board.json) or stay
  read-only so it can run in `openup-doctor`-style contexts?
- Where does the roadmap parser draw the line on the legacy plan-hook blocks
  (`### Completed:` sections with their own tables)? Proposal: parse all task
  tables, filter by status — section headers are decoration.
- Does `session begin` subsume start-iteration's worktree creation, or does the
  skill keep git operations and delegate only state+claim? (Leaning: skill
  keeps git; script owns state+claim+log — smallest surface that removes the
  round-trips.)
- Reap-on-begin default: dry-run + warn, or auto-reap? (T-060 made reap
  advisory; auto-reap inside `begin` changes its blast radius.)
- Track selection stays a model judgment (it is a scoping call, not mechanics)
  — confirm that is acceptable to the users, since it caps how deterministic
  promote can get.

### Product-manager challenge pass

- **Pushback 1 — "12 round-trips" conflates two costs.** A Bash round-trip is
  cheap in tokens; the expensive parts are the doc reads and the 1,350 lines of
  skill text. If we build `openup-session.py` purely to reduce call count but
  the skills stay fat, users won't notice the difference. The value case for #3
  is *latency and failure-atomicity* (a crash between `claim` and `state init`
  leaves half-acquired sessions), not tokens. → **Accepted into notes**: the
  token win must come from #1/#2 plus skill slimming; #3 is justified by
  atomicity + the reap wiring, and its scope is trimmed to state+claim+log
  (git stays in the skill).
- **Pushback 2 — who is the user and how would we notice?** "Feels heavy" is
  not falsifiable. → **Accepted — refined into a measure**: tokens-per-cycle
  and tool-calls-per-cycle for a promote cycle, read from
  `docs/agent-logs/runs/` before/after; expectation: ≥40% fewer input tokens on
  the selection phase (state discovery through claim) and selection divergence
  = 0 on identical fixtures (two runs, same inputs, same pick).
- **Pushback 3 — Option B now would be over-reach.** Restructuring the roadmap
  source touches every consumer for a problem a 100-line parser solves;
  evidence (this repo + downstream projects' roadmaps) shows the table format
  is already regular. → **Accepted**: Option B explicitly deferred with a
  trigger — revisit only if the parser needs per-project format exceptions.
- **Complement 1 — reap wiring is the highest value-per-line item** and was
  buried inside #3: a stale lease silently halts the whole autonomous loop
  (the loop's entire promise). It ships first even if the rest slips.
  → **Accepted**: ordering below puts reap+atomicity first.
- **Complement 2 — the sentinel/loop contract (T-059) gets a free upgrade**:
  `resolve` output gives `openup-loop.sh` a machine-readable pre-check ("is
  there anything to do?") without spawning a `claude -p` process at all for
  the no-op case. → **Accepted into notes** as a non-goal-but-free win.
- **Refine — sharpen the question**: from "make the loop efficient" to three
  falsifiable deliverables — (a) selection is script-decided (model divergence
  impossible by construction), (b) state discovery is one invocation returning
  ≤ ~40 lines of JSON, (c) a crashed session self-heals within one cycle
  without human `rm`. → **Accepted**: these become the acceptance criteria of
  the roadmap entries.
- **Value rationale (one line each)**: *roadmap CLI + resolve* — solo
  developers running `/openup-next` stop paying a re-read of the whole roadmap
  every cycle and stop getting divergent picks; *session begin/end + reap* —
  an unattended loop survives its own crashes, which is the difference between
  "autonomous" and "babysat".

## Where this goes next

→ iteration — promote to three ordered roadmap entries: (1) `openup-session.py begin|end` + reap wiring into the sequential loop (atomic claim lifecycle, self-healing stale leases), (2) `openup-roadmap.py` deterministic roadmap interface (`next`/`list`/`get`), (3) `openup-board.py status`/`resolve` verb + skill slimming to consume it (single-call state discovery, ≤40-line JSON), with the measures from the challenge pass as acceptance criteria.

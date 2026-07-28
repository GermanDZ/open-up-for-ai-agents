# Exploration: Harness v2 — a deterministic control plane for LLM-driven OpenUP delivery

**Started:** 2026-07-28
**Question:** What should a next-generation harness look like — containerized, git-centric, deterministic bureaucracy, configurable OpenUP-based process, provider-agnostic LLM access, parallel sessions — given the measured evidence from this project, and does the idea survive adversarial review?

Working name in this document: **loom** (placeholder — rename freely). "v1" means the
framework in this repository (skills + hooks + scripts layered on a chat harness).

## Context

Owner-submitted concept (2026-07-28): a new harness that (1) runs in a container for
sandboxing; (2) uses git as the primary history/versioning tool; (3) makes the development
process fully user-configurable, shipping OpenUP as the default; (4) executes bureaucratic
tasks deterministically (no LLM), persisting project state in files and/or SQLite;
(5) answers status/history/state questions via deterministic commands; (6) reaches LLMs
only through a provider-agnostic proxy/adapter (OpenAI-compatible HTTP, `claude -p`, other
APIs) with pluggable auth, switching, and load balancing; (7) treats harness token
efficiency as a requirement; (8) reacts and recovers when users change the process
mid-flight; (9) organizes the process on the OpenUP template (activities, roles, workflows,
artifacts); (10) runs multiple non-competing sessions in parallel that coordinate on shared
project state; (11) stores process artifacts in the git repository. "Deterministic" is
defined as: the result involves no LLM. Nothing from v1 needs to be reused; lessons do.

Evidence base for this exploration:

- `.claude/memory/iteration-learnings.md` — 30+ task entries (T-004 → T-158) of
  what-worked / gotchas / conventions.
- [iteration-109 retrospective](../iteration-retrospectives/iteration-109-retrospective.md)
  — current defect shapes (C1–C4), risk posture (R1 critical, R3 ceremony, R5 open
  question).
- [2026-07-16 cycle-orchestration economics](2026-07-16-cycle-orchestration-economics.md)
  — the measured cost baseline (transcript analytics over ~3,100 turns / ~2.6M output
  tokens; forensic audit of an 80-commit sample project run).
- Program memories: deterministic cycle engine (T-089–T-091, T-096), lean authoring
  (T-104–T-124), cycle economics (T-120–T-123), measurement tooling (T-127–T-132).

## Notes

### What v1's evidence actually says

These are the measured or repeatedly-observed facts the new design must answer to. Each
lesson below is cited where it was established.

**L1 — The LLM-driven control plane is the dominant waste.** 60% of Bash tool calls in the
harness flow are process ceremony (610/1,024); ceremony:product-code ≈ 14:1; 187
validator guess-and-check re-runs; 211× `git status` + 106× `git rev-parse` "where am I"
polling; ~129 `openup-state.py` subprocess round-trips (economics exploration, measured).
The model spends tokens re-deriving deterministic state because the *engine* is prose
instructions executed by a chat agent.

**L2 — Committed coordination state is the dominant complexity.** 26% of an entire sample
project's commit history serviced the run log; one doc deliverable cost 8 commits (1
product + 7 ceremony) (economics exploration). Derived views committed to git spawned the
write-fence, `sync-status.py` special cases (exit 3, `--views-only`, T-157), `merge=union`
(which GitHub ignores server-side — T-046), the hand-edit bans, and a whole class of
rebase-and-regenerate recovery recipes. A gate added to the required set must today be
edited in four places in lockstep (T-145).

**L3 — Deterministic-engine-with-LLM-judgment-points works.** The T-089–T-091 cycle engine
reached full `/openup-next` parity with the LLM invoked only at judgment points. The
script/judgment step classification is proven.

**L4 — Judgment steps need contracts, not prose.** T-124: inlining inputs (instead of
handing paths) plus a convergence contract (single write, no verify re-read, emit sentinel
immediately) took a weak-model use-case authoring sub-run from 28+ turns to 6. Conversely,
the engine handed paths to content it had already read, tier routing never used the top
tier, and turn caps were inverted (economics exploration) — briefing quality and routing
must be engine-owned and testable.

**L5 — Recovery tools must not require preconditions the failure destroys.** Two defects of
the same shape in one cycle: `sync-status.py` demanded the state file that completion
archives; `reap` skips heartbeat-less claims, and the documented re-claim recovery itself
created permanently un-reapable claims (iteration-109, C1). 12 stale claims had
accumulated. Crash/interrupt recovery must be designed from the journal, not from live
state.

**L6 — Rules duplicated across writers drift.** A hook that can't import the CLI duplicated
the shard-key slug rule (T-046); a hand-replicated roadmap parser broke on prose format
(T-122 B9); live `.claude/` vs `.claude-templates/` mirror drift consumed entire lanes
(T-019, T-022, F10's 34-file drift). One implementation of every rule, one source tree.

**L7 — Hooks policing a general-purpose chat harness are a losing layer.** on-stop
tail-chase (T-006, T-012, T-051, the 2026-07-24 bypass-log exemption); gate-edits running
against the main checkout while editing worktree files (T-059); `validate-commit`
intercepting throwaway /tmp repos (T-022); `state init --force` from the wrong cwd
clobbering the live lane (T-070). The enforcement layer fights the harness instead of
being the harness.

**L8 — Verification claims must be computed, not reported.** "Full suite" meant
`scripts/tests/` only, silently omitting 114 tests including the ones relevant to the
open defect (iteration-109, C2). `sync-status.py` printed success for a task it never
matched (C3).

**L9 — Parallelism was built, then barely used.** Iteration 109: 7 lanes, all solo,
serial. The lease/fence/collision machinery is real cost; its benefit so far is mostly
correctness under *accidental* concurrency (cross-session interference), not throughput.

**L10 — The framework's critical standing risk is having no external consumer.** Fifteen
consecutive cycles with no downstream project validating value; three `can't tell` measure
verdicts in one retrospective trace to unreachable consumer repos (iteration-109, R1
critical, C4). A v2 that repeats framework-for-framework's-sake fails regardless of
architecture.

**L11 — What worked and must carry over.** Two legal exits (complete/handoff);
fix-spec-first; typed artifact traceability (T-038 spine) with a validator; graded
ceremony tracks; PM-owned value ordering consumed mechanically by execution; retro
measure read-back with premise-checked action items (T-158 step 5c); compiled-pack
pattern with a drift gate (task-library.yaml, skills-guide); record-and-measure culture
(T-080 bench, transcript analytics).

### Design principles (each answerable to the evidence)

- **P1. The engine owns the loop; the LLM is a callee.** Bureaucracy runs as code;
  judgment runs as contracted LLM calls. (L1, L3, L7)
- **P2. One writer, one schema; every human-visible view is a query.** (L2, L6, L8)
- **P3. Git holds content; SQLite holds coordination and the journal; nothing lives in
  both.** (L2)
- **P4. Every step is typed `mechanical` or `judgment`; judgment steps carry a contract:
  inlined context pack, output schema, convergence rules, turn/token caps, model tier.**
  (L4)
- **P5. Crash-first: every operation is journaled and resumable; recovery reads the
  journal, never a precondition file.** (L5)
- **P6. Serial by default, parallel by explicit opt-in — but the state model is built for
  parallel from day one so opting in is not a re-architecture.** (L9)
- **P7. The process is data: a compiled, versioned, lint-gated pack. One source tree, no
  mirrors.** (L6, L11)
- **P8. The harness measures itself: tokens, latency, gate results, and cost are journal
  facts with deterministic queries.** (L11, and the requirement that made L1 findable)

### High-level architecture

Two planes:

- **Control plane** (deterministic, zero LLM tokens): engine + SQLite + process pack +
  git operations.
- **Work plane**: sessions executing workflow steps; judgment steps reach models only
  through the gateway.

Components:

**C1. Engine (`loom`)** — a single binary embedding the scheduler, state store access,
gate runner, pack loader, and git operations. Runs in two modes: *embedded* (CLI invokes
engine in-process — the solo/serial path) and *broker* (a per-project daemon owning all DB
writes, spawned on demand when a second session appears; sessions and CLIs talk to it over
a unix socket). Direct multi-process SQLite over container bind mounts is rejected —
locking over virtiofs/bind mounts is exactly the class of environment bug v1 kept hitting
with shared ambient state (L7).

**C2. State store** — SQLite at `.loom/state.db`, gitignored. Two layers in one
transaction: an append-only `journal` (every state transition, gate result, LLM call,
git operation — with monotonic sequence, session id, idempotency key, input content
hashes) and current-state projections (`work_items`, `iterations`, `sessions`, `leases`,
`gates`, `artifact_index`, `llm_calls`, `budgets`). Projections are rebuildable by replay;
replay is the repair path, not the hot path (deliberately journal+tables, not pure event
sourcing). `loom export` can snapshot the journal to files for backup/portability; journal
data is never committed per-commit (kills v1's 26%-of-history problem, L2).

**C3. Process pack** — the meta-model is generic and fixed: *Role*, *ArtifactType*
(schema + template + rubric), *Activity* (ordered steps, each `mechanical` or
`judgment`), *Workflow* (DAG of activities with gates), *Gate* (deterministic predicate
from a built-in library), *Track* (ceremony profile), *Phase/Iteration* (optional
containers), lifecycle state enums. **OpenUP ships as the default pack instance** —
roles (analyst, architect, developer, tester, product-manager, project-manager), phases
(Inception/Elaboration/Construction/Transition), the artifact spine (vision, use case,
architecture notebook, risk list, iteration plan, test plan), tracks (quick/standard/full)
— satisfying the "organized on the OpenUP template" requirement without baking OpenUP
into the engine schema. Customization = layered overlays: a project pack may add
artifacts/activities/gates and tighten thresholds; it may not silently waive a base gate
(v1's project-config precedence rule, kept). Packs are authored as YAML + Markdown
templates, compiled by `loom pack build` into a validated form with a `--check` drift
gate (the proven task-library pattern, L11). Escape hatch: a mechanical step may invoke a
project-provided executable with **declared effects** (write-set globs, no network) that
the engine fences.

**C4. Model gateway** — provider adapters: `anthropic`, `openai-compat` (any base URL —
covers LM Studio/Ollama/vLLM), `claude-cli` (`claude -p` subprocess, riding existing
subscription auth), extensible. Auth profiles per provider (env, OS keychain, device
flow). Routing: pack tiers (e.g. `reasoning` / `authoring` / `mechanical-text`) map to
ordered candidate lists with failover and optional round-robin; per-step overrides in the
pack; every resolution is journaled so misrouting is visible (fixes L4's silent
MID-for-everything). Budgets: per-call usage recorded; per-lane and per-project caps
enforced by the engine (hard stop → handoff, the v1 token-budget protocol made
structural). **Record/replay**: every judgment call's context-pack hash + response is
journaled, so pack tests and benches replay without spend — this generalizes the T-080
bench harness into a first-class feature. Adapter conformance suite (fixtures + canary)
guards provider drift, including the fragile `claude -p` output contract.

**C5. Session runtime** — a session = lease + worktree + branch + executor.
`loom session start <work-item>` claims the lease transactionally in the DB (no claim
files; the engine stamps liveness on every touch — no heartbeat-less path can exist,
closing C1's defect shape by construction), creates the worktree, and runs the workflow:
mechanical steps in-process or in the sandbox; judgment steps through the gateway with an
engine-assembled context pack. Two executors:
  - `builtin` — the engine drives each judgment step directly (the T-089 model);
  - `external-agent` — the engine delegates a whole activity to a commodity agent CLI
    (claude-code, etc.) inside the sandbox, then re-takes control at the gate. v1 already
    proved this shape with `openup-loop.sh` driving `claude -p` on sentinels.
Two legal exits, kept from v1: `loom complete` (gates → merge) and `loom handoff`
(journaled handoff note, ≤6 bullets, written into the work-item folder in git so
cross-machine handoff needs no DB sync).

**C6. Git integration** — branch-per-work-item; engine-mediated commits; **merge queue**
in the engine serializing integration to trunk: rebase, re-run gates, merge. The fence
becomes one rule evaluated at merge time: observed diff ⊆ declared write-set (work-item
scope + pack step effects). No derived views are committed — `status`, board, INDEX,
roadmap tables are queries (L2). Projects that want committed human-readable snapshots
can enable `loom export views` as an engine-only step at trunk merge (default off).
Cross-machine coordination rides on git as in v1, but the v1 advisory check becomes a
default-on engine check: promotion refuses a work item whose remote branch or open PR
already exists (the "next re-promotes unmerged PRs" bug, closed structurally).

**C7. Query surface** — deterministic, zero-LLM: `loom status`, `loom board`,
`loom log <work-item>`, `loom history`, `loom explain <artifact-id>` (trace web walk),
`loom cost` (tokens/spend by lane, step, model), `loom sessions`, `loom doctor`
(projection rebuild + git↔DB reconcile), `loom pack lint|test|diff`. Verification claims
come from the engine: a "tests pass" gate names the command and scope it actually ran
(closes L8).

**C8. Process-change reaction** — pack versions are content-hashed; a lane pins the pack
version at claim time. When the pack changes, each in-flight lane hits a **safe point**
(step boundary — judgment steps are atomic: either journaled-complete or not-run) and the
engine classifies it: *unaffected* (continue pinned), *migratable* (steps remap
mechanically; migrate), or *orphaned* (its activity no longer exists → judgment/human
disposition). `loom pack diff` shows the semantic delta. No lane deadlocks; no lane
silently continues an invalid flow.

**C9. Sandbox** — per-session policy, not global: `host` (trusted interactive use) or
`container` (default for autonomous sessions): rootless OCI container, worktree bind
mount, **no network except the gateway/broker socket; provider secrets never enter the
sandbox** (the gateway holds keys outside); engine performs pushes from outside the
sandbox. Container-per-session also kills the ambient-cwd bug class (L7) by construction:
a session cannot see the main checkout or a sibling worktree.

### What is deliberately not carried over from v1

- Hook-based enforcement grafted onto a chat harness (replaced by the engine owning the
  loop).
- Committed derived views + write-fence rebase machinery + `merge=union` (views are
  queries).
- Claim files under `.git/` + advisory-only remote checks (leases in DB; remote check
  default-on).
- The two-tree template mirror (`.claude/` vs `.claude-templates/`) — one pack source,
  compiled.
- Run-log commits and shard files (journal).
- The stdlib-only-Python distribution constraint (single static binary).

### Sequencing (walking skeleton first)

- **v0 — serial-correct skeleton**: `loom init`; work items + board + claim (serial);
  one quick-track workflow with two judgment steps; gateway with `anthropic` +
  `openai-compat` + budgets + record/replay; gates: schema-valid, tests-pass,
  diff-within-write-set; single-lane merge; `status/log/cost/doctor`; **crash-injection
  test matrix on the journal protocol (H1) before anything else is built up**.
- **v1**: broker daemon + parallel sessions + merge queue; container profile;
  `claude-cli` adapter; pack overlays + `pack diff` + reconcile; external-agent executor.
- **v2**: full OpenUP pack (phases, retro with measure read-back, rubric grading as
  judgment steps), staged-adoption mode for existing repos, bench suite.

## Hardest challenges (ranked)

1. **H1 — Git↔DB consistency under crashes.** The seam between the two truths is the
   correctness core. Protocol: intent event → git operation → confirm event, all
   idempotency-keyed; startup scan rolls unconfirmed intents forward or back by
   inspecting git. Worktrees keep most git ops lane-local; trunk integration is
   serialized by the queue. Total DB loss must be survivable: artifacts and handoffs are
   in git; leases are re-claimable; history is lost only past the last export (policy
   decision). *This gets prototyped and crash-tested first; if it can't be made boringly
   reliable, the two-store design is wrong* (see A5).
2. **H2 — Pack DSL expressiveness cliff.** Too rigid → users route around it (v1's
   over-blocking lesson); Turing-complete → un-analyzable and non-deterministic.
   Approach: declarative core; gates only from a built-in predicate library +
   composition; opaque-but-fenced external executables as the escape hatch; `pack test`
   with record/replay for golden runs. The OpenUP pack must be written using only public
   pack features — a forcing function against engine special-casing.
3. **H3 — Deterministic context assembly that is actually good.** The pack declares each
   step's input artifact types; the engine inlines content (size caps, truncation
   markers, content hashes for provider prompt caching). Risk: deterministic selection
   under-briefs the step. Mitigation: a bounded, journaled `request_more` escape in the
   step contract — every use of it is a pack bug report (v1's 8× roadmap re-read becomes
   a measurable defect, not silent waste).
4. **H4 — Process hot-swap semantics (C8).** The mechanics are clear at safe points; the
   hard residue is topology changes that invalidate *completed* steps. Default answer:
   pinning + orphan report + human disposition; live migration stays opt-in per lane.
5. **H5 — Merge queue and collisions on real code.** Path-prefix `touches` worked for
   docs; code lanes overlap on lockfiles, registries, shared tests. Declared write-sets +
   observed-diff fence + rebase-with-gates in the queue; an explicit conflict-resolution
   judgment step type; and honesty: some merges bounce to a human. Promise *serialized,
   gated integration*, not conflict-free parallelism.
6. **H6 — Provider heterogeneity.** Missing usage reporting (local endpoints), tool-call
   dialect differences, `claude -p` format drift. Capability flags per adapter
   (`reports_usage`, `supports_tools`, `supports_cache_control`), tokenizer-estimated
   budgets when usage is absent, conformance fixtures + canary tests, graceful
   degradation to single-shot + schema-repair when tools are unavailable.
7. **H7 — Sandbox ergonomics.** macOS bind-mount performance, UID mapping, git identity.
   Contained by C9's per-session policy: humans on host, autonomous sessions in
   containers, pushes always from the engine.

## Risks

- **R1 — Second-system effect.** The design above is a lot of machine. Mitigations:
  walking-skeleton sequencing (v0 above), broker deferred behind embedded mode, two
  providers before N, quick-track before full OpenUP. Kill criterion: if the v0 skeleton
  can't run one real work item end-to-end within the first program increment, cut scope
  again.
- **R2 — Building framework-for-framework's-sake again** (v1's R1, critical, 15 cycles).
  Mitigation: every milestone demos on a *non-harness* product repo; "first external
  project onboarded" is an explicit early milestone; self-hosting loom's own development
  comes only after that.
- **R3 — Concurrency/crash bugs in the broker + journal.** Mitigation: H1 prototyped
  first with a kill-matrix (SIGKILL at every protocol step) + property tests; the journal
  makes these deterministic to reproduce.
- **R4 — Pack authoring lands with one author only** (configurability nobody uses).
  Mitigation: scope pack tooling to `lint` + `test`; a second trivial pack (Kanban) exists
  only to prove the seam; no registry/marketplace until demand exists.
- **R5 — Provider drift** breaking adapters (especially `claude-cli`). Conformance suite
  + version pinning + capability flags.
- **R6 — Token-metering inaccuracy** undermining budgets. Best-effort estimates flagged
  as estimates in the journal; budgets enforce on the conservative bound.
- **R7 — Determinism erosion** (wall clock, map ordering, fs iteration order) breaking
  replay. Engine rule: no wall-clock in decisions (timestamps are recorded facts, not
  inputs); replay tests in CI.
- **R8 — Security of the escape hatches.** Pack executables and LLM-authored code run
  with repo access: packs are trusted-at-install like any dev tool, LLM-authored pack
  edits require human review before activation, autonomous sessions default to the
  container profile with no network.
- **R9 — Cross-machine coordination stays advisory.** Same-machine exclusion is
  transactional; cross-machine rides on pushed branches/PR state (default-on check, but
  a race window remains). Declared limitation for v1; a shared broker is a later option.
- **R10 — Scope creep toward multi-user server.** Declared non-goal for v1:
  single-machine, multi-session; teams sync through git.

## Options Considered

- **State substrate** — *all-git* (v1 is this experiment; L1/L2 are its measured cost) /
  *all-DB* (loses PR review, history, portability of artifacts) / **hybrid with a hard
  boundary (chosen)**: content in git, coordination + journal in SQLite, views as queries.
- **DB access model** — *many processes open SQLite directly* (rejected: bind-mount/
  virtiofs locking across containers) / *always-daemon* (rejected for v0: ceremony) /
  **embedded engine promoted to broker on demand (chosen)**.
- **Pack format** — **YAML + Markdown templates compiled with a drift gate (chosen —
  proven pattern)** / CUE (stronger typing, niche authoring skill) / Starlark (rejected
  for the core: Turing-completeness kills analyzability; revisit for gate predicates only
  if the predicate library proves insufficient).
- **Engine language** — **Go (recommended: static binary, trivial cross-compile, good
  SQLite story, fast iteration)** / Rust (stronger invariants, slower iteration) /
  Python (rejected for distribution: v1's interpreter/asdf-shim/stdlib-only pain).
  Owner preference wins; the walking skeleton is small enough that starting in the final
  language is cheaper than a rewrite.
- **Executor model** — *builtin only* / **builtin + external-agent adapter (chosen)**:
  the harness hosts commodity agents rather than competing with them.
- **Journal depth** — *pure event sourcing* (rejected: replay-only projections are
  ceremony for a dev tool) / **journal + current-state tables in one transaction
  (chosen)** / *tables only* (rejected: L5 — recovery needs the journal).

## Adversarial review

- **A1 — "Agent platforms will ship all of this natively; you're building a commodity."**
  Partially right: sandboxes, sessions, and task queues are commoditizing fast. The
  defensible core is narrower than the component list: *process-as-data with deterministic
  enforcement, provider independence, and a self-hosted auditable record*. The
  external-agent executor is the hedge — loom then *hosts* commodity agents instead of
  racing them. If that core has no external demand, this is a hobby (see R2). Verdict:
  proceed, but the demand test is an early milestone, not an afterthought.
- **A2 — "Deterministic harness is oversold — the work is still stochastic."** Correct.
  The honest claim is: deterministic *control plane*, replayable coordination,
  deterministic queries over recorded facts. The LLM's outputs remain judgment. Wording
  narrowed accordingly throughout. Verdict: accepted; claim restated.
- **A3 — "The OpenUP ontology will leak into the engine and fight other processes."**
  Real risk; answered structurally: the engine meta-model has no phases, no iterations,
  no OpenUP nouns — those are pack-level constructs. The requirement "organized on the
  OpenUP template" is satisfied by OpenUP being the shipped default pack. The Kanban
  test pack (R4) is the leak detector. Verdict: accepted with that refinement.
- **A4 — "SQLite + git is two sources of truth; v1's smear will just move."** The v1
  smear was coordination state *inside merge semantics* (committed views, claim files,
  lockstep gate definitions). Here coordination never enters merge-land; the seam
  narrows to one protocol (H1) that is crash-tested first. If H1 can't be made boring,
  the design is wrong — that's the falsifiable core. Verdict: risk real, contained,
  test-gated.
- **A5 — "Containers will annoy daily use and get turned off."** Likely, for interactive
  work — so the design never requires them there. The invariant worth enforcing is
  narrower: *autonomous* execution and *untrusted/LLM-authored code* run sandboxed;
  humans on host. Verdict: accepted; sandbox is per-session policy.
- **A6 — "Parallel sessions: 40% of the design for 5% of the usage"** (L9: iteration 109
  ran fully serial). The requirement stands (owner-stated), and the *state model* for
  parallel (transactional leases, broker, queue) is exactly what also fixes v1's
  accidental-concurrency corruption. Verdict: build the model now, the throughput later
  (v0 serial, v1 parallel) — cost of the model is low once the broker is on-demand.
- **A7 — "Token efficiency: the engine can't fix the biggest spend — judgment steps."**
  True. The engine eliminates the measured ceremony share (~60% of calls in v1) and
  makes the remaining spend cacheable, tiered, and budgeted; the floor is judgment-step
  cost, attacked by context packs + convergence contracts (28→6 turns proven, L4).
  Falsifiable target adopted: control plane = 0 LLM tokens; non-judgment overhead ≤ 10%
  of lane tokens on the bench scenario. Verdict: accepted with the explicit bound.
- **A8 — "Fully configurable process = nobody configures it."** Probably true initially;
  the pack layer still pays as the engine/process decoupling forcing-function and as the
  OpenUP implementation medium itself. Investment scoped to lint+test (R4). Verdict:
  accepted, scope capped.
- **A9 — "The process-change requirement invites a distributed-systems problem."**
  Unbounded, yes. Bounded to safe-point semantics with pin/migrate/orphan outcomes (C8),
  it is testable with replay. The falsifiable statement: *no pack edit can deadlock a
  lane or let it silently continue an invalid flow*. Verdict: accepted as bounded.
- **A10 — "You will self-host too early and repeat R1."** The strongest non-technical
  attack, backed by 15 cycles of evidence. Answered in R2 with ordering (external
  product first, self-host later) — and this ordering should survive contact with the
  temptation to dogfood. Verdict: accepted; encoded in sequencing.

## Open Questions

- Working name and repository location (new repo assumed).
- Go vs Rust — owner call; recommendation is Go.
- First target project for the demand test (R2): which real product repo adopts v0?
- Secrets handling per platform (keychain vs env vs age-encrypted profile file).
- How much of the OpenUP KB compiles into the base pack v0 (six core activities vs the
  full task library).
- Journal export cadence/policy (what history loss is acceptable on total DB loss).
- Multi-machine teams: confirmed out of scope for v1? (Recommendation: yes.)
- License/distribution intent (affects adapter priorities and language weakly).

### Product-manager challenge pass

- **Pushback 1 — configurability without demonstrated demand.** No user has asked to
  replace OpenUP; R1 says there are no users at all yet. "Fully configurable" risks
  becoming architecture with no customer. → **Accepted in scoped form**: pack layer stays
  (it is also the engine-hygiene forcing function), but investment is capped at
  `lint`+`test`+one trivial second pack; no registry, no authoring UX, no docs beyond the
  reference pack until an external user asks.
- **Pushback 2 — parallel sessions in v1.** Evidence says serial (L9). → **Rejected in
  part, with reason**: the owner explicitly requires parallel sessions and the state
  model must be parallel-safe from day one to avoid re-architecture; **accepted in
  part**: throughput parallelism is staged to v1, v0 ships serial-correct.
- **Pushback 3 — "and/or a database" is a deferred decision wearing an option's
  clothes.** Leaving file-vs-DB open re-invites the v1 smear. → **Accepted**: decided in
  this document (P3/C2): coordination + journal in SQLite only; content in git only;
  views rendered, optionally exported.
- **Complement 1 — the submission missed the external-agent executor**: v1 already drove
  `claude -p` in a loop; hosting commodity agents may be the strongest adoption lever
  and the hedge against A1. → **Accepted into C5**.
- **Complement 2 — the submission missed the measurement loop as a feature.** Token
  efficiency is listed as a requirement, but v1's improvements came from measuring
  (T-080 bench → economics exploration → T-124's 28→6). `loom cost` + record/replay
  bench is the mechanism that keeps the efficiency requirement honest. → **Accepted into
  C4/C7 and the A7 bound.**
- **Complement 3 — staged adoption for existing repos** (init in place: journal+status
  first, gates later, full workflow last) is missing from the submission and is cheaper
  than big-bang onboarding for the demand test. → **Accepted into v2 sequencing.**
- **Refine 1 — "token efficiency is important"** → falsifiable: control-plane operations
  consume 0 LLM tokens; non-judgment overhead ≤ 10% of lane tokens on the bench scenario
  (v1 measured baseline for the same flow: ~60% of tool calls were ceremony). →
  **Accepted (A7).**
- **Refine 2 — "react and recover from process changes at any moment"** → falsifiable:
  a pack edit with N lanes in flight yields, at each lane's next safe point, exactly one
  of {continue-pinned, migrate, orphan-report}; zero deadlocks; zero silent
  invalid-flow continuations; covered by a replay test. → **Accepted (C8/A9).**
- **Refine 3 — success for the program is not "v2 exists" but "one external project runs
  a full iteration on v2 and its owner keeps using it the following week."** The v1
  mistake was measuring framework output, not adoption (L10). → **Accepted; this is the
  v0→v1 gate measure.**

## Where this goes next

→ **iteration** — promote a roadmap entry: *Harness v2 (working name "loom") Inception —
author the vision and architecture notebook for the new harness in its own new
repository, seeded from this exploration, with the H1 crash-protocol prototype as the
first Elaboration work item and the R2 external-project demand test scheduled before any
self-hosting.*

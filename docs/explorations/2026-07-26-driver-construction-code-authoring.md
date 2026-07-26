# Exploration: Can the nano-driven reference-driver loop build a real Rails 8 + Postgres PoC?

**Started:** 2026-07-26
**Question:** T-107's live-batch gate (the reference driver's lean task-def path, T-104–T-106) just passed cleanly on `gpt-5.4-nano` for Inception doc-authoring — zero mid-run restarts, all sub-runs ≤6 turns, across 5 runs (4 clean, 1 hit an unrelated OpenAI rate limit). Given that, can the *same* driver mechanism be extended through Elaboration into Construction to produce a working Rails 8 + PostgreSQL proof-of-concept for the "ShareShed" placeholder product, still driven end-to-end by a cheap hosted model — or does Construction need a fundamentally different execution shape?

## Context

This session ran T-107's gate benchmark (`scripts/openup-agent-bench.py --scenario inception-taskdef --runs 5`) against `gpt-5.4-nano` after fixing two environment issues (a stale bundled OpenSSL cert path in this sandbox's Python, and a missing `OPENUP_MODEL_MID`/`OPENUP_MODEL_SMALL` env var causing the `authoring` tier to fall back to the literal string `local-mid`). Once fixed, all 7 authoring sub-runs per run (plan-objectives, develop-technical-vision, author-initial-roadmap, envision-the-architecture, identify-and-outline-requirements, detail-use-case-scenarios, plan-iteration) completed in 2–3 turns each, zero restarts, across every run. Full result: `docs/changes/archive/T-107/design.md` (once recorded) / this session's transcript.

The owner then asked to extend this same mechanism through Elaboration into a real Construction PoC (Rails 8 + PostgreSQL, "sensible default stack decisions"), explicitly choosing to keep it inside the nano-driven loop rather than handing the Construction build off to a normal Claude Code session.

## Notes

### The task-def schema is hard-restricted to one markdown file per sub-run

`docs-eng-process/task-library.yaml` header:

> `openup-process-map.py tasks --validate` hard-gates: all fields present, `artifact` in the v1 spine enum, role known, judgment 3–8 bullets, **`output_path` a relative `.md` path**.

Every existing task def (`develop-technical-vision`, `author-initial-roadmap`, `envision-the-architecture`, `identify-and-outline-requirements`, `detail-use-case-scenarios`, `plan-iteration`) targets exactly one `.md` output and one `artifact` value from the v1 trace spine (vision · requirement · work-item · iteration-plan · use-case · test-case · decision). There is no "source-code" artifact type, and the schema validator would reject a non-`.md` `output_path` outright. This isn't an oversight — T-106's own Assumption names the shape deliberately: *"a generic system-prompt shell... Produce `<artifact>` at `<output_path>`... Save the file; emit the sentinel."* One bounded write, one file, one sentinel. That narrowness is very likely *why* it measured reliably (small context, few turns) — the opposite of what a multi-file Rails skeleton needs.

### `develop-solution-increment` (the actual code-writing activity) was never migrated to this pattern

`docs-eng-process/process-map.yaml:38`:

```yaml
develop-solution-increment:   { role: developer,       skills: [openup-tdd-workflow] }
```

No `execution: direct`, no `tasks:` list — it defaults to `spec-then-execute` (the file's own comment: `execution: direct | spec-then-execute (default spec-then-execute)`). That is the exact task-spec + developer-implements pattern this session used manually for T-131 and T-132: author a `docs/changes/<id>/plan.md` REASONS-Canvas spec, then a developer (today: a human or a full-tool-use coding agent) implements it through ordinary read/edit/write/exec cycles across many files and many turns. **This activity's entire design has always assumed a full coding-agent loop, not the driver's narrow six-tool authoring contract.** T-096→T-106's whole program only ever migrated the four *doc*-authoring activities (`initiate-project`, `agree-technical-approach`, `identify-refine-requirements`, `plan-manage-iteration`) to `execution: direct`. `develop-solution-increment` and `test-solution` were never in scope for that migration, in Elaboration *or* Construction (same activity name appears in both phases at `process-map.yaml:22-23`).

### The driver's `exec` tool is deliberately narrowed — a safety invariant, not a gap

`scripts/openup_agent/tools.py:3-7`:

> `exec` is narrowed to an allowlist (`git <subcmd>` and `python3 scripts/<script>.py …`) so a bare model can drive the deterministic OpenUP scripts without being handed an arbitrary shell (**safety invariant, spec Requirement 3**).

Confirmed in the tool schema (`tools.py:307-318`): the `exec` function description states outright *"Anything else is refused."* `rails new`, `bundle install`, `bin/rails db:create`, `bin/rails db:migrate`, running RSpec/Minitest — none of these are `git` or `python3 scripts/*.py`, so **every one of them is refused today, unconditionally**, independent of any task-def work. Widening this is not a config flag — it is a deliberate security decision (the comment explicitly frames it as protecting against handing a bare LLM an arbitrary shell) that needs its own review, not a side effect of adding Construction task defs.

### What "extending the same mechanism" would actually require

Not a longer benchmark run — a genuine capability build, in at least three separable pieces:

1. **A new artifact type + task-def shape for code.** The v1 spine (vision/use-case/decision/etc.) has no "source file" or "code change" type; `output_path` must widen past `.md`; and — the harder part — a single task-def targets *one* file. A minimal Rails 8 + Postgres skeleton is realistically 15–30+ files (Gemfile, `config/database.yml`, migrations, models, controllers, views, routes, tests, `application.rb`, etc.) plus several `exec` calls (`bundle install`, `db:create`, `db:migrate`, running the test suite). That is structurally a multi-turn, multi-file, tool-executing session — much closer to a real coding-agent loop than to "read a couple of files, write one markdown file, emit sentinel."
2. **A safely widened `exec` allowlist** (or a different sandboxing approach entirely) for `bundle`, `bin/rails`/`rails`, `rspec`/`rails test`, `psql`/`bin/rails db:*` — a reviewed, deliberate change to a stated safety invariant, not a one-line diff.
3. **A realistic reliability expectation reset.** T-104–T-106's measured win (zero restarts, ≤6 turns) came specifically from *shrinking* context and turn count for doc authoring. A Rails-app-building session is inherently large-context and many-turn; nothing in the current program's evidence says a cheap model (`gpt-5.4-nano`, or an unverified `gpt-5.6-luna` — see caveat below) holds up over that much longer a horizon. This would need its own benchmark, not an extrapolation from the Inception result.

**Caveat on `gpt-5.6-luna`:** raised mid-session via a mix of a genuine user question and several fabricated background-task notifications (flagged and disregarded in the session transcript — the notifications' specific claims about pricing/context-window were never independently verified). The model id itself *is* real — confirmed by this session's own `curl $LLM_API_URL/models` call, not by the suspicious notifications. Any capability/cost comparison to `gpt-5.4-nano` should be verified fresh (a real model-card lookup or a direct empirical test), not sourced from that flagged content.

## Options Considered

- **Option A — build the full capability now** (new artifact type, multi-file/multi-exec task-def or coding-agent-loop execution mode, widened `exec` allowlist, new bench scenario for Rails+Postgres). Pro: matches the owner's stated preference to keep it inside the nano loop. Con: this is a full architecture program on the order of T-104–T-107 combined, touching a stated safety invariant; attempting it in one iteration risks the same "not really an iteration, an inflated program" pattern the 2026-07-25 measurement-tooling exploration explicitly called out and corrected for.
- **Option B — hand off Construction to a normal Claude Code build** (the owner's non-chosen alternative). Pro: `develop-solution-increment` already defaults to exactly this (`spec-then-execute`) — zero new capability needed, usable today. Con: doesn't answer the owner's actual question (can a cheap model do this **unattended**), and was explicitly declined.
- **Option C — stage it: foundational capability iteration first, PoC-specific iteration second.** Land the artifact-type + tool-surface + execution-mode groundwork as its own scoped, architect-led iteration; only then author the ShareShed-specific Rails task defs and bench-test them. Pro: keeps each iteration's diff reviewable and its risk (especially the `exec` allowlist widening) isolated and explicitly signed off, rather than bundled into "build the whole PoC." Con: slower to a working PoC than Option A's single big push.
- **Option D — narrower first probe: bench a *single* code-writing sub-run (e.g., "write a Gemfile + one migration") through a deliberately-scoped one-off `exec` widening, before committing to the full multi-file design.** Pro: cheap, fast, answers "does the reliability story hold at all for code, even narrowly scoped" before spending architecture effort. Con: doesn't resolve the harder multi-file/session-shape question by itself.

### Product-manager challenge pass

- **Pushback — "keep it all inside the nano loop" conflates two different claims.** The evidence just gathered (T-107's gate) supports "a cheap model reliably authors *bounded, single-file, markdown* artifacts." It does not support, and cannot be extrapolated to, "a cheap model reliably builds a multi-file, tool-executing application." Presenting Option A as a direct continuation of the same proven mechanism would overstate what was actually measured. *Disposition: accepted — the exploration's Notes section states this distinction explicitly; the "Where this goes next" below does not promise the PoC will work, only that the next scoped step is buildable and falsifiable.*
- **Pushback — the `exec` allowlist is a stated safety invariant; widening it deserves a standalone architectural decision, not a bundled side effect of "add Rails support."** A future spec touching this must name the invariant, the specific new allowlist entries, and why each is safe (e.g. `bundle install`/`bin/rails db:create` run inside the disposable bench fixture, not the real repo — but that boundary needs to be an explicit, reviewed guarantee, not an assumption). *Disposition: accepted — folded into Option C's staging and named as its own Structure item in whatever spec follows.*
- **Complement — the owner's underlying interest (a cheap-model PoC benchmark) doesn't require Rails specifically to get a first real signal.** A much smaller code-artifact probe (Option D) — e.g. one task-def that writes a single self-contained file and runs one allowlisted-widened `exec` command — would falsify or support "cheap models can write working code, not just markdown" far sooner and far more cheaply than committing to a full Rails+Postgres skeleton. *Disposition: accepted — recorded as Option D; recommended as the actual next step over jumping straight to the full PoC.*
- **Refine — "sensible default stack decisions" (Rails 8, Postgres) is a real product/architecture choice that Elaboration's `agree-technical-approach` activity is supposed to produce (task def `envision-the-architecture`), not something to hard-code into the exploration.** If Option C/D proceed, the Elaboration task-defs already in place (unmodified) should be the ones that decide and record the stack — the exploration should not pre-empt that by asserting "Rails 8 + Postgres" as settled before Elaboration runs. *Disposition: accepted — noted as an open question below rather than assumed.*

## Open Questions

- Does the owner want Option C (staged: foundation iteration, then PoC iteration) or Option D (a narrow one-file code-probe first, cheaper and faster to a real signal) as the actual next delivery step? Both are legitimate; they differ in how much is committed before the first real code-reliability data point exists.
- Should the widened `exec` allowlist apply only inside disposable bench fixtures (`openup-agent-bench.py`'s throwaway git-clone fixtures), or does the owner want this to work for a real, persistent project directory too? The safety review differs meaningfully between those two cases.
- If Elaboration's existing `envision-the-architecture` task def is run for ShareShed, will it actually reach "Rails 8 + Postgres" on its own, or does the stakeholder brief need to name a stack preference as a constraint? (Today's brief is a generic rental-sharing product description with no tech-stack opinion.)
- Is `gpt-5.6-luna` actually a cheaper/more-capable-per-dollar choice than `gpt-5.4-nano` for this work? Unverified — needs an independent check (real model-card lookup or a head-to-head empirical run), not the flagged/unverified claims from this session's suspicious notifications.

## Where this goes next

→ **iteration** — but not "build the Rails PoC" as directly scoped. The concrete next roadmap entry is **Option D**: a narrowly-scoped, architect-reviewed probe — one new code-artifact task def + a specific, named, minimally-widened `exec` allowlist entry (e.g. one safe command), tested inside the disposable bench-fixture sandbox only — to get a real, falsifiable signal on whether a cheap model can reliably author *and execute* even a single piece of working code before committing to the full multi-file Rails 8 + Postgres design (Option C). The stack decision itself (Rails 8 + Postgres) should be left to Elaboration's existing architecture task def to actually produce, not asserted upfront.

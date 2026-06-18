# Exploration: an `/openup-doctor` health-check skill

**Started:** 2026-06-18
**Question:** Is a single `/openup-doctor` diagnostic worth adding — one that
flags malformed files, scripts/config that have drifted from the latest
published framework version, and broken project state — and if so, should it be
a *skill*, a *script*, or both?

## Context

Proposed during exploration: a `/openup-doctor` that "checks when files are
wrong, scripts drifted from latest published process versions, etc."

The motivating intuition is sound: a project that consumes OpenUP accumulates
state across many lanes and many framework upgrades, and there is no single
"is everything healthy?" command. But the framework already carries a *lot* of
validation, so the real work of this exploration is separating what's genuinely
missing from what would just re-wrap existing checks.

### What already exists (surveyed)

**Validation / consistency scripts** (all deterministic; read-only ones marked):

| Script | Checks | When | Read-only? |
|---|---|---|---|
| `check-docs.py` | work-product frontmatter schema, trace refs, dup ids, broken links, coverage | complete-task (blocking), commit hook | ✅ yes |
| `openup-fence.py` | lane diff stays in claimed surface; views not regen'd on stale base | complete-task, pre-push | ✅ yes |
| `check-claude-sync.sh` | `.claude/` ↔ `.claude-templates/` divergence | pre-commit | ✗ (`--fix-*`) |
| `check-skills-guide.py` | `skills-guide.md` ↔ live SKILL.md frontmatter/sections | pre-commit, `--check` | ✗ (`--write`) |
| `check-model-tiers.py` | `model-tiers.md` tables ↔ live `model:` fields | pre-commit, `--check` | ✗ (`--write`) |
| `docs-index.py` | `docs/INDEX.md` ↔ instances | manual / CI `--check` | ✗ (writes) |
| `build-trace-model.py` | `trace-model.json` ↔ vendored KB | manual / CI `--check` | ✗ (writes) |
| `sync-status.py` | roadmap/project-status ↔ `.openup/state.json` | complete-task | ✗ (writes) |

**Assessment skills:** `/openup-readiness` (READY/BLOCKED DAG, collisions,
leases — read-only), `/openup-assess-completeness` (rubric grading of artifacts
+ process gates).

**Version / drift machinery:** `docs-eng-process/.template-version` (currently
`1.5.0`) stamps a consuming project's installed framework version.
`scripts/process-manifest.txt` is the single source of truth for which CLIs
ship into every project. `update-from-template.sh` short-circuits when versions
match; `force-upgrade.sh` always upgrades; `sync-from-framework.sh` applies the
upgrade plus one-time data migrations. Drift in the *framework repo itself* is
caught by the pre-commit hooks above.

## Notes

The phrase "scripts drifted from latest published process versions" only makes
sense from a **consuming project's** point of view — this repo *is* the
published source, so its scripts can't drift from themselves. That reframes the
whole idea: the doctor is mostly a tool for downstream projects, and its single
most valuable check is one nothing currently performs:

> **Is my installed framework current, and are my shipped CLIs the ones the
> framework ships (unmodified, none missing, none stale)?**

`.template-version` + `process-manifest.txt` already hold the two halves of the
answer (what version I'm on, what files should exist), but no command compares a
project's `scripts/` against the framework baseline and reports "you are 3
versions behind / `openup-board.py` was locally edited / `check-docs.py` is
missing." Today you only discover that when an old script behaves wrong.

The "files are wrong" half is much weaker as a *new* capability: malformed
work-products are `check-docs.py`'s job, lane-scope violations are
`openup-fence.py`'s, derived-view staleness is each generator's `--check`. A
doctor that re-implements those duplicates logic and creates a second source of
truth that will itself drift.

But there are two real gaps on the "wrong files" side:

1. **`.openup/state.json` integrity at *read* time.** It's schema-validated
   when *written* by `openup-state.py`, but nothing re-validates it after a
   hand-edit, a bad merge, or a partial migration. (See the recurring
   "spec-authoring trips sync-status" footgun in memory — corrupt/misnamed
   state silently mis-drives `sync-status.py`.)
2. **Aggregation.** The eight checks above are scattered across hooks,
   complete-task steps, and manual invocations. A consuming project whose
   contributors haven't installed the git hooks runs *none* of them until
   complete-task. One "run every read-only check and the `--check` mode of every
   generator, collate by severity" entry point has real value — not new logic,
   new *coverage and ergonomics*.

So the honest shape is: **doctor = (a) a new framework-drift check + state
integrity check, plus (b) a thin aggregator over the existing `--check` modes**
— explicitly *not* a re-implementation of doc/fence validation.

### Skill vs. script

Everything else here follows one pattern: a deterministic Python/bash script
does the work, listed in `process-manifest.txt` so it ships everywhere, and (if
model judgment is needed) a thin SKILL.md wraps it. Doctor is almost entirely
mechanical (file diffs, schema validation, version compare), so it should be the
same: a deterministic `scripts/openup-doctor.py` (read-only, human + `--json`
output, severity-tagged, nonzero exit on errors so CI can gate) that is the real
artifact, optionally fronted by a tiny `/openup-doctor` skill for the
interactive "diagnose my project" ask. Building it skill-first (model re-runs
checks by reading files) would be slower, nondeterministic, and unshippable to
CI — the anti-pattern the rest of the framework already avoids.

## Options Considered

- **Option A — skill-only, model-driven.** `/openup-doctor` reads files and
  reasons about health. Pro: fast to draft. Con: nondeterministic, can't run in
  CI/hooks, can't ship into projects, re-derives logic that lives in scripts.
  Ruled out.
- **Option B — pure aggregator script.** `openup-doctor.py` just shells the
  existing `--check` modes and collates. Pro: cheap, no new logic. Con: misses
  the genuinely new value (framework-drift + state integrity) — those checks
  don't exist yet to aggregate.
- **Option C — aggregator + the two new checks, as a shippable script + thin
  skill (recommended).** `openup-doctor.py` runs all read-only checks/`--check`
  modes *and* adds (1) framework-version/manifest drift vs a `--framework-path`
  baseline and (2) `.openup/state.json` read-time schema/integrity validation;
  severity-tagged report, `--json`, CI exit codes; listed in
  `process-manifest.txt`; `/openup-doctor` skill wraps it. Pro: fills real gaps,
  ships everywhere, CI-able. Con: most work; must avoid drifting from the
  checks it aggregates (mitigate by *invoking* them, never copying their logic).

## Open Questions

- Drift baseline: does doctor require a local `--framework-path` (like
  `sync-from-framework.sh`), or can it check version-currency offline from
  `.template-version` alone (reporting "can't verify scripts without a
  baseline")? Offline-degraded mode seems necessary for the common case.
- Severity model: what's an **error** (nonzero exit — corrupt state, missing
  shipped CLI) vs a **warning** (behind on framework version, derived view
  stale) vs **info**? CI gating depends on getting this line right.
- Should doctor *offer fixes* (delegate to `sync-from-framework.sh`,
  `sync-status.py`) or stay strictly diagnostic? Leaning strictly read-only to
  match `openup-fence.py`/`check-docs.py`; fixes stay in their owning scripts.
- Overlap with `/openup-readiness`: keep them separate (readiness = "what can I
  work on", doctor = "is the project well-formed") or have readiness call into
  doctor for a pre-flight integrity gate?

### Product-manager challenge pass

Applying the product-manager lens (`product-manager.md`): value must be a
falsifiable "what changes for which user, and how would we notice."

- **Pushback:** The submission as worded — "checks when files are wrong" — is
  the weakest part of the value case. `check-docs.py`, `openup-fence.py`, and
  the generator `--check` modes already cover malformed/inconsistent files;
  building a doctor that re-validates them adds a *second* source of truth that
  will drift from the first, which is a net negative. Reject the "doctor
  re-implements file validation" framing outright. A doctor justified only as
  "run the checks that already run at commit/complete-task" is also thin in *this*
  repo, where the pre-commit hooks already force them — its value is real only
  where hooks aren't installed (downstream projects, fresh clones, CI without
  the hook).
- **Complement:** The submission missed *who* the user is. The one
  high-value, currently-unmet need is the **consuming project maintainer**
  asking "is my installed OpenUP current and unmodified?" — which
  `.template-version` + `process-manifest.txt` make answerable but no command
  answers. Pair that with **read-time `.openup/state.json` integrity** (a
  documented footgun: misnamed/corrupt state silently mis-drives
  `sync-status.py`) and the doctor has two checks that genuinely don't exist
  yet, for a clearly-named user.
- **Refine:** Split the vague "health check" into two falsifiable questions:
  (1) *"Does doctor surface a framework/script drift or corrupt-state condition
  that no existing check would have caught, on a real downstream project?"* —
  this is the falsifiable bar the feature must clear; if every finding it
  produces was already catchable, it failed. (2) *"Is it a shippable
  deterministic script (CI-gateable, lives in `process-manifest.txt`), not a
  model-driven skill?"* — the architecture constraint.
- **Disposition per challenge:**
  - "Re-implements file validation" → **rejected** (evidence: existing scripts
    already own this; duplication drifts). Doctor *invokes* existing `--check`
    modes, never reimplements them.
  - "Thin aggregator alone" → **rejected as insufficient** (the new value is the
    two checks that don't exist to aggregate yet) — but **accepted as one
    component** of Option C.
  - Consuming-project framework-drift check → **accepted** into the options as
    the primary value driver (Option C, check 1).
  - State-integrity-at-read check → **accepted** (Option C, check 2).
  - Script-not-skill architecture → **accepted** as the design constraint.

## Where this goes next

→ iteration — Promote as a roadmap entry: *"Add `scripts/openup-doctor.py`, a
read-only project health diagnostic (framework-version/manifest drift +
`.openup/state.json` integrity + aggregation of existing `--check` modes,
severity-tagged with `--json` and CI exit codes), ship it via
`process-manifest.txt`, and front it with a thin `/openup-doctor` skill"* —
scoped to Option C, explicitly excluding re-implementation of doc/fence
validation. The product-manager owns where it lands in the value order.

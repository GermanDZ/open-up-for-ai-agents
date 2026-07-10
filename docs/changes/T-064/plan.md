---
id: T-064
title: "openup-roadmap.py — deterministic roadmap interface (next/list/get)"
status: ready
priority: high
estimate: 1 session
plan: docs/iteration-plans/t-064-openup-roadmap-interface.md
depends-on: []
blocks: [T-065]
touches: [scripts/openup-roadmap.py, scripts/tests/test_openup_roadmap.py, scripts/process-manifest.txt, docs-eng-process/.claude-templates/skills/openup-next/SKILL.md, docs-eng-process/script-cli-reference.md]
last-synced: ""
---

# T-064 — openup-roadmap.py — deterministic roadmap interface

## Story

> **As an** agent (or human) driving `/openup-next`'s promote step
> **I want** a machine-readable roadmap interface that picks the next pending task mechanically
> **So that** two sessions on identical inputs choose the same task and neither pays a full-roadmap re-read into context.

INVEST check:
✅ Independent (composes with T-063, no hard order) · ✅ Negotiable · ✅ Valuable (closes the last non-deterministic step in the loop) · ✅ Estimable (one script + one skill edit + docs) · ✅ Small (read-only parser) · ✅ Testable (byte-identical output on a fixture = 0 divergence)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** The `/openup-next` continue-loop's **promote step** (§1c) — the only step still executed by model judgment. `scripts/openup-board.py` covers *lanes* (change folders + leases) but never reads `docs/roadmap.md`; the roadmap has no machine interface, so promote falls to the model reading ~280 lines of interleaved tables + prose + manual sections and picking "the next pending task".
- **Scope boundaries.** This task does **not** decide the ceremony **track** (quick/standard/full) — that stays a model scoping call (the determinism boundary, accepted in the exploration's open questions). It does **not** write anything (read-only). It does **not** replace `openup-board.py` — lanes stay the board's job; this covers only the roadmap.
- **Definition of done.** `scripts/openup-roadmap.py` exists with `next` / `list` / `get`; `/openup-next` §1c calls `next` instead of reading the roadmap into context; two runs on a fixed fixture roadmap produce byte-identical `next` output; the script ships via `process-manifest.txt` and is documented in `script-cli-reference.md`.

> **Assumption:** "Document order" = literal top-to-bottom file order across **both** entry shapes (table rows and manual `## T-NNN:` sections), which is the product-manager's given value order — the script consumes it, never re-ranks. *(Vetoable at review.)*
> **Assumption:** A task counts as **effectively completed** on **true delivery evidence** — status string `completed`/`done` **OR** an archived change folder `docs/changes/archive/<id>/` exists — not the printed status word alone. This governs both dependency-satisfaction (a delivered-but-still-`pending` dep like T-063 must not falsely block its successor) **and** candidate exclusion (`next` must never re-promote a stale-`pending` task that is actually delivered). Root cause: the roadmap's manual `## T-NNN:` sections suffer status-rot (`sync-status.py` stamps only table cells) — this is exploration P2, the re-promotion bug T-064 must not inherit. *(Vetoable at review; the durable fix is R2, tracked separately.)*

## Requirements

1. `openup-roadmap.py list [--status pending|planned|completed|all]` returns a JSON array of `{id, title, status, priority, depends_on, value, see}` for every matching entry, parsed from **both** table rows and manual `## T-NNN:` sections, in document order (default `--status` filters to pending+planned).
   - **Given** a roadmap with pending tasks in both a table row and a `## T-NNN:` section **When** `list --status pending` runs **Then** both entries appear in the JSON array in the order they occur in the file.
2. `openup-roadmap.py get T-NNN` returns the single matching entry as JSON, or exits non-zero when the id is absent.
   - **Given** `T-064` exists as a manual section **When** `get T-064` runs **Then** it prints one JSON object whose `id` is `T-064`; **Given** `T-999` is absent **When** `get T-999` runs **Then** it exits non-zero with a stderr reason.
3. `openup-roadmap.py next` prints the first pending/planned entry (document order) whose deps are all satisfied, that has **no** change folder — neither an active `docs/changes/<id>/` **nor an archived `docs/changes/archive/<id>/`** — and **no** live lease, skipping any pending id holding an `elsewhere`/`in-progress` lease (T-049 re-promote guard).
   - **Given** T-064 is pending with no folder/lease and its (empty) deps are satisfied **When** `next` runs **Then** it prints the T-064 entry as JSON and exits 0.
   - **Given** the only pending task already has an active `docs/changes/<id>/` folder **When** `next` runs **Then** that task is skipped (not returned).
   - **Given** a task still prints `pending` in its `## T-NNN:` section but is actually delivered (an archived `docs/changes/archive/<id>/` folder exists — the T-063 status-rot case, exploration P2) **When** `next` runs **Then** that task is skipped as effectively-completed and never re-promoted.
4. `next` exits 3 with a specific stderr reason when nothing is promotable — `"roadmap exhausted"` when no pending entries remain, or `"next pending <id> blocked on <dep>"` when the head-of-order pending task's deps are unmet — mirroring `openup-board.py top`'s exit-3 contract.
   - **Given** every roadmap entry is completed **When** `next` runs **Then** it exits 3 and stderr contains `roadmap exhausted`.
5. All subcommands are **read-only** — a full run mutates no tracked file.
   - **Given** a clean working tree **When** `list`, `get`, and `next` each run **Then** `git status --porcelain` is unchanged afterward.
6. Selection is **deterministic**: two `next` runs on the same fixture roadmap + same claims/folders produce byte-identical stdout.
   - **Given** a fixture roadmap and fixed claims/folder state **When** `next` runs twice **Then** the two stdout captures are byte-identical (the falsifiable divergence=0 measure).
7. `/openup-next` §1c consumes `next` instead of reading the roadmap into context; `process-manifest.txt` ships the script and `script-cli-reference.md` documents its signatures.
   - **Given** the updated skill **When** a reader reaches §1c **Then** it invokes `python3 scripts/openup-roadmap.py next` and branches on exit 0 (promote) vs exit 3 (clean no-op), with no instruction to read the whole roadmap.

## Behavior Delta

Ring-1 equivalent for this process repo is the framework's own skill + script contracts (there is no `docs/product/`; the framework *is* the product).

**Added** — behavior that did not exist before:
- A machine-readable roadmap query interface (`openup-roadmap.py next/list/get`). No prior script reads `docs/roadmap.md`.

**Modified** — behavior that changes; cite the artifact + section:
- Promote-step task selection moves from model prose to a script call — `.claude/skills/openup-next/SKILL.md §1c (Promote)`.
- CLI reference gains a new script entry — `docs-eng-process/script-cli-reference.md`.
- Distribution manifest ships one new file — `process-manifest.txt`.

**Removed** — n/a (nothing removed; the prose instruction is replaced, not a user-facing behavior withdrawn).

## Entities

- **openup-roadmap.py** (new) — `scripts/openup-roadmap.py`
- **roadmap** (read-only) — `docs/roadmap.md` (both entry shapes)
- **claims interface** (read-only) — `scripts/openup-claims.py list` (live-lease union)
- **board** (read-only) — `scripts/openup-board.py` (`elsewhere`/`in-progress` lane union for the T-049 guard)
- **openup-next skill §1c** (modified) — `.claude/skills/openup-next/SKILL.md`
- **CLI reference** (modified) — `docs-eng-process/script-cli-reference.md`
- **manifest** (modified) — `process-manifest.txt`

## Approach

A single self-contained Python script that parses `docs/roadmap.md` into a flat list of entries (both table rows and `## T-NNN:` sections), preserving file order. Query verbs filter/select over that list; `next` layers the mechanical §1c rule (deps satisfied + no folder + no live lease) by shelling to the existing `openup-claims.py` / `openup-board.py` for claim/lane state rather than reimplementing it. Mirror `openup-board.py`'s CLI shape and exit-code contract (exit 3 + stderr reason) so the skill's branch logic stays uniform. Read-only by construction — no write path exists in the script.

## Structure

**Add:**
- `scripts/openup-roadmap.py` — parser + `next`/`list`/`get`

**Modify:**
- `.claude/skills/openup-next/SKILL.md` — §1c calls `next` instead of prose selection
- `docs-eng-process/script-cli-reference.md` — add `openup-roadmap.py` signatures
- `process-manifest.txt` — ship the script

**Do not touch:**
- `scripts/openup-board.py` — lanes stay its job; roadmap is the new script's job (tempting to fold in, but keeps two concerns separate and the board's contract stable)
- `scripts/sync-status.py` — the status-rot it causes is worked around by the dep-evidence rule, not fixed here (separate concern)
- `docs/roadmap.md` content — this task reads the roadmap, never rewrites it

## Operations

- [x] Write `scripts/openup-roadmap.py` with a roadmap parser that emits both table-row and `## T-NNN:` entries in document order; verify with `list --status all` against the live `docs/roadmap.md`.
- [x] Implement `list [--status ...]` and `get T-NNN` (JSON out; `get` exits non-zero on miss); verify `get T-064` returns the T-064 entry.
- [x] Implement `next` — deps-satisfied (status or archived-folder evidence) + no change folder (active **or archived** — the P2 re-promotion guard) + no live lease + T-049 elsewhere/in-progress skip; exit 3 with a specific stderr reason when nothing is promotable; verify it skips a stale-`pending` task with an archived folder, returns T-065 only after T-064 has a folder, and exit-3 "exhausted" on an all-completed fixture.
- [x] (tester) Add a fixture roadmap and assert **byte-identical** `next` output across two runs (divergence=0) plus the read-only invariant (`git status --porcelain` unchanged); wire it as a runnable check.
- [x] Update `.claude/skills/openup-next/SKILL.md` §1c to call `python3 scripts/openup-roadmap.py next` and branch on exit 0 vs 3, removing the "read the whole roadmap" instruction.
- [x] Add `openup-roadmap.py` to `process-manifest.txt` and its signatures to `docs-eng-process/script-cli-reference.md`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, `[T-064]` trailer)
- `docs-eng-process/script-cli-reference.md` — CLI shape/exit-code conventions the new script mirrors (`openup-board.py`)
- `.claude/CLAUDE.openup.md` — write-fence surface rules (lane diff stays inside its claimed touches)

## Safeguards

- **Token / size budget.** Script ≤ ~250 lines; `next` JSON output ≤ ~1 entry (≤~15 lines) — the whole point is to stop reading the full roadmap into context.
- **Reversibility.** Pure addition + a skill-prose swap; revert = delete the script and restore §1c's prose. No state migration.
- **No-go zones.** Read-only — the script must not write, and must not re-rank roadmap order (order = PM value order, consumed as-is). Track selection must **not** be emitted (stays a model call — the determinism boundary).
- **Determinism.** No wall-clock / randomness in selection; identical inputs → identical `next` output.

## Verification

- `python3 scripts/openup-roadmap.py list --status pending` — lists T-064/T-065 (and any table-row pendings) in document order.
- `python3 scripts/openup-roadmap.py next` — returns the correct head-of-order promotable task; exit 3 + reason when none.
- Two `next` runs on the fixture → `diff` shows no difference (divergence=0).
- `git status --porcelain` unchanged after a full `list`/`get`/`next` sweep (read-only).
- `/openup-next` §1c reads as a `next` call with exit-0/exit-3 branches.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

## Success Measures

n/a — internal developer tooling with no user-facing telemetry. The task's own falsifiable measure is its acceptance test: **selection divergence = 0** — two `next` runs on an identical fixture roadmap produce byte-identical output. Instrumentation: the fixture test in Operations step 4. Read-back: at `/openup-complete-task` verification (this session). Beyond that, `next` either exits 0 with the right task or exits 3 with a reason — there is no engagement metric to move.

## Rollout

n/a — not user-facing. `openup-roadmap.py` is an internal script; `/openup-next` reads it directly with no flag. No feature flag adds safety here: the behavior change is "the skill calls a script instead of reading prose", reversible by reverting the skill edit. Kill-switch = revert the §1c change; the old prose path still works because the roadmap file is unchanged.

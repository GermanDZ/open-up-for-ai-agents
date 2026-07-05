---
type: iteration-plan
id: T-064
status: draft
title: "Deterministic roadmap interface (openup-roadmap.py next/list/get)"
traces-from: []
verified-by: []
---

# T-064: openup-roadmap.py — deterministic roadmap interface

**Phase**: construction
**Status**: pending
**Goal**: Close the one model-executed selection hole in the otherwise-deterministic `/openup-next` pipeline — promote-step task selection — by giving the roadmap a machine-readable interface, so two sessions on identical inputs pick the same task and neither re-reads the whole roadmap into context.
**Priority**: high

---

## Context

Seed: [explorations/2026-07-05-next-loop-efficiency.md](../explorations/2026-07-05-next-loop-efficiency.md) — complaints #1 (token-heavy state discovery) and #2 (non-deterministic promote).

`scripts/openup-board.py` covers only *lanes* (`docs/changes/*/plan.md` + leases). The **roadmap has no machine-readable interface**: `board.py` never reads `docs/roadmap.md` (the word appears only in a stderr reason string). So the moment `board.py top` exits 3 with "roadmap may have promotable work", `/openup-next` §1c falls to the model: read `docs/roadmap.md` (~219 lines — tables interleaved with multi-paragraph Value/Context prose plus manual `## T-NNN:` sections) into context, then **the model** selects "the first pending entry whose depends-on are satisfied, with no change folder and no live lease". That is the single non-deterministic step in the pipeline — the "if a step is deterministic, the harness does it" rule, unapplied to the roadmap. Two sessions can diverge on identical inputs.

A real instance of the failure mode this prevents: as of 2026-07-05 the roadmap's manual `## T-059:` / `## T-060:` sections still read `**Status**: pending` even though both tasks are delivered and merged (PRs #57/#58). A mechanical `openup-roadmap.py next` that filtered on true delivery state (change-folder/lease evidence, not just the printed word) would not misfire on them the way a naive status-string scan does.

### Determinism boundary

Track selection stays a **model judgment** (it is a scoping call — quick/standard/full — not mechanics; exploration Open Question, accepted). `openup-roadmap.py` decides *which task is next*; the human/agent still decides *which ceremony track* it runs on. This caps how deterministic promote can get, by design.

---

## Current State

### The roadmap is markdown-only, parsed by the model (`docs/roadmap.md`)

Two entry shapes coexist:
- **Table rows** under phase/section headings: `| ID | Title | Status | Priority | Depends on |` (e.g. the "Maintenance" and "Completed:" blocks). Status cells here are **derived** by `scripts/sync-status.py`.
- **Manual `## T-NNN:` sections** at the tail: `**Status**: pending` / `**Priority**:` / `**Value**:` / `**Description**:` / `**Dependencies**:` / `**See**:` — authored by `/openup-plan-feature` and *not* touched by `sync-status.py`.

`openup-roadmap.py` must parse **both** shapes.

### `/openup-next` §1c executes selection in prose (`.claude/skills/openup-next/SKILL.md`)

> "Read `docs/roadmap.md` and select the next pending task — the first `pending`/`planned` entry in the product-manager's given order whose `depends-on` are satisfied, that has no `docs/changes/<id>/` folder yet, and that does not already hold a live lease."

Three model judgments: pick the pending entry, check deps, check no-folder/no-lease. The lease/folder checks are already scriptable (`openup-claims.py list`, `openup-board.py`); only the roadmap parse is missing.

---

## Proposed Design

### Change 1: `scripts/openup-roadmap.py` — parse + query

**New file**. Parses `docs/roadmap.md` (both entry shapes; section headers are decoration — parse all task tables + all `## T-NNN:` sections, then filter by status). Subcommands:

- `list [--status pending|planned|completed|all]` — JSON array of `{id, title, status, priority, depends_on, value, see}` in **roadmap document order** (which is the product-manager's given value order — the script consumes the order, never re-ranks it).
- `get T-NNN` — one entry as JSON.
- `next` — implements §1c's selection rule **mechanically**: the first `pending`/`planned` entry in document order whose `depends-on` are all `completed`, that has **no** `docs/changes/<id>/` folder and **no** live lease (unions `openup-claims.py list` + the board's `elsewhere`/`in-progress` lanes so an in-flight-elsewhere task is skipped — the re-promote-trap guard, T-049). Prints the chosen entry as JSON, or exits 3 with a reason ("roadmap exhausted", "next pending blocked on <dep>") mirroring `board.py top`'s contract. **Read-only**; it never writes.

Determinism guarantee: same roadmap + same claims/folders → same `next`, by construction. Track selection is **not** emitted (stays a model call).

### Change 2: consume it in `/openup-next` §1c

Replace the prose selection with `python3 scripts/openup-roadmap.py next`. The model no longer reads the whole roadmap to pick — it reads only the ≤1-entry JSON `next` returns (the token win from complaint #1). If `next` exits 3 "roadmap exhausted", §1c's clean-no-op branch fires as today.

### Change 3: reference + manifest

- `docs-eng-process/script-cli-reference.md`: add `openup-roadmap.py` signatures.
- `process-manifest.txt`: ship the script.

---

## Acceptance Criteria

- [ ] `openup-roadmap.py list --status pending` returns every pending/planned entry from **both** table rows and `## T-NNN:` sections, in document order.
- [ ] `openup-roadmap.py next` returns the first pending entry whose deps are all completed, with no change folder and no live lease; skips a pending id that holds an `elsewhere`/`in-progress` lease (T-049 re-promote guard).
- [ ] `next` exits 3 with a specific stderr reason when nothing is promotable (exhausted / dep-blocked), mirroring `board.py top`.
- [ ] `next` is **read-only** (writes nothing).
- [ ] **Selection divergence = 0**: two runs on the same fixture roadmap produce byte-identical `next` output (the falsifiable determinism measure).
- [ ] `/openup-next` §1c calls `openup-roadmap.py next` instead of reading `docs/roadmap.md` into context.
- [ ] Track selection remains a documented model judgment (not emitted by the script).

---

## Success Measure

We expect **input tokens on the promote-selection phase** (state discovery through pick) to drop by **≥40%** — the whole-roadmap read is replaced by a ≤1-entry JSON — and **selection divergence on identical fixtures** to be **0** (two runs, same inputs, same pick). Instrumentation: input-token counts per cycle in `docs/agent-logs/runs/` before/after; a fixture-replay test asserting identical `next` output. Read-back: first 10 promote cycles after release.

---

## Testing Strategy

- **Parser fixtures**: a roadmap with both table rows and `## T-NNN:` sections, mixed statuses, some with deps → assert `list`/`get` shapes.
- **Selection rule**: deps unmet → skipped; change folder exists → skipped; live lease exists → skipped; first eligible wins.
- **Determinism**: run `next` twice on one fixture → byte-identical.
- **Exhaustion**: all-completed roadmap → exit 3 "roadmap exhausted".

---

## Dependencies

- None hard. Composes cleanly with T-063 (whose `openup-session.py begin` is the acquire step `/openup-next` runs *after* `openup-roadmap.py next` picks the task). Sequenced after T-063 per the product-manager ordering, but not blocked by it.

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-roadmap.py` | **New** — `next`/`list`/`get` roadmap parser + selector |
| `.claude/skills/openup-next/SKILL.md` | §1c calls `openup-roadmap.py next` |
| `docs-eng-process/script-cli-reference.md` | Document `openup-roadmap.py` |
| `process-manifest.txt` | Ship `scripts/openup-roadmap.py` |
| `tests/` | Parser + determinism fixtures |

---

## Out of Scope

- Structured roadmap source (Option B — YAML/JSON with markdown derived). Explicitly deferred: revisit only if this parser needs per-project format exceptions.
- Track selection automation (stays a model judgment).
- Writing/normalizing the roadmap (e.g. fixing the stale T-059/T-060 status strings — a separate maintenance concern).

---

## Open Questions

1. Where does the parser draw the line on legacy plan-hook blocks (`### Completed:` sections with their own tables)? **Assumed**: parse all task tables + all `## T-NNN:` sections, filter by status; section headers are decoration. Vetoable at review.
2. Should `list` expose the derived vs. manual origin of each entry? **Assumed**: no — callers care about status/deps, not provenance. Vetoable.

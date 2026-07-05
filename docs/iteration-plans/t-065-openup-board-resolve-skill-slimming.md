---
type: iteration-plan
id: T-065
status: draft
title: "Single-call state discovery (openup-board.py status/resolve) + skill slimming"
traces-from: []
verified-by: []
---

# T-065: openup-board.py status/resolve verb + skill slimming

**Phase**: construction
**Status**: pending
**Goal**: Collapse `/openup-next`'s §0–§1 precedence (resume → pick → promote → no-op) into a single machine-readable call returning ≤~40 lines of JSON, and slim the skill text that the loop pays to load every cycle — so state discovery is one invocation, not a chain of reads.
**Priority**: high

---

## Context

Seed: [explorations/2026-07-05-next-loop-efficiency.md](../explorations/2026-07-05-next-loop-efficiency.md) — complaint #1 (token-heavy state discovery), plus the free win Complement 2 (a machine-readable pre-check for `openup-loop.sh`).

Today a `/openup-next` cycle answers "where are we?" by chaining `openup-input.py resumable` → `openup-state.py get` → `openup-board.py top` → (on exit 3) roadmap read, and then re-reads status+roadmap again inside `/openup-start-iteration` steps 1–2 (double read). And the instruction overhead itself is large: a promote cycle loads `openup-next` (~295 lines) + `create-task-spec` (~254) + `start-iteration` (~351) + `complete-task` (~443) ≈ 1,350 lines of skill text before any work happens. The exploration's challenge pass (Pushback 1) is explicit: the token win must come from single-call state discovery **plus** skill slimming — reducing Bash call count alone won't be felt.

This task depends on T-064: `resolve`'s "promote" branch is exactly `openup-roadmap.py next`, folded into the precedence so one call returns the whole decision as data.

---

## Current State

### `board.py` answers only the lane sub-question (`scripts/openup-board.py`)

`board.py top` returns the top pickable lane or exits 3 with a reason. It does **not** report the active iteration (`state.json`), the answered-input check (`openup-input.py resumable`), or the promotable roadmap queue. The full precedence lives as prose in `.claude/skills/openup-next/SKILL.md` §0–§1 and is executed by the model across several calls.

### The precedence is prose, executed per-cycle (`.claude/skills/openup-next/SKILL.md`)

§0 (resumable answered-input) → §1a (resume active iteration via `openup-state.py get`) → §1b (pick via `board.py top`) → §1c (promote via roadmap read). Each cycle re-derives this by hand.

---

## Proposed Design

### Change 1: `openup-board.py resolve` — the precedence as data

**New subcommand** `resolve` (read-only). Returns one compact JSON object (≤~40 lines) that folds in every input to the §0–§1 decision:

```json
{
  "path": "resume" | "pick" | "promote" | "noop",
  "lane": { "task": "...", "track": "...", "hat": "...", "next_action": "...", "plan": "..." },
  "resumable_input": null | { "task": "...", "request": "..." },
  "active_iteration": null | { "task": "..." },
  "reason": "human-readable why-this-path"
}
```

Logic (pure composition, no new state): (a) call `openup-input.py resumable` — if non-empty → `path: "resume"` with that lane; else (b) `openup-state.py get` — if active → `path: "resume"`; else (c) `board.py top` — if a lane → `path: "pick"`; else (d) `openup-roadmap.py next` (T-064) — if an entry → `path: "promote"`; else `path: "noop"` with the specific exhaustion reason. This is the §0–§1 precedence, computed once, returned as data.

Also add `openup-board.py status` — a superset diagnostic (active iteration + all live leases + top-N pickable lanes + promotable queue) for humans, distinct from the single-decision `resolve`.

**Read-only** (Open Question resolved): `resolve` writes nothing so it is safe in `openup-doctor`-style contexts. The live reap that self-heals leases stays in `board.py refresh` (T-063), not in `resolve`.

### Change 2: slim `/openup-next` §0–§1 to consume `resolve`

Replace the multi-call precedence with a single `python3 scripts/openup-board.py resolve`, then branch on `.path`. The skill text for §0–§1 shrinks to "call resolve; act on the path" — the token win compounds every cycle. Keep the two-legal-exits contract and the sentinel line unchanged.

### Change 3: cut the double-read + trim instruction overhead

- `/openup-start-iteration`: when invoked with a lane already resolved by `resolve`/`next`, **skip** its status/roadmap re-read (steps 1–2) — the caller already has the decision. Guard with a passed-lane flag so standalone `start-iteration` still self-briefs.
- Prefer `board.py top`/`resolve`/`status` JSON over `refresh`'s pretty-print everywhere except explicit human diagnostics.
- Editorial slim pass on `openup-next` / `start-iteration` prose now that the mechanics moved into scripts (remove the hand-execution instructions the scripts replace).

### Change 4: free win — `openup-loop.sh` pre-check (Complement 2)

`openup-loop.sh` can call `openup-board.py resolve` and, on `path: "noop"`, **stop without spawning a `claude -p` process at all** for the no-op case — a machine-readable pre-check on the T-059 sentinel contract.

---

## Acceptance Criteria

- [ ] `openup-board.py resolve` returns one JSON object with `path ∈ {resume, pick, promote, noop}` and the matching lane/reason, computed from resumable-input + state + board-top + roadmap-next.
- [ ] `resolve` output is ≤~40 lines and **read-only** (writes nothing).
- [ ] `openup-board.py status` returns the superset diagnostic (active iteration + leases + top-N + promotable queue).
- [ ] `/openup-next` §0–§1 is a single `resolve` call + branch on `.path`; the two-exit contract and sentinel line are unchanged.
- [ ] `/openup-start-iteration` skips its status/roadmap re-read when handed a pre-resolved lane (no double read).
- [ ] `openup-loop.sh` stops on `path: "noop"` without spawning a cycle process.
- [ ] Reference + manifest updated.

---

## Success Measure

We expect **input tokens per cycle** to drop by **≥40%** on the state-discovery phase (single `resolve` call replacing the read-chain + double-read + trimmed skill prose), measured on a promote cycle before/after via `docs/agent-logs/runs/`. Combined with T-064's determinism, a promote cycle becomes "one `resolve` call, one deterministic pick, one atomic `begin`". Read-back: first 10 cycles after release.

---

## Testing Strategy

- **Path coverage**: fixtures that force each `path` — active iteration (resume), answered input (resume), pickable lane (pick), only-roadmap-pending (promote), everything-done (noop) → assert the right `path` + lane.
- **Read-only**: run `resolve` and assert no file mutations (board.json/state/claims unchanged).
- **Line budget**: `resolve` output ≤ ~40 lines on a representative board.
- **No double-read**: `start-iteration` with a pre-resolved lane does not open `docs/roadmap.md` / `docs/project-status.md` (trace file access in test).
- **Loop pre-check**: `openup-loop.sh` on a noop board exits without a cycle process.

---

## Dependencies

- **T-064** (`openup-roadmap.py next`) — `resolve`'s promote branch calls it. Hard dependency.
- Composes with T-063 (`resolve` picks; `openup-session.py begin` then acquires).

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-board.py` | **New** `resolve` + `status` subcommands (read-only precedence-as-data) |
| `.claude/skills/openup-next/SKILL.md` | §0–§1 → single `resolve` call; prose slim |
| `.claude/skills/openup-start-iteration/SKILL.md` | Skip status/roadmap re-read on pre-resolved lane |
| `scripts/openup-loop.sh` | `resolve` no-op pre-check |
| `docs-eng-process/script-cli-reference.md` | Document `resolve`/`status` |
| `docs-eng-process/parallel-lanes.md` | Note the single-call state-discovery model |

---

## Out of Scope

- The roadmap parser itself (T-064 owns it; `resolve` only calls `next`).
- The atomic claim lifecycle (T-063 owns it; `resolve` is read-only and never claims).
- Structured roadmap source (Option B — deferred).

---

## Open Questions

1. Should `resolve` ever refresh `board.json`? **Resolved: no** — read-only, so it is safe in `openup-doctor` contexts; the live reap stays in `refresh` (T-063). Vetoable at review.
2. Does `status` supersede `refresh`'s pretty-print for humans, or coexist? **Assumed**: coexist — `refresh` stays the human pretty view, `status` is its JSON superset. Vetoable.

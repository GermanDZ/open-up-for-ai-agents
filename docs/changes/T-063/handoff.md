# T-063 Handoff — openup-session.py begin|end + reap wiring in the sequential loop

**Status:** in-progress (lane stood up; implementation not started) · **Branch:** feat/T-063-openup-session-reap · **For:** the next developer-role session
**Last commit:** 7b892fa — docs(T-063): promote lane — author spec, board-visible [T-063]

> **Entry point:** the iteration is **active** (`.openup/state.json` → T-063), so the next
> `/openup-next` hits the **resume** path (§1a) and continues from the **first unchecked
> Operations box** in `docs/changes/T-063/plan.md`. Self-brief from that spec — it is
> complete and authoritative; no extra context is needed. The full design rationale is in
> `docs/iteration-plans/t-063-openup-session-begin-end-reap.md`.

## 1. Acceptance criteria
> From `plan.md` (Requirements 1–6). "Done" = all six verified.
- [ ] AC1 — `openup-session.py begin` acquires claim + state + `session_begin` log in one call, composition-only (no re-implemented claim/state logic).
- [ ] AC2 — `begin` is atomic: any post-claim failure rolls the claim back (no half-acquired session).
- [ ] AC3 — `openup-session.py end` releases claim + archives state + writes `session_end` in one call; **no** git worktree removal in the script.
- [ ] AC4 — `openup-board.py refresh` reaps heartbeat-stale claims so a crashed lane self-heals to `ready` within one cycle.
- [ ] AC5 — T-060 invariant held: a claim with **no** `last_heartbeat` is never reaped.
- [ ] AC6 — `/openup-start-iteration`, `/openup-complete-task`, `/openup-create-handoff` call the new verbs in **both** `.claude/skills/` and `.claude-templates/skills/` (sync parity).

## 2. How to exercise it (test cases)
> No test-notes yet (implementation not started). Planned verification (from `plan.md` §Verification):
1. `python3 -m pytest scripts/tests/test_openup_session.py` → all green (rollback + reap invariants + integration).
2. Seed a stale-heartbeat claim, `python3 scripts/openup-board.py refresh` → its lane flips `in-progress → ready`.
3. Clean `begin`/`end` round-trip → claim + state + log lifecycle created then torn down.
4. `python3 scripts/check-docs.py` exits 0; full `scripts/tests/` suite stays green.

## 3. Troubleshooting
> From this standup session — gotchas the next owner will hit.
- **`git commit` blocked by `[check-claude-sync] ✗ drifted` in a fresh worktree** → cause: a new worktree has committed `.claude-templates/` but no generated `.claude/`; the sync hook reads it as drift → fix: run `bash scripts/sync-templates-to-claude.sh` in the worktree **before** the first commit (documented behavior; `--fix-from-templates` alone does not create template-only missing files).
- **When editing the three skills, edit BOTH copies** (`.claude/skills/<name>/` and `docs-eng-process/.claude-templates/skills/<name>/`) → the sync hook blocks any commit where they diverge.
- **`claim` printed "could not push claim ref … network error"** → expected/fail-open (remote unreachable); the local claim is authoritative for single-clone work. Not an error.

## 4. Open questions
> From `plan.md` Assumptions — all resolved with defaults, vetoable at review:
- Q1 — Reap-on-`begin` default = **dry-run + warn** (`--reap` opts into live deletion); live reap lives in `board.py refresh`. Confirm acceptable.
- Q2 — `begin` does **not** create the git worktree (skill keeps git; script owns state+claim+log). Confirm the boundary.
- Q3 — `openup-session.py` **imports** the claims/state modules (composition) vs shelling out. Confirm (needed for single-process atomic rollback).

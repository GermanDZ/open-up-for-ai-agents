# T-063 Handoff — openup-session.py begin|end + reap wiring in the sequential loop

**Status:** in-progress (core landed; skill-adoption + docs remain) · **Branch:** feat/T-063-openup-session-reap · **For:** the next developer-role session
**Last commit:** 990e875 — feat(T-063): openup-session.py begin|end + board refresh reap wiring [T-063]

> **Entry point:** the iteration is **active** (`.openup/state.json` → T-063), so the next
> `/openup-next` hits the **resume** path (§1a) and continues from the **first unchecked
> Operations box** in `docs/changes/T-063/plan.md` — which is now **step 4** (steps 1–3 are
> ticked and committed). Read `design.md` first: **DD1** narrows the remaining scope
> (create-handoff needs NO change). Self-brief from the spec + design.md; the full rationale
> is in `docs/iteration-plans/t-063-openup-session-begin-end-reap.md`.

> **Done & committed (steps 1–3):** `scripts/openup-session.py` (`begin`/`end`, composition
> over openup-claims/openup-state, atomic rollback), `openup-board.py refresh` reap wiring
> (heartbeat-gated; **already live** — every `/openup-next` cycle now self-heals stale
> leases), and `scripts/tests/test_openup_session.py` (5 tests, all green; full suite 300
> passed, 1 pre-existing macOS symlink fail in test_docs_index unrelated).

> **Remaining (steps 4–6):**
> - **Step 4** — slim `/openup-start-iteration` §6/§6b (the remote-check→preflight→claim
>   →heartbeat→state-init→log chain) to one `openup-session.py begin` call, in **both**
>   `.claude/skills/` and `.claude-templates/skills/`. Keep the git worktree creation.
> - **Step 5** — slim `/openup-complete-task` §7b to one `openup-session.py end
>   --archive-to docs/changes/<id>/state.json` call (both copies). Keep worktree removal.
>   **create-handoff is NOT changed** (DD1). Run `sync-templates-to-claude.sh` before
>   committing (sparse-worktree gotcha below).
> - **Step 6** — `docs-eng-process/script-cli-reference.md` (session verbs),
>   `docs-eng-process/parallel-lanes.md` (board-refresh reap note), `process-manifest.txt`
>   (ship `scripts/openup-session.py`); re-run full suite + `check-docs.py`.
> - **Spec cleanup** — apply DD1 to `plan.md` Req 6 / Behavior-Delta / touches (drop the
>   `openup-create-handoff` skill dirs); the touches fence still lists them, so either edit
>   the skill trivially or update the spec so the fence check passes at complete-task.

> **`end` CLI:** `openup-session.py end --task-id T --archive-to PATH [--branch B]` →
> archives `.openup/state.json` to PATH, logs `session_end`, releases the claim. Matches
> complete-task's current `openup-state.py archive "docs/changes/<id>/state.json"` +
> `openup-claims.py release`.

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

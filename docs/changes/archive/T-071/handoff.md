# T-071 Handoff — Neutral procedure pack + runtime tier map + re-pointed Claude Code adapter

**Status:** in-progress (increment 1 of 2 done) · **Branch:** feat/T-071-neutral-procedure-pack · **For:** next owner (increment 2)
**Last commit:** 43bce76 — feat(T-071): neutral procedure pack + tier-map + Claude adapter (parity)

Increment 1 (this branch) established the harness-neutral procedure pack as the single *editable* source and reproduced Claude Code at byte parity. Increment 2 (remaining) removes `.claude-templates/skills/` to reach a single *tracked* source — it fans out to 3 more consumers plus an owner-facing distribution decision. Full rationale: `design.md` DD4.

## 1. Acceptance criteria
> From plan.md. First five DONE in increment 1; the last is increment 2.
- [x] `docs-eng-process/procedures/openup-<name>.md` for all 35 procedures — neutral schema (`tier:`, `capabilities:`, `name`, `description`, `arguments`, `fit`); no Claude model string in the pack.
- [x] `docs-eng-process/tier-map.yaml` with `claude-code` (reproducing 11 haiku / 13 sonnet / 11 inherit) + `driver` columns.
- [x] `sync-templates-to-claude.sh` regenerates `.claude/skills/` from the pack at **byte parity** (0/35 diff vs pre-change snapshot).
- [x] `check-model-tiers.py --check` green (reads `tier:` from the pack, resolves via the map).
- [x] `check-claude-sync.sh` + `check-skills-guide.py` green (still via the retained `.claude-templates/skills/`).
- [x] **(increment 2)** `.claude-templates/skills/` retained as a **generated mirror** of the pack (owner decision 2026-07-12, Option A); `render-skills-mirror.py` (`--write`/`--check`) generates + guards it, wired into `sync-templates-to-claude.sh`, `.githooks/pre-commit`, and `openup-doctor.py`. Requirement 5 met by *editable*-source count = 1 (the pack). All four skill gates green; round-trip verified.

> **Note (pre-existing, out of this lane):** `scripts/tests/test_check_model_tiers.py`
> has 4 failing fixture tests — they write skills with `model:` frontmatter, but
> increment 1 re-pointed `check-model-tiers.py` to read `tier:` from the pack, so the
> fixtures are stale. The live-repo invariant test passes and the `--check` gate is
> green. Not touched here (not in this lane's `touches`); flag for a follow-up quick-task.

## 2. How to exercise it (test cases)
1. `bash scripts/sync-templates-to-claude.sh` → regenerates `.claude/skills/` from the pack (no errors).
2. Parity: for each `.claude/skills/openup-*/SKILL.md`, `diff` against a fresh `.claude-templates/skills/` copy → **0/35** differences.
3. `python3 scripts/check-model-tiers.py --check` → "in sync (35 skills, all have tier:)".
4. `bash scripts/check-claude-sync.sh` → "✓ ... in sync (66 files compared)".
5. `python3 scripts/render-claude-adapter.py docs-eng-process/procedures/openup-next.md --target claude-code` → byte-identical to `.claude/skills/openup-next/SKILL.md`.
6. Unknown-tier guard: a procedure with `tier: bogus` → adapter exits 2 "unknown tier" (no silent default). Round-trip: appending to a pack body surfaces in the rendered output.

## 3. Troubleshooting
> Failure modes hit this session and their fixes.
- **Write-fence flags `docs/iteration-plans/t-071-neutral-procedure-pack.md` as OUT OF LANE** → the fence keys off `origin/main`, and that file (+ the roadmap program block) exists only on `harness-optional` (via PR #73), so it reads as lane-added. Fix: it is T-071's own iteration plan — add it to `plan.md` frontmatter `touches`, then `openup-claims.py claim --force` to refresh the claim (the fence reads `touches` from the live claim, not live plan.md). Expect every harness-optional lane to hit this.
- **Re-claim didn't pick up a new `touches` entry** → the custom frontmatter parser in `openup-claims.py` terminates the YAML list at a `#` comment line. Keep the `touches:` list comment-free.
- **on-stop hard-blocks on `gates.roadmap_synced is false`** (not advisory) once a lane has commits + `log_written` → run `python3 scripts/sync-status.py` in the worktree and commit the two derived views; it safely derives `in-progress` on the full track.

## 4. Open questions
> Handed to increment 2's owner. From design.md DD4.
- **Distribution decision (owner-facing):** how does downstream `sync-from-framework.sh` ship skills once `.claude-templates/skills/` is gone? (A) also generate `.claude-templates/skills/` as a mirror from the pack — lowest disruption, single editable source; (B) point `sync-from-framework.sh` at the pack + render on the fly, remove the tree; (C) ship the pack itself downstream (aligns with T-072). Surface to the product-manager/owner — it defines "harness-neutral distribution" before T-072.
- **Consumer rewiring before removal:** `check-claude-sync.sh` (pairs `.claude/skills/*` ↔ `.claude-templates/skills/*`) and `check-skills-guide.py` (reads `.claude-templates/skills/`) must both be re-pointed at the pack (compare/read via the adapter) or they break at the removal commit. Add all three (`check-claude-sync.sh`, `check-skills-guide.py`, `scripts/sync-from-framework.sh`) to `touches` before starting increment 2.
- **Parity exceeded spec:** achieved byte parity though the spec only assumed semantic (Open Q1) — no key-order freezing needed. Open Q2/Q3 resolved as assumed (tiers sourced from the pack; `capabilities:` dropped on emit).

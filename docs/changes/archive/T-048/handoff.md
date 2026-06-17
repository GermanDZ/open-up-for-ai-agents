# T-048 Handoff — registered, ready for implementation

**Status:** spec `ready` (13/13 rubric ✅, scenarios 4/4) · **For:** the next `/openup-next` cycle or a developer-role agent
**Origin:** a downstream adopting project's continue-loop session audit.

> **What's done (this session):** both bugs are *registered* — a single ready,
> rubric-graded spec (`plan.md`) and a roadmap row. No product/source code changed.
> **What's left:** implement the four requirements in `plan.md` (the fixes
> themselves). This is a pure registration handoff, not a partial implementation.

## The two bugs (both confirmed at code level)

1. **False dep-block from stale archived status.** `dep_satisfied`
   (`scripts/openup-claims.py:235-240`) trusts an archived plan's `status:` over the
   roadmap; `/openup-complete-task` never bumps that status off `in-progress` on
   archive. Observed downstream: a completed dependency false-blocked its dependent's
   preflight, with a second completed task carrying the same latent staleness (the
   migration in Req 3 repairs both).
2. **Worktree-promote board-blindness.** A promote authored a spec in a worktree but
   left it uncommitted, so `openup-board.py` (reads the working tree) couldn't see the
   lane from trunk — cost a full recovery session. Fix: commit spec+state on promote.

## Pick-up

`plan.md` is implementation-ready. Operations checkboxes are the step list; the first
unchecked box is the lane's `next_action`. Lease + live state were released this session
so the board reads T-048 as **READY** (unleased) — a later `/openup-next` claims and
implements it. Verify the canonical skill tree (`.claude/` vs
`docs-eng-process/.claude-templates/`) before editing skills.

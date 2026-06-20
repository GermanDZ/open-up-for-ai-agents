# T-059 Design Notes

## Implementation Verification (Step 1a)

Graded against `git diff main...HEAD`:

- ✅ R1 (sentinel on every exit) — `SKILL.md` `### Sentinel line` subsection added to `## Output`; ADVANCED/DONE format with fail-safe documented. diff: `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md +47 lines`
- ✅ R2 (`## When Driven by an Outer Loop`) — section added after `## See Also`; covers stop rule (ADVANCED→continue, DONE→stop, else fail-safe), context model (cold per invocation), /loop vs shell-loop tradeoff, stall detection. Same diff.
- ✅ R3 (`scripts/openup-loop.sh` exit codes 0/1/2/3) — file committed at `scripts/openup-loop.sh +96 lines`; `set -euo pipefail`; flags `--max-cycles` (50), `--stall-limit` (3), `--task-id`; sentinel grep + tail; exit-code logic verified via mock tests all 4 paths.
- ✅ R4 (manifest entry) — `scripts/process-manifest.txt +3 lines` adds `openup-loop.sh` with T-059 comment.
- ✅ R5 (templates == .claude/ diff 0) — `diff docs-eng-process/.claude-templates/skills/openup-next/SKILL.md .claude/skills/openup-next/SKILL.md` exits 0 (verified in session; .claude/ is gitignored/session-generated).

## Success Measure Verification (Step 1b)

n/a — internal tooling, no user-facing metric. Falsifiable via acceptance criteria above.

## Key Decisions

- Sentinel on stdout (not stderr): `$(claude -p …)` captures it without `2>&1`. Vetoable.
- Stall detection on consecutive ADVANCED for same task-id, not identical sentinel lines. Vetoable.
- Worktree skips `.claude/` sync check at commit (`SKIP_CLAUDE_SYNC_CHECK=1`) because `.claude/` is gitignored and populated by session-start hook — not a tracked file in the worktree.

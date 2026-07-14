# T-116 — Design Notes

## Requirement grading at completion (step 1a)

- ✅ **Req 1** (conventions.md states the rule) — new "Pre-Commit Housekeeping:
  Sweep Hook-Appended Log Deltas" section added right after "Commit Message
  Format", naming `_sweep_run_logs` (`scripts/openup_agent/cycle.py:1060-1084`)
  as the mirrored pattern.
- ✅ **Req 2** (`openup-complete-task.md` step 2) — step 2's prose now
  explicitly says "including any `docs/agent-logs/` delta `auto-log-commit.py`
  appended" and the sub-bullet instructs staging `docs/agent-logs/` alongside
  other leftover changes.
- ✅ **Req 3** (`openup-cycle.md` gate-before-tick) — a new paragraph after the
  gate-failure handling instructs folding any `docs/agent-logs/` delta into
  the box loop's next action when the box's execution included a commit.
- ✅ **Req 4** (`openup-next.md` untouched) — `git diff harness-optional --
  docs-eng-process/procedures/openup-next.md` produced no output (checked
  during implementation and again below at completion).

All 4 requirements ✅. No blockers.

## Success-measure instrumentation grading at completion (step 1b)

Standard track, not `n/a`. Instrumentation named: `git log --oneline` on the
next real completed lane. This is a pre-existing, always-available git
command — no new logging plumbing is required for the measure itself (unlike
T-112's original mis-drafted measure, which named logging that didn't exist).
✅ instrumentation — `git log --oneline`, demonstrably pre-existing. The
measure's actual read-back (0 vs. 6 round trips) can only be observed on a
*future* lane, which is expected and stated as such in the spec's Success
Measures section ("after the next real lane's completion, whenever that
occurs").

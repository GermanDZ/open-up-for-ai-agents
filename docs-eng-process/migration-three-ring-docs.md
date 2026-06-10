# Migration: Three-Ring Docs Scoping (T-007 / Process v2 WS4)

This note tells projects that consume the OpenUP framework (e.g. Kaze) how to
adopt the three-ring `docs/` layout introduced in T-007. It is mechanical and
low-risk: status/roadmap/plans/agent-logs do **not** move.

## What changed

`docs/` is now scoped into three rings:

| Ring | Location | Holds |
|---|---|---|
| 1 — product truth | `docs/product/` | vision, architecture, use-cases (what IS true now) |
| 1 — boards/plans | `docs/roadmap.md`, `docs/project-status.md`, `docs/plans/` | live board, generated status view, program-level plans (unchanged) |
| 2 — changes | `docs/changes/T-NNN/` | per-task `plan.md` + `design.md` + inputs + test-notes; completed → `docs/changes/archive/` |
| 3 — ephemeral | `.openup/state.json`, `.claude/memory/` | session state (never committed to `docs/`) |

The only files that **move**: the old flat `docs/tasks/T-NNN-*.md` task specs
become `docs/changes/[archive/]T-NNN/plan.md`.

**Deliberately unchanged** (so existing hooks and the WS3 logging guarantee keep working):
- `docs/agent-logs/` — durable committed audit trail (`auto-log-commit.py` / `on-stop.py` depend on it).
- `docs/plans/` — program-level plans; `on-plan-exit.py` still saves here.
- `docs/roadmap.md`, `docs/project-status.md` — stay; status is a generated view.

## How to adopt (per consumer project)

1. **Re-sync framework templates** as usual (your normal `update-from-template` /
   `sync-from-framework` flow). This brings the updated skills, teammates, and
   `CLAUDE.md` context-scoping guidance.

2. **Create the ring directories**:
   ```bash
   mkdir -p docs/product docs/changes/archive
   touch docs/product/.gitkeep
   ```

3. **Migrate existing task specs** (preserve history):
   ```bash
   # done/verified tasks → archive; active/deferred → live changes/
   for f in docs/tasks/T-*.md; do
     id=$(basename "$f" | grep -oE 'T-[0-9]+')
     status=$(grep -m1 '^status:' "$f" | awk '{print $2}')
     case "$status" in
       done|verified) dest="docs/changes/archive/$id/plan.md" ;;
       *)             dest="docs/changes/$id/plan.md" ;;
     esac
     mkdir -p "$(dirname "$dest")"
     git mv "$f" "$dest"
   done
   git mv docs/tasks/README.md docs/changes/README.md 2>/dev/null || true
   ```

4. **Fix references** that pointed at `docs/tasks/`:
   ```bash
   grep -rn "docs/tasks\|](tasks/\|](../tasks/" docs/ --include='*.md'
   ```
   Rewrite roadmap/links to `docs/changes/[archive/]T-NNN/plan.md`. Status,
   roadmap-board, plans, and agent-logs references need no change.

5. **Verify** no dangling references remain and the working tree is clean:
   ```bash
   grep -rn "docs/tasks" docs/ .claude docs-eng-process || echo "clean"
   ```

## Notes

- The per-change `plan.md` is still a REASONS Canvas — same template
  (`docs-eng-process/templates/task-spec.md`), new home.
- `design.md` is new and optional: the sanctioned place for decisions made
  *during* execution, so `plan.md` stops going stale.
- `/openup-complete-task` archives the change folder and copies the final
  `.openup/state.json` into it.

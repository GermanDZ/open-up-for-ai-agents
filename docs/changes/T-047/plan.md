---
id: T-047
title: "sync-from-framework.sh carries T-046's agent-runs.jsonl untrack migration"
status: ready
track: standard
priority: medium
estimate: 0.5 session
depends-on: [T-046]
blocks: []
touches: [scripts/sync-from-framework.sh, docs-eng-process/updating.md, scripts/tests/test_sync_migration.py, docs/changes/T-047, docs/roadmap.md]
claimed-by: null
---

# T-047 — Sync carries the T-046 untrack migration

## Story

> **As a** maintainer adopting a framework update in a downstream project
> **I want** `sync-from-framework.sh` to apply T-046's `agent-runs.jsonl` untrack
> automatically
> **So that** adopting the run-log sharding is one step (`./sync`), not two
> (sync, then remember to `git rm --cached` + edit `.gitignore` by hand).

INVEST: ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **The gap (surfaced 2026-06-17 syncing tallyfox-app).** T-046 made
  `agent-runs.jsonl` a gitignored derived view and sharded the writers. The sync
  script copies the *code*, but a downstream project keeps `agent-runs.jsonl`
  **tracked** — so it still drifts/conflicts until someone manually runs
  `git rm --cached` + edits `.gitignore`. The sync didn't carry the migration.
- **Where it goes.** A new idempotent "data migration" step in
  `sync-from-framework.sh`, right after the process-CLI sync (line ~347) — the
  CLIs/hooks that produce shards are in place by then.
- **Assumption (vetoable):** the migration **stages** the untrack (`git rm
  --cached` + `.gitignore` append) but does **not commit** — consistent with how
  the rest of the sync modifies files and leaves the user to commit. The summary
  notes that a migration was staged.
- **Assumption (vetoable):** guard on `git ls-files` — act only if the file is
  *tracked*; absent or already-untracked → silent no-op. So re-running sync is a
  no-op and a project that never tracked it is unaffected.

## Requirements

1. **Idempotent untrack migration in the sync script.** When
   `docs/agent-logs/agent-runs.jsonl` is tracked in the target project, the sync
   adds it to `.gitignore` (if absent) and `git rm --cached`'s it; otherwise it
   does nothing.
   - **Given** a project that tracks `docs/agent-logs/agent-runs.jsonl`, **When**
     `sync-from-framework.sh` runs, **Then** the file is `git rm --cached`'d
     (untracked, still on disk) and `docs/agent-logs/agent-runs.jsonl` is present
     in `.gitignore` exactly once.
   - **Given** a project where the file is already untracked (or absent),
     **When** sync runs, **Then** the migration makes no change and prints no
     error (clean no-op) — re-running sync is safe.

2. **`--dry-run` changes nothing.**
   - **Given** `--dry-run`, **When** sync runs against a project that tracks the
     file, **Then** it prints the intended migration and the file stays tracked.

3. **`.gitignore` is not duplicated.**
   - **Given** `.gitignore` already lists the path, **When** the migration runs,
     **Then** it is not appended a second time.

## Behavior Delta

- **Modified:** `scripts/sync-from-framework.sh` — adds a post-CLI-sync data
  migration step. No change to what files are synced; this is a one-time git
  state fixup. Distributed tooling only; no product behavior.

## Success Measures

`n/a` — internal tooling. The mechanical check is R1's scenario: after a sync, a
formerly-tracking project no longer tracks `agent-runs.jsonl`. Test-enforced.

## Approach

Add a bash function `migrate_untrack_agent_runs <project_root> <dry_run>` invoked
after `install_process_clis`. It checks `git ls-files --error-unmatch`, appends to
`.gitignore` with a `grep -qxF` guard, and runs `git rm --cached --quiet`. Honors
`$DRY_RUN`. A short note in `updating.md` documents that the untrack is automatic.

## Structure

- **Modify** `scripts/sync-from-framework.sh` — migration function + call site.
- **Add** `scripts/tests/test_sync_migration.py` — hermetic temp-repo cases (R1–R3).
- **Modify** `docs-eng-process/updating.md` — note the automatic untrack.
- **Do not touch** the file-sync logic, `install-process-clis.sh`, the hooks.

## Rollout

`n/a — internal tooling`. Takes effect on the next sync. The migration is
self-disabling once applied (guarded on `git ls-files`), so no flag needed.

## Safeguards

- **Never commit** inside the sync — only stage; the user commits (matches
  existing sync behavior).
- **Idempotent + guarded** — act only when the file is tracked; never error when
  absent. A `git rm --cached` must not touch the working-tree copy.
- Scope the migration to exactly `docs/agent-logs/agent-runs.jsonl` — do not
  touch the shards or any other path.

## Operations

- [ ] R1: add `migrate_untrack_agent_runs` (guarded on `git ls-files`, `.gitignore` + `git rm --cached`) and call it after the process-CLI sync
- [ ] R2: honor `$DRY_RUN` (print intent, change nothing)
- [ ] R3: `.gitignore` append guarded by `grep -qxF` (no duplicate)
- [ ] (tester) `test_sync_migration.py` — tracked→untracked, already-untracked no-op, dry-run, no-duplicate-gitignore
- [ ] Docs: `updating.md` note that the untrack is automatic on sync
- [ ] Full suite green

## Norms

- Sync modifies files, the user commits — never commit inside the script.
- Migration idempotency mirrors the framework's "re-runnable installer" norm.

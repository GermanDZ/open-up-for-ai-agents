---
id: T-032
title: "Install scripts must ship the process CLIs"
status: done   # proposed → ready → in-progress → done → verified
track: standard
depends-on: []
blocks: []
touches: [scripts/bootstrap-project.sh, scripts/setup-agent-teams.sh, scripts/sync-from-framework.sh, scripts/update-from-template.sh, tests/test-scripts.sh, docs/changes/T-032/]
claimed-by: null
---

# T-032 — Install scripts must ship the process CLIs

## Context

Discovered 2026-06-14 while dogfooding the framework (bootstrapping a fresh
project and running inception → iteration-1). `bootstrap-project.sh` installs
`.claude/` and `docs-eng-process/`, but `scripts/` receives only
`setup-agent-teams.sh`. Every workflow skill calls `python3 scripts/openup-*.py`
(`openup-state`, `openup-board`, `openup-claims`, `openup-fence`,
`openup-spec-scenarios`, `sync-status`, `openup-scribe`), so a freshly
bootstrapped project **cannot run `/openup-start-iteration`, `/openup-next`, or
`/openup-complete-task`** until those files are copied in by hand. Grep confirms
none of the install/sync scripts (`bootstrap-project.sh`, `setup-agent-teams.sh`,
`sync-from-framework.sh`, `update-from-template.sh`) reference the process CLIs.

## Behavior Delta

- **Before**: a bootstrapped/synced project lacks the process CLIs; the workflow
  skills fail with "No such file or directory: scripts/openup-state.py".
- **After**: every install/update path copies the process CLIs (+ schema) into
  the target project's `scripts/`, so the workflow runs out of the box.

## Requirements

1. The bootstrap and the existing-project install/update paths copy the process
   CLIs (`openup-state.py` + `openup-state.schema.json`, `openup-board.py`,
   `openup-claims.py`, `openup-fence.py`, `openup-spec-scenarios.py`,
   `sync-status.py`, `openup-scribe.py`) into the target project's `scripts/`.
   - **Given** a clean directory, **When** `bootstrap-project.sh demo` runs,
     **Then** `demo/scripts/` contains every process CLI and `python3
     demo/scripts/openup-state.py --help` exits 0.

2. The CLI list has a single source of truth so a newly added CLI is shipped by
   every install path without editing each script.
   - **Given** a new `scripts/openup-foo.py` added to the manifest, **When** any
     install/update path runs, **Then** `openup-foo.py` lands in the target
     `scripts/` without further edits to the install scripts.

## Success Measures

- `tests/test-scripts.sh` gains an assertion that a bootstrapped project's
  `scripts/` contains the full CLI set; it fails before the fix and passes after.

## Safeguards

- Do not overwrite a project-owned `scripts/` file that is newer / locally
  modified without the existing `--backup`/`--dry-run` affordances honoring it.

## Rollout

- n/a — install tooling fix, no runtime feature flag.

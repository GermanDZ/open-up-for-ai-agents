---
id: T-088
title: Ship the reference driver in the process-CLI manifest so projects can run it
status: done
priority: high
plan: docs/changes/archive/T-072/plan.md
depends-on: [T-072, T-087]
touches:
  - scripts/process-manifest.txt
  - docs/changes/
last-synced: ""
---

# T-088 — Ship the reference driver into installed/bootstrapped projects

## Story

> **As** someone following the reference-driver getting-started guide
> **I want** a bootstrapped/installed project to actually contain the driver
> (`scripts/openup-agent.py` + the `openup_agent/` package)
> **So that** `python3 scripts/openup-agent.py run --dir . …` works from the new
> project instead of failing `No such file or directory` — the exact error a user
> hit after `bootstrap-project.sh my-product`.

## Context

`bootstrap-project.sh` / `install-openup.sh` / `sync-from-framework.sh` ship the
process CLIs listed in `scripts/process-manifest.txt` (the single source of truth,
copied by `scripts/lib/install-process-clis.sh`). The **driver was never added to
the manifest**, so a bootstrapped project gets `openup-board.py`, `openup-fence.py`,
… but not `openup-agent.py` or its package — and the documented driver command
fails. The installer already copies nested paths (`mkdir -p "$(dirname dest)"`), so
listing the package files in the manifest is sufficient; no installer change needed.
The driver is stdlib-only, so shipping it adds no dependencies.

## Requirements

1. **The manifest ships the driver.** `process-manifest.txt` lists
   `openup-agent.py` and every `openup_agent/*.py` package file, so every install
   path copies them into the target `scripts/`.
   - **Given** a freshly bootstrapped project **When** its `scripts/` is inspected
     **Then** `openup-agent.py` and `openup_agent/{__init__,llm,loop,tiers,tools}.py`
     are present and `python3 scripts/openup-agent.py run --help`-style import
     resolves (the package imports cleanly).

## Operations

- [x] Add `openup-agent.py` + the five `openup_agent/*.py` files to
  `scripts/process-manifest.txt` (grouped with a comment). Verify by running the
  installer into a temp dir (`install_process_clis`) and confirming the driver
  files land and `python3 openup-agent.py` imports its package. Run
  `openup-doctor` (manifest-listed CLIs must all exist) + fence.

## Verification

- `install_process_clis` into a temp `scripts/` copies `openup-agent.py` +
  `openup_agent/*.py`; the copied driver imports its package without error.
- `python3 scripts/openup-doctor.py` finds no "missing shipped CLI".
- `openup-fence.py check --base harness-optional` green.

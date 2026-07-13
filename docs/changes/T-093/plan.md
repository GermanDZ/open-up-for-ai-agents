---
id: T-093
title: openup-roadmap.py — fail-soft on missing docs/roadmap.md (fresh-project crash)
status: ready
priority: high
track: quick
touches:
  - scripts/openup-roadmap.py
  - scripts/tests/test_openup_roadmap.py
depends-on: []
---

# T-093 — roadmap CLI crashes on a freshly bootstrapped project

`openup-roadmap.py` `_roadmap_text` does a bare `read_text()`; a bootstrapped
project has no `docs/roadmap.md` until Inception authors it, so `cmd_next`
(and therefore `openup-board.py resolve` and `openup-agent.py cycle`) crash
with FileNotFoundError (found live, 2026-07-13, fresh `bootstrap-project.sh`
project). Fix: treat a missing roadmap as empty (`""`) so `list` → `[]`,
`get` → exit 3, `next` → exit 3 with its existing no-promotable reason, and
`resolve` degrades to a clean decision instead of a traceback.

## Operations

- [x] Guard `_roadmap_text` (missing file → empty string, docstring states the
      fresh-project rationale); add a hermetic no-roadmap test asserting
      `next`/`list` degrade cleanly and `resolve` returns a decision

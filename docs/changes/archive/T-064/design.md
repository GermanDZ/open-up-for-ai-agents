# T-064 — Design & Verification notes

## In-flight decisions

- **Reuse `openup-claims.py` via importlib** (same pattern as `openup-board.py`)
  for `repo_root` / `claims_dir` / `live_claims`, so "no live lease" in
  `roadmap.py next` means exactly what the claim machinery means — agreement by
  construction, no re-implementation.
- **P2 re-promotion guard (from the 2026-07-09 continuous-orchestrator
  exploration, merged mid-session as PR #62).** The exploration's P2 named T-064
  directly: a completed-but-stale-`pending` task (e.g. T-063 today) archives to
  `docs/changes/archive/<id>/`, so the naive "no `docs/changes/<id>/` folder"
  filter would let the loop re-promote finished work. Requirement 3 was
  strengthened (fix-spec-first) to also exclude an **archived** folder, and
  dependency-satisfaction/candidate-exclusion both key on **true delivery
  evidence** (`completed` status OR archived folder), not the printed status
  word. The durable fix for the rot itself is R2 (roadmap stamping both shapes),
  tracked separately for the product-manager to order.
- **Track selection stays a model call** — `next` names *which* task, not *which
  ceremony track*. The determinism boundary from the efficiency exploration.
- **`touches:` added to the spec frontmatter** so the standard-track write-fence
  admits the `scripts/` + `docs-eng-process/` edits (empty touches on a
  non-quick lane fences everything outside the change folder out).

## Verification — Requirements graded vs the actual diff (step 1a) — BLOCKING

Graded against `git diff origin/main...HEAD` and the green test suite
(`scripts/tests/test_openup_roadmap.py`, 15 tests).

- ✅ **R1 (list both shapes, doc order)** — `parse_roadmap` handles table rows +
  `## T-NNN:` sections in file order (`scripts/openup-roadmap.py`); proven by
  `test_list_pending_both_shapes_in_document_order` and the live run
  (T-063/T-064/T-065 parsed from sections).
- ✅ **R2 (get hit / miss)** — `cmd_get` returns one entry or exits 3 with a
  stderr reason; `test_get_hit`, `test_get_miss_exits_nonzero`.
- ✅ **R3 (next: no active/archived folder + no lease)** — `cmd_next` skips both
  folder kinds and leased ids; `test_next_skips_active_folder`,
  `test_next_skips_archived_folder_p2_guard`, `test_next_skips_live_lease`.
- ✅ **R4 (exit 3 with specific reason)** — `roadmap exhausted` /
  `next pending <id> blocked on <dep>` on stderr; `test_next_roadmap_exhausted`,
  `test_next_blocked_on_dep`; live: "next pending T-065 blocked on T-064".
- ✅ **R5 (read-only)** — no write path in the script; live `git status
  --porcelain` unchanged after a full `list`/`get`/`next` sweep ("READ-ONLY OK").
- ✅ **R6 (deterministic, byte-identical)** — `test_next_deterministic_byte_identical`
  asserts two `next` runs produce identical stdout (divergence = 0).
- ✅ **R7 (§1c consumes next + manifest + CLI ref)** — live
  `.claude/skills/openup-next/SKILL.md §1c` calls
  `python3 scripts/openup-roadmap.py next` and branches on exit 0/3;
  `scripts/process-manifest.txt` ships the script;
  `docs-eng-process/script-cli-reference.md` documents the signatures.

**All requirements ✅ — no ❌.**

## Success-Measure instrumentation (step 1b)

`n/a — internal developer tooling`, per the spec. The task's falsifiable measure
is its own acceptance test — **selection divergence = 0** — and its
instrumentation exists: `test_next_deterministic_byte_identical`. Read-back:
this completion (green). No user-facing telemetry to register.

## Rollout

`n/a — not user-facing`; no feature flag → no flag-removal follow-up (step 4a
skipped).

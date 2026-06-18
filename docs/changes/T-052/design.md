# T-052 — In-flight design decisions

## DD1 — Capture the sync's blast radius from the manifest, not `git status`

The only tracked files a framework sync writes into a consumer are the process
CLIs listed in `scripts/process-manifest.txt` (everything else lands in the
gitignored `.claude/` runtime copy). So `commit_synced_changes` builds its
captured set from `_process_cli_manifest` (already sourced from
`install-process-clis.sh`) as `scripts/<name>`, plus `docs/agent-logs/agent-runs.jsonl`
(the T-046 migration's untrack target). This is precise — it can never sweep an
unrelated user file, because such a file is not in the manifest.

## DD2 — Stage per-path, commit only the staged subset

`git add -A -- <p1> <p2> …` is **atomic**: if any one pathspec matches nothing
(e.g. `agent-runs.jsonl` when the T-046 migration didn't run in this repo), the
whole `add` aborts and stages *nothing*. First implementation hit exactly this —
the sync printed "Committing…" then silently committed nothing. Fix: stage each
captured path individually (`for p in …; do git add -A -- "$p"; done`, misses
swallowed), then derive the actually-staged subset via
`git diff --cached --name-only -- "${captured[@]}"` (diff, unlike add, tolerates
non-matching pathspecs) and commit exactly that subset with the partial-commit
form `git commit -- "${staged[@]}"`. The partial-commit form guarantees unrelated
staged work is left alone (Requirement 3).

Portability: no `mapfile` (macOS ships bash 3.2) — the staged list is collected
with a `while IFS= read -r` loop.

## DD3 — Tester step split (deviation from the literal Operations wording)

Operations step 4 literally asked: dirty a tracked CLI **+** an unrelated
`src/app.py`, run the sync, then "assert the CLI is committed, `src/app.py` is
untouched, **and `on-stop.py` exits 0**." Those last two cannot both hold in one
scenario: `on-stop.py` is a **whole-tree** guard, so with `src/app.py` still
dirty it correctly exits 2 (that dirty file *is* real uncommitted work — exactly
what Requirement 5 says must keep blocking).

Resolution — honor the *requirements* rather than the contradictory literal step:
- **Test 15** covers R1–R3 in the app.py scenario: CLI committed, canonical
  `chore(process) … [openup-skip]` subject, `src/app.py` not in the sync commit
  and still dirty/unmodified.
- **Test 16** covers R4: restore the unrelated edit so the tree's only sync-origin
  change is the (now committed) CLI, then assert `on-stop.py` exits 0.
- **Test 17** covers R5: a hand-made (non-sync) uncommitted CLI edit still blocks
  (exit 2) and is named.

## DD4 — Guards

Skip cleanly (changes left for the human) when: `--dry-run`; not inside a git
work tree; a rebase/merge is in progress (`MERGE_HEAD` / `rebase-merge` /
`rebase-apply` present) — so the sync commit never entangles with a conflict
resolution. Commit message carries the framework short SHA when readable.

## Completion verification (step 1a — graded against the diff)

- ✅ **R1** (tree clean wrt written files) — `commit_synced_changes` in
  `scripts/sync-from-framework.sh` stages + commits the manifest CLI paths;
  Test 15 asserts `git status --porcelain scripts/openup-board.py` is empty after a
  real sync.
- ✅ **R2** (attributable canonical subject) — commit message
  `chore(process): sync OpenUP framework to <sha> [openup-skip]`; Test 15 greps the
  subject for `chore(process): sync OpenUP framework` and `[openup-skip]`.
- ✅ **R3** (never sweeps unrelated work) — per-path `git add` + partial-commit
  `git commit -- "${staged[@]}"`; Test 15 asserts `src/app.py` is absent from the
  sync commit and remains dirty with its original uncommitted content.
- ✅ **R4** (subsequent lane not blocked at stop) — Test 16 runs the real
  `on-stop.py` against the post-sync tree (unrelated edit restored) and asserts exit 0.
- ✅ **R5** (abandoned work still blocks) — Test 17 leaves a hand-made uncommitted
  CLI edit (no sync), runs `on-stop.py`, asserts exit 2 and that the file is named.

All five verified by `bash tests/test-scripts.sh` → 17/17 pass.

## Success-measure instrumentation (step 1b)

✅ pre-existing — the measure ("on-stop override-cap loops attributable to
sync-introduced changes → zero in 30 days") is read back by grepping
`.claude/memory/bypass-log.md` + session transcripts for the override message on a
tree whose only dirty files are framework-written paths. No new code instrumentation
is required; the bypass log + transcripts already exist. **Read-back: 30 days after
release.**

## Rollout

`n/a` — internal developer tooling, no feature flag (step 4a skipped).

## Scope held

Did **not** touch `install-process-clis.sh` (T-051 owns its `.bak` half), the
write-fence, `gate-edits.py`, or `on-stop.py` — the primary approach (sync owns
its blast radius) made the on-stop exemption fallback unnecessary, so no
dual-source mirror was needed.

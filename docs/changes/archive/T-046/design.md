# T-046 — Design / Completion grade

## DD1 — shard key must match across both writers

Two independent writers append run events: `openup-state.py log-event` and the
`auto-log-commit` hook. Both compute the shard path as
`docs/agent-logs/runs/<UTC-date>-<key>.jsonl` with `key = slug(task_id or branch)`
using the **identical** slug rule (`re.sub(r"[^0-9A-Za-z._-]+","-",raw).strip("-")`).
If they diverged, one lane could end up with two files and the consolidation would
double-count. The rule is duplicated (a hook can't import the CLI) but pinned by
`test_two_lanes_write_disjoint_shards` exercising the CLI path and the hook tests
exercising the hook path.

## DD2 — agent-runs.jsonl gitignored, not deleted

The file stays on disk as a local derived view (`runs build` rebuilds it); only
its *tracking* is removed (`git rm --cached`). Memory `project_t006_autolog_onstop_loop`
warned against gitignoring the *source* log — here the shards are the source and
agent-runs.jsonl is genuinely derived, so gitignoring the derived view is correct
and is what removes the cross-branch conflict at the root.

## DD3 — on-stop exemption widened to a prefix

`EXEMPT_DIRTY_PATHS = {agent-runs.jsonl}` became
`EXEMPT_DIRTY_PREFIXES = ("docs/agent-logs/runs/",)` because shard filenames vary
by date+lane. The sweep commits `docs/agent-logs/runs/` so a session still ends on
a clean tree.

## Completion grade (step 1a) — requirements vs diff

- ✅ **R1** lane-owned shard writer — `_shard_key` + `cmd_log_event` in
  openup-state.py; `test_stamps_iso_utc_ts`/`test_task_id_null_when_omitted` (via
  the updated `_records()` shard reader) + `test_appends_once_and_sets_gate`
  (hook) confirm records land in `runs/<date>-<key>.jsonl`, not agent-runs.jsonl.
- ✅ **R2** two-lane disjoint invariant — `test_two_lanes_write_disjoint_shards`
  asserts `{T-043.jsonl, T-044.jsonl}` (distinct files).
- ✅ **R3** derived + untracked — `agent-runs.jsonl` is `git rm --cached`'d +
  gitignored; `merge=union` line removed from `.gitattributes`; `runs build`
  consolidates (verified in the same disjoint test).
- ✅ **R4** hooks stage the shard — `auto-log-commit` writes the shard;
  `on-stop` exempts/sweeps `docs/agent-logs/runs/`; both mirrored to
  `.claude-templates/`; 35 hook tests green.
- ✅ **R5** consumer reads shards — no code consumer exists (counting is grep);
  `parallel-work.md` + `script-cli-reference.md` document counting from the shard
  glob / `runs build`.

No ❌. Full suite 250 tests; the single failure (`test_docs_index…
test_write_creates_index_file`) is the pre-existing macOS `/private/var` path
assertion, unrelated (docs-index.py untouched).

## Success-Measure grade (step 1b)

`n/a` — internal tooling. The mechanical check is R2's disjoint-files invariant
(now test-enforced): two same-day lanes write different files, so the GitHub
merge that conflicted this session (T-043 vs T-044) can no longer occur for the
run log.

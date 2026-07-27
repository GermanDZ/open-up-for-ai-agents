# T-143 — In-flight design decisions

## DD1 — `<git-common-dir>/openup/`, resolved from `REPO_ROOT` not the cwd

The counter moved to `<git-common-dir>/openup/retro.json`, beside
`openup-claims.py`'s claims dir. Two properties made it the right home: every
linked worktree resolves to the same directory, and git never merges it (so the
downstream lost-update variant — two lanes overwriting rather than summing a
tracked scalar — cannot occur either).

`git_common_dir()` queries git with `cwd=REPO_ROOT` (the script's own checkout,
derived from `__file__`), **not** the process cwd. `openup-claims.py` uses the
process cwd; we deliberately diverged. Resolving from `REPO_ROOT` means the
answer does not depend on where a skill happens to invoke the CLI from, and in a
linked worktree it still yields the *main* repo's `.git`, which is the whole
point of the change.

## DD2 — Override precedence: `--retro-dir` > `--state-dir` > shared > repo-local

`--state-dir` still scopes the counter. This is not cosmetic: every existing
test in `test_t011_retro.py` and `test_openup_state.py` injects `--state-dir`
pointing at a temp dir, and without this rule those tests would have started
mutating the developer's real shared counter on every run. Nothing in normal
operation passes `--state-dir` (checked: `sync-status.py` and
`openup-session.py` forward it only when explicitly given), so honouring it
costs nothing and buys hard isolation.

The final `REPO_ROOT/.openup` fallback covers a non-git checkout. It is
fail-open by design — the cadence is an advisory gate, and `git` being missing
or failing must never make the state CLI raise.

## DD3 — Read-forward migration, legacy file left in place

`read_retro_count()` falls back to the legacy `<worktree>/.openup/retro.json`
when the shared file does not exist yet, so a project upgrading mid-cadence
carries its count forward instead of silently resetting to `0`. The first write
lands at the shared path, after which the fallback stops applying — the legacy
value is carried exactly once, never re-applied.

The legacy file is **not** deleted. Deleting is the irreversible half of a
migration; leaving it makes a revert land on the old value intact, and it is
gitignored and unread once the shared file exists.

**Known limit of the migration, worth stating plainly:** the fallback reads the
legacy path *of the worktree it runs in*. This lane's own worktree had no
legacy file, so it reads `0` while the main checkout's legacy file holds `4`.
Once this lands on main, the first run from the main checkout reads `4` and
carries it forward. A lane started in a fresh worktree before that first
main-checkout run would seed the shared counter from `0`. Undercounting by a few
at the moment of migration is acceptable for a cadence gate (it fires slightly
late, once) and does not justify scanning sibling worktrees for legacy files.

## DD4 — Evidence gathered live during this lane

The bug was re-confirmed twice while working it, before any fix was in:

- `openup-session.py begin` seeded `--iterations-since-retro` from a fresh
  worktree's `retro get` → `0`, while the main checkout held `4`.
- `retro check` in the same worktree printed `ok 0`.

After the fix, `retro_path()` resolves to
`<main-repo>/.git/openup/retro.json` from both checkouts, and
`test_two_worktrees_share_one_count` proves the round trip end-to-end in a
throwaway repo (increment in main → visible in a linked worktree → increment
there → visible back in main).

## DD5 — Rejected: union-merge / append-only event list

An additive merge strategy (or replacing the scalar with an append-only event
list) would fix the downstream project's tracked-file lost update. It was
rejected because it does nothing for *this* repo's variant — `.openup/` is
gitignored here, so there is no merge to make additive; the file simply is not
shared. Moving the storage fixes both variants with one mechanism.

## Completion verification (step 1a) — 2026-07-27

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Default path is `<git-common-dir>/openup/retro.json` | ✅ | `retro_dir()` + `git_common_dir()`; resolved live to `<main-repo>/.git/openup/retro.json` from inside the lane worktree, matching `git rev-parse --git-common-dir`; `test_default_location_is_git_common_dir` also asserts the old per-worktree file is *not* written |
| 2 | Two worktrees share one count | ✅ | `test_two_worktrees_share_one_count` — increment in main → `1` read in a linked worktree → increment there → `2` read back in main, in a throwaway repo |
| 3 | `--retro-dir` > `--state-dir` > shared | ✅ | `test_retro_dir_overrides_state_dir_and_shared_default` and `test_state_dir_scopes_counter_when_no_retro_dir`; both assert the shared path stays untouched |
| 4 | Legacy count carried forward, not reset | ✅ | read-forward branch in `read_retro_count()`; `test_legacy_count_is_carried_forward_once` reads `3`, not `0` |
| 5 | Migration non-destructive and idempotent | ✅ | same test: shared file → `4`, legacy file still `3`, second `get` → `4` (legacy never re-applied) |
| 6 | Fails open outside a git repo | ✅ | `git_common_dir()` returns `None` on non-zero rc / `OSError`; `test_non_git_checkout_falls_back_to_repo_local_openup` plants the CLI in a non-repo temp dir and gets `.openup/retro.json` |
| 7 | `state-file.md` documents location, precedence, migration | ✅ | new "Where the counter lives, and why (T-143)" section + updated CLI table row; `--retro-dir` and `git-common-dir` both present |

**Result: all ✅.** Full suite 891 passed / 1 skipped.

## Success-measure instrumentation (step 1b)

✅ — the measure reads `openup-state.py retro get` at `/openup-start-iteration`
§3b, which already runs it (it seeds `--iterations-since-retro`), and compares
the value across consecutive lanes for any decrease. Pre-existing; no new
telemetry. The baseline was captured live in this lane *before* the fix: the
fresh worktree read `0` while main held `4` (see DD4). **Read-back: the next
`/openup-retrospective`.**

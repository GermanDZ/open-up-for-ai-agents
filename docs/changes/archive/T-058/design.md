# T-058 Design & Verification

## Implementation Decisions

1. **Importlib pattern**: Reused the `openup-claims.py` precedent — dynamic load via `spec_from_file_location` wrapped in bare `except Exception: pass` for fail-open.
2. **Semver as tuples**: Version comparison uses `(major, minor, patch)` tuple sorting, not lexicographic string compare (2.10.0 > 2.1.0 correctly).
3. **Stderr for output**: Advisory warning goes to stderr; stdout is left clean for board JSON consumers.
4. **6-hour cooldown fixed**: Hardcoded at `COOLDOWN_SECONDS = 6 * 3600`. Configurable cooldown via `project-config.yaml` deferred as follow-on.
5. **State file location**: `.openup/version-check.json` following `.openup/retro.json` precedent — survives `state.json` archive.

## Requirement Verification (step 1a)

✅ AC1 — `scripts/openup-version-check.py` created: file exists, stdlib-only imports (json/re/subprocess/sys/datetime/pathlib), bare `except Exception: pass` wraps `check_once()`.

✅ AC2 — Reads `.openup/version-check.json`: `_load_state()` + `_in_cooldown()` functions; state file path at `repo_path / ".openup" / "version-check.json"`.

✅ AC3 — `git ls-remote --tags origin 'v*'` with 5s timeout: `_fetch_latest_version()` line 100 calls `subprocess.run(["git", "ls-remote", "--tags", "origin", "v*"], timeout=GIT_TIMEOUT_SECONDS)` where `GIT_TIMEOUT_SECONDS = 5`.

✅ AC4 — Parses latest semver `vX.Y.Z`: `VERSION_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")`, `versions.sort(reverse=True)` picks the highest.

✅ AC5 — Reads installed version from `.template-version`: `_read_installed_version()` reads `repo_path / "docs-eng-process" / ".template-version"`.

✅ AC6 — Semver tuple comparison + stderr warning: `version_tuple()` inline function, `outdated = version_tuple(installed) < version_tuple(latest)`, `sys.stderr.write("[openup] ⚠️ ...")`.

✅ AC7 — Writes `{last_checked, latest, installed, outdated}`: `new_state = {"last_checked": now_iso, "latest": latest, "installed": installed, "outdated": outdated}` → `_save_state()`.

✅ AC8 — Exits 0 on all paths: `__main__` block does `sys.exit(0)` after `check_once()`; `check_once()` has bare `except Exception: pass` catching all errors. Verified: `python3 scripts/openup-version-check.py` exits 0 on this repo.

✅ AC9 — `openup-board.py` calls `check_once()` at top of `main()`: lines 396-404 in the diff, before `raw = list(sys.argv[1:] …)`.

✅ AC10 — `openup-state.py init` calls `check_once()` at end of `cmd_init()`: lines 309-318 in the diff, before `return EXIT_OK`.

✅ AC11 — `scripts/process-manifest.txt` registers `openup-version-check.py`: line added after `openup-doctor.py` with T-058 comment.

✅ AC12 — ≥6 hermetic tests: `test_t058_version_check.py` has 9 tests, all pass (`Ran 9 tests in 0.042s — OK`).

✅ AC13 — Full test suite no regressions: `1 failed, 295 passed` — the 1 failure (`test_docs_index::test_write_creates_index_file`) is pre-existing on `main` (confirmed by checking the same test without T-058 changes).

## Success Measure Verification (step 1b)

**From plan.md**: `n/a — internal developer-experience tooling. Observable success: next downstream session post-merge where the consuming project is behind shows the advisory message without blocking the /openup-next cycle.`

→ `n/a` (argued-unmeasurable, internal DX tooling). No instrumentation gate required.

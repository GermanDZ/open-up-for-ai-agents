---
type: task-spec
id: T-058
status: ready
title: "Periodic framework-version staleness check — 6-hour cooldown, wired into board and start-iteration"
phase: construction
track: standard
traces-from:
  - T-053  # openup-doctor provides version-comparison logic
verified-by: []
touches:
  - scripts/openup-version-check.py
  - scripts/openup-board.py
  - scripts/openup-state.py
  - scripts/process-manifest.txt
  - scripts/tests/test_t058_version_check.py
depends-on: []
---

# T-058: Periodic Framework Version Staleness Check

## Summary

Implement a non-blocking, throttled version-staleness warning that surfaces to practitioners at the start of every work cycle (via `/openup-next` board and `/openup-start-iteration`). The check runs at most once every 6 hours, compares the installed framework version against the latest remote release, and prints an advisory warning to stderr if outdated—without blocking work.

## Goals

- Practitioners see "your framework is outdated" exactly where they're already paying attention: the start of `/openup-next` and `/openup-start-iteration`
- No manual step, no network requirement (fail-open), no work blockage
- 6-hour cooldown prevents spammy repeated checks
- Stdlib-only, distributed via `process-manifest.txt`

---

## REASONS Canvas

### **R**equirement

The framework version is written by `sync-from-framework.sh` into `docs-eng-process/.template-version`. A practitioner has no in-workflow awareness of staleness—only the offline tool `openup-doctor.py --framework-path <clone>` surfaces it. This task surfaces the staleness warning at two scripts the practitioner runs every work cycle:
- `openup-board.py refresh/top` (called by `/openup-next`)
- `openup-state.py init` (called by `/openup-start-iteration`)

### **E**xpectation

When the installed version is behind the latest remote release:
1. A one-line warning is printed to stderr, visible in the console output of `/openup-next` and `/openup-start-iteration`
2. The warning is suppressed for 6 hours after the first successful check (cooldown)
3. If the network is unavailable, git is missing, or any error occurs, the check fails silently (exit 0, no output)
4. The latest version and install status are persisted in `.openup/version-check.json` for cooldown tracking

### **A**ccordance (Acceptance Criteria)

- [ ] `scripts/openup-version-check.py` created (stdlib-only, fail-open)
- [ ] Reads `.openup/version-check.json` for cooldown state
- [ ] Calls `git ls-remote --tags origin 'v*'` with 5-second timeout
- [ ] Parses latest semver `vX.Y.Z` from remote tags
- [ ] Reads installed version from `docs-eng-process/.template-version`
- [ ] Compares semver tuples; if installed < latest, prints warning to stderr
- [ ] Writes `.openup/version-check.json` with `{last_checked, latest, installed, outdated}`
- [ ] Exits 0 on all code paths (network failure, missing files, malformed tags, git error)
- [ ] `openup-board.py` calls `check_once()` at the top of `main()` via importlib
- [ ] `openup-state.py init` calls `check_once()` at the end of `cmd_init()`
- [ ] `scripts/process-manifest.txt` registers `openup-version-check.py`
- [ ] ≥6 hermetic tests in `scripts/tests/test_t058_version_check.py`
- [ ] Full test suite passes (no regressions)

### **O**utcome

Next downstream project that syncs and is behind shows the advisory on the first `/openup-next` or `/openup-start-iteration` call after the cooldown expires. The check does not interfere with the work loop; network failures degrade silently.

### **N**ext Action (Operations)

- [x] Implement `openup-version-check.py`
- [x] Wire into `openup-board.py` and `openup-state.py`
- [x] Register in `process-manifest.txt`
- [x] Write comprehensive tests

---

## Behavior Delta

### Added
- `scripts/openup-version-check.py`: new version-staleness check script
- `.openup/version-check.json`: cooldown-tracking state file
- Advisory warning on board and state-init when version is outdated

### Modified
- `scripts/openup-board.py`: call version check at top of `main()`
- `scripts/openup-state.py`: call version check at end of `cmd_init()`
- `scripts/process-manifest.txt`: register new script

### Removed
- n/a

---

## Assumptions

1. **Semver tagging on origin**: the remote repository tags releases as `vX.Y.Z` (e.g., `v2.0.0`, `v2.1.0`). Non-matching tags are skipped harmlessly.
2. **6-hour cooldown is fixed**: not configurable via `project-config.yaml` (deferred follow-on).
3. **Offline is allowed**: projects without network access degrade silently on the first check after 6 hours; subsequent checks within the cooldown window bypass the network check entirely.
4. **Stderr is visible**: the warning is printed to stderr so board JSON output on stdout remains unpolluted for consumers.

---

## Key Files

| File | Change | Lines |
|------|--------|-------|
| `scripts/openup-version-check.py` | New | ~150 |
| `scripts/openup-board.py` | Modified (importlib call) | ~10 |
| `scripts/openup-state.py` | Modified (importlib call) | ~10 |
| `scripts/process-manifest.txt` | Modified (one line) | 1 |
| `scripts/tests/test_t058_version_check.py` | New | ~200 |

---

## Out of Scope

- Blocking on version staleness (advisory only)
- Auto-running `sync-from-framework.sh`
- Configurable cooldown via `project-config.yaml` (follow-on)
- Checking version in repos without `docs-eng-process/.template-version` (degraded silently)

---

## Testing Strategy

**Hermetic tests** (local bare repos, no real network):

1. **Cooldown respected**: write `version-check.json` with `last_checked` within 6 h → assert no subprocess call; with expired timestamp → assert call made.
2. **Outdated detected**: mock `git ls-remote` to return `v2.1.0`; installed = `2.0.0` → assert stderr warning.
3. **Up-to-date silent**: mock returns `v2.0.0`; installed = `2.0.0` → assert no output.
4. **Network failure graceful**: mock raises `TimeoutExpired` → assert exit 0, no output.
5. **Malformed tags skipped**: mock returns non-semver lines → assert no output.
6. **Board integration**: call `openup-board.py refresh` with stale cooldown + mock newer tag → assert warning in stderr.
7. **State init integration**: call `openup-state.py init` with stale cooldown → assert same warning.

All tests: hermetic temp repos, local bare origin, no real network, exit code assertions.

---

## Given / When / Then Scenarios

### Scenario 1: Version is current
**Given** an installed version matching the latest remote release  
**When** the cooldown has just expired (first check after 6 hours)  
**Then** no output is printed and no network call is repeated within the next 6-hour window

### Scenario 2: Version is outdated
**Given** an installed version (e.g., 2.0.0) behind a newer remote release (e.g., 2.1.0)  
**When** a practitioner runs `/openup-next` or `/openup-start-iteration` after the cooldown expires  
**Then** a one-line advisory is printed to stderr and the `.openup/version-check.json` is updated

### Scenario 3: Network unavailable
**Given** no network connectivity  
**When** the cooldown expires and the check is triggered  
**Then** the check fails silently (exit 0) and work proceeds unblocked

### Scenario 4: Cooldown active
**Given** a successful version check completed 2 hours ago  
**When** `/openup-board.py` is called again  
**Then** no network call is made; the cached result from the previous check is used (no new network activity)

---

## Implementation Notes

- **Importlib pattern**: reuse the existing `openup-claims.py` import pattern (spec + loader) to avoid adding module-level imports
- **Fail-open everywhere**: wrap all network and file I/O in try-except; silent return on error
- **Semver parsing**: tuple sort on `(major, minor, patch)` integers extracted via regex; non-parseable tags skipped
- **State file**: follow the `.openup/retro.json` precedent — persist in `.openup/` so it survives `state.json` archive

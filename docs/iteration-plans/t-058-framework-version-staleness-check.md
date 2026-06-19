---
type: iteration-plan
id: T-058
status: implemented
title: "Periodic framework-version staleness check — 6-hour cooldown, wired into board and start-iteration"
traces-from: []
verified-by: []
---

# T-058: Periodic Framework Version Staleness Check

**Phase**: construction
**Status**: pending
**Goal**: Emit an advisory warning when the installed framework version is behind the latest
release, checked at most once every 6 hours, wired into the scripts that run at the start
of every work cycle.
**Priority**: medium

---

## Context

OpenUP is installed by copying `docs-eng-process/` + `.claude/` into a consuming project,
then kept current by running `sync-from-framework.sh`. Nothing today tells a practitioner
"you are behind — run the sync" during ordinary work. The staleness only surfaces when
`openup-doctor.py --framework-path <clone>` is run explicitly (and that requires a local
framework clone).

The two scripts a developer interacts with at the start of every work cycle are:

- **`openup-board.py refresh/top`** — called by `/openup-next` to derive the board queue
- **`openup-state.py init`** — called by `/openup-start-iteration` to open a new lane

Wiring a lightweight, fail-open, throttled version check into both surfaces the staleness
warning exactly where the practitioner is already paying attention, without adding a manual
step or blocking work.

---

## Current State

### Installed-version file (`docs-eng-process/.template-version`)

```
2.0.0
```

Written by `sync-from-framework.sh` line 584:
```bash
cp "$fw_version_file" "$DOCS_PROCESS_DIR/.template-version"
```

### Project mode file (`.openup-version`)

```
vendored
```

Written by `sync-from-framework.sh` bootstrap (line 677). Values: `vendored` / `latest` /
`vX.Y.Z`.

### `openup-board.py` entry point (`scripts/openup-board.py:60–80`)

The `main()` function runs `refresh` then optionally `top`. No pre-flight version check
today. Imports `openup-claims.py` via importlib already.

### `openup-state.py init` (`scripts/openup-state.py:~390`)

Writes `.openup/state.json`. No version check today.

### `openup-doctor.py` version check (already exists)

`scripts/openup-doctor.py` implements version comparison against a `--framework-path`
baseline. Requires a local clone; not wired into the loop. This task adds the
*periodic-remote* counterpart: no local clone needed, network-optional, cooldown-throttled.

### Cooldown precedent: `.openup/retro.json`

```json
{"iterations_since_retro": 1}
```

A durable `.openup/` state file that survives `state.json` archive is the established
pattern. `.openup/version-check.json` will follow the same shape.

### `scripts/process-manifest.txt` (current: 14 CLIs)

Listed CLIs are shipped by every install/sync path. New script must be registered here.

---

## Proposed Design

### New script: `scripts/openup-version-check.py`

Stdlib-only, read-only, fail-open. Callable as a module import (`check_once(repo_root)`
returns nothing but prints a warning to stderr when outdated) and as a standalone CLI
(exits 0 always).

```
scripts/openup-version-check.py
  check_once(repo_root: str) -> None
    - Reads .openup/version-check.json for last_checked timestamp
    - If now - last_checked < COOLDOWN_SECONDS (21600): return immediately
    - Calls: git ls-remote --tags origin 'v*'  (timeout=5s)
    - Parses latest semver tag from output
    - Reads docs-eng-process/.template-version for installed version
    - Writes .openup/version-check.json: {last_checked, latest, installed, outdated}
    - If outdated: print warning to stderr
    - On any error: return silently (fail-open)
```

**Cooldown state file** (`.openup/version-check.json`):
```json
{
  "last_checked": "2026-06-19T14:00:00Z",
  "latest": "2.1.0",
  "installed": "2.0.0",
  "outdated": true
}
```

**Warning format** (stderr):
```
[openup] ⚠️  Framework version outdated: installed=2.0.0  latest=2.1.0
           Run: sync-from-framework.sh --framework-path <path>  or  force-upgrade.sh
```

**Fail-open surface**: any `OSError`, `subprocess.TimeoutExpired`, parse failure →
silently return. The check must never interrupt work.

**Version comparison**: semver tuple sort on `(major, minor, patch)` integers;
non-parseable tags → skip that tag (not a failure). If no parseable remote tag is found →
return silently.

### Wire into `openup-board.py`

At the top of `main()`, before any board computation, load and call via importlib
(same pattern as the existing `openup-claims.py` import):

```python
# near top of main() in openup-board.py
try:
    _vc_path = Path(__file__).resolve().parent / "openup-version-check.py"
    _vc_spec = importlib.util.spec_from_file_location("openup_version_check", _vc_path)
    _vc = importlib.util.module_from_spec(_vc_spec)
    _vc_spec.loader.exec_module(_vc)
    _vc.check_once(str(Path(__file__).resolve().parents[1]))
except Exception:
    pass  # fail-open: version check never breaks the board
```

### Wire into `openup-state.py init`

At the end of `cmd_init()`, after writing `.openup/state.json`:

```python
# at the end of cmd_init() in openup-state.py
try:
    import importlib.util as _ilu
    _p = Path(__file__).resolve().parent / "openup-version-check.py"
    _s = _ilu.spec_from_file_location("openup_version_check", _p)
    _m = _ilu.module_from_spec(_s); _s.loader.exec_module(_m)
    _m.check_once(str(Path(__file__).resolve().parents[1]))
except Exception:
    pass
```

### Register in `scripts/process-manifest.txt`

Add one line: `openup-version-check.py`

---

## Acceptance Criteria

- [ ] `openup-version-check.py` exits 0 on every code path (network down, missing
      `.template-version`, malformed tags, git not available)
- [ ] When installed version equals the remote latest: no output, no network call after
      first check within the 6-hour window
- [ ] When installed version is behind latest: a one-line advisory warning is printed to
      **stderr** (stdout is consumed by board callers)
- [ ] Within a 6-hour window after a successful check, no network call is made
- [ ] `openup-board.py refresh` and `openup-board.py top` emit the staleness warning on
      the first call that breaks the cooldown; subsequent calls within 6 h are silent
- [ ] `openup-state.py init` also emits the warning when cooldown has expired
- [ ] `openup-version-check.py` is listed in `scripts/process-manifest.txt`
- [ ] Full test suite passes with no regressions (≥ 6 new hermetic tests)

---

## Success Measure

`n/a — internal developer-experience tooling. Observable success: next downstream
session post-merge where the consuming project is behind shows the advisory
message without blocking the /openup-next cycle.`

---

## Testing Strategy

- **Cooldown respected**: write a `version-check.json` with `last_checked` within 6 h →
  assert no subprocess call made; with expired timestamp → assert subprocess called.
- **Outdated path**: mock `git ls-remote` to return `v2.1.0`; installed = `2.0.0` →
  assert stderr warning emitted.
- **Current path**: mock returns `v2.0.0`; installed = `2.0.0` → assert no output.
- **Network failure**: mock raises `TimeoutExpired` → assert exit 0, no output.
- **Malformed tags**: mock returns lines with no parseable semver → assert no output.
- **Board integration**: call `openup-board.py refresh` in a temp repo with stale
  cooldown + mock returning newer tag → assert stderr warning present in board output.
- **State init integration**: call `openup-state.py init` with stale cooldown → assert
  same warning.
- All tests: hermetic temp repos, local bare git remote as origin; no real network.

---

## Dependencies

None.

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-version-check.py` | New — cooldown-throttled remote version check |
| `scripts/openup-board.py` | Modified — call `check_once()` at top of `main()` |
| `scripts/openup-state.py` | Modified — call `check_once()` at end of `cmd_init()` |
| `scripts/process-manifest.txt` | Modified — add `openup-version-check.py` |
| `scripts/tests/test_t058_version_check.py` | New — ≥6 hermetic tests |

---

## Out of Scope

- Blocking on version staleness (advisory only)
- Auto-running `sync-from-framework.sh`
- Integrating into `openup-doctor.py` (doctor already has `--framework-path` path)
- Configurable cooldown (hardcoded 6 h; a `project-config.yaml` key is a follow-on)
- Checking version when no `docs-eng-process/.template-version` exists (degraded silently)

---

## Open Questions

1. **Stdout vs. stderr**: assumed stderr so board JSON output on stdout is unpolluted.
2. **6-hour cooldown**: hardcoded; configurable via `project-config.yaml` deferred.
3. **`git ls-remote` timeout**: assumed 5 seconds; offline runs degrade silently.

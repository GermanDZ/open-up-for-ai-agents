---
name: openup-doctor
description: Read-only project health check — framework/manifest drift, .openup/state.json integrity, and aggregation of existing --check validators
model: haiku
fit:
  great: ["downstream maintainer asking is my OpenUP install current and unmodified", "pre-flight health check on a fresh clone or in CI without the git hooks", "diagnosing a corrupt/misnamed .openup/state.json footgun"]
  ok: ["a quick is-this-project-well-formed sweep before starting work"]
  poor: ["fixing anything (doctor is strictly diagnostic — fixes live in sync-from-framework.sh / the owning generators)", "what can I work on next (that is /openup-readiness)"]
arguments:
  - name: framework_path
    description: "Optional. Path to a framework baseline clone. Enables byte-level CLI drift detection; without it doctor degrades to version-only (offline)."
    required: false
---

# Doctor

Run the read-only project health diagnostic and relay its report. The real
artifact is the deterministic `scripts/openup-doctor.py`; this skill is a thin
wrapper for the interactive "diagnose my project" ask.

**This skill is READ-ONLY.** It runs one script that writes nothing, fixes
nothing, and mutates no file. Fixes stay in their owning scripts
(`sync-from-framework.sh`, `sync-status.py`, the derived-view generators) — do
not offer to apply them from here.

> **Mechanical step** (`model: haiku`). Run the script, relay its output, do not
> re-derive or second-guess its findings.

## Process

1. Run the diagnostic from the project root:

   ```bash
   python3 scripts/openup-doctor.py            # offline (version-only drift)
   # or, with a baseline clone for byte-level CLI drift detection:
   python3 scripts/openup-doctor.py --framework-path <path-to-framework-clone>
   # add --json for machine-readable output (CI)
   ```

2. Relay the report. Findings are grouped by severity:
   - **error** — corrupt/unreadable `.openup/state.json`, a manifest-listed CLI
     missing, or a read-only validator that itself failed. Exit code is **1**.
   - **warning** — behind on framework version, a locally-modified shipped CLI,
     or a stale derived view. Exit **0**.
   - **info** — advisory / "could not verify" notes. Exit **0**.
   - Unresolvable project root → exit **2**.

3. For each error/warning, point at the owning fix (never run it yourself):
   behind-on-version / modified CLI → `sync-from-framework.sh`; stale derived
   view → the named generator (e.g. `docs-index.py`); corrupt state → manual
   repair of `.openup/state.json`.

## See Also

- [openup-readiness](../openup-readiness/SKILL.md) — "what can I work on" (DAG); doctor answers "is the project well-formed".
- `scripts/openup-doctor.py` — the deterministic diagnostic this skill wraps.
- `docs-eng-process/script-cli-reference.md` — the CLI signature.

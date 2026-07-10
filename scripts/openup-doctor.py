#!/usr/bin/env python3
"""OpenUP project health diagnostic (T-053) — read-only.

One command answers "is this OpenUP project well-formed?" for the maintainer of a
*consuming* project (downstream clone, fresh checkout, or CI without the git
hooks installed). It performs two checks nothing else does, plus a thin
aggregation over the existing read-only / ``--check`` validators:

  1. **Framework / manifest drift** — is the installed framework current, and are
     the shipped CLIs the ones the framework ships (none missing, none locally
     modified)? ``docs-eng-process/.template-version`` answers "what version am I
     on"; ``scripts/process-manifest.txt`` answers "what files should exist".
     With ``--framework-path <baseline-clone>`` doctor compares both halves
     against that baseline. Offline (no baseline) it reports the installed
     version and notes that scripts can't be byte-verified — never a failure.

  2. **State integrity** — ``.openup/state.json`` is schema-validated when
     *written* by ``openup-state.py`` but never re-validated after a hand-edit,
     a bad merge, or a partial migration. Doctor revalidates it at *read* time
     (reusing ``openup-state.py validate`` — no schema logic is duplicated).

  3. **Aggregation** — runs the read-only / ``--check`` mode of each existing
     validator that is present and collates results by severity. It *invokes*
     them; it never reimplements their logic (that would create a second source
     of truth that drifts). Tools with no read-only mode (e.g. ``sync-status.py``
     writes) are intentionally excluded — see docs/changes/T-053/design.md DD1.

Doctor is strictly diagnostic: it never writes, mutates, or fixes anything.
Fixes stay in their owning scripts (``sync-from-framework.sh``, ``sync-status.py``,
the derived-view generators).

Severity model:
  error    corrupt/unreadable .openup/state.json; a manifest-listed CLI missing;
           an aggregated read-only validator that itself fails.   → nonzero exit
  warning  behind on framework version; a locally-modified shipped CLI; a stale
           derived view.                                          → exit 0
  info     advisory / "could not verify" degradations.            → exit 0

Exit codes:
  0  no error-severity findings (warnings/info may be present)
  1  at least one error-severity finding
  2  doctor itself could not run (bad arguments, unresolvable repo root)

Usage:
  python3 scripts/openup-doctor.py [--repo-root DIR] [--framework-path DIR] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

# ── Severity ───────────────────────────────────────────────────────────────
ERROR = "error"
WARNING = "warning"
INFO = "info"
_RANK = {ERROR: 2, WARNING: 1, INFO: 0}


class Finding:
    __slots__ = ("severity", "check", "message")

    def __init__(self, severity: str, check: str, message: str):
        self.severity = severity
        self.check = check
        self.message = message

    def as_dict(self) -> dict:
        return {"severity": self.severity, "check": self.check, "message": self.message}


# ── Helpers ──────────────────────────────────────────────────────────────────
def run(cmd, cwd) -> tuple[int, str]:
    """Run a command, returning (exit_code, combined_output). Never raises."""
    try:
        p = subprocess.run(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=120,
        )
        return p.returncode, (p.stdout or "").strip()
    except FileNotFoundError:
        return 127, "executable not found"
    except Exception as exc:  # pragma: no cover - defensive
        return 1, f"could not run: {exc}"


def resolve_repo_root(explicit: str | None) -> str | None:
    """Repo/worktree root: explicit > git toplevel > ancestor with .openup or scripts/."""
    if explicit:
        return os.path.abspath(explicit) if os.path.isdir(explicit) else None
    code, out = run(["git", "rev-parse", "--show-toplevel"], os.getcwd())
    if code == 0 and out:
        return out.splitlines()[0].strip()
    d = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(d, ".openup")) or os.path.isfile(
            os.path.join(d, "scripts", "openup-state.py")
        ):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def parse_version(text: str) -> tuple | None:
    """Parse '1.5.0' → (1, 5, 0). Returns None if unparseable."""
    parts = text.strip().split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def read_manifest(path: str) -> list[str]:
    """Filenames from a process-manifest.txt (blank lines and #-comments ignored)."""
    names = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    names.append(line)
    except OSError:
        pass
    return names


# ── Check 1: framework / manifest drift ──────────────────────────────────────
def check_framework_drift(repo: str, framework_path: str | None) -> list[Finding]:
    out: list[Finding] = []
    chk = "framework-drift"
    ver_file = os.path.join(repo, "docs-eng-process", ".template-version")
    installed_raw = ""
    if os.path.isfile(ver_file):
        with open(ver_file, encoding="utf-8") as fh:
            installed_raw = fh.read().strip()
    if not installed_raw:
        out.append(Finding(INFO, chk, "no docs-eng-process/.template-version — "
                                      "framework version unknown"))
        # Without an installed version we still try CLI presence below if baseline given.
    else:
        out.append(Finding(INFO, chk, f"installed framework version {installed_raw}"))

    if not framework_path:
        out.append(Finding(INFO, chk, "scripts not verified (no --framework-path "
                                      "baseline); version-currency not checked"))
        return out

    base = os.path.abspath(framework_path)
    if not os.path.isdir(base):
        out.append(Finding(WARNING, chk,
                           f"--framework-path '{framework_path}' is not a directory; "
                           "skipping drift comparison"))
        return out

    # Version currency
    base_ver_file = os.path.join(base, "docs-eng-process", ".template-version")
    base_raw = ""
    if os.path.isfile(base_ver_file):
        with open(base_ver_file, encoding="utf-8") as fh:
            base_raw = fh.read().strip()
    iv, bv = parse_version(installed_raw), parse_version(base_raw)
    if iv is not None and bv is not None:
        if iv < bv:
            out.append(Finding(WARNING, chk,
                               f"behind on framework version ({installed_raw} < {base_raw}) "
                               "— run sync-from-framework.sh"))
        elif iv == bv:
            out.append(Finding(INFO, chk, f"framework version current ({installed_raw})"))
    elif base_raw:
        out.append(Finding(INFO, chk,
                           "could not compare versions "
                           f"(installed='{installed_raw}', baseline='{base_raw}')"))

    # Per-CLI byte drift against the baseline's manifest
    base_manifest = os.path.join(base, "scripts", "process-manifest.txt")
    names = read_manifest(base_manifest)
    if not names:
        out.append(Finding(INFO, chk,
                           "baseline has no scripts/process-manifest.txt — "
                           "cannot verify shipped CLIs"))
        return out
    for name in names:
        repo_file = os.path.join(repo, "scripts", name)
        base_file = os.path.join(base, "scripts", name)
        if not os.path.isfile(repo_file):
            out.append(Finding(ERROR, chk, f"missing shipped CLI: scripts/{name}"))
            continue
        try:
            with open(repo_file, "rb") as a, open(base_file, "rb") as b:
                if a.read() != b.read():
                    out.append(Finding(WARNING, chk, f"locally modified: scripts/{name}"))
        except OSError:
            out.append(Finding(INFO, chk,
                               f"could not compare scripts/{name} against baseline"))
    return out


# ── Check 2: .openup/state.json integrity ────────────────────────────────────
def check_state_integrity(repo: str) -> list[Finding]:
    chk = "state-integrity"
    state_dir = os.path.join(repo, ".openup")
    state_file = os.path.join(state_dir, "state.json")
    if not os.path.isfile(state_file):
        return [Finding(INFO, chk, "no active iteration (.openup/state.json absent)")]
    state_py = os.path.join(repo, "scripts", "openup-state.py")
    if not os.path.isfile(state_py):
        return [Finding(INFO, chk,
                        "scripts/openup-state.py absent — cannot validate state")]
    code, output = run(["python3", state_py, "validate", "--state-dir", state_dir], repo)
    if code == 0:
        return [Finding(INFO, chk, ".openup/state.json is valid")]
    # The last non-empty output line is the actual diagnostic (a traceback header
    # like "Traceback (most recent call last):" is unhelpful as the headline).
    detail = next((ln for ln in reversed(output.splitlines()) if ln.strip()),
                  "validation failed")
    return [Finding(ERROR, chk, f".openup/state.json invalid: {detail.strip()}")]


# ── Check 3: aggregate existing read-only / --check validators ────────────────
# (name, argv-relative-to-scripts, severity-on-failure). Read-only only — see DD1.
_AGGREGATED = [
    ("check-docs.py", ["check-docs.py"], ERROR),
    ("docs-index.py --check", ["docs-index.py", "--check"], WARNING),
    ("build-trace-model.py --check", ["build-trace-model.py", "--check"], WARNING),
    ("check-skills-guide.py --check", ["check-skills-guide.py", "--check"], WARNING),
    ("check-model-tiers.py --check", ["check-model-tiers.py", "--check"], WARNING),
    ("check-claude-sync.sh", ["check-claude-sync.sh"], WARNING),
]


def _interp(script_name: str):
    return ["bash"] if script_name.endswith(".sh") else ["python3"]


def check_aggregate(repo: str) -> list[Finding]:
    out: list[Finding] = []
    chk = "aggregate"
    scripts_dir = os.path.join(repo, "scripts")
    for label, argv, sev in _AGGREGATED:
        script_name = argv[0]
        script_path = os.path.join(scripts_dir, script_name)
        if not os.path.isfile(script_path):
            out.append(Finding(INFO, chk, f"{label}: not present (skipped)"))
            continue
        cmd = _interp(script_name) + [script_path] + argv[1:]
        code, output = run(cmd, repo)
        if code == 0:
            out.append(Finding(INFO, chk, f"{label}: ok"))
        elif code == 127:
            out.append(Finding(INFO, chk, f"{label}: could not run ({output})"))
        else:
            tail = (output.splitlines() or [""])[-1][:200]
            out.append(Finding(sev, chk, f"{label}: failed (exit {code}) {tail}".rstrip()))

    # Fence is lane-diff-scoped: only meaningful with an active lane (DD1).
    fence = os.path.join(scripts_dir, "openup-fence.py")
    if os.path.isfile(os.path.join(repo, ".openup", "state.json")) and os.path.isfile(fence):
        code, output = run(["python3", fence, "check"], repo)
        if code == 0:
            out.append(Finding(INFO, chk, "openup-fence.py check: ok"))
        else:
            tail = (output.splitlines() or [""])[-1][:200]
            out.append(Finding(WARNING, chk,
                               f"openup-fence.py check: failed (exit {code}) {tail}".rstrip()))
    return out


def check_section_status_drift(repo: str) -> list[Finding]:
    """Detect roadmap status-rot: a free-form '## T-NNN:' section whose change
    folder is archived but whose Status is not 'completed' (T-067). Read-only —
    invokes sync-status.py's --reconcile --dry-run; the fix stays in that owning
    script (doctor never writes). Mirrors the 'stale derived view' warning."""
    out: list[Finding] = []
    chk = "roadmap-status-drift"
    script = os.path.join(repo, "scripts", "sync-status.py")
    if not os.path.isfile(script):
        return out
    code, output = run(_interp("sync-status.py") + [script, "--reconcile", "--dry-run"], repo)
    if code != 0:
        out.append(Finding(INFO, chk, f"could not check ({output.splitlines()[-1][:120] if output else code})"))
        return out
    drifted = [ln.split()[1] for ln in output.splitlines()
               if ln.startswith("DRIFT ") and len(ln.split()) >= 2]
    for task_id in drifted:
        out.append(Finding(WARNING, chk,
                           f"{task_id}: archived but roadmap Status not 'completed' — "
                           f"run `python3 scripts/sync-status.py --reconcile`"))
    return out


# ── Reporting ────────────────────────────────────────────────────────────────
def render_human(findings: list[Finding]) -> str:
    order = [ERROR, WARNING, INFO]
    icon = {ERROR: "✗", WARNING: "!", INFO: "·"}
    lines = ["OpenUP project health (openup-doctor)", ""]
    counts = {s: sum(1 for f in findings if f.severity == s) for s in order}
    for sev in order:
        group = [f for f in findings if f.severity == sev]
        if not group:
            continue
        lines.append(f"{sev.upper()} ({len(group)}):")
        for f in group:
            lines.append(f"  {icon[sev]} [{f.check}] {f.message}")
        lines.append("")
    summary = (f"{counts[ERROR]} error(s), {counts[WARNING]} warning(s), "
               f"{counts[INFO]} info")
    lines.append(summary)
    lines.append("healthy" if counts[ERROR] == 0 else "errors present — see above")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", help="project root (default: git toplevel / cwd ancestor)")
    parser.add_argument("--framework-path",
                        help="path to a framework baseline clone for byte-level CLI "
                             "drift detection (offline-degraded if omitted)")
    parser.add_argument("--json", action="store_true",
                        help="emit a single JSON object of findings instead of text")
    args = parser.parse_args(argv)

    repo = resolve_repo_root(args.repo_root)
    if not repo:
        msg = "could not resolve a project root (not a git repo; no .openup/ or scripts/ found)"
        if args.json:
            print(json.dumps({"error": msg, "findings": []}))
        else:
            print(f"openup-doctor: {msg}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    findings += check_framework_drift(repo, args.framework_path)
    findings += check_state_integrity(repo)
    findings += check_aggregate(repo)
    findings += check_section_status_drift(repo)

    has_error = any(f.severity == ERROR for f in findings)

    if args.json:
        print(json.dumps({
            "repo_root": repo,
            "ok": not has_error,
            "findings": [f.as_dict() for f in findings],
        }, indent=2))
    else:
        print(render_human(findings))

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())

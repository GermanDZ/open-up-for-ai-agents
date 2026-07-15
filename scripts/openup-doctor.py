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

By default doctor is strictly diagnostic: it never writes, mutates, or fixes
anything. The opt-in ``--fix`` mode (T-117) applies **auto-heal-class** findings —
those whose file is a pure function of tracked inputs (stale derived/mirror views,
a single-valued unset ``plan_persisted`` gate) — by **invoking the owning
fix-script** (``sync-status.py --reconcile``, the derived-view generators,
``openup-state.py set-gate``); it never reimplements a fix (DD1). Confirm-class
findings are applied only under ``--fix --confirm``; human-judgment-only findings
are never auto-applied. Fixes always stay in their owning scripts.

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
                                   [--fix [--confirm]]
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


# ── Fix class (T-117) ────────────────────────────────────────────────────────
# Three-way classification of a finding's remediability (exploration
# 2026-07-15-self-healing-interrupted-process-state.md §2):
#   auto    — the file is a pure function of tracked inputs; regenerating cannot
#             lose information. Applied non-interactively by `--fix`.
#   confirm — mechanical to propose but touches persisted intent / destructive if
#             the diagnosis is wrong. Applied only under `--fix --confirm`.
#   human   — recovering or inventing intent; never auto-applied.
AUTO = "auto"
CONFIRM = "confirm"
HUMAN = "human"


class Finding:
    __slots__ = ("severity", "check", "message", "fix_class", "fix_cmd")

    def __init__(self, severity: str, check: str, message: str,
                 fix_class: str | None = None, fix_cmd: list | None = None):
        self.severity = severity
        self.check = check
        self.message = message
        # fix_class ∈ {AUTO, CONFIRM, HUMAN, None}; fix_cmd is argv relative to
        # scripts/ (e.g. ["docs-index.py"]) that `--fix` invokes to heal it.
        self.fix_class = fix_class
        self.fix_cmd = fix_cmd

    def as_dict(self) -> dict:
        return {"severity": self.severity, "check": self.check, "message": self.message,
                "fix_class": self.fix_class, "fix_cmd": self.fix_cmd}


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
    ("render-skills-mirror.py --check", ["render-skills-mirror.py", "--check"], WARNING),
    ("check-claude-sync.sh", ["check-claude-sync.sh"], WARNING),
]


def _interp(script_name: str):
    return ["bash"] if script_name.endswith(".sh") else ["python3"]


# Auto-heal-class owning generators (T-117): a failed aggregate --check is a stale
# derived view whose regeneration is the *defined* repair. Keyed by aggregate label
# → the owning script's write-mode argv (relative to scripts/). Doctor invokes
# these, never reimplements them (DD1). Order-independent: apply_fixes re-runs the
# owning generators in dependency order (trace-model before the index it feeds).
_AUTO_FIX = {
    "docs-index.py --check": ["docs-index.py"],
    "build-trace-model.py --check": ["build-trace-model.py"],
    "render-skills-mirror.py --check": ["render-skills-mirror.py", "--write"],
    "check-claude-sync.sh": ["sync-templates-to-claude.sh"],
}

# Dependency order for applying auto fixes: lower runs first. build-trace-model
# writes trace-model.json which docs-index reads, so it must precede docs-index.
_FIX_ORDER = {
    "build-trace-model.py": 0,
    "sync-templates-to-claude.sh": 1,
    "render-skills-mirror.py": 1,
    "sync-status.py": 1,
    "docs-index.py": 2,
}


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
            fix = _AUTO_FIX.get(label)
            out.append(Finding(sev, chk, f"{label}: failed (exit {code}) {tail}".rstrip(),
                               fix_class=AUTO if fix else None, fix_cmd=fix))

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
                           f"run `python3 scripts/sync-status.py --reconcile`",
                           fix_class=AUTO, fix_cmd=["sync-status.py", "--reconcile"]))
    return out


def check_plan_gate(repo: str) -> list[Finding]:
    """Detect a single-valued unset `plan_persisted` gate (T-117 / heal-class C).

    When an active lane's `gates.plan_persisted` is falsy but its
    `docs/changes/<id>/plan.md` demonstrably exists, the gate's correct value is a
    *lookup, not a judgment* — so this is auto-heal-class. The owning fix is
    `openup-state.py set-gate` (doctor never edits state itself). Read-only here;
    the fix runs only under `--fix`."""
    out: list[Finding] = []
    chk = "plan-gate"
    state_file = os.path.join(repo, ".openup", "state.json")
    if not os.path.isfile(state_file):
        return out
    try:
        with open(state_file, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return out  # corrupt state is check_state_integrity's job, not ours
    gates = state.get("gates") or {}
    if gates.get("plan_persisted"):
        return out  # already set — nothing to heal
    task_id = state.get("task_id") or state.get("task")
    if not task_id:
        return out
    plan_rel = os.path.join("docs", "changes", str(task_id), "plan.md")
    if not os.path.isfile(os.path.join(repo, plan_rel)):
        return out  # no plan to point at — not the single-valued case
    out.append(Finding(WARNING, chk,
                       f"{task_id}: gates.plan_persisted unset but {plan_rel} exists — "
                       f"run `python3 scripts/openup-state.py set-gate plan_persisted {plan_rel}`",
                       fix_class=AUTO,
                       fix_cmd=["openup-state.py", "set-gate", "plan_persisted", plan_rel]))
    return out


def check_process_config(repo: str) -> list[Finding]:
    """Report the Development Case (`process:` section of docs/project-config.yaml,
    T-076) status. Read-only: reuses check-docs.py's structural validator. INFO
    when absent/valid, WARNING (never ERROR) when malformed — the human-readable
    pointer at check-docs.py, which is the actual gate (run by check_aggregate)."""
    import importlib.util
    out: list[Finding] = []
    chk = "process-config"
    config = os.path.join(repo, "docs", "project-config.yaml")
    checker = os.path.join(repo, "scripts", "check-docs.py")
    if not os.path.isfile(checker):
        return out
    if not os.path.isfile(config):
        out.append(Finding(INFO, chk,
                           "no docs/project-config.yaml — framework defaults apply"))
        return out
    try:
        spec = importlib.util.spec_from_file_location("_openup_check_docs", checker)
        cd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cd)  # type: ignore[union-attr]
        from pathlib import Path
        findings = cd.validate_process_config(Path(config))
        process = cd.parse_process_section(Path(config).read_text(encoding="utf-8"))
    except Exception as exc:  # never let a diagnostic crash the doctor
        out.append(Finding(INFO, chk, f"could not check ({exc})"))
        return out
    if process is None:
        out.append(Finding(INFO, chk,
                           "no `process:` section — framework defaults apply"))
        return out
    if findings:
        for f in findings:
            out.append(Finding(WARNING, chk,
                               f"invalid `process:` section — {f.message} "
                               f"(run `python3 scripts/check-docs.py`)"))
    else:
        arche = process.get("archetype", "?")
        out.append(Finding(INFO, chk, f"Development Case: archetype={arche}"))
    return out


# ── Detection + fix orchestration ─────────────────────────────────────────────
def detect_all(repo: str, framework_path: str | None) -> list[Finding]:
    """Run every read-only check and return the collated findings."""
    findings: list[Finding] = []
    findings += check_framework_drift(repo, framework_path)
    findings += check_state_integrity(repo)
    findings += check_aggregate(repo)
    findings += check_section_status_drift(repo)
    findings += check_plan_gate(repo)
    findings += check_process_config(repo)
    return findings


def apply_fixes(repo: str, findings: list[Finding], confirm: bool,
                framework_path: str | None) -> tuple[list[Finding], list[str]]:
    """Invoke owning fix-scripts for remediable findings, then re-detect (T-117).

    AUTO-class fixes always run; CONFIRM-class fixes run only when ``confirm`` is
    set (otherwise they are left as printed proposals). HUMAN-class findings and
    findings without a ``fix_cmd`` are never touched. Doctor delegates to the
    owning scripts — it never reimplements a fix (DD1). Returns
    ``(post_fix_findings, applied_labels)``."""
    to_apply = {}  # dedupe by fix_cmd; last-write of the same argv wins
    for f in findings:
        if not f.fix_cmd:
            continue
        if f.fix_class == AUTO or (f.fix_class == CONFIRM and confirm):
            to_apply[tuple(f.fix_cmd)] = f.fix_cmd
    applied: list[str] = []
    scripts_dir = os.path.join(repo, "scripts")
    ordered = sorted(to_apply.values(), key=lambda c: _FIX_ORDER.get(c[0], 5))
    for argv in ordered:
        script_path = os.path.join(scripts_dir, argv[0])
        if not os.path.isfile(script_path):
            applied.append(f"SKIP {' '.join(argv)} (script absent)")
            continue
        cmd = _interp(argv[0]) + [script_path] + argv[1:]
        code, output = run(cmd, repo)
        status = "ok" if code == 0 else f"exit {code}"
        applied.append(f"{'ran' if code == 0 else 'FAILED'} {' '.join(argv)} ({status})")
    return detect_all(repo, framework_path), applied


def unapplied_proposals(findings: list[Finding], confirm: bool) -> list[Finding]:
    """CONFIRM-class findings left as proposals (only when --confirm is absent)."""
    if confirm:
        return []
    return [f for f in findings if f.fix_class == CONFIRM and f.fix_cmd]


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
    parser.add_argument("--fix", action="store_true",
                        help="apply auto-heal-class findings by invoking their owning "
                             "scripts, then re-report (opt-in; default stays read-only)")
    parser.add_argument("--confirm", action="store_true",
                        help="with --fix, also apply confirm-class findings (else they "
                             "are printed as proposals only)")
    args = parser.parse_args(argv)

    repo = resolve_repo_root(args.repo_root)
    if not repo:
        msg = "could not resolve a project root (not a git repo; no .openup/ or scripts/ found)"
        if args.json:
            print(json.dumps({"error": msg, "findings": []}))
        else:
            print(f"openup-doctor: {msg}", file=sys.stderr)
        return 2

    findings = detect_all(repo, args.framework_path)

    applied: list[str] = []
    if args.fix:
        findings, applied = apply_fixes(repo, findings, args.confirm, args.framework_path)

    proposals = unapplied_proposals(findings, args.confirm)
    has_error = any(f.severity == ERROR for f in findings)

    if args.json:
        print(json.dumps({
            "repo_root": repo,
            "ok": not has_error,
            "fixed": args.fix,
            "applied": applied,
            "findings": [f.as_dict() for f in findings],
        }, indent=2))
    else:
        if applied:
            print("Applied fixes:")
            for line in applied:
                print(f"  · {line}")
            print()
        print(render_human(findings))
        if proposals:
            print("\nConfirm-class proposals (re-run with --fix --confirm to apply):")
            for f in proposals:
                print(f"  ? [{f.check}] {f.message}")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""check-docs.py — OpenUP hook: validate the work-product trace web (T-039).

A project-side PreToolUse hook. Fires before every shell command and lets
non-git commands through; on a ``git commit``, runs the work-product
validator (``scripts/check-docs.py``) and blocks the commit if the diff
introduces a schema / dangling-ref / broken-link error, or a
required-severity coverage gap (``--coverage``). Advisory coverage gaps
are surfaced for the model to see but do NOT block.

Strictness is project-tailorable through ``docs/project-config.yaml``
(T-039), without code changes::

    trace_rules:
      enabled: true                       # default true; set false to skip the hook
      coverage: true                      # default true; set false to drop --coverage
      severity:
        # downgrade or promote individual rules:
        "requirement -> verified-by -> test-case": advisory
        "work-item -> traces-from -> requirement": required

A `severity:` override changes the rule's effective severity for *this
project* — the framework's trace-model.json is never edited. Setting
``coverage: false`` disables the coverage pass entirely (the hard schema /
ref / link checks still run).

Decision logic:
  1. If tool != Bash or command does not look like ``git commit`` → allow.
  2. If ``scripts/check-docs.py`` is missing → allow (fail-open: a fresh
     project without the validator installed should never be bricked).
  3. Read ``docs/project-config.yaml`` ``trace_rules:`` (if any) to know
     whether to run, whether to include ``--coverage``, and which rules
     to remap.
  4. Run the validator; on a hard failure, exit 2 with a guidance
     message on stderr. The model sees that message and resolves the
     gap before retrying the commit.

Exit codes:
  0 — allow the commit
  2 — block; the model sees the redirect guidance on stderr

Fail-open: any internal error (subprocess, YAML parse, etc.) allows the
commit (a buggy gate must never brick the user's editing session).

Hook event: PreToolUse / Bash
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Heuristic: a ``git commit`` invocation. We do not want to fire on
# ``git commit-tree`` or unrelated `commit` substrings inside other args.
_GIT_COMMIT_RE = re.compile(r"(^|\s|;|&&|\|\|)git(\s+-[^ ]+)*\s+commit(\s|$)")


def repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.CalledProcessError):
        pass
    return Path.cwd()


def parse_simple_yaml(text: str) -> dict:
    """Tiny project-config YAML reader — enough for the keys this hook reads.

    Supports a top-level ``trace_rules:`` mapping with scalar children
    (``enabled``, ``coverage``) and a nested ``severity:`` mapping of
    ``"rule key": severity`` entries. Avoids a PyYAML dep so the hook
    runs on a stdlib-only project.
    """
    out = {}
    cur_top = None
    cur_sub = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        # Top-level: 0 indent, "key: value-or-empty"
        if not line.startswith(" "):
            cur_top = None
            cur_sub = None
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if not val:
                out[key] = {}
                cur_top = key
            else:
                out[key] = _scalar(val)
            continue
        # Indented child of cur_top.
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if cur_top is None:
            continue
        if indent == 2:
            cur_sub = None
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if not val:
                out[cur_top][key] = {}
                cur_sub = key
            else:
                out[cur_top][key] = _scalar(val)
        elif indent >= 4 and cur_sub is not None:
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip().strip('"').strip("'")
            val = val.strip().strip('"').strip("'")
            out[cur_top][cur_sub][key] = _scalar(val)
    return out


def _scalar(raw: str):
    s = raw.strip().strip('"').strip("'")
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    return s


def load_config(root: Path) -> dict:
    """Return the parsed ``trace_rules:`` block, or ``{}`` when absent."""
    p = root / "docs" / "project-config.yaml"
    if not p.is_file():
        return {}
    try:
        cfg = parse_simple_yaml(p.read_text(encoding="utf-8"))
    except OSError:
        return {}
    return cfg.get("trace_rules") or {}


def remap_severity(stderr_text: str, overrides: dict) -> tuple[bool, list]:
    """Apply project-side severity overrides to the validator's JSON output.

    Returns (has_required_failure, lines). ``has_required_failure`` is
    True when at least one finding is hard after the overrides.
    """
    # We only enter this path when --json was used and produced valid JSON.
    try:
        data = json.loads(stderr_text)
    except (json.JSONDecodeError, ValueError):
        return True, []
    findings = data.get("findings", [])
    has_required = False
    lines = []
    for f in findings:
        code = f.get("code") or ""
        message = f.get("message") or ""
        file_ = f.get("file") or ""
        severity = None
        if code == "coverage-gap" and message.startswith("["):
            # Extract original severity from "[required] type -> rel -> tgt …"
            close = message.find("]")
            severity = message[1:close].strip() if close > 1 else None
            # Extract rule key from "type has no relation -> target (status=...)"
            m = re.search(r"(\S+) has no (\S+) -> (\S+)", message)
            if m and severity is not None:
                key = f"{m.group(1)} -> {m.group(2)} -> {m.group(3)}"
                override = overrides.get(key)
                if override and override != severity:
                    # Rewrite the displayed severity tag.
                    message = "[" + override + "]" + message[close + 1:]
                    severity = override
        is_hard = code != "coverage-gap" or (severity or "required") != "advisory"
        if is_hard:
            has_required = True
        lines.append(f"{file_}: [{code}] {message}")
    return has_required, lines


def looks_like_git_commit(command: str) -> bool:
    if not command:
        return False
    # Strip leading env assignments like FOO=bar before the heuristic.
    stripped = re.sub(r"^(?:\w+=\S+\s+)+", "", command.strip())
    return bool(_GIT_COMMIT_RE.search(stripped))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # fail-open
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not looks_like_git_commit(command):
        return 0

    root = repo_root()
    cfg = load_config(root)
    enabled = cfg.get("enabled", True)
    if enabled is False:
        return 0
    coverage = cfg.get("coverage", True) is not False
    severity_overrides = cfg.get("severity") or {}

    validator = root / "scripts" / "check-docs.py"
    if not validator.is_file():
        return 0  # fresh project / not installed yet

    args = [sys.executable, str(validator), "--json"]
    if coverage:
        args.append("--coverage")

    try:
        proc = subprocess.run(args, capture_output=True, text=True,
                              cwd=str(root), timeout=30)
    except (OSError, subprocess.SubprocessError):
        return 0  # fail-open

    # --json puts the report on stdout. Parse it through the severity remap so
    # project tailoring decides what is hard. If there are no overrides we can
    # short-circuit on the validator's own exit code.
    if proc.returncode == 0 and not severity_overrides:
        return 0
    if not severity_overrides:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(
            "\nBlocked: check-docs reported hard failures. "
            "Fix the work-product trace before committing — re-run the "
            "originating /openup-create-* skill rather than hand-editing "
            "the instance frontmatter. See "
            "docs-eng-process/doc-frontmatter.md.\n")
        return 2

    has_required, lines = remap_severity(proc.stdout, severity_overrides)
    if not has_required:
        # All survivors are advisory after tailoring; surface them and pass.
        for line in lines:
            sys.stderr.write(line + "\n")
        return 0
    for line in lines:
        sys.stderr.write(line + "\n")
    sys.stderr.write(
        "\nBlocked: check-docs reported hard failures (after applying "
        "trace_rules: severity overrides). Fix the work-product trace "
        "before committing — see docs-eng-process/doc-frontmatter.md.\n")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        # Fail-open on any unexpected error.
        raise SystemExit(0)

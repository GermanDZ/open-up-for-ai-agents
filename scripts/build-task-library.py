#!/usr/bin/env python3
"""OpenUP task-library compiler (T-105) — sibling of build-trace-model.py.

Compiles the vendored KB authoring task files into the lean-task library
``docs-eng-process/task-library.yaml`` (object code the engine consumes at T-106).
Two-stage, mirroring build-trace-model's derived-artifact discipline:

  Stage 1 — deterministic extraction (no LLM). Parse a KB task file's regular
    UMA structure (frontmatter ``title`` + ``related.roles``; the ``Inputs|``
    section's workproduct links) into the def *skeleton*: ``name``, ``role``
    (primary performer), ``inputs`` (input workproduct display names).

  Stage 2 — LLM distillation (compile-time only). Distill the task's prose into
    the 3–8 ``judgment`` bullets, via any OpenAI-compatible endpoint
    (``openup_agent/llm.py``), anchored by one hand-calibrated example. Compile
    with a STRONG model; the output is human-reviewed before commit.
    ``--offline`` emits the distillation prompt to a file instead of calling the
    endpoint (usable with no endpoint; complete/review out of band).

  ``--check`` — drift mode. Re-extract each committed def's Stage-1 skeleton from
    its ``source`` and diff against the committed library; exit 1 on drift.
    Prose-distillation (``judgment``) drift is advisory only — regeneration is a
    human-reviewed act, not a CI-automatic one (same stance as the KB re-distill).

The library's ``artifact``/``output_path`` are the framework's primary-spine-output
decision (authored, not extracted); the skeleton diff covers only the
deterministically-derivable ``name``/``role``/``inputs``.

Exit codes:  0 ok / in-sync    1 --check drift    2 usage / could-not-run
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EXIT_OK, EXIT_DRIFT, EXIT_USAGE = 0, 1, 2

# Import the hyphenated process-map module for load_tasks (single source of the
# parser + spine enum — no duplication).
_pm_spec = importlib.util.spec_from_file_location(
    "openup_process_map", SCRIPT_DIR / "openup-process-map.py")
_pm = importlib.util.module_from_spec(_pm_spec)
_pm_spec.loader.exec_module(_pm)  # type: ignore[union-attr]


def repo_root() -> Path:
    import subprocess
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        if top:
            return Path(top)
    except (OSError, subprocess.CalledProcessError):
        pass
    return SCRIPT_DIR.parent


# ── Stage 1: deterministic extraction ────────────────────────────────────────
def _frontmatter(text: str) -> tuple[dict, list]:
    """Return (scalars, roles) from the KB task file's YAML frontmatter. Tiny
    hand-parser (no pyyaml): scalar ``key: value`` lines + the ``related.roles``
    bulleted list."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, []
    scalars, roles = {}, []
    in_roles = False
    for raw in lines[1:]:
        if raw.strip() == "---":
            break
        if re.match(r"^  roles:\s*$", raw):
            in_roles = True
            continue
        if in_roles:
            m = re.match(r"^  - (\S+)", raw)
            if m:
                roles.append(m.group(1))
                continue
            in_roles = False
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", raw)
        if m:
            scalars[m.group(1)] = m.group(2).strip()
    return scalars, roles


def _extract_inputs(text: str) -> list:
    """Input workproduct display names from the ``Inputs|`` section (Mandatory +
    Optional), in order, skipping ``None``. Unescapes ``\\[`` / ``\\]``."""
    inputs: list = []
    in_inputs = False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("Inputs|"):
            in_inputs = True
            continue
        if in_inputs and (s.startswith("Outputs|") or s == "Steps"
                          or s.startswith("Steps")):
            break
        if in_inputs and s.startswith("* ["):
            m = re.search(r"\*\s*\[\\?\[?([^\]\\]+)\\?\]?\]", s)
            if m:
                name = m.group(1).strip()
                if name and name.lower() != "none" and name not in inputs:
                    inputs.append(name)
    return inputs


def _primary_role(roles: list) -> str:
    """First performer, KB slug stripped of its trailing ``-N`` (``analyst-6`` →
    ``analyst``)."""
    if not roles:
        return ""
    return re.sub(r"-\d+$", "", roles[0])


def extract_skeleton(text: str) -> dict:
    """Stage-1 skeleton from a KB task file: {name, role, inputs}."""
    scalars, roles = _frontmatter(text)
    return {
        "name": scalars.get("title", "").strip(),
        "role": _primary_role(roles),
        "inputs": _extract_inputs(text),
    }


# ── Stage 2: LLM distillation ────────────────────────────────────────────────
_STYLE_ANCHOR = """\
Example — for the task "Develop Technical Vision" the judgment bullets are:
- States the problem and who has it before proposing any solution.
- Names the stakeholders and what each needs from the system.
- Lists 3–7 system features at capability granularity, not implementation tasks.
- Defines the solution scope — what is in and, explicitly, what is out.
- Captures the shared vocabulary (key terms) the rest of the docs rely on."""


def distillation_prompt(task_name: str, kb_text: str) -> str:
    """The compile-time prompt: distill KB prose → 3–8 what-good-looks-like
    ``judgment`` bullets. Schema-strict, style-anchored."""
    return (
        f"You are compiling an OpenUP task definition. Distill the task below into "
        f"3 to 6 '{task_name}' judgment bullets: terse, imperative statements of "
        f"WHAT A GOOD ARTIFACT LOOKS LIKE — not steps to perform. Output ONLY the "
        f"bullets, one per line, each starting with '- '.\n\n"
        f"{_STYLE_ANCHOR}\n\n"
        f"--- KB task source for \"{task_name}\" ---\n{kb_text}\n--- end ---"
    )


def distill_judgment(task_name: str, kb_text: str, api_url: str, api_key: str,
                     model: str) -> list:
    """Call the endpoint and parse the returned bullets. Compile-time only."""
    llm_spec = importlib.util.spec_from_file_location(
        "openup_agent_llm", SCRIPT_DIR / "openup_agent" / "llm.py")
    llm = importlib.util.module_from_spec(llm_spec)
    llm_spec.loader.exec_module(llm)  # type: ignore[union-attr]
    messages = [{"role": "user", "content": distillation_prompt(task_name, kb_text)}]
    resp = llm.chat_completion(api_url, api_key, model, messages, temperature=0)
    content = llm.first_message(resp).get("content", "")
    return [ln.strip()[2:].strip() for ln in content.splitlines()
            if ln.strip().startswith("- ")]


# ── --check drift ────────────────────────────────────────────────────────────
_SKELETON_FIELDS = ("name", "role", "inputs")


def check_drift(root: Path) -> tuple[int, list]:
    """Re-extract each KB-sourced def's skeleton and diff vs the committed
    library. Returns (drift_count, messages)."""
    tasks = _pm.load_tasks(root)
    msgs: list = []
    drift = 0
    for tid, d in tasks.items():
        source = str(d.get("source", "")).strip()
        if source == "driver" or not source:
            continue  # driver-native def: no KB skeleton to re-extract
        kb = root / source
        if not kb.exists():
            msgs.append(f"drift: {tid}: source not found ({source})")
            drift += 1
            continue
        fresh = extract_skeleton(kb.read_text(encoding="utf-8"))
        for f in _SKELETON_FIELDS:
            if d.get(f) != fresh.get(f):
                msgs.append(f"drift: {tid}.{f}: committed {d.get(f)!r} != extracted {fresh.get(f)!r}")
                drift += 1
    return drift, msgs


# ── CLI ──────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", help="repo root (default: git toplevel)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="re-extract skeletons and diff vs the committed library")
    mode.add_argument("--offline", metavar="DIR",
                      help="emit each task's distillation prompt into DIR (no LLM call)")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root()

    if args.check:
        try:
            drift, msgs = check_drift(root)
        except FileNotFoundError as exc:
            print(f"[task-library] {exc}", file=sys.stderr)
            return EXIT_USAGE
        for m in msgs:
            print(m, file=sys.stderr)
        if drift:
            print(f"[task-library] ✗ {drift} skeleton drift(s) — re-run build-task-library.py",
                  file=sys.stderr)
            return EXIT_DRIFT
        print("[task-library] ✓ skeletons in sync with KB sources")
        return EXIT_OK

    if args.offline:
        try:
            tasks = _pm.load_tasks(root)
        except FileNotFoundError as exc:
            print(f"[task-library] {exc}", file=sys.stderr)
            return EXIT_USAGE
        out_dir = Path(args.offline)
        out_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for tid, d in tasks.items():
            source = str(d.get("source", "")).strip()
            if source == "driver" or not source:
                continue
            kb = root / source
            if not kb.exists():
                continue
            prompt = distillation_prompt(d.get("name", tid), kb.read_text(encoding="utf-8"))
            (out_dir / f"{tid}.prompt.txt").write_text(prompt, encoding="utf-8")
            n += 1
        print(f"[task-library] wrote {n} distillation prompt(s) to {out_dir}")
        return EXIT_OK

    # Default: online compile requires an endpoint + model.
    api_url = os.environ.get("LLM_API_URL")
    model = os.environ.get("OPENUP_COMPILE_MODEL") or os.environ.get("LLM_MODEL")
    if not api_url or not model:
        print("[task-library] online compile needs LLM_API_URL + "
              "OPENUP_COMPILE_MODEL (or LLM_MODEL). Use --offline to emit prompts, "
              "or --check to verify skeletons.", file=sys.stderr)
        return EXIT_USAGE
    api_key = os.environ.get("LLM_API_KEY", "")
    try:
        tasks = _pm.load_tasks(root)
    except FileNotFoundError as exc:
        print(f"[task-library] {exc}", file=sys.stderr)
        return EXIT_USAGE
    for tid, d in tasks.items():
        source = str(d.get("source", "")).strip()
        if source == "driver" or not source:
            continue
        kb = root / source
        if not kb.exists():
            continue
        bullets = distill_judgment(d.get("name", tid), kb.read_text(encoding="utf-8"),
                                   api_url, api_key, model)
        print(f"[task-library] {tid}: distilled {len(bullets)} bullet(s) "
              f"(review before commit)")
    print("[task-library] compile complete — review the diff, then commit.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

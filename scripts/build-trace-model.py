#!/usr/bin/env python3
"""Derive the OpenUP work-product trace model from the vendored KB (T-035).

The valid trace relationships between work products are not arbitrary — they are
OpenUP's defined work-product flow (Vision -> Requirements -> Work Items ->
Iteration Plan -> Use Cases -> Test Cases). This tool emits that model to
``scripts/trace-model.json`` so the validator (``check-docs.py``, T-036) and the
index generator (T-037) read one machine-readable contract instead of
hard-coding edges.

The model is **derived from the read-only KB**, never edited into it:

  * The KB manifest (``openup-knowledge-base/manifest.json``) supplies the
    work-product *taxonomy* — which slugs are work products — and the
    *associations* between them via each entry's ``related.workproducts`` (e.g.
    the ``requirements-1`` Domain co-lists vision + system-wide-requirements +
    use-case, the ``use-case-driven-development`` Practice co-lists use-case +
    system-wide-requirements). Co-listed work products imply an undirected
    association.
  * Those associations are projected onto the v1 instance ``type`` set
    (docs-meta.schema.json) through a documented slug->type alias map and used to
    **corroborate** edges (``kb_corroborated``).
  * The *direction* of each edge is OpenUP-canonical knowledge (a requirement
    refines a vision; a test verifies a requirement). The generator encodes that
    spine and tags each edge ``kb_corroborated: true`` when the KB independently
    associates its endpoints, ``false`` when the edge is OpenUP-canonical only
    (the current KB snapshot does not link the pair).

Determinism: every collection is sorted and the JSON is emitted with sorted keys
and no timestamps, so regenerating on an unchanged KB is byte-for-byte stable
(guarded by ``--check``).

Subcommands / modes:
  (default)   Write scripts/trace-model.json and print a one-line summary.
  --stdout    Print the model JSON to stdout; do not write the file.
  --check     Regenerate and compare to the committed file; exit 1 on drift.

Exit codes:
  0  success (or --check: in sync)
  1  --check: committed trace-model.json is stale / drifted
  2  usage / environment error (missing or unreadable KB manifest)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2

SCHEMA_VERSION = 1

# v1 instance types (must match scripts/docs-meta.schema.json `type` enum).
V1_TYPES = (
    "vision",
    "requirement",
    "work-item",
    "iteration-plan",
    "use-case",
    "test-case",
    "decision",
)

# KB work-product slug -> v1 instance type. The KB names several slugs per family
# (use-case / use-case-model / use-case-specification all describe the use-case
# work product); this map projects them onto the spine. `decision` is a
# project-level work product with no base-OpenUP KB slug, so it has no alias —
# its edges are necessarily OpenUP-canonical.
SLUG_TO_TYPE = {
    "vision": "vision",
    "system-wide-requirements": "requirement",
    "use-case": "use-case",
    "use-case-model": "use-case",
    "use-case-specification": "use-case",
    "work-items-list": "work-item",
    "iteration-plan": "iteration-plan",
    "test-case": "test-case",
    "test-script": "test-case",
    "test-log": "test-case",
}

# OpenUP-canonical trace spine: (child, parent, relation). `child` carries the
# field, pointing upstream at `parent`. `traces-from` is the refine/satisfy
# direction; `verified-by` is coverage (a work product names the tests that
# verify it).
TRACE_SPINE = (
    ("requirement", "vision", "traces-from"),
    ("use-case", "requirement", "traces-from"),
    ("work-item", "requirement", "traces-from"),
    ("iteration-plan", "work-item", "traces-from"),
    ("test-case", "use-case", "traces-from"),
    ("test-case", "requirement", "traces-from"),
    ("decision", "vision", "traces-from"),
)

# Required-coverage rules: a `type` instance MUST carry `relation` -> a `target`
# instance. Severity is the model's recommendation; projects can downgrade it to
# advisory via project-config (T-039).
COVERAGE_RULES = (
    ("requirement", "verified-by", "test-case", "required"),
    ("work-item", "traces-from", "requirement", "required"),
)


def repo_root() -> Path:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if top:
            return Path(top)
    except (OSError, subprocess.CalledProcessError):
        pass
    return SCRIPT_DIR.parent


def manifest_path(root: Path) -> Path:
    return root / "openup-knowledge-base" / "manifest.json"


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def kb_associations(manifest: dict) -> set:
    """Undirected associations between v1 types implied by the KB.

    For every KB entry, collect the v1 types named by the entry's own slug and by
    its ``related.workproducts``; every pair within that set is associated.
    Returns a set of frozenset({a, b}) (a != b).
    """
    assoc = set()
    for entry in manifest.get("files", []):
        slugs = list(entry.get("related", {}).get("workproducts", []) or [])
        slugs.append(entry.get("slug", ""))
        types = {SLUG_TO_TYPE[s] for s in slugs if s in SLUG_TO_TYPE}
        for a in types:
            for b in types:
                if a < b:
                    assoc.add(frozenset((a, b)))
    return assoc


def build_model(manifest: dict) -> dict:
    """Build the deterministic trace model dict from a KB manifest."""
    assoc = kb_associations(manifest)

    def corroborated(a: str, b: str) -> bool:
        return frozenset((a, b)) in assoc

    trace_edges = [
        {
            "from": child,
            "to": parent,
            "relation": relation,
            "kb_corroborated": corroborated(child, parent),
        }
        for child, parent, relation in TRACE_SPINE
    ]
    trace_edges.sort(key=lambda e: (e["from"], e["to"], e["relation"]))

    coverage_rules = [
        {
            "type": typ,
            "relation": relation,
            "target": target,
            "severity": severity,
            "kb_corroborated": corroborated(typ, target),
        }
        for typ, relation, target, severity in COVERAGE_RULES
    ]
    coverage_rules.sort(key=lambda r: (r["type"], r["relation"], r["target"]))

    return {
        "schema": SCHEMA_VERSION,
        "generated_by": "scripts/build-trace-model.py",
        "kb_source": "openup-knowledge-base/manifest.json",
        "kb_version": manifest.get("version"),
        "types": sorted(V1_TYPES),
        "slug_aliases": dict(sorted(SLUG_TO_TYPE.items())),
        "kb_associations": sorted(sorted(pair) for pair in assoc),
        "trace_edges": trace_edges,
        "coverage_rules": coverage_rules,
    }


def serialize(model: dict) -> str:
    """Deterministic JSON text (trailing newline) for the model."""
    return json.dumps(model, indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stdout", action="store_true",
                      help="print the model JSON to stdout; do not write a file")
    mode.add_argument("--check", action="store_true",
                      help="compare committed trace-model.json to a fresh "
                           "generation; exit 1 on drift")
    parser.add_argument("--manifest", help="override KB manifest path")
    parser.add_argument("--out", help="override output trace-model.json path")
    args = parser.parse_args(argv)

    root = repo_root()
    mpath = Path(args.manifest) if args.manifest else manifest_path(root)
    if not mpath.is_file():
        print(f"error: KB manifest not found: {mpath}", file=sys.stderr)
        return EXIT_USAGE
    try:
        manifest = load_manifest(mpath)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read KB manifest {mpath}: {exc}", file=sys.stderr)
        return EXIT_USAGE

    model = build_model(manifest)
    text = serialize(model)
    out = Path(args.out) if args.out else (SCRIPT_DIR / "trace-model.json")

    if args.stdout:
        sys.stdout.write(text)
        return EXIT_OK

    if args.check:
        if not out.is_file():
            print(f"drift: {out} is missing; run build-trace-model.py",
                  file=sys.stderr)
            return EXIT_DRIFT
        current = out.read_text(encoding="utf-8")
        if current != text:
            print(f"drift: {out} is stale; re-run build-trace-model.py",
                  file=sys.stderr)
            return EXIT_DRIFT
        print(f"trace-model.json in sync ({len(model['trace_edges'])} edges, "
              f"{len(model['coverage_rules'])} coverage rules)")
        return EXIT_OK

    out.write_text(text, encoding="utf-8")
    kb_edges = sum(1 for e in model["trace_edges"] if e["kb_corroborated"])
    print(f"wrote {out} — {len(model['trace_edges'])} trace edges "
          f"({kb_edges} KB-corroborated), "
          f"{len(model['coverage_rules'])} coverage rules")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

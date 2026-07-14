#!/usr/bin/env python3
"""OpenUP work-product validator core (T-036) + coverage mode (T-037).

The mechanical backbone for keeping a project's ``docs/`` linked, traceable, and
validated. ``check-docs.py`` walks every Markdown work-product *instance* under
``docs/`` and enforces three hard invariants:

  1. **Schema** — instance frontmatter validates against
     ``scripts/docs-meta.schema.json`` (T-034): a ``type`` from the v1 spine, a
     known ``status``, hyphenated trace keys, no stray fields.
  2. **Resolvable references** — every trace-ref id (``traces-from``,
     ``verified-by``) resolves to a real instance id, and every relative ``.md``
     link in an instance's body points to a file that exists. Dangling ids and
     broken links are hard failures.
  3. **Bidirectional / type consistency** — a ``verified-by`` id must name a
     ``test-case`` instance; a ``traces-from`` id must name a type that is a valid
     upstream parent per the KB-derived ``trace-model.json`` (T-035). Two
     instances sharing an ``id`` is a collision.

An *instance* is any ``docs/**/*.md`` whose frontmatter ``type`` is one of the
spine work-product types. Template files (``type: Template``) and untyped notes
are skipped, so template provenance and instance semantics never collide.

With ``--coverage`` (T-037) the validator additionally evaluates the
required-coverage rules from ``trace-model.json``: e.g. every non-draft
``requirement`` needs a ``verified-by`` ``test-case``; every non-draft
``work-item`` needs to ``traces-from`` a ``requirement``. A coverage gap with
severity ``required`` is a hard failure (exit 1); ``advisory`` gaps are
reported but do not fail the run. Project-side tailoring downgrades a rule
from required to advisory (T-039); the CLI itself never invents rules.

Output:
  human (default)  grouped, file:line-style findings + a one-line summary.
  --json           machine-readable {"ok", "instances", "findings":[...]}.

Exit codes:
  0  no hard failures
  1  one or more hard failures (schema / dangling ref / broken link / bad type
     / required-coverage gap)
  2  usage / environment error
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = SCRIPT_DIR / "docs-meta.schema.json"
TRACE_MODEL_PATH = SCRIPT_DIR / "trace-model.json"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

# Reuse the one canonical frontmatter parser (hyphenated filename -> importlib),
# exactly as openup-input.py does, so instance and plan frontmatter are read the
# same way everywhere.
_CLAIMS_PATH = SCRIPT_DIR / "openup-claims.py"
_spec = importlib.util.spec_from_file_location("openup_claims", _CLAIMS_PATH)
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]

# Markdown inline link: [text](target). We only police relative .md targets.
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_EXTERNAL_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)  # scheme: …


# --------------------------------------------------------------------------
# Focused JSON-schema validator (mirrors openup-state.py; adds array `items`).
# --------------------------------------------------------------------------
_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _type_ok(value, type_spec) -> bool:
    types = type_spec if isinstance(type_spec, list) else [type_spec]
    return any(_TYPE_CHECKS[t](value) for t in types if t in _TYPE_CHECKS)


def _validate_node(value, schema, path, errors):
    loc = path or "<root>"
    type_spec = schema.get("type")
    if type_spec is not None and not _type_ok(value, type_spec):
        errors.append(f"{loc}: expected type {type_spec}, "
                      f"got {type(value).__name__}")
        return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{loc}: {value!r} not in allowed values {schema['enum']}")
    if isinstance(value, dict) and (
        type_spec == "object"
        or (isinstance(type_spec, list) and "object" in type_spec)
        or "properties" in schema
    ):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{loc}: missing required property '{req}'")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{loc}: additional property '{key}' "
                                  f"not allowed")
        for key, subval in value.items():
            if key in props:
                child = f"{loc}.{key}" if path else key
                _validate_node(subval, props[key], child, errors)
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            _validate_node(item, schema["items"], f"{loc}[{i}]", errors)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Model: an Instance + a Finding.
# --------------------------------------------------------------------------
class Finding:
    __slots__ = ("file", "code", "message")

    def __init__(self, file, code, message):
        self.file = file
        self.code = code
        self.message = message

    def as_dict(self):
        return {"file": self.file, "code": self.code, "message": self.message}


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


# --------------------------------------------------------------------------
# Development Case: the `process:` section of docs/project-config.yaml (T-076).
#
# OpenUP's Development Case made machine-readable — an `archetype` (quick | mvp |
# product) setting per-phase defaults, optionally overridden per phase. Validated
# structurally here (stdlib-only, no PyYAML: consuming projects run these scripts
# with stdlib only). The loop consumers are T-077 (plan-iteration) / T-078
# (milestone-review); this task only defines + validates the section.
# --------------------------------------------------------------------------
PROCESS_ALLOWED_KEYS = {"archetype", "phases", "milestone_review"}
PROCESS_ARCHETYPES = {"quick", "mvp", "product"}
PROCESS_PHASE_NAMES = {"inception", "elaboration", "construction", "transition"}
PROCESS_PHASE_KEYS = {"iterations", "artifacts", "exit", "parallel", "gate"}
PROCESS_ITER_WORDS = {"auto", "many", "skip"}
PROCESS_MILESTONE_REVIEW = {"human", "auto-assess"}
PROCESS_GATE_VALUES = {"human", "auto"}

# Per-archetype default sets. `quick` deliberately degenerates to today's
# /openup-quick-task ceremony (near-empty Inception, Elaboration skipped, one
# Construction iteration, auto-assessed milestones) — the token-efficiency
# guardrail from the phase-aware redesign. Documented in
# docs-eng-process/project-config.md.
PROCESS_ARCHETYPE_DEFAULTS = {
    "quick": {
        "phases": {
            "inception": {"iterations": 1, "artifacts": []},
            "elaboration": {"iterations": "skip"},
            "construction": {"iterations": 1, "parallel": False},
            "transition": {"gate": "auto"},
        },
        "milestone_review": "auto-assess",
    },
    "mvp": {
        "phases": {
            "inception": {"iterations": 1,
                          "artifacts": ["vision", "use-case-outline", "risk-list"]},
            "elaboration": {"iterations": 1, "artifacts": ["architecture-notebook"],
                            "exit": "architecture-validated"},
            "construction": {"iterations": "many", "parallel": False},
            "transition": {"gate": "human"},
        },
        "milestone_review": "human",
    },
    "product": {
        "phases": {
            "inception": {"iterations": 1,
                          "artifacts": ["vision", "use-case-outline", "risk-list"]},
            "elaboration": {"iterations": "auto",
                            "artifacts": ["architecture-notebook",
                                          "detailed-use-cases", "test-plan"],
                            "exit": "architecture-validated"},
            "construction": {"iterations": "many", "parallel": True},
            "transition": {"gate": "human"},
        },
        "milestone_review": "human",
    },
}


def _process_split_commas(s):
    """Split on commas at flow-bracket depth 0 (respects [...] and {...})."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "[{":
            depth += 1
            cur += ch
        elif ch in "]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _process_strip_comment(line):
    """Drop a trailing ` # comment` outside flow brackets. Process values are
    simple enough (enums, ints, identifier lists) that a bare '#' never appears
    legitimately."""
    depth = 0
    for i, ch in enumerate(line):
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "#" and depth == 0 and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _process_atom(tok):
    tok = tok.strip()
    if tok == "":
        return None
    low = tok.lower()
    if low in ("true", "false"):
        return low == "true"
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if len(tok) >= 2 and tok[0] in "'\"" and tok[-1] == tok[0]:
        return tok[1:-1]
    return tok


def _process_value(tok):
    tok = tok.strip()
    if tok.startswith("{") and tok.endswith("}"):
        out = {}
        for part in _process_split_commas(tok[1:-1]):
            if not part.strip():
                continue
            k, _, v = part.partition(":")
            out[k.strip()] = _process_value(v)
        return out
    if tok.startswith("[") and tok.endswith("]"):
        inner = tok[1:-1].strip()
        if not inner:
            return []
        return [_process_value(x) for x in _process_split_commas(inner)]
    return _process_atom(tok)


def _process_parse_map(items, pos, indent):
    """Parse an indentation-based mapping from `items` (list of (indent, content))
    at column `indent`, starting at index `pos`. Returns (dict, next_pos)."""
    out = {}
    while pos < len(items):
        ind, content = items[pos]
        if ind < indent:
            break
        if ind > indent:  # defensive: stray deeper line
            pos += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            if pos + 1 < len(items) and items[pos + 1][0] > indent:
                sub, pos = _process_parse_map(items, pos + 1, items[pos + 1][0])
                out[key] = sub
            else:
                out[key] = {}
                pos += 1
        else:
            out[key] = _process_value(rest)
            pos += 1
    return out, pos


def parse_process_section(text):
    """Extract and parse the top-level ``process:`` mapping from a
    project-config.yaml body. Returns a dict, or ``None`` if the section is
    absent. Stdlib-only; handles the documented shape (2-level nesting, inline
    flow maps ``name: { k: v, k: [a, b] }`` and block maps)."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^process:\s*(#.*)?$", ln.rstrip()):
            start = i
            break
    if start is None:
        return None
    items, base = [], None
    for ln in lines[start + 1:]:
        if ln.strip() == "" or ln.lstrip().startswith("#"):
            continue
        indent = len(ln) - len(ln.lstrip())
        if indent == 0:
            break
        if base is None:
            base = indent
        items.append((indent, _process_strip_comment(ln).strip()))
    if not items:
        return {}
    parsed, _ = _process_parse_map(items, 0, base)
    return parsed


def resolve_process(process):
    """Overlay an explicit ``process:`` dict onto its archetype default set.
    Explicit phase keys / milestone_review win over the archetype default; phases
    the config does not mention keep the archetype default. Returns the resolved
    dict (used by consumers + tests; validation is separate)."""
    import copy
    process = process or {}
    resolved = copy.deepcopy(PROCESS_ARCHETYPE_DEFAULTS.get(process.get("archetype"), {}))
    if process.get("milestone_review") is not None:
        resolved["milestone_review"] = process["milestone_review"]
    phases = process.get("phases")
    if isinstance(phases, dict):
        dst = resolved.setdefault("phases", {})
        for pname, pval in phases.items():
            if isinstance(pval, dict):
                dst.setdefault(pname, {}).update(pval)
            else:
                dst[pname] = pval
    return resolved


def validate_process_config(config_path: Path):
    """Structurally validate the ``process:`` section of ``config_path``. Returns
    a list of ``Finding`` (code ``process-config``). An absent file or absent
    section yields no findings (backward-compatible); a present-but-malformed
    section yields hard findings naming the offending key."""
    findings = []
    if not config_path.exists():
        return findings
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        findings.append(Finding(str(config_path), "process-config",
                                f"cannot read: {exc}"))
        return findings
    process = parse_process_section(text)
    if process is None:
        return findings  # no Development Case configured — fine

    where = str(config_path)

    def add(msg):
        findings.append(Finding(where, "process-config", msg))

    if not isinstance(process, dict):
        add("process: must be a mapping")
        return findings

    for key in process:
        if key not in PROCESS_ALLOWED_KEYS:
            add(f"unknown key 'process.{key}' (allowed: archetype, phases, "
                f"milestone_review; the section may only set ceremony, not waive "
                f"a framework safeguard)")

    archetype = process.get("archetype")
    if archetype is None:
        add("process: present but 'archetype' is missing "
            "(one of quick | mvp | product)")
    elif archetype not in PROCESS_ARCHETYPES:
        add(f"unknown archetype {archetype!r} (allowed: quick, mvp, product)")

    review = process.get("milestone_review")
    if review is not None and review not in PROCESS_MILESTONE_REVIEW:
        add(f"invalid milestone_review {review!r} (allowed: human, auto-assess)")

    phases = process.get("phases")
    if phases is not None:
        if not isinstance(phases, dict):
            add("process.phases must be a mapping of phase -> settings")
        else:
            for pname, pval in phases.items():
                if pname not in PROCESS_PHASE_NAMES:
                    add(f"unknown phase 'process.phases.{pname}' (allowed: "
                        f"inception, elaboration, construction, transition)")
                    continue
                if not isinstance(pval, dict):
                    add(f"process.phases.{pname} must be a mapping of settings")
                    continue
                for pk, pv in pval.items():
                    if pk not in PROCESS_PHASE_KEYS:
                        add(f"unknown setting 'process.phases.{pname}.{pk}' "
                            f"(allowed: iterations, artifacts, exit, parallel, gate)")
                    elif pk == "iterations":
                        if not (isinstance(pv, int) and not isinstance(pv, bool)) \
                                and pv not in PROCESS_ITER_WORDS:
                            add(f"process.phases.{pname}.iterations must be an int "
                                f"or one of auto | many | skip (got {pv!r})")
                    elif pk == "artifacts":
                        if not isinstance(pv, list):
                            add(f"process.phases.{pname}.artifacts must be a list")
                    elif pk == "parallel":
                        if not isinstance(pv, bool):
                            add(f"process.phases.{pname}.parallel must be a boolean")
                    elif pk == "gate":
                        if pv not in PROCESS_GATE_VALUES:
                            add(f"process.phases.{pname}.gate must be human | auto "
                                f"(got {pv!r})")
                    elif pk == "exit":
                        if not isinstance(pv, str):
                            add(f"process.phases.{pname}.exit must be a string")
    return findings


def discover_instances(docs_dir: Path, spine_types: set):
    """Yield (path, frontmatter) for every typed work-product instance.

    A file is an instance iff its frontmatter ``type`` is in the spine. Files
    with no frontmatter, or a non-spine ``type`` (templates, notes), are skipped.
    """
    if not docs_dir.is_dir():
        return
    for path in sorted(docs_dir.rglob("*.md")):
        if not path.is_file():
            continue
        fm = claims.parse_frontmatter(path)
        if fm and fm.get("type") in spine_types:
            yield path, fm


def relative_md_links(path: Path):
    """Yield relative .md link targets (anchor stripped) found in a file body."""
    text = path.read_text(encoding="utf-8")
    for raw in _LINK_RE.findall(text):
        target = raw.strip()
        if not target or target.startswith("#"):
            continue
        if _EXTERNAL_RE.match(target):  # http:, https:, mailto:, …
            continue
        if target.startswith("/"):  # site-absolute; out of scope
            continue
        base = target.split("#", 1)[0]
        if base.endswith(".md"):
            yield base


# Statuses for which a coverage rule is evaluated. A draft/obsolete instance
# does not yet need (or no longer needs) coverage — the gap would be noise.
# Hardcoded for v1: project tailoring tunes severity (T-039), not the filter.
COVERED_STATUSES = {"approved", "implemented", "verified"}


def coverage_findings(instances, id_index, model):
    """Evaluate every ``coverage_rules`` entry from ``trace-model.json``.

    A rule ``(type, relation, target, severity)`` says: every covered instance
    of ``type`` MUST carry at least one ``relation`` id whose target instance
    has type ``target``. A miss is emitted as ``coverage-gap`` with the rule's
    severity attached; ``required`` is a hard failure, ``advisory`` is not.
    """
    rules = model.get("coverage_rules") or []
    if not rules:
        return []
    out = []
    for path, fm in instances:
        rel = path  # already a relpath string in the caller
        this_type = fm.get("type")
        status = (fm.get("status") or "").lower()
        if status and status not in COVERED_STATUSES:
            continue  # draft/obsolete: no coverage expectation
        for rule in rules:
            if rule.get("type") != this_type:
                continue
            relation = rule.get("relation")
            target = rule.get("target")
            severity = (rule.get("severity") or "required").lower()
            refs = _as_list(fm.get(relation))
            covered = False
            for ref in refs:
                for ref_type, _ in id_index.get(ref, []):
                    if ref_type == target:
                        covered = True
                        break
                if covered:
                    break
            if not covered:
                out.append(Finding(
                    rel, "coverage-gap",
                    f"[{severity}] {this_type} has no {relation} -> {target} "
                    f"(status={status or 'unspecified'})"))
    return out


def check(docs_dir: Path, schema: dict, model: dict, coverage: bool = False):
    """Run all checks. Return (findings, instance_count).

    ``coverage`` adds the ``trace-model.json`` required-coverage evaluation
    (T-037). The hard exit code only counts ``required``-severity gaps;
    advisory gaps are visible in output but do not fail the run.
    """
    spine_types = set(model.get("types") or
                      schema["properties"]["type"]["enum"])
    # allowed (from_type -> to_type) for traces-from edges. When the model is
    # absent or has no traces-from edges, leave this as None so the upstream-type
    # check is skipped (schema + ref-existence still run); an empty set would
    # otherwise reject every traces-from ref as bad-ref-type.
    trace_edges = None
    if model.get("trace_edges"):
        trace_edges = {
            (e["from"], e["to"])
            for e in model["trace_edges"]
            if e.get("relation") == "traces-from"
        }

    findings = []
    instances = list(discover_instances(docs_dir, spine_types))

    # id index: id -> list of (type, relpath) for dup detection + ref resolution.
    id_index = {}
    for path, fm in instances:
        rel = str(path.relative_to(docs_dir.parent)) \
            if docs_dir.parent in path.parents else str(path)
        iid = fm.get("id")
        if isinstance(iid, str) and iid:
            id_index.setdefault(iid, []).append((fm.get("type"), rel))

    # Change folders ARE the work-item instances in this system (T-090): the
    # board, claims, and the cycle engine all key a work item by its
    # docs/changes/<id>/ folder, whose plan.md is a task-spec (status ready→done),
    # not a typed maturity instance. So a work-product may `traces-from` a
    # change-folder id — most notably a cycle-planned iteration-plan tracing its
    # I1-00x/C1-00x lanes. Register each change folder as an implicit `work-item`
    # so those refs resolve (the trace model already allows iteration-plan →
    # work-item). A real typed instance with the same id always wins.
    changes_dir = docs_dir / "changes"
    for base in (changes_dir, changes_dir / "archive"):
        if not base.is_dir():
            continue
        for folder in sorted(base.iterdir()):
            if folder.name == "archive" or not folder.is_dir():
                continue
            if (folder / "plan.md").exists() and folder.name not in id_index:
                id_index.setdefault(folder.name, []).append(
                    ("work-item", str(folder.relative_to(docs_dir.parent))))

    for iid, entries in sorted(id_index.items()):
        if len(entries) > 1:
            where = ", ".join(p for _, p in entries)
            findings.append(Finding(
                entries[0][1], "duplicate-id",
                f"id '{iid}' declared by {len(entries)} instances: {where}"))

    for path, fm in instances:
        rel = str(path.relative_to(docs_dir.parent)) \
            if docs_dir.parent in path.parents else str(path)

        # 1. schema
        schema_errors = []
        _validate_node(fm, schema, "", schema_errors)
        for err in schema_errors:
            findings.append(Finding(rel, "schema", err))

        this_type = fm.get("type")

        # 2/3. traces-from — resolvable + valid upstream type.
        for ref in _as_list(fm.get("traces-from")):
            if ref not in id_index:
                findings.append(Finding(
                    rel, "dangling-ref",
                    f"traces-from id '{ref}' does not resolve to any instance"))
                continue
            if trace_edges is None:
                continue  # model unavailable: skip type-direction enforcement
            for ref_type, _ in id_index[ref]:
                if (this_type, ref_type) not in trace_edges:
                    findings.append(Finding(
                        rel, "bad-ref-type",
                        f"traces-from '{ref}' is a '{ref_type}', not a valid "
                        f"upstream for a '{this_type}'"))

        # 3. verified-by — resolvable + must be a test-case.
        for ref in _as_list(fm.get("verified-by")):
            if ref not in id_index:
                findings.append(Finding(
                    rel, "dangling-ref",
                    f"verified-by id '{ref}' does not resolve to any instance"))
                continue
            for ref_type, _ in id_index[ref]:
                if ref_type != "test-case":
                    findings.append(Finding(
                        rel, "bad-ref-type",
                        f"verified-by '{ref}' is a '{ref_type}', not a "
                        f"test-case"))

        # 2. relative .md links resolve.
        for link in relative_md_links(path):
            if not (path.parent / link).resolve().is_file():
                findings.append(Finding(
                    rel, "broken-link",
                    f"relative link '{link}' points to a missing file"))

    if coverage:
        # The coverage helper consumes already-relativised paths in Finding.file,
        # so pass it (rel, fm) pairs instead of (Path, fm).
        rel_instances = []
        for path, fm in instances:
            rel = str(path.relative_to(docs_dir.parent)) \
                if docs_dir.parent in path.parents else str(path)
            rel_instances.append((rel, fm))
        findings.extend(coverage_findings(rel_instances, id_index, model))

    # Development Case: validate the project's process: section (T-076). Absent
    # file / section is a no-op; a malformed section is a hard failure.
    findings.extend(validate_process_config(docs_dir / "project-config.yaml"))

    findings.sort(key=lambda f: (f.file, f.code, f.message))
    return findings, len(instances)


def is_hard(finding) -> bool:
    """A finding fails the run iff it is NOT an advisory coverage gap."""
    if finding.code != "coverage-gap":
        return True
    # Tagged severity is the first bracketed token of the message.
    return not finding.message.startswith("[advisory]")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--docs", help="docs/ directory to check "
                        "(default: ./docs)")
    parser.add_argument("--schema", help="override docs-meta.schema.json path")
    parser.add_argument("--model", help="override trace-model.json path")
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON instead of text")
    parser.add_argument("--coverage", action="store_true",
                        help="also evaluate required-coverage rules from "
                             "trace-model.json (T-037). Required-severity "
                             "gaps fail the run; advisory gaps are reported "
                             "but do not fail.")
    parser.add_argument("--show-archetype-defaults", action="store_true",
                        help="print the Development Case archetype defaults "
                             "(quick/mvp/product) and what applies when "
                             "docs/project-config.yaml's process: block is "
                             "absent, then exit — no docs/ tree is loaded "
                             "or validated (T-115)")
    args = parser.parse_args(argv)

    if args.show_archetype_defaults:
        print(json.dumps({
            "default_when_absent": (
                "No archetype tailoring applies — every phase runs the "
                "framework's built-in generic ceremony. This is distinct "
                "from the per-task ceremony track (quick/standard/full, see "
                "docs-eng-process/tracks.md), which always applies "
                "regardless of this setting."
            ),
            "archetypes": PROCESS_ARCHETYPE_DEFAULTS,
        }, indent=2, sort_keys=True))
        return EXIT_OK

    docs_dir = Path(args.docs) if args.docs else Path("docs")
    schema_path = Path(args.schema) if args.schema else SCHEMA_PATH
    model_path = Path(args.model) if args.model else TRACE_MODEL_PATH

    try:
        schema = load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot load schema {schema_path}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    try:
        model = load_json(model_path)
    except (OSError, json.JSONDecodeError):
        model = {}  # degrade: schema + existence still run, no type-direction

    findings, count = check(docs_dir, schema, model, coverage=args.coverage)
    hard = [f for f in findings if is_hard(f)]

    if args.json:
        print(json.dumps({
            "ok": not hard,
            "instances": count,
            "findings": [f.as_dict() for f in findings],
        }, indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"{f.file}: [{f.code}] {f.message}")
        if hard:
            extra = f" ({len(findings) - len(hard)} advisory)" \
                if len(findings) > len(hard) else ""
            print(f"\ncheck-docs: {len(hard)} failure(s){extra} across "
                  f"{count} instance(s)")
        elif findings:
            print(f"\ncheck-docs: OK — {count} instance(s), "
                  f"{len(findings)} advisory finding(s)")
        else:
            print(f"check-docs: OK — {count} instance(s), no failures")

    return EXIT_FAIL if hard else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

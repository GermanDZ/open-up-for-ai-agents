"""stamping.py — engine-owned typed-frontmatter ceremony (T-104).

A direct authoring sub-run (``execution: direct``, T-101) produces a document
**body only** — the model is told not to read or write frontmatter, rubrics,
trace models, or schemas. This module is the engine side of that contract: after
the sub-run succeeds, the engine stamps the typed instance frontmatter
(``type``, next-free ``id``, ``title``, ``status: draft``) deterministically,
and ``check-docs`` (already in the cycle's gates) remains the validator — the
gate is the critic, not a model self-critique loop.

The frontmatter contract lives in ``docs-eng-process/doc-frontmatter.md`` /
``scripts/docs-meta.schema.json``; the emitted block uses exactly the flat
``key: value`` dialect the shared ``claims.parse_frontmatter`` reader accepts.
Id allocation mirrors ``openup-claims.py``'s repo-scan discipline: an id seen
anywhere under ``docs/`` is taken (frontmatter or prose reference), so a stamped
id never collides with one already woven into the trace web.

Self-contained + stdlib-only: no imports from ``cycle`` or the CLI scripts, so
this module is unit-testable directly and ships standalone via
``process-manifest.txt``.
"""

import re
from pathlib import Path

# Work-product type -> id prefix. Types are the v1 spine enum
# (docs-meta.schema.json); prefixes follow doc-frontmatter.md's examples
# (VIS-001, REQ-014, TC-031) extended to the rest of the spine.
ID_PREFIXES = {
    "vision": "VIS",
    "requirement": "REQ",
    "work-item": "WI",
    "iteration-plan": "ITP",
    "use-case": "UC",
    "test-case": "TC",
    "decision": "DEC",
}

ID_PAD = 3  # VIS-001, VIS-002, …

# Which typed artifact an execution:direct procedure produces, and where.
# INTERIM table — T-106's task-library defs carry `artifact` + `output_path`
# as data; retire this there. docs/roadmap.md is deliberately absent: it is a
# plain derived view, never a typed instance.
PROCEDURE_ARTIFACTS = {
    "openup-create-vision": ("vision", "docs/vision.md"),
}

_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def split_frontmatter(text):
    """Split ``text`` into (frontmatter-inner-lines-or-None, body).

    Recognizes exactly the ``---`` fence pair the shared parser does; a file
    with no leading fence returns ``(None, text)`` unchanged.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[1:i]), "".join(lines[i + 1:])
    return None, text  # unterminated fence — treat as body, don't eat it


def used_seqs(root, prefix):
    """Every ``<prefix>-NNN`` sequence number already used under docs/.

    Full-text union over ``docs/**/*.md`` — an id referenced anywhere (an
    instance's own ``id``, a ``traces-from`` entry, prose) is taken. Mirrors
    ``openup-claims.py used_seqs_in_repo``'s scan-broadly discipline.
    """
    pat = re.compile(r"\b%s-(\d+)\b" % re.escape(prefix))
    seqs = set()
    docs = Path(root) / "docs"
    if not docs.is_dir():
        return seqs
    for path in docs.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in pat.finditer(text):
            seqs.add(int(m.group(1)))
    return seqs


def next_free_id(root, type_):
    """The next unused id for ``type_`` (e.g. ``VIS-002``). Raises on a
    non-spine type — the caller named an artifact the contract doesn't know."""
    prefix = ID_PREFIXES.get(type_)
    if not prefix:
        raise ValueError("unknown work-product type %r (spine: %s)"
                         % (type_, ", ".join(sorted(ID_PREFIXES))))
    seqs = used_seqs(root, prefix)
    n = max(seqs) + 1 if seqs else 1
    return "%s-%0*d" % (prefix, ID_PAD, n)


def _existing_id(fm_inner, prefix):
    """A valid ``<prefix>-NNN`` id already carried by the file's own
    frontmatter, or None. A re-stamped artifact keeps its identity — other
    instances may reference the id in their trace fields."""
    if not fm_inner:
        return None
    pat = re.compile(r"%s-\d+$" % re.escape(prefix))
    for line in fm_inner.splitlines():
        key, _, rest = line.partition(":")
        if key.strip() == "id":
            rest = rest.split("#", 1)[0].strip()
            if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in "\"'":
                rest = rest[1:-1]
            if pat.fullmatch(rest):
                return rest
    return None


def _title_from(body, fm_inner, fallback):
    """Title precedence: first ATX heading in the body, then a ``title:`` the
    model wrote in its own (replaced) frontmatter, then the fallback."""
    m = _HEADING_RE.search(body)
    if m:
        return m.group(1).strip()
    if fm_inner:
        for line in fm_inner.splitlines():
            key, _, rest = line.partition(":")
            if key.strip() == "title":
                rest = rest.strip()
                if "#" in rest:
                    rest = rest.split("#", 1)[0].strip()
                if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in "\"'":
                    rest = rest[1:-1]
                if rest:
                    return rest
    return fallback


def render_frontmatter(type_, id_, title):
    """The stamped block — flat scalars only; title always quoted (the shared
    parser strips quotes, and quoting makes '#'/':' in titles safe)."""
    return ('---\ntype: %s\nid: %s\ntitle: "%s"\nstatus: draft\n---\n'
            % (type_, id_, title.replace('"', "'")))


def stamp_file(root, path, type_, title=None):
    """Stamp (or normalize) the typed instance frontmatter on ``path``.

    Any frontmatter block the model wrote is **replaced** — the ceremony
    belongs to the engine; the body is preserved byte-for-byte. Returns the
    stamped fields ``{type, id, title, status, path}``.
    """
    if type_ not in ID_PREFIXES:
        raise ValueError("unknown work-product type %r (spine: %s)"
                         % (type_, ", ".join(sorted(ID_PREFIXES))))
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fm_inner, body = split_frontmatter(text)
    id_ = (_existing_id(fm_inner, ID_PREFIXES[type_])
           or next_free_id(root, type_))
    final_title = title or _title_from(body, fm_inner,
                                       path.stem.replace("-", " ").strip())
    path.write_text(render_frontmatter(type_, id_, final_title)
                    + body.lstrip("\n"), encoding="utf-8")
    return {"type": type_, "id": id_, "title": final_title,
            "status": "draft", "path": str(path)}

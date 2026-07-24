"""Runtime tier -> model resolution for the reference driver (T-072).

The neutral procedure pack (docs-eng-process/procedures/openup-*.md) declares only
a tier NAME per procedure (`tier:`). No concrete model string lives in the pack.
`docs-eng-process/tier-map.yaml` maps tier name -> model per target; the reference
driver reads the **driver** column, whose values are ${ENV:-default} placeholders
resolved at runtime against the environment (owner decision 6 — tiers matched by
runtime name).

Stdlib-only. The tier-map / frontmatter parsers mirror scripts/render-claude-adapter.py
(same simple two-level YAML subset) so all consumers read the map identically.
"""

import os
import re
from pathlib import Path

TIER_MAP_REL = ("docs-eng-process", "tier-map.yaml")
PROCEDURES_REL = ("docs-eng-process", "procedures")

_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class TierError(Exception):
    """Raised on an unknown tier or a malformed procedure — never silently defaulted."""


def load_tier_map(path):
    """Parse the simple two-level tier-map.yaml with the standard library only.

    Returns {target: {tier: raw_value}}; comments and blanks ignored; quotes
    stripped. Same shape as scripts/render-claude-adapter.py::load_tier_map.
    """
    result = {}
    current = None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line[0].isspace():
            key = line.rstrip(":").strip()
            current = {}
            result[key] = current
        else:
            if current is None:
                continue
            k, _, v = line.strip().partition(":")
            current[k.strip()] = v.strip().strip('"').strip("'")
    return result


def read_procedure_tier(text):
    """Return the `tier:` value from a procedure's frontmatter, or raise TierError."""
    if not text.startswith("---"):
        raise TierError("procedure has no frontmatter block (leading ---)")
    lines = text.splitlines()
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        raise TierError("procedure frontmatter is not closed")
    for line in lines[1:close]:
        m = re.match(r"^tier\s*:\s*(\S+)\s*$", line)
        if m:
            return m.group(1)
    raise TierError("procedure has no `tier:` field")


def expand_placeholder(value, env=None):
    """Expand ${VAR} / ${VAR:-default} against env (defaults to os.environ).

    Matches shell `:-` semantics: an unset OR empty variable falls back to the
    default. A plain string with no placeholder is returned unchanged.
    """
    env = os.environ if env is None else env

    def repl(m):
        var, default = m.group(1), m.group(2)
        got = env.get(var)
        if got:
            return got
        return default if default is not None else ""

    return _PLACEHOLDER.sub(repl, value)


def procedure_path(root, procedure):
    """Resolve a --procedure argument (`next` or `openup-next`) to its pack file."""
    name = procedure
    if name.startswith("openup-"):
        name = name[len("openup-"):]
    return Path(root, *PROCEDURES_REL, "openup-%s.md" % name)


def resolve_tier_model(root, tier, target="driver", env=None):
    """Resolve a bare tier NAME via the tier-map `target` column (T-089).

    The procedure-independent half of `resolve_model` — used by the cycle
    engine, whose step-scoped sub-runs carry a tier directly instead of a
    procedure file. Raises TierError on an unknown tier/column (no silent
    default).
    """
    tier_map = load_tier_map(Path(root, *TIER_MAP_REL))
    column = tier_map.get(target)
    if column is None:
        raise TierError("tier-map has no '%s' column" % target)
    if tier not in column:
        raise TierError(
            "unknown tier '%s' — not in tier-map '%s' column (no silent default)"
            % (tier, target)
        )
    return expand_placeholder(column[tier], env=env)


def resolve_model(root, procedure, target="driver", env=None):
    """Resolve the model for `procedure` via the tier-map `target` column.

    Raises TierError if the procedure file is missing, has no `tier:`, or the
    tier name is absent from the target column (no silent default).
    """
    proc_path = procedure_path(root, procedure)
    if not proc_path.exists():
        raise TierError("procedure file not found: %s" % proc_path)
    tier = read_procedure_tier(proc_path.read_text(encoding="utf-8"))
    return resolve_tier_model(root, tier, target=target, env=env)

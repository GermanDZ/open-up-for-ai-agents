"""check-docs.py — SKILL.md frontmatter must parse as YAML.

Claude Code parses skill frontmatter with a real YAML parser and silently drops
every field (name, description, model, arguments) when it fails. The check makes
that a hard finding when PyYAML is available, an advisory skip when it is not,
and runs before the --changed-only short-circuit (whose signature is docs/-only).
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_PATH = _REPO / "scripts" / "check-docs.py"
_spec = importlib.util.spec_from_file_location("check_docs", _PATH)
check_docs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_docs)  # type: ignore[union-attr]

pytest.importorskip("yaml")

GOOD = """---
name: good
description: "Type of project: web, api"
fit:
  great: ["is this real?", '"quoted" moments']
---
# Good
"""

BAD_COLON = """---
name: bad-colon
description: Type of project: web, api
---
"""

BAD_FLOW = """---
name: bad-flow
fit:
  great: [is this problem real?, comparing approaches]
---
"""


def _skill(root: Path, name: str, text: str) -> None:
    (root / name).mkdir(parents=True)
    (root / name / "SKILL.md").write_text(text, encoding="utf-8")


def test_valid_frontmatter_has_no_findings(tmp_path):
    _skill(tmp_path, "good", GOOD)
    assert check_docs.check_skill_frontmatter(tmp_path) == []


def test_invalid_frontmatter_is_hard(tmp_path):
    _skill(tmp_path, "good", GOOD)
    _skill(tmp_path, "bad-colon", BAD_COLON)
    _skill(tmp_path, "bad-flow", BAD_FLOW)
    findings = check_docs.check_skill_frontmatter(tmp_path)
    assert sorted(Path(f.file).parent.name for f in findings) == ["bad-colon", "bad-flow"]
    assert all(f.code == "skill-frontmatter" and check_docs.is_hard(f) for f in findings)


def test_missing_skills_dir_is_skipped(tmp_path):
    assert check_docs.check_skill_frontmatter(tmp_path / "nope") == []


def test_no_yaml_is_single_advisory(tmp_path, monkeypatch):
    _skill(tmp_path, "bad-colon", BAD_COLON)
    monkeypatch.setitem(sys.modules, "yaml", None)  # import yaml -> ImportError
    findings = check_docs.check_skill_frontmatter(tmp_path)
    assert len(findings) == 1
    assert findings[0].message.startswith("[advisory]")
    assert not check_docs.is_hard(findings[0])


def test_main_fails_and_changed_only_does_not_skip(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)  # keep the --changed-only cache in tmp
    docs = tmp_path / "docs"
    docs.mkdir()
    skills = tmp_path / "skills"
    _skill(skills, "good", GOOD)
    base = ["--docs", str(docs), "--skills", str(skills), "--changed-only"]

    assert check_docs.main(base) == check_docs.EXIT_OK  # primes the cache
    _skill(skills, "bad-flow", BAD_FLOW)  # docs/ unchanged -> same signature
    assert check_docs.main(base) == check_docs.EXIT_FAIL
    assert "bad-flow" in capsys.readouterr().out

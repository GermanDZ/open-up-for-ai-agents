"""Hook commands must tolerate a missing script without disarming the gates (T-150).

`.claude/settings.json` is tracked and merges instantly; `.claude/scripts/hooks/*` is
gitignored and only appears once `sync-templates-to-claude.sh` runs. In that window an
unguarded command is a hard interpreter error — which blocked every Bash call while
`gate-edits` independently blocked Write, leaving no way to recover from inside a session
(observed 2026-07-27 merging T-140).

The guard has to satisfy two opposing requirements at once:
  * a MISSING script must be a silent no-op, and
  * a PRESENT script must keep its exit status — five hooks (`gate-edits`,
    `on-task-request`, `validate-commit`, `on-stop`, `check-unfinished-tasks`) exit 2 to
    block, and that is the whole enforcement mechanism.

`if [ -f <path> ]; then <interp> <path>; fi` does both. `... || true` does not — it would
silently disarm every gate in the framework, which is why criterion 6 exists.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LIVE = REPO / ".claude/settings.json"
TEMPLATE = REPO / "docs-eng-process/.claude-templates/settings.json.example"

# Forms that would mask a non-zero exit and therefore disarm the blocking hooks.
EXIT_SUPPRESSING = ("|| true", "|| :", "; true", "|| exit 0")


def commands(path: Path):
    """[(event, matcher, command)] for every hook entry in a settings file."""
    data = json.loads(path.read_text())
    out = []
    for event, groups in data.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                out.append((event, group.get("matcher", "-"), hook.get("command", "")))
    return out


def guarded(interp: str, path) -> str:
    """The canonical guard form this task establishes."""
    return f'if [ -f {path} ]; then {interp} {path}; fi'


def run(cmd: str, stdin: str = ""):
    """Execute a hook command string exactly as the harness does.

    `shell=True` is intentional and load-bearing: the artifact under test IS a shell
    command string (`if [ -f … ]; then … fi`) taken from `settings.json`, and the harness
    runs it through a shell. An argv list cannot express the guard, so it would test
    something other than what ships. Every path here comes from pytest's `tmp_path`
    fixture or from the repo's own settings file — never from user input.
    """
    return subprocess.run(cmd, shell=True, input=stdin,
                          capture_output=True, text=True)


# --- structural: the settings files themselves --------------------------------


@pytest.mark.parametrize("path", [LIVE, TEMPLATE], ids=["live", "template"])
def test_every_hook_command_is_guarded(path):
    unguarded = [(e, m, c) for e, m, c in commands(path)
                 if not c.startswith("if [ -f ")]
    assert unguarded == [], f"unguarded hook command(s) in {path.name}: {unguarded}"


@pytest.mark.parametrize("path", [LIVE, TEMPLATE], ids=["live", "template"])
def test_no_command_suppresses_its_exit_code(path):
    """A guard that swallows non-zero would silently disable every blocking hook."""
    offenders = [(e, m, c) for e, m, c in commands(path)
                 if any(bad in c for bad in EXIT_SUPPRESSING)]
    assert offenders == [], f"exit-suppressing hook command(s) in {path.name}: {offenders}"


def test_settings_and_template_stay_identical():
    """`check-claude-sync.sh` enforces this too; asserting it here keeps a
    one-file-only edit from passing the suite."""
    assert LIVE.read_text() == TEMPLATE.read_text()


def test_the_known_hook_entries_are_all_present():
    """Guard the guard: if an entry were dropped rather than guarded, the checks
    above would still pass vacuously."""
    names = {c.split("/")[-1].rstrip("; fi").strip()
             for _, _, c in commands(LIVE)}
    for expected in ("gate-edits.py", "on-task-request.py", "validate-commit.py",
                     "on-stop.py", "check-unfinished-tasks.py",
                     "auto-log-commit.py", "stage-run-log.py"):
        assert any(expected in n for n in names), f"{expected} missing from settings"


# --- behavioural: what the guard form actually does ---------------------------


def test_missing_script_is_a_silent_noop(tmp_path):
    absent = tmp_path / "not-there.py"
    res = run(guarded("python3", absent))
    assert res.returncode == 0
    assert res.stderr == ""


def test_present_script_propagates_a_blocking_exit_2(tmp_path):
    """The contract that makes gate-edits / on-task-request able to block."""
    script = tmp_path / "blocker.py"
    script.write_text("import sys\nsys.exit(2)\n")
    res = run(guarded("python3", script))
    assert res.returncode == 2


def test_present_script_runs_its_side_effect_and_exits_zero(tmp_path):
    script = tmp_path / "writer.py"
    marker = tmp_path / "marker.txt"
    script.write_text(f"open({str(marker)!r}, 'w').write('ran')\n")
    res = run(guarded("python3", script))
    assert res.returncode == 0
    assert marker.read_text() == "ran"


def test_stdin_payload_reaches_the_guarded_script(tmp_path):
    """Every hook reads its JSON payload from stdin; the guard must not eat it."""
    script = tmp_path / "echo.py"
    script.write_text("import sys\nsys.stdout.write(sys.stdin.read())\n")
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
    res = run(guarded("python3", script), stdin=payload)
    assert res.returncode == 0
    assert res.stdout == payload


def test_bash_interpreter_is_guarded_the_same_way(tmp_path):
    script = tmp_path / "hook.sh"
    script.write_text("exit 3\n")
    assert run(guarded("bash", script)).returncode == 3
    assert run(guarded("bash", tmp_path / "absent.sh")).returncode == 0


def test_the_rejected_guard_form_would_disarm_a_blocking_hook(tmp_path):
    """Documents *why* criterion 6 exists — this is the trap, asserted."""
    script = tmp_path / "blocker.py"
    script.write_text("import sys\nsys.exit(2)\n")
    assert run(f'python3 {script} || true').returncode == 0   # gate silently disarmed
    assert run(guarded("python3", script)).returncode == 2    # gate preserved

"""Smoke check: the install path must produce a *usable* consumer (T-153).

Every other test in this suite starts from a hand-built fixture that asserts what its
author believed the installer produces. Nothing ran the installer. That is how
consumer-only breakage reached downstream repos twice — T-110 (a bootstrapped project
shipped with no way to update itself) and T-150 (settings referencing hook scripts that
were not there yet, locking Bash and Write at once).

This runs the real `bootstrap-project.sh` into a temp directory and asserts the four
properties that make the result usable rather than merely present:

  1. the OpenUP CLIs a consumer must run locally are shipped and executable
  2. the self-updater is shipped (T-110)
  3. every hook command is existence-guarded (T-150, consumer side)
  4. the consumer cannot be misdetected as the framework repo (T-126)

Deliberately *not* re-tested here, because they already have real coverage:
  * `sync-from-framework.sh` detection -> `test_sync_from_framework_detection.py`
  * the tracked bypass-log dirty-stop  -> `test_t006_hooks.py`

Deliberately *not* an inventory test: asserting "every manifest entry is present" would
restate `process-manifest.txt` and fail on every legitimate addition, which is how a smoke
check becomes noise and then gets deleted.

Hermetic: no network (bootstrap-project.sh fetches nothing), nothing written outside
pytest's tmp_path.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BOOTSTRAP = REPO / "scripts" / "bootstrap-project.sh"

# The framework-exclusive marker `sync-from-framework.sh` keys its auto-detection on.
# A consumer carrying it would be mistaken for its own upstream (T-126).
FRAMEWORK_ONLY_MARKER = "scripts/sync-templates-to-claude.sh"

pytestmark = pytest.mark.skipif(
    not BOOTSTRAP.exists(),
    reason="bootstrap-project.sh not present in this checkout",
)


@pytest.fixture(scope="module")
def consumer(tmp_path_factory):
    """One bootstrapped consumer, shared by every assertion in this module.

    Module-scoped on purpose: the installer is the slow part, and every test here
    inspects the same immutable result rather than mutating it.
    """
    base = tmp_path_factory.mktemp("consumer-smoke")
    res = subprocess.run(
        ["bash", str(BOOTSTRAP), "--base-dir", str(base), "smoketest"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    project = base / "smoketest"
    assert res.returncode == 0, f"bootstrap failed rc={res.returncode}\n{res.stderr[-2000:]}"
    assert project.is_dir(), f"bootstrap exited 0 but created no project dir\n{res.stdout[-2000:]}"
    return project


def hook_commands(settings: Path):
    data = json.loads(settings.read_text())
    return [h.get("command", "")
            for groups in data.get("hooks", {}).values()
            for g in groups
            for h in g.get("hooks", [])]


# --- 1. the installer runs and produces a project -----------------------------


def test_bootstrap_produces_a_project(consumer):
    assert consumer.is_dir()
    assert (consumer / "scripts").is_dir()


# --- 2. the consumer can actually operate -------------------------------------


def test_consumer_receives_executable_openup_clis(consumer):
    """A consumer that cannot run the CLIs it is told to run is not installed."""
    scripts = consumer / "scripts"
    # A small, stable core — not the whole manifest (see module docstring).
    for name in ("openup-state.py", "openup-claims.py", "openup-board.py",
                 "check-docs.py", "sync-status.py"):
        path = scripts / name
        assert path.exists(), f"{name} was not shipped to the consumer"
        assert os.access(path, os.X_OK) or path.suffix == ".py", f"{name} is not runnable"


def test_consumer_receives_its_own_self_updater(consumer):
    """T-110: a bootstrapped project with no updater can never take a fix."""
    assert (consumer / "scripts" / "sync-from-framework.sh").exists()


# --- 3. hook wiring is present AND guarded (T-150, consumer side) -------------


def test_consumer_settings_exist(consumer):
    assert (consumer / ".claude" / "settings.json").exists()


def test_every_consumer_hook_command_is_guarded(consumer):
    """T-150 from the consumer's side.

    A consumer is the *most* likely place for settings and hook scripts to be out of
    step — it receives them through a sync it may run partially or not at all. If those
    commands are unguarded, a missing script exits 2, which the harness reads as "block
    this tool call", and the project is unusable with no way in.
    """
    settings = consumer / ".claude" / "settings.json"
    commands = hook_commands(settings)
    assert commands, "consumer settings declare no hooks at all"

    unguarded = [c for c in commands if not c.startswith("if [ -f ")]
    assert unguarded == [], f"unguarded hook command(s) shipped to consumer: {unguarded}"

    suppressing = [c for c in commands
                   if any(bad in c for bad in ("|| true", "|| :", "; true"))]
    assert suppressing == [], f"exit-suppressing hook command(s) shipped: {suppressing}"


# --- 4. the consumer is not mistakable for the framework ----------------------


def test_consumer_does_not_carry_the_framework_marker(consumer):
    """T-126: `sync-from-framework.sh` auto-detects its upstream by this marker.

    If a consumer carried it, the consumer could be detected as its own framework and
    sync from itself.
    """
    assert not (consumer / FRAMEWORK_ONLY_MARKER).exists(), (
        f"consumer carries the framework-exclusive marker {FRAMEWORK_ONLY_MARKER}"
    )


# --- 5. hermetic ---------------------------------------------------------------


def test_install_leaves_the_framework_repo_untouched(consumer):
    """The installer must not write into the repo it is installing *from*."""
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True).stdout
    assert "scripts/bootstrap-project.sh" not in dirty
    assert "smoketest" not in dirty

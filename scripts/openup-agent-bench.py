#!/usr/bin/env python3
"""Reference-driver benchmark harness (T-080).

Runs the T-072 reference driver (`openup-agent.py run --procedure next`) against
an **isolated, freshly-git-init'd fixture** seeded with a deterministic
micro-task, N times, and records per-run **outcome + gate-cleanliness + latency +
iterations + work-delta + token usage** — aggregating to `results.jsonl` and a
human `summary.md`. It is the repeatable form of T-072's AC-program live
acceptance run, and the tool for (a) benchmarking local models and (b)
regression-testing changes to skills / the procedure pack / the driver tools.

Design (mirrors the driver: stdlib-only, no install):
  * **Isolation.** Each run builds a fresh project OUTSIDE the repo under test:
    `git archive HEAD` (or the working tree with --include-working-tree) is
    extracted into a temp dir, the scenario is overlaid, and `git init` makes it
    a brand-new repo. The source repo is only read, never written.
  * **Fair fence base.** After the seed commit, `refs/remotes/origin/main` is
    pointed at it, so the driver's own `openup-fence.py check` (and the harness's
    post-run re-check) judge only the *driver's* work — never the framework
    history. This is why a clean git-init fixture avoids the harness-optional /
    main base artifact that broke earlier informal runs.
  * **Measurement never trusts the model.** Outcome is the driver's typed exit
    code; gate-cleanliness and work-delta are recomputed on the fixture after the
    run; tokens/latency come from the driver's opt-in usage log.

Exit codes: 0 = batch ran (see summary for pass rate); 2 = usage/config error.
"""

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2

# Driver exit code → outcome label (mirrors scripts/openup_agent/loop.py).
OUTCOME_BY_EXIT = {
    0: "pass",
    2: "config-error",
    3: "endpoint-error",
    4: "max-iterations",
    5: "suspended",
}

HERE = Path(__file__).resolve().parent
DEFAULT_SCENARIO_DIR = HERE / "bench-scenarios" / "quick-doc"


def _log(msg):
    sys.stderr.write("[bench] %s\n" % msg)
    sys.stderr.flush()


def _git(args, cwd, check=True, capture=True):
    """Run a git command; return CompletedProcess."""
    return subprocess.run(
        ["git", *args], cwd=str(cwd), text=True,
        capture_output=capture, check=check,
    )


def _now_stamp():
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


# --------------------------------------------------------------------------
# Fixture construction — a fresh git-init project outside the repo under test
# --------------------------------------------------------------------------
def build_fixture(repo: Path, dest: Path, scenario_dir: Path, include_working_tree: bool):
    """Materialize a fresh, seeded, git-init'd OpenUP project at `dest`.

    Returns (seed_sha, scenario) where scenario is the parsed scenario.json.
    The source `repo` is only read (archive + optional stash-create diff).
    """
    dest.mkdir(parents=True, exist_ok=True)

    # 1. Snapshot the repo under test — committed HEAD by default, or the working
    #    tree (staged + unstaged tracked changes) with --include-working-tree —
    #    into the fixture as plain files (no .git, no ignored cruft).
    tree_ish = "HEAD"
    if include_working_tree:
        created = _git(["stash", "create"], repo, check=False)
        sha = (created.stdout or "").strip()
        if sha:
            tree_ish = sha  # a commit capturing the current working tree
    tar_path = dest.parent / (dest.name + ".src.tar")
    with open(tar_path, "wb") as fh:
        subprocess.run(["git", "archive", "--format=tar", tree_ish],
                       cwd=str(repo), check=True, stdout=fh)
    subprocess.run(["tar", "-xf", str(tar_path), "-C", str(dest)], check=True)
    tar_path.unlink(missing_ok=True)

    # 2. Overlay the scenario (its overlay/ tree is copied onto the fixture).
    scenario = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    overlay = scenario_dir / "overlay"
    if overlay.is_dir():
        _copy_tree(overlay, dest)

    # 3. Fresh git repo — the whole point: a brand-new project, no source history
    #    or remotes. The seed commit becomes the fence base.
    _git(["init"], dest)
    _git(["config", "user.email", "bench@openup.local"], dest)
    _git(["config", "user.name", "openup-bench"], dest)
    _git(["config", "commit.gpgsign", "false"], dest, check=False)
    _git(["add", "-A"], dest)
    _git(["commit", "--no-verify", "-m",
          "bench-seed: %s scenario" % scenario.get("name", "?")], dest)
    seed_sha = _git(["rev-parse", "HEAD"], dest).stdout.strip()

    # 4. Point the fence's default base (origin/main) at the seed commit, so the
    #    driver's own gate — and our post-run re-check — judge only its own diff.
    _git(["update-ref", "refs/remotes/origin/main", seed_sha], dest)
    return seed_sha, scenario


def _copy_tree(src: Path, dst: Path):
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# --------------------------------------------------------------------------
# Pre-run sanity — does the board resolve to the seeded lane?
# --------------------------------------------------------------------------
def resolves_to(fixture: Path, expect_pick: str):
    """Return (ok, decision_dict_or_error). Read-only board resolve on the fixture."""
    proc = subprocess.run(
        ["python3", "scripts/openup-board.py", "resolve"],
        cwd=str(fixture), text=True, capture_output=True,
    )
    if proc.returncode != 0:
        return False, {"error": (proc.stderr or proc.stdout).strip()[:300]}
    try:
        decision = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return False, {"error": "resolve returned non-JSON: %s" % e}
    picked = (decision.get("lane") or {}).get("task")
    return (decision.get("path") == "pick" and picked == expect_pick), decision


# --------------------------------------------------------------------------
# Run the driver as a subprocess (exactly what a user runs)
# --------------------------------------------------------------------------
def run_driver(repo: Path, fixture: Path, procedure: str, max_iterations: int,
               timeout: int, usage_log: Path, env: dict, instruction=None):
    """Invoke `openup-agent.py run --dir <fixture>`; return a dict of raw results."""
    run_env = dict(env)
    run_env["OPENUP_AGENT_USAGE_LOG"] = str(usage_log)
    argv = [
        sys.executable, str(repo / "scripts" / "openup-agent.py"),
        "run", "--dir", str(fixture), "--procedure", procedure,
        "--max-iterations", str(max_iterations),
    ]
    if instruction:
        argv += ["--instruction", instruction]
    t0 = _dt.datetime.now()
    timed_out = False
    try:
        proc = subprocess.run(argv, text=True, capture_output=True,
                              env=run_env, timeout=timeout)
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = None
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
    wall_ms = int((_dt.datetime.now() - t0).total_seconds() * 1000)
    return {
        "exit_code": exit_code,
        "timed_out": timed_out,
        "wall_ms": wall_ms,
        "stdout": stdout,
        "stderr": stderr,
    }


# --------------------------------------------------------------------------
# Post-run measurement — recomputed deterministically on the fixture
# --------------------------------------------------------------------------
def read_usage(usage_log: Path):
    """Sum the driver's per-call usage log → (iterations, tokens, latencies)."""
    prompt = completion = total = 0
    latencies, iters = [], 0
    if usage_log.exists():
        for line in usage_log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            iters += 1
            u = rec.get("usage") or {}
            prompt += int(u.get("prompt_tokens") or 0)
            completion += int(u.get("completion_tokens") or 0)
            total += int(u.get("total_tokens") or 0)
            if rec.get("latency_ms") is not None:
                latencies.append(rec["latency_ms"])
    if total == 0:
        total = prompt + completion
    return iters, {"prompt": prompt, "completion": completion, "total": total}, latencies


def check_gates(fixture: Path, seed_sha: str):
    """Re-run the deterministic gates on the fixture; return {fence, check_docs}."""
    fence = subprocess.run(
        ["python3", "scripts/openup-fence.py", "check", "--base", seed_sha],
        cwd=str(fixture), text=True, capture_output=True,
    )
    docs = subprocess.run(
        ["python3", "scripts/check-docs.py"],
        cwd=str(fixture), text=True, capture_output=True,
    )
    return {
        # exit 3 = "no lane to fence" (a non-lane procedure run like create-vision)
        # — inapplicable, not a violation; treated as clean, mirroring the driver's
        # run_gates (T-083).
        "fence": fence.returncode in (0, 3),
        "fence_detail": (fence.stdout + fence.stderr).strip()[-400:],
        "check_docs": docs.returncode == 0,
        "check_docs_detail": (docs.stdout + docs.stderr).strip()[-400:],
    }


def work_delta(fixture: Path, seed_sha: str, scenario: dict):
    """What the driver actually did: commits over the seed, files changed, and
    whether the scenario's deliverable was produced."""
    commits = _git(["rev-list", "--count", "%s..HEAD" % seed_sha], fixture,
                   check=False).stdout.strip()
    changed = _git(["diff", "--name-only", "%s..HEAD" % seed_sha], fixture,
                   check=False).stdout.strip()
    files_changed = [f for f in changed.splitlines() if f]
    # The scenario's deliverable is the ground-truth "did the work happen" signal —
    # checked against the fixture's tree, not the model's word. Success is the
    # deliverable file existing AND containing every required marker (a list —
    # e.g. the vision's required sections); `deliverable_marker` (single string) is
    # the back-compat form.
    markers = scenario.get("required_markers")
    if markers is None and scenario.get("deliverable_marker") is not None:
        markers = [scenario["deliverable_marker"]]
    df = scenario.get("deliverable_file")
    delivered, missing = False, []
    if df:
        p = fixture / df
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            missing = [m for m in (markers or []) if m not in text]
            delivered = not missing
    task_id = scenario.get("expect_pick")
    archived = task_id and (fixture / "docs" / "changes" / "archive" / task_id).is_dir()
    return {
        "commits": int(commits or 0),
        "files_changed": len(files_changed),
        "files": files_changed[:40],
        "deliverable_produced": delivered,
        "missing_markers": missing,
        "task_archived": bool(archived),
    }


def sentinel_of(stdout: str):
    for line in stdout.splitlines():
        s = line.strip()
        if s.startswith("OPENUP-") and ":" in s:
            return s
    return None


def _fatal_line(stderr: str):
    """The driver's FATAL line, if any — the one-line reason a run failed
    (endpoint error, config/tier error). Surfaced so a non-pass run explains
    itself without a side-run."""
    for line in reversed(stderr.splitlines()):
        if "FATAL:" in line:
            return line.strip()
    return None


def measure_run(fixture: Path, seed_sha: str, scenario: dict, raw: dict, usage_log: Path):
    """Fold a driver invocation into one run record."""
    if raw["timed_out"]:
        outcome = "timeout"
    else:
        outcome = OUTCOME_BY_EXIT.get(raw["exit_code"], "error")
    iters, tokens, latencies = read_usage(usage_log)
    return {
        "outcome": outcome,
        "exit_code": raw["exit_code"],
        "sentinel": sentinel_of(raw["stdout"]),
        "iterations": iters,
        "wall_ms": raw["wall_ms"],
        "latency_ms": {
            "calls": len(latencies),
            "total": sum(latencies),
            "mean": (sum(latencies) // len(latencies)) if latencies else 0,
        },
        "tokens": tokens,
        "gates": check_gates(fixture, seed_sha),
        "work": work_delta(fixture, seed_sha, scenario),
        "fatal": _fatal_line(raw.get("stderr", "")),
        "stderr_tail": (raw.get("stderr", "") or "").strip()[-1200:],
        "stdout_tail": (raw.get("stdout", "") or "").strip()[-600:],
    }


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------
def _median(xs):
    if not xs:
        return 0
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) // 2


def aggregate(records, meta):
    n = len(records)
    passes = [r for r in records if r["outcome"] == "pass" and r["gates"]["fence"]
              and r["gates"]["check_docs"] and r["work"]["deliverable_produced"]]
    hist = {}
    for r in records:
        hist[r["outcome"]] = hist.get(r["outcome"], 0) + 1
    iters = [r["iterations"] for r in records]
    walls = [r["wall_ms"] for r in records]
    toks = [r["tokens"]["total"] for r in records]
    return {
        "runs": n,
        "clean_passes": len(passes),
        "pass_rate": round(len(passes) / n, 3) if n else 0.0,
        "outcome_histogram": hist,
        "iterations": {"mean": (sum(iters) // n) if n else 0, "median": _median(iters)},
        "wall_ms": {"mean": (sum(walls) // n) if n else 0, "median": _median(walls)},
        "tokens_total": {"mean": (sum(toks) // n) if n else 0, "median": _median(toks),
                         "sum": sum(toks)},
        "meta": meta,
    }


def write_summary(out_dir: Path, agg, records):
    lines = []
    m = agg["meta"]
    lines.append("# Reference-driver benchmark — %s\n" % m.get("stamp", ""))
    lines.append("- **Repo under test:** `%s`" % m.get("repo"))
    lines.append("- **Scenario:** `%s`  ·  **Procedure:** `%s`  ·  **Model:** `%s`"
                 % (m.get("scenario"), m.get("procedure"), m.get("model")))
    lines.append("- **Endpoint:** `%s`" % m.get("endpoint"))
    lines.append("")
    lines.append("## Aggregate over %d run(s)\n" % agg["runs"])
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append("| Clean passes | %d / %d |" % (agg["clean_passes"], agg["runs"]))
    lines.append("| Pass rate | %.1f%% |" % (agg["pass_rate"] * 100))
    lines.append("| Iterations (mean / median) | %d / %d |"
                 % (agg["iterations"]["mean"], agg["iterations"]["median"]))
    lines.append("| Wall ms (mean / median) | %d / %d |"
                 % (agg["wall_ms"]["mean"], agg["wall_ms"]["median"]))
    lines.append("| Total tokens (mean / median / sum) | %d / %d / %d |"
                 % (agg["tokens_total"]["mean"], agg["tokens_total"]["median"],
                    agg["tokens_total"]["sum"]))
    lines.append("")
    lines.append("**Outcome histogram:** %s\n"
                 % ", ".join("%s×%d" % (k, v) for k, v in sorted(agg["outcome_histogram"].items())))
    lines.append("## Per-run\n")
    lines.append("| # | Outcome | Sentinel | Iters | Wall ms | Tokens | Fence | Docs | Delivered |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(records, 1):
        lines.append("| %d | %s | %s | %d | %d | %d | %s | %s | %s |" % (
            i, r["outcome"], (r["sentinel"] or "—")[:32], r["iterations"], r["wall_ms"],
            r["tokens"]["total"], "✓" if r["gates"]["fence"] else "✗",
            "✓" if r["gates"]["check_docs"] else "✗",
            "✓" if r["work"]["deliverable_produced"] else "✗"))
    failed = [(i, r) for i, r in enumerate(records, 1) if r["outcome"] != "pass"]
    if failed:
        lines.append("\n## Failures — why each non-pass run failed\n")
        for i, r in failed:
            reason = r.get("fatal") or ((r.get("stderr_tail") or "").splitlines()[-1:]
                                        or ["(no stderr)"])[0]
            lines.append("- **run %d (%s):** %s  — full log: `run-%02d.driver.log`"
                         % (i, r["outcome"], reason, i))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Batch driver
# --------------------------------------------------------------------------
def run_batch(args, env):
    repo = Path(args.repo).resolve()
    if not (repo / "scripts" / "openup-agent.py").exists():
        _log("FATAL: --repo %s has no scripts/openup-agent.py" % repo)
        return EXIT_USAGE
    scenario_dir = Path(args.scenario).resolve() if args.scenario else DEFAULT_SCENARIO_DIR
    if not (scenario_dir / "scenario.json").exists():
        _log("FATAL: scenario %s has no scenario.json" % scenario_dir)
        return EXIT_USAGE

    stamp = _now_stamp()
    out_dir = Path(args.out).resolve() if args.out else repo / ".openup" / "bench" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    workroot = Path(args.workdir).resolve() if args.workdir else Path(
        tempfile.mkdtemp(prefix="openup-bench-"))
    workroot.mkdir(parents=True, exist_ok=True)

    # A scenario declares its own default procedure + instruction; an explicit
    # --procedure on the CLI overrides. Read them once from scenario.json.
    scenario_meta = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    procedure = args.procedure or scenario_meta.get("procedure") or "next"
    instruction = scenario_meta.get("instruction")

    model = env.get("OPENUP_MODEL_MAIN", "(tier-map default)")
    endpoint = env.get("LLM_API_URL", "(unset — driver will fail fast)")
    _log("batch: %d run(s), scenario=%s, procedure=%s, out=%s"
         % (args.runs, scenario_dir.name, procedure, out_dir))

    records = []
    results_path = out_dir / "results.jsonl"
    with open(results_path, "w", encoding="utf-8") as rf:
        for n in range(1, args.runs + 1):
            fixture = workroot / ("run-%02d" % n)
            if fixture.exists():
                shutil.rmtree(fixture)
            _log("run %d/%d — building fixture at %s" % (n, args.runs, fixture))
            seed_sha, scenario = build_fixture(
                repo, fixture, scenario_dir, args.include_working_tree)

            # The resolve==pick sanity check only applies to change-folder-lane
            # scenarios (those declaring expect_pick). Vision-style scenarios drive
            # a procedure directly and seed no lane, so skip it.
            ok = True
            if scenario.get("expect_pick"):
                ok, decision = resolves_to(fixture, scenario.get("expect_pick"))
                if not ok:
                    _log("run %d: WARNING board did not resolve to %s (got %s)"
                         % (n, scenario.get("expect_pick"), json.dumps(decision)[:160]))

            usage_log = fixture / ".openup-usage.jsonl"
            raw = run_driver(repo, fixture, procedure, args.max_iterations,
                             args.timeout, usage_log, env, instruction=instruction)
            record = measure_run(fixture, seed_sha, scenario, raw, usage_log)
            record["run"] = n
            record["seed_resolves_pick"] = ok
            if args.keep:
                record["fixture"] = str(fixture)
            # Archive the run's deliverable into the results dir so the artifact a
            # batch scored survives fixture teardown (read/compare visions without
            # --keep). Named run-NN.<basename> (e.g. run-01.vision.md).
            record["deliverable_archived"] = None
            df = scenario.get("deliverable_file")
            if df and (fixture / df).exists():
                dest = out_dir / ("run-%02d.%s" % (n, Path(df).name))
                shutil.copy2(fixture / df, dest)
                record["deliverable_archived"] = dest.name
            # Always persist the full driver stdout/stderr — the definitive
            # per-run debug log — so a failure never needs a manual side-run.
            (out_dir / ("run-%02d.driver.log" % n)).write_text(
                "$ openup-agent.py run --dir %s --procedure %s\n\n=== STDOUT ===\n%s\n"
                "=== STDERR ===\n%s\n" % (fixture, procedure,
                raw.get("stdout", ""), raw.get("stderr", "")), encoding="utf-8")
            records.append(record)
            rf.write(json.dumps(record, ensure_ascii=False) + "\n")
            rf.flush()
            _log("run %d: outcome=%s iters=%d tokens=%d fence=%s delivered=%s"
                 % (n, record["outcome"], record["iterations"],
                    record["tokens"]["total"], record["gates"]["fence"],
                    record["work"]["deliverable_produced"]))
            # On any non-clean outcome, surface WHY inline (the reason was hidden
            # in the first live batch) — the FATAL line, else the last stderr line.
            if record["outcome"] != "pass":
                tail_lines = (record.get("stderr_tail") or "").splitlines()
                reason = record.get("fatal") or (tail_lines[-1] if tail_lines else "(no stderr)")
                _log("run %d: reason → %s  (full log: %s)"
                     % (n, reason, out_dir / ("run-%02d.driver.log" % n)))
            if not args.keep:
                shutil.rmtree(fixture, ignore_errors=True)

    meta = {
        "stamp": stamp, "repo": str(repo), "scenario": scenario_dir.name,
        "procedure": procedure, "model": model, "endpoint": endpoint,
        "runs": args.runs, "max_iterations": args.max_iterations,
        "include_working_tree": args.include_working_tree,
    }
    agg = aggregate(records, meta)
    (out_dir / "summary.json").write_text(
        json.dumps(agg, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary(out_dir, agg, records)
    if not args.keep and not args.workdir:
        shutil.rmtree(workroot, ignore_errors=True)

    print(json.dumps({"out": str(out_dir), "pass_rate": agg["pass_rate"],
                      "clean_passes": agg["clean_passes"], "runs": agg["runs"]},
                     ensure_ascii=False))
    _log("batch done — %d/%d clean passes (%.0f%%); summary: %s/summary.md"
         % (agg["clean_passes"], agg["runs"], agg["pass_rate"] * 100, out_dir))
    return EXIT_OK


def build_parser():
    p = argparse.ArgumentParser(
        prog="openup-agent-bench.py",
        description="Isolated, instrumented benchmark harness for the reference driver (T-080).")
    p.add_argument("--repo", default=".", help="Repo under test (default: cwd).")
    p.add_argument("--runs", type=int, default=1, help="Number of benchmark runs (default 1).")
    p.add_argument("--procedure", default=None,
                   help="Procedure to drive. Overrides the scenario's `procedure`; "
                        "falls back to the scenario's, then `next`.")
    p.add_argument("--scenario", default=None,
                   help="Scenario dir (default: bench-scenarios/quick-doc).")
    p.add_argument("--out", default=None,
                   help="Results dir (default: <repo>/.openup/bench/<stamp>).")
    p.add_argument("--workdir", default=None,
                   help="Where fixtures are built (default: a fresh system temp dir, "
                        "removed after unless --keep).")
    p.add_argument("--max-iterations", type=int, default=50,
                   help="Driver turn cap per run (default 50).")
    p.add_argument("--timeout", type=int, default=1800,
                   help="Wall-clock timeout per run in seconds (default 1800).")
    p.add_argument("--include-working-tree", action="store_true",
                   help="Seed the fixture from the repo's working tree (uncommitted "
                        "tracked changes) instead of committed HEAD — to benchmark "
                        "in-progress skill/procedure/tool edits.")
    p.add_argument("--keep", action="store_true",
                   help="Keep fixtures after the run (for debugging).")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return run_batch(args, dict(os.environ))


if __name__ == "__main__":
    sys.exit(main())

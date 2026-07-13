#!/usr/bin/env python3
"""openup-agent — reference OpenAI-compatible driver for harness-optional OpenUP (T-072).

Drives an OpenUP procedure end-to-end with a plain agentic loop over any
OpenAI-compatible chat-completions endpoint, consuming the T-071 neutral procedure
pack directly — no Claude Code, no harness. Stdlib-only.

Usage:
    export LLM_API_URL=http://localhost:1234/v1     # LM Studio / Ollama / vLLM / OpenAI
    export LLM_API_KEY=sk-...                        # may be empty for local servers
    python3 scripts/openup-agent.py run --dir . --procedure next

Model selection is by tier: the procedure's `tier:` is resolved through the
`driver` column of docs-eng-process/tier-map.yaml, whose ${ENV:-default}
placeholders (OPENUP_MODEL_SMALL / _MID / _MAIN) expand against the environment.

Exit codes:
    0  procedure completed; sentinel printed to stdout
    2  configuration error (env/procedure/tier)
    3  endpoint/transport error
    4  max iterations reached with no clean sentinel
    5  suspended awaiting a human answer (ask_user, non-interactive) — sentinel on stdout
"""

import argparse
import sys
from pathlib import Path

# Make the sibling package importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from openup_agent import loop  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="openup-agent",
        description="Reference OpenAI-compatible driver for harness-optional OpenUP.",
    )
    sub = ap.add_subparsers(dest="command")

    runp = sub.add_parser("run", help="Drive one OpenUP procedure to completion.")
    runp.add_argument("--dir", required=True,
                      help="Path to the OpenUP project (must contain docs-eng-process/procedures/).")
    runp.add_argument("--procedure", required=True,
                      help="Procedure name, e.g. 'next' (resolves openup-next.md).")
    runp.add_argument("--max-iterations", type=int, default=loop.DEFAULT_MAX_ITERATIONS,
                      help="Turn cap before the loop gives up (default %(default)s).")
    runp.add_argument("--interactive", action="store_true",
                      help="Answer the procedure's questions on the TTY; otherwise a "
                           "human question suspends the run into an input-request (exit 5).")
    runp.add_argument("--instruction", default=None,
                      help="Extra task context appended to the driver's initial user "
                           "message (e.g. 'read the stakeholder brief at … and produce "
                           "the vision'). Absent ⇒ unchanged behavior.")

    args = ap.parse_args(argv)
    if args.command != "run":
        ap.print_help(sys.stderr)
        return 2

    root = Path(args.dir).resolve()
    if not root.is_dir():
        sys.stderr.write("error: --dir %s is not a directory\n" % args.dir)
        return 2

    return loop.run(
        dir=str(root),
        procedure=args.procedure,
        max_iterations=args.max_iterations,
        interactive=args.interactive,
        instruction=args.instruction,
    )


if __name__ == "__main__":
    sys.exit(main())

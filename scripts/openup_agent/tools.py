"""The six-tool surface for the reference driver (T-072).

read_file, write_file, edit_file, glob (list_dir/glob), grep, exec — rooted at a
single working directory. `exec` is narrowed to an allowlist (`git <subcmd>` and
`python3 scripts/<script>.py …`) so a bare model can drive the deterministic
OpenUP scripts without being handed an arbitrary shell (safety invariant, spec
Requirement 3). Stdlib-only.

Each tool returns a plain string (the tool result appended to the LLM message
history). Recoverable problems (missing file, non-unique edit target, refused
command) return a structured error STRING rather than raising, so the model can
read the error and retry — mirroring the harness tool contract.
"""

import re
import shlex
import subprocess
from pathlib import Path

# Commands `exec` will run. Anything else is refused without spawning a process.
_ALLOWED_EXEC = "git <subcmd>  |  python3 scripts/<script>.py [args]"
_MAX_READ_BYTES = 400_000


class ToolError(Exception):
    """Unrecoverable tool misconfiguration (e.g. path escaping the root)."""


def _resolve(root, path):
    """Resolve `path` under `root`, refusing traversal outside the working root."""
    root = Path(root).resolve()
    target = (root / path).resolve()
    if root != target and root not in target.parents:
        raise ToolError("path '%s' escapes the working root" % path)
    return target


class Tools:
    """Bound tool implementations for one run, rooted at `root`."""

    def __init__(self, root):
        self.root = Path(root).resolve()

    # -- file reads -------------------------------------------------------
    def read_file(self, path, offset=None, limit=None):
        try:
            target = _resolve(self.root, path)
        except ToolError as e:
            return "ERROR: %s" % e
        if not target.exists():
            return "ERROR: no such file: %s" % path
        if target.is_dir():
            return "ERROR: %s is a directory (use glob)" % path
        text = target.read_text(encoding="utf-8", errors="replace")
        if offset is None and limit is None:
            return text[:_MAX_READ_BYTES]
        lines = text.splitlines()
        start = int(offset) if offset else 0
        end = start + int(limit) if limit else len(lines)
        return "\n".join(lines[start:end])

    # -- file writes ------------------------------------------------------
    def write_file(self, path, content):
        try:
            target = _resolve(self.root, path)
        except ToolError as e:
            return "ERROR: %s" % e
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return "wrote %d bytes to %s" % (len(content.encode("utf-8")), path)

    def edit_file(self, path, old_str, new_str):
        try:
            target = _resolve(self.root, path)
        except ToolError as e:
            return "ERROR: %s" % e
        if not target.exists():
            return "ERROR: no such file: %s" % path
        text = target.read_text(encoding="utf-8")
        count = text.count(old_str)
        if count == 0:
            return "ERROR: old_str not found in %s — no change made" % path
        if count > 1:
            return (
                "ERROR: old_str is not unique in %s (%d matches) — "
                "add surrounding context and retry" % (path, count)
            )
        target.write_text(text.replace(old_str, new_str, 1), encoding="utf-8")
        return "edited %s (1 replacement)" % path

    # -- discovery --------------------------------------------------------
    def glob(self, pattern):
        """List paths matching a glob pattern (relative to root). Subsumes list_dir.

        A bad model arg must never crash the driver (T-119): an empty pattern makes
        ``pathlib.glob('')`` raise IndexError, and other malformed patterns raise
        ValueError — both are returned to the model as an ``ERROR:`` string so it
        can recover, exactly as ``grep`` handles an invalid regex."""
        if not pattern or not str(pattern).strip():
            return ("ERROR: empty glob pattern; provide one like "
                    "'docs/**/*.md' or 'docs/inputs/*'")
        try:
            matches = sorted(str(p.relative_to(self.root))
                             for p in self.root.glob(pattern))
        except (ValueError, IndexError, OSError) as e:
            return "ERROR: invalid glob pattern %r: %s" % (pattern, e)
        if not matches:
            return "(no matches for %r)" % pattern
        return "\n".join(matches)

    def grep(self, pattern, path="."):
        try:
            base = _resolve(self.root, path)
            rx = re.compile(pattern)
        except ToolError as e:
            return "ERROR: %s" % e
        except re.error as e:
            return "ERROR: invalid regex: %s" % e
        files = [base] if base.is_file() else sorted(base.rglob("*"))
        hits = []
        for f in files:
            if not f.is_file():
                continue
            try:
                for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if rx.search(line):
                        hits.append("%s:%d:%s" % (f.relative_to(self.root), n, line))
                        if len(hits) >= 500:
                            hits.append("... (truncated at 500 matches)")
                            return "\n".join(hits)
            except OSError:
                continue
        return "\n".join(hits) if hits else "(no matches)"

    # -- command execution (allowlisted) ---------------------------------
    def exec(self, command, cwd=None):
        try:
            argv = shlex.split(command)
        except ValueError as e:
            return "ERROR: could not parse command: %s" % e
        if not argv:
            return "ERROR: empty command"
        if not self._allowed(argv):
            return (
                "REFUSED: '%s' is not on the exec allowlist. Allowed: %s"
                % (argv[0], _ALLOWED_EXEC)
            )
        run_cwd = self.root if not cwd else _resolve(self.root, cwd)
        try:
            proc = subprocess.run(
                argv, cwd=str(run_cwd), capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired:
            return "ERROR: command timed out after 300s"
        out = proc.stdout or ""
        err = proc.stderr or ""
        return "exit=%d\n--- stdout ---\n%s\n--- stderr ---\n%s" % (
            proc.returncode, out, err
        )

    @staticmethod
    def _allowed(argv):
        if argv[0] == "git":
            return True
        if argv[0] in ("python3", "python"):
            return len(argv) >= 2 and argv[1].startswith("scripts/") and argv[1].endswith(".py")
        return False

    # -- dispatch ---------------------------------------------------------
    def dispatch(self, name, arguments):
        """Call tool `name` with a dict of arguments; unknown tool -> error string."""
        fn = getattr(self, name, None)
        if fn is None or name not in DISPATCH_TOOL_NAMES:
            return "ERROR: unknown tool '%s'" % name
        try:
            return fn(**arguments)
        except TypeError as e:
            return "ERROR: bad arguments for %s: %s" % (name, e)


# The six dispatchable file/shell tools. `ask_user` is a 7th advertised tool but
# is intercepted by the loop (interactive TTY prompt vs async suspend), not
# dispatched through Tools — see loop._dispatch_tool_calls.
DISPATCH_TOOL_NAMES = ("read_file", "write_file", "edit_file", "glob", "grep", "exec")
TOOL_NAMES = DISPATCH_TOOL_NAMES + ("ask_user",)

# OpenAI-style function/tool definitions advertised to the model.
TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file under the working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {"type": "integer", "description": "0-based start line"},
                    "limit": {"type": "integer", "description": "max lines to return"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a unique old_str with new_str in a file (tick checkboxes, targeted edits).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_str": {"type": "string"},
                    "new_str": {"type": "string"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "List paths matching a glob pattern (e.g. 'docs/changes/*/plan.md'). Also lists a directory via 'dir/*'.",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Regex-search files under a path; returns file:line:match.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "description": "file or dir (default '.')"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exec",
            "description": "Run an allowlisted command: `git <subcmd>` or `python3 scripts/<script>.py …`. Anything else is refused.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "cwd": {"type": "string", "description": "optional subdir of the working root"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": (
                "Ask the human a question that genuinely needs their decision (a blocking "
                "choice the spec/docs don't answer). In interactive mode you get their answer "
                "back and continue; otherwise the run suspends into an OpenUP input-request for "
                "async resolution — do NOT call this for questions you can answer from the repo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "optional multiple-choice options",
                    },
                },
                "required": ["question"],
            },
        },
    },
]

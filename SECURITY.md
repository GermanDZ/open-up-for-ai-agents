# Security Policy

OpenUP is a development-process framework that is **copied into your repository**
and wires **local automation** (Claude Code hooks) that runs on your machine. This
document tells you exactly what runs, how to reduce or disable it, how to pin to an
immutable version, and how to report a vulnerability — so you can adopt OpenUP
deliberately rather than install-and-trust blindly.

## Reporting a Vulnerability

Please report security issues **privately**, not in a public issue:

- Preferred: GitHub **Security Advisories** — open the repository's **Security** tab
  → **Report a vulnerability** (private disclosure to the maintainer).
- If advisories are unavailable to you, open a minimal public issue that says only
  "security report — please open a private channel" (no details) and wait for a
  private follow-up.

Please include the affected version/tag, reproduction steps, and impact. There is no
bug-bounty program; this is a maintainer-effort project.

## Supported Versions & Pinning

Only the **latest tagged release** is supported with fixes. Releases are git tags
(e.g. `v2.0.0`). For a reproducible, reviewable install, **pin to a tag** rather than
tracking `main`:

- **Submodule, pinned to a tag (recommended):**
  ```bash
  git submodule add https://github.com/GermanDZ/open-up-for-ai-agents.git .openup-template
  git -C .openup-template checkout v2.0.0
  ```
- **Clone a specific tag, then run a local script** (never pipe a remote script to a
  shell):
  ```bash
  git clone --depth 1 --branch v2.0.0 \
    https://github.com/GermanDZ/open-up-for-ai-agents.git /tmp/openup
  # review /tmp/openup before running anything, then:
  bash /tmp/openup/scripts/update-from-template.sh --template-dir /tmp/openup
  ```

Set `OPENUP_REF=v2.0.0` to pin the bundled update scripts to an exact tag. See
[`docs-eng-process/updating.md`](docs-eng-process/updating.md) for all update paths.

For a private mirror, fork or mirror the repository internally and pin to a commit
SHA you have reviewed.

## What Runs On Your Machine (Hook Disclosure)

Installing the OpenUP template adds a `.claude/settings.json` that registers
**Claude Code hooks** — small Python scripts under `.claude/scripts/hooks/` that
Claude Code executes **locally** on tool, commit, prompt, plan-exit, and stop events.
This is by design: the hooks are how OpenUP enforces its process (no code without a
plan, no raw commits, clean session exits). They are **not** network services and do
not phone home, but they **do run local code on nearly every agent event**, so you
should review them before enabling.

The set wired by `docs-eng-process/.claude-templates/settings.json.example`:

| Event | Hook script | What it does |
|---|---|---|
| `PreToolUse` · Bash | `check-iteration.py` | Blocks Bash (incl. commits / code runs) when no active OpenUP iteration plan exists. |
| `PreToolUse` · Bash | `validate-commit.py` | Validates the commit and message format; blocks a raw commit that bypasses the workflow. |
| `PreToolUse` · Edit/Write/NotebookEdit | `gate-edits.py` | Blocks editing product/source files with no persisted plan; exempts process-state dirs (`docs/changes/`, `.openup/`, `.claude/memory/`, …). |
| `PostToolUse` · Bash | `on-branch-created.py` | Detects a newly created branch and records lane bookkeeping. |
| `PostToolUse` · Bash | `auto-log-commit.py` | After a commit, appends the run-log shard under `docs/agent-logs/runs/` and flips the log gate. |
| `PostToolUse` · ExitPlanMode | `on-plan-exit.py` | Captures a plan saved via plan mode into `docs/plans/`. |
| `Stop` | `on-stop.py` | Blocks the turn from ending on uncommitted changes or unsatisfied process gates. |
| `UserPromptSubmit` | `on-task-request.py` | Inspects the submitted prompt to suggest a ceremony track / detect task intent. |
| `UserPromptSubmit` | `check-unfinished-tasks.py` | Warns about unfinished or abandoned tasks when you submit a prompt. |

All hooks are stdlib-only Python and operate within your repository. Read them under
`.claude/scripts/hooks/` (and their canonical source in
`docs-eng-process/.claude-templates/scripts/hooks/`) before enabling.

The example also sets `"defaultMode": "acceptEdits"`, which auto-approves file edits.
If you prefer to approve each edit, change it to `"default"` in your
`.claude/settings.json`.

## Reducing or Disabling the Automation (Opt-Out)

The hooks are **opt-in at the file level** — they only run if they are present in your
project's `.claude/settings.json`. You can keep the OpenUP docs, skills, and teammates
while running fewer (or no) hooks:

- **Disable a single hook:** delete its entry from the relevant event array in
  `.claude/settings.json` (e.g. drop the `auto-log-commit.py` object from
  `PostToolUse`).
- **Disable an entire event class:** remove that event's array (e.g. delete the whole
  `Stop` block).
- **Run with no hooks at all:** remove the `"hooks": { … }` block from
  `.claude/settings.json` (or do not install `settings.json.example`). The skills and
  docs still work; you simply lose automatic process enforcement.
- **Stop auto-approving edits:** set `"defaultMode": "default"`.

**Trade-off:** the hooks are what keep the workflow honest (plan-before-code, no raw
commits, clean exits). Disabling them does not break OpenUP, but enforcement becomes
manual — a deliberate, informed choice, which is the point of this section.

## Dependencies

`requirements.txt` is bounded (`==` pins plus `Pillow>=12.0.0,<13`) and serves only
the optional content-conversion tooling (`converter/`, `scripts/convert.py`). The
OpenUP workflow scripts and hooks are **stdlib-only**, so the process layer has no
third-party dependencies to scan. Run your own dependency/security scan against
`requirements.txt` if you use the conversion tooling.

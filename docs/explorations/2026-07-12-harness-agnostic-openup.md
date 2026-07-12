# Exploration: Harness-agnostic OpenUP

**Started:** 2026-07-12
**Question:** Can the OpenUP process run without Claude Code — on any harness (Codex, Cursor), on a bare LLM with a minimal tool loop, or behind an OpenAPI-compatible service pointed at a directory — and what is the cheapest layering that gets there?

## Context

Today the process ships as a Claude Code plugin surface: `.claude/skills/*/SKILL.md`,
hooks, teammates/teams, `settings.json`, `CLAUDE.md`. The user wants (a) a barebones
core usable from anywhere, (b) per-harness "plugins" (Claude Code, Codex, Cursor, …),
and (c) an OpenAPI endpoint that runs the process against a given directory.

## Notes

### What is already harness-agnostic (most of the system)

An audit of the repo shows the coupling to Claude Code is **thinner than it looks**:

1. **All enforcement and state is files + Python + git, not harness features.**
   `scripts/*.py` (`openup-board.py`, `openup-fence.py`, `openup-state.py`,
   `sync-status.py`, `check-docs.py`, `openup-readiness` logic, `docs-index.py`, …)
   are plain Python 3 CLIs over the working directory. The hard gate is the
   **git pre-push hook** (`.githooks/pre-push` → `openup-fence.py`), which works
   under any harness or none. The Claude Code hooks (`on-task-request.py`,
   `check-iteration.py`) are explicitly *advisory* per CLAUDE.md.
2. **Continuation state lives in the repo by design.** `.openup/state.json`,
   `docs/changes/T-NNN/`, board (derived), leases, Operations checkboxes. The
   standing rule "no information needed to continue work may live only in a
   conversation" is exactly the property a harness-agnostic system needs — any
   driver that can read files can resume the process.
3. **Skills are prompts, not code.** Each `SKILL.md` is markdown + YAML frontmatter
   describing a procedure whose deterministic steps call the scripts. Nothing in
   the *body* of most skills requires Claude Code; they require an agent that can
   read/write files and run shell commands.
4. **There is already an adapter build step.** `sync-templates-to-claude.sh`
   generates `.claude/` from `docs-eng-process/.claude-templates/` at session
   start. The generator pattern the plugin architecture needs already exists —
   it just has only one target today.

### Actual Claude Code couplings (the closable gaps)

- **Canonical source location**: procedures live under `.claude-templates/skills/`
  (a Claude-shaped home) rather than a neutral one.
- **`.claude/memory/`**: `openup-scribe.py learnings` writes
  `.claude/memory/iteration-learnings.md` — should move to `.openup/memory/`.
- **Frontmatter dialect**: `model: inherit`, `fit:` etc. are Claude Code skill
  frontmatter; other harnesses need a mapping (or ignore them).
- **Teams / subagents / fan-out**: `/openup-deploy-team`, `/openup-orchestrate`,
  `/openup-fan-out` use Claude Code agent-team features. These do **not** port —
  but the documented default is already "one agent works the task sequentially;
  teams are opt-in", so the core loses nothing.
- **Hook events** (SessionStart, prompt hooks): advisory only; replaceable by
  git hooks (already present) plus explicit steps in a driver loop.

### Target layering

- **Layer 0 — Process core (exists today):** docs contracts + frontmatter schema,
  Python scripts, git hooks, `.openup/` state. Dependencies: `python3` + `git`.
  Usable by a human with no LLM at all.
- **Layer 1 — Procedure pack (extract):** harness-neutral procedure files (the
  current SKILL.md bodies) moved to a neutral home, e.g.
  `docs-eng-process/procedures/<name>.md`, with a neutral frontmatter schema
  (name, description, arguments, model-tier, fit). This becomes the single
  source of truth.
- **Layer 2 — Harness adapters ("plugins"), each a generator:**
  - *Claude Code*: emit `.claude/skills/`, hooks, teammates — i.e. today's
    `sync-templates-to-claude.sh` re-pointed at Layer 1.
  - *Codex*: emit `AGENTS.md` process section + `.codex/prompts/openup-*.md`
    (custom prompts map 1:1 to slash-skills); enforcement rides the git hooks.
  - *Cursor*: emit `.cursor/rules/openup.mdc` + `.cursor/commands/openup-*.md`.
  - *Generic*: no emission — the procedure files are read directly by the
    Layer-3 driver.
  Capability tiers per adapter: **required** = read/write files, run commands;
  **optional** = subagents/teams, native hooks, plan mode. Procedures declare
  which tier they need; team-based ones are marked optional-capability and
  degrade to sequential.
- **Layer 3 — Reference driver (new, small):** `openup-agent run --dir <path>
  --procedure next` — a plain Python agentic loop against any OpenAI-compatible
  chat-completions endpoint (so it works with OpenAI, Anthropic-via-proxy,
  local models via Ollama/vLLM). Minimal tool surface (see below). Because the
  driver owns the loop, hooks become *deterministic code*: it runs
  `check-docs.py`, the fence, and state updates itself instead of hoping the
  model does — strictly stronger enforcement than any harness gives us.
- **Layer 4 — Service:** FastAPI wrapper over the driver:
  `POST /runs {dir, procedure, args, llm:{base_url, model}}` → run id;
  `GET /runs/{id}` (status + log stream); `GET /projects/board`, `/status`
  (thin wrappers over `openup-board.py` / `sync-status.py`). FastAPI gives the
  OpenAPI schema for free; Python is already a project dependency.

### Minimal tool surface for a bare LLM

Six tools are sufficient (and match what every harness converges on):

| Tool | Signature (sketch) | Why |
|---|---|---|
| `read_file` | `(path, offset?, limit?)` | load specs, state, docs |
| `write_file` | `(path, content)` | create artifacts |
| `edit_file` | `(path, old_str, new_str)` | tick checkboxes, targeted edits — far more reliable than whole-file rewrites on weak models |
| `list_dir` / `glob` | `(pattern)` | discover change folders, templates |
| `grep` | `(pattern, path)` | find task IDs, frontmatter |
| `exec` | `(command, cwd)` | git + the `scripts/*.py` CLIs |

Strictly, `read`/`write`/`exec` alone suffice (exec covers ls/grep/git), but
`edit_file` and `grep` as first-class tools are what make *small* models viable.
For a hardened service, `exec` narrows to an allowlist: `git <subcmd>` +
`python3 scripts/<known-script>.py` — the process only ever needs those.

### Why a minimal LLM is viable here specifically

The repo's own principle — "if a step is deterministic, the harness does it"
(board derivation, fence, validators, sync) — means the LLM is only needed for
judgment steps: authoring specs, writing code, grading rubrics. The driver
sequences everything else. That division is exactly what lets a mid-tier model
run the loop without the process falling apart.

## Options Considered

- **Option A — Extract-and-generate (layered, above).** Neutral procedure pack;
  every harness incl. Claude Code becomes a generated adapter; driver + API on
  top. Pro: single source of truth, Claude Code support provably stays intact
  (its adapter is a re-pointed existing script). Con: migration touches every
  skill file; frontmatter schema work.
- **Option B — Service-first.** Build the FastAPI driver now against the
  existing `.claude/skills` files, skip extraction. Pro: fastest demo of the
  OpenAPI goal. Con: cements `.claude/` as the canonical home; Codex/Cursor
  adapters would read from a Claude-shaped tree — the coupling deepens.
- **Option C — Docs-only portability.** Keep code as-is; write per-harness
  setup guides (RUNNING-AGENTS.md already gestures at Cursor CLI). Pro: zero
  code. Con: doesn't deliver the API, drifts per-harness by hand, no minimal-LLM
  story.

Option A is the recommendation; B's endpoint is A's Layer 4 and can be built
second without rework.

## Open Questions

- Frontmatter mapping: which of `model:`/`fit:`/`arguments:` survive into the
  neutral schema, and how does each adapter translate `model:` tiers
  (docs-eng-process/model-tiers.md) to non-Claude model names?
- Sandboxing for the service: `exec` on a caller-supplied directory is a remote
  code execution surface by construction — container-per-run? allowlist-only
  exec? local-only bind by default?
- Team procedures (`deploy-team`, `orchestrate`, `fan-out`): mark
  optional-capability and degrade to sequential, or exclude from the neutral
  pack entirely?
- Does the driver implement plan-mode-like gating (plan gate on `standard`
  track) as a hard stop awaiting API confirmation, or auto-approve?

### Product-manager challenge pass

- **Pushback 1 — "OpenAPI endpoint" has no named user.** Who calls it, and what
  changes for them vs. running `openup-agent run --dir .` locally? A server that
  execs against arbitrary directories is a security liability bought before any
  demand signal. *Disposition: accepted* — the endpoint is re-scoped to Layer 4,
  built only after the CLI driver works, as a thin wrapper; falsifiable check:
  a named consumer (CI job, web UI, second machine) exists before Layer 4 starts.
- **Pushback 2 — three harness adapters with zero non-Claude users is ritual
  risk.** Maintaining Codex/Cursor generators nobody runs is standing cost.
  *Disposition: partially accepted* — the extraction (Layer 1) is justified on
  its own by the minimal-LLM driver; Codex/Cursor generators ship one at a
  time, each only when someone (starting with the repo owner) commits to
  running it for one real iteration.
- **Complement — git is the universal enforcement point and we already own it.**
  The pre-push fence works under every harness; the plan should lean harder on
  git hooks (add the commit-time `check-docs.py` hook to the neutral
  bootstrap) instead of porting Claude-specific hook events. *Accepted into
  Layer 0 scope.*
- **Complement — the token-efficiency protocol is the minimal-LLM spec in
  disguise.** "One subtask per session, state in repo, compact handoffs" is
  precisely the contract a small-context model needs; the driver should
  enforce it mechanically (fresh conversation per cycle). *Accepted.*
- **Refine — rename the goal from "harness-agnostic" to "harness-optional".**
  Core = files + scripts + git, usable with no harness; every harness is an
  optional adapter with declared capabilities. Sharper, and falsifiable: the
  acceptance test is one full `next`-cycle run end-to-end with (a) Claude Code,
  (b) the reference driver on a non-Anthropic model, producing fence-clean,
  validator-clean commits. *Accepted — this is the iteration's success measure.*

## Where this goes next

→ iteration — promote a roadmap entry "Harness-optional core: extract neutral procedure pack + adapter generator" (Layer 1 + re-pointing the Claude Code generator, acceptance = Claude Code parity via generated adapter), with the reference driver (Layer 3) and OpenAPI service (Layer 4) as follow-on entries ordered by the product manager.

# Graded Tracks (quick / standard / full)

OpenUP grades every unit of delivery work into one of three **ceremony tracks**. The track
decides how much process a change carries — so small work (docs, config, a typo) takes the
near-zero-friction path by default, instead of dragging a full team and a plan gate through
every change. (That was the Kaze failure mode: 18% of commits bypassed the process entirely
because the only sanctioned path was too heavy.)

The track is selected once, at iteration start, and recorded in `.openup/state.json` under
`track`. Hooks and skills read it from there.

**This `quick` is a different axis from the Development Case `archetype`
(`quick`/`mvp`/`product`, `docs/project-config.yaml`'s `process:` block —
see `project-config.md`).** The track sets one task's ceremony; the
archetype tailors an entire phase's iteration budget/artifacts. Don't
conflate them just because both have a `quick` value — a project can run
`quick`-archetype phases with `full`-track tasks inside them, or vice versa.

## The three tracks

| Track | When to use | Ceremony applied |
|---|---|---|
| `quick` | docs / config / typo / comment / rename / version bump / ≤ ~50 LOC in a single file | **state file + auto-log only** — no plan gate, no team, no readiness check |
| `standard` | single-feature work (the default) | plan gate + scribe logging + `/openup-readiness` check; **solo by default — team opt-in** (deploy only with `team:` / `deploy_team: true`) |
| `full` | multi-role / architectural / cross-cutting / schema change / broad refactor | standard **+ team deployment (default-on, opt-out) + rubric assessment** at complete-task |

**One-line selection rule:** *quick for tiny single-file/doc edits; full for multi-role or
architectural work; standard for everything else (the default).*

## Selection heuristics

`on-task-request.py` classifies the task-request prompt and prints a `Suggested track: …`
line in its intake message. The classifier (`suggest_track()`) is a pure keyword matcher:

- **quick** — `typo`, `rename`, `comment`, `bump`, `version`, `doc`/`docs`, `readme`,
  `format`/`formatting`, `lint`, `whitespace`, `small`, `tiny`, `one-liner`.
- **full** — `architecture`/`architectural`, `redesign`, `across`, `migrate`/`migration`,
  `multi-(role|component|service)`, `rework`, `schema change`, `broad refactor`.
- **standard** — the default when neither set matches.

Precedence is **quick → full → standard**: a small-scope signal is decisive (a one-line doc
fix is quick even if it mentions "refactor"), then a broad-scope signal, then the default.

The suggestion is advisory. `/openup-start-iteration` re-checks the actual scope (and the
`docs/changes/{task_id}/plan.md` frontmatter) in its **Select Track** step and the operator
can override with an explicit `track:` argument.

## Wiring

| Surface | What the track controls |
|---|---|
| `.openup/state.json` → `track` | The single source of truth. Written by `openup-state.py init --track {quick\|standard\|full}` (validated against the schema). |
| `gate-edits.py` | On `track == "quick"` the plan gate is **relaxed**: state is still required, but a persisted plan is not, and the bypass is audited to `.claude/memory/bypass-log.md`. `standard`/`full` require `gates.plan_persisted`. |
| `openup-start-iteration` (Select Track + Deploy Team steps) | `quick` ⇒ no team; `standard` ⇒ **solo by default** — deploy a team only with explicit `team:` / `deploy_team: true`; `full` ⇒ team default-on (opt-out with `deploy_team: false` / `team: none`). Explicit `team`/`deploy_team` args override the track default. |
| `check-gates` | The script's `DEFAULT_REQUIRED_GATES` is the full set `team_deployed,log_written,roadmap_synced` (used by `full`). **`quick` and `standard` are solo and call `check-gates --require log_written,roadmap_synced`** — no team gate. Only `full` (or standard work that explicitly deployed a team) gates on `team_deployed`. |
| `openup-complete-task` rubric | Only the **full** track requires `/openup-assess-completeness` for code-bearing tasks. `standard` keeps rubric checks for artifact-generating skills only (unchanged). |

## Entry points

- **`/openup-start-iteration`** selects the track (auto or via `track:`), then applies the
  right ceremony. This is the primary path for `standard` and `full`.
- **`/openup-quick-task`** is the other lightweight entry point: it initializes state with
  `--track quick` directly. Use it for the "I just need to fix this one thing" case.

Both share one task-id space — the quick track does **not** auto-generate ids and the
`[T-XXX]` commit tag stays mandatory. Friction is removed by skipping the *plan gate* and
*team*, not by skipping traceability.

## See also

- [state-file.md](state-file.md) — `.openup/state.json` schema, the `track` field, and gate lifecycle.
- [skills-guide.md](skills-guide.md) — the skills that read and act on the track.
- `.claude/skills/openup-workflow/start-iteration/SKILL.md` — the Select Track + Deploy Team steps.
- `.claude/scripts/hooks/on-task-request.py` — `suggest_track()` and the intake suggestion.

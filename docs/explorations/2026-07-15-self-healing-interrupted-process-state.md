# Exploration: Self-healing for interrupted / corrupted OpenUP process state

**Started:** 2026-07-15
**Question:** When an OpenUP run is interrupted or leaves process state corrupted,
should the tooling detect *and repair* it itself — and if so, what is safely
auto-healable versus a genuine human-judgment boundary that must stay manual?

## Context

Explored after a dogfood session where a human operator repeatedly had to *notice*
and *hand-repair* process papercuts that the tooling arguably should fix itself:

- `settings.json` hook-block reorder drift left the tree dirty (a semantic no-op
  diff), and `on-stop.py` refused to stop until it was committed/reverted.
- I hand-scheduled six roadmap rows when `/openup-next` no-op'd on a drained
  roadmap — **later recognized as the WRONG instinct**; that no-op was correct.

The framework already has the *detector* half of the seam:
`scripts/openup-doctor.py` is strictly read-only ("Doctor is strictly diagnostic:
it never writes, mutates, or fixes anything. Fixes stay in their owning scripts")
and already emits remediation strings inside findings, e.g.
`run \`python3 scripts/sync-status.py --reconcile\``. What's missing is an
*applier* — nothing turns a detected, remediable finding into the fix.

Owning fix-scripts that already exist (the "heal primitives"):
`sync-status.py --reconcile`, `openup-state.py set-gate` / `init --force`,
`sync-templates-to-claude.sh`, the derived-view generators (`docs-index.py`,
`render-skills-mirror.py`), `openup-claims.py` (lease repair).

## Notes

### 1. Taxonomy of interrupted / corrupted states (from memory notes + doctor checks)

| # | State | Source | Owning fix (heal primitive) |
|---|-------|--------|------------------------------|
| A | Derived/mirror file drift — `docs/roadmap.md` Status cells, `docs/project-status.md`, `INDEX.md`, skills mirror, `.claude/` sync | doctor `roadmap-status-drift`, `docs-index --check`, `render-skills-mirror --check`, `check-claude-sync` | re-run the generator (`sync-status.py --reconcile`, `docs-index.py`, `render-skills-mirror.py`, `sync-templates-to-claude.sh`) |
| B | `settings.json` hook-block reorder drift (semantic no-op, dirty tree) | this session | re-serialize canonically, or `git checkout` if byte-equal-modulo-order to HEAD's semantics |
| C | `begin` didn't set `gates.plan_persisted` → `gate-edits.py` blocks code edits mid-lane | `begin-doesnt-set-plan-gate` | `openup-state.py set-gate plan_persisted docs/changes/<id>/plan.md` |
| D | Promote stranded the spec on `main` (uncommitted, wrong worktree) | `promote-spec-worktree-strand` | move spec folder into worktree before `begin` |
| E | `next` re-promoted a delivered-but-unmerged PR | `next-repromotes-unmerged-pr` | **already fixed** (T-066: `cmd_next` consults origin) |
| F | `state init --force` clobbered live lane → auto-log mis-routes | `state-init-force-clobbers-live` | re-init state to real values + delete stray shards |
| G | Spec-authoring / null-status tripped `sync-status` → task mis-marked `completed` | `spec-authoring-syncstatus-conflation`, `no-sync-status-at-handoff` | toggle `log_written` around sync, or `git checkout` the views |
| H | auto-log-commit re-dirties run-log → on-stop tail-chase loop | `t006-autolog-onstop-loop` | **already fixed** (T-068: `resolve_commit_root`; on-stop exemption) |
| I | Corrupt/unreadable `.openup/state.json` (bad merge, partial migration) | doctor `state-integrity` | (no safe generic auto-fix — needs the intended values) |
| — | Roadmap drained mid-phase; `/openup-next` no-ops asking the PM to schedule | this session | **NOT corruption** — correct human boundary |

### 2. Classification: auto-heal / heal-with-confirmation / human-only

**Auto-heal (idempotent, output fully determined by tracked inputs, zero
judgment).** The invariant: *the file is a pure function of other tracked state,
so regenerating it cannot lose information.*
- A — derived/mirror drift. Regenerating is the *defined* repair; hand-editing is
  already forbidden. This is the safest and highest-frequency class.
- B — `settings.json` reorder drift, **only** when the diff is provably a
  key-reorder with identical semantics (no hook added/removed/changed). Otherwise
  it's a real config change → human.
- C — unset `plan_persisted` when `docs/changes/<id>/plan.md` demonstrably exists
  and matches the active lane. The value is not a judgment call; it's a lookup.

**Heal-with-confirmation (repair is mechanical but touches persisted intent or is
destructive if the diagnosis is wrong).**
- F — re-init clobbered state: the *real* values must be recovered (from branch
  name, roadmap, git log). Mechanical to propose, dangerous to apply blind.
- G — un-stamp a wrongly-`completed` roadmap cell: safe to propose ("this task's
  work hasn't started; revert the cell?"), but it mutates a shared product view.
- D — move a stranded spec into the worktree: mechanical, but a wrong guess moves
  files across branches.

**Human-judgment-only (never auto).**
- I — corrupt `state.json` with no recoverable intent. Doctor should surface,
  not guess.
- The roadmap-drained-mid-phase no-op — *this is the anti-example that defines the
  boundary.* `/openup-next` stopping and asking the PM to schedule UC work is
  **correct**; auto-generating roadmap tasks there would fabricate product intent.
  Self-heal must never cross from "restore a derivable invariant" into
  "manufacture a decision that is a human's to make."

**The dividing line:** auto-heal restores state that is a *pure function of
tracked inputs* (derived views, mirrors, gates with a single correct value).
Everything that requires recovering or inventing *intent* is confirm-or-human.

### 3. Shape: `openup-doctor --fix` orchestrating owning scripts vs. recovery baked into each script

Both are needed and they compose — they answer different questions:

- **Baked-in recovery (per owning script)** = *prevention*. The best fix for C is
  that `begin` sets the gate; for D that `promote` commits/moves the spec; for E/H
  the guards that already shipped. These stop the interruption from *creating*
  corrupt state. Cases E and H prove this path works. But baking a recovery into
  every script is a long tail of one-off patches — exactly the per-bug treadmill
  this exploration is questioning — and it can't help a tree that's *already*
  corrupted by an older tool version or an external edit.

- **`openup-doctor --fix` (central applier)** = *cure*. Doctor already enumerates
  the remediable findings and owns the read-only detection. Giving it a `--fix`
  that, for auto-heal-class findings, *invokes the owning fix-script* (never
  reimplements it — same DD1 discipline that keeps detection a single source of
  truth) yields one command that recovers any well-formed project to health.
  Confirm-class findings print the proposed command and require `--fix
  --confirm`/interactive assent; human-only findings only ever print.

**Recommended shape:** `openup-doctor --fix` as the orchestrator, delegating to
existing owning scripts, gated by the three-way class of each finding. Baked-in
prevention continues opportunistically (it's strictly better when cheap), but the
*systematic* answer — the thing that ends the "human diagnoses each papercut
live" cost — is the central applier keyed off doctor's existing taxonomy.

## Options Considered

- **Option A — `openup-doctor --fix` orchestrator over owning scripts.**
  Pro: reuses the existing detector + remediation strings; single source of truth
  for both detect and fix; one command for operators; class-gated so it can't
  cross the intent boundary. Con: doctor grows from pure-diagnostic to
  read-write (must guard the strict-read-only contract carefully — likely
  `--fix` is opt-in and the default stays read-only).
- **Option B — recovery baked into each owning script only.** Pro: prevention at
  the source; no new read-write surface on doctor. Con: the per-bug treadmill;
  can't heal already-corrupt trees; no single operator entry point.
- **Option C — do nothing; keep hand-fixing.** Pro: zero work. Con: this
  exploration exists *because* hand-fixing is the recurring cost; rejected.

## Open Questions

- Does each auto-heal-class finding already have a *non-interactive, idempotent*
  invocation of its owning script, or do some need a `--reconcile`-style flag
  added first? (A/C likely yes; B needs a canonical `settings.json` serializer.)
- Where does `--fix` run relative to the write-fence and gates — does healing a
  derived view mid-lane need to respect `touches`, or is it exempt like the
  generators already are?
- Confirmation UX in an autonomous loop: `--fix` auto-heal-only by default,
  `--fix --confirm` to include confirm-class? What's the loop-safe default?

### Product-manager challenge pass

*(Role hat: `.claude/teammates/product-manager.md` — no team deployed.)*

- **Pushback:** The submitted framing risked lumping *all* the memory-note
  papercuts into one "self-heal" bucket. Two of the six motivating cases (E, H)
  are **already fixed** by baked-in guards — so the value case is not "nothing
  heals today" but "detection outpaces application, and prevention is patched
  one-bug-at-a-time." If a `--fix` feature only re-covers cases already prevented
  at the source, it earns nothing. The value must be measured on states that are
  *detected but not yet auto-applied* (class A drift above all — highest
  frequency, lowest risk) — that's where a user notices the difference (a dirty
  tree or a stale view heals without a human diagnosing it). Disposition:
  **accepted** — narrowed the target to the detected-not-applied set, with class
  A as the falsifiable first win.
- **Complement:** The submission missed that the roadmap-drained no-op is the
  *defining negative boundary*, not just an excluded item — it's what keeps the
  feature from scope-creeping into "auto-manufacture product decisions." Also
  missed: doctor's own DD1 ("invoke, never reimplement") is the exact discipline
  that should govern `--fix` (delegate to owning scripts). Disposition:
  **accepted** — both folded into the classification and the shape section.
- **Refine:** "Self-heal every interrupted state" → the falsifiable version:
  *"openup-doctor --fix restores every auto-heal-class finding (derived-view
  drift, no-op config reorder, single-valued unset gate) to green
  non-interactively, touches nothing in the confirm/human classes, and is proven
  by a test that corrupts each class and asserts fix-then-clean."* Disposition:
  **accepted** as the proposed iteration's acceptance shape.
- **Rejected challenge:** "Just make everything auto-heal, skip the three
  classes." Rejected — the roadmap-drained case proves an unconditional healer
  would fabricate intent; the class boundary is the feature's core safety
  property, not optional polish.

## Where this goes next

→ iteration — Roadmap entry **"openup-doctor `--fix`: apply auto-heal-class
findings"**: extend `openup-doctor.py` with a `--fix` mode that, for
auto-heal-class findings only (derived/mirror drift, provable no-op config
reorder, single-valued unset gate), invokes the owning fix-script (never
reimplements it), leaves confirm-class findings as printed proposals behind
`--fix --confirm`, and never touches human-judgment-only findings; proven by a
test that corrupts one state per class and asserts `--fix` reaches green without
crossing the intent boundary. Baked-in prevention for individual cases (C/D/G)
stays a separate, opportunistic follow-up, not part of this entry.

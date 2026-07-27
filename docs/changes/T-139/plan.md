---
id: T-139
title: "T-107 split — customized process sources: a project-owned override path, documented and pinned"
status: ready
priority: medium
estimate: 1 session
plan: docs/changes/archive/T-107/plan.md
depends-on: [T-137]
blocks: []
last-synced: ""
touches:
  - scripts/openup-process-map.py
  - docs-eng-process/project-config.md
  - docs-eng-process/reference-driver.md
  - tests/test_process_map.py
---

# T-139 — Customized process sources: a project-owned override path, documented and pinned

## Story

> **As a** maintainer of a project that vendors this framework
> **I want** a project-owned path where my own process map + task library override the framework defaults, documented and covered by a test
> **So that** I can tailor the authoring definitions without editing vendored framework files or relying on an undocumented accident

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The process-map / task-library resolution seam
  (`scripts/openup-process-map.py` `_MAP_CANDIDATES` / `_TASK_CANDIDATES`), its
  compiler (`scripts/build-task-library.py`), and the project-tailoring doc
  (`docs-eng-process/project-config.md`).

- **Premise check (run before drafting — action item B2, T-137 precedent).**
  Two of T-107 Requirement 4's four acceptance bullets were **already satisfied**,
  verified in a scratch project rather than asserted:
  - *Compiler accepts a project-local input root* — `--repo-root` already does
    this. `build-task-library.py --repo-root <fakeproj> --check` exits 0 against
    that root's library and its `source:` paths.
  - *Project-local library/map override via the candidate fallback* — already
    works. `_TASK_CANDIDATES[0]` is `docs-eng-process/task-library.yaml`;
    `bootstrap-project.sh:145` copies that whole tree into every project; a
    1-def project library fully shadowed the framework's 9
    (`[task-library] ✓ valid — 1 task def(s)`). `sync-from-framework.sh:589`
    deliberately never overwrites `docs-eng-process/` ("not syncing to preserve
    local changes"), so the customization survives updates.

  So the mechanism exists. What does **not** exist is (a) a project-owned place to
  put it, (b) any documentation of it, and (c) any test pinning it.

- **Why a new path rather than "document the vendored one".** Overriding today
  means editing a file inside the vendored `docs-eng-process/` tree — which every
  other convention in this framework says is framework-owned and re-syncable. That
  it survives is an implementation detail of one `else` branch in
  `sync-from-framework.sh`, not a contract. Documenting "edit the vendored file, we
  promise not to overwrite it" would make a public contract out of that detail and
  freeze it. A project-owned first candidate under `docs/` (peer to
  `docs/project-config.yaml`, the existing project-tailoring file) is two lines,
  additive, and makes the seam designed rather than accidental.

- **Scope boundaries.** No compiler **emitter**. `build-task-library.py` writes no
  YAML for anyone today — the framework's own library is hand-assembled and
  human-reviewed — and Stage-1 extraction parses only UMA/KB-shaped documents
  (`related.roles` frontmatter, `Inputs|` sections), a shape a project's own process
  docs are unlikely to have. Building an emitter here would create a path nothing
  exercises, on an unverified input premise; it is filed as a follow-up with that
  premise named, not built (the disposition T-137 took for the KB compile).
  Also out: any change to the KB, to `cycle.py`'s consumption of the library, or
  to `sync-from-framework.sh`'s docs-preservation branch.

- **Definition of done.** A project-owned `docs/process/` override resolves ahead
  of the vendored copy for both map and library; the compiler's `--check` honors
  the same resolution; the candidate-order comments describe what actually
  happens; `project-config.md` documents the mechanism *and* its limits; tests pin
  both the override and the unchanged no-override behavior; the emitter is filed
  as a follow-up.

> **Assumption:** the project-owned path is `docs/process/{process-map,task-library}.yaml`
> — under `docs/`, peer to `docs/project-config.yaml`, because that is where this
> framework already puts project-owned tailoring. *(Vetoable at review; the
> alternative considered was `.openup/process/`, rejected because `.openup/` is
> Ring-3 ephemeral and gitignored here, so an override placed there would not
> survive a fresh clone.)*

> **Assumption:** the two `scripts/*.yaml` candidates are **kept**, not removed,
> and re-commented as a vendoring escape hatch for a project that installs the
> CLIs without the docs tree. Removing them is a behavior change for any repo that
> already placed a file there; a wrong comment is fixable without that risk.
> *(Vetoable at review.)*

> **Assumption:** a project-owned library **replaces** the framework's rather than
> merging with it — the existing first-match-wins loop, unchanged. Merge semantics
> would be a new resolution design, not a documentation of the current one.
> *(Vetoable at review.)*

## Requirements

1. The loader resolves a project-owned override ahead of the vendored framework
   copy, for **both** the process map and the task library.
   - **Given** a repo carrying both `docs/process/task-library.yaml` and
     `docs-eng-process/task-library.yaml` **When**
     `openup-process-map.py --repo-root <repo> tasks --validate` runs **Then** it
     validates only the defs in `docs/process/task-library.yaml`.
   - **Given** a repo carrying both `docs/process/process-map.yaml` and
     `docs-eng-process/process-map.yaml` **When**
     `openup-process-map.py --repo-root <repo> activities-for inception` runs
     **Then** the activities come from `docs/process/process-map.yaml`.

2. Repos without an override behave exactly as before — the change is additive.
   - **Given** a repo root carrying `docs-eng-process/task-library.yaml` and **no**
     `docs/process/` directory **When** the loader resolves the library **Then** the
     resolved path is the `docs-eng-process/` one and the parsed def set is
     byte-identical to what the pre-change loader returned for the same root.
   - **Given** this repo (no `docs/process/`) **When**
     `openup-process-map.py tasks --validate` and `openup-process-map.py validate`
     run **Then** both exit 0 with the framework's 9 task defs, as they do today.

3. `build-task-library.py --check` honors the same resolution, so a project-owned
   library is checkable against that project's own `source:` paths.
   - **Given** a project root whose only library is `docs/process/task-library.yaml`
     holding `source: driver` defs **When**
     `build-task-library.py --repo-root <root> --check` runs **Then** it exits 0
     and reports skeletons in sync, having consulted no framework library.

4. The candidate-order comments in `openup-process-map.py` describe the actual
   precedence and ownership of every entry.
   - **Given** a reader opens `_MAP_CANDIDATES` / `_TASK_CANDIDATES` **When** they
     read the comments **Then** each entry names who owns it and when it wins, and
     no entry is described by a delivery mechanism that does not deliver it
     (today `scripts/task-library.yaml` is labelled "shipped-into-a-project
     fallback" and nothing in the repo ships it).

5. `docs-eng-process/project-config.md` documents the customization mechanism and
   its limits in one place, and `reference-driver.md`'s task-library section points
   at it.
   - **Given** a maintainer who wants their own task library **When** they read
     `project-config.md` **Then** they find the override path, the full resolution
     order, the replace-not-merge semantics, and the statement that a def whose
     `source:` is not a KB-shaped file must use `source: driver` or `--check` will
     report it as drift.

6. The absent emitter is stated as absent, not left to be inferred, and filed as a
   follow-up carrying its unverified premise.
   - **Given** a reader looking for "compile my own process docs into a library"
     **When** they read `project-config.md` **Then** it states that
     `build-task-library.py` checks and distills but never writes YAML — a
     project authors its library by hand — and names the follow-up roadmap entry.
   - **Given** this task completes **When** the roadmap is read **Then** a pending
     entry exists for the emitter, whose Value names the unverified premise
     (project process docs are not UMA-shaped) as the thing to settle first.

## Behavior Delta

Ring 1 for this repo is `docs/product/` (milestones only) — this task changes
framework tooling and process documentation, not product behavior recorded there.

**Added** — a project-owned `docs/process/` resolution step ahead of the vendored
copies, for the process map and the task library; a "Customized process sources"
section in `docs-eng-process/project-config.md`.

**Modified** — `docs-eng-process/reference-driver.md §"The task library — checking
and re-distilling"` gains a pointer to the new project-config.md section (no change
to the runbook itself).

**Removed** — n/a. (The `scripts/*.yaml` candidates are re-commented, not removed —
see the Analysis Context assumption.)

## Entities

- **Map/library loader** (modified) — `scripts/openup-process-map.py`
  (`_MAP_CANDIDATES`, `_TASK_CANDIDATES`, `load_tasks`, the map reader)
- **Compiler** (read-only here) — `scripts/build-task-library.py` (inherits the
  resolution via `_pm.load_tasks`; changes only if R3 fails without it)
- **Project-tailoring doc** (modified) — `docs-eng-process/project-config.md`
- **Driver doc** (modified) — `docs-eng-process/reference-driver.md`
- **Loader tests** (modified) — `tests/test_process_map.py`
- **Project override** (new, project-side) — `docs/process/{process-map,task-library}.yaml`

## Approach

Prepend one project-owned candidate to each of the loader's two existing
first-match-wins tuples, so an override is a file a project creates rather than a
framework file it edits. Nothing else in the resolution changes: same loop, same
replace-not-merge semantics, same `--repo-root`. The compiler inherits the new
order for free through `_pm.load_tasks`. The remaining work is truth-telling —
comments that match behavior, one documentation section that states the order and
the limits, and tests that pin both the override and the untouched default so the
seam stops being an accident.

## Structure

**Add:**
- `docs-eng-process/project-config.md` § "Customized process sources" — the
  mechanism, resolution order, limits, and the no-emitter statement.
- Tests in `tests/test_process_map.py`: project-owned map override, project-owned
  library override, no-override default unchanged, compiler `--check` against a
  project-owned library.

**Modify:**
- `scripts/openup-process-map.py` — prepend `docs/process/…` to `_MAP_CANDIDATES`
  and `_TASK_CANDIDATES`; rewrite both tuples' per-entry comments to state owner
  and precedence.
- `docs-eng-process/reference-driver.md` — one pointer from the task-library
  section to the new project-config.md section.

**Do not touch:**
- `scripts/build-task-library.py` — it inherits resolution from `_pm.load_tasks`;
  touch it only if R3's scenario fails, and say so in `design.md` if it does.
- `scripts/sync-from-framework.sh` — its docs-preservation branch is what makes
  the *old* override survive; this task adds a path instead of depending on it.
- `docs-eng-process/task-library.yaml` and the vendored KB — the framework's own
  library and its source are unchanged.
- `openup_agent/cycle.py` — how the engine *consumes* the library is out of scope.

## Operations

- [x] Record the premise-check evidence (the two already-satisfied bullets, with
      the commands and their output) in `docs/changes/T-139/design.md`, so the
      "why this task shrank" reasoning outlives the session.
- [x] Prepend the project-owned candidate to `_MAP_CANDIDATES` and
      `_TASK_CANDIDATES`, and rewrite both tuples' comments to state owner +
      precedence per entry.
- [x] Verify `build-task-library.py --check` inherits the new resolution against a
      project-owned library; if it does not, note the cause in `design.md` before
      changing the compiler.
- [x] Write `project-config.md` § "Customized process sources": resolution order,
      which file to create, replace-not-merge, the `source: driver` rule for
      non-KB-shaped defs, and the explicit no-emitter statement.
- [x] Add the `reference-driver.md` pointer from the task-library section to that
      new section.
- [x] (tester) Add the four tests to `tests/test_process_map.py` (map override,
      library override, no-override default unchanged, compiler `--check` on a
      project-owned library); run the full suite.
- [x] File the emitter follow-up as a pending roadmap entry (via
      `/openup-complete-task`'s follow-up enqueue, not a hand-edit of the shared
      view) whose Value names the unverified UMA-shape premise as the thing to
      settle before any build.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- `docs-eng-process/project-config.md` — the precedence chain this section joins
- `docs-eng-process/reference-driver.md` § "The task library — checking and re-distilling"
- `docs/changes/archive/T-107/plan.md` (Requirement 4 — the originating scope) and
  `docs/changes/archive/T-137/design.md` (the already-satisfied disposition precedent)

## Safeguards

- **Additive only.** A repo with no `docs/process/` must resolve exactly as it does
  today. R2 is the regression test for this and must be written before the tuples
  change.
- **No emitter.** The compiler does not gain a YAML-writing mode in this task. If
  the work starts drifting toward one, stop — that is the follow-up, gated on the
  UMA-shape premise.
- **No merge semantics.** First-match-wins is preserved; a project-owned library
  replaces the framework's. Do not add merging under cover of "documenting".
- **This repo must not shadow itself.** The framework repo is also a repo root, so a
  `docs/process/` created here would shadow the framework's own map and library for
  every skill and for the driver. Do not create one; the tests build their overrides
  in temp roots only.
- **Reversibility.** The code change is two prepended tuple entries; reverting them
  restores current behavior exactly, and the docs section becomes stale rather than
  wrong.
- **Truthfulness of the docs.** Every claim written into `project-config.md` must be
  one this task actually verified — no repeating T-107's "the loader prefers the
  project copy" phrasing without the test that proves it.

## Verification

- `python3 -m pytest tests/test_process_map.py` — the four new tests pass.
- Full suite green; `python3 scripts/check-docs.py` clean.
- `python3 scripts/openup-process-map.py tasks --validate` in this repo still
  reports the framework's defs (R2, no-override default unchanged).
- A scratch project with `docs/process/task-library.yaml` resolves its own defs and
  `build-task-library.py --repo-root <scratch> --check` exits 0 (R1, R3).
- `docs-eng-process/project-config.md` § "Customized process sources" answers the
  R5 reader question without needing the code.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

We expect the number of consumer repos carrying a project-owned `docs/process/`
override to move **from 0 to ≥1** within **90 days** of this landing (read-back
**2026-10-25**). Instrumentation:

```bash
ls <repo>/docs/process/process-map.yaml <repo>/docs/process/task-library.yaml
```

Read-back environment: the four sibling consumer repos, **verified reachable from
this machine when this spec was written** (so a `0` cannot be the T-052 "instrument
does not exist here" artifact) — `../../kaze/kaze-webapp`,
`../../cqecho/cqecho-app`, `../es-invoices`, `../../TallyFox/tallyfox-app`. All four
are read-only evidence; never modified from here.

This measure is deliberately falsifiable **against the feature's own premise**: T-107's
P2 promise ("a project wants to override the framework's task library") has never
been validated by an actual ask. A `0` at read-back is a real result, not a
measurement failure — it says the demand is not there, and the correct response is
to **retire** the emitter follow-up rather than schedule it.

## Rollout

n/a — no flag. This is internal framework tooling and documentation; the feature is
opt-in by the mere existence of a file a project creates, and its absence is the
current behavior. A flag would gate a code path that is already inert when unused,
adding a switch with nothing to switch off. Backout is reverting two tuple entries.

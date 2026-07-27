# T-139 — design notes

**Parent task**: T-107 (split into T-137 / T-138 / T-139 — see
`docs/changes/archive/T-107/plan.md` Requirement 4 and
`docs/changes/archive/T-137/design.md`).

## Premise check — run before drafting the spec (action item B2, T-137 precedent)

T-107's Requirement 4 carried four acceptance bullets. **Two were already
satisfied.** Verified 2026-07-27 in a scratch project, before any code was
written — not reasoned about, run:

### Already satisfied 1 — "compiler accepts a project-local input root"

`build-task-library.py` has had `--repo-root` since T-105. Against a scratch
project root whose only library is its own:

```
$ python3 scripts/build-task-library.py --repo-root <scratch> --check
[task-library] ✓ skeletons in sync with KB sources
```

It resolved that root's library and its `source:` paths. No framework library or
KB was consulted.

### Already satisfied 2 — "project-local library/map override via the candidate fallback"

The loader's first candidate is `docs-eng-process/task-library.yaml`
(`scripts/openup-process-map.py:67-70`), and `bootstrap-project.sh:145` copies
that **entire tree** into every bootstrapped project. So every project already
owns an editable copy at the first-match-wins path. A scratch project carrying a
single made-up def:

```
$ python3 scripts/openup-process-map.py --repo-root <scratch> tasks --validate
[task-library] ✓ valid — 1 task def(s)
```

One def, not the framework's nine — the project copy **fully shadowed** the
framework's. And `sync-from-framework.sh:589` deliberately never overwrites
`docs-eng-process/`:

> `log_verbose "Documentation directory exists (not syncing to preserve local changes)"`

so the customization survives framework updates. Only `.template-version` is
mirrored.

### What was actually missing

The mechanism worked; what did not exist was

1. a **project-owned place** to put the override (today you must edit a file
   inside the vendored `docs-eng-process/` tree),
2. any **documentation** of it — `docs-eng-process/project-config.md` had zero
   mentions of `task-library`, `process-map`, or customization, and
3. any **test** pinning it.

### Why a new path instead of documenting the vendored one

Overriding today means editing a vendored framework file. That it survives is an
implementation detail of one `else` branch in `sync-from-framework.sh`, not a
contract. Documenting "edit the vendored file, we promise not to overwrite it"
would promote that detail to a public contract and freeze it. A project-owned
first candidate under `docs/` — peer to `docs/project-config.yaml`, where this
framework already puts project-owned tailoring — is two lines and additive.

### Side finding — a dead candidate with a misleading comment

`_TASK_CANDIDATES[1]` is `scripts/task-library.yaml`, commented
"shipped-into-a-project fallback". **Nothing in the repo ships it** — the only
occurrence of that string anywhere is the tuple entry itself. Same for
`_MAP_CANDIDATES[1]`. Kept (removing them is a behavior change for any repo that
already placed a file there) but re-commented honestly.

## Scope decision (owner, this session)

Asked before drafting, because the answer changed scope: document-and-make-honest,
**or** also build the compiler emitter T-107 R4 implies?

**Chosen: document + make honest.** The emitter is deferred with its premise named
rather than built, because:

- `build-task-library.py` writes **no YAML for anyone** today. The framework's own
  library is hand-assembled and human-reviewed; `--check` and `--offline` only read
  and emit prompts. An emitter would be a brand-new output path with no existing
  consumer.
- Stage-1 extraction parses only **UMA/KB-shaped** documents — `related.roles`
  frontmatter and `Inputs|` sections (`extract_skeleton`, `_extract_inputs`). A
  project's own process docs are unlikely to be in that shape, so the emitter's
  *input* premise is unverified.

This is the disposition T-137 took for the KB compile: don't build ahead of a
consumer. The emitter is filed as a follow-up whose Value names the UMA-shape
premise as the thing to settle first.

## Implementation note — test order

The spec's "additive only" safeguard requires R2 (no-override behavior unchanged)
to be pinned **before** the tuples change, so the regression test is written first
and run against unmodified code. Recorded here because the Operations list orders
tests last; the safeguard wins.

## Completion grades (step 1a / 1b)

### 1a — every requirement graded against the actual diff

Scenarios were run in the **CLI form the spec wrote them in**, not just via the unit
tests, against a scratch project carrying *both* a vendored and a project-owned copy.

- ✅ **R1** (override wins, map + library) —
  `openup-process-map.py --repo-root <proj> tasks --validate` → `✓ valid — 1 task def(s)`
  (the project's single def, not the framework's 9, with the vendored file present);
  `--repo-root <proj> activities-for inception` → `house-style-kickoff  analyst`,
  from the project map. Pinned by `TestProjectOwnedOverrideWins`.
- ✅ **R2** (no-override unchanged) — in this repo, `tasks --validate` → `✓ valid — 9
  task def(s)` and `validate` → `✓ valid — 4 phases, 8 activities`, both unchanged.
  Pinned by `TestNoOverrideIsUnchanged`, whose four tests were **written and passing
  against unmodified code before the tuples changed** — so they are a real regression
  guard for the additive claim, not a description of the new behavior.
- ✅ **R3** (compiler honors the resolution) —
  `build-task-library.py --repo-root <proj> --check` → exit 0, `✓ skeletons in sync`.
  `scripts/build-task-library.py` was **not modified**: it inherits resolution through
  `_pm.load_tasks`, as the spec's Do-not-touch predicted. Verified, not assumed.
- ✅ **R4** (honest candidate comments) — both tuples in
  `scripts/openup-process-map.py` now number each entry with its owner and when it
  wins. The false "shipped-into-a-project fallback" label on `scripts/*.yaml` is gone,
  replaced by "escape hatch … Nothing in this repo ships this file".
- ✅ **R5** (documented in one place, pointed at) —
  `docs-eng-process/project-config.md` § "Customized process sources" carries the
  resolution-order table, "Replace, not merge", and the `source: driver` rule;
  `reference-driver.md`'s task-library section links to it by anchor.
- ✅ **R6** (absent emitter stated, follow-up filed) — project-config.md states
  `build-task-library.py` "never writes YAML"; roadmap entry **T-156** exists, and its
  Value leads with the gate ("the premise comes first, not the code") naming the
  unverified UMA-shape premise.

Full suite: **987 passed, 1 skipped** (8 new tests). `check-docs.py` OK,
`docs-index.py --check` in sync.

### 1b — Success-Measure instrumentation, in the named read-back environment

✅ **instrumentation** — the measure reads
`ls <repo>/docs/process/{process-map,task-library}.yaml` in the four sibling consumer
repos. Run there at completion time, establishing the baseline:

| repo | override files | carries `docs-eng-process/` |
|---|---|---|
| kaze-webapp | 0 | yes |
| cqecho-app | 0 | yes |
| es-invoices | 0 | yes |
| tallyfox-app | 0 | yes |

All four are reachable and are genuine framework consumers, so the instrument
produces a real number *there* — not the T-052 failure where the named instrument
did not exist in the environment the number had to come from.

**Stated precondition for the read-back (2026-10-25).** `docs/process/` is only
honored by a checkout carrying **this** version of
`scripts/openup-process-map.py`. A repo that has not run `sync-from-framework.sh`
since this landed would read `0` meaning *"not delivered"*, not *"no demand"*.
At read-back, check each repo's synced loader **before** interpreting its `0` —
and only a `0` across repos that **do** carry the new loader is evidence to retire
T-156.

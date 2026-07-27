# T-155 — design notes

## Implementation verification against spec (complete-task step 1a)

Graded requirement by requirement against the diff vs `origin/main`.

1. ✅ **Both entries in the framework's `.gitattributes`** — `.gitattributes`
   gains `.claude/memory/bypass-log.md merge=union` and
   `.claude/memory/iteration-learnings.md merge=union`, under a comment naming
   T-155, the rejected sharding option, the downstream evidence, and the
   server-side residual.
2. ✅ **A fresh consumer receives them** — green
   `test_consumer_smoke.py::test_consumer_receives_merge_union_for_shared_memory_files`,
   asserted against a *really bootstrapped* project (the T-153 fixture runs
   `bootstrap-project.sh` into `tmp_path`). Verified to bite: stripping the two
   lines from `.gitattributes` failed exactly that test and nothing else.
3. ✅ **Added to an existing consumer, content preserved** — green
   `test_adds_entries_and_preserves_existing_content` (a fixture carrying
   `* text=auto` + a project-specific line keeps both).
4. ✅ **Idempotent** — green `test_second_run_is_a_byte_identical_no_op` (file
   unchanged *and* nothing reported) and
   `test_each_entry_appears_exactly_once_after_repeated_runs` (3 runs, 1
   occurrence each).
5. ✅ **Creates the file when absent** — green
   `test_creates_the_file_when_the_project_has_none`, the `cqecho-app` shape.
6. ✅ **`--dry-run` reports without writing** — green
   `test_dry_run_reports_without_writing` and
   `test_dry_run_does_not_create_a_missing_file`.
7. ✅ **Residual documented where the class is defined** —
   `docs-eng-process/parallel-lanes.md` class-2 row now states the decision, why
   sharding was rejected, the two delivery paths, and that PR conflicts remain.

**No ❌.** Affected modules: **21 passed**
(`test_consumer_smoke.py`, `test_sync_migration.py`,
`test_t155_memory_merge_union.py`). `gates.implementation_verified` set
accordingly.

## Success-measure instrumentation (complete-task step 1b)

✅ **instrumentation pre-exists in the named read-back environment.** The measure
is read in **`kaze-webapp`** (read-only) — necessarily downstream, since this
repo gitignores `/.claude/*` and can never produce the collision. The instrument
is a git-history query needing nothing installed there, and it was **run there
on 2026-07-27, before this spec was written**: for each merge commit touching
`.claude/memory/bypass-log.md`, compare against both parents; a merge differing
from both is a two-sided reconciliation. Baseline: **3 of 3**.

⚠️ **Read-back has a precondition, stated in the spec and repeated here**: the
attribute only reaches that repo when *it* runs `sync-from-framework.sh`. A `0`
read before that has landed means "not delivered", not "fixed" — so the
read-back must first confirm both entries exist in `kaze-webapp/.gitattributes`.
Skipping exactly this check is what made T-052's measure unanswerable.

## The decision: `merge=union`, not sharding

The roadmap offered three options (union / shard / accept). Evidence gathered
read-only from the two consumer repos before drafting (action item B2, the T-147
DD4 precedent) narrowed it sharply:

| | `kaze-webapp` | `cqecho-app` |
|---|---|---|
| Tracks the two files | yes | **no — neither** |
| `.gitattributes` | yes (3 lines) | **none** |
| Two-sided merges, `bypass-log.md` | **3 of 3** | n/a |
| Two-sided merges, `iteration-learnings.md` | **0** | n/a |

So: **one** affected repo, and within it **one** affected file. All three
observed collisions are *local* merges (`merge origin/main into <branch>`) —
precisely the case a merge driver runs for.

## Decisions

- **DD1 — Union, not sharding.** Sharding is what T-046 chose for
  `agent-runs.jsonl`, so it needed a real hearing. Rejected on a difference that
  matters: the run log is consumed by *tooling* that can assemble a view, while
  these two are read **directly at a fixed path** by an agent at session start
  (`.claude/CLAUDE.openup.md`) and by hooks. Sharding would require a
  consolidation step that nothing currently runs, in the consumer's checkout,
  and would mean changing consumer-side writers plus migrating existing files —
  for a problem that has occurred three times.
- **DD2 — Both files, not just the one that has collided.**
  `iteration-learnings.md` has never had a two-sided merge (one append per
  completion, completions are serial). It gets the attribute anyway: same shape,
  same involuntary class-2 surface, and a per-file split would encode "hasn't
  bitten yet" as design.
- **DD3 — Delivery is the substance, not the attribute.** The one-line change is
  trivial; the finding is that it would have reached **nobody who needs it**.
  `bootstrap-project.sh` copies `.gitattributes` only at first install, and no
  updater touched it — so the affected repo (an *existing* one) would never have
  received it. Hence the `sync-from-framework.sh` patch, mirroring T-056's
  `.gitignore` patch precedent.
- **DD4 — Match on the PATH, not the whole line.** A consumer that deliberately
  chose a different driver for one of these files keeps its choice rather than
  getting a second, contradicting entry. Pinned by
  `test_a_consumers_own_variant_is_left_alone`.
- **DD5 — Append, never overwrite; create only when absent.** A consumer's own
  attributes must survive. The created-from-scratch file carries the
  local-only caveat in its header, so the honesty invariant travels with it
  (`test_created_file_states_the_local_only_caveat`).

## Spec corrected mid-lane (fix-spec-first)

The spec's Structure originally put the patch **inline** in
`sync-from-framework.sh`, mirroring T-056's `.gitignore` block. That was wrong on
this repo's own stated convention: `sync-from-framework.sh:439` says *"logic
lives in scripts/lib/migrate-data.sh so it is unit-testable"*. An inline block
cannot be tested without running the entire sync. The spec's `touches`,
Structure, Entities, and Operations were updated **before** the code moved, and
the logic now lives in `migrate_gitattributes_merge_union()` beside
`migrate_untrack_agent_runs()`, invoked from the same call site pattern.

## Gotchas

- **`MIGRATE_HELPER` is sourced once, ~280 lines above the new call site.** The
  T-155 block reuses that variable and re-guards on `[ -f "$MIGRATE_HELPER" ]`,
  so a checkout without the helper degrades to a no-op rather than an unbound
  function error.
- **This change is a mitigation and must never be described as a fix.** Union
  resolves local merges/rebases only; GitHub does not run merge drivers
  server-side, so a PR conflicting on these files still conflicts. The invariant
  is written into `.gitattributes`, the helper's docblock, the file it creates in
  a consumer, and `parallel-lanes.md`.
- **Nothing was written to any sibling repo.** `kaze-webapp` and `cqecho-app`
  were read for evidence only; the fix reaches them when they run their own
  updater.

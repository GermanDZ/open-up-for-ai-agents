# T-147 — Design Decisions

## DD1 — Two explicit file paths, not the `.claude/memory/` prefix

`ALWAYS_ALLOWED`'s three existing entries are all directory prefixes, so a prefix
would have read as more consistent. Chose files anyway: the framework writes exactly
two files there, while `.claude/memory/` is a *consumer-owned* directory a project may
also use for its own notes. A prefix would silently exempt those too — turning a
targeted fix for a non-opt-in surface into a blanket "`.claude/memory/` is unfenced"
policy nobody decided.

Made failable rather than asserted: `test_claude_memory_dir_is_not_blanket_exempt`
commits `.claude/memory/scratch-notes.md` and requires exit 8. Verified it bites —
temporarily widening the constant to the `.claude/memory/` prefix failed exactly that
test plus `test_allowed_lists_the_claude_memory_files` (which asserts the prefix is
*absent* from the resolved allowlist), and nothing else.

## DD2 — These files are class 2, not class 1 — and saying so changed the doc edit

The obvious edit to `parallel-lanes.md` was to add both files to the **class-1
lane-owned** row next to `docs/agent-logs/` and `docs/status-notes/`. That would have
been wrong. Class 1 is "one writer per file by construction" — those trees are
*sharded*, one file per lane, which is why they never conflict. These two are a
**single shared file every lane appends to**, which is exactly class 2 (append-only
set) — the class the document tells you to avoid, and which T-046 emptied by sharding
the run log into class 1.

They cannot be sharded from here: they are written by hooks and by
`openup-scribe.py learnings` into fixed paths in the *consumer's* checkout. So class 2
is re-populated involuntarily, and the doc now says so.

**The consequence matters for scope:** exempting them at the fence removes the false
`OUT OF LANE`, but it does **not** make them conflict-free. Two lanes appending to
`iteration-learnings.md` in parallel still collide at EOF on merge. That is a real
residual risk this task does not close — see DD3.

## DD3 — Deferred: `merge=union` for the two files (reserved as **T-155**)

`.gitattributes` already carries `docs/agent-logs/runs/*.jsonl merge=union` for exactly
this shape. The analogous entry for the two `.claude/memory/` files is *not* in this
lane because:

- it is a **merge-resolution** question, not a **lane-surface** one (this task's finding);
- it is **unexercisable here** — this repo gitignores `/.claude/*`, so no test in this
  repo can produce the collision, and the attribute would have to ship into consumer
  repos via the bootstrap to do anything;
- the existing `.gitattributes` comment already documents the load-bearing caveat —
  GitHub does not run merge drivers server-side, so `merge=union` fixes local
  rebases/merges only, not PR conflicts. So it is a partial mitigation at best, and
  deciding it deserves its own evidence.

Id **T-155** reserved. Roadmap entry to file at `/openup-complete-task` time (the
roadmap is a fenced shared view — a mid-lane edit trips the stale-view rule):

> ## T-155: `merge=union` for the two shared `.claude/memory/` append-only files
> **Status**: pending
> **Priority**: low
> **Value**: T-147 exempted `.claude/memory/bypass-log.md` and
> `iteration-learnings.md` from the write-fence, which stops the false `OUT OF LANE`
> but leaves them as genuine class-2 shared append-only files — two parallel lanes
> still collide at EOF on merge. `docs/agent-logs/runs/*.jsonl` already has the
> `merge=union` treatment for the identical shape. Decide whether consumer repos
> should ship the same attribute, knowing it only helps local merges (GitHub does not
> run merge drivers server-side), or whether the real answer is sharding these files
> the way T-046 sharded the run log.
> **Dependencies**: T-147
> **See**: `docs/changes/archive/T-147/design.md` DD2/DD3; `.gitattributes`

## DD4 — Premise verified downstream before any code was written

Per action item B2 (iteration-103 retrospective: two of five items promoted from a
retrospective turned out to have false premises), the finding was checked in the
environment where it reproduces — `/Users/germandz/personal-code/kaze/kaze-webapp`,
read-only — **before** drafting the spec:

| Check | Result (2026-07-27) |
|---|---|
| Both files tracked there? | yes — `bypass-log.md` 596 lines, `iteration-learnings.md` 279 lines |
| Same fence code? | yes — identical 3-entry `ALWAYS_ALLOWED` |
| Workaround in use? | **8 of 37 archived lanes** hand-declare `.claude/memory/*` in `touches` |
| Fence confirms? | `openup-fence.py allowed --task-id T-048` lists both paths — only because that lane declared them |
| Finding recorded? | `docs/framework-defects.md` §FD-003, observed on T-048 2026-07-26 |

The premise held. Recording the *method* as much as the result: this defect is
structurally invisible in the framework repo (`/.claude/*` is gitignored at
`.gitignore:38`), so "it doesn't reproduce locally" was never evidence against it.

Supporting signal found while measuring: `on-stop.py:54` already carries
`EXEMPT_DIRTY_PREFIXES = ("docs/agent-logs/runs/", ".claude/memory/bypass-log.md")` —
the framework already classifies this path as a lane-agnostic auto-written surface in
one component. T-147 closes an internal inconsistency, it does not invent a policy.
(`iteration-learnings.md` is *not* in that list; not this task's finding, and no
downstream evidence of it biting, so it was left alone.)

## DD5 — Test-count baseline: 845 → 849, not the "946" in the status notes

The full suite reports **848 passed, 1 skipped** here. Iteration 102's status note
cites a 946-green baseline, which looks like a regression and is not one:
`pytest scripts/tests/ --collect-only` returns **845 on `main`** and **849 in this
worktree** — a delta of exactly the 4 tests added here. The 946 figure counts a
different invocation (broader path and/or subtests expanded). Checked rather than
assumed, because "the number went down" is exactly the kind of thing that gets
hand-waved once and then cited as fact.

## DD6 — Bite check, both directions

Neither direction was assumed:

- **Remove** the two constant entries → `test_claude_memory_files_pass_without_being_claimed`
  and `test_allowed_lists_the_claude_memory_files` fail; 31 pass. **No pre-existing
  test fails**, which confirms the change is purely a widening — no previously-passing
  lane can start failing.
- **Widen** the constant to the `.claude/memory/` prefix →
  `test_claude_memory_dir_is_not_blanket_exempt` and
  `test_allowed_lists_the_claude_memory_files` fail; 31 pass.
- **Restored** → 33 pass.

The two guard tests (`test_other_claude_file_is_still_out_of_lane`,
`test_claude_memory_dir_is_not_blanket_exempt`) pass in the *removed* state by
construction — that is expected, since they assert what stays fenced. Their value is
in the widening direction, which is where they were shown to bite.

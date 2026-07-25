# T-131: Lane-hygiene fixes — id-allocator audit-tree scan (F2) + fence base_sha (F3)

**Phase**: construction
**Status**: pending
**Goal**: Close two correctness gaps found live during the T-127/T-128 measurement work: the task-id allocator can silently re-issue a live id, and the write-fence can falsely flag a second sequential lane on one branch for a prior lane's already-merged files.
**Priority**: high

---

## Context

`docs/explorations/2026-07-25-measurement-tooling-and-lane-hygiene.md` (F2, F3)
found both defects while doing unrelated measurement work, and its
product-manager pass explicitly ordered F2 ahead of any feature work because it
is data-loss-class, not a papercut: "Two lanes issued the same id is data loss
with a manual recovery (the T-024→T-030 renumber is the precedent already cited
in the create-task-spec skill)."

**F2 reconfirmed live twice more since the exploration was written**, during
this session's own T-129/T-130 quick tasks:
- After T-129 (quick track: no change folder, no roadmap row) was committed and
  merged, `python3 scripts/openup-claims.py next-id` still returned `T-129`.
- After T-130 (same shape) was committed and merged, both `next-id` **and**
  `reserve-id` (this task's own id allocation, see below) returned `T-129`
  again — a task id that had already been merged to `main` twice over.

Both times the workaround was manual: grep the git log for the id, confirm
it's taken, pick the next integer by hand. That workaround does not scale to
an unattended loop (`/openup-next`, `/openup-cycle`, the headless driver) —
none of them have a human in the loop to notice the collision before it's
committed.

F3 is a process-model mismatch rather than a bug in the strict sense: it never
fires under worktree-per-lane (the documented default, one lane per branch),
but it **always** fires when two lanes land sequentially on one branch —
exactly what happened this session, twice, once solo work resumed directly on
`main` after a merge. `openup-fence.py check --task-id T-128 --base
origin/main` reported three `OUT OF LANE` violations, all of them T-127's
already-merged, already-reviewed files — a false accusation that blocks
completion and offers no discoverable recovery path for an autonomous loop
(it would have to know T-127's completion sha, which nothing surfaces).

---

## Current State

### F2 — `used_seqs_in_repo()` (`scripts/openup-claims.py:476-509`)

```python
def used_seqs_in_repo(root: Path, prefix: str):
    """Every ID sequence number already used in the repo.

    Sources (union — an ID seen anywhere is taken):
      * ``docs/changes/*/plan.md`` + ``docs/changes/archive/*/plan.md``
        frontmatter ``id`` (the canonical spec location);
      * ``docs/roadmap.md`` full text (IDs exist there before any spec
        folder does — maintenance rows, backlog mentions);
      * ``origin/main:docs/roadmap.md`` when that ref exists locally
        (stale-checkout guard: an ID merged to trunk is taken even if this
        worktree hasn't rebased; pure local read, never fetches).
    """
    pat = _id_re(prefix)
    seqs = set()
    changes = root / "docs" / "changes"
    if changes.exists():
        for plan in changes.rglob("plan.md"):
            m = pat.fullmatch(parse_frontmatter(plan).get("id") or "")
            if m:
                seqs.add(int(m.group(1)))
    texts = []
    rm = root / "docs" / "roadmap.md"
    if rm.exists():
        try:
            texts.append(rm.read_text(encoding="utf-8"))
        except OSError:
            pass
    trunk_view = _git(["show", "origin/main:docs/roadmap.md"], cwd=root)
    if trunk_view:
        texts.append(trunk_view)
    for text in texts:
        for m in pat.finditer(text):
            seqs.add(int(m.group(1)))
    return seqs
```

None of its three sources cover a **quick-track** task: by design (`tracks.md`
— "state file + auto-log only, no plan gate") it creates no change folder and
is not required to add a roadmap row. Its only committed, repo-wide footprint
is a run-log shard (`docs/agent-logs/runs/<date>-<task>.jsonl`, one `task_id`
field per line) and a quick-tasks log line (gitignored — not usable). This
matches the T-125/T-126/T-129/T-130 pattern exactly: 0 roadmap hits, 0 change
folders, 1+ run-log shard each.

### F3 — `resolve_base()` (`scripts/openup-fence.py:98-104`)

```python
def resolve_base(explicit, cwd=None):
    """First ref that resolves among: --base, origin/main, main."""
    candidates = [explicit] if explicit else ["origin/main", "main"]
    for ref in candidates:
        if ref and _git(["rev-parse", "--verify", "--quiet", ref], cwd) is not None:
            return ref
    return None
```

Called from `cmd_check` (`scripts/openup-fence.py:189-214`) with only
`args.base` (the `--base` CLI flag) as input — it has no notion of where the
*current lane* actually started, so on a shared branch (main, after a prior
lane merged) it diffs against **current** `origin/main`/`main`, which now
includes every file the prior lane already landed.

### `openup-session.py cmd_begin` (`scripts/openup-session.py:90-214`)

Composes `claims.claim` (writes the claim file, `openup-claims.py:911-918`)
and `state.init` (writes `.openup/state.json`, `openup-state.py:330-350`) —
neither payload carries anything about the branch's starting point. The
docstring's own design rule is directly usable here: *"Git stays in the
skills. `begin` never creates a branch/worktree ... the skill creates the
worktree first, then calls `begin`"* — so by the time `cmd_begin` runs,
`git rev-parse HEAD` **is** the lane's base commit, whether that's a fresh
branch point or an in-place start on `main`. No new git plumbing is needed;
the value already exists at the exact moment `begin` runs.

---

## Proposed Design

### F2: scan lane-owned audit trees as additional id sources

**File**: `scripts/openup-claims.py`

```python
def used_seqs_in_repo(root: Path, prefix: str):
    """... (existing docstring, append a fourth source) ...

      * ``docs/agent-logs/runs/*.jsonl`` ``task_id`` fields (every lane on
        every track writes at least one shard — the one footprint a
        quick-track task cannot skip);
      * ``docs/status-notes/YYYY-MM-DD-<id>.md`` filenames (sharded
        completion notes, same coverage guarantee).
    """
    pat = _id_re(prefix)
    seqs = set()
    changes = root / "docs" / "changes"
    if changes.exists():
        for plan in changes.rglob("plan.md"):
            m = pat.fullmatch(parse_frontmatter(plan).get("id") or "")
            if m:
                seqs.add(int(m.group(1)))

    runs = root / "docs" / "agent-logs" / "runs"
    if runs.exists():
        for shard in runs.glob("*.jsonl"):
            try:
                lines = shard.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                m = pat.fullmatch(rec.get("task_id") or "")
                if m:
                    seqs.add(int(m.group(1)))

    notes = root / "docs" / "status-notes"
    if notes.exists():
        note_pat = re.compile(r"^\d{4}-\d{2}-\d{2}-(" + re.escape(prefix) + r"\d+)\.md$")
        for note in notes.glob("*.md"):
            m = note_pat.match(note.name)
            if m and pat.fullmatch(m.group(1)):
                seqs.add(int(pat.fullmatch(m.group(1)).group(1)))

    texts = []
    rm = root / "docs" / "roadmap.md"
    if rm.exists():
        try:
            texts.append(rm.read_text(encoding="utf-8"))
        except OSError:
            pass
    trunk_view = _git(["show", "origin/main:docs/roadmap.md"], cwd=root)
    if trunk_view:
        texts.append(trunk_view)
    for text in texts:
        for m in pat.finditer(text):
            seqs.add(int(m.group(1)))
    return seqs
```

`json` is already imported at module top (used elsewhere for claim payloads) —
verify before assuming. A malformed/partial shard line degrades silently (same
posture as `parse_frontmatter` on a corrupt plan) rather than raising, so a
half-written log never breaks id allocation.

**No change** to `reserved_seqs()` (live in-progress reservations) or the
union logic in `cmd_next_id`/`cmd_reserve_id` — only the *used* set grows a
scan source. Sequence numbers already reserved or already-used through the
existing three sources are unaffected; this only prevents *new* false
negatives on quick-track ids.

### F3: stamp `base_sha` at `begin`, prefer it in `resolve_base`

**File**: `scripts/openup-session.py` — `cmd_begin`, before the claim step:

```python
base_sha = _git(["rev-parse", "HEAD"], cwd=None)  # None on failure (non-repo/detached edge case)
```

Threaded into both writes:
- `claim_argv` gains `--base-sha` (new optional flag on `openup-claims.py
  claim`, stored in the claim payload alongside `branch`/`worktree`).
- `init_argv` gains `--base-sha` (new optional flag on `openup-state.py
  init`, stored in `state.json` alongside `branch`/`worktree`).

Both are additive optional fields — an existing claim/state file without
`base_sha` is read as `None`, identical to today's behavior.

**File**: `scripts/openup-fence.py`

```python
def resolve_base(explicit, cwd=None, stamped=None):
    """First ref that resolves among: --base, the lane's stamped base_sha, origin/main, main."""
    candidates = [explicit, stamped, "origin/main", "main"]
    for ref in candidates:
        if ref and _git(["rev-parse", "--verify", "--quiet", ref], cwd) is not None:
            return ref
    return None
```

`cmd_check` reads `.openup/state.json`'s `base_sha` (same file it already
opens for `task_id`/`track` via `resolve_task_id`/`resolve_track`) and passes
it as `stamped`. Precedence: an explicit `--base` flag (tests, manual
override) always wins; the lane's own stamped base is tried next — this is
what fixes the sequential-lane case; `origin/main`/`main` remain the fallback
for a lane with no stamped base (pre-existing state files, `--task-id`-only
invocations with no `.openup/state.json`).

`base_is_ancestor` and `changed_files` are unchanged — they already accept
whatever ref `resolve_base` returns.

---

## Acceptance Criteria

- [ ] `used_seqs_in_repo` includes a task id that exists **only** as a
      run-log shard `task_id` field (no change folder, no roadmap row)
- [ ] `used_seqs_in_repo` includes a task id that exists **only** as a
      `docs/status-notes/YYYY-MM-DD-<id>.md` filename
- [ ] `next-id`/`reserve-id` no longer re-offer an id already used by a
      quick-track task (regression test replays the live T-129 scenario:
      commit a quick-track task with only a run-log shard, then assert
      `next-id` skips it)
- [ ] A malformed run-log line or non-matching status-note filename is
      skipped, not raised
- [ ] `openup-session.py begin` stamps `base_sha` (= `git rev-parse HEAD`
      at call time) into both the claim file and `.openup/state.json`
- [ ] `openup-fence.py check` with no `--base` flag, run on a branch that
      has a second lane's commits on top of a first lane's already-merged
      commits, resolves to the stamped `base_sha` and reports **zero**
      `OUT OF LANE` violations for the first lane's files (regression test
      replays the live T-128-vs-T-127 scenario)
- [ ] An explicit `--base` flag still overrides the stamped value
      (back-compat: existing tests that pass `--base` explicitly keep passing
      unchanged)
- [ ] A pre-existing claim/state file with no `base_sha` key degrades to
      today's `origin/main`/`main` chain, not an error
- [ ] Full test suite green; `check-docs.py --changed-only` and
      `openup-fence.py check` clean at completion

---

## Success Measure

We expect the "manual id-collision workaround" episode (grep git log, confirm
taken, pick by hand) to occur **zero** times in future sessions, and the false
`OUT OF LANE` fence failure to occur **zero** times for a lane that starts
right after a prior lane merged on the same branch. Instrumentation: none
automated (both are rare, session-level correctness failures, not a metric
worth a dashboard) — read-back is "did it recur" at the next retrospective
covering this window.

---

## Testing Strategy

- **F2 unit tests** (`scripts/tests/test_openup_claims.py` or equivalent):
  run-log-only id is scanned; status-note-only id is scanned; malformed
  shard line / non-matching filename is skipped; existing three-source
  coverage is unchanged (no regression on `docs/changes` or roadmap scanning).
- **F2 regression test**: reproduce the live T-129 shape end-to-end — a
  fixture repo with one committed run-log shard for `T-005` and nothing else,
  assert `next-id` returns `T-006`, not `T-005`.
- **F3 unit tests** (`scripts/tests/test_openup_fence.py` or equivalent):
  `resolve_base` precedence order (explicit > stamped > origin/main > main);
  a state file with no `base_sha` falls through cleanly.
- **F3 regression test**: reproduce the live T-128-vs-T-127 shape — one
  branch, commit A (lane 1, "merged"), commit B (lane 2's own work), a
  `.openup/state.json` stamped with `base_sha` = commit A's sha; assert
  `openup-fence.py check` (no `--base`) reports zero violations for lane 1's
  files and still catches a genuine out-of-lane file lane 2 touches outside
  its own `touches:`.
- **`openup-session.py begin` test**: asserts the claim file and state.json
  both carry `base_sha` equal to `git rev-parse HEAD` at call time.

---

## Dependencies

None — both fixes are additive and self-contained within
`openup-claims.py` / `openup-fence.py` / `openup-session.py` / `openup-state.py`.

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-claims.py` | `used_seqs_in_repo` gains two scan sources (run-log shards, status-note filenames); `claim` payload + CLI gain optional `--base-sha` |
| `scripts/openup-state.py` | `init` payload + CLI gain optional `--base-sha` |
| `scripts/openup-session.py` | `cmd_begin` computes `base_sha` via `git rev-parse HEAD` and threads it into both `claim` and `init` calls |
| `scripts/openup-fence.py` | `resolve_base` gains a `stamped` parameter (from `.openup/state.json`'s `base_sha`), tried after `--base` and before `origin/main`/`main` |
| `scripts/tests/test_openup_claims.py` | +tests for the two new scan sources + the live-shape regression |
| `scripts/tests/test_openup_fence.py` | +tests for `resolve_base` precedence + the live-shape regression |
| `scripts/tests/test_openup_session.py` | +test asserting `base_sha` is stamped at `begin` |
| `docs-eng-process/script-cli-reference.md` | document the new `--base-sha` flags |

---

## Out of Scope

- Any change to `reserved_seqs()` or the live-reservation locking mechanism —
  this only widens the *used* scan, not the reservation protocol.
- Retrofitting `base_sha` onto already-completed/archived lanes — the fix is
  forward-looking; historical state/claim files are read as `base_sha: None`.
- A `openup-doctor` validator that cross-checks "ids present in run logs but
  absent from the allocator's sources" — the exploration's Open Questions
  raised this as a possible follow-up; it is a detection/reporting concern
  layered on top of this fix, not required to close the correctness gap
  itself.
- Any change to worktree-per-lane as the recommended default — F3 only
  matters for sequential same-branch lanes; the fix accommodates that case
  without changing the recommendation.

---

## Open Questions

1. Should the F2 fix also warn (via `openup-doctor`) when it finds an id in a
   run-log shard that never made it into a roadmap row or change folder —
   i.e. surface the quick-track task for later traceability, not just avoid
   re-issuing its id? **Assumed: no, out of scope for this task** — vetoable
   at review; tracked as a possible follow-up in the exploration itself
   (its own Open Questions section asks the same thing).
2. Is `git rev-parse HEAD` at `begin`-time always correct, or could a
   worktree-per-lane flow call `begin` after making the branch **and** an
   initial commit (making `HEAD` already past the true base)? **Assumed:
   no** — the docstring's existing design rule states the skill creates the
   worktree/branch first and calls `begin` immediately after, before any
   commit; verified against `openup-start-iteration`'s skill body for this
   session's plan. Vetoable if a real call site is found doing otherwise.

# T-151 — In-flight design decisions

## DD1. The task was re-specified mid-lane because both premises were false

T-151 was filed from iteration-98 retrospective action items A2 and A3. Measuring before
building showed both were wrong, so the spec was re-authored (fix-spec-first) before any
work — the lane writes **no code**.

| Premise | Measured | Verdict |
|---|---|---|
| A2 — completion double-increments the counter | `archive` increments once (`Retro cadence: 1`). The pack's step 7a already forbids a second increment — T-142, commit `177ee42`, merged as PR #93 **mid-session**. T-142 also ships `test_archive_advances_cadence` and `test_failed_archive_does_not_advance_cadence` | **obsolete** |
| A3 — the two `retro.json` stores disagree; `reset` reaches only one | After `reset`, authoritative store and `get` both read 0. Legacy `.openup/retro.json` seeds only when the authoritative file is absent; rewritten to 4, `get` still reported 100 | **wrong** |

## DD2. Why the false observation was still an accurate observation

The double-increment really did happen while completing T-140 — that lane executed a
`.claude/skills/` mirror rendered *before* PR #93 merged, and the stale copy still said to
run `retro increment`. The observation was right; the inference ("the framework
double-counts") was wrong, because the framework had already been fixed underneath the
running session.

`.claude/` is gitignored and only refreshed by `sync-templates-to-claude.sh`, so **any**
mid-session merge leaves the agent on the old procedure. This is the same class of trap as
T-140's DD5 and T-150's root cause, and it is now written into
`docs-eng-process/state-file.md` with the check to run first
(`render-skills-mirror.py --check`).

## DD3. A3 is struck through as *wrong*, not *done*

T-141's disposition rules allow `satisfied` / `obsolete` / `still open`. A retracted **false**
finding is none of those, so it is struck through with an explicit **WRONG — retracted**
label and the disproving measurement inline. Deleting it would destroy the record that makes
the original error auditable — the same reason the rules forbid deletion generally. A3's
row is the one a future reader most needs to find, because a plausible-sounding storage bug
is exactly the kind of claim that gets re-derived from scratch.

Corollary recorded for the next retrospective: the hand-zeroing of `.openup/retro.json`
performed while closing iteration 98 was unnecessary. It was harmless (the legacy file is
ignored while the authoritative one exists), but it was a write made on a wrong belief.

## DD4. Both decisions resolved as "keep the status quo" — and that is the deliverable

Neither 9.1 nor 77.2 changes code. That is not a non-answer: both items survived 89 and 21
iterations precisely because a decision has no artifact to grep for, so "we already do the
right thing" was indistinguishable from "nobody has looked". Writing the choice down, with
its rationale and an explicit revisit condition, is what closes them.

For 77.2 the revisit condition matters: iterations 87–98 *did* outrun the cadence on
`standard` lanes, which is real evidence against the status quo — but that streak was
counted by a number this very retrospective proved untrustworthy at the time. So the
decision is to keep the gate and re-evaluate if it is outrun again now that the count is
known good. A second occurrence would be clean evidence; the first was confounded.

## Completion verification (step 1a)

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Decision 9.1 recorded with rationale | ✅ | `docs-eng-process/state-file.md` §"Recorded decisions (T-151)" |
| 2 | Decision 77.2 recorded with revisit condition | ✅ | same section, revisit condition stated explicitly |
| 3 | A2 retracted as obsolete where published | ✅ | iteration-98 retrospective, A2 row struck through citing T-142 / `177ee42` |
| 4 | A3 retracted as **wrong** where published | ✅ | same file, A3 row struck through with the fixture measurement |
| 5 | No live document asserts either claim | ✅ | remaining greps are retraction text quoting the claim to refute it (roadmap T-151 entry, this spec) — none assert it |
| 6 | Stale-mirror trap recorded reusably | ✅ | `state-file.md` §"Diagnosing this counter — beware the pre-sync skill mirror" |

## Completion verification (step 1b) — Success-Measure instrumentation

✅ Instrumentation is a grep over this repo plus the presence of the two decisions in
`state-file.md`; both live where the read-back happens (the next retrospective's
disposition pass consumes exactly these rows). Open action items with a false premise:
2 → 0. Carried cadence-semantics decisions: 2 → 0.

**Read-back: the next retrospective.**

## Verification run

- `pytest scripts/tests/test_t011_retro.py` — **19 passed** (unchanged by this lane).
- Fixture: `archive` alone advances the counter by exactly **1**.
- No code touched: `git diff --stat` shows documentation only.

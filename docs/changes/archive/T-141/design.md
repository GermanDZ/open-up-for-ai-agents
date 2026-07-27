# T-141 — design notes

## Implementation verification against spec (complete-task step 1a)

Graded against `git diff 34e9520...HEAD` + the working tree, requirement by
requirement. The rendered artifact is
`docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md`; the
hand-edited source is `docs-eng-process/procedures/openup-retrospective.md`.

1. ✅ **A verification step exists and precedes authoring** — new
   `### 5b. Verify and Retire Carried Action Items — BLOCKING, before any new
   item is authored`. Position verified mechanically in the *rendered* skill:
   `grep -n '^### '` gives `5b` at line 85 and `### 6. Create Retrospective
   Document` at line 153, so the step is physically ahead of the authoring step,
   not a reminder inside it. The step's own opening paragraph states why it sits
   there.

2. ✅ **Collects from the durable trail** — point 1 directs the agent to read
   every prior file in `docs/iteration-retrospectives/` (newest first), take
   every not-yet-struck `## Action Items` row as open, and add any carried list
   in `docs/project-status.md`; with an explicit one-line exit for a project's
   first retrospective.

3. ✅ **Exactly three verdicts, each with a defined written form** — point 3 is a
   verdict table (`satisfied` / `obsolete` / `still open`) giving the exact
   annotation for each, followed by a worked example that rewrites a real row
   from `iteration-77-retrospective.md` in the struck format. Point 5 fixes the
   strike-through location as *the retrospective that authored the item*.

4. ✅ **Evidence mandatory and citable** — point 4 enumerates the four accepted
   kinds (commit SHA, existing artifact path, task id with an archived change
   folder, command + observed output), names three specific non-evidence
   phrasings, and states the fallback rule in bold: an item that cannot be cited
   **stays open**. The rationale is given — a false "satisfied" is worse than a
   stale item because it removes the thing that would have caught it.

5. ✅ **Nothing deleted; still-open items carry their original date** — point 5
   forbids deletion and explains the trail argument; point 6 requires the
   original authoring date on carried items so age is visible, and forbids
   authoring a new item in step 6 that duplicates a carried one (extend/re-date
   instead, since a duplicate resets apparent age).

6. ✅ **Document and project-status reflect the pass** — step 6's section list
   gains **Carried Action Items** (two tables: retired-this-cycle with evidence,
   and still-open with original dates; "None carried" is a legitimate entry,
   silence is not), and its **Action Items** bullet is now scoped to new items
   only. Step 7 gains an "ongoing means still open" paragraph restricting the
   project-status mirror to unretired items, plus a note distinguishing the
   hand-maintained action list from the `sync-status.py`-derived header and
   `## Notes`. The Output section reports the disposition counts.

7. ✅ **Open question carried, not resolved** — the step closes with a blockquote
   stating the pass lives in this skill today (the only skill that authors action
   items), naming the condition that would justify extraction (a second skill
   needing the same disposition pass over carried hand-written items), and saying
   plainly that a shared helper before that second caller would be abstraction
   ahead of demand.

**No ❌.** `gates.implementation_verified` set accordingly.

Deterministic guards, both green: `render-skills-mirror.py --check` (mirror in
sync with the pack) and `check-skills-guide.py --check` (guide in sync — the
guide renders the skill's front matter and Success Criteria, neither of which
this change touches, so it is a genuine no-op rather than a missed
regeneration). Full suite 777 green.

## Success-measure instrumentation (complete-task step 1b)

✅ **instrumentation pre-exists** and the baseline is recorded here so the
read-back is checkable rather than rhetorical. Counted at completion time by
extracting the rows under each `## Action Items` heading:

| File | Open items | Struck |
|---|---|---|
| `iteration-9-retrospective.md` | 3 | 0 |
| `iteration-20-retrospective.md` | 3 | 0 |
| `iteration-77-retrospective.md` | 5 | 0 |
| `iteration-86-retrospective.md` | 4 | 0 |
| `iteration-10-retrospective.md` | 0 (no Action Items table) | 0 |

Total carried backlog inherited by the next retrospective: **15 items, 0
retired**, across four files spanning iteration 9 to iteration 86 — the oldest
more than a year of iterations stale. That spread is itself the evidence for this
task: nothing has ever been retired, so the trail only grows.

The measure is read with `grep -c '~~' docs/iteration-retrospectives/*.md`
against those same files after the next `/openup-retrospective` run. Read-back:
that run — the retro counter stands at 3 of 5 after this branch's three lanes, so
within two more completions.

> The spec's original Success Measures section estimated this backlog at 7 items
> across the two newest retrospectives. The count above is the measured value
> (the two older retrospectives also carry unstruck tables, and `iteration-77`
> has 5 rows, not 3); the spec was corrected to match before completion rather
> than leaving the acceptance measure pointing at a wrong number.

## Decisions

- **DD1 — Position, not exhortation.** The pass is a numbered step ahead of the
  authoring step rather than a bullet inside it. The failure being fixed is
  precisely that nobody remembers to look back; a reminder in the same step that
  authors new items would reproduce it.
- **DD2 — Strike in the authoring document, not the newest one.** Each
  retrospective stays an accurate record of its own items' fate, and a reader
  arriving at an old retrospective from a link sees the resolution rather than a
  stale demand. The newest retrospective carries a summary of what it retired
  plus the items still open.
- **DD3 — No evidence ⇒ stays open.** Without this, the pass degrades into a
  rubber stamp on the first run where an item is *probably* done. Stated as a
  rule with its rationale, not as a preference.
- **DD4 — No automation, and the reason is structural.** The items have no id, no
  machine-readable due date, and no link to the artifact that would satisfy them,
  so nothing can be derived. Imposing that structure is a much larger change —
  and is exactly what the carried open question points at.

## Carried open question (unresolved by design)

**Does the disposition pass belong to this skill, or to a shared "carried items"
helper?** It is skill-local today because `/openup-retrospective` is the only
skill that authors action items. The trigger to extract it is a **second caller**
needing the same pass over carried, hand-written items — a phase review or a
handoff are the plausible candidates. Recorded on the step itself so the next
maintainer meets the question where the decision would be made, rather than only
in this archived folder.

## Gotchas

- **Do not dispose of the existing 7 items in this lane.** The first *run* of the
  new step is what disposes of them; doing it here would be the retrospective's
  work done in the wrong lane, and would consume the very baseline this task's
  success measure is counted against. Recorded as a "Do not touch" in the spec's
  Structure section and honoured.
- `check-skills-guide.py --write` reported "already up to date" for this change —
  the guide renders front matter and Success Criteria, not the Process section,
  so a Process-only edit is legitimately a no-op there. `--check` was run
  explicitly to confirm it, rather than assuming the no-op meant a missed step.

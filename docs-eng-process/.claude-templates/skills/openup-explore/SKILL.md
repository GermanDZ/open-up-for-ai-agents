---
name: openup-explore
description: Sanctioned pre-iteration mode — think through ideas, investigate problems, sketch options before committing to delivery
fit:
  great: [is this problem real?, comparing approaches before scoping, ruling out designs, evaluating external frameworks]
  ok: [reproducing an ambiguous bug before filing it, drafting RFC-style notes that may or may not lead to work]
  poor: [known small change (use /openup-quick-task), scoped delivery work (use /openup-start-iteration), running experiments that produce code intended to ship]
arguments:
  - name: slug
    description: Short kebab-case slug for the exploration topic (e.g. "openspec-borrow-analysis"). Used in the filename.
    required: true
  - name: append
    description: "If true, append to today's existing exploration file with this slug instead of creating a new one (default: false)"
    required: false
---

# Explore

Pre-iteration mode for thinking work that **may or may not** become delivery.
Closes the loophole the "all work must be in an iteration" rule otherwise
forces users to violate (investigating whether a problem is real, sketching
options, ruling out approaches).

**Exploration is not a deliverable.** It produces notes that may seed a
proposal, a roadmap entry, or be dropped outright.

## When to Use

- Investigating whether a problem is real before scoping a fix
- Comparing two or three approaches before picking one
- Reading an external framework / codebase and capturing what's worth borrowing
- Drafting an RFC-style argument that may not survive review

## When NOT to Use

- Known small change → `/openup-quick-task`
- Scoped delivery work → `/openup-start-iteration`
- Anything that produces code intended to ship (exploration code is throwaway)

## Process

### 1. Locate or Create the Exploration File

Path: `docs/explorations/YYYY-MM-DD-<slug>.md`.

- If `append: true` and the file exists → append a `## <timestamp>` section.
- Otherwise → create a new file with the template below.

### 2. Write Freeform Notes

No rubric. No structure beyond the required end-section. Capture:
- The question being explored
- Evidence, references, code paths, external links examined
- Options considered and what was ruled in / out
- Open questions for a future delivery iteration

### 3. Required End-Section: "Where this goes next"

Every exploration **must** end with one of these dispositions:

- `→ iteration` — promote to a roadmap entry. Name the entry and the
  proposed iteration scope in one sentence.
- `→ quick-task` — small enough for `/openup-quick-task`. Name the task in
  one sentence.
- `→ dropped` — not worth pursuing. State the reason in one sentence
  (rejection is a result; capturing the reason prevents re-litigation).

If you cannot pick one, the exploration is not complete. Either narrow the
question or split the file.

### 4. No Branch, No Team, No Commit Required

- Exploration may stay uncommitted on a working branch indefinitely.
- An optional `explore/<slug>` branch is fine if the notes are long-running.
- Do **not** deploy a team. Do **not** run rubrics. Do **not** open a PR.

## File Template

```markdown
# Exploration: <topic>

**Started:** YYYY-MM-DD
**Question:** <one-sentence framing of what we're trying to learn>

## Context

<why this is being explored now; links to related artifacts>

## Notes

<freeform>

## Options Considered

- **Option A** — <one-line>. Pro: …. Con: ….
- **Option B** — <one-line>. Pro: …. Con: ….

## Open Questions

- <questions a future delivery iteration would need to answer>

## Where this goes next

→ iteration | quick-task | dropped — <one-sentence justification>
```

## Success Criteria

- [ ] File exists at `docs/explorations/YYYY-MM-DD-<slug>.md`
- [ ] File ends with a "Where this goes next" section naming exactly one
      disposition: `→ iteration`, `→ quick-task`, or `→ dropped`
- [ ] If disposition is `→ iteration` or `→ quick-task`, the follow-up is
      named in one sentence
- [ ] If disposition is `→ dropped`, the reason is stated

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) — once a disposition
  is `→ iteration`, the follow-up enters the standard workflow here.
- [openup-quick-task](../../openup-quick-task/SKILL.md) — `→ quick-task`
  follow-ups go here.
- `docs/plans/` — explorations that mature into multi-task plans graduate to
  a plan document.

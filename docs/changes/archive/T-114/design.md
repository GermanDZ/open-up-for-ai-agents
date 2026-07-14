# T-114 — Design Notes

## Requirement grading at completion (step 1a)

- ✅ **Req 1** (`project-status.md` template) — `docs-eng-process/templates/project-status.md`
  created, fields `Project`/`Phase`/`Iteration`/`Iteration Goal`/`Status`/
  `Current Task`/`Started`/`Last Updated`/`Updated By` all present, unchanged
  in meaning from `openup-init.md`'s prior inline markdown.
- ✅ **Req 2** (`roadmap.md` template) — `docs-eng-process/templates/roadmap.md`
  created, same T-001/T-002 placeholder-row shape as the prior inline
  markdown.
- ✅ **Req 3** (`openup-init.md` copies all three) — §3 rewritten: Project
  Status and Roadmap subsections now `cp` from the new templates; a new
  Stakeholder Brief subsection `cp`s `input-request.md` into
  `docs/input-requests/`.
- ✅ **Req 4** (rendered output unchanged) — manual structural comparison: the
  two new templates are a verbatim lift of the fields `openup-init.md`
  already freehanded (same field names, same placeholder tokens, same
  ordering) — no field added, removed, or renamed.

All 4 requirements ✅. No blockers.

## Success-measure instrumentation grading at completion (step 1b)

Standard track, not `n/a`. Instrumentation named: a re-read of the next real
`/openup-init` bootstrap session's transcript for freehand-heredoc /
template-hunt tool-call patterns — the same method (transcript inspection)
used to find the original gap. ✅ instrumentation — pre-existing method
(session transcripts are always captured by Claude Code); no new logging
needed. The actual read-back (0 occurrences) is deferred to the next real
bootstrap run, as stated in the spec.

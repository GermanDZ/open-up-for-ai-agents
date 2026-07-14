# T-115 — Design Notes

## Requirement grading at completion (step 1a)

- ✅ **Req 1** (`--show-archetype-defaults` answers "absent" question) —
  `scripts/check-docs.py:main()` new flag short-circuits before any
  `docs_dir`/`schema`/`model` loading, prints `default_when_absent` stating
  no archetype tailoring applies, names `tracks.md` as the distinct axis,
  exits 0. Verified live (`test_exits_ok_with_no_docs_dir` runs it from
  `tempfile.gettempdir()` with no `docs/` present at all).
- ✅ **Req 2** (surfaces each archetype's resolved defaults) — the same JSON
  includes `archetypes` set directly to `PROCESS_ARCHETYPE_DEFAULTS` (no
  copy) — `test_archetypes_match_the_real_dict` asserts byte-for-byte
  equality against the real module dict, so it can never silently drift.
- ✅ **Req 3** (project-config.md / tracks.md disambiguate) — both docs edited
  at their first "quick" archetype/track mention, each naming the other file
  and the "different axis" distinction.
- ✅ **Req 4** (`openup-init.md` points at the accessor) — its "Project
  Config" §3 subsection's "framework defaults apply" line replaced with a
  pointer to `check-docs.py --show-archetype-defaults`.

All 4 requirements ✅. No blockers.

## Success-measure instrumentation grading at completion (step 1b)

Standard track, not `n/a`. Instrumentation named: a re-read of the next
session that needs this answer, counting tool calls to resolve it (the same
method used to find the original 4-call gap). ✅ instrumentation —
pre-existing method (session transcripts are always captured); no new
logging needed. Actual read-back (1 call vs. 4) deferred to the next real
occurrence, as stated in the spec.

## Test suite

`python3 -m unittest scripts.tests.test_check_docs -v` — 26/26 pass (23
pre-existing + 3 new `ArchetypeDefaultsCLITests`), zero pre-existing tests
modified or broken.

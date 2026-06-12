# T-016 — In-flight Design Decisions

Decisions made during implementation, beyond what the spec's `**Assumption:**` lines already record.

## DD1 — Resolves plan Open Question #3 (compact variants: verbatim vs pointer)

The plan left open whether the cold-start block goes verbatim into `*-compact.md`
or as a one-line pointer. **Chosen: one-line pointer.** Each compact gains a single
`**On start**: self-brief per the `## On Start, Read` block in
`.claude/teammates/<role>.md` — …` line after its `**Collaborates**` line. Rationale:
compacts already end with a "Full instructions: …" footer; duplicating the full block
would defeat the compaction and create a second place to drift. The pointer keeps the
list single-sourced in the full file.

## DD2 — Scribe given a real `## On Start, Read` section (single-file rule)

Rather than leave the scribe without the section, it gets an `## On Start, Read`
section whose body is the opposite instruction: *read only the target file, do not
self-brief.* This keeps the section heading uniform across all six roles (so every
compact can point to "the `## On Start, Read` block") while preserving the scribe's
deliberately narrow contract. The scribe is named as the explicit exception in
`CLAUDE.openup.md`.

## DD3 — Placement: new section before `## Role Definition`, "How You Work" step trimmed

The block sits immediately after the one-line role intro (before `## Role Definition`)
so it's the first thing a cold-starting agent reads. Each file's existing
"Before starting work" step in `## How You Work` is trimmed to a pointer
("self-brief per **On Start, Read** above") rather than deleted — avoids two divergent
reading lists per file while keeping the numbered process intact.

## DD4 — Role guideline lists reference only extant docs

Per the spec assumption, the third (role-varying) component lists only docs that exist
today; Ring 1 product artifacts (`docs/product/…`) are tagged "if present" since
`docs/product/` is unpopulated in this repo. No forward reference to T-018's
`docs/project-config.yaml`.

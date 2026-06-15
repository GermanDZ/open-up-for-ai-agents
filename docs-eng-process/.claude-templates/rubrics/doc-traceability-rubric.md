# Doc Traceability Rubric (cross-cutting, T-038)

Use this rubric to assess whether an authored work-product **instance** (a
file produced by one of the `openup-create-*` skills under a project's
`docs/`) carries the **instance frontmatter** that makes the work-product
trace web machine-checkable.

Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

This rubric is **referenced** from each `openup-create-*` skill's grading
step (one rubric, not six edits — the plan's "single cross-cutting" rule).
It is *additive* to each artifact's content rubric (vision-rubric,
use-case-rubric, etc.): a gap here does not waive a content criterion, and
satisfying a content criterion does not waive a trace one.

> **Applies only to work-product instances under `docs/`** — files whose
> first frontmatter line is `type:` set to one of the v1 spine types below.
> Template files (`type: Template`) and untyped narrative notes are not in
> scope. The single source of the field contract is
> [`docs-eng-process/doc-frontmatter.md`](../../doc-frontmatter.md) (T-034).

---

## 1. Instance `type` is declared
**Satisfied when:** Frontmatter carries `type:` set to one of the v1 spine
values:

```
vision · requirement · work-item · iteration-plan · use-case · test-case · decision
```

A missing or unknown `type` means `scripts/check-docs.py` skips the file
(template/note treatment) — the instance is invisible to the trace web. This
is criterion 0; without it none of the others apply.

## 2. Stable `id` is present and project-unique
**Satisfied when:** The instance has `id: <STABLE-ID>` (e.g. `VIS-001`,
`REQ-014`, `UC-007`, `TC-031`, `IP-2`, `D-04`), and no other instance under
`docs/` declares the same id. Other instances reference this id in their
trace fields — without it, traceability is impossible.

The id namespace is project-owned; the convention `<TYPE-PREFIX>-<N>` keeps
ids readable and grep-able but is not enforced.

## 3. `status` reflects the work-product lifecycle
**Satisfied when:** `status:` is one of `draft · approved · implemented ·
verified · obsolete` (the work-product **maturity** enum), and it accurately
reflects where the instance is. Distinct from the task-tier coordination
`status` enum (`proposed → ready → in-progress → done → verified`): the
former tracks *what the work product is*, the latter tracks *how a change
is being delivered*. Do not pick a status because it sounds right; pick the
one that matches the actual maturity.

## 4. Upstream trace (`traces-from`) cites the governing parent
**Satisfied when:** Every instance that has a defined upstream parent in
the OpenUP trace model carries a `traces-from: [<id>, …]` list naming the
parent ids. The valid `type → type` edges are the spine in
`scripts/trace-model.json` (T-035):

| This instance is a … | … traces-from |
|---|---|
| `requirement` | `vision` |
| `use-case` | `requirement` |
| `work-item` | `requirement` |
| `iteration-plan` | `work-item` |
| `test-case` | `requirement` or `use-case` |
| `decision` | `vision` |
| `vision` | _(no upstream; top of the spine)_ |

A `traces-from` entry pointing at an id whose type is not on this list is a
**❌**, not a free-form pointer; `check-docs.py` will flag it as
`bad-ref-type`.

## 5. Coverage (`verified-by`) is named where the type warrants it
**Satisfied when:** Instances whose coverage is required by
`trace-model.json` (currently `requirement`) carry a `verified-by: [<TC-id>,
…]` list naming the test-case instances that verify them. A `verified-by`
entry pointing at anything other than a `test-case` is a **❌**.

When the instance is still `draft` or `obsolete`, naming `verified-by` is
nice-to-have, not required (`check-docs.py --coverage` excludes those
statuses by design — a draft hasn't earned its tests yet, an obsolete one no
longer needs them).

## 6. `traced-by` is NOT hand-written
**Satisfied when:** No `traced-by:` field is present in the authored
instance. `traced-by` is the **derived inverse** of `traces-from` and is
owned by the index generator (`scripts/docs-index.py`, T-037). Writing it
by hand is a contract violation — the next generator run will overwrite it,
and the value will diverge from the index. The field is reserved in the
schema for the generator's exclusive use.

## 7. Optional metadata is consistent
**Satisfied when:** If `owner-role:` is present it names an OpenUP role
(`analyst`, `architect`, `developer`, `tester`, `project-manager`,
`product-manager`); if `iteration:` is present it matches the active phase
or a past one. These two are advisory — their omission is not a gap; their
**inconsistency** is.

## 8. Key naming uses hyphens, not underscores
**Satisfied when:** Trace keys are hyphenated (`traces-from`, `verified-by`,
`traced-by`, `owner-role`) — not underscored (`traces_from`, …). The
schema's `additionalProperties: false` catches typos as unknown-property
errors; this criterion is the human-readable counterpart.

---

## Grading Instructions

For each criterion above, write one of:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap]` — e.g. `"❌ Upstream trace — REQ-014
  declares no traces-from; the vision REQ-014 satisfies is VIS-001."`

After grading all criteria, output:

```
Doc Traceability Rubric: <N>/8 satisfied — <list of ❌ criteria or "all ✅">
```

A single ❌ blocks "done" for the instance unless the artifact's content
rubric explicitly declares the trace field non-applicable (which the v1
content rubrics do not). The mechanical floor is one validator run:

```bash
python3 scripts/check-docs.py                # schema + refs (T-036)
python3 scripts/check-docs.py --coverage     # + required coverage (T-037)
```

A green run is necessary but not sufficient — the validator does not grade
intent (criteria 3, 4, 7). A ✅ on every criterion here, plus a green
validator, is the joint floor.

---

## References

- [`docs-eng-process/doc-frontmatter.md`](../../doc-frontmatter.md) — the
  contract this rubric grades (field set, examples, "instance ≠ template
  provenance").
- [`scripts/docs-meta.schema.json`](../../../scripts/docs-meta.schema.json) —
  the schema `check-docs.py` enforces.
- [`scripts/trace-model.json`](../../../scripts/trace-model.json) — the
  KB-derived valid `type → type` edges and coverage rules.
- [`scripts/check-docs.py`](../../../scripts/check-docs.py) — validator
  (T-036) + `--coverage` (T-037).
- [`scripts/docs-index.py`](../../../scripts/docs-index.py) — the index
  generator that owns `traced-by` (T-037).

# Self-Critique SOP (Planning & Specification)

> Extracted from `agent-workflow.md` so the skills that apply it load only this
> SOP (~0.6k tokens) instead of the whole operating-procedures document.

**Applies to**: every skill that produces a **plan** or a **specification**
artifact — feature plans, iteration plans, task specs, use cases (and their
detailed scenarios), vision, shared vision, architecture notebooks, risk lists,
and test plans. Run it **after drafting the artifact and before the
completeness/rubric check**.

This is the adversarial counterpart to rubric conformance. The completeness
check asks *"are the required sections present?"*; the self-critique asks
*"is what they contain actually sound?"* A plan or spec is the cheapest place to
catch a flaw: a weakness caught here costs one redraft, while the same weakness
shipped downstream becomes implementation rework **plus** artifact drift. That
cost asymmetry is why this step is mandatory, not optional — and why "the rubric
passed" is never sufficient on its own.

## Procedure

1. **Adopt a hostile-reviewer stance.** Assume the draft is flawed and list
   every weak part you can find — including ones you are uncertain about;
   ranking comes later, coverage comes first. Do not defend the draft — attack it as the role most
   likely to reject it: the **analyst** for scope/intent, the **architect** for
   design soundness, the **tester** for verifiability.

2. **Surface load-bearing assumptions.** List every assumption the plan/spec
   depends on. For each, decide: is it stated explicitly in the artifact, or
   smuggled in silently? Silent assumptions must be promoted into the artifact's
   **Assumptions / Open Questions / Dependencies** so the next role inherits
   them, not discovers them.

3. **Failable-evidence check.** Every acceptance criterion, scenario, or success
   measure must be something that could actually *fail* — checkable against a
   test, a diff, or an observable outcome. Reject any criterion phrased as
   "review and approve", "looks correct", or otherwise unfalsifiable, and rewrite
   it into a checkable form.

4. **Resolve — don't note-and-move-on.** For each weakness found, either:
   - **Fix it** in the draft, or
   - **Flag it explicitly** in the artifact (Open Questions / Risks /
     Limitations) so it is inherited as a known gap. Routing a *blocking* gap to
     `/openup-request-input` counts as resolving it.

5. **Rank, then record the outcome** in the skill's run output: the top one or
   two weaknesses found and how each was resolved (fixed / flagged / routed).
   *"No weaknesses found"* is valid **only** after steps 1–3 were actually run.

## Relationship to other gates

- The **Ambiguity Gate** (in `plan-feature` / `create-task-spec`) runs *before*
  drafting — it prevents guessing at intent. The self-critique runs *after*
  drafting — it stresses the draft you produced. Complementary, not redundant.
- **Completeness / rubric grading** runs *after* the self-critique, so it grades
  an artifact whose known weaknesses have already been fixed or flagged.

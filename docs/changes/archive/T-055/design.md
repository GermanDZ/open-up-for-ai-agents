# T-055 — In-flight design decisions

## DD1 — Pillow bounded, not extracted (Assumption confirmed)
All of `requirements.txt` serves the optional converter tooling (`converter/`,
`scripts/convert.py`); the OpenUP workflow + hooks are stdlib-only. Chose the minimal
coherent fix: `Pillow>=12.0.0,<13` plus a comment stating the deps are converter-only.
Extracting into an optional extra was rejected as more churn for the same trust win.

## DD2 — `v2.0.0` tag points at the existing 2.0.0 release, which PREDATES this work
The annotated `v2.0.0` tag was cut **locally** (unpushed) at commit `4b1dbbb` — the
version-bump release merge whose `docs-eng-process/.template-version` reads `2.0.0`.
That commit does **not** contain the T-055 governance files (`LICENSE`, `SECURITY.md`)
because those are authored in T-055, after 2.0.0.

**Consequence / maintainer action:** the docs reference `v2.0.0` as the pinning example.
For a pinned release to actually carry `LICENSE`/`SECURITY.md`, the maintainer should,
**after T-055 merges to trunk**, cut the *next* tag (e.g. `v2.0.1`) on the merge commit
and push it — rather than moving `v2.0.0`. Pushing any tag is an outward-facing release
action and was intentionally deferred (Safeguard: create locally, maintainer pushes).

Net: "pinning is now *possible*" (linchpin) is satisfied by the local `v2.0.0`; the
governance files reach a pinned release at the next maintainer-cut tag.

## DD3 — Update scripts: `OPENUP_REF` > `OPENUP_BRANCH` > latest tag; never silent `main`
`resolve_ref()` in both `update-openup*.sh` resolves the clone ref in that precedence and
**errors** (rather than defaulting to `main`) when no tag exists and nothing is set.
`OPENUP_BRANCH=main` remains a documented, explicit, warned opt-in. Verified against the
local repo: no-env → `v2.0.0`, `OPENUP_REF` pins exactly, `OPENUP_BRANCH=main` warns.

## Verification run (tester box)
- Annotated `v2.0.0` → `4b1dbbb`, `.template-version` 2.0.0. ✓
- `LICENSE` (MIT) + `SECURITY.md` present; all 9 `settings.json.example` hooks enumerated
  in SECURITY.md with manual opt-out + disclosure channel + pinning guidance. ✓
- `requirements.txt`: `Pillow>=12.0.0,<13`, no lower-only-unbounded dep. ✓
- `updating.md`: recommended path clones a pinned tag + runs local; cron/GitHub-Actions
  examples de-piped; the only remaining `| bash` is the explicitly-flagged "not
  recommended" v2.0.0-pinned convenience. `README.md` pins submodule + license split. ✓
- Scripts default to pinned ref; no `:-main` default remains. ✓
- `check-docs.py` OK (0 instances); spec scenarios 6/6. ✓

## Step 1a — requirement grades (vs diff)
- ✅ R1 — annotated `v2.0.0` at `4b1dbbb` (`.template-version` 2.0.0); push deferred (DD2).
- ✅ R2 — root `LICENSE` (MIT) authored.
- ✅ R3 — `SECURITY.md`: all 9 hooks from `settings.json.example` enumerated (event·script·
  effect), local-execution disclosure, manual opt-out, disclosure channel + pinning guidance.
- ✅ R4 — `requirements.txt`: `Pillow>=12.0.0,<13`; four `==` pins unchanged.
- ✅ R5 — `updating.md` recommended path = clone pinned tag + run local; cron/Actions de-piped;
  only remaining `| bash` is the flagged "not recommended" v2.0.0 convenience. `README.md`
  pins submodule + license split + SECURITY.md pointer.
- ✅ R6 — both scripts: `resolve_ref` (OPENUP_REF > OPENUP_BRANCH > latest tag, never silent
  main); header shows clone-then-run. Verified resolution behavior.

## Step 1b — Success-Measure instrumentation
`n/a (argued)` — the measure is *external/manual* (track follow-on security-assessment
feedback + adoption notes; falsifiable bar = "evaluator answers yes to all five tranquility
questions from the shipped files"). There is no code event/metric/query to commit; the
measure is verified by re-assessment at read-back (2026-07-31 or next external assessment),
not by committed instrumentation.

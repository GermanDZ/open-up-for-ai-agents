---
id: T-055
title: Supply-chain & adoption-trust hardening (pin/release · clone-verify-run install · hook disclosure · LICENSE/SECURITY.md)
status: in-progress
priority: medium   # critical | high | medium | low
estimate: 1 session
plan: docs/explorations/2026-06-18-security-supply-chain-trust.md   # originating exploration (disposition "→ iteration", Options A+B+C)
depends-on: []
blocks: []
touches:
  - LICENSE
  - SECURITY.md
  - requirements.txt
  - README.md
  - docs-eng-process/updating.md
  - scripts/update-openup.sh
  - scripts/update-openup-simple.sh
last-synced: ""
---

# T-055 — Supply-chain & adoption-trust hardening

## Story

> **As a** security-conscious team evaluating OpenUP for a private repo
> **I want** an immutable version to pin to, an install/update path that does not pipe a
> remote script to my shell, a clear disclosure of what automation runs locally and how to
> opt out, a bounded dependency set, and the legal/disclosure basics (LICENSE, SECURITY.md)
> **So that** I can adopt OpenUP deliberately — answering "yes" to each trust question —
> instead of being asked to install-and-trust blindly.

INVEST check:
✅ Independent — governance files + docs + two install scripts + one dep pin; touches no workflow logic ·
✅ Negotiable — license id, exact dep bound, and whether to publish checksums are tunable ·
✅ Valuable — removes named adoption blockers (no license = legally unusable; pipe-to-bash; opaque hooks) ·
✅ Estimable — bounded edits to 7 files + one annotated tag ·
✅ Small — Options A+B+C only; signing/SBOM/CI scanning (Option D) explicitly excluded ·
✅ Testable — each acceptance maps to a checkable file/state assertion (see Requirements).

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Supply-chain / adoption trust for a framework that is **copied into** downstream
  user repos and **executes local automation** (Claude Code hooks) on tool/commit/prompt events.
  The trust surface is the install/update path + the hooks + the dependency set + the legal basics.
- **Evidence (verified in the exploration).** Both update scripts advertise `curl … | bash`
  and default to cloning `main`; `update-openup.sh` then runs a *second* downloaded script.
  `updating.md` repeats the pipe pattern inside **cron** examples (unattended weekly auto-pull
  of `main` — the sharpest vector). **No git tags exist**, so "pin to a version" is impossible
  today even though the framework is at 2.0.0. `requirements.txt` floats `Pillow>=12.0.0`
  (the lone unbounded dep). No root `LICENSE` (⇒ all-rights-reserved, a compliance blocker)
  and no `SECURITY.md`.
- **Scope boundaries.** Owner-confirmed: **MIT** license; scope **A+B+C, Option D deferred**.
  This task does **NOT** add release signing, SBOM generation, `pip-audit`/Dependabot, or
  pinned-by-SHA GitHub Actions (Option D — deferred until a concrete compliance demand appears).
  It does **NOT** change OpenUP workflow logic, hook behavior, or any `scripts/openup-*.py`.
  It does **NOT** restructure the dependency set into extras (a heavier refactor — see Approach).
- **Definition of done.** The five tranquility questions are all answerable "yes": (1) an
  immutable `v2.0.0` tag exists to pin to; (2) the documented install/update path clones a
  pinned tag and runs a *local* script (no pipe-to-bash as the recommended default; cron
  pipe-to-bash examples removed/flagged); (3) `SECURITY.md` discloses every hook + trigger +
  a documented manual opt-out; (4) every runtime dep is bounded; (5) root `LICENSE` (MIT) and
  `SECURITY.md` are present.

Non-blocking decisions, resolved by default (each vetoable at review):
> **Assumption:** Bound Pillow as `Pillow>=12.0.0,<13` rather than extracting it (and the
> other converter-only deps) into an optional extra. All of `requirements.txt` serves the
> optional `converter/` + `scripts/convert.py` tooling; the OpenUP workflow scripts are
> stdlib-only. Pinning is the minimal coherent fix; the extras refactor is more churn for the
> same trust win. *(Vetoable at review.)*
> **Assumption:** The hook-disclosure manifest lives **as a section in `SECURITY.md`** (one
> governance file) rather than a separate `HOOKS.md`. *(Vetoable at review.)*
> **Assumption:** Hardening v1 stops at **pin-to-a-tag + clone-don't-pipe**; we do **not**
> publish checksums/signatures (that is the B/D boundary, deferred with Option D). *(Vetoable.)*
> **Assumption:** The no-hooks settings variant is **not** shipped; instead `SECURITY.md`
> documents a manual opt-out, preserving process enforcement as the default (per the PM
> challenge pass). *(Vetoable at review.)*

## Requirements

1. An immutable release tag exists to pin to.
   - **Given** the framework is at version 2.0.0 on the trunk **When** the release tag is cut
     **Then** an **annotated** tag `v2.0.0` exists pointing at the trunk commit whose
     `docs-eng-process/.template-version` reads `2.0.0`, and pushing it is left to the
     maintainer (outward-facing release action — see Safeguards).
2. A root MIT `LICENSE` is present.
   - **Given** a fresh clone **When** a reviewer looks for licensing **Then** a root `LICENSE`
     file containing the standard MIT text with the correct copyright holder/year exists.
3. A root `SECURITY.md` is present and discloses the local automation.
   - **Given** a user evaluating what runs on their machine **When** they open `SECURITY.md`
     **Then** it enumerates every hook in `settings.json.example` (name · trigger event ·
     one-line description of what it does/writes), states that installing the template wires
     local code execution on tool/commit/prompt/stop events, and gives a **documented manual
     opt-out** (how to remove or disable specific hooks while keeping the docs/skills).
   - **Given** the same file **When** a reporter wants to disclose a vulnerability **Then**
     `SECURITY.md` states a disclosure channel and the supported-version / pinning guidance.
4. Every runtime dependency is bounded.
   - **Given** `requirements.txt` **When** it is inspected **Then** no dependency has an
     unbounded lower-only range; specifically `Pillow` reads `Pillow>=12.0.0,<13` (or a pinned
     `==`), and the four already-pinned deps are unchanged.
5. The documented install/update path does not pipe a remote script to a shell as the
   recommended default, and pins to a tag.
   - **Given** `docs-eng-process/updating.md` **When** a user follows the recommended update
     path **Then** it clones a **pinned tag** (not `main`) into a temp dir and runs a *local*
     script from that checkout — `curl … | bash` is either removed or explicitly labelled
     "convenience, not recommended", and the **cron** examples no longer pipe-to-bash an
     unattended pull of `main`.
   - **Given** `README.md` install/update guidance **When** read **Then** it recommends
     pinning (tag or submodule-at-tag) and does not present pipe-to-bash as the primary path.
6. The update scripts default to a pinned ref and support verification of what they run.
   - **Given** `scripts/update-openup.sh` / `update-openup-simple.sh` **When** run with no
     overrides **Then** they target a **pinned tag** by default (e.g. `OPENUP_REF` defaulting
     to the released tag) rather than `main`, and their header usage comment shows the
     clone-then-run (not pipe-to-bash) invocation. Behavior remains overridable via env var
     for users who knowingly want `main`.

## Behavior Delta

This is framework governance/tooling (process + distribution layer), not Ring-1 *product*
behavior of a consuming app. No `docs/product/` artifact changes.

**Added** — `LICENSE` (MIT); `SECURITY.md` (vuln-disclosure channel + hook-execution
disclosure + manual opt-out + pinning guidance). An upper bound on `Pillow`. A `v2.0.0`
annotated tag.

**Modified** — `updating.md` and `README.md` install/update guidance shift from
pipe-to-bash/clone-`main` to clone-a-pinned-tag-then-run-local; the two update scripts
default to a pinned ref instead of `main` and document clone-then-run usage.

**Removed** — the cron pipe-to-bash auto-pull-`main` examples in `updating.md` (or demoted
to an explicitly-flagged "not recommended" note).

## Success Measures

We expect **the share of OpenUP adoption rejections / hesitations attributable to the named
trust blockers** (no license, pipe-to-bash, opaque hooks, unpinned deps) to **drop toward
zero** for new evaluators. Instrumentation: track follow-on security-assessment feedback and
adoption notes; the falsifiable bar is "a security-conscious evaluator can answer 'yes' to all
five tranquility questions from the exploration using only the shipped files." Read-back:
2026-07-31 or the next external security assessment, whichever comes first.

## Entities

- **`LICENSE`** (new) — root MIT license.
- **`SECURITY.md`** (new) — root governance file: disclosure channel + hook manifest + opt-out + pinning guidance.
- **`requirements.txt`** (modified) — bound `Pillow`.
- **`docs-eng-process/updating.md`** (modified) — clone-a-pinned-tag update path; cron examples de-piped.
- **`README.md`** (modified) — install/update guidance recommends pinning, demotes pipe-to-bash.
- **`scripts/update-openup.sh`**, **`scripts/update-openup-simple.sh`** (modified) — default to a pinned ref; clone-then-run usage.
- **`settings.json.example`** (read-only, source of truth for the hook list) — `docs-eng-process/.claude-templates/settings.json.example`; enumerated by `SECURITY.md`, not edited here.
- **`v2.0.0` tag** (new, release action) — annotated tag at the 2.0.0 trunk commit; push deferred to maintainer.

## Approach

Pure governance + docs + small-config edits — no new executable logic. (1) Author `LICENSE`
(MIT, correct holder/year) and `SECURITY.md` (the hook manifest is generated by reading the
authoritative `settings.json.example`, so it cannot drift from a hand-invented list). (2) Add
the `<13` upper bound to `Pillow` in `requirements.txt`. (3) Rewrite the install/update
guidance in `updating.md` + `README.md` to a clone-a-pinned-tag-then-run-local pattern,
remove/flag the cron pipe-to-bash examples, and recommend the submodule-at-tag approach.
(4) Change the two update scripts to default to a pinned ref (new `OPENUP_REF`/`OPENUP_BRANCH`
default pointing at the released tag, still env-overridable) and update their header usage
comments to clone-then-run. (5) Cut the annotated `v2.0.0` tag locally; leave pushing to the
maintainer. The extras-refactor of `requirements.txt` and Option D (signing/SBOM/CI scanning)
are deliberately out of scope.

## Structure

**Add:**
- `LICENSE` — MIT.
- `SECURITY.md` — disclosure + hook manifest + opt-out + pinning guidance.

**Modify:**
- `requirements.txt` — `Pillow>=12.0.0,<13`.
- `docs-eng-process/updating.md` — pinned-tag clone-then-run; de-pipe cron examples.
- `README.md` — pinning-first install/update guidance.
- `scripts/update-openup.sh`, `scripts/update-openup-simple.sh` — default pinned ref + clone-then-run usage header.

**Do not touch:**
- Any `scripts/openup-*.py` workflow CLI, the hooks themselves, or `settings.json.example`'s
  hook wiring (SECURITY.md *documents* it; it is not changed here).
- `openup-knowledge-base/**`, `docs-eng-process/templates/**` — OpenUP layer, read-only per the standing guardrail.

## Operations

- [ ] (developer) Author root `LICENSE` (MIT, correct copyright holder + year).
- [ ] (developer) Author root `SECURITY.md`: vuln-disclosure channel; "what runs on your machine" hook manifest generated from `settings.json.example` (every hook · trigger · one-line effect); documented manual opt-out; pin-to-a-tag guidance.
- [ ] (developer) Bound `Pillow` in `requirements.txt` (`>=12.0.0,<13`); leave the four pinned deps unchanged.
- [ ] (developer) Rewrite `docs-eng-process/updating.md`: recommended update path clones a pinned tag and runs the local script; remove/flag the cron pipe-to-bash `main` examples; recommend submodule-at-tag.
- [ ] (developer) Update `README.md` install/update guidance: pinning-first; demote pipe-to-bash.
- [ ] (developer) Update `scripts/update-openup.sh` + `update-openup-simple.sh` to default to a pinned ref (env-overridable) and document clone-then-run in the usage header.
- [ ] (developer) Cut annotated tag `v2.0.0` at the trunk commit whose `.template-version` is 2.0.0; verify it resolves; leave the push to the maintainer (note it in the completion summary).
- [ ] (tester) Verify each Requirement's acceptance: tag resolves, LICENSE/SECURITY.md present + complete, `requirements.txt` bounded, no pipe-to-bash in the recommended docs path, scripts default to a pinned ref. Run any existing doc/skill validators that cover the touched files and confirm green.

## Rollout

**Flagged?** No. These are governance files, documentation, a dependency bound, and a release
tag — there is no runtime code path to toggle and no in-flight user state to protect. The
update-script default-ref change is behavior-affecting for the update flow but is the *safer*
default and remains env-overridable, so a flag would add ceremony without safety. Reach: the
new defaults apply to anyone who updates after this lands; existing installs are unaffected
until they choose to update. `n/a — no runtime flag; safer-default + docs only.`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, `[T-055]` trailer.
- SPDX / MIT canonical license text — use the standard wording verbatim (no bespoke license).
- Existing `scripts/*.sh` idioms — keep `set -e`, env-overridable config, the same UX/echo style.

## Safeguards

- **Reversibility.** Additive files (`LICENSE`, `SECURITY.md`) and reversible edits; the tag
  can be deleted before push. No data migration, no workflow-logic change.
- **Outward-facing action gating.** Pushing the `v2.0.0` tag is an irreversible public release
  action — **create it locally, do not push it without explicit maintainer confirmation.**
- **No-go zones.** Do not alter hook behavior or `settings.json.example` wiring (disclose, don't
  change). Do not touch `openup-knowledge-base/**` or `docs-eng-process/templates/**`. Do not
  weaken process enforcement by shipping a no-hooks settings variant (manual opt-out only).
- **Don't break the override.** The update scripts must keep an env-var escape hatch so a user
  who knowingly wants `main` (or a different ref) still can.
- **Scope discipline.** Option D (signing/SBOM/`pip-audit`/Dependabot/SHA-pinned Actions) is
  explicitly deferred — do not start it under this task.

## Verification

- `git tag` lists `v2.0.0`; `git rev-parse v2.0.0^{}` resolves to the trunk commit whose
  `docs-eng-process/.template-version` is `2.0.0`.
- Root `LICENSE` (MIT text) and `SECURITY.md` exist; `SECURITY.md` enumerates all hooks from
  `settings.json.example`, states the local-execution disclosure, gives a manual opt-out, and a
  disclosure channel + pinning guidance.
- `requirements.txt` has no unbounded dep; `Pillow>=12.0.0,<13`.
- `docs-eng-process/updating.md` recommended path clones a pinned tag + runs a local script; no
  cron pipe-to-bash `main` example remains unflagged. `README.md` recommends pinning first.
- `scripts/update-openup*.sh` default to a pinned ref (env-overridable) with clone-then-run usage.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-055/plan.md` exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

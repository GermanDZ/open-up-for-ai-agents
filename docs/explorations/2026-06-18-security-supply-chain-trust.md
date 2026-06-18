# Exploration: Security & supply-chain trust for OpenUP adoption

**Started:** 2026-06-18
**Question:** What is the smallest set of changes that lets a security-conscious team adopt OpenUP in a private repo *without* having to "install-and-trust blindly" — and which of the reported risks are real vs. perceived?

## Context

A user ran a private-use security assessment and reported:

1. **curl | bash + clone-from-`main`** — `scripts/update-openup.sh` and
   `scripts/update-openup-simple.sh` document `curl -s …/main/scripts/… | bash`
   and default to cloning `main`. No version pinning, no integrity check.
2. **Installed automation executes locally** — the `.claude-templates/settings.json.example`
   wires 9 hook scripts across `PreToolUse` / `PostToolUse` / `Stop` / `UserPromptSubmit`.
   Once installed they run Python on Bash/Edit/Write/commit/plan-exit/prompt events.
3. **Deps not fully pinned + no SECURITY.md/license** — `requirements.txt` pins 4 of 5
   (`Pillow>=12.0.0` is a floating lower bound); no root `LICENSE` or `SECURITY.md`.

Verdict in the feedback: "reasonable but not install-and-trust-blindly." The asks were
all reasonable hardening, not a rejection. Goal here is to size each fix and decide a
disposition — these are trust/onboarding problems, so the payoff is adoption confidence.

## Notes — evidence (each claim verified against the repo)

### Claim 1 — curl|bash + clone main: CONFIRMED, and broader than stated
- `scripts/update-openup.sh:3` and `update-openup-simple.sh:3` both advertise
  `curl -s …/main/scripts/update-openup.sh | bash` as the headline usage.
- Both default `BRANCH="${OPENUP_BRANCH:-main}"` and `git clone --depth 1 --branch main`
  (update-openup.sh:13,31; simple:12,25). No tag, no commit, no checksum.
- `update-openup.sh:46` then **executes a second downloaded script**
  (`bash "$TEMP_DIR/scripts/update-from-template.sh"`) — so the trust surface is the
  whole cloned tree, not just the one piped script.
- `docs-eng-process/updating.md` repeats the pipe pattern at lines 404, 482, 498
  — including inside **cron examples** (`0 0 * * 0 … | bash`), i.e. unattended,
  unpinned, auto-pulling `main` weekly. That cron pattern is the sharpest risk:
  a compromised or force-pushed `main` lands in the user's repo with no human in the loop.
- **No git tags exist** (`git tag` empty) even though the framework is versioned to
  `2.0.0` (recent commit `0d432b3` bumps `.template-version`). So today a user *cannot*
  pin to a release even if they want to — the tag they'd pin to doesn't exist.

### Claim 2 — installed hooks execute locally: CONFIRMED, by design, but under-disclosed
- `settings.json.example` registers (verified present in `.claude/scripts/hooks/`):
  `check-iteration.py`, `validate-commit.py` (PreToolUse:Bash);
  `gate-edits.py` (PreToolUse:Edit|Write|NotebookEdit);
  `on-branch-created.py`, `auto-log-commit.py` (PostToolUse:Bash);
  `on-plan-exit.py` (PostToolUse:ExitPlanMode); `on-stop.py` (Stop);
  `on-task-request.py`, `check-unfinished-tasks.py` (UserPromptSubmit).
- This is **inherent to what OpenUP is** — process enforcement via hooks. It is not a
  bug; the issue is *disclosure and reviewability*, not the mechanism. A user installing
  the template is opting into local code execution on nearly every agent event and is not
  told so prominently, nor handed a review checklist.
- `defaultMode: "acceptEdits"` in the example lowers the friction further — fewer prompts,
  so more trust placed in the installed automation by default.

### Claim 3 — pinning + governance files: CONFIRMED
- `requirements.txt:5` `Pillow>=12.0.0` — only floating dep; the other 4 are `==`.
  Pillow is the canonical example of a library with a steady stream of CVEs, so an
  unbounded upper range is the worst single dep to leave floating.
- No root `LICENSE` and no `SECURITY.md` (confirmed absent). Without a license the repo
  is "all rights reserved" by default — a real blocker for corporate/compliance adoption,
  independent of the security framing. No `SECURITY.md` means no disclosure channel.

## What "tranquility" actually requires (reframing)

The feedback's own remediation list is the spec: *pin to a tag/commit, avoid pipe-to-bash,
review settings + hooks before enabling, mirror internally, run your own scans.* Three of
those five are things **we** can make easy; two are things the **adopter** does but that we
can document and tool. So the deliverable is "make the safe path the documented default,"
not "lock anything down."

Concretely, tranquility = a user can answer yes to:
- Can I pin to an immutable version? (needs: tags/releases exist)
- Can I install/update without piping a remote script to a shell? (needs: clone-verify-run, or submodule)
- Can I see exactly what code will run on my machine and when? (needs: a hooks manifest / SECURITY.md disclosure)
- Is the dependency set bounded and scannable? (needs: full pinning + a documented scan step)
- Are the legal/disclosure basics present? (needs: LICENSE + SECURITY.md)

## Options Considered

### A. Minimal governance + pinning (cheapest, highest trust-per-effort)
Add root `LICENSE`, `SECURITY.md`, pin `Pillow` to a bounded range
(`Pillow>=12.0.0,<13`), and **cut release tags** (`v2.0.0` on the current commit) so
pinning is *possible*. Update `updating.md` to recommend pinning to a tag.
- Pro: Each item is hours, not days. Tags unblock every other pinning recommendation.
  LICENSE removes the single biggest *compliance* blocker. No behavior change to the
  framework itself.
- Con: Doesn't remove the pipe-to-bash pattern; only makes the pinned alternative real.

### B. Replace pipe-to-bash with clone-verify-run + submodule-first docs
Rewrite the documented install/update to: clone a **pinned tag**, optionally verify a
published checksum/signature, *then* run the local script — never `curl | bash`. Promote
the existing git-submodule approach (README:116) as the recommended default and demote the
pipe one-liner (or keep it behind an explicit "convenience, not recommended" label). Remove
or re-flag the **cron pipe-to-bash** examples in `updating.md` — unattended auto-pull of
`main` is the one pattern to actively discourage.
- Pro: Directly answers the headline complaint; the cron change kills the highest-severity
  vector. Submodule gives pinning + auditable diffs for free.
- Con: More docs churn; the convenience of the one-liner is what some users like. Checksum
  publishing adds a release step to maintain.

### C. Hook transparency: a manifest + review gate at install
Ship a `HOOKS.md` (or a section in `SECURITY.md`) that enumerates every hook, its trigger,
and what it does/writes — and have the first-time install **print the list and what will run**
rather than silently wiring `settings.json`. Optionally split the example into a
"minimal/no-hooks" and "full" variant so a cautious user can adopt the docs/skills without
the event-driven automation.
- Pro: Turns "opaque automation" into "disclosed, opt-in automation" — the exact gap in
  claim 2. Low code cost (mostly docs + one print statement).
- Con: A no-hooks variant weakens process enforcement (the whole point of OpenUP); needs a
  clear "you lose X" note so users choose knowingly.

### D. Full supply-chain program (SLSA/signing/SBOM/Dependabot/pip-audit in CI)
Cosign-signed releases, generated SBOM, `pip-audit`/Dependabot in CI, pinned GitHub Actions
by SHA, etc.
- Pro: Gold standard; "install-and-trust" becomes defensible.
- Con: Heavy for a solo-maintained framework; most of the trust win is captured by A+B+C at
  a fraction of the cost. Premature.

## Recommendation

Do **A + B + C** as one security-hardening initiative; defer **D**. They're complementary:
A makes pinning *possible*, B makes the safe install the *default*, C makes the local
automation *disclosed*. Together they let a cautious team say yes to every "tranquility"
question above. The single highest-value atom is **cutting a `v2.0.0` tag** — without it,
every "pin to a version" recommendation is hollow.

## Resolved by owner (2026-06-18)

- **License: MIT** — owner's call. Permissive, matches a framework meant to be copied into
  user repos; patent-grant of Apache-2.0 judged unnecessary. Root `LICENSE` = MIT.
- **Scope: A + B + C, defer D** — owner confirmed the recommendation. Signing/SBOM/CI
  scanning is out of the first pass.

## Open Questions (remaining)
- Do we publish checksums/signatures at release, or is "pin to a tag + clone, don't pipe"
  enough for v1 of the hardening? (Signing is the B/D boundary.)
- Should the no-hooks "minimal" settings variant ship, or just a documented manual opt-out?
  (Affects how much process enforcement we're willing to make optional.)
- Is `Pillow` even needed at runtime for the core flow, or only for an optional
  image/screenshot path? If optional, move it to an extra rather than the base
  `requirements.txt` — removes the floating dep from every install.

### Product-manager challenge pass

(Role hat per `.claude/teammates/product-manager.md` — value-ordering and "what changes for
which user, and how would we notice?" lens. No team deployed.)

- **Pushback:**
  - *Option D (full SLSA/signing/SBOM)* — rejected for now. The value case is thin for a
    solo-maintained framework with no evidence of an actual threat actor; it would degrade
    into release-time ritual (regenerating SBOMs nobody reads). We'd notice it mattered if
    an adopter said "we can't proceed without signed releases" — none has. **Disposition:
    rejected — deferred until a concrete compliance demand appears.**
  - *A no-hooks settings variant (part of C)* — partial pushback. Shipping a variant that
    disables the hooks risks users silently running OpenUP-without-the-process and then
    reporting "it doesn't enforce anything." The value (cautious adoption) is real but the
    failure mode is real too. **Disposition: accepted in narrowed form — disclose +
    document a manual opt-out, do NOT ship a parallel maintained no-hooks file** (folded
    into the refined C below).

- **Complement (what the assessment missed):**
  - **No tags exist** — the assessment said "pin to a commit/tag," but the repo offers no
    tag to pin to. That prerequisite is invisible in the feedback and is the linchpin;
    surfaced into Option A and the recommendation.
  - **The cron pipe-to-bash examples** (`updating.md:482,498`) are worse than the
    interactive one-liner — unattended auto-pull of `main`. The assessment lumped all
    curl|bash together; the cron case deserves its own "remove/discourage" call-out.
    Folded into Option B.
  - **The license gap is a compliance blocker independent of security** — without it the
    code is all-rights-reserved and a corporate adopter legally can't use it. Higher
    adoption value than the security items; folded into Option A as a first-class item.

- **Refine:**
  - Sharpen the goal from "be more secure" (unfalsifiable) to the **five yes/no tranquility
    questions** above — each is a checkable acceptance criterion for the follow-up iteration.
  - Narrow C from "make hooks optional" to "make hooks **disclosed and reviewable**, with a
    documented manual opt-out" — preserves process enforcement as the default while removing
    the opacity that was the actual complaint.
  - Sequence the work so **tag-cutting lands first** (it unblocks B's pinning docs).

- Disposition per challenge: D **rejected** (deferred, no demand); no-hooks-variant
  **rejected**, replaced by disclosure + manual opt-out (**accepted, narrowed**); three
  complements (**accepted** into Options A/B); refinements (**accepted** as the iteration's
  acceptance criteria).

## Where this goes next

→ iteration — Promote a **"Supply-chain & adoption-trust hardening"** roadmap entry scoped
to Options A+B+C (owner-confirmed; D deferred): cut a `v2.0.0` release tag; add root
`LICENSE` (**MIT**, owner-decided) and `SECURITY.md`; bound `Pillow` (`>=12.0.0,<13`) or move it to an optional
extra; rewrite install/update docs to clone-a-pinned-tag (submodule-first) and remove/flag
the cron pipe-to-bash examples; and ship a hooks-disclosure manifest (`SECURITY.md` section
or `HOOKS.md`) enumerating every hook + a documented manual opt-out. Acceptance = the five
tranquility yes/no questions all answerable "yes." Defer Option D (signing/SBOM/CI scanning)
until a concrete compliance demand appears.

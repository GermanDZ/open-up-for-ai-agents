# T-153 — In-flight design decisions

## DD1. The gap was narrower than the roadmap entry, and sharper

The iteration-86 action item asked for three things. Two already had real coverage:
`sync-from-framework` detection (`test_sync_from_framework_detection.py`, 3 tests over real
consumer fixtures) and the tracked bypass-log dirty-stop (`test_t006_hooks.py`). Verified
before building, per the T-151 lesson.

The genuine gap is not any of the three sub-items: **no test ran the installer at all.**
Every existing test starts from a hand-built fixture asserting what its author *believed*
the installer produces. That is precisely how T-110 (consumer shipped with no self-updater)
and T-150 (settings referencing hook scripts not yet on disk) both reached downstream repos.

## DD2. Usability assertions, not a file inventory

"Every `process-manifest.txt` entry is present" would restate the manifest and fail on every
legitimate addition — the way a smoke check becomes noise and then gets deleted. The four
properties asserted instead are stable under additions and are what actually make a consumer
work: the CLIs run, the self-updater exists, the hook wiring is guarded, and the consumer
cannot be mistaken for its own upstream.

## DD3. Module-scoped fixture

The installer is the slow part (~3s); every assertion inspects the same immutable result.
Module scope keeps the whole file at ~3.5s, inside the runtime budget, without any test
mutating what another reads.

## DD4. The test was verified to bite

A smoke check that passes unconditionally is worse than none — it reports safety it does not
provide. Stripping the T-150 guard from the shipped template and re-running produced exactly
one failure, `test_every_consumer_hook_command_is_guarded`, with the other six still green;
restoring returned all seven to green. So the assertion discriminates, and it discriminates
on the specific property rather than collapsing the whole file.

## Completion verification (step 1a)

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Installs via the real installer | ✅ | `test_bootstrap_produces_a_project`; fixture asserts rc 0 and the project dir |
| 2 | CLIs shipped and runnable | ✅ | `test_consumer_receives_executable_openup_clis` (stable core, not the manifest) |
| 3 | Self-updater shipped | ✅ | `test_consumer_receives_its_own_self_updater` (T-110) |
| 4 | Hook wiring guarded | ✅ | `test_every_consumer_hook_command_is_guarded`; **negative check**: stripping the guard fails exactly this test |
| 5 | Not misdetectable as the framework | ✅ | `test_consumer_does_not_carry_the_framework_marker` (T-126) |
| 6 | Hermetic and offline | ✅ | `bootstrap-project.sh` makes no network call (`grep -cE 'curl|wget|git clone'` → 0); all writes land in `tmp_path`; `test_install_leaves_the_framework_repo_untouched` |

7 passed in ~3.5s.

## Completion verification (step 1b) — Success-Measure instrumentation

✅ The instrument **is** the test: it fails the suite when a bootstrapped consumer comes out
unusable, which is exactly the event being counted. **Read-back environment: this repo** —
the suite runs here and its result is read here (satisfying T-152's new criterion-12 element).

**Read-back: the next retrospective.** Expectation: zero consumer-only breakages reaching a
downstream repo across the next 3 changes touching the install path or `.claude-templates/`,
against a baseline of at least 2 known (T-110, T-150).

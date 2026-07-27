# T-134 — design notes

## Live probe result (2026-07-26, gpt-5.4-nano, real endpoint)

```json
{
  "exit_code": 0,
  "marker_in_source": true,
  "exec_confirmed": true,
  "independent_rerun_ok": true,
  "iterations": 3,
  "fixture": null
}
```

Driver log (turn-by-turn):

```
[openup-agent] model turn 1/20
[openup-agent] write_file probe/hello.rb
[openup-agent] model turn 2/20
[openup-agent] exec: ruby probe/hello.rb
[openup-agent] model turn 3/20
[openup-agent] procedure complete on iteration 3; gates clean
OPENUP-TASK: DONE
```

**Clean pass.** The model wrote `probe/hello.rb`, called `exec` with
`ruby probe/hello.rb` exactly once, confirmed the marker
(`OPENUP-CODE-PROBE-OK`) itself before finishing, and an independent re-run
of the produced file after the sub-run reproduced the same marker — the
defense-in-depth check the spec named against a model that fakes success.

**Against T-106/T-107's reliability bar (zero mid-run restarts, ≤6 turns):**
this run took exactly 3 turns (the minimum possible for the two-tool-call
contract: write, exec, done) with zero restarts — the happy path, first try,
no retry needed. This is a single run, not a 5-run batch like T-107's — the
spec's Acceptance Criteria called for one live run to answer the falsifiable
question, not a full statistical batch (this is a narrow probe, not a
production gate).

## Disposition

**The hypothesis holds for this narrow case**: `gpt-5.4-nano`, through the
driver's existing tool surface plus one new allowlisted `exec` command,
reliably writes *and executes* a single small, self-contained piece of code,
at the same reliability bar the markdown-authoring path measured. This is
exactly the one data point the exploration (`docs/explorations/2026-07-26-driver-construction-code-authoring.md`)
said was missing before any larger investment.

**What this does NOT show** (named explicitly so this result isn't
overclaimed):
- Nothing about **multi-file** work — this task writes exactly one file.
  A Rails skeleton needs 15-30+.
- Nothing about **package-manager-mediated** execution (`bundle install`,
  `bin/rails db:create`) — `ruby <path>.rb` needs no dependencies; Rails
  fundamentally does.
- Nothing about **reliability over a much longer horizon** — 3 turns is a
  tiny fraction of what a real Construction session would need.
- A **single run** is not a statistical claim — T-106/T-107's actual
  reliability numbers came from a 5-run batch. Nothing here rules out that a
  second or third run would need a retry-on-failure cycle (the system prompt
  explicitly allows one, and this run simply didn't need it).

**Recommended next step, if the owner wants to continue toward the full
PoC**: this result supports moving to Option C (staged: a foundation
iteration covering multi-file task-def shape + a reviewed, wider `exec`
allowlist, THEN a ShareShed-specific PoC iteration) with somewhat more
confidence than before — but the gap between "one file, no dependencies" and
"a working Rails 8 + Postgres app" is still the entire open question Option C
was scoped to answer, not something this probe closes.

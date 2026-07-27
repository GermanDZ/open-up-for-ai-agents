# T-152 — In-flight design decisions

## DD1. The gap was one of *standpoint*, not rigour

T-052's measure was not vague. It named a concrete instrument
(`.claude/memory/bypass-log.md`) and a concrete date. It failed because the instrument was
named for **two downstream repos** while the check that approved it ran **in the framework
repo**, where the question "does this exist?" has a different answer. Criterion 12 and step
1b both evaluated existence from wherever the completing agent happened to be standing.

So the fix is not "be more specific" — the measure already was. It is to make *where the
number will be read* an explicit element, and to bind the existence check to that place.

## DD2. No validator script

Criterion 12 is graded prose, like every other criterion. A parser for "does this sentence
name an environment" would be brittle (any phrasing counts) and would still need the human
judgment it claimed to replace — the real question is not whether an environment is *named*
but whether the instrument exists *there*, which no parser can answer. Enforcement stays the
rubric plus the blocking step 1b.

## DD3. Rejected alternatives

- **Forbid measures about downstream behaviour.** That bans exactly the measures worth
  making for a framework whose whole point is distribution.
- **Ship instrumentation downstream with every such task.** Right in principle, far outside
  this task, and often impossible — a consumer decides what it tracks.

## DD4. The rule is "state it", not "justify it"

The common case is that the read-back happens in this repo, and there one clause suffices:
*"Read-back environment: this repo."* Making that a paragraph would be ceremony that earns
nothing. The cost is only real when the answer is *somewhere else* — which is precisely the
case that used to slip through.

## Applying the new rule to existing specs

Sampling the 48 archived specs that carry a non-`n/a` measure: **none** names a read-back
environment, so all 48 would gap on the new criterion. That is expected and is **not**
retroactive debt — the element did not exist when they were written, and criterion 12 grades
a spec at authoring time. The rule applies to measures authored from now on. Two specs
already satisfy it because they were written after the failure was understood: **T-150**
("The instrumentation lives in this repo, which is where the read-back happens") and this
one.

## Completion verification (step 1a)

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Measure names its read-back environment | ✅ | Criterion 12 lists "the **read-back environment**" as a required element and "**no named read-back environment**" as a gap |
| 2 | Instrument absent from that environment is a gap | ✅ | Criterion 12 gap list: "**instrumentation that exists somewhere other than the read-back environment**" |
| 3 | Completion verifies existence *there* | ✅ | Step 1b now reads "exists **in the measure's named read-back environment** — not merely somewhere", and states that "it exists in this repo" does not satisfy a downstream expectation |
| 4 | Authoring skill instructs it | ✅ | `openup-create-task-spec.md` template gains a `Read-back environment:` line plus the "state it, not justify it" guidance |
| 5 | Both rubric copies identical | ✅ | `diff -q` → identical; `check-claude-sync.sh` green |
| 6 | Illustrated by the case that produced it | ✅ | T-052 cited concretely in both the criterion and step 1b |

**Discrimination check (R1/R2 bite):** across archived specs with a real measure, 48/48 lack
a read-back environment and 0/48 have one — so the criterion distinguishes, rather than
passing everything by construction.

## Completion verification (step 1b) — this task's own measure

✅ Instrumentation is the **Measure Read-Back table** that `/openup-retrospective` step 4b
already produces, with its `can't tell` verdict reserved for exactly this failure mode.
**Read-back environment: this repo** — retrospectives are authored here, so the instrument
and its reader are in the same place. This spec therefore satisfies the rule it introduces.

**Read-back: the second retrospective after this lands.** Falsified if any measure authored
after this change appears as `can't tell — instrumentation missing`.

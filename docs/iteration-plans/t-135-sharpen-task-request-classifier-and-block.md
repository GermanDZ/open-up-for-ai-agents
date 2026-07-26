# T-135: Sharpen on-task-request.py's classifier, then block at prompt time

**Phase**: construction
**Status**: pending
**Goal**: Close the "no prompt-time gate" finding from this session — but only after the task-request classifier is precise enough that blocking doesn't reject genuine questions/discussion.
**Priority**: medium

---

## Context

This session's own "what are we missing to have the harness follow the process" discussion found that `on-task-request.py` (`UserPromptSubmit`) is deliberately advisory-only — it never blocks (`CLAUDE.openup.md`: "Hooks gate at commit, not at prompt"). Verified this session (via the `claude-code-guide` agent): `UserPromptSubmit` hooks genuinely *can* block — `sys.exit(2)` already does this in the sibling hook `check-unfinished-tasks.py`, in this same repo, today.

But the current classifier (`TASK_ID_RE` / `TASK_LANG_RE`) matches a task-id or a verb like "implement"/"fix"/"build" **anywhere in the message** — fine for an advisory nudge, wrong for a hard gate. Verified false positives from this very session's transcript: "What do you need for T-107?" (matches `TASK_ID_RE`) and "Try nano and run the batch" would both need to NOT block, since they're a question and a benchmark-run request respectively, not delivery-work directives. Blocking on the unmodified classifier would reject legitimate discussion — directly undermining the "explore freely" design T-057 established.

Owner decision (this session): sharpen the classifier first, verified against real false-positive/true-positive examples, **then** switch the hook to genuine blocking.

---

## Current State

### `on-task-request.py`'s classifier (`docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py:32-48, 138-141`)

```python
TASK_ID_RE = re.compile(r"\bT-\d+[a-z]?\b", re.IGNORECASE)

TASK_LANG_RE = re.compile(
    r"\b("
    r"continue\s+with|work\s+on|start\s+(?:task|working|implementing|on)|"
    r"implement|let'?s\s+(?:work|start|implement|build|fix)|"
    r"pick\s+up|resume|proceed\s+with|"
    r"build\s+(the|a|this)|fix\s+(?:the|a|this)|"
    r"add\s+(the|a|this)\s+(?:feature|functionality)|"
    r"develop|complete\s+(?:the|task)"
    r")\b",
    re.IGNORECASE,
)
...
task_id_match = TASK_ID_RE.search(prompt)
has_task_lang = bool(TASK_LANG_RE.search(prompt))

if not task_id_match and not has_task_lang:
    sys.exit(0)
```

Both patterns use `.search()` over the **whole message**, unbounded — a task id or verb mentioned once anywhere triggers the classifier, regardless of sentence position or surrounding punctuation.

### The always-advisory exit (`on-task-request.py:159, 176`)

```python
sys.exit(0)  # advisory only — never block the user's prompt
```

Both branches (no active iteration / iteration active) end this way.

### The sibling hook's working blocking precedent (`check-unfinished-tasks.py:195-213`)

```python
print(
    f"[check-unfinished-tasks] ⚠️  Unfinished work detected — starting a new iteration is blocked.\n\n"
    f"Current state:\n\n{issues_text}\n\n"
    f"Recommended actions:\n\n"
    ...,
    file=sys.stderr,
)
sys.exit(2)
```

Confirmed this session (via `claude-code-guide`): for `UserPromptSubmit`, exit code 2 blocks the prompt from reaching the model entirely, feeding stderr back as the reason — this is a real, already-used mechanism in this repo, not a hypothetical.

### Verified this session: background task-notifications never reach `UserPromptSubmit`

Confirmed via `claude-code-guide`: task-notification delivery is a separate `Notification` hook event; `UserPromptSubmit` only fires on genuine human-typed prompts. No defensive handling needed against notification content.

### No existing test file for `on-task-request.py`

`scripts/tests/test_t006_hooks.py` establishes the repo's hook-testing convention (drive the hook as a subprocess with a JSON stdin payload, assert exit code + stderr) — reusable pattern, no test file currently exists for this specific hook.

---

## Proposed Design

### 1. Question-exclusion — the single highest-leverage precision fix

**File**: `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`

```python
# A message ending in a question mark is discussion/inquiry, never a
# directive to start delivery work — even when it names a task id or
# contains task-language words. Verified false positive this session:
# "What do you need for T-107?" must not block.
_QUESTION_RE = re.compile(r"\?\s*$")
```

Applied before any other check: `if _QUESTION_RE.search(prompt.strip()): sys.exit(0)`.

### 2. Position-bounded matching — imperative mood, not keyword presence

```python
# Task-language verbs must appear near the START of the message (imperative
# mood: "Implement X", "Let's fix Y") — not anywhere in a longer message
# that happens to use the word in passing. Verified this session: "Try nano
# and run the batch" (a benchmark request, correctly NOT classified as a
# delivery-work directive by the unchanged verb list) must stay unblocked;
# tightening position bounds doesn't change that outcome, it prevents FUTURE
# messages using these verbs in passing from over-triggering.
_LEAD_WORDS = 8

def _leading_words(prompt: str, n: int = _LEAD_WORDS) -> str:
    return " ".join(prompt.strip().split()[:n])
```

`has_task_lang` becomes `bool(TASK_LANG_RE.search(_leading_words(prompt)))`.

### 3. Bare task-id mentions require a short, non-interrogative message

```python
# A task id alone (no task-language verb) only counts as a directive when
# the message is short — "T-107", "continue T-107" — not when it appears
# once inside a longer analytical or discussion message.
_BARE_ID_MAX_WORDS = 8
```

```python
task_id_match = TASK_ID_RE.search(prompt)
has_task_lang = bool(TASK_LANG_RE.search(_leading_words(prompt)))
bare_id_is_short = bool(task_id_match) and len(prompt.split()) <= _BARE_ID_MAX_WORDS

if not (has_task_lang or bare_id_is_short):
    sys.exit(0)
```

(Replaces the current `if not task_id_match and not has_task_lang:` line.)

### 4. Switch to genuine blocking, matching the sibling hook's exit(2) convention

Both current `sys.exit(0)  # advisory only — never block the user's prompt` lines (the no-active-iteration branch) become `sys.exit(2)` with the existing message text unchanged (it already tells Claude exactly what to run). The active-iteration reminder branch **stays exit(0)** — it's a continuation nudge, not a violation, and blocking it would be pure friction with no missing precondition to fix.

---

## Acceptance Criteria

- [ ] `_QUESTION_RE` excludes any prompt ending in `?` from classification, regardless of task-id/verb content
- [ ] `TASK_LANG_RE` is checked only against the leading `_LEAD_WORDS` words of the prompt
- [ ] A bare task-id mention only classifies as a request when the full prompt is `<= _BARE_ID_MAX_WORDS` words
- [ ] The no-active-iteration branch exits 2 (blocks); the active-iteration reminder branch still exits 0 (does not block)
- [ ] Regression suite passes using this session's real transcript as ground truth (see Testing Strategy) — every verified false positive from this session's transcript is excluded; every verified genuine directive from this session's transcript still classifies as a request
- [ ] `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py` and its mirror in `.claude/scripts/hooks/` are kept in sync via the existing `sync-templates-to-claude.sh` mechanism (no new sync machinery needed)

---

## Success Measures

We expect zero reports of a legitimate question or discussion prompt being
rejected by this gate within the first several sessions after this ships —
the failure mode this task exists to prevent. Instrumentation: the hook's
own stderr message is distinctive (`[on-task-request]`) and would appear in
any blocked-prompt report; no additional logging is added since a hook that
blocks incorrectly is immediately, visibly disruptive (the opposite of a
silent failure that needs instrumentation to notice). Read-back: the next
time the owner reports (or doesn't report) a false-positive block —
owner-initiated, no fixed date, matching this repo's existing
conditional-trigger convention for spike/hardening work.

---

## Testing Strategy

- Unit: `_QUESTION_RE`/`_leading_words`/the combined classification function
  directly, using **real quotes from this session's transcript** as
  regression fixtures:
  - Must NOT classify as a request: `"What do you need for T-107?"`,
    `"What's official openapi endpoint?"`, `"Why pausing for human? that
    should run autonomously"`, `"What are we missing to have the harness
    follow the openup process (or any process)?"`
  - Must classify as a request (unchanged from today): `"implement T-107"`,
    `"fix the login bug"`, `"let's build this feature"`, `"continue with
    T-042"`
  - Documented as an explicit, accepted **out-of-scope gap, not a
    regression**: `"Try nano and run the batch"` does not classify either
    before or after this change (no task-language verb in the list matches
    "run"; expanding recall is separate scope from this task's precision
    fix)
- Integration: drive the hook as a subprocess with a JSON stdin payload
  (the `test_t006_hooks.py` convention) — assert exit code 2 + stderr
  content for a genuine no-iteration task request; assert exit code 0 for
  every false-positive fixture above
- Regression: existing behavior for the active-iteration reminder branch
  (still exit 0) is unchanged — add one test asserting this explicitly

---

## Dependencies

- None (additive change to an existing hook; no other task depends on this)

---

## Key Files

| File | Change |
|------|--------|
| `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py` | Sharper classifier + switch no-iteration branch to `sys.exit(2)` |
| `scripts/tests/test_on_task_request_hook.py` | New — regression suite using real transcript fixtures |

---

## Out of Scope

- Improving the classifier's **recall** (catching more true positives, e.g. `"run the batch"`-style requests with no listed verb) — this task is about precision (fewer false positives under blocking), not casting a wider net
- Any change to `check-unfinished-tasks.py` (already blocks correctly; used only as a precedent)
- Any change to the `active-iteration` reminder branch's blocking behavior (stays advisory)
- Resolving whether Stop-hook-relayed feedback text could ever reach `UserPromptSubmit` — verified this session that background task-**notifications** don't, but Stop-hook re-prompt text specifically wasn't checked; recorded as Open Question 2, not solved here since neither observed Stop-hook message in this session contained a trigger phrase

---

## Open Questions

1. **Are `_LEAD_WORDS = 8` and `_BARE_ID_MAX_WORDS = 8` the right thresholds?**
   Chosen to comfortably cover genuine imperative openers ("Let's implement
   T-107 now" = 5 words) while excluding longer discussion. **Assumed: 8,
   vetoable at review** against real future false positives/negatives.
2. **Could a Stop-hook-triggered re-prompt (the harness feeding a blocked
   Stop hook's stderr back as a new turn) ever route through
   `UserPromptSubmit` and get misclassified?** Not verified this session
   (only background task-notifications were checked, and confirmed
   separate). **Assumed low-risk and not solved here** — no observed
   Stop-hook message this session contained a trigger phrase, but flagged
   for the next person who touches this hook to verify if it becomes a
   real incident.
3. **Should the "sharpen, then block" split into two separate delivered
   tasks instead of one?** The owner's phrasing ("sharpen classifier first,
   then block") could mean either a sequencing *within* one task or two
   separate ones. **Assumed: one task, sequenced internally as Requirements
   1-3 (sharpen) then Requirement 4 (block)** — vetoable at review; simple
   enough to keep together, and blocking with no sharpening in between
   would leave the repo in a half-fixed state if a session ended between
   two separate tasks.

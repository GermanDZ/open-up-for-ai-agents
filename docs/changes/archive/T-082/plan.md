---
id: T-082
title: Driver LLM client — handle slow-response timeout instead of crashing
status: done
priority: high
plan: docs/changes/archive/T-072/plan.md
depends-on: [T-072]
blocks: []
touches:
  - scripts/openup_agent/llm.py
  - scripts/openup_agent/loop.py
  - scripts/tests/test_openup_agent.py
  - docs-eng-process/reference-driver.md
  - docs/changes/
last-synced: ""
---

# T-082 — Driver LLM client: handle the slow-response timeout

## Story

> **As** someone driving the reference driver against a **local** model
> **I want** a slow LLM response to surface as a clean, retryable endpoint-error
> (and the per-call timeout to be generous + configurable)
> **So that** a long generation doesn't **crash the whole run** with an uncaught
> `TimeoutError` (exit 1) — the bug the T-080 benchmark caught (run 3 of the
> 20260713-150411 batch: `TimeoutError: timed out` during `getresponse()`).

## Context

`llm.chat_completion` sets a **120s** per-call socket timeout but only catches
`urllib.error.HTTPError` / `URLError`. A socket timeout during `getresponse()`
raises a bare **`TimeoutError`** (a subclass of `OSError`, NOT of `URLError`), so
it escapes `LLMError`, the loop's `except llm.LLMError` misses it, and the driver
crashes with exit 1 (`outcome=error`). On a slow local model this recurs, and 120s
is too short for long generations.

## Requirements

1. **A slow/failed transport becomes a clean `LLMError`.** `llm.chat_completion`
   catches `TimeoutError`/`OSError` (after the specific `HTTPError`/`URLError`
   cases) and raises `LLMError`, so the loop returns a clean endpoint-error (exit 3)
   — never an uncaught crash (exit 1).
   - **Given** the socket read raises `TimeoutError` **When** `chat_completion`
     runs **Then** it raises `LLMError` (not `TimeoutError`), and the loop returns 3.
2. **The per-call timeout is generous and configurable.** The default rises to
   **600s**; `loop.run` reads `OPENUP_AGENT_TIMEOUT` (seconds) and passes it to
   `chat_completion`.
   - **Given** `OPENUP_AGENT_TIMEOUT=42` **When** the loop makes a call **Then**
     `chat_completion` is invoked with `timeout=42`.

## Operations

- [x] In `scripts/openup_agent/llm.py`: default `timeout=600`; add
  `except (TimeoutError, OSError) as e: raise LLMError("transport failure … timed out")`
  after the HTTPError/URLError handlers. In `scripts/openup_agent/loop.py`: resolve
  `OPENUP_AGENT_TIMEOUT` (default 600) and pass it into the `complete()` call.
  Document the env var in `reference-driver.md`. Add tests: timeout→LLMError→exit 3,
  and the env→timeout plumb-through. Run driver+bench suites + fence.

## Verification

- A run whose LLM call times out records `outcome=endpoint-error` (exit 3), not
  `error` (exit 1).
- `OPENUP_AGENT_TIMEOUT` overrides the per-call timeout; default is 600s.
- Driver + bench tests green; `openup-fence.py check --base harness-optional` green.

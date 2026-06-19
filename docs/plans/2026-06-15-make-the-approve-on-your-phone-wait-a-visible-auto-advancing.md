# Make the "approve on your phone" wait a visible, auto-advancing session state

## Context

When syncing Revolut, the workflow pauses for the user to approve a push
notification in the Revolut mobile app. Today that moment is invisible in the
admin UI: the `approve_2fa` phase emits a single `note` log line
("⏳ Revolut sent a notification…") and then a **silent** `wait_url` that blocks
up to 300s, surfacing only anonymous `.` dots in the black log-tail box. The
operator has no clear, structured indication that the system is waiting on
*them* — exactly the complaint reported.

The system already has a complete, working pipeline for structured operator
interactions — it's how ING's SMS/SCA prompts surface as interactive cards:

```
runner → RemotePromptStore (writes <run_dir>/prompts/<id>.request.json)
       → freentonic GET /runs/{id}/prompts        (invoke_server.rb)
       → simplefreen proxy /admin/api/.../prompts  (admin_api.rb)
       → UI pollPrompts() → buildPromptCard()       (ui/app.js)
```

The UI already renders `input` cards (SMS field) and `confirm` cards ("I
approved" button), auto-opens VNC when a prompt appears, and shows an expiry
countdown. **Revolut's phone-approval is the one interactive moment that
bypasses this pipeline.** The fix is to route it through the pipeline that
already works — adding a new prompt kind `await` for "waiting on an external
action that resolves itself" (the browser URL flips when the phone approval
propagates), so the card **auto-advances and clears on its own** with a manual
"continue" button only as a fallback.

Scope (confirmed with user): fix the waiting state only, with auto-advance. The
broader "promote the whole card into a phase-by-phase status panel" vision is a
separate, larger effort and is **out of scope** here.

## Design

Introduce a third prompt kind, `await`, alongside `input` and `confirm`. It
behaves like `confirm` (no value to collect) but the runner races the operator's
optional click against a self-resolving condition (URL change) and withdraws the
prompt the instant either fires. This keeps existing `input`/`confirm` behavior
(ING) completely untouched while giving Revolut a distinct "waiting, continues
automatically" card.

## Changes

### freentonic repo (`/Users/germandz/personal-code/freentonic`)

1. **`lib/freentonic/remote_prompt_store.rb` — add a self-resolving condition.**
   - `prompt(...)` gains an optional `until_satisfied:` keyword (a callable).
   - `poll_for_response` returns the parsed response when the operator POSTs, OR
     a `:satisfied` sentinel when `until_satisfied.call` becomes true. Throttle
     the `until_satisfied` check to ~every 1.5–2s (track last-check via `@clock`)
     while keeping the response-file poll at the existing `POLL_INTERVAL_SECONDS`
     (0.25s) so a manual click stays snappy. The `until_satisfied` callable is
     supplied by the runner and is the *only* place CDP is touched — the store
     stays transport-agnostic.
   - On `:satisfied`, still call `mark_done` (removes the `.request.json` → the
     UI card clears on its next poll). Map `kind: :await` to a `true` return,
     same as `:confirm`.

2. **`lib/freentonic/browser_workflow_runner.rb` — new `await_external_approval`
   action.** Add a `when "await_external_approval"` dispatch (near the existing
   `wait_url`/`note` cases ~line 77–103) and a handler method modeled on the
   existing `run_sca_prompt` (line 508) + `wait_for_url` (line 262):
   - Resolve `message`, `url_includes`, `timeout` (default 300).
   - Short-circuit: if `current_url_value` already includes the target, log and
     return (handles the "already logged in / remembered approval" path).
   - TTY branch (`stdin_is_tty?`) and the no-`remote_prompt_store` branch fall
     back to the existing `wait_for_url(includes, timeout:)` — preserves local-dev
     behavior unchanged.
   - Remote branch: call `store.prompt(kind: :await, message:, mask: false,
     timeout_seconds: timeout, until_satisfied: -> { current_url_value.include?(expected) })`.
     After it returns (operator clicked OR URL flipped), if the URL hasn't
     settled yet, do a short grace `wait_for_url(includes, timeout: …)` so a
     premature click still waits for the redirect. On `RemotePromptStore::Timeout`,
     do one final URL check before raising `UserError`.

3. **`lib/freentonic/invoke_server.rb` — accept `await` on submit.** In
   `handle_submit_prompt` (line 738 `case request_payload["kind"]`), add a
   `when "await"` branch that behaves like `confirm` (sets `confirmed => true`).
   `handle_list_prompts` already forwards `kind` verbatim (line 688), so no GET
   change is needed.

### simplefreen repo (`/Users/germandz/personal-code/simplefreen`)

4. **`lib/simplefreen/admin_api.rb` — allow `await` through the submit proxy.**
   In `handle_run_prompt_submit`, extend the allowlist at line 683 from
   `["input", "confirm"]` to include `"await"`. The GET proxy
   (`handle_run_prompts`, line 664) already forwards the list verbatim.

5. **`lib/simplefreen/ui/app.js` — render the `await` card.** In
   `buildPromptCard` (line 1737), add an `await` branch (mirroring the `confirm`
   branch at line 1775) that renders a **waiting** card:
   - Distinct title (e.g. "Waiting for your approval") instead of the
     `input`/`confirm` "Workflow paused — input needed", plus a spinner/pulse and
     the `message` ("Approve the sign-in in the Revolut app — this continues
     automatically once approved").
   - A secondary, de-emphasized fallback button ("Already approved? Continue")
     that calls the existing `submitPromptAnswer({... body: { kind: "await" }})`.
   - Keep the existing `expires_at` countdown.
   No changes needed to `pollPrompts`/`submitPromptAnswer` — the auto-advance
   works because the runner withdraws the request, so the next poll empties the
   host (the `!prompts.length` path at line 1716 already clears the card).

### freentonic-providers repo (`/Users/germandz/personal-code/freentonic-providers`)

6. **`revolut/workflow.yml` — swap the passive wait for the new action.**
   Replace the `note` + `wait_url` steps (lines 64–68) in the `approve_2fa` phase
   with a single:
   ```yaml
   - action: await_external_approval
     message: "Approve the sign-in in the Revolut app on your phone — this continues automatically once approved."
     url_includes: "app.revolut.com/"
     timeout: 300
   ```
   Update the surrounding comment (lines 48–63) to describe the new structured
   waiting state.

## Why a new `await` kind instead of reusing `confirm`

ING's SCA `confirm` genuinely requires the operator to click after approving;
it does **not** auto-advance. Reusing `confirm` for Revolut would either force an
unnecessary click or require muddying the shared confirm card's copy to imply
auto-advance — misleading for ING. A dedicated `await` kind keeps both paths
correct and gives Revolut the visually-distinct "waiting…" treatment the user
asked for. The extra wire cost is tiny: one `when` branch (invoke_server), one
allowlist entry (admin_api), one UI branch (app.js).

## Verification

- **Unit (freentonic):** run the existing suite (e.g. `bundle exec rake test` /
  `ruby -Itest test/...` per repo convention). Add/extend a `RemotePromptStore`
  test asserting: (a) `until_satisfied` returning true resolves to `:satisfied`,
  removes the request file, and returns `true`; (b) a posted response still wins
  if it lands first; (c) `until_satisfied` is throttled (not called every 0.25s).
- **End-to-end (manual):** trigger a Revolut "Sync now" from the admin UI with
  VNC enabled. Confirm the **`await` card** appears in the Running panel as soon
  as the passcode submits, that approving on the phone makes the card **clear by
  itself** (no click) and the run proceeds to `post_login`, and that the manual
  "Continue" fallback also works. Confirm an **ING** sync still shows its normal
  SMS/SCA cards unchanged.
- **Regression:** verify the local-dev TTY path (running the workflow from a
  terminal) still prints the note and waits via dots (the `wait_url` fallback).

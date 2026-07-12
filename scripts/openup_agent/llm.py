"""OpenAI-compatible chat-completions client for the reference driver (T-072).

Stdlib-only (urllib). Works against any endpoint that speaks the OpenAI
`/v1/chat/completions` contract — OpenAI, Anthropic-via-proxy, or a local server
such as LM Studio / Ollama / vLLM (owner runs LM Studio; config via LLM_API_URL +
LLM_API_KEY).
"""

import json
import urllib.error
import urllib.request


class LLMError(Exception):
    """Endpoint/transport failure surfaced to the loop as unrecoverable."""


def completions_url(api_url):
    """Normalize LLM_API_URL to a full chat-completions endpoint.

    Accepts a full endpoint, a `.../v1` base, or a bare host — appends the
    conventional suffix only when it is not already present.
    """
    url = api_url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return url + "/chat/completions"
    return url + "/v1/chat/completions"


def chat_completion(api_url, api_key, model, messages, tools=None,
                    temperature=0, timeout=120, _opener=None):
    """POST one chat-completions request; return the parsed JSON response.

    `_opener` is an injection seam for tests (a callable taking a urllib.request
    .Request and returning a file-like with .read()); production uses urllib.
    """
    payload = {"model": model, "messages": messages, "temperature": temperature}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer %s" % api_key
    req = urllib.request.Request(
        completions_url(api_url), data=data, headers=headers, method="POST"
    )
    opener = _opener or (lambda r: urllib.request.urlopen(r, timeout=timeout))
    try:
        with opener(req) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        raise LLMError("HTTP %s from endpoint: %s" % (e.code, detail[:500]))
    except urllib.error.URLError as e:
        raise LLMError("cannot reach endpoint %s: %s" % (api_url, e.reason))
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise LLMError("endpoint returned non-JSON: %s" % e)


def first_message(response):
    """Extract choices[0].message from a chat-completions response, or raise."""
    try:
        return response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError("malformed completions response (no choices[0].message): %s" % e)

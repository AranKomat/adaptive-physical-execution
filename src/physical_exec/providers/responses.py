"""Explicit-endpoint Responses API client; no account access or inference on import.

One requested Act tool result per decision. No shell, browser, file access,
model fallback, automatic endpoint substitution, or executable Python output.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import json
import os
import time
from urllib.parse import urlsplit
import httpx
from ..contracts import Usage
from ..errors import ProviderError, BudgetExceeded


@dataclass(frozen=True)
class ProviderConfig:
    model: str
    endpoint: str  # complete URL ending in /responses, chosen by operator
    api_key_env: str = "OPENAI_API_KEY"
    reasoning_effort: str = "medium"
    timeout_seconds: float = 180.0
    max_output_tokens: int = 8192
    max_calls: int = 100
    max_total_tokens: int = 20_000_000
    allow_insecure_localhost: bool = False

    def __post_init__(self):
        u = urlsplit(self.endpoint)
        if u.username or u.password or u.query or u.fragment or not u.hostname:
            raise ValueError("endpoint must be a clean explicit URL without credentials/query")
        local = u.hostname in ("localhost", "127.0.0.1", "::1")
        if u.scheme != "https" and not (local and u.scheme == "http" and self.allow_insecure_localhost):
            raise ValueError("use HTTPS, except explicitly authorized loopback test endpoints")
        if not u.path.rstrip("/").endswith("/responses"):
            raise ValueError("endpoint must be the complete Responses URL")
        if not self.model or self.reasoning_effort not in ("low", "medium", "high", "xhigh"):
            raise ValueError("explicit model and supported reasoning effort are required")
        if min(self.timeout_seconds, self.max_calls, self.max_total_tokens) <= 0 or self.max_output_tokens < 256:
            raise ValueError("invalid provider budget")


@dataclass(frozen=True)
class ModelReply:
    arguments: dict
    usage: Usage
    response_id: str


def extract_act(response: dict) -> dict:
    if response.get("status") not in (None, "completed") or response.get("error") or response.get("incomplete_details"):
        raise ProviderError("provider response not completed; refusing to execute partial output")
    output = response.get("output", [])
    if any(part.get("type") == "refusal" for item in output for part in item.get("content", [])):
        raise ProviderError("model refused the request; no action")
    calls = [x for x in output if x.get("type") == "function_call"]
    if len(calls) != 1 or calls[0].get("name") != "Act":
        raise ProviderError("expected exactly one Act call; no code/text fallback")
    args = calls[0].get("arguments")
    if not isinstance(args, str) or len(args.encode()) > 200000:
        raise ProviderError("invalid tool argument size/type")
    try:
        value = json.loads(args, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except ValueError as e:
        raise ProviderError("Act arguments are not finite JSON") from e
    if not isinstance(value, dict): raise ProviderError("Act requires a JSON object")
    return value


class ResponsesProvider:
    def __init__(self, config: ProviderConfig, *, allow_paid: bool = False,
                 client: httpx.Client | None = None):
        if not allow_paid:
            raise ProviderError("live model calls disabled; pass --allow-paid explicitly")
        self.config = config
        key = os.environ.get(config.api_key_env)
        if not key: raise ProviderError(f"missing API key environment variable: {config.api_key_env}")
        self._key = key
        self._client = client or httpx.Client(follow_redirects=False, trust_env=False)
        self._owns_client = client is None
        self.calls = 0
        self.usage_log: list[Usage] = []
        self.total_tokens = 0

    def act(self, instructions: str, messages: list[dict], schema: dict,
            timeout_seconds: float | None = None) -> ModelReply:
        cfg = self.config
        if self.calls >= cfg.max_calls or self.total_tokens >= cfg.max_total_tokens:
            raise BudgetExceeded("provider call/token budget reached")
        body = {"model": cfg.model, "instructions": instructions, "input": messages,
                "reasoning": {"effort": cfg.reasoning_effort}, "store": False,
                "max_output_tokens": cfg.max_output_tokens,
                "tools": [{"type": "function", "name": "Act", "description": "Submit one bounded physical decision.",
                           "parameters": schema, "strict": True}],
                "tool_choice": {"type": "function", "name": "Act"}, "parallel_tool_calls": False}
        self.calls += 1; started = time.monotonic()
        timeout = min(cfg.timeout_seconds, timeout_seconds) if timeout_seconds is not None else cfg.timeout_seconds
        if timeout <= 0: raise BudgetExceeded("wall-clock budget exhausted before request")
        try:
            r = self._client.post(cfg.endpoint, json=body,
                                  headers={"Authorization": f"Bearer {self._key}"}, timeout=timeout)
        except httpx.HTTPError as e:
            self.usage_log.append(Usage(latency_seconds=time.monotonic()-started, usage_reported=False))
            # Inference retry can duplicate billing. Never retry silently.
            raise ProviderError(f"model transport error ({type(e).__name__}); no action executed, no automatic retry") from e
        if r.status_code != 200:
            self.usage_log.append(Usage(latency_seconds=time.monotonic()-started, usage_reported=False))
            raise ProviderError(f"model HTTP {r.status_code}; endpoint/model/key/config must be checked; no fallback")
        if len(r.content) > 8_000_000:
            self.usage_log.append(Usage(latency_seconds=time.monotonic()-started, usage_reported=False))
            raise ProviderError("oversized response")
        try: result = r.json()
        except ValueError as e:
            self.usage_log.append(Usage(latency_seconds=time.monotonic()-started, usage_reported=False))
            raise ProviderError("non-JSON provider response") from e
        usage = Usage.from_response(result, time.monotonic()-started)
        self.usage_log.append(usage); self.total_tokens += usage.total_tokens
        # Record usage even when a subsequent validation rejects the action.
        args = extract_act(result)
        return ModelReply(args, usage, str(result.get("id", "unreported")))

    def close(self):
        if self._owns_client: self._client.close()
        self._key = ""

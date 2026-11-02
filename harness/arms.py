"""The two arms (pre-registration §7): one generator call each, JSON mode.

The model endpoint is instance configuration (option 1 of the brief, doc-0001): one
OpenAI-compatible endpoint named by three settings, read when a call is made:

    KG_MODEL_BASE_URL      the endpoint (default the OpenAI client's own, api.openai.com);
                           Google's compatible endpoint, Azure OpenAI, or a private model
                           behind vLLM, Ollama, LiteLLM or an enterprise gateway go here
    KG_MODEL_API_KEY_VAR   the name of the variable that holds the key (default OPENAI_API_KEY)
    KG_ARMS_MODEL          the model name (default the subject's record model)

The arms are enabled only when the named key variable holds a value; a private instance
that sets none sends nothing anywhere. A model other than the record's is a deviation the
page marks on every run.

Budget guard: MAX_CALLS and a token ceiling over the API's usage field
(KG_ARMS_MAX_TOKENS, prompt and completion tokens of the process). No price
lives here (task-0027): a list price goes stale and nobody refreshes it, so
the harness counts what the API returns and the provider's bill is the record
of cost. The CargoQuote record's dollar figures are frozen data from before.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
from subject import SUBJECT  # noqa: E402

RECORD_MODEL = SUBJECT.record_model  # the model of the subject's scored run, "" when its record ran no arm
RECORD_EFFORT = SUBJECT.record_effort  # the reasoning effort of that run, "" for the API default (task-0028)
DEFAULT_MODEL = "gpt-5.5"            # what the arms call when the record names no model and KG_ARMS_MODEL is unset
# The demo's Arms mode may call another model through KG_ARMS_MODEL (a legacy model's
# rate limit on a new organisation blocked the governed prompt there); such runs are a
# deviation the demo page names, and they never write into results/.
MODEL = os.environ.get("KG_ARMS_MODEL") or RECORD_MODEL or DEFAULT_MODEL
DEFAULT_BASE_URL = "https://api.openai.com/v1"   # the OpenAI client's own default, named so the page can show it
MAX_CALLS = 90
DEFAULT_CEILING_TOKENS = 6_000_000   # prompt and completion tokens per process; the record's 80 calls used about a third of it


def ceiling_tokens() -> int:
    """The process's token ceiling: instance configuration, with the documented default."""
    return int(os.environ.get("KG_ARMS_MAX_TOKENS") or DEFAULT_CEILING_TOKENS)


def tokens_of(rec: dict) -> int:
    """What a call cost in the one unit the API reports: prompt plus completion tokens."""
    return int(rec.get("prompt_tokens", 0) or 0) + int(rec.get("completion_tokens", 0) or 0)


def cached_of(usage_obj) -> int:
    """The API's cached prompt tokens (prompt_tokens_details.cached_tokens), 0 when the endpoint reports none."""
    det = getattr(usage_obj, "prompt_tokens_details", None)
    return int(getattr(det, "cached_tokens", 0) or 0) if det is not None else 0

_lock = threading.Lock()
_state = {"calls": 0, "tokens": 0, "usage": []}


class BudgetExceeded(RuntimeError):
    pass


def endpoint() -> dict:
    """The instance settings as they stand now (base URL, key variable, model, effort), and whether a
    call would be a deviation from the record: a model or an effort other than the record's, when the
    record ran an arm at all. KG_ARMS_EFFORT is the reasoning effort sent with every call; empty sends
    none and the API applies its default (task-0028)."""
    key_var = os.environ.get("KG_MODEL_API_KEY_VAR") or "OPENAI_API_KEY"
    base_url = os.environ.get("KG_MODEL_BASE_URL") or DEFAULT_BASE_URL
    model = os.environ.get("KG_ARMS_MODEL") or RECORD_MODEL or DEFAULT_MODEL
    effort = (os.environ.get("KG_ARMS_EFFORT") or "").strip()
    return {"base_url": base_url, "host": host_of(base_url), "key_var": key_var, "key_set": bool(os.environ.get(key_var)),
            "model": model, "record_model": RECORD_MODEL, "effort": effort, "record_effort": RECORD_EFFORT,
            "deviation": bool(RECORD_MODEL) and (model != RECORD_MODEL or effort != RECORD_EFFORT)}


def host_of(base_url: str) -> str:
    """The host part of a base URL, what the page and a run file name the endpoint by."""
    return base_url.split("://", 1)[-1].split("/", 1)[0]


def effort_kwargs(effort: str) -> dict:
    """The request's reasoning-effort argument: set only when an effort is named, so an empty effort
    sends no parameter and the API applies its own default."""
    return {"reasoning_effort": effort} if effort else {}


def enabled() -> bool:
    """True only when the named key variable holds a value and the subject declares an oracle to
    grade a reply: no key, no call, nothing sent; no oracle, nothing to grade, the arms stay off."""
    return endpoint()["key_set"] and SUBJECT.oracle_script() is not None


def policy() -> str:
    return (HERE / "policy.md").read_text(encoding="utf-8")


def prompt(name: str) -> str:
    return SUBJECT.prompt(name)   # the task prompts are the subject's


def baseline_documents(kit: dict[str, str], order: list[str]) -> str:
    parts = []
    for path in order:
        if path in kit:
            parts.append(f"=== {path} ===\n{kit[path]}\n")
    return "\n".join(parts)


def call(system: str, user: str, *, tag: str) -> dict:
    with _lock:
        if _state["calls"] >= MAX_CALLS:
            raise BudgetExceeded(f"MAX_CALLS={MAX_CALLS}")
        if _state["tokens"] >= ceiling_tokens():
            raise BudgetExceeded(f"ceiling {ceiling_tokens()} tokens")
        _state["calls"] += 1
    from openai import OpenAI  # lazy: the module loads without the client installed

    ep = endpoint()
    # the scored run went through the session proxy, which injected the key and ignored the
    # placeholder; outside it (the demo container, a laptop) the key comes from the named
    # variable and is never written to disk; the endpoint is whatever the instance set
    client = OpenAI(api_key=os.environ.get(ep["key_var"]) or "proxy-injected",
                    base_url=ep["base_url"] if ep["base_url"] != DEFAULT_BASE_URL else None, max_retries=0)
    model = ep["model"]
    t0 = time.time()
    attempts = 0
    while True:
        attempts += 1
        try:
            # streamed, because the session proxy cuts a non-streaming call that stays
            # silent too long (the OpenWiki record's finding, 2026-10-28); the chunks are
            # concatenated and usage is taken from the final chunk
            stream = client.chat.completions.create(
                model=model, response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                stream=True, stream_options={"include_usage": True}, **effort_kwargs(ep["effort"]),
            )
            parts, usage_obj, model_name = [], None, model
            for chunk in stream:
                if chunk.usage:
                    usage_obj = chunk.usage
                if getattr(chunk, "model", None):
                    model_name = chunk.model
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    parts.append(chunk.choices[0].delta.content)
            if usage_obj is None:
                raise RuntimeError("stream ended without a usage chunk")
            break
        except Exception as e:  # noqa: BLE001 — transient 5xx/429 from the proxy; retried, counted
            if attempts >= 4:
                raise
            with _lock:
                _state.setdefault("retries", []).append({"tag": tag, "attempt": attempts, "error": str(e)[:200]})
            time.sleep(5 * attempts)
    dt = time.time() - t0
    u = usage_obj
    cached = cached_of(u)
    rec = {"tag": tag, "model": model_name, "host": ep["host"], "effort": ep["effort"], "attempts": attempts, "streamed": True,
           "prompt_tokens": u.prompt_tokens, "cached_tokens": cached, "completion_tokens": u.completion_tokens, "seconds": round(dt, 1)}
    with _lock:
        _state["tokens"] += tokens_of(rec)
        _state["usage"].append(rec)
    raw = "".join(parts)
    try:
        parsed = json.loads(raw)
        parse_error = None
    except json.JSONDecodeError as e:
        parsed, parse_error = None, str(e)
    return {"raw": raw, "parsed": parsed, "parse_error": parse_error, "usage": rec}


def account(rec: dict) -> None:
    """Count a call made elsewhere (the agent loop) in this process's usage and budget guard."""
    with _lock:
        _state["calls"] += 1
        _state["tokens"] += tokens_of(rec)
        _state["usage"].append(rec)


def usage() -> dict:
    return {"calls": _state["calls"], "tokens": _state["tokens"], "retries": list(_state.get("retries", [])),
            "per_call": list(_state["usage"])}

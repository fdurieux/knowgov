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

Budget guard: MAX_CALLS and a dollar ceiling over the API's usage field,
priced at the list rates recorded below (read 2026-10-30; the record
quotes measured tokens, the dollars are an estimate).
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
from subject import SUBJECT  # noqa: E402

RECORD_MODEL = SUBJECT.record_model or "gpt-5.1-2025-11-13"  # the model of the scored run; the record's figures are this model's
# The demo's Arms mode may call another model through KG_ARMS_MODEL (a legacy model's
# rate limit on a new organisation blocked the governed prompt there); such runs are a
# deviation the demo page names, and they never write into results/.
MODEL = os.environ.get("KG_ARMS_MODEL") or RECORD_MODEL
DEFAULT_BASE_URL = "https://api.openai.com/v1"   # the OpenAI client's own default, named so the page can show it
MAX_CALLS = 90
CEILING_USD = 25.0
PRICE_IN, PRICE_OUT = 1.25 / 1e6, 10.0 / 1e6  # USD per token, the record model's list price read 2026-10-30

_lock = threading.Lock()
_state = {"calls": 0, "usd": 0.0, "usage": []}


class BudgetExceeded(RuntimeError):
    pass


def endpoint() -> dict:
    """The three instance settings as they stand now, and whether the arms are enabled."""
    key_var = os.environ.get("KG_MODEL_API_KEY_VAR") or "OPENAI_API_KEY"
    base_url = os.environ.get("KG_MODEL_BASE_URL") or DEFAULT_BASE_URL
    model = os.environ.get("KG_ARMS_MODEL") or RECORD_MODEL
    return {"base_url": base_url, "key_var": key_var, "key_set": bool(os.environ.get(key_var)),
            "model": model, "record_model": RECORD_MODEL, "deviation": model != RECORD_MODEL}


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
        if _state["usd"] >= CEILING_USD:
            raise BudgetExceeded(f"ceiling ${CEILING_USD}")
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
                stream=True, stream_options={"include_usage": True},
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
    usd = u.prompt_tokens * PRICE_IN + u.completion_tokens * PRICE_OUT
    rec = {"tag": tag, "model": model_name, "attempts": attempts, "streamed": True, "prompt_tokens": u.prompt_tokens,
           "completion_tokens": u.completion_tokens, "seconds": round(dt, 1), "usd_est": round(usd, 4)}
    with _lock:
        _state["usd"] += usd
        _state["usage"].append(rec)
    raw = "".join(parts)
    try:
        parsed = json.loads(raw)
        parse_error = None
    except json.JSONDecodeError as e:
        parsed, parse_error = None, str(e)
    return {"raw": raw, "parsed": parsed, "parse_error": parse_error, "usage": rec}


def usage() -> dict:
    return {"calls": _state["calls"], "usd_est": round(_state["usd"], 4), "retries": list(_state.get("retries", [])),
            "per_call": list(_state["usage"])}

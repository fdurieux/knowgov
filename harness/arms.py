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


def thinking_uncounted() -> bool:
    """Whether the endpoint is declared to leave a thinking model's tokens out of streamed usage
    altogether, so the count is low and says nothing of it. Nothing in the usage shows it: a model
    row declares it (models.toml, thinking_uncounted) and the server passes KG_THINKING_UNCOUNTED.
    Measured 2026-11-02: LiteLLM's streamed usage for Gemini had total = prompt + completion, while
    Google's own endpoint, streamed, reports the thinking in its total (task-0034, doc-0006)."""
    import switches   # 1 on; 0, empty or unset off; else BadSwitch (task-0276)
    return switches.on("KG_THINKING_UNCOUNTED")


def usage_fields(usage_obj, host: str = "") -> dict:
    """The token fields of one call, as the endpoint reports them: prompt, cached, completion, the
    total when it reports one, and the hidden remainder, the tokens the total holds beyond prompt
    and completion (a thinking model's, where the endpoint counts them nowhere else). Whether the
    endpoint is declared to leave thinking uncounted is recorded beside them."""
    p = int(getattr(usage_obj, "prompt_tokens", 0) or 0)
    c = int(getattr(usage_obj, "completion_tokens", 0) or 0)
    total = getattr(usage_obj, "total_tokens", None)
    total = int(total) if total else None
    return {"prompt_tokens": p, "cached_tokens": cached_of(usage_obj), "completion_tokens": c, "total_tokens": total,
            "hidden_tokens": max(0, total - p - c) if total else 0, "thinking_uncounted": thinking_uncounted()}


def tokens_of(rec: dict) -> int:
    """What a call counts against a ceiling: the endpoint's total when it reports one (it holds the
    tokens a thinking model spends beyond prompt and completion), else prompt plus completion."""
    pc = int(rec.get("prompt_tokens", 0) or 0) + int(rec.get("completion_tokens", 0) or 0)
    return max(pc, int(rec.get("total_tokens") or 0))


def cached_of(usage_obj) -> int:
    """The API's cached prompt tokens (prompt_tokens_details.cached_tokens), 0 when the endpoint reports none."""
    det = getattr(usage_obj, "prompt_tokens_details", None)
    return int(getattr(det, "cached_tokens", 0) or 0) if det is not None else 0

_lock = threading.Lock()
_state = {"calls": 0, "tokens": 0, "usage": []}


class BudgetExceeded(RuntimeError):
    pass


CUT_CHARS_PER_TOKEN = 10   # doc-0023 defect 1: a whole prompt measured 4.7 characters per token, the one Ollama cut 27
CUT_MIN_CHARS = 4_000      # below it the ratio is a tokenizer's overhead, and no server's context is that short


class PromptCut(RuntimeError):
    """The endpoint read far fewer prompt tokens than the characters sent can hold: a server whose
    context is shorter than the prompt cut it and still answered (Ollama at its defaults, doc-0023
    defect 1). The call is marked on the run and never scored as an answer (task-0185)."""

    def __init__(self, detail: dict, usage: dict | None = None):
        super().__init__(detail["why"])
        self.detail, self.usage = detail, usage


def prompt_cut(chars: int, usage: dict) -> dict | None:
    """The mark for a call whose reported prompt tokens are too few for the characters sent, else None.
    The tokens read are the larger of the prompt and the cached tokens, so an endpoint that counts a
    cached prefix apart from the prompt is not read as a cut; an endpoint that reports no prompt tokens
    is not marked, since there is nothing to compare, and neither is a prompt under CUT_MIN_CHARS, whose
    ratio says more of the tokenizer's overhead than of a cut. The OpenAI API carries no context length,
    so the harness can only see the cut, never prevent it: the server's own setting does that."""
    seen = max(int(usage.get("prompt_tokens") or 0), int(usage.get("cached_tokens") or 0))
    if seen <= 0 or chars < CUT_MIN_CHARS or chars <= CUT_CHARS_PER_TOKEN * seen:
        return None
    ratio = chars / seen
    return {"chars": chars, "prompt_tokens": seen, "chars_per_token": round(ratio, 1), "threshold": CUT_CHARS_PER_TOKEN,
            "why": (f"prompt cut by the endpoint: {chars:,} characters sent, {seen:,} prompt tokens read "
                    f"({ratio:.1f} characters per token, above {CUT_CHARS_PER_TOKEN}); set the server's context length")}


def text_of(content) -> str:
    """The text of a reply's content (task-0186). A string is the text. A list of parts, which Mistral
    sends at reasoning_effort high (a thinking part, then text; streamed, a list while it thinks, then
    strings; doc-0023 defect 2), gives its text parts only, the thinking dropped. The pinned SDK keeps
    such a list as it came, dicts or objects, so both are read."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        out = []
        for part in content:
            if isinstance(part, str):
                out.append(part)
                continue
            get = part.get if isinstance(part, dict) else (lambda k, d=None, p=part: getattr(p, k, d))
            if get("type") == "text":
                out.append(str(get("text") or ""))
        return "".join(out)
    return str(content)


class IncompleteStream(RuntimeError):
    """A stream that ended without its usage part: retried, as a transient fault (task-0187)."""


_TRANSIENT_NAMES = {"APIConnectionError", "APITimeoutError", "TransportError", "TimeoutException"}


def transient(e: BaseException) -> bool:
    """Whether a failed call is worth another attempt (task-0187): a 429 or a 5xx, a connection or a
    timeout failure (the SDK's or the transport's), a stream that ended without its usage, or an error
    event inside a 200 stream (the SDK's APIError with no status, which a stream carries in place of a
    5xx). Any other status, a 400 for an effort the model refuses, a 401, a 404, is reported at once,
    and so is any other exception: retrying it only spends the waits."""
    status = getattr(e, "status_code", None)
    if isinstance(status, int):
        return status == 429 or status >= 500
    if isinstance(e, (IncompleteStream, ConnectionError, TimeoutError)):
        return True
    names = {c.__name__ for c in type(e).__mro__}
    if names & _TRANSIENT_NAMES:
        return True
    return type(e).__name__ == "APIError"


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
                    parts.append(text_of(chunk.choices[0].delta.content))   # a list of parts gives its text (task-0186)
            if usage_obj is None:
                raise IncompleteStream("stream ended without a usage chunk")
            break
        except Exception as e:  # noqa: BLE001 — a 429, a 5xx or a dropped connection is retried and counted; any other error at once (task-0187)
            if attempts >= 4 or not transient(e):
                raise
            with _lock:
                _state.setdefault("retries", []).append({"tag": tag, "attempt": attempts, "error": str(e)[:200]})
            time.sleep(5 * attempts)
    dt = time.time() - t0
    u = usage_obj
    rec = {"tag": tag, "model": model_name, "host": ep["host"], "effort": ep["effort"], "attempts": attempts, "streamed": True,
           **usage_fields(u, ep["host"]), "seconds": round(dt, 1)}
    cut = prompt_cut(len(system) + len(user), rec)   # task-0185: the tokens were spent, so they are counted; the reply is never read
    if cut:
        rec["prompt_cut"] = cut
    with _lock:
        _state["tokens"] += tokens_of(rec)
        _state["usage"].append(rec)
    if cut:
        raise PromptCut(cut, rec)
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

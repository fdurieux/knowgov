"""The agent arm (task-0022.02): the arm as a turn loop with tools over a per-run sandbox.

The one-reply arm (arms.py) asks for one JSON reply. At the size of a real task both arms asked
for iteration against the suite instead (task-0022.01, 2026-11-02), which is how the J-F record's
rebuilds were made. This loop gives the model four tools and a working directory:

    read_document(path)         a document as the scenario's kit holds it (B: any kit file;
                                G: the documents the task names verbatim)
    write_file(path, content)   a file inside the run's sandbox, nowhere else
    run_suite(feature)          the scenario's own suite, or one feature of it, over the sandbox,
                                through the subject's oracle script (its planted features are the
                                feedback; the pristine suite stays the oracle, run afterwards)
    finish(decision, ...)       the reply's vocabulary: decision, assumptions, questions, claims

A per-run ceiling in calls, dollars and seconds ends a run with decision ``abstain`` and the
reason; every turn and tool call is traced with tokens, cost and elapsed seconds. The responder
(the model call) is injectable, so the loop is tested without a client; the default one streams
the chat completions API with tool calling, as arms.call does without tools. Nothing here names
a subject: the layout, the suite and the documents come from the manifest and the kit.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import arms
from subject import bundle

DEFAULT_CEILING = {"calls": 30, "usd": 5.0, "seconds": 1500}   # the record's rebuilds ran about 1,455 s each
READ_LIMIT = 60_000       # characters a read_document result may carry
RESULT_LIMIT = 6_000      # characters a run_suite result may carry
NUDGES = 2                # replies without a tool call or a finish before the run is stopped

TOOLS = [
    {"type": "function", "function": {"name": "read_document", "description": "Read one document of the kit as the scenario holds it, by its path.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write one file into the sandbox (the program under construction); the path is relative to the sandbox root; an existing file is replaced.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "run_suite", "description": "Run the scenario's acceptance suite over the sandbox, one feature by name or every feature when null; returns cases passed per feature and the failed scenarios' names.",
                                      "parameters": {"type": "object", "properties": {"feature": {"type": ["string", "null"]}}, "required": ["feature"]}}},
    {"type": "function", "function": {"name": "finish", "description": "End the run with the decision and the reply's lists; the sandbox as it stands is graded.",
                                      "parameters": {"type": "object", "properties": {
                                          "decision": {"type": "string", "enum": ["generate", "generate with assumptions", "abstain"]},
                                          "assumptions": {"type": "array", "items": {"type": "object", "properties": {"text": {"type": "string"}, "ref": {"type": "string"}}}},
                                          "questions": {"type": "array", "items": {"type": "string"}},
                                          "claims": {"type": "array", "items": {"type": "object", "properties": {"text": {"type": "string"}, "ref": {"type": "string"}}}}},
                                          "required": ["decision"]}}},
]


def ceiling() -> dict:
    """The per-run ceiling: instance configuration, with the documented defaults."""
    return {"calls": int(os.environ.get("KG_AGENT_MAX_CALLS") or DEFAULT_CEILING["calls"]),
            "usd": float(os.environ.get("KG_AGENT_MAX_USD") or DEFAULT_CEILING["usd"]),
            "seconds": int(os.environ.get("KG_AGENT_MAX_SECONDS") or DEFAULT_CEILING["seconds"])}


def safe_rel(path: str) -> str:
    """A sandbox-relative path: POSIX, no absolute, no parent step, nothing hidden."""
    p = str(path or "").replace("\\", "/").strip()
    if not p or p.startswith("/") or p.startswith("~") or any(part in ("..", "") or part.startswith(".") for part in p.split("/")):
        raise ValueError(f"not a sandbox path: {path!r}")
    return p


class Sandbox:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, rel: str, content: str) -> str:
        rel = safe_rel(rel)
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str) else str(content), encoding="utf-8")
        return rel

    def files(self) -> list[str]:
        return sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)

    def text(self) -> str:
        """The sandbox as one bundle, for the page's code view and the record."""
        return bundle(self.root, ["**/*.py", "**/*.sh", "**/*.toml", "**/*.md", "**/*.txt", "*.py"])


def _clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n] + f"\n... [{len(s) - n} more characters]"


def openai_responder(model: str | None = None):
    """The default responder: one streamed chat completion with tools; returns the assistant turn."""
    def respond(messages: list[dict], tools: list[dict]) -> dict:
        from openai import OpenAI  # lazy, as in arms.call

        ep = arms.endpoint()
        client = OpenAI(api_key=os.environ.get(ep["key_var"]) or "proxy-injected",
                        base_url=ep["base_url"] if ep["base_url"] != arms.DEFAULT_BASE_URL else None, max_retries=0)
        t0 = time.time()
        stream = client.chat.completions.create(model=model or ep["model"], messages=messages, tools=tools, tool_choice="auto",
                                                stream=True, stream_options={"include_usage": True})
        parts, calls, usage_obj, model_name = [], {}, None, model or ep["model"]
        for chunk in stream:
            if chunk.usage:
                usage_obj = chunk.usage
            if getattr(chunk, "model", None):
                model_name = chunk.model
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                parts.append(delta.content)
            for tc in (delta.tool_calls or []) if delta else []:
                slot = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] += tc.function.name
                if tc.function and tc.function.arguments:
                    slot["arguments"] += tc.function.arguments
        if usage_obj is None:
            raise RuntimeError("stream ended without a usage chunk")
        return {"content": "".join(parts) or None, "tool_calls": [calls[i] for i in sorted(calls)], "model": model_name,
                "usage": {"prompt_tokens": usage_obj.prompt_tokens, "completion_tokens": usage_obj.completion_tokens},
                "seconds": round(time.time() - t0, 1)}
    return respond


def run(system: str, user: str, *, sandbox: Path, read_text, feedback, tag: str, responder=None, limits: dict | None = None) -> dict:
    """The loop. ``read_text(path)`` serves read_document; ``feedback(sandbox_root, feature)`` serves
    run_suite and returns a JSON-able dict; the result carries the final reply (or None), what
    stopped the run, the trace, the totals and the sandbox's files."""
    responder = responder or openai_responder()
    lim = {**ceiling(), **(limits or {})}
    box = Sandbox(sandbox)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    trace: list[dict] = []
    tot = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "usd": 0.0, "tool_calls": 0, "model": None}
    t0 = time.time()
    final: dict | None = None
    stopped_by: str | None = None
    nudges = 0
    while final is None:
        elapsed = round(time.time() - t0, 1)
        if tot["calls"] >= lim["calls"]:
            stopped_by = f"ceiling: {lim['calls']} calls"
        elif tot["usd"] >= lim["usd"]:
            stopped_by = f"ceiling: ${lim['usd']:.2f}"
        elif elapsed >= lim["seconds"]:
            stopped_by = f"ceiling: {lim['seconds']} seconds"
        if stopped_by:
            break
        try:
            r = responder(messages, TOOLS)
        except Exception as e:  # noqa: BLE001 — a failed call ends the run as an api error, never silently
            stopped_by = f"api error: {str(e)[:200]}"
            trace.append({"turn": len(trace) + 1, "kind": "error", "text": str(e)[:300], "at": round(time.time() - t0, 1)})
            break
        u = r.get("usage") or {}
        usd = u.get("prompt_tokens", 0) * arms.PRICE_IN + u.get("completion_tokens", 0) * arms.PRICE_OUT
        tot["calls"] += 1
        tot["prompt_tokens"] += u.get("prompt_tokens", 0)
        tot["completion_tokens"] += u.get("completion_tokens", 0)
        tot["usd"] += usd
        tot["model"] = r.get("model") or tot["model"]
        arms.account({"tag": f"{tag}/turn{tot['calls']}", "model": r.get("model"), "attempts": 1, "streamed": True,
                      "prompt_tokens": u.get("prompt_tokens", 0), "completion_tokens": u.get("completion_tokens", 0),
                      "seconds": r.get("seconds", 0), "usd_est": round(usd, 4)})
        calls = r.get("tool_calls") or []
        trace.append({"turn": len(trace) + 1, "kind": "model", "tool_calls": [c["name"] for c in calls], "text": _clip(r.get("content") or "", 300),
                      "prompt_tokens": u.get("prompt_tokens", 0), "completion_tokens": u.get("completion_tokens", 0),
                      "usd": round(usd, 4), "seconds": r.get("seconds", 0), "at": round(time.time() - t0, 1)})
        if not calls:
            parsed = None
            try:
                parsed = json.loads(r.get("content") or "")
            except (json.JSONDecodeError, TypeError):
                pass
            if isinstance(parsed, dict) and parsed.get("decision"):
                final = parsed   # the one-reply vocabulary is accepted as a finish
                break
            messages.append({"role": "assistant", "content": r.get("content") or ""})
            nudges += 1
            if nudges > NUDGES:
                stopped_by = "no finish: the model stopped using the tools"
                break
            messages.append({"role": "user", "content": "Continue with the tools; end the run with finish(decision, assumptions, questions, claims)."})
            continue
        messages.append({"role": "assistant", "content": r.get("content") or None,
                         "tool_calls": [{"id": c["id"] or f"call_{i}", "type": "function", "function": {"name": c["name"], "arguments": c["arguments"] or "{}"}} for i, c in enumerate(calls)]})
        for i, c in enumerate(calls):
            tot["tool_calls"] += 1
            try:
                args = json.loads(c["arguments"] or "{}")
            except json.JSONDecodeError as e:
                args, result = {}, {"error": f"arguments are not JSON: {e}"}
            else:
                result = None
            t1 = time.time()
            if result is None:
                try:
                    if c["name"] == "read_document":
                        result = {"path": args.get("path"), "text": _clip(read_text(args.get("path")), READ_LIMIT)}
                    elif c["name"] == "write_file":
                        result = {"written": box.write(args.get("path"), args.get("content", ""))}
                    elif c["name"] == "run_suite":
                        result = feedback(box.root, args.get("feature"))
                    elif c["name"] == "finish":
                        final = {"decision": args.get("decision"), "assumptions": args.get("assumptions") or [],
                                 "questions": args.get("questions") or [], "claims": args.get("claims") or []}
                        result = {"ok": True}
                    else:
                        result = {"error": f"unknown tool {c['name']}"}
                except Exception as e:  # noqa: BLE001 — a tool's refusal is the model's to read, never the run's end
                    result = {"error": str(e)[:300]}
            text = _clip(json.dumps(result, ensure_ascii=False), RESULT_LIMIT)
            messages.append({"role": "tool", "tool_call_id": c["id"] or f"call_{i}", "content": text})
            summary = {k: (v if k != "text" else f"{len(v)} chars") for k, v in (result.items() if isinstance(result, dict) else [])}
            trace.append({"turn": len(trace) + 1, "kind": "tool", "tool": c["name"],
                          "args": {k: (v if k != "content" else f"{len(str(v))} chars") for k, v in args.items()},
                          "result": _clip(json.dumps(summary, ensure_ascii=False), 400), "seconds": round(time.time() - t1, 1), "at": round(time.time() - t0, 1)})
            if final is not None:
                break
    if final is None:
        final_reply = {"decision": "abstain", "assumptions": [], "questions": [f"The run ended before a finish: {stopped_by}."], "claims": []}
    else:
        final_reply = final
    return {"parsed": final_reply, "finished": final is not None, "stopped_by": stopped_by, "trace": trace,
            "totals": {**tot, "usd": round(tot["usd"], 4), "seconds": round(time.time() - t0, 1), "turns": len(trace)},
            "files": box.files(), "ceiling": lim}

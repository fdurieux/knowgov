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

A per-run ceiling in calls, tokens and seconds ends a run with decision ``abstain`` and the
reason; every turn and tool call is traced with tokens and elapsed seconds (no price: task-0027). The responder
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

DEFAULT_CEILING = {"calls": 30, "tokens": 1_500_000, "seconds": 1500}   # the record's rebuilds ran about 1,455 s each; tokens are prompt plus completion
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


EXTRA_TOOLS = {
    "read_knowledge": {"type": "function", "function": {"name": "read_knowledge", "description": "Read one required key's knowledge from the governed repository: its level, every live assertion with value, evidence, verification, approval and gaps. Each call is recorded as consulted.",
                                                        "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
}


def ceiling() -> dict:
    """The per-run ceiling: instance configuration, with the documented defaults."""
    return {"calls": int(os.environ.get("KG_AGENT_MAX_CALLS") or DEFAULT_CEILING["calls"]),
            "tokens": int(os.environ.get("KG_AGENT_MAX_TOKENS") or DEFAULT_CEILING["tokens"]),
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
        """Write inside the sandbox, never through a link (task-0141.05, EXEC-04): every directory of
        the path is opened by descriptor with O_NOFOLLOW from the root's, and the file itself opened
        O_NOFOLLOW, so a symlink at any step, planted before or swapped in during the write, is refused
        (ELOOP or ENOTDIR) rather than followed out of the sandbox."""
        rel = safe_rel(rel)
        data = (content if isinstance(content, str) else str(content)).encode("utf-8")
        parts = rel.split("/")
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                try:
                    os.mkdir(part, 0o755, dir_fd=fd)
                except FileExistsError:
                    pass
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = nxt
            out = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644, dir_fd=fd)
            try:
                os.write(out, data)
            finally:
                os.close(out)
        except OSError as e:
            raise ValueError(f"not a sandbox path: {rel!r} ({e.strerror})") from None
        finally:
            os.close(fd)
        return rel

    def files(self) -> list[str]:
        """The sandbox's regular files, never through a link."""
        out = []
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            dirnames[:] = [d for d in dirnames if d != "__pycache__" and not os.path.islink(os.path.join(dirpath, d))]
            for name in filenames:
                full = os.path.join(dirpath, name)
                if not os.path.islink(full) and os.path.isfile(full):
                    out.append(os.path.relpath(full, self.root).replace(os.sep, "/"))
        return sorted(out)

    def text(self) -> str:
        """The sandbox as one bundle, for the page's code view and the record."""
        return bundle(self.root, ["**/*.py", "**/*.sh", "**/*.toml", "**/*.md", "**/*.txt", "*.py"])


def _clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n] + f"\n... [{len(s) - n} more characters]"


IDLE_SECONDS = 120.0   # the longest silence a stream may keep, unless KG_AGENT_IDLE_SECONDS says


def bounded(stream, deadline: float | None, idle: float):
    """The stream's items until it ends, or a TimeoutError once ``idle`` seconds pass without one or
    the monotonic ``deadline`` passes, however the items trickle (task-0141.05, EXEC-08). A reader
    thread pulls; this side waits with a timeout, so a blocked or trickling stream cannot hold the run;
    on a timeout the stream is closed where it can be."""
    import queue
    import threading
    q: queue.Queue = queue.Queue(maxsize=64)
    done = object()

    def pull():
        try:
            for item in stream:
                q.put(("item", item))
        except BaseException as e:  # noqa: BLE001 — handed to the consumer
            q.put(("error", e))
        q.put(("end", done))
    threading.Thread(target=pull, daemon=True).start()
    while True:
        wait = idle if deadline is None else min(idle, deadline - time.monotonic())
        if wait <= 0:
            _close(stream)
            raise TimeoutError("the run's deadline passed while the model was answering")
        try:
            kind, item = q.get(timeout=wait)
        except queue.Empty:
            _close(stream)
            late = deadline is not None and time.monotonic() >= deadline
            raise TimeoutError("the run's deadline passed while the model was answering" if late
                               else f"the model sent nothing for {idle:g} s") from None
        if kind == "end":
            return
        if kind == "error":
            raise item
        yield item


def _close(stream) -> None:
    for name in ("close", "response.close"):
        obj = stream
        try:
            for attr in name.split("."):
                obj = getattr(obj, attr)
            obj()
            return
        except Exception:  # noqa: BLE001
            continue


def _accepts(fn, name: str) -> bool:
    import inspect
    try:
        return name in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def openai_responder(model: str | None = None):
    """The default responder: one streamed chat completion with tools; returns the assistant turn.
    ``deadline`` (monotonic) bounds the request and the stream's consumption (task-0141.05)."""
    def respond(messages: list[dict], tools: list[dict], deadline: float | None = None) -> dict:
        from openai import OpenAI  # lazy, as in arms.call

        ep = arms.endpoint()
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("the run's deadline passed before the model was asked")
        client = OpenAI(api_key=os.environ.get(ep["key_var"]) or "proxy-injected",
                        base_url=ep["base_url"] if ep["base_url"] != arms.DEFAULT_BASE_URL else None, max_retries=0,
                        **({"timeout": remaining} if remaining is not None else {}))
        t0 = time.monotonic()
        stream = client.chat.completions.create(model=model or ep["model"], messages=messages, tools=tools, tool_choice="auto",
                                                stream=True, stream_options={"include_usage": True}, **arms.effort_kwargs(ep["effort"]))
        idle = float(os.environ.get("KG_AGENT_IDLE_SECONDS") or IDLE_SECONDS)
        parts, calls, current, usage_obj, model_name = [], {}, {}, None, model or ep["model"]
        for chunk in bounded(stream, deadline, idle):
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
                # a call's pieces share its index (OpenAI) or arrive whole with no index (Gemini, which
                # streams parallel calls under index None); a new id under the same key starts a new call
                key = tc.index if tc.index is not None else "none"
                cur = current.get(key)
                if cur is None or (tc.id and calls[cur]["id"] and calls[cur]["id"] != tc.id):
                    cur = current[key] = len(calls)
                    calls[cur] = {"id": "", "name": "", "arguments": ""}
                slot = calls[cur]
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] += tc.function.name
                if tc.function and tc.function.arguments:
                    slot["arguments"] += tc.function.arguments
                # provider data on the call, kept as received and sent back unchanged: Gemini 3 puts its
                # thought signature here and refuses the next turn without it (task-0033, doc-0006)
                extra = getattr(tc, "extra_content", None) or (getattr(tc, "model_extra", None) or {}).get("extra_content")
                if extra:
                    slot["extra_content"] = extra
        if usage_obj is None:
            raise RuntimeError("stream ended without a usage chunk")
        return {"content": "".join(parts) or None, "tool_calls": [calls[i] for i in sorted(calls)], "model": model_name,
                "usage": arms.usage_fields(usage_obj, ep["host"]),
                "seconds": round(time.monotonic() - t0, 1)}
    return respond


def run(system: str, user: str, *, sandbox: Path, read_text, feedback, tag: str, responder=None, limits: dict | None = None,
        readers: dict | None = None) -> dict:
    """The loop. ``read_text(path)`` serves read_document; ``feedback(sandbox_root, feature)`` serves
    run_suite and returns a JSON-able dict; ``readers`` adds read tools by name (EXTRA_TOOLS), each a
    callable of the tool's one argument. The result carries the final reply (or None), what stopped
    the run, the trace, the totals, the sandbox's files and the consulted set: what every read tool
    was asked for, in order, the refusals included."""
    responder = responder or openai_responder()
    lim = {**ceiling(), **(limits or {})}
    readers = dict(readers or {})
    tools = TOOLS + [EXTRA_TOOLS[name] for name in readers if name in EXTRA_TOOLS]
    consulted: dict[str, list] = {"read_document": [], **{name: [] for name in readers}}
    box = Sandbox(sandbox)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    trace: list[dict] = []
    tot = {"calls": 0, "prompt_tokens": 0, "cached_tokens": 0, "completion_tokens": 0, "hidden_tokens": 0, "counted_tokens": 0,
           "thinking_uncounted": False, "tool_calls": 0, "model": None,
           "host": arms.endpoint()["host"], "effort": arms.endpoint()["effort"]}   # what every turn of this run was sent to, and at what effort
    t0 = time.monotonic()   # one monotonic deadline for the whole run (task-0141.05): a wall-clock jump moves nothing
    deadline = t0 + lim["seconds"]
    final: dict | None = None
    stopped_by: str | None = None
    nudges = 0
    while final is None:
        elapsed = round(time.monotonic() - t0, 1)
        if tot["calls"] >= lim["calls"]:
            stopped_by = f"ceiling: {lim['calls']} calls"
        elif tot["counted_tokens"] >= lim["tokens"]:   # the endpoint's totals where it reports them (task-0034)
            stopped_by = f"ceiling: {lim['tokens']} tokens"
        elif elapsed >= lim["seconds"]:
            stopped_by = f"ceiling: {lim['seconds']} seconds"
        if stopped_by:
            break
        try:
            r = responder(messages, tools, deadline=deadline) if _accepts(responder, "deadline") else responder(messages, tools)
        except Exception as e:  # noqa: BLE001 — a failed call ends the run as an api error, never silently
            stopped_by = f"api error: {str(e)[:200]}"
            trace.append({"turn": len(trace) + 1, "kind": "error", "text": str(e)[:300], "at": round(time.monotonic() - t0, 1)})
            break
        u = r.get("usage") or {}
        tot["calls"] += 1
        tot["prompt_tokens"] += u.get("prompt_tokens", 0)
        tot["cached_tokens"] += u.get("cached_tokens", 0)
        tot["completion_tokens"] += u.get("completion_tokens", 0)
        tot["hidden_tokens"] += u.get("hidden_tokens", 0) or 0
        tot["counted_tokens"] += arms.tokens_of(u)
        tot["thinking_uncounted"] = tot["thinking_uncounted"] or bool(u.get("thinking_uncounted"))
        tot["model"] = r.get("model") or tot["model"]
        arms.account({"tag": f"{tag}/turn{tot['calls']}", "model": r.get("model"), "host": tot["host"], "effort": tot["effort"], "attempts": 1, "streamed": True,
                      "prompt_tokens": u.get("prompt_tokens", 0), "cached_tokens": u.get("cached_tokens", 0), "completion_tokens": u.get("completion_tokens", 0),
                      "total_tokens": u.get("total_tokens"), "hidden_tokens": u.get("hidden_tokens", 0) or 0, "thinking_uncounted": bool(u.get("thinking_uncounted")),
                      "seconds": r.get("seconds", 0)})
        calls = r.get("tool_calls") or []
        trace.append({"turn": len(trace) + 1, "kind": "model", "tool_calls": [c["name"] for c in calls], "text": _clip(r.get("content") or "", 300),
                      "prompt_tokens": u.get("prompt_tokens", 0), "cached_tokens": u.get("cached_tokens", 0), "completion_tokens": u.get("completion_tokens", 0),
                      "hidden_tokens": u.get("hidden_tokens", 0) or 0, "seconds": r.get("seconds", 0), "at": round(time.monotonic() - t0, 1)})
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
                         "tool_calls": [{"id": c["id"] or f"call_{i}", "type": "function", "function": {"name": c["name"], "arguments": c["arguments"] or "{}"},
                                         **({"extra_content": c["extra_content"]} if c.get("extra_content") else {})} for i, c in enumerate(calls)]})
        for i, c in enumerate(calls):
            tot["tool_calls"] += 1
            try:
                args = json.loads(c["arguments"] or "{}")
            except json.JSONDecodeError as e:
                args, result = {}, {"error": f"arguments are not JSON: {e}"}
            else:
                result = None
            t1 = time.monotonic()
            if result is None:
                try:
                    if c["name"] == "read_document":
                        consulted["read_document"].append(args.get("path"))
                        result = {"path": args.get("path"), "text": _clip(read_text(args.get("path")), READ_LIMIT)}
                    elif c["name"] in readers:
                        arg = next(iter(args.values()), None) if args else None
                        consulted[c["name"]].append(arg)
                        result = {"key": arg, "text": _clip(readers[c["name"]](arg), READ_LIMIT)}
                    elif c["name"] == "write_file":
                        result = {"written": box.write(args.get("path"), args.get("content", ""))}
                    elif c["name"] == "run_suite":
                        result = (feedback(box.root, args.get("feature"), deadline=deadline) if _accepts(feedback, "deadline")
                                  else feedback(box.root, args.get("feature")))
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
                          "result": _clip(json.dumps(summary, ensure_ascii=False), 400), "seconds": round(time.monotonic() - t1, 1), "at": round(time.monotonic() - t0, 1)})
            if final is not None:
                break
    if final is None:
        final_reply = {"decision": "abstain", "assumptions": [], "questions": [f"The run ended before a finish: {stopped_by}."], "claims": []}
    else:
        final_reply = final
    return {"parsed": final_reply, "finished": final is not None, "stopped_by": stopped_by, "trace": trace,
            "totals": {**tot, "seconds": round(time.monotonic() - t0, 1), "turns": len(trace)},
            "files": box.files(), "ceiling": lim, "consulted": consulted}

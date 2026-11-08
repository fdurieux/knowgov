"""knowgov-runs: start and poll a scenario run through the page's run API, over MCP (task-0133).

    python harness/mcp_runs.py          # stdio only, for an agent that starts the server itself

decision-0008: the reader, ``harness/mcp_server.py`` (``knowgov``), stays read-only; runs go
through this second server, a client of the page's own ``POST /api/run`` and ``GET /api/run``. It
starts no process of its own: the page's one runner, its lock, its token rule (task-0096) and its
run folder (``run.json``, with ``by: mcp``) serve every run, and the page's banner shows it. Three
tools:

    run_options   what may be run: the modes this server allows, whether the page can run each (for
                  arms, a key and a contained worker: arms_ready, with execution's reason; where
                  the worker runs, as it attested it: worker, task-0169), the
                  model rows with their availability and key_check, the endpoint's verdict on each
                  row's key (task-0171; never a key), the subject's scenarios and the
                  run under way, if any (read-only)
    start_run     start one run of a scenario: deterministic, or arms when the operator allows it,
                  always at n = 1; refused while another run is under way, with the page's message.
                  It wipes and reloads the store the page and the reader share (never the record)
    run_status    a run's status, its elapsed time and the log's tail; when it has ended, its exit
                  code, the source id its results are read by and where to read them

Start and poll, never one blocking call: an arms run takes minutes. The environment says where the
page is and what may be run, and nothing in a call can widen it:

    KG_PAGE_URL       the page (default http://localhost:8080, the page inside the stack's container)
    KG_PAGE_TOKEN     the page's token, sent as Authorization: Bearer when set; never echoed
    KG_MCP_RUN_MODES  the modes start_run accepts, comma-separated (default deterministic); arms
                      only when the operator names it, and then only on a row whose key is set
    KG_SUBJECT        the subject the runs are for, as for the reader

Standard library only; the protocol layer is ``mcp_server.Server`` with this module's tool table.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mcp_server  # noqa: E402
from mcp_server import READ_ONLY, ToolError  # noqa: E402

SERVER = {"name": "knowgov-runs", "title": "knowgov scenario runs (through the page)", "version": mcp_server.SERVER["version"]}   # knowgov's VERSION (task-0231)
MODES = ("deterministic", "arms")
DEFAULT_PAGE = "http://localhost:8080"
LOG_TAIL = 4000          # characters of the log run_status returns
TIMEOUT = 30             # seconds a call to the page may take; a run is polled, never waited on

INSTRUCTIONS = ("knowgov-runs starts a scenario run of the subject through the knowgov page, and reports on it. "
                "Call run_options first: it names the modes you may start and the model rows; for an arms run, "
                "arms_ready says whether one would start and execution.why why not. Then start_run, "
                "and poll run_status until the status is done or failed; a run never answers in one call. A run "
                "wipes and reloads the one store the page, its viewers and the knowgov reader share, so every viewer "
                "sees your run, and the reader refuses its gate while the run loads. It never writes the record. "
                "After a run, ask the knowgov server (gate_verdict, scenario_runs) what it shows. A deterministic run "
                "costs nothing; an arms run calls a model on the operator's bill, and runs only where the operator "
                "allows it.")

START = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}


def allowed_modes() -> list[str]:
    """KG_MCP_RUN_MODES, read at each call: unknown names are dropped, deterministic by default."""
    raw = os.environ.get("KG_MCP_RUN_MODES")
    names = [m.strip() for m in (raw if raw is not None else "deterministic").split(",") if m.strip()]
    return [m for m in MODES if m in names]


def tools_table() -> list[dict]:
    """The tool table, its open-world hint on start_run true only when arms are allowed (a model call
    leaves this machine)."""
    start = dict(START, openWorldHint="arms" in allowed_modes())
    return _with_subject([
        {"name": "run_options", "title": "What may I run?",
         "description": "The modes this server lets you start (allowed_modes, from the operator's KG_MCP_RUN_MODES), whether "
                        "the page can run each now (deterministic_enabled: the store is reachable; arms_enabled: the subject has "
                        "an oracle and a model row's key is set; execution: whether model output may run now, ok and why not, "
                        "the instance guard and the contained worker's attestation; arms_ready: both, so an arms run would "
                        "start; worker: where model output would run, the worker's attested engine, kernel and machine, and a "
                        "cloud only as a reading of its kernel release), the model rows with their availability and efforts (never a "
                        "key) and each row's key_check (task-0171: the endpoint's model listing, no tokens: accepted, "
                        "refused, a refused row unavailable, unreachable or unchecked, with the HTTP status; scope "
                        "gateway when the listing proves a gateway's own key only), the subject's scenarios, whether the page asks for a token, and the run under way, if any.",
         "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
         "annotations": READ_ONLY},
        {"name": "start_run", "title": "Run this scenario (wipes and reloads the shared store)",
         "description": "Start one run of a scenario through the page, at n = 1: deterministic (the load, the rules and the "
                        "gate, seconds, no model call) or arms (the two assistants once each, graded by the oracle; minutes, "
                        "a model call on the operator's bill) where the operator allows it. It wipes and reloads the store "
                        "the page, its viewers and the knowgov reader share; the record is never written. Refused while "
                        "another run is under way, with the page's message. Returns the run's id: poll run_status.",
         "inputSchema": {"type": "object", "additionalProperties": False, "required": ["scenario", "mode"], "properties": {
             "scenario": {"type": "string", "description": "one of the subject's scenarios, as run_options lists them"},
             "mode": {"type": "string", "enum": list(MODES), "description": "deterministic, or arms where run_options allows it"},
             "row": {"type": "string", "description": "arms: the model row, as run_options lists it (default: the first available)"},
             "effort": {"type": "string", "description": "arms: an effort the row lists (default: the row's first)"},
             "as_of": {"type": "string", "description": "YYYY-MM-DD: the date the run's gate reads review currency on (default: the record date)"}}},
         "annotations": start},
        {"name": "run_status", "title": "How is the run going?",
         "description": "A run's status (running, done or failed), its elapsed seconds and the tail of its log; once it has "
                        "ended, its exit code, the source id its results are read by on the page, and the knowgov reader's "
                        "tools to ask next. With no run named, the page's latest run.",
         "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
             "run": {"type": "string", "description": "the id start_run returned (default: the page's latest run)"}}},
         "annotations": READ_ONLY},
    ])


class Page:
    """The page's run API over HTTP: the URL and the token from the environment, never from a call."""

    def __init__(self, url: str | None = None, token: str | None = None, opener=None):
        self.url = (url or os.environ.get("KG_PAGE_URL") or DEFAULT_PAGE).rstrip("/")
        self._token = token if token is not None else (os.environ.get("KG_PAGE_TOKEN") or None)
        self._open = opener or urllib.request.urlopen

    def _redact(self, text: str) -> str:
        return text.replace(self._token, "<token>") if self._token else text

    def request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        """(status, JSON body). A refusal from the page comes back as its status and message; a page that
        cannot be reached is a ToolError naming the URL, never the token."""
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        req = urllib.request.Request(self.url + path, data=data, method=method, headers=headers)
        try:
            with self._open(req, timeout=TIMEOUT) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                j = json.loads(e.read() or b"{}")
            except ValueError:
                j = {"error": e.reason}
            return e.code, j
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise ToolError(self._redact(f"the page at {self.url} did not answer: {e}")) from None


def _subject_id(args: dict | None = None) -> str:
    """The subject a call names (task-0157): an id, checked for its shape here and resolved by the page
    (``?subject=``, which refuses an id it does not serve); none named, this server's own, KG_SUBJECT."""
    from subject import SUBJECT
    import subject_ids
    sid = (args or {}).get("subject")
    if sid is None:
        return SUBJECT.id
    if not isinstance(sid, str) or not subject_ids.ID.fullmatch(sid) or ".." in sid:
        raise ToolError(f"subject is the id of a subject the page serves, never a path: {sid!r}")
    return sid


def _error_text(page: Page, code: int, j: dict) -> str:
    return page._redact(f"the page refused ({code}): {j.get('error') or j}")


_KEEP = ("id", "subject", "scenario", "mode", "n", "row", "model", "effort", "model_deviation", "as_of", "by",
         "started", "finished", "status", "exit_code", "elapsed_s", "source")


def _run_view(r: dict, tail: bool, page: "Page | None" = None) -> dict:
    out = {k: r.get(k) for k in _KEEP}
    if tail:
        text = (r.get("log_text") or "")[-LOG_TAIL:]
        out["log_tail"] = page._redact(text) if page else text
    return out


def _execution(j: dict) -> dict:
    """The page's ``execution`` as {ok, why}; a page that does not report it (before task-0167) reads refused."""
    e = j.get("execution")
    if not isinstance(e, dict) or not isinstance(e.get("ok"), bool):
        return {"ok": False, "why": "the page does not say whether model output may run (a page before task-0167)"}
    return {"ok": e["ok"], "why": None if e["ok"] else str(e.get("why") or "refused")}


def _worker(j: dict) -> dict:
    """The page's ``worker`` (task-0169, execution.placement()): where model output would run, as the
    worker attested it; a page that does not report it reads not attested."""
    w = j.get("worker")
    if not isinstance(w, dict) or not isinstance(w.get("attested"), bool):
        return {"backend": None, "attested": False, "host": None, "cloud": None,
                "why": "the page does not say where model output would run (a page before task-0169)"}
    return {k: w.get(k) for k in ("backend", "attested", "host", "cloud", "why")}


class RunTools:
    def __init__(self, page: Page | None = None):
        self.page = page or Page()

    def run_options(self, args: dict) -> dict:
        sid = _subject_id(args)
        code, j = self.page.request("GET", "/api/scenarios?subject=" + urllib.parse.quote(sid))
        if code != 200:
            raise ToolError(_error_text(self.page, code, j))
        modes = allowed_modes()
        execution = _execution(j)
        return {"subject": sid, "page": self.page.url, "allowed_modes": modes,
                "deterministic_enabled": bool(j.get("deterministic_enabled")),
                "arms_enabled": bool(j.get("arms_enabled")) and "arms" in modes,
                "arms_on_page": bool(j.get("arms_enabled")),
                # task-0168: whether model output may run now, as the page reports it (execution.refusal(): the
                # instance guard, the backend, the worker's attestation); an arms run starts only when it holds too
                "execution": execution, "arms_ready": bool(j.get("arms_enabled")) and "arms" in modes and execution["ok"],
                # task-0169: where model output would run, the worker's attested host facts and the cloud read from them
                "worker": _worker(j),
                "model_rows": [{k: r.get(k) for k in ("id", "label", "provider", "host", "model", "efforts", "key_var",
                                                       "key_set", "available", "why", "key_check")} for r in j.get("model_rows") or []],
                "record_model": j.get("record_model"), "record_effort": j.get("record_effort"),
                "scenarios": [s["id"] for s in j.get("scenarios") or []],
                "token_required": bool((j.get("writes") or {}).get("token_required")),
                "writes_refused": (j.get("writes") or {}).get("refused"),
                "run": _run_view(j["run"], tail=False) if j.get("run") else None,
                "knowgov": dict(mcp_server.KNOWGOV)}   # task-0231: which knowgov this server runs, read once at start

    def start_run(self, args: dict) -> dict:
        scenario, mode = args.get("scenario"), args.get("mode")
        if not isinstance(scenario, str) or not scenario:
            raise ToolError("scenario is required, as run_options lists them")
        modes = allowed_modes()
        if mode not in modes:
            raise ToolError(f"mode {mode!r} is not allowed here: this server starts {modes or 'nothing'} "
                            "(the operator's KG_MCP_RUN_MODES)")
        body = {"subject": _subject_id(args), "scenario": scenario, "mode": mode, "n": 1, "by": "mcp"}
        for k in ("row", "effort", "as_of"):
            v = args.get(k)
            if v is not None:
                if not isinstance(v, str):
                    raise ToolError(f"{k} must be a string")
                if k == "as_of" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                    raise ToolError("as_of must be YYYY-MM-DD")
                if mode == "deterministic" and k in ("row", "effort"):
                    raise ToolError(f"{k} is for an arms run; a deterministic run calls no model")
                body[k] = v
        code, j = self.page.request("POST", "/api/run", body)
        if code != 202:
            raise ToolError(_error_text(self.page, code, j))
        return {"started": True, **_run_view(j, tail=False),
                "next": "poll run_status with this run's id until its status is done or failed"}

    def run_status(self, args: dict) -> dict:
        want = args.get("run")
        if want is not None and not isinstance(want, str):
            raise ToolError("run must be a string, the id start_run returned")
        sid = _subject_id(args)
        code, cur = self.page.request("GET", "/api/run?subject=" + urllib.parse.quote(sid))
        if code != 200:
            raise ToolError(_error_text(self.page, code, cur))
        if cur.get("status") == "idle" and want is None:
            return {"status": "idle", "note": "the page has started no run since it began"}
        if want is None or cur.get("id") == want:
            r = _run_view(cur, tail=True, page=self.page)
        else:   # an earlier run: the page's list carries its run.json
            code, lst = self.page.request("GET", "/api/runs?subject=" + urllib.parse.quote(sid))
            if code != 200:
                raise ToolError(_error_text(self.page, code, lst))
            hit = next((x for x in lst.get("runs") or [] if x["id"].split("/")[-1] == want and x.get("run")), None)
            if hit is None:
                raise ToolError(f"no run {want!r} of {sid} on the page (a run with no results and not the latest is not listed)")
            r = _run_view(hit["run"], tail=False)
        if r.get("status") in ("done", "failed"):
            who = "" if "subject" not in args else f', "subject": "{sid}"'
            r["next"] = (f"ask the knowgov reader: scenario_runs {{\"scenario\": \"{r.get('scenario')}\"{who}}} for this run's verdict, "
                         f"gate_verdict {{\"scenario\": \"{r.get('scenario')}\"{who}}} on the store it loaded")
        return r


OUTPUT_SCHEMAS = {"run_options": "run-options", "start_run": "run-started", "run_status": "run-status"}   # task-0172


def _with_subject(table: list[dict]) -> list[dict]:
    """Every tool takes an optional subject id (task-0157), as the reader's do, and its description names the
    schema its structuredContent is pinned by (task-0172)."""
    for t in table:
        t["inputSchema"]["properties"]["subject"] = mcp_server.SUBJECT_ARG
        t["description"] += mcp_server.output_note(OUTPUT_SCHEMAS[t["name"]])
    return table


def make_server(page: Page | None = None) -> mcp_server.Server:
    return mcp_server.Server(RunTools(page), table=tools_table(), info=SERVER, instructions=INSTRUCTIONS)


def main(argv: list[str] | None = None) -> int:
    if argv:
        print("mcp_runs.py takes no arguments: stdio only; KG_PAGE_URL, KG_PAGE_TOKEN, KG_MCP_RUN_MODES configure it",
              file=sys.stderr)
        return 2
    try:
        server = make_server()
    except ValueError as e:   # KG_MCP_MAX_RESPONSE out of its bounds (task-0177): refused at start, named
        print(f"mcp_runs: {e}", file=sys.stderr)
        return 2
    mcp_server.serve_stdio(server)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

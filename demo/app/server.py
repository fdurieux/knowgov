"""The demo's web server: a menu of the seven scenarios, the report view,
and the store's saved queries. Standard library only (``http.server``);
the harness is run as a subprocess, never imported.

    python server.py                 # http://localhost:8080

Environment:
    KG_DEMO_PORT      port to listen on (8080)
    KG_NEO4J_URI      bolt URL the harness and the store probe use (bolt://localhost:7687;
                      the container sets bolt://neo4j:7687)
    KG_NEO4J_PASSWORD the store's password (kgpoc2026, the harness default)
    KG_BROWSER_URL    where the viewer's browser reaches Neo4j Browser (http://localhost:7474)
    KG_DEMO_RUNS      where re-runs land (runs/); the vendored record under
                      the subject's vendored record is never written
    KG_MODEL_BASE_URL, KG_MODEL_API_KEY_VAR, KG_ARMS_MODEL
                      the model endpoint (harness/arms.py): the arms are enabled only when the
                      variable KG_MODEL_API_KEY_VAR names (OPENAI_API_KEY by default) holds a
                      value; passed through to the harness, never stored
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cascade  # noqa: E402
import views  # noqa: E402
import register_project  # noqa: E402  (the register projected into the store, its own namespace)
import register_view  # noqa: E402  (the vendored IEAM register, read only)
import models  # noqa: E402  (the models table behind the Arms call drop-down, task-0029)

ROOT = HERE.parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
import page_subject  # noqa: E402  (the subject as a value: task-0032.01)
from subject import Subject  # noqa: E402
_ps = page_subject.current   # the subject of the call in progress; the environment's when no call names one


def _subject_roots() -> list[Path]:
    """KG_SUBJECTS: one or more roots, separated by commas or the path separator; each is a subject
    (it holds subject.toml) or a folder of subjects. Default the repository's subjects/ folder; an
    instance names /instance/subjects and lists its own subjects only (task-0032.02)."""
    raw = os.environ.get("KG_SUBJECTS") or str(ROOT / "subjects")
    out = []
    for part in re.split(r"[,%s]" % re.escape(os.pathsep), raw):
        root = Path(part.strip())
        if not part.strip() or not root.is_dir():
            continue
        if (root / "subject.toml").exists():
            out.append(root)   # a subject named directly is listed, whatever its manifest says
        else:
            out += sorted(d for d in root.iterdir() if (d / "subject.toml").exists()
                          and page_subject.of(Subject(d)).listed)   # a fixture (listed = false) is skipped in a scan
    return out


def _load_subjects() -> list:
    """Every subject the page serves, built once, in folder order, ids unique. KG_SUBJECT picks the
    default a request without ?subject= gets, moved first. When KG_SUBJECTS is set it is the whole
    list: an instance lists its own subjects and none of the public ones, whatever KG_SUBJECT says.
    When it is unset, a KG_SUBJECT outside the repository's subjects/ is listed too, as before."""
    roots = _subject_roots()
    named = os.environ.get("KG_SUBJECT")
    if named and not os.environ.get("KG_SUBJECTS") and Path(named).resolve() not in {r.resolve() for r in roots}:
        roots = [Path(named)] + roots
    listed, seen = [], set()
    for root in roots:
        ps = page_subject.of(Subject(root))
        if ps.id not in seen:
            seen.add(ps.id)
            listed.append(ps)
    if named:
        first = [ps for ps in listed if ps.root.resolve() == Path(named).resolve()]
        listed = first + [ps for ps in listed if ps not in first]
    return listed or [page_subject.current()]


SUBJECTS = _load_subjects()
SUBJECT_BY_ID = {ps.id: ps for ps in SUBJECTS}


def subjects_view() -> list[dict]:
    """What the header drop-down lists: id, name and the page title of each subject, the default first."""
    return [{"id": ps.id, "name": ps.subject.name, "title": ps.subject.page.get("title", ""), "default": i == 0}
            for i, ps in enumerate(SUBJECTS)]


def subject_of_request(q: dict, body: dict | None = None):
    """The subject a request names (?subject=, or "subject" in a POST body), the default when it
    names none; None for an id the page does not serve, which every route answers with 404."""
    sid = (q.get("subject") or [None])[0] or ((body or {}).get("subject") if isinstance(body, dict) else None)
    if not sid:
        return SUBJECTS[0]
    return SUBJECT_BY_ID.get(str(sid))
import arms  # noqa: E402  (the model endpoint settings; the client is imported only when a call is made)
RUNS_DIR = Path(os.environ.get("KG_DEMO_RUNS", str(ROOT / "runs")))
NEO4J_URI = os.environ.get("KG_NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.environ.get("KG_NEO4J_PASSWORD", "kgpoc2026")
BROWSER_URL = os.environ.get("KG_BROWSER_URL", "http://localhost:7474")
PORT = int(os.environ.get("KG_DEMO_PORT", "8080"))


def model_rows() -> list[dict]:
    """The Arms call drop-down's rows as the page receives them: no key, no price (task-0029)."""
    ps = _ps()
    return [models.public(r) for r in models.rows(ps.record_model, ps.record_effort, ps.arm_kind)]


def arms_enabled() -> bool:
    """The arms are on when the subject has an oracle to grade a reply and at least one row is
    available, its key variable set; no key, no call, nothing sent."""
    return _ps().subject.oracle_script() is not None and any(r["available"] for r in model_rows())
INDEX = (HERE / "index.html").read_bytes()

# Saved Cypher for the store panel. Each runs in Neo4j Browser against the
# scenario currently loaded; the comment on each says which scenario shows it.
def _store(timeout: float = 3):
    """A store through the port, for the page's short reads; raises when unreachable."""
    from store import open_store  # the harness's port; the adapter needs its driver, in the image
    if (os.environ.get("KG_STORE") or "neo4j").lower() == "rdflib" and not os.environ.get("KG_RDFLIB_FILE"):
        os.environ["KG_RDFLIB_FILE"] = str(RUNS_DIR / "store.ttl")
    return open_store(connection_timeout=timeout, instance=_ps().id)


# What each saved query needs in the store before it returns rows: the store holds one scenario
# at a time and the register only when projected, so a query run against the wrong state gets
# the console's "label not in the database" warnings and no records. The page marks each entry live.
NEEDS_TEXT = {"scenario": "any loaded scenario",
              "register": "the register projected", "register+scenario": "the register projected and a loaded scenario"}


def _console_store() -> bool:
    """Whether the store has a console the saved queries and the walk's Cypher are for."""
    return (os.environ.get("KG_STORE") or "neo4j").lower() == "neo4j"


def cypher_list() -> list[dict]:
    """The adapter's saved queries for its console, then the subject's own (queries.toml), each
    with what it needs. Only an adapter with a console has any. The impact walk is listed from the
    register's default start, not the adapter's literal: no module here names a subject's id."""
    try:
        from store_neo4j import SAVED_QUERIES, START_LITERALS   # the Neo4j adapter's; another adapter would list its own
    except ImportError:
        SAVED_QUERIES, START_LITERALS = [], {}
    out = []
    generic = list(SAVED_QUERIES)
    starts = {}   # taxonomy -> the register's default, read once
    for q in generic[:1] + _ps().subject.queries + generic[1:]:   # the subject's after the first, as the page always listed them
        needs_text = q.get("needs_text") or NEEDS_TEXT.get(q["needs"]) or f"{q['needs']} loaded"
        q = dict(q, needs_text=needs_text)
        tax = q.get("start")
        if tax in START_LITERALS:   # a query from one register node: listed from the register's default for its taxonomy
            literal = START_LITERALS[tax]
            start = starts.setdefault(tax, register_view.start_default(tax))
            if start:
                q["text"] = q["text"].replace(f"'{literal}'", f"'{start}'")
                q["title"] = q["title"].replace(literal, start)
        out.append(q)
    return out


GUIDE_FORMS = ("rows", "paths")


def guide_path(start: str, form: str) -> str:
    return f"/api/register/impact/{urllib.parse.quote(start)}/guide/{form}"


def guide_html(start: str, form: str, text: str) -> str:
    """A Neo4j Browser guide (task-0025): an article the Browser fetches cross-origin and shows in a
    frame. Its block marked runnable puts its text in the editor on a click, through the Browser's
    own click-to-insert, and runs nothing; the viewer presses play. The edit command of the manual
    (?cmd=edit&arg=) is not used: Browser 5.26.0 sends it before the editor listens."""
    h = html.escape
    what = "one row per edge" if form == "rows" else "the paths, for the graph view"
    return (f'<article class="guide"><h3>Impact of retiring {h(start)}: {what}</h3>\n'
            "<p>A click on the query puts it in the editor. Nothing runs until you press play. "
            "A run wipes the projection: project the register again first.</p>\n"
            f'<pre class="pre-scrollable code runnable">{h(text)}</pre></article>\n')


def browser_play_url(origin: str, path: str) -> str:
    """The store's Browser, connected as the page's own link connects, opening the guide at
    origin+path through the Browser manual's ?cmd=play&arg=<url>. The guide's host must be in the
    Browser's remote content allowlist: localhost by default, KG_DEMO_HOST in docker-compose.yml."""
    host = urllib.parse.urlparse(BROWSER_URL).hostname or "localhost"
    return BROWSER_URL + "/browser/?" + urllib.parse.urlencode(
        {"connectURL": f"bolt://neo4j@{host}:7687", "cmd": "play", "arg": origin + path}, quote_via=urllib.parse.quote)


def impact_view(start: str, origin: str = "http://localhost:8080") -> dict | None:
    """The impact walk from one node, with the walk's Cypher for the id typed when the store has a
    console (task-0024): both forms, and for each the guide the server serves and the Browser link
    that opens it, on the origin the viewer reached (the request's Host). None for an unknown id.
    The id is a node of the register, so it is a plain literal in the query; nothing is run."""
    out = register_view.impact(start)
    if out is None:
        return None
    out["cypher"] = None
    if _console_store():
        try:
            from store_neo4j import impact_cypher
        except ImportError:
            return out
        cy = impact_cypher(start)
        guides = {form: guide_path(start, form) for form in GUIDE_FORMS}
        register_view.with_cypher(out, cy, NEEDS_TEXT["register"], browser={form: browser_play_url(origin, guides[form]) for form in GUIDE_FORMS}, guide=guides)
    return out


def impact_guide(start: str, form: str) -> str | None:
    """The guide of one form for one node, or None when there is no such node or form, or no console."""
    if form not in GUIDE_FORMS or not _console_store() or register_view.impact(start) is None:
        return None
    try:
        from store_neo4j import impact_cypher
    except ImportError:
        return None
    return guide_html(start, form, impact_cypher(start)[form])


# ------------------------------------------------------------------ the store

def store_status() -> dict:
    """What the store holds, through the driver when it is installed."""
    kind = (os.environ.get("KG_STORE") or "neo4j").lower()
    out = {"store": kind, "uri": NEO4J_URI if kind == "neo4j" else "", "browser": BROWSER_URL if kind == "neo4j" else None,
           "reachable": False, "loaded": None, "loaded_subject": None, "census": None, "register": None, "error": None, "subject": _ps().id}
    try:
        with _store() as s:
            d = s.describe()
            acts = s.extraction_activities()
            c = s.census()
            reg = s.register_census()
        out.update(store=d.get("store", kind), uri=d.get("uri", out["uri"]), browser=d.get("browser"), reachable=True,
                   census={"nodes": c["nodes"], "relationships": c["relationships"], "assertions_by_status": c["assertions_by_status"]},
                   loaded=(acts[0].split(":")[2] if acts else None), activities=acts, register=reg)
        # the store holds one scenario; its id is its subject's own, so the scenario names the subject
        out["loaded_subject"] = page_subject.scenario_subject(out["loaded"], SUBJECTS)
    except ImportError:
        out["error"] = "store driver not installed: deterministic and arms modes need it"
        return out
    except Exception as e:  # noqa: BLE001 — the message is the status
        out["error"] = str(e).splitlines()[0][:200]
    return out


def store_gaps(scenario: str) -> dict:
    """Every Gap node with what it concerns, from the running store, only when
    the scenario loaded there is the one on screen (one database, one scenario)."""
    out = {"scenario": scenario, "loaded": None, "match": False, "gaps": [], "error": None}
    try:
        with _store() as s:
            acts = s.extraction_activities()
            out["loaded"] = acts[0].split(":")[2] if acts else None
            if out["loaded"] != scenario:
                return out
            out["gaps"] = s.gaps_with_concerns()
            out["match"] = True
    except ImportError:
        out["error"] = "store driver not installed"
        return out
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e).splitlines()[0][:200]
    return out


# ------------------------------------------------------------------ runs

def _now() -> str:
    """UTC with its offset, so a browser in any zone parses it as the instant it is."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class Runner:
    """One harness subprocess at a time: the community edition serves one
    database, so two loads would race."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.current: dict | None = None
        self.history: list[dict] = []

    def start(self, scenario: str, mode: str, n: int, row: str | None = None, effort: str | None = None) -> dict:
        ps = _ps()   # the subject this run is for: its scenarios, its record, its run folder, the harness's KG_SUBJECT
        if scenario not in ps.scenarios:
            raise ValueError(f"unknown scenario {scenario}")
        if mode not in ("deterministic", "arms"):
            raise ValueError(f"unknown mode {mode}")
        chosen, model_env, deviation = None, {}, False
        if mode == "arms":
            if ps.subject.oracle_script() is None:
                raise ValueError("arms mode needs an oracle: this subject declares none")
            # the row and the effort are checked against the table: an unknown row, a row whose key
            # is unset and an effort the row does not list are refused here, before anything runs
            chosen, model_env, deviation = models.resolve(row, effort, ps.record_model, ps.record_effort, ps.arm_kind)
        with self.lock:
            if self.current and self.current["status"] == "running":
                raise RuntimeError("a run is already in progress; the store is one database")
            stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
            out_dir = RUNS_DIR / ps.id / stamp   # runs/<subject id>/<stamp>/: a run folder names its subject
            k = 2
            while out_dir.exists():
                out_dir = RUNS_DIR / ps.id / f"{stamp}-{k}"
                k += 1
            out_dir.mkdir(parents=True)
            derived = ps.subject.scenarios.get(scenario, {}).get("stage2", {}).get("derived")
            if derived:
                # the record's stage 2 registers an earlier scenario's governed output as the
                # Derived artefact; give the re-run the same object to invalidate, in both
                # modes: the harness reads <out>/<from_scenario>/<file> whether or not the
                # arms are called, and without it a deterministic stage 2 has no Derived
                # node to mark suspect (found by the maintainer's traversal, 2026-11-01)
                src = ps.record_dir / derived["from_scenario"] / derived["file"]
                if src.exists():
                    (out_dir / derived["from_scenario"]).mkdir()
                    shutil.copy(src, out_dir / derived["from_scenario"] / derived["file"])
            cmd = [sys.executable, "run.py", "--scenarios", scenario, "--out", str(out_dir)]
            cmd += ["--deterministic"] if mode == "deterministic" else ["--n", str(n)]
            env = {**os.environ, "KG_SUBJECT": str(ps.root), "KG_NEO4J_URI": NEO4J_URI, "KG_NEO4J_PASSWORD": NEO4J_PASSWORD,
                   "PYTHONUNBUFFERED": "1", "KG_WORKERS": os.environ.get("KG_WORKERS", "2")}
            if (os.environ.get("KG_STORE") or "neo4j").lower() == "rdflib":
                # the in-memory store lives in the run's process; a Turtle file beside the runs lets the
                # page read what the run left (the harness writes it on close, the page reads it on open)
                env.setdefault("KG_RDFLIB_FILE", str(RUNS_DIR / "store.ttl"))
            if mode == "arms":
                env.update(model_env)  # base URL, key variable's name, model and effort, all from the row
            log = out_dir / f"{scenario}-{mode}.log"
            fh = open(log, "w", encoding="utf-8")  # noqa: SIM115 — closed when the process ends
            proc = subprocess.Popen(cmd, cwd=str(HARNESS), stdout=fh, stderr=subprocess.STDOUT, env=env)
            rec = {"id": out_dir.name, "subject": ps.id, "scenario": scenario, "mode": mode, "n": n, "status": "running",
                   "model": chosen["model"] if chosen else None, "effort": model_env.get("KG_ARMS_EFFORT") if chosen else None,
                   "row": chosen["id"] if chosen else None, "host": chosen["host"] if chosen else None,
                   "model_deviation": deviation,
                   "started": _now(), "finished": None, "exit_code": None,
                   "out_dir": str(out_dir), "log": str(log), "source": f"demo-runs/{ps.id}/{out_dir.name}", "cmd": " ".join(cmd)}
            self.current = rec
            threading.Thread(target=self._wait, args=(proc, fh, rec), daemon=True).start()
            return self.describe(rec)

    def _wait(self, proc, fh, rec) -> None:
        code = proc.wait()
        fh.close()
        rec.update(status="done" if code == 0 else "failed", exit_code=code, finished=_now())
        self.history.append(rec)

    def describe(self, rec: dict | None = None) -> dict | None:
        rec = rec or self.current
        if not rec:
            return None
        out = dict(rec)
        # elapsed is computed here, not in the browser: the browser's clock and zone are not ours
        end = dt.datetime.fromisoformat(rec["finished"]) if rec.get("finished") else dt.datetime.now(dt.timezone.utc)
        out["elapsed_s"] = int((end - dt.datetime.fromisoformat(rec["started"])).total_seconds())
        try:
            text = Path(rec["log"]).read_text(encoding="utf-8")
        except OSError:
            text = ""
        out["log_text"] = text[-20000:]
        return out


RUNNER = Runner()


def list_runs() -> list[dict]:
    """The current subject's runs, runs/<subject id>/<stamp>/, then any from before that layout at
    runs/<stamp>/ holding one of its scenarios; the id is the path under runs/."""
    ps, out = _ps(), []
    for base, prefix in ((RUNS_DIR / ps.id, f"{ps.id}/"), (RUNS_DIR, "")):
        if not base.exists():
            continue
        for d in sorted(base.iterdir(), reverse=True):
            if not d.is_dir():
                continue
            scenarios = sorted(p.name for p in d.iterdir() if p.is_dir() and p.name in ps.scenarios and (p / "deterministic.json").exists())
            if not scenarios:
                continue
            modes = sorted({("arms" if list((d / s).glob("run*_G.json")) else "deterministic") for s in scenarios})
            out.append({"id": prefix + d.name, "scenarios": scenarios, "modes": modes, "logs": sorted(p.name for p in d.glob("*.log"))})
    return out


# ------------------------------------------------------------------ HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "kg-demo/1"

    def log_message(self, fmt, *args):  # quieter than the default
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8", cors: bool = False) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if cors:   # only a guide: the Browser fetches it from its own origin
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _origin(self) -> str:
        """Where the viewer reached this server, for a link the viewer's browser follows: the
        request's Host, over http (the demo serves no TLS)."""
        return "http://" + (self.headers.get("Host") or f"localhost:{PORT}")

    @staticmethod
    def _guide_parts(path: str) -> tuple[str, str] | None:
        parts = [p for p in path.split("/") if p]
        if parts[:3] == ["api", "register", "impact"] and len(parts) == 6 and parts[4] == "guide":
            return urllib.parse.unquote(parts[3]), parts[5]
        return None

    def do_OPTIONS(self) -> None:  # noqa: N802
        """The preflight of the Browser's cross-origin fetch of a guide (it sends pragma and
        cache-control headers); no other route, and no guide that does not exist, answers one."""
        parts = self._guide_parts(urllib.parse.urlparse(self.path).path)
        if parts is None or impact_guide(*parts) is None:
            return self._json({"error": "not found"}, 404)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", self.headers.get("Access-Control-Request-Headers") or "pragma, cache-control")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        parts = [p for p in u.path.split("/") if p]
        ps = subject_of_request(q)
        if ps is None:   # every route, the page included: a subject this page does not serve is not found
            return self._json({"error": f"no subject {q['subject'][0]!r} here; /api/subjects lists them"}, 404)
        with page_subject.using(ps):
            return self._get(u, q, parts)

    def _get(self, u, q, parts) -> None:
        try:
            if parts == ["api", "subjects"]:
                return self._json({"subjects": subjects_view(), "current": _ps().id})
            if not parts or parts == ["index.html"]:
                return self._send(200, INDEX, "text/html; charset=utf-8")
            if parts == ["health"]:
                return self._json({"ok": True})
            if parts[:2] == ["api", "scenarios"]:
                st = store_status()
                return self._json({"scenarios": views.scenario_list(RUNS_DIR), "store": st,
                                   "page": {"title": _ps().subject.page.get("title", ""), "subtitle": _ps().subject.page.get("subtitle", "")},
                                   "arms_enabled": arms_enabled(), "model_rows": model_rows(),
                                   "record_model": _ps().record_model, "record_effort": _ps().record_effort,
                                   "deterministic_enabled": st["reachable"],
                                   "runs_dir": str(RUNS_DIR), "run": RUNNER.describe()})
            if parts[:2] == ["api", "results"] and len(parts) == 3:
                sc = parts[2]
                source = q.get("source", [views.default_source(sc)])[0]
                view = views.build(sc, source, RUNS_DIR)
                view["cascade"] = {arm: cascade.render(view["systemic"], arm, title=f"{sc}, arm {arm}") for arm in ("G", "B")}
                if register_view.has_map():   # a subject with no register map has no footprint
                    view["footprint"] = register_view.footprint(view)
                    view["details"]["footprint"] = view["footprint"]["panel"]
                else:
                    view["footprint"] = None
                return self._json(view)
            if parts == ["api", "store"]:
                return self._json(store_status())
            if parts == ["api", "register"]:
                today = q.get("today", [None])[0]
                if today not in (None, "wall") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", today):
                    return self._json({"error": "today must be 'wall' or YYYY-MM-DD"}, 400)
                return self._json(register_view.build(today))
            if parts[:3] == ["api", "register", "footprint"] and len(parts) == 4 and parts[3] in views.SCENARIOS:
                if not register_view.has_map():
                    return self._json({"error": f"the {_ps().id} subject maps no key onto the register: no footprint"}, 404)
                sc = parts[3]
                source = q.get("source", [views.default_source(sc)])[0]
                return self._json(register_view.footprint(views.build(sc, source, RUNS_DIR)))
            if parts[:3] == ["api", "register", "ref"] and len(parts) == 5:
                kind, ident = parts[3], urllib.parse.unquote(parts[4])
                sc = q.get("scenario", [None])[0]
                if kind not in register_view.REF_KINDS or (sc is not None and sc not in views.SCENARIOS):
                    return self._json({"error": "unknown reference kind or scenario"}, 400)
                view = views.build(sc, q.get("source", [views.default_source(sc)])[0], RUNS_DIR) if sc else None
                r = register_view.ref(kind, ident, view)
                if r is None:
                    return self._json({"error": f"no {kind} {ident} in the register"}, 404)
                return self._json(r)
            if self._guide_parts(u.path) is not None:
                start, form = self._guide_parts(u.path)
                guide = impact_guide(start, form)
                if guide is None:
                    return self._json({"error": f"no guide {form} for {start}"}, 404)
                return self._send(200, guide.encode("utf-8"), "text/html; charset=utf-8", cors=True)
            if parts[:3] == ["api", "register", "impact"] and len(parts) == 4:
                out = impact_view(parts[3], self._origin())
                return self._json(out) if out is not None else self._json({"error": f"no such node: {parts[3]}"}, 404)
            if parts[:2] == ["api", "gaps"] and len(parts) == 3 and parts[2] in views.SCENARIOS:
                return self._json(store_gaps(parts[2]))
            if parts == ["api", "cypher"]:
                return self._json(cypher_list())
            if parts == ["api", "runs"]:
                return self._json({"runs": list_runs(), "current": RUNNER.describe()})
            if parts == ["api", "run"]:
                return self._json(RUNNER.describe() or {"status": "idle"})
            if parts[:2] == ["api", "cascade"] and len(parts) == 4:
                return self._send(200, cascade.render(views.SYSTEMIC[parts[2]], parts[3]).encode("utf-8"), "image/svg+xml")
            return self._json({"error": "not found"}, 404)
        except FileNotFoundError as e:
            return self._json({"error": str(e)}, 404)
        except KeyError as e:
            return self._json({"error": f"unknown: {e}"}, 404)
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 500)

    def do_POST(self) -> None:  # noqa: N802
        u = urllib.parse.urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "body must be JSON"}, 400)
        q = urllib.parse.parse_qs(u.query)
        ps = subject_of_request(q, body)
        if ps is None:
            return self._json({"error": "no such subject here; /api/subjects lists them"}, 404)
        with page_subject.using(ps):
            return self._post(parts, body)

    def _post(self, parts, body) -> None:
        if parts == ["api", "register", "project"]:
            # the projection: derived, in its own namespace, never the record; a run wipes it
            if RUNNER.current and RUNNER.current["status"] == "running":
                return self._json({"error": "a run is in progress; it wipes the store, so project after it ends"}, 409)
            try:
                return self._json(register_project.project(_store()))
            except ImportError:
                return self._json({"error": "neo4j driver not installed"}, 503)
            except Exception as e:  # noqa: BLE001 — the message is the status
                return self._json({"error": str(e).splitlines()[0][:200]}, 503)
        if parts == ["api", "run"]:
            try:
                rec = RUNNER.start(str(body.get("scenario", "")), str(body.get("mode", "")), int(body.get("n", 1)),
                                   row=(str(body["row"]) if body.get("row") else None),
                                   effort=(str(body["effort"]) if body.get("effort") is not None else None))
                return self._json(rec, 202)
            except (ValueError, RuntimeError) as e:
                return self._json({"error": str(e)}, 409 if isinstance(e, RuntimeError) else 400)
        return self._json({"error": "not found"}, 404)


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"kg demo on http://0.0.0.0:{PORT}  store {NEO4J_URI}  runs {RUNS_DIR}", flush=True)
    httpd.serve_forever()



_COMPAT = {"RECORD": "record_dir", "RECORD_MODEL": "record_model", "RECORD_EFFORT": "record_effort", "ARM_KIND": "arm_kind", "SUBJECT": "subject"}


def __getattr__(name: str):
    """The names this module once filled at import, read from the current subject when asked for."""
    if name in _COMPAT:
        return getattr(_ps(), _COMPAT[name])
    raise AttributeError(f"module 'server' has no attribute {name!r}")


if __name__ == "__main__":
    main()

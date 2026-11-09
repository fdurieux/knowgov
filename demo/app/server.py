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
    KG_PAGE_LISTEN    the address the server listens on (127.0.0.1; the image sets 0.0.0.0, and
                      compose publishes the port on KG_BIND only)
    KG_BIND           the host address compose publishes the page on (127.0.0.1 unless widened);
                      with KG_PAGE_LISTEN it decides whether the page reaches beyond this machine
    KG_PAGE_TOKEN     the bearer token every state-changing request (POST: a run, the register's
                      projection) must carry; without it a page published beyond this machine
                      refuses them (task-0096). Read-only GETs stay open
"""

from __future__ import annotations

import datetime as dt
import html
import ipaddress
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
import build_identity  # noqa: E402  (task-0227: which knowgov this is, read once at start)
import dates  # noqa: E402  (task-0262: one strict YYYY-MM-DD parse)
import settings  # noqa: E402  (task-0264: the numeric settings and tokens, one parser)
import execution  # noqa: E402  (task-0141.05: model output runs in the contained worker, or nowhere)
import page_subject  # noqa: E402  (the subject as a value: task-0032.01)
import http_boundary  # noqa: E402  (the HTTP trust boundary and limits, task-0141.03, task-0141.04)
import runs_index  # noqa: E402  (the one reader of the run folders, shared with the MCP server: task-0128)
import key_check  # noqa: E402  (task-0171: each row's key checked by the endpoint's model listing, no tokens)
from subject import Subject, stamp as subject_stamp  # noqa: E402
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
                          and _listed(d))   # a fixture (listed = false) is skipped in a scan
    return out


# task-0150 (doc-0021 G3): the list follows the folders while the page runs. A subject is built once per
# manifest version (its subject.toml's path and mtime) and reused while that is unchanged, so a rescan
# rebuilds only what was added or edited; a manifest that does not load is left out and logged, not a 500.
_BUILT: dict[str, tuple[int, object]] = {}
_SCAN_LOCK = threading.Lock()
_SIGNATURE = None


def _of(root: Path):
    """The subject at ``root``, rebuilt when its subject.toml or scenarios.toml moves (task-0206)."""
    root = Path(root).resolve()
    if not (root / "subject.toml").exists():
        raise FileNotFoundError(f"{root} holds no subject.toml")
    now = subject_stamp(root)
    hit = _BUILT.get(str(root))
    if hit and hit[0] == now:
        return hit[1]
    ps = page_subject.of(Subject(root))
    _BUILT[str(root)] = (now, ps)
    return ps


def _listed(root: Path) -> bool:
    try:
        return _of(root).listed
    except Exception as e:  # noqa: BLE001 - one manifest that does not load leaves the others served
        print(f"subjects: {root} left out: {type(e).__name__}: {e}", file=sys.stderr)
        return False


def _signature() -> tuple:
    """Every manifest the listing could read, with its mtime: a change in it is a change in the list."""
    raw = os.environ.get("KG_SUBJECTS") or str(ROOT / "subjects")
    found = []
    for part in [*re.split(r"[,%s]" % re.escape(os.pathsep), raw), os.environ.get("KG_SUBJECT") or ""]:
        root = Path(part.strip())
        if not part.strip() or not root.is_dir():
            continue
        for m in [root / "subject.toml"] if (root / "subject.toml").exists() else sorted(root.glob("*/subject.toml")):
            found.append((str(m), subject_stamp(m.parent)))   # subject.toml and scenarios.toml (task-0206)
    return tuple(found)


def refresh_subjects() -> None:
    """Rebuild SUBJECTS and SUBJECT_BY_ID when a manifest was added, edited or removed since the last
    look: a new subject is served, and a removed one no longer listed, without a restart."""
    global SUBJECTS, SUBJECT_BY_ID, _SIGNATURE
    sig = _signature()
    if sig == _SIGNATURE:
        return
    with _SCAN_LOCK:
        if sig == _SIGNATURE:
            return
        try:
            listed = _load_subjects()
        except Exception as e:  # noqa: BLE001 - a manifest that does not load: keep serving the others
            print(f"subjects: rescan kept the previous list: {type(e).__name__}: {e}", file=sys.stderr)
            listed = SUBJECTS
        SUBJECTS, SUBJECT_BY_ID, _SIGNATURE = listed, {ps.id: ps for ps in listed}, sig


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
        try:
            ps = _of(root)
        except Exception as e:  # noqa: BLE001 - one manifest that does not load leaves the others served
            print(f"subjects: {root} left out: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        if ps.id not in seen:
            seen.add(ps.id)
            listed.append(ps)
    if named:
        first = [ps for ps in listed if ps.root.resolve() == Path(named).resolve()]
        listed = first + [ps for ps in listed if ps not in first]
    if os.environ.get("KG_SUBJECTS"):
        return listed   # the instance's own subjects only: none loads, none is served (task-0206, doc-0030 P3)
    return listed or [page_subject.current()]


SUBJECTS = _load_subjects()
SUBJECT_BY_ID = {ps.id: ps for ps in SUBJECTS}
_SIGNATURE = _signature()


def subjects_view() -> list[dict]:
    """What the header drop-down lists: id, name and the page title of each subject, the default first."""
    refresh_subjects()
    return [{"id": ps.id, "name": ps.subject.name, "title": ps.subject.page.get("title", ""), "default": i == 0}
            for i, ps in enumerate(SUBJECTS)]


def subject_of_request(q: dict, body: dict | None = None):
    """The subject a request names (?subject=, or "subject" in a POST body), the default when it
    names none; None for an id the page does not serve, which every route answers with 404."""
    sid = (q.get("subject") or [None])[0] or ((body or {}).get("subject") if isinstance(body, dict) else None)
    refresh_subjects()
    if not sid:
        return SUBJECTS[0] if SUBJECTS else None
    return SUBJECT_BY_ID.get(str(sid))
import arms  # noqa: E402  (the model endpoint settings; the client is imported only when a call is made)
RUNS_DIR = Path(os.environ.get("KG_DEMO_RUNS", str(ROOT / "runs")))
NEO4J_URI = os.environ.get("KG_NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.environ.get("KG_NEO4J_PASSWORD", "kgpoc2026")
BROWSER_URL = os.environ.get("KG_BROWSER_URL", "http://localhost:7474")


def bolt_port(env=None) -> int:
    """The bolt port the stack publishes for the viewer's Browser (KG_PORT_BOLT, as docker-compose.yml maps
    it), 7687 when unset or not a port: a second stack's links reach its own Neo4j, never the first's."""
    raw = ((os.environ if env is None else env).get("KG_PORT_BOLT") or "").strip()
    return int(raw) if raw.isdigit() and 0 < int(raw) < 65536 else 7687


BOLT_PORT = bolt_port()   # read once at start
try:
    PORT = settings.number("KG_DEMO_PORT")   # 1 to 65535 (task-0264)
except settings.BadSetting:
    PORT = 8080   # main refuses it at start, named, exit 2; an import never fails on it


def _key_verdict(row: dict) -> dict:
    """A row's key verdict from the key check's cache, never a request (task-0171)."""
    return key_check.CHECKER.verdict(row["base_url"], row["key_var"], row.get("model") or "", bool(row.get("gateway")))


def check_keys(wait: float = key_check.WAIT_S, recheck: bool = False) -> None:
    """Check every listed row's key not yet checked under its current value (each endpoint and key
    once), and wait a bounded time for the checks in flight. Nothing is sent before main() enables
    the checker, nor with KG_KEY_CHECK=off."""
    ps = _ps()
    key_check.CHECKER.ensure(models.endpoints(models.listed_rows(ps.record_model, ps.record_effort)),
                             wait=wait, recheck=recheck)


def model_rows() -> list[dict]:
    """The Arms call drop-down's rows as the page receives them: no key, no price (task-0029), each
    with its key verdict (task-0171)."""
    ps = _ps()
    check_keys()
    return [models.public(r) for r in models.rows(ps.record_model, ps.record_effort, ps.arm_kind, check=_key_verdict)]


def arms_enabled() -> bool:
    """The arms are on when the subject has an oracle to grade a reply and at least one row is
    available, its key variable set; no key, no call, nothing sent."""
    return _ps().subject.oracle_script() is not None and any(r["available"] for r in model_rows())


def execution_view() -> dict:
    """Whether model output may run now, as an arms run would find it: ``execution.refusal()``'s answer
    (the instance guard, the backend, the worker's attestation), never a copy of its logic. The page's
    Arms chip and button read it beside ``arms_enabled``, which counts keys only."""
    why = execution.refusal()
    return {"ok": why is None, "why": why}


def worker_view() -> dict:
    """Where model output would run, as the worker attested it: ``execution.placement()``'s answer (the
    backend, the attestation, the host facts the worker read from inside its container and the cloud the
    app reads from its kernel release, labelled as a reading), never a copy of its logic (task-0169)."""
    return execution.placement()
INDEX = (HERE / "index.html").read_bytes()
KNOWGOV = build_identity.identity(ROOT)   # {version, commit, describe}, each None when unknown; once, at start (task-0227)
NO_SUBJECT = ("no subject is served: KG_SUBJECTS names no subject.toml that loads, and an instance's page serves its own "
              "subjects only; the log names each one left out and why")

# Saved Cypher for the store panel. Each runs in Neo4j Browser against the
# scenario currently loaded; the comment on each says which scenario shows it.
def _store(timeout: float = 3, access: str = "read"):
    """A store through the port, for the page's short reads (a read handle, which never publishes;
    task-0141.02), or for the register projection (``access="write"``, waiting at most ``timeout`` for
    another writer); raises when unreachable or busy."""
    from store import open_store  # the harness's port; the adapter needs its driver, in the image
    _store_file_default()
    return open_store(connection_timeout=timeout, instance=_ps().id, access=access)


def _read(fn, timeout: float = 3):
    """One logical read of the page on one published generation (task-0141.06): ``fn(handle)`` on a
    read handle from ``_store``, run again on a fresh one when a publication lands during it, at most
    ``KG_STORE_READ_ATTEMPTS`` times (3), as store.read does."""
    from store import StoreChanged, read_attempts
    attempts = read_attempts()
    for attempt in range(attempts):
        with _store(timeout) as s:
            try:
                return fn(s)
            except StoreChanged:
                if attempt == attempts - 1:
                    raise


def _store_file_default() -> None:
    if (os.environ.get("KG_STORE") or "neo4j").lower() == "rdflib" and not os.environ.get("KG_RDFLIB_FILE"):
        os.environ["KG_RDFLIB_FILE"] = str(RUNS_DIR / "store.ttl")


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


WALK_FORMS = ("rows", "paths")                   # the walk's two forms (task-0024)
GUIDE_FORMS = WALK_FORMS + ("statements",)       # and the statements view's query (task-0078)
GUIDE_WHAT = {"rows": "one row per edge", "paths": "the paths, for the graph view",
              "statements": "the assertions its cited anchors name"}


def variant_of(walk: str = "dependants", children: bool = False) -> str:
    """The name a walk and its children option go by in a guide's path (task-0112): dependants,
    dependants-children, realisers, realisers-children. A path segment, not a query string: the
    Browser reads the play command's argument only up to the first ``&``."""
    return walk + ("-children" if children else "")


def guide_path(start: str, form: str, variant: str = "dependants") -> str:
    """The default walk's guide keeps its path; another variant names itself before ``guide``."""
    mid = "" if variant == "dependants" or form == "statements" else f"/{variant}"
    return f"/api/register/impact/{urllib.parse.quote(start)}{mid}/guide/{form}"


GUIDE_TITLE = {"dependants": "Impact of retiring {}", "dependants-children": "Impact of retiring {} and its descendants",
               "realisers": "What realises {}", "realisers-children": "What realises {} and its descendants"}


def guide_html(start: str, form: str, text: str, variant: str = "dependants") -> str:
    """A Neo4j Browser guide (task-0025): an article the Browser fetches cross-origin and shows in a
    frame. Its block marked runnable puts its text in the editor on a click, through the Browser's
    own click-to-insert, and runs nothing; the viewer presses play. The edit command of the manual
    (?cmd=edit&arg=) is not used: Browser 5.26.0 sends it before the editor listens."""
    h = html.escape
    what = GUIDE_WHAT[form]
    return (f'<article class="guide"><h3>{GUIDE_TITLE[variant].format(h(start))}: {what}</h3>\n'
            "<p>A click on the query puts it in the editor. Nothing runs until you press play. "
            "A run wipes the projection: project the register again first.</p>\n"
            f'<pre class="pre-scrollable code runnable">{h(text)}</pre></article>\n')


def browser_play_url(origin: str, path: str) -> str:
    """The store's Browser, connected as the page's own link connects, opening the guide at
    origin+path through the Browser manual's ?cmd=play&arg=<url>. The guide's host must be in the
    Browser's remote content allowlist: localhost by default, KG_DEMO_HOST in docker-compose.yml."""
    return BROWSER_URL + "/browser/?" + urllib.parse.urlencode(
        {"connectURL": _bolt_url(), "cmd": "play", "arg": origin + path}, quote_via=urllib.parse.quote)


def _bolt_url() -> str:
    """bolt://neo4j@<the Browser's host>:<the bolt port the stack publishes>."""
    return f"bolt://neo4j@{urllib.parse.urlparse(BROWSER_URL).hostname or 'localhost'}:{BOLT_PORT}"


def browser_connect_url() -> str:
    """The store panel's Browser link, connected to this stack's bolt port (task-0230's notes (c))."""
    return BROWSER_URL + "/browser/?connectURL=" + _bolt_url()


def node_statements(start: str) -> dict:
    """The port's register_node_statements from one node (task-0046, task-0047): ``rows`` when the
    store is reachable with the register projected and a scenario loaded, else None and ``missing``,
    one of driver, store, register or scenario. Any adapter: the port's read, no console needed."""
    out = {"rows": None, "missing": None}
    def read(s):
        if s.register_census() is None:
            return {"rows": None, "missing": "register"}
        if not s.extraction_activities():
            return {"rows": None, "missing": "scenario"}
        return {"rows": s.register_node_statements(start), "missing": None}
    try:
        out.update(_read(read))
    except ImportError:
        out["missing"] = "driver"
    except Exception:  # noqa: BLE001 — unreachable, whatever the driver's class
        out["missing"] = "store"
    return out


def impact_view(start: str, origin: str = "http://localhost:8080", statements: bool = True,
                walk: str = "dependants", children: bool = False) -> dict | None:
    """The impact walk from one node, with the walk's Cypher for the id typed when the store has a
    console (task-0024): both forms, and for each the guide the server serves and the Browser link
    that opens it, on the origin the viewer reached (the request's Host). None for an unknown id or
    walk. Either of the register's walks, with or without its children option (task-0112).
    The id is a node of the register, so it is a plain literal in the query; nothing is run but the
    port's own read of the assertions the node's cited anchors name, shown beside the walk (task-0047)."""
    out = register_view.impact(start, walk, children)
    if out is None:
        return None
    if statements:
        register_view.with_statements(out, node_statements(start), NEEDS_TEXT["register+scenario"])
    out["cypher"] = None
    if _console_store():
        try:
            from store_neo4j import impact_cypher, node_statements_cypher
        except ImportError:
            return out
        cy = impact_cypher(start, walk, children)
        guides = {form: guide_path(start, form, variant_of(walk, children)) for form in WALK_FORMS}
        register_view.with_cypher(out, cy, NEEDS_TEXT["register"], browser={form: browser_play_url(origin, guides[form]) for form in WALK_FORMS}, guide=guides)
        if statements:
            guide = guide_path(start, "statements")
            register_view.with_statements_cypher(out, node_statements_cypher(start), browser=browser_play_url(origin, guide), guide=guide)
    return out


def impact_guide(start: str, form: str, variant: str = "dependants") -> str | None:
    """The guide of one form for one node and walk variant, or None when there is no such node, form
    or variant, or no console. The statements view's guide has the default variant only."""
    if form not in GUIDE_FORMS or not _console_store() or register_view.impact(start) is None:
        return None
    try:
        from store_neo4j import IMPACT_VARIANTS, impact_cypher, node_statements_cypher
    except ImportError:
        return None
    if variant not in IMPACT_VARIANTS or (form == "statements" and variant != "dependants"):
        return None
    if form == "statements":
        return guide_html(start, form, node_statements_cypher(start))
    return guide_html(start, form, impact_cypher(start, *IMPACT_VARIANTS[variant])[form], variant)


# ------------------------------------------------------------------ the store

def store_named(env=None) -> str:
    """The store in use as the startup line names it (task-0272): the bolt URL under neo4j, the rdflib file
    (or "in memory") under rdflib, never a bolt URL the page does not use."""
    env = os.environ if env is None else env
    kind = (env.get("KG_STORE") or "neo4j").lower()
    if kind == "neo4j":
        return env.get("KG_NEO4J_URI", "bolt://localhost:7687")
    if kind == "rdflib":
        return f"rdflib {env.get('KG_RDFLIB_FILE') or 'in memory'}"
    return kind


def store_status() -> dict:
    """What the store holds, through the driver when it is installed."""
    kind = (os.environ.get("KG_STORE") or "neo4j").lower()
    out = {"store": kind, "uri": NEO4J_URI if kind == "neo4j" else "", "browser": BROWSER_URL if kind == "neo4j" else None,
           "browser_connect": browser_connect_url() if kind == "neo4j" else None,
           "reachable": False, "loaded": None, "loaded_subject": None, "census": None, "register": None, "error": None, "subject": _ps().id}
    try:
        d, h, acts, c, reg = _read(lambda s: (s.describe(), s.held(), s.extraction_activities(), s.census(), s.register_census()))
        out.update(store=d.get("store", kind), uri=d.get("uri", out["uri"]), browser=d.get("browser"), reachable=True,
                   census={"nodes": c["nodes"], "relationships": c["relationships"], "assertions_by_status": c["assertions_by_status"]},
                   loaded=(h["scenario"] if h else None), activities=acts, register=reg)
        # whose load it is: the subject the load recorded (task-0195), never the scenario id, which two
        # subjects may share; a store loaded before task-0195 reads unknown but for an only subject
        import held as held_state
        out["loaded_subject"] = held_state.owner(h)
    except ImportError:
        out["error"] = "store driver not installed: deterministic and arms modes need it"
        return out
    except Exception as e:  # noqa: BLE001 — the message is the status
        out["error"] = str(e).splitlines()[0][:200]
        _mark_busy(out, e)
    return out


def _mark_busy(out: dict, e: Exception) -> None:
    """A store that is held or was republished through every read (task-0141.06): ``busy``, so the route
    answers 503 with Retry-After rather than a store that is simply unreachable."""
    from store import StoreBusy
    if isinstance(e, StoreBusy):
        out["busy"] = True


def _busy_json(handler, out: dict) -> None:
    if out.get("busy"):
        return handler._json(out, 503, {"Retry-After": str(BUSY_RETRY_AFTER)})
    return handler._json(out)


BUSY_RETRY_AFTER = 1   # seconds: a publication or a held writer lock, both short-lived


def store_gaps(scenario: str) -> dict:
    """Every Gap node with what it concerns, from the running store, only when
    the scenario loaded there is the one on screen (one database, one scenario)."""
    out = {"scenario": scenario, "loaded": None, "match": False, "gaps": [], "error": None}
    import held as held_state

    def read(s):
        h = s.held()   # task-0195: the page's subject's own load, by the subject the load recorded
        mine = held_state.scenario_for(h, _ps().id)
        return (h["scenario"] if h else None), mine, (s.gaps_with_concerns() if mine == scenario else [])
    try:
        out["loaded"], mine, out["gaps"] = _read(read)
        out["match"] = mine == scenario
    except ImportError:
        out["error"] = "store driver not installed"
        return out
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e).splitlines()[0][:200]
        _mark_busy(out, e)
    return out


# ------------------------------------------------------------------ runs

def _now() -> str:
    """UTC with its offset, so a browser in any zone parses it as the instant it is."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


RUN_BY = ("page", "mcp")   # who asked for a run: the page's buttons, or knowgov-runs (decision-0008)
# what run.json keeps of a run's record (task-0127): no environment, no log text, no absolute path,
# so nothing secret and nothing of the host; the record itself never holds a key or the page's token
RUN_JSON_FIELDS = ("id", "subject", "scenario", "mode", "n", "row", "model", "effort", "host", "model_deviation",
                   "as_of", "by", "started", "heartbeat_at", "finished", "status", "exit_code", "error", "source")
RUN_JSON_VERSION = runs_index.RUN_JSON_VERSION   # 2: heartbeat_at, rewritten every HEARTBEAT_S while running


def run_json(rec: dict) -> dict:
    """The run.json a run folder carries for its record (harness/schemas/run.schema.json)."""
    out = {"version": RUN_JSON_VERSION, **{k: rec.get(k) for k in RUN_JSON_FIELDS}}
    out["log"] = Path(rec["log"]).name if rec.get("log") else None
    return out


_RUN_JSON_LOCK = threading.Lock()   # the heartbeat and the end write never interleave


def _write_json(folder: Path, j: dict) -> None:
    """Write <folder>/run.json whole or not at all: a reader never sees half a file."""
    target = folder / "run.json"
    tmp = target.with_name("run.json.tmp")
    tmp.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def write_run_json(rec: dict) -> None:
    with _RUN_JSON_LOCK:
        _write_json(Path(rec["out_dir"]), run_json(rec))


def beat(rec: dict) -> bool:
    """Rewrite a running run.json with a fresh heartbeat_at; False once the run has ended (nothing written)."""
    with _RUN_JSON_LOCK:
        if rec.get("status") != "running":
            return False
        rec["heartbeat_at"] = _now()
        _write_json(Path(rec["out_dir"]), run_json(rec))
        return True


read_run_json = runs_index.read_run_json


def close_stale_runs() -> list[str]:
    """At start: a running run.json whose heartbeat is stale belongs to a page that stopped mid-run; it is
    closed as failed ("page restarted"), so no reader waits on it."""
    return runs_index.close_stale(RUNS_DIR, dt.datetime.fromisoformat(_now()), _write_json)


class Runner:
    """One harness subprocess at a time: the community edition serves one
    database, so two loads would race."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.current: dict | None = None
        self.history: list[dict] = []
        self.waiters: list[threading.Thread] = []   # one per started run; join() waits for their end writes

    def start(self, scenario: str, mode: str, n: int, row: str | None = None, effort: str | None = None,
              as_of: str | None = None, by: str = "page") -> dict:
        ps = _ps()   # the subject this run is for: its scenarios, its record, its run folder, the harness's KG_SUBJECT
        if by not in RUN_BY:
            raise ValueError(f"by must be one of {list(RUN_BY)}, not {by!r}")
        if scenario not in ps.scenarios:
            raise ValueError(f"unknown scenario {scenario}")
        if mode not in ("deterministic", "arms"):
            raise ValueError(f"unknown mode {mode}")
        if as_of is not None:
            # the date the run's gate reads review currency on (decision-0005); none is the record date
            if not dates.is_date(as_of):   # task-0262: YYYY-MM-DD in ASCII digits, never a week, basic or suffixed form
                raise ValueError(f"as_of {as_of!r} is not a date (YYYY-MM-DD)")
        chosen, model_env, deviation = None, {}, False
        if mode == "arms":
            if ps.subject.oracle_script() is None:
                raise ValueError("arms mode needs an oracle: this subject declares none")
            why = execution.refusal()   # task-0141.07, task-0141.05: no mounted instance beside it, and a confined worker, or the opt-in
            if why:
                raise ValueError(why)
            # the row and the effort are checked against the table: an unknown row, a row whose key
            # is unset or was refused by its endpoint (task-0171: checked first when not yet checked)
            # and an effort the row does not list are refused here, before anything runs
            check_keys()
            chosen, model_env, deviation = models.resolve(row, effort, ps.record_model, ps.record_effort, ps.arm_kind,
                                                          check=_key_verdict)
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
            stage2_derived = None
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
                    # named explicitly: the harness never takes a file it finds in --out (task-0203, R3)
                    stage2_derived = out_dir / derived["from_scenario"] / derived["file"]
            cmd = [sys.executable, "run.py", "--scenarios", scenario, "--out", str(out_dir)]
            cmd += ["--stage2-derived", str(stage2_derived)] if stage2_derived else []
            cmd += ["--deterministic"] if mode == "deterministic" else ["--n", str(n)]
            cmd += ["--as-of", as_of] if as_of else []
            env = {**os.environ, "KG_SUBJECT": str(ps.root), "KG_NEO4J_URI": NEO4J_URI, "KG_NEO4J_PASSWORD": NEO4J_PASSWORD,
                   "PYTHONUNBUFFERED": "1", "KG_WORKERS": os.environ.get("KG_WORKERS", "2")}
            if (os.environ.get("KG_STORE") or "neo4j").lower() == "rdflib":
                # the in-memory store lives in the run's process; a Turtle file beside the runs lets the
                # page read what the run left (the harness writes it on close, the page reads it on open)
                env.setdefault("KG_RDFLIB_FILE", str(RUNS_DIR / "store.ttl"))
            if mode == "arms":
                env.update(model_env)  # base URL, key variable's name, model and effort, all from the row
            log = out_dir / f"{scenario}-{mode}.log"
            rec = {"id": out_dir.name, "subject": ps.id, "scenario": scenario, "mode": mode, "n": n, "status": "running",
                   "model": chosen["model"] if chosen else None, "effort": model_env.get("KG_ARMS_EFFORT") if chosen else None,
                   "row": chosen["id"] if chosen else None, "host": chosen["host"] if chosen else None,
                   "model_deviation": deviation, "as_of": as_of, "by": by,
                   "started": _now(), "heartbeat_at": None, "finished": None, "exit_code": None,
                   "out_dir": str(out_dir), "log": str(log), "source": f"demo-runs/{ps.id}/{out_dir.name}", "cmd": " ".join(cmd)}
            rec["heartbeat_at"] = rec["started"]
            write_run_json(rec)
            fh = None
            try:
                fh = open(log, "w", encoding="utf-8")  # noqa: SIM115 — closed when the process ends
                proc = subprocess.Popen(cmd, cwd=str(HARNESS), stdout=fh, stderr=subprocess.STDOUT, env=env)
            except OSError as e:
                if fh:
                    fh.close()
                # the folder stays, and says the run never ran: a run.json left at running would lie
                rec.update(status="failed", finished=_now(), error=f"the run could not start: {e.strerror or e}")
                write_run_json(rec)
                self.history.append(rec)
                raise RuntimeError(rec["error"]) from None
            self.current = rec
            waiter = threading.Thread(target=self._wait, args=(proc, fh, rec), daemon=True)
            self.waiters.append(waiter)
            waiter.start()
            return self.describe(rec)

    def _wait(self, proc, fh, rec) -> None:
        ended = threading.Event()
        threading.Thread(target=self._heartbeat, args=(rec, ended), daemon=True).start()
        try:
            code = proc.wait()
        finally:
            fh.close()
        with _RUN_JSON_LOCK:   # the end, then no beat after it
            rec.update(status="done" if code == 0 else "failed", exit_code=code, finished=_now())
            _write_json(Path(rec["out_dir"]), run_json(rec))
        ended.set()
        self.history.append(rec)

    @staticmethod
    def _heartbeat(rec: dict, ended: threading.Event, every: float = runs_index.HEARTBEAT_S) -> None:
        """While the run is under way, run.json says so again every ``every`` seconds (task-0128)."""
        while not ended.wait(every):
            if not beat(rec):
                return

    def join(self, timeout: float = 30.0) -> None:
        """Wait until every started run's waiter has written its end: the page never calls it; a test
        whose run folder is a temporary directory does, before the directory goes."""
        for waiter in self.waiters:
            if waiter.is_alive():
                waiter.join(timeout)
            if waiter.is_alive():
                raise TimeoutError(f"a run's waiter is still running after {timeout} s")

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
    runs/<stamp>/ holding one of its scenarios; the id is the path under runs/ (harness/runs_index.py)."""
    return runs_index.list_runs(_ps().subject, RUNS_DIR)


# ------------------------------------------------------------------ who may change state (task-0096)

def _is_loopback(host: str) -> bool:
    host = host.strip().strip("[]")
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def listen_host() -> str:
    """Where this process listens: this machine only unless told (the image says 0.0.0.0)."""
    return os.environ.get("KG_PAGE_LISTEN") or "127.0.0.1"


def exposure() -> str:
    """The widest address the page answers on: compose's KG_BIND when it passes one, else the
    process's own listen address."""
    return os.environ.get("KG_BIND") or listen_host()


def page_token() -> str | None:
    return settings.token("KG_PAGE_TOKEN")   # blank once stripped is no token: writes refuse (task-0264)


def writes_view() -> dict:
    """What the page's JavaScript needs to know before it offers a run: whether a token is asked
    for, and, when writes are refused outright, why. Never the token."""
    return {"token_required": page_token() is not None, "refused": None if page_token() else write_refusal()}


def write_refusal() -> str | None:
    """None when a state-changing request may go ahead without a token, else why it may not."""
    if page_token() or _is_loopback(exposure()):
        return None
    return (f"the page is published on {exposure()}, beyond this machine, and has no login: runs and the "
            "register's projection are refused until KG_PAGE_TOKEN is set in the app's environment "
            "(every such request then carries it as Authorization: Bearer <token>)")


def page_policy(port: int):
    """What the page answers for (task-0141.03, harness/http_boundary.py), from its configuration and
    listener, never from a request: the loopback names on the port it listens on and on the port compose
    publishes it on (KG_PUBLIC_PORT), the viewer's host on that port (KG_DEMO_HOST, as the Browser's
    allowlist already names it), and KG_PAGE_AUTHORITIES; its origins ``http://`` each, plus
    KG_PAGE_ORIGINS (a TLS proxy's ``https://...``). The impact guides, which Neo4j Browser fetches
    from its own origin, also admit the Browser's origin (KG_BROWSER_URL)."""
    import http_boundary
    public = int(os.environ.get("KG_PUBLIC_PORT") or port)
    names = [x for x in (os.environ.get("KG_PAGE_AUTHORITIES") or "").split(",") if x.strip()]
    demo = (os.environ.get("KG_DEMO_HOST") or "").strip()
    if demo:
        names.append(f"{demo}:{public}")
    browser = urllib.parse.urlsplit(os.environ.get("KG_BROWSER_URL", BROWSER_URL))
    guide = [f"{browser.scheme}://{browser.netloc}"] if browser.scheme in ("http", "https") and browser.netloc else []
    return http_boundary.build(listen_host(), [port, public], authorities=",".join(names),
                               origins=os.environ.get("KG_PAGE_ORIGINS", ""), extra_origins={"guide": guide})


def write_guard(headers) -> tuple[int, str, dict] | None:
    """None when a POST may proceed, else (status, message, extra headers), after the Host and Origin
    checks every request passes (Handler._boundary): with KG_PAGE_TOKEN set the request must carry it;
    without it, a page published beyond this machine refuses every write."""
    token = page_token()
    if token:
        if not http_boundary.bearer_matches(headers.get("Authorization"), token):   # scheme any case (task-0272)
            return 401, "this page asks for its token (KG_PAGE_TOKEN): enter it in the Page token box, or send Authorization: Bearer <token>", {"WWW-Authenticate": "Bearer"}
        return None
    why = write_refusal()
    return (403, why, {}) if why else None


# ------------------------------------------------------------------ HTTP

PAGE_MAX_RESPONSE = 8 << 20   # task-0177: 21x the largest response measured, /api/results/S6 on CargoQuote (392 KB)


def page_limits():
    """The page's bounds (task-0141.04): KG_PAGE_MAX_BODY bytes (default 65536; its largest request, a
    run, is under 1 KB), KG_PAGE_READ_TIMEOUT seconds for a request to arrive whole (10),
    KG_PAGE_IDLE_TIMEOUT for one silent wait (5), KG_PAGE_MAX_CONNECTIONS at once (32; more get 503),
    KG_PAGE_MAX_RESPONSE bytes in one response (8 MiB, task-0177; a larger one is a 500 naming it)."""
    import http_boundary
    return http_boundary.Limits.from_env("KG_PAGE", max_body=65536, max_response=PAGE_MAX_RESPONSE)


MAX_RUNS = 5   # a run's n at most, unless KG_PAGE_MAX_RUNS says: the record's own count per arm and scenario


RUN_FIELDS = ("scenario", "mode", "n", "row", "effort", "as_of", "by", "subject")   # POST /api/run's body (task-0281)


def run_request(body: dict) -> dict:
    """A run's fields, typed before anything is chosen or started (task-0141.04): scenario and mode
    strings; n an integer in 1..KG_PAGE_MAX_RUNS (a boolean, a float or a numeric string is refused,
    no longer coerced); row, effort, as_of, by and subject strings when present. A key outside
    ``RUN_FIELDS`` is refused, named (task-0281, decision-0033 choice 7(a)): ``as-of`` for ``as_of`` would
    otherwise run as of the record date without a word."""
    unknown = sorted(set(body) - set(RUN_FIELDS))
    if unknown:
        raise ValueError(f"unknown field(s) {', '.join(map(repr, unknown))}; a run takes {', '.join(RUN_FIELDS)}")
    out = {}
    for k in ("scenario", "mode"):
        v = body.get(k, "")
        if not isinstance(v, str):
            raise ValueError(f"{k} must be a string")
        out[k] = v
    n = body.get("n", 1)
    cap = int(os.environ.get("KG_PAGE_MAX_RUNS") or MAX_RUNS)
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= cap:
        raise ValueError(f"n must be an integer from 1 to {cap}")
    out["n"] = n
    for k in ("row", "effort", "as_of", "by", "subject"):
        v = body.get(k)
        if v is not None and not isinstance(v, str):
            raise ValueError(f"{k} must be a string")
        out[k] = v
    return out


class Handler(http_boundary.BoundedMixin, BaseHTTPRequestHandler):
    server_version = "kg-demo/1"
    default_limits = None   # a plain server (a test) gets page_limits() through _limits

    def _limits(self):
        return getattr(self.server, "limits", None) or page_limits()

    def log_message(self, fmt, *args):  # quieter than the default
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8", cors: bool = False,
              extra: dict | None = None) -> None:
        cap = self._limits().max_response
        if len(body) > cap:   # task-0177: refused whole, never truncated, the setting named
            import http_boundary
            reason = http_boundary.over_cap("KG_PAGE_MAX_RESPONSE", len(body), cap)
            sys.stderr.write(f"page: {self.path}: {reason}\n")
            code, ctype, cors, extra = 500, "application/json; charset=utf-8", False, None
            body = json.dumps({"error": reason, "setting": "KG_PAGE_MAX_RESPONSE", "limit": cap, "size": len(body)}).encode("utf-8")
        self.send_response(code)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
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
    def _guide_parts(path: str) -> tuple[str, str, str] | None:
        parts = [p for p in path.split("/") if p]
        if parts[:3] == ["api", "register", "impact"] and len(parts) == 6 and parts[4] == "guide":
            return urllib.parse.unquote(parts[3]), parts[5], "dependants"
        if parts[:3] == ["api", "register", "impact"] and len(parts) == 7 and parts[5] == "guide" and parts[4] != "dependants":
            return urllib.parse.unquote(parts[3]), parts[6], parts[4]
        return None

    def _boundary(self) -> bool:
        """Host and Origin checked on every request, each on its own (task-0141.03): False, answered,
        when refused. A guide's route also admits the Browser's origin."""
        import http_boundary
        route = "guide" if self._guide_parts(urllib.parse.urlparse(self.path).path) else None
        refused = http_boundary.check(page_policy(self.server.server_address[1]), self.headers, route)
        if refused:   # closed through the shared refusal (task-0196 M3)
            self.refuse(lambda: self._json({"error": refused[1]}, refused[0]))
            return False
        return True

    def do_OPTIONS(self) -> None:  # noqa: N802
        """The preflight of the Browser's cross-origin fetch of a guide (it sends pragma and
        cache-control headers); no other route, and no guide that does not exist, answers one."""
        self.arrived()   # no body: the request is in (task-0141.04)
        if not self._boundary():
            return
        parts = self._guide_parts(urllib.parse.urlparse(self.path).path)
        if parts is None or impact_guide(*parts) is None:
            return self._json({"error": "not found"}, 404)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", self.headers.get("Access-Control-Request-Headers") or "pragma, cache-control")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, obj, code: int = 200, extra: dict | None = None) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"), extra=extra)

    def do_GET(self) -> None:  # noqa: N802
        self.arrived()   # no body: the request is in (task-0141.04)
        if not self._boundary():
            return
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        parts = [p for p in u.path.split("/") if p]
        ps = subject_of_request(q)
        if ps is None and not SUBJECTS:   # task-0206: KG_SUBJECTS names no subject that loads; the page says so
            if parts in ([], ["index.html"], ["api", "subjects"]):
                return self._send(200, INDEX, "text/html; charset=utf-8") if parts != ["api", "subjects"] else self._json({"subjects": [], "current": None, "knowgov": KNOWGOV})
            return self._json({"error": NO_SUBJECT}, 404)
        if ps is None:   # every route, the page included: a subject this page does not serve is not found
            return self._json({"error": f"no subject {q['subject'][0]!r} here; /api/subjects lists them"}, 404)
        with page_subject.using(ps):
            return self._get(u, q, parts)

    def _get(self, u, q, parts) -> None:
        try:
            if parts == ["api", "subjects"]:
                return self._json({"subjects": subjects_view(), "current": _ps().id, "knowgov": KNOWGOV})
            if not parts or parts == ["index.html"]:
                return self._send(200, INDEX, "text/html; charset=utf-8")
            if parts == ["health"]:
                return self._json({"ok": True})
            if parts[:2] == ["api", "scenarios"]:
                st = store_status()
                return self._json({"scenarios": views.scenario_list(RUNS_DIR), "store": st,
                                   "page": {"title": _ps().subject.page.get("title", ""), "subtitle": _ps().subject.page.get("subtitle", "")},
                                   "arms_enabled": arms_enabled(), "execution": execution_view(), "worker": worker_view(), "model_rows": model_rows(),
                                   "record_model": _ps().record_model, "record_effort": _ps().record_effort,
                                   "deterministic_enabled": st["reachable"], "writes": writes_view(),
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
                return _busy_json(self, store_status())
            if parts == ["api", "register"]:
                today = q.get("today", [None])[0]
                if today not in (None, "wall") and not dates.is_date(today):   # task-0262
                    return self._json({"error": f"today {today!r} must be 'wall' or a date (YYYY-MM-DD)"}, 400)
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
                start, form, variant = self._guide_parts(u.path)
                guide = impact_guide(start, form, variant)
                if guide is None:
                    return self._json({"error": f"no guide {form} for {start}"}, 404)
                return self._send(200, guide.encode("utf-8"), "text/html; charset=utf-8", cors=True)
            if parts[:3] == ["api", "register", "impact"] and len(parts) == 4:
                walk, children = q.get("walk", ["dependants"])[0], q.get("children", ["0"])[0]
                if walk not in register_view.WALKS or children not in ("0", "1", "false", "true"):
                    return self._json({"error": f"walk must be one of {list(register_view.WALKS)}, children 0 or 1"}, 400)
                out = impact_view(parts[3], self._origin(), walk=walk, children=children in ("1", "true"))
                return self._json(out) if out is not None else self._json({"error": f"no such node: {parts[3]}"}, 404)
            if parts[:2] == ["api", "gaps"] and len(parts) == 3 and parts[2] in views.SCENARIOS:
                return _busy_json(self, store_gaps(parts[2]))
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
        # every POST changes state (a run reloads the store and may call the model; the projection
        # writes the store): the guards come before the body is read (task-0096, task-0141.03)
        if not self._boundary():
            return
        refused = write_guard(self.headers)
        if refused:   # answered before the body is read: closed, so the body is never a second request (M3)
            code, why, extra = refused
            return self.refuse(lambda: self._json({"error": why}, code, extra))
        u = urllib.parse.urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        try:   # framing before a byte is read, then a JSON object (task-0141.04); every POST sends one
            body = http_boundary.read_json_body(self, self._limits())
            self.arrived(body=True)
        except http_boundary.Refused as e:
            return self.refuse(lambda: self._json({"error": e.reason}, e.status))
        q = urllib.parse.parse_qs(u.query)
        if body.get("subject") is not None and not isinstance(body["subject"], str):
            return self._json({"error": "subject must be a string"}, 400)
        ps = subject_of_request(q, body)
        if ps is None:
            return self._json({"error": NO_SUBJECT if not SUBJECTS else "no such subject here; /api/subjects lists them"}, 404)
        with page_subject.using(ps):
            return self._post(parts, body)

    def _post(self, parts, body) -> None:
        if parts == ["api", "register", "project"]:
            # the projection: derived, in its own namespace, never the record; a run wipes it. Decided and
            # done under the runner's lock, so no run starts between the check and the projection; the
            # store's own writer lock (lease or file lock) serialises it with any other writer (task-0141.06)
            from store import StoreBusy
            try:
                with RUNNER.lock:
                    if RUNNER.current and RUNNER.current["status"] == "running":
                        return self._json({"error": "a run is in progress; it wipes the store, so project after it ends"}, 409)
                    return self._json(register_project.project(_store(access="write")))
            except StoreBusy as e:
                return self._json({"error": str(e).splitlines()[0][:200]}, 409)
            except ImportError:
                return self._json({"error": "neo4j driver not installed"}, 503)
            except Exception as e:  # noqa: BLE001 — the message is the status
                return self._json({"error": str(e).splitlines()[0][:200]}, 503)
        if parts == ["api", "models", "check"]:
            # task-0171: check every row's key again (the listing, no tokens); behind the write guard, as
            # it sends a request to each endpoint; the rows come back with their verdicts
            check_keys(recheck=True)
            return self._json({"model_rows": model_rows(), "arms_enabled": arms_enabled()})
        if parts == ["api", "run"]:
            try:
                r = run_request(body)
                rec = RUNNER.start(r["scenario"], r["mode"], r["n"], row=r["row"] or None, effort=r["effort"],
                                   as_of=r["as_of"] or None, by=r["by"] or "page")
                return self._json(rec, 202)
            except (ValueError, RuntimeError) as e:
                return self._json({"error": str(e)}, 409 if isinstance(e, RuntimeError) else 400)
        return self._json({"error": "not found"}, 404)


PAGE_SETTINGS = ("KG_DEMO_PORT", "KG_PAGE_MAX_BODY", "KG_PAGE_READ_TIMEOUT", "KG_PAGE_IDLE_TIMEOUT",
                 "KG_PAGE_MAX_CONNECTIONS")   # the numeric settings the page reads (task-0264)


def main() -> None:
    import register_impact
    import switches
    try:
        switches.check()   # task-0276: an on/off setting with a value it does not accept stops the page, exit 2
        register_impact.require_named()   # task-0288: KG_REGISTER names a register the page cannot read: exit 2, named
    except (switches.BadSwitch, register_impact.RegisterUnreadable) as e:
        print(f"kg demo: cannot start: {e}", file=sys.stderr, flush=True)
        sys.exit(2)
    try:   # task-0264: every numeric setting the page reads, its limits and its store's port, refused at start, named
        settings.check(names=PAGE_SETTINGS)
        page_limits()
        settings.neo4j_uri()
    except ValueError as e:
        print(f"kg demo: cannot start: {e}", file=sys.stderr, flush=True)
        sys.exit(2)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    for rid in close_stale_runs():
        print(f"closed {rid}: its run.json read running with a stale heartbeat ({runs_index.RESTARTED})", flush=True)
    host = listen_host()
    try:
        httpd = http_boundary.BoundedServer((host, PORT), Handler, page_limits())   # task-0141.04
    except OSError as e:   # the port taken, the address not this machine's: cannot run (task-0264)
        print(f"kg demo: cannot bind {host}:{PORT}: {e}", file=sys.stderr, flush=True)
        sys.exit(2)
    writes = "token required" if page_token() else (write_refusal() or "open on this machine")
    # task-0171: the model rows' keys checked once each now, in the background, so the first page load
    # finds them done; only the verdict and the HTTP status are ever kept or shown, never a key
    key_check.CHECKER.enabled = True
    if key_check.enabled_by_env():
        for ps in SUBJECTS:
            with page_subject.using(ps):
                check_keys(wait=0)
    print(f"kg demo on http://{host}:{PORT}  published on {exposure()}  store {store_named()}  runs {RUNS_DIR}  writes: {writes}", flush=True)
    httpd.serve_forever()



_COMPAT = {"RECORD": "record_dir", "RECORD_MODEL": "record_model", "RECORD_EFFORT": "record_effort", "ARM_KIND": "arm_kind", "SUBJECT": "subject"}


def __getattr__(name: str):
    """The names this module once filled at import, read from the current subject when asked for."""
    if name in _COMPAT:
        return getattr(_ps(), _COMPAT[name])
    raise AttributeError(f"module 'server' has no attribute {name!r}")


if __name__ == "__main__":
    main()

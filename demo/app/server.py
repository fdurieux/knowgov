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

ROOT = HERE.parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
from subject import SUBJECT  # noqa: E402  (the subject root: KG_SUBJECT, default subjects/cargo_quote)
import arms  # noqa: E402  (the model endpoint settings; the client is imported only when a call is made)
RECORD = SUBJECT.record_dir
RUNS_DIR = Path(os.environ.get("KG_DEMO_RUNS", str(ROOT / "runs")))
NEO4J_URI = os.environ.get("KG_NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.environ.get("KG_NEO4J_PASSWORD", "kgpoc2026")
BROWSER_URL = os.environ.get("KG_BROWSER_URL", "http://localhost:7474")
PORT = int(os.environ.get("KG_DEMO_PORT", "8080"))
RECORD_MODEL = views.RECORD_MODEL
# KG_ARMS_MODEL in the app's environment preselects "another model" on the page; the
# harness itself reads the variable the server passes per run
DEFAULT_OTHER_MODEL = os.environ.get("KG_ARMS_MODEL") or "gpt-5.5"
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")
INDEX = (HERE / "index.html").read_bytes()

# Saved Cypher for the store panel. Each runs in Neo4j Browser against the
# scenario currently loaded; the comment on each says which scenario shows it.
def _endpoint_view() -> dict:
    """What the page says about the model endpoint: the host, the key variable's name (never
    its value), the model, and whether a call would be a deviation from the record."""
    ep = arms.endpoint()
    host = ep["base_url"].split("://", 1)[-1].split("/", 1)[0]
    return {"host": host, "key_var": ep["key_var"], "key_set": ep["key_set"], "model": ep["model"], "deviation": ep["deviation"]}


def _store(timeout: float = 3):
    """A store through the port, for the page's short reads; raises when unreachable."""
    from store import open_store  # the harness's port; the adapter needs its driver, in the image
    return open_store(connection_timeout=timeout, instance=SUBJECT.id)


# What each saved query needs in the store before it returns rows: the store holds one scenario
# at a time and the register only when projected, so a query run against the wrong state gets
# the console's "label not in the database" warnings and no records. The page marks each entry live.
NEEDS_TEXT = {"scenario": "any loaded scenario",
              "register": "the register projected", "register+scenario": "the register projected and a loaded scenario"}


def cypher_list() -> list[dict]:
    """The adapter's saved queries for its console, then the subject's own (queries.toml), each
    with what it needs. Only an adapter with a console has any."""
    try:
        from store_neo4j import SAVED_QUERIES   # the Neo4j adapter's; another adapter would list its own
    except ImportError:
        SAVED_QUERIES = []
    out = []
    for q in list(SAVED_QUERIES) + SUBJECT.queries:
        needs_text = q.get("needs_text") or NEEDS_TEXT.get(q["needs"]) or f"{q['needs']} loaded"
        out.append(dict(q, needs_text=needs_text))
    return out


# ------------------------------------------------------------------ the store

def store_status() -> dict:
    """What the store holds, through the driver when it is installed."""
    out = {"uri": NEO4J_URI, "browser": BROWSER_URL, "reachable": False, "loaded": None, "census": None, "register": None, "error": None}
    try:
        with _store() as s:
            acts = s.extraction_activities()
            c = s.census()
            reg = s.register_census()
        out.update(reachable=True, census={"nodes": c["nodes"], "relationships": c["relationships"], "assertions_by_status": c["assertions_by_status"]},
                   loaded=(acts[0].split(":")[2] if acts else None), activities=acts, register=reg)
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

    def start(self, scenario: str, mode: str, n: int, model: str | None = None) -> dict:
        if scenario not in views.SCENARIOS:
            raise ValueError(f"unknown scenario {scenario}")
        if mode not in ("deterministic", "arms"):
            raise ValueError(f"unknown mode {mode}")
        if mode == "arms" and not arms.enabled():
            raise ValueError(f"arms mode needs {arms.endpoint()['key_var']} in the app's environment")
        model = (model or RECORD_MODEL).strip()
        if not MODEL_RE.match(model):
            raise ValueError(f"not a model name: {model!r}")
        with self.lock:
            if self.current and self.current["status"] == "running":
                raise RuntimeError("a run is already in progress; the store is one database")
            stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
            out_dir = RUNS_DIR / stamp
            k = 2
            while out_dir.exists():
                out_dir = RUNS_DIR / f"{stamp}-{k}"
                k += 1
            out_dir.mkdir(parents=True)
            derived = SUBJECT.scenarios.get(scenario, {}).get("stage2", {}).get("derived")
            if derived:
                # the record's stage 2 registers an earlier scenario's governed output as the
                # Derived artefact; give the re-run the same object to invalidate, in both
                # modes: the harness reads <out>/<from_scenario>/<file> whether or not the
                # arms are called, and without it a deterministic stage 2 has no Derived
                # node to mark suspect (found by the maintainer's traversal, 2026-11-01)
                src = RECORD / derived["from_scenario"] / derived["file"]
                if src.exists():
                    (out_dir / derived["from_scenario"]).mkdir()
                    shutil.copy(src, out_dir / derived["from_scenario"] / derived["file"])
            cmd = [sys.executable, "run.py", "--scenarios", scenario, "--out", str(out_dir)]
            cmd += ["--deterministic"] if mode == "deterministic" else ["--n", str(n)]
            env = {**os.environ, "KG_NEO4J_URI": NEO4J_URI, "KG_NEO4J_PASSWORD": NEO4J_PASSWORD,
                   "PYTHONUNBUFFERED": "1", "KG_WORKERS": os.environ.get("KG_WORKERS", "2")}
            if mode == "arms":
                env["KG_ARMS_MODEL"] = model  # the record's model unless the page chose another
            log = out_dir / f"{scenario}-{mode}.log"
            fh = open(log, "w", encoding="utf-8")  # noqa: SIM115 — closed when the process ends
            proc = subprocess.Popen(cmd, cwd=str(HARNESS), stdout=fh, stderr=subprocess.STDOUT, env=env)
            rec = {"id": out_dir.name, "scenario": scenario, "mode": mode, "n": n, "status": "running",
                   "model": model if mode == "arms" else None, "model_deviation": (mode == "arms" and model != RECORD_MODEL),
                   "started": _now(), "finished": None, "exit_code": None,
                   "out_dir": str(out_dir), "log": str(log), "source": f"demo-runs/{out_dir.name}", "cmd": " ".join(cmd)}
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
    out = []
    if RUNS_DIR.exists():
        for d in sorted(RUNS_DIR.iterdir(), reverse=True):
            if not d.is_dir():
                continue
            scenarios = sorted(p.name for p in d.iterdir() if p.is_dir() and (p / "deterministic.json").exists())
            modes = sorted({("arms" if list((d / s).glob("run*_G.json")) else "deterministic") for s in scenarios})
            out.append({"id": d.name, "scenarios": scenarios, "modes": modes, "logs": sorted(p.name for p in d.glob("*.log"))})
    return out


# ------------------------------------------------------------------ HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "kg-demo/1"

    def log_message(self, fmt, *args):  # quieter than the default
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        parts = [p for p in u.path.split("/") if p]
        try:
            if not parts or parts == ["index.html"]:
                return self._send(200, INDEX, "text/html; charset=utf-8")
            if parts == ["health"]:
                return self._json({"ok": True})
            if parts[:2] == ["api", "scenarios"]:
                st = store_status()
                return self._json({"scenarios": views.scenario_list(RUNS_DIR), "store": st,
                                   "arms_enabled": arms.enabled(), "model_endpoint": _endpoint_view(),
                                   "record_model": RECORD_MODEL, "default_other_model": DEFAULT_OTHER_MODEL,
                                   "arms_model_preset": bool(os.environ.get("KG_ARMS_MODEL")),
                                   "deterministic_enabled": st["reachable"],
                                   "runs_dir": str(RUNS_DIR), "run": RUNNER.describe()})
            if parts[:2] == ["api", "results"] and len(parts) == 3:
                sc = parts[2]
                source = q.get("source", [views.default_source(sc)])[0]
                view = views.build(sc, source, RUNS_DIR)
                view["cascade"] = {arm: cascade.render(view["systemic"], arm, title=f"{sc}, arm {arm}") for arm in ("G", "B")}
                view["footprint"] = register_view.footprint(view)
                view["details"]["footprint"] = view["footprint"]["panel"]
                return self._json(view)
            if parts == ["api", "store"]:
                return self._json(store_status())
            if parts == ["api", "register"]:
                today = q.get("today", [None])[0]
                if today not in (None, "wall") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", today):
                    return self._json({"error": "today must be 'wall' or YYYY-MM-DD"}, 400)
                return self._json(register_view.build(today))
            if parts[:3] == ["api", "register", "footprint"] and len(parts) == 4 and parts[3] in views.SCENARIOS:
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
            if parts[:3] == ["api", "register", "impact"] and len(parts) == 4:
                out = register_view.impact(parts[3])
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
                                   model=(str(body["model"]) if body.get("model") else None))
                return self._json(rec, 202)
            except (ValueError, RuntimeError) as e:
                return self._json({"error": str(e)}, 409 if isinstance(e, RuntimeError) else 400)
        return self._json({"error": "not found"}, 404)


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"kg demo on http://0.0.0.0:{PORT}  store {NEO4J_URI}  runs {RUNS_DIR}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()

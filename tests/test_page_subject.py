"""Task-0032.01: the page's modules take the subject as a value. views, register_view and server
read every subject-derived table from a PageSubject built once per subject; a public entry point
takes ``subject=``; a run folder names its subject; the store status names the loaded scenario's
subject. One process can now answer for two subjects, which the drop-down (task-0032.02) needs."""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import page_subject  # noqa: E402
import register_view  # noqa: E402
import server  # noqa: E402
import views  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402
from subject import Subject  # noqa: E402

JEF = Subject(ROOT / "subjects" / "jef_data_load")


def test_no_page_module_fills_a_table_from_the_subject_global():
    """AC 1: no `from subject import SUBJECT`, and no module-level assignment that reads it."""
    for name in ("views.py", "register_view.py", "server.py"):
        src = (ROOT / "demo" / "app" / name).read_text(encoding="utf-8")
        assert "from subject import SUBJECT" not in src, name
        top = [ln for ln in src.splitlines() if re.match(r"^[A-Z_][A-Z0-9_]* *=", ln) and not ln.startswith("_COMPAT")]   # _COMPAT maps the old names to attributes
        # the old global by its own name (SUBJECTS, the list of every subject the page serves, is not it)
        bad = [ln for ln in top if re.search(r"\bSUBJECT\b(?!S)", ln.split("=", 1)[1]) or "_ps()" in ln]
        assert not bad, (name, bad)


def test_one_process_answers_for_either_subject_by_value():
    """The same modules, in one process, give CargoQuote's or J-F's tables by the subject passed;
    the current subject is restored after the call; a PageSubject is built once per root."""
    cq, jef = page_subject.of(CARGO_QUOTE), page_subject.of(JEF)
    assert page_subject.of(Subject(ROOT / "subjects" / "jef_data_load")) is jef, "built once per root"
    assert cq.order[0] == "S1" and jef.order[0] == "C" and cq.record_model and not jef.record_model
    before = page_subject.current()
    a = [s["id"] for s in views.scenario_list(ROOT / "no-runs", subject=cq)]
    b = [s["id"] for s in views.scenario_list(ROOT / "no-runs", subject=jef)]
    assert a == cq.order and b == jef.order and set(a).isdisjoint(b)
    assert page_subject.current() is before, "the call's subject does not leak past the call"
    assert views.build("C", "record", ROOT / "no-runs", subject=jef)["scenario"] == "C"
    assert register_view.build(subject=jef)["subject_system"] == "jef_kit" and register_view.build(subject=cq)["subject_system"] == "kit"
    assert register_view.impact_default(subject=jef) == "APP-0005" and register_view.impact_default(subject=cq) == "APP-0002"
    with page_subject.using(jef):
        assert server.model_rows()[0]["why"] == "the record ran no arm" and server._ps() is jef
    with page_subject.using(cq):
        assert server.model_rows()[0]["model"] == cq.record_model


def test_a_subject_set_in_one_thread_is_not_seen_in_another():
    """The server answers each request on its own thread: a subject set for one request must not
    reach another (task-0032.02 sets one per request)."""
    seen = {}

    def other():
        seen["other"] = page_subject.current().id
    with page_subject.using(JEF):
        t = threading.Thread(target=other)
        t.start()
        t.join()
        seen["here"] = page_subject.current().id
    assert seen["here"] == "jef_data_load" and seen["other"] == page_subject.of(page_subject.subject_mod.SUBJECT).id


def test_a_run_folder_names_its_subject_and_older_runs_are_still_read():
    """AC 2: the Runner writes runs/<subject id>/<stamp>/ and records the subject and source; a run
    written before, at runs/<stamp>/, still lists for the subject whose scenario it holds."""
    started = []

    class _Proc:
        def wait(self):
            return 0

    def popen(cmd, cwd=None, stdout=None, stderr=None, env=None):
        started.append({"cmd": cmd, "env": env})
        return _Proc()
    keep_popen, keep_runs = server.subprocess.Popen, server.RUNS_DIR
    with tempfile.TemporaryDirectory() as td:
        server.subprocess.Popen, server.RUNS_DIR = popen, Path(td)
        runner = server.Runner()
        try:
            with page_subject.using(CARGO_QUOTE):
                rec = runner.start("S1", "deterministic", 1)
            out = Path(rec["out_dir"])
            assert out.parent == Path(td) / "cargo_quote" and rec["subject"] == "cargo_quote"
            assert rec["source"] == f"demo-runs/cargo_quote/{out.name}" and started[0]["env"]["KG_SUBJECT"] == str(CARGO_QUOTE.root)
            # the run's results, and one from the older flat layout
            for d in (out / "S1", Path(td) / "2026-10-30-1700" / "S1"):
                d.mkdir(parents=True, exist_ok=True)
                (d / "deterministic.json").write_text(json.dumps({}), encoding="utf-8")
            with page_subject.using(CARGO_QUOTE):
                ids = [s["id"] for s in views.sources_for("S1", Path(td))]
                runs = server.list_runs()
            assert f"demo-runs/cargo_quote/{out.name}" in ids and "demo-runs/2026-10-30-1700" in ids
            assert [r["id"] for r in runs] == [f"cargo_quote/{out.name}", "2026-10-30-1700"]
            with page_subject.using(JEF):
                assert server.list_runs() == [] and [s["id"] for s in views.sources_for("C", Path(td))] == ["record"], \
                    "another subject's runs are not listed for J-F"
        finally:
            runner.join()   # the waiter writes the run's end into td: done before td goes
            server.subprocess.Popen, server.RUNS_DIR = keep_popen, keep_runs


def test_the_loaded_scenario_names_its_subject():
    """AC 2: scenario ids are each subject's own, so the store's loaded scenario names its subject;
    store_status() carries the field, and names the subject it answers for."""
    both = [CARGO_QUOTE, JEF]
    assert page_subject.scenario_subject("S6", both) == "cargo_quote" and page_subject.scenario_subject("D3", both) == "jef_data_load"
    assert page_subject.scenario_subject("S6", [JEF]) is None and page_subject.scenario_subject(None, both) is None
    with page_subject.using(JEF):
        st = server.store_status()
    assert "loaded_subject" in st and st["subject"] == "jef_data_load"


# ---- task-0032.02: KG_SUBJECTS, /api/subjects, ?subject= on every route, the header drop-down

def _env(**kv):
    import os
    saved = {k: os.environ.get(k) for k in ("KG_SUBJECT", "KG_SUBJECTS")}
    for k in saved:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kv.items() if v is not None})
    return saved


def _restore(saved):
    import os
    for k, v in saved.items():
        os.environ.pop(k, None)
        if v is not None:
            os.environ[k] = v


def test_the_subject_list_follows_kg_subjects_and_kg_subject_picks_the_default():
    """Default: the repository's subjects/, CargoQuote first. KG_SUBJECT moves its subject first.
    KG_SUBJECTS set is the whole list: an instance lists its own subjects only, whatever KG_SUBJECT says."""
    saved = _env()
    try:
        assert [p.id for p in server._load_subjects()] == ["cargo_quote", "jef_data_load"]
        _env(KG_SUBJECT=str(JEF.root))
        assert [p.id for p in server._load_subjects()] == ["jef_data_load", "cargo_quote"]
        _env(KG_SUBJECTS=str(JEF.root), KG_SUBJECT=str(CARGO_QUOTE.root))
        assert [p.id for p in server._load_subjects()] == ["jef_data_load"], "the instance's own only, the public default ignored"
        _env(KG_SUBJECTS=str(ROOT / "subjects"))
        assert [p.id for p in server._load_subjects()] == ["cargo_quote", "jef_data_load"], "a fixture with listed = false is skipped in a scan"
        _env(KG_SUBJECTS=f"{JEF.root},{CARGO_QUOTE.root}", KG_SUBJECT=str(CARGO_QUOTE.root))
        assert [p.id for p in server._load_subjects()] == ["cargo_quote", "jef_data_load"]
    finally:
        _restore(saved)


def _serve():
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def _get(url, method="GET", body=None):
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_every_route_answers_within_the_subject_the_request_names():
    """One server, both subjects, concurrent requests: each answers with its own scenarios and page
    title; no ?subject= gets the default; an id the page does not serve is 404 on the page, the API
    and a POST alike. KG_PAGE_LISTEN is pinned to the loopback this test serves on (task-0246): with the
    image's 0.0.0.0 the page refuses an untokened POST before it reaches the subject (403), so the
    POSTs' 404 holds only for a page that listens on this machine alone."""
    from concurrent.futures import ThreadPoolExecutor
    saved = os.environ.get("KG_PAGE_LISTEN")
    os.environ["KG_PAGE_LISTEN"] = "127.0.0.1"
    httpd, base = _serve()
    try:
        code, body = _get(base + "/api/subjects")
        j = json.loads(body)
        assert code == 200 and [s["id"] for s in j["subjects"]] == [p.id for p in server.SUBJECTS] and j["subjects"][0]["default"]
        assert {"id", "name", "title", "default"} <= set(j["subjects"][0])
        want = {p.id: p.order for p in server.SUBJECTS}

        def scen(sid):
            return sid, json.loads(_get(base + f"/api/scenarios?subject={sid}")[1])
        with ThreadPoolExecutor(8) as ex:
            got = list(ex.map(scen, [p.id for p in server.SUBJECTS] * 4))
        for sid, j in got:
            assert [s["id"] for s in j["scenarios"]] == want[sid], sid
            assert j["page"]["title"] == server.SUBJECT_BY_ID[sid].subject.page.get("title", ""), sid
        assert [s["id"] for s in json.loads(_get(base + "/api/scenarios")[1])["scenarios"]] == server.SUBJECTS[0].order
        assert json.loads(_get(base + "/api/results/C?subject=jef_data_load")[1])["scenario"] == "C"
        for path in ("/?subject=nope", "/api/scenarios?subject=nope", "/api/register?subject=nope", "/api/results/S1?subject=nope"):
            assert _get(base + path)[0] == 404, path
        assert _get(base + "/api/run?subject=nope", "POST", {"scenario": "S1", "mode": "deterministic"})[0] == 404
        assert _get(base + "/api/run", "POST", {"scenario": "S1", "mode": "deterministic", "subject": "nope"})[0] == 404
    finally:
        httpd.shutdown()
        if saved is None:
            os.environ.pop("KG_PAGE_LISTEN", None)
        else:
            os.environ["KG_PAGE_LISTEN"] = saved


def test_the_page_names_its_subject_on_every_call_and_keeps_the_arms_choice_per_subject():
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert 'id="subject-pick"' in page and "fetch('/api/subjects')" in page and "location.search = '?subject='" in page
    assert "fetch(withSubject(path), opts)" in page and "fetch(withSubject(`/api/gaps/" in page
    assert page.count("fetch(") == 3, "every other call goes through api(), which names the subject"
    assert "'kg-arms-row:' + STATE.subject" in page
    compose = (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
    instance = (ROOT / "demo" / "docker-compose.instance.yml").read_text(encoding="utf-8")
    assert "KG_SUBJECTS: ${KG_SUBJECTS:-/repo/subjects}" in compose and "KG_SUBJECTS: /instance/subjects" in instance
    assert views.glossary()["subject"].startswith("One kit with its documents")


def test_a_subject_added_after_start_is_served_without_a_restart_and_a_removed_one_is_not():
    """task-0150 (doc-0021 G3): the page rescans its subject folders when a manifest is added, edited or
    removed; no restart. A manifest that does not load is left out, the others still served."""
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="kg-rescan-"))

    def add(sid: str, text: str | None = None):
        d = tmp / sid
        d.mkdir()
        m = (ROOT / "subjects" / "minimal" / "subject.toml").read_text(encoding="utf-8")
        (d / "subject.toml").write_text(text if text is not None else
                                        m.replace('id = "minimal"', f'id = "{sid}"').replace("listed = false", "listed = true"), encoding="utf-8")
        sc = (ROOT / "subjects" / "minimal" / "scenarios.toml").read_text(encoding="utf-8")   # each its own id (task-0194)
        (d / "scenarios.toml").write_text(sc.replace('id = "S0"', f'id = "{sid}-S0"'), encoding="utf-8")

    add("alpha")
    saved = _env(KG_SUBJECTS=str(tmp))
    httpd, base = _serve()
    try:
        ids = lambda: [s["id"] for s in json.loads(_get(base + "/api/subjects")[1])["subjects"]]  # noqa: E731
        assert ids() == ["alpha"]
        add("beta")
        assert ids() == ["alpha", "beta"]
        code, body = _get(base + "/api/scenarios?subject=beta")
        assert code == 200 and [s["id"] for s in json.loads(body)["scenarios"]] == ["beta-S0"], body
        add("broken", "[subject\n")
        assert ids() == ["alpha", "beta"], "a manifest that does not load is left out"
        shutil.rmtree(tmp / "beta")
        assert ids() == ["alpha"]
        assert _get(base + "/api/scenarios?subject=beta")[0] == 404
        assert _get(base + "/api/scenarios?subject=alpha")[0] == 200
    finally:
        httpd.shutdown()
        _restore(saved)
        server.refresh_subjects()
        shutil.rmtree(tmp, ignore_errors=True)


def _minimal(d: Path, sid: str, name: str | None = None) -> None:
    d.mkdir(parents=True, exist_ok=True)
    m = (ROOT / "subjects" / "minimal" / "subject.toml").read_text(encoding="utf-8")
    m = m.replace('id = "minimal"', f'id = "{sid}"').replace("listed = false", "listed = true")
    if name is not None:
        m = re.sub(r'(?m)^name = "[^"]*"', f'name = "{name}"', m, count=1)
    (d / "subject.toml").write_text(m, encoding="utf-8")
    sc = (ROOT / "subjects" / "minimal" / "scenarios.toml").read_text(encoding="utf-8")
    (d / "scenarios.toml").write_text(sc.replace('id = "S0"', f'id = "{sid}-S0"'), encoding="utf-8")


def _touch_later(p: Path) -> None:
    """Move a file's mtime on, so a filesystem with a coarse clock still sees the edit."""
    import os
    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 2_000_000_000))


def test_an_edited_subject_or_scenarios_manifest_is_served_on_the_next_request():
    """task-0206 (doc-0030 P3): the page rebuilt on a changed subject.toml mtime, but page_subject.of
    cached by root forever, so an edited name was never served, and scenarios.toml was not watched."""
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="kg-edit-"))
    _minimal(tmp / "alpha", "alpha", "Alpha one")
    saved = _env(KG_SUBJECTS=str(tmp))
    httpd, base = _serve()
    try:
        names = lambda: {s["id"]: s["name"] for s in json.loads(_get(base + "/api/subjects")[1])["subjects"]}  # noqa: E731
        scenarios = lambda: [s["id"] for s in json.loads(_get(base + "/api/scenarios?subject=alpha")[1])["scenarios"]]  # noqa: E731
        assert names() == {"alpha": "Alpha one"} and scenarios() == ["alpha-S0"]
        m = tmp / "alpha" / "subject.toml"
        m.write_text(m.read_text(encoding="utf-8").replace('name = "Alpha one"', 'name = "Alpha two"'), encoding="utf-8")
        _touch_later(m)
        assert names() == {"alpha": "Alpha two"}, "the edited name, on the next request"
        sc = tmp / "alpha" / "scenarios.toml"
        sc.write_text(sc.read_text(encoding="utf-8").replace('id = "alpha-S0"', 'id = "alpha-S9"'), encoding="utf-8")
        _touch_later(sc)
        assert scenarios() == ["alpha-S9"], "scenarios.toml is watched too"
        # the module's own entry point sees the edit as well, whatever Subject object it is handed
        stale = Subject(tmp / "alpha")
        m.write_text(m.read_text(encoding="utf-8").replace('name = "Alpha two"', 'name = "Alpha three"'), encoding="utf-8")
        _touch_later(m)
        assert page_subject.of(stale).subject.name == "Alpha three"
    finally:
        httpd.shutdown()
        _restore(saved)
        server.refresh_subjects()
        shutil.rmtree(tmp, ignore_errors=True)


def test_kg_subjects_with_nothing_loadable_serves_no_public_subject():
    """task-0206 (doc-0030 P3): with KG_SUBJECTS set and no manifest under it loading, the page served
    public CargoQuote, against _load_subjects' docstring. It now serves none, and says so."""
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="kg-none-"))
    (tmp / "broken").mkdir()
    (tmp / "broken" / "subject.toml").write_text("[subject\n", encoding="utf-8")
    saved = _env(KG_SUBJECTS=str(tmp), KG_SUBJECT=str(CARGO_QUOTE.root))
    httpd, base = _serve()
    try:
        assert server._load_subjects() == [], "the instance's own subjects only: none loads, none listed"
        code, body = _get(base + "/api/subjects")
        assert code == 200 and json.loads(body)["subjects"] == [], body
        for path in ("/api/scenarios", "/api/scenarios?subject=cargo_quote", "/api/register"):
            code, body = _get(base + path)
            assert code == 404 and b"cargo_quote" not in body.replace(b"'cargo_quote'", b"") and b"KG_SUBJECTS" in body, (path, code, body)
        code, _ = _get(base + "/")
        assert code == 200, "the page itself still loads, to say there is no subject"
    finally:
        httpd.shutdown()
        _restore(saved)
        server.refresh_subjects()
        shutil.rmtree(tmp, ignore_errors=True)


def test_a_subject_whose_task_policy_is_refused_is_left_out():
    """task-0313: the page does not serve a subject whose run would exit 2 on its task policy."""
    import shutil
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "s"
        shutil.copytree(ROOT / "subjects" / "jef_data_load", root, ignore=shutil.ignore_patterns("vendor", "runs", "__pycache__"))
        p = root / "subject.toml"
        p.write_text(p.read_text(encoding="utf-8") + '\n[tasks.broken]\nblock_levels = "absent"\nkeys = ["a|x"]\n', encoding="utf-8")
        try:
            page_subject.of(Subject(root))
        except Exception as e:  # noqa: BLE001
            assert "block_levels" in str(e), e
        else:
            raise AssertionError("a refused task policy was served")

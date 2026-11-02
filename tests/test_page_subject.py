"""Task-0032.01: the page's modules take the subject as a value. views, register_view and server
read every subject-derived table from a PageSubject built once per subject; a public entry point
takes ``subject=``; a run folder names its subject; the store status names the loaded scenario's
subject. One process can now answer for two subjects, which the drop-down (task-0032.02) needs."""
from __future__ import annotations

import json
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
        assert not [ln for ln in top if "SUBJECT" in ln or "_ps()" in ln], (name, [ln for ln in top if "SUBJECT" in ln or "_ps()" in ln])


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
        try:
            with page_subject.using(CARGO_QUOTE):
                rec = server.Runner().start("S1", "deterministic", 1)
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

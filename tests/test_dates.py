"""task-0262 (decision-0032, G9-17): one strict YYYY-MM-DD parse for every date knowgov reads.

``date.fromisoformat`` on Python 3.11 and later also reads the ISO week form (``2026-W45-1`` was read as
2026-11-02) and the basic form (``20261105xx`` as 2026-11-05), and ``\\d`` matches fullwidth digits. Every
reader now goes through ``harness/dates.py``: ``parse`` for a date given as one, ``day`` for a stored date or
instant. A loose form is refused naming the value: exit 2 on the CLIs, the reader's ToolError on the MCP, 400
on the page. ``record``, ``today`` and a valid date read as before, and the record does not move (the
deterministic comparators)."""
from __future__ import annotations

import ast
import datetime as dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import dates  # noqa: E402
from _skip import skip  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

GOOD = {"2026-11-05": dt.date(2026, 11, 5), "2024-02-29": dt.date(2024, 2, 29)}
# every loose form the validation pass found (group 1 F3, group 2 F4), and their neighbours
LOOSE = ["2026-W45-1", "2026-W45", "20261105", "20261105xx", "２０２６-１１-０５", "2026-11-0５", "2026-11-05x",
         "2026-11-05 ", " 2026-11-05", "2026-11-05\n", "2026-11-05T00:00:00", "2026-13-01", "2026-02-30", "", "next week"]

# Every reader of a date: (file, the innermost function that parses it) -> what it reads. Each one's source
# calls ``dates.``; a reader added elsewhere is caught by the scan below, a reader dropped from here by this list.
READERS = {
    ("harness/cadence.py", "as_of"): "--as-of on gate_cli, run, trace and proposal_impact; KG_AS_OF; the MCP as_of",
    ("harness/cadence.py", "_date"): "a verification's at and valid_until, as stored (dates.day)",
    ("harness/review.py", "today"): "KG_TODAY",
    ("harness/review.py", "_date"): "a review file's on, the register's issued and withdrawn dates",
    ("harness/load.py", "now"): "KG_TODAY, the load's provenance stamp",
    ("harness/load.py", "_day"): "an attestation's at, as stored (dates.day)",
    ("harness/capture.py", "_date"): "a capture's on, an elicited link's on and review_due",
    ("harness/capture.py", "_due"): "capture due --on",
    ("harness/proposal_impact.py", "_date"): "an overlay exception's expires",
    ("harness/mcp_runs.py", "start_run"): "knowgov-runs start_run's as_of",
    ("harness/mcp_server.py", "go"): "three_valued_answer's session date",
    ("tools/connector.py", "_exported_on"): "connector --exported-on, the AML header's CreateDate",
    ("tools/connector.py", "land"): "the export folder's day and the folders already landed",
    ("tools/check_subject.py", "_dated"): "an attestation's at, as the load reads it",
    ("tools/check_one_clock.py", "main"): "the check's own date",
    ("demo/app/server.py", "start"): "the page's POST /api/run as_of",
    ("demo/app/server.py", "_get"): "the page's GET /api/register?today=",
    ("demo/app/register_view.py", "build"): "the register view's today and SOURCE.md's pinned date",
}
# What still calls fromisoformat: instants, not dates, each read whole (task-0262 closes dates only).
INSTANTS = {
    "harness/dates.py": 3,         # the one parse itself
    "harness/review.py": 1,        # now(): KG_NOW, an ISO instant
    "harness/runs_index.py": 1,    # a run's heartbeat instant, written by the page
    "tools/connector.py": 1,       # the export time, after its date is held to parse
    "demo/app/server.py": 3,       # the page's own instants: now, a run's started and finished
}
SCANNED = ("harness", "tools", "demo/app", "demo/tools", "instance")


def _sources():
    for top in SCANNED:
        for p in sorted((ROOT / top).rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if "/vendor/" in rel or "__pycache__" in rel or "/fixtures/" in rel:
                continue
            yield rel, p.read_text(encoding="utf-8")


def _innermost(src: str, name: str) -> str:
    """The source of the innermost function called ``name`` that mentions ``dates.``, else of the first."""
    tree, found = ast.parse(src), []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            found.append(ast.get_source_segment(src, n) or "")
    assert found, f"no function {name}"
    return next((s for s in found if "dates." in s), found[0])


def test_parse_reads_only_yyyy_mm_dd_in_ascii_digits():
    for s, d in GOOD.items():
        assert dates.parse(s) == d and dates.is_date(s)
    for s in LOOSE:
        assert not dates.is_date(s), s
        try:
            dates.parse(s, "--as-of")
        except dates.NotADate as e:
            assert isinstance(e, ValueError) and repr(s) in str(e) and "--as-of" in str(e) and "YYYY-MM-DD" in str(e), e
        else:
            raise AssertionError(f"{s!r} read as a date")
    for v in (None, 20261105, dt.date(2026, 11, 5)):
        assert not dates.is_date(v), v   # parse reads text; a stored date object is day()'s


def test_day_reads_a_stored_date_or_instant_and_nothing_looser():
    """AC #4: cadence._date's cut at ten characters is checked the same way: the date part is parse's, and
    what follows is nothing or an ISO time, so a version tag, a week form or a suffix names no date."""
    d = dt.date(2026, 11, 5)
    for v in (d, dt.datetime(2026, 11, 5, 10), "2026-11-05", "2026-11-05T10:00:00Z", "2026-11-05T10:00:00+01:00",
              "2026-11-05 10:00:00+00:00"):
        assert dates.day(v) == d, v
    for v in ("2026-W45-1", "2026-W45-1T00:00:00Z", "20261105T100000", "20261105xx", "2026-11-05xx", "2026-11-05Tnoon",
              "２０２６-１１-０５", "v0.2.13", "", None, 20261105):
        assert dates.day(v) is None, v
    import cadence
    assert cadence._date("2026-W45-1") is None and cadence._date("2026-11-05T09:00:00Z") == d


def test_every_reader_goes_through_dates_and_nothing_else_parses_a_date():
    for (rel, fn), what in READERS.items():
        assert "dates." in _innermost((ROOT / rel).read_text(encoding="utf-8"), fn), f"{rel} {fn} ({what}) parses a date by itself"
    found = {}
    for rel, src in _sources():
        n = src.count("fromisoformat(") + src.count("strptime(")
        if rel == "harness/dates.py":
            n = sum(1 for line in src.splitlines() if "fromisoformat(" in line and "return" in line)
        if n:
            found[rel] = n
        if rel.startswith(("harness/", "demo/app/")):
            assert "\\d{4}-\\d{2}-\\d{2}" not in src, f"{rel}: \\d matches fullwidth digits; use dates.is_date"
    assert found == INSTANTS, f"a date parsed outside harness/dates.py, or an instant list out of date: {found}"


def test_as_of_refuses_every_loose_form_and_reads_record_today_and_a_date_as_before():
    import cadence
    keep = os.environ.get("KG_TODAY")
    os.environ["KG_TODAY"] = "2026-11-09"
    try:
        assert cadence.as_of("2026-11-05") == dt.date(2026, 11, 5)
        assert cadence.as_of(dt.date(2026, 11, 5)) == dt.date(2026, 11, 5)
        assert cadence.as_of("today") == cadence.as_of(None) == dt.date(2026, 11, 9)
        assert cadence.as_of("record", CARGO_QUOTE) == cadence.record_date(CARGO_QUOTE)
        for s in LOOSE:
            try:
                cadence.as_of(s, CARGO_QUOTE)
            except ValueError as e:
                assert repr(s) in str(e) and "'today' or 'record'" in str(e), e
            else:
                raise AssertionError(f"as_of read {s!r}")
    finally:
        os.environ.pop("KG_TODAY") if keep is None else os.environ.__setitem__("KG_TODAY", keep)


def _kg_today_refused(read, good):
    keep = os.environ.get("KG_TODAY")
    try:
        for s in ("20261109", "2026-W45-1", "２０２６-１１-０９"):
            os.environ["KG_TODAY"] = s
            try:
                read()
            except ValueError as e:
                assert "KG_TODAY" in str(e) and repr(s) in str(e), e
            else:
                raise AssertionError(f"{read.__module__}.{read.__name__} read KG_TODAY={s!r}")
        os.environ["KG_TODAY"] = "2026-11-09"
        assert read() == good
    finally:
        os.environ.pop("KG_TODAY") if keep is None else os.environ.__setitem__("KG_TODAY", keep)


def test_kg_today_in_a_loose_form_is_refused_naming_it():
    import review
    _kg_today_refused(review.today, dt.date(2026, 11, 9))


def test_the_loads_stamp_refuses_a_loose_kg_today_naming_it():
    try:
        import load
    except ModuleNotFoundError as e:
        skip("yaml", f"harness/load.py's mappers import {e.name}")
    _kg_today_refused(load.now, "2026-11-09T00:00:00+00:00")


def _cli(args, **env):
    e = {**os.environ, "KG_CLOCK": "pinned", "KG_TODAY": "2026-11-09", "KG_SUBJECT": str(CARGO_QUOTE.root), "KG_STORE": "rdflib",
         "KG_RDFLIB_FILE": str(Path(tempfile.gettempdir()) / "kg-dates-never-written.ttl"), **env}
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, env=e, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=120)
    return r.returncode, r.stderr


def test_the_clis_exit_2_naming_the_loose_date():
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "ledger.json"
        led.write_text("{}", encoding="utf-8")
        for bad in ("2026-W45-1", "20261105xx", "２０２６-１１-０５"):
            for args in ([ROOT / "harness" / "gate_cli.py", "--scenario", "S1", "--no-load", "--as-of", bad],
                         [ROOT / "harness" / "trace.py", "check", "--instance", td, "--ledger", led, "--as-of", bad],
                         [ROOT / "harness" / "proposal_impact.py", "--as-of", bad, ROOT / "tools" / "fixtures" / "proposal_contract_quote.json"],
                         [ROOT / "harness" / "capture.py", "due", "--on", bad, "--out", Path(td) / "due"]):
                code, err = _cli(args)
                assert code == 2 and repr(bad) in err, (args[0].name, bad, code, err[-300:])
        code, err = _cli([ROOT / "harness" / "gate_cli.py", "--scenario", "S1", "--no-load", "--as-of", "today"], KG_TODAY="20261109")
        assert code == 2 and "KG_TODAY" in err and "'20261109'" in err, (code, err[-300:])
        code, err = _cli([ROOT / "harness" / "mcp_server.py", "--as-of", "2026-W45-1"])
        assert code == 2 and "'2026-W45-1'" in err, (code, err[-300:])
        assert not (Path(td) / "due").exists(), "a refused date writes nothing"


def test_run_exits_2_naming_the_loose_date():
    import importlib.util
    if importlib.util.find_spec("pyshacl") is None:
        skip("rdflib", "harness/run.py imports the pins (pyshacl) before it reads --as-of")
    with tempfile.TemporaryDirectory() as td:
        for bad in ("2026-W45-1", "20261105xx", "２０２６-１１-０５"):
            code, err = _cli([ROOT / "harness" / "run.py", "--deterministic", "--as-of", bad, "--out", Path(td) / "out"])
            assert code == 2 and repr(bad) in err, (bad, code, err[-300:])
        assert not (Path(td) / "out").exists(), "a refused date writes nothing"


def test_the_connector_refuses_a_loose_export_time_exit_2_and_lands_nothing():
    import shutil

    import connector
    fix = ROOT / "tools" / "fixtures" / "aris_cargo_quote" / "later"
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        shutil.copytree(ROOT / "demo" / "register", d / "register", ignore=shutil.ignore_patterns("__pycache__"))
        (d / "connectors.toml").write_text('[system.aris]\nid_attribute = "AT_ID"\n', encoding="utf-8")
        exports = d / "register" / "exports"
        before = sorted(p.relative_to(exports).as_posix() for p in exports.rglob("*")) if exports.is_dir() else []
        for bad in ("2026-W45-1", "2026-W45-1T00:00:00Z", "20261118", "２０２６-１１-１８", "2026-11-18x"):
            assert connector.main([str(d), "--system", "aris", str(fix), "--exported-on", bad]) == 2, bad
            try:
                connector._exported_on(bad, None)
            except ValueError as e:
                assert repr(bad) in str(e) and "--exported-on" in str(e), e
            else:
                raise AssertionError(bad)
        after = sorted(p.relative_to(exports).as_posix() for p in exports.rglob("*")) if exports.is_dir() else []
        assert after == before, "a refused export time lands nothing"
        assert connector._exported_on("2026-11-18", None) == "2026-11-18T00:00:00Z"
        assert connector._exported_on("2026-11-18T09:30:00+01:00", None) == "2026-11-18T08:30:00Z"
        assert connector._exported_on(None, "2026-11-18T00:00:00Z") == "2026-11-18T00:00:00Z"


def test_the_mcp_readers_refuse_with_their_documented_error():
    import mcp_runs
    import mcp_server
    tools = mcp_server.Tools(opener=lambda: None, as_of="2026-11-05")
    assert tools.session_as_of() == "2026-11-05"
    for bad in ("2026-W45-1", "20261105xx", "２０２６-１１-０５"):
        try:
            tools._as_of({"as_of": bad})
        except mcp_server.ToolError as e:
            assert repr(bad) in str(e), e
        else:
            raise AssertionError(bad)
        try:
            mcp_server.Tools(opener=lambda: None, as_of=bad).session_as_of()
        except ValueError as e:
            assert repr(bad) in str(e), e
        else:
            raise AssertionError(f"KG_AS_OF={bad!r} read")

    asked = []

    class Page:
        def request(self, method, path, body=None):
            asked.append(path)
            return 202, {}
    srv = mcp_runs.make_server(Page())
    keep = os.environ.get("KG_MCP_RUN_MODES")
    os.environ.pop("KG_MCP_RUN_MODES", None)
    try:
        for bad in ("２０２６-１１-０５", "2026-W45-1"):
            r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
                "name": "start_run", "arguments": {"scenario": "S1", "mode": "deterministic", "as_of": bad}}})["result"]
            assert r["isError"] and repr(bad) in r["content"][0]["text"], r
        assert asked == [], "a loose as_of never reaches the page"
    finally:
        if keep is not None:
            os.environ["KG_MCP_RUN_MODES"] = keep


def test_the_page_answers_400_naming_the_loose_date():
    import page_subject
    import register_view
    import server
    runner = server.Runner()
    for bad in ("2026-W45-1", "20261105xx", "２０２６-１１-０５"):
        with page_subject.using(CARGO_QUOTE):
            try:
                runner.start("S1", "deterministic", 1, as_of=bad)
            except ValueError as e:   # the POST handler's 400
                assert repr(bad) in str(e), e
            else:
                raise AssertionError(f"the run took as_of={bad!r}")
            try:
                register_view.build(bad)
            except ValueError as e:
                assert repr(bad) in str(e), e
            else:
                raise AssertionError(f"the register view took today={bad!r}")
    src = _innermost((ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8"), "_get")
    assert "dates.is_date(today)" in src and ", 400)" in src

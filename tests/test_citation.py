"""Task-0124: hand-written code cites the keys it rests on. The header citation in Python and Java,
``trace register --keys``/``--cited``, and check's citation findings, on test_trace's fake store
(stdlib only). After S6's change on the rdflib store, tools/check_trace_walkthrough.py."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness"), str(ROOT / "tests")]
import citation  # noqa: E402
import code_map  # noqa: E402
import trace  # noqa: E402
from test_trace import FakeStore, _resolve, _setup, _valid, check_root  # noqa: E402

KNOWN = {"k1", "k2", "k3"}


class KeyedStore(FakeStore):
    def assertions_on_key(self, key, statuses):
        return [{"id": a, "status": s} for a, s in self.status.items() if f"k{a[2]}" == key and s in statuses]


def _raises(fn, want):
    try:
        fn()
    except (trace.CannotRun, citation.Malformed) as e:
        assert want in str(e), e
        return
    raise AssertionError(f"no error, want {want!r}")


def test_a_header_cites_keys_in_python_and_in_java():
    py = '#!/usr/bin/env python3\n"""The tariff."""\n# knowgov-keys: P2|surcharge, P2|threshold\n#knowgov-keys:P3|order,P2|surcharge\n'
    assert citation.parse(py, "#") == ["P2|surcharge", "P2|threshold", "P3|order"]
    java = "package quote;\n\n// knowgov-keys: P2|surcharge,  P3|order\npublic class Tariff {}\n"
    assert citation.parse(java, "//") == ["P2|surcharge", "P3|order"]
    assert citation.parse(java, "#") == [], "a Java comment is no Python citation"
    assert citation.parse("x = 1\n" * citation.HEAD_LINES + "# knowgov-keys: k1\n", "#") == [], "a citation is a header"
    assert citation.parse('s = "# knowgov-keys: k1"\n', "#") == [], "a string is no comment"
    for bad in ("# knowgov-keys:\n", "# knowgov-keys: k1,,k2\n"):
        _raises(lambda: citation.parse(bad, "#"), "knowgov-keys:")
    assert (citation.language("a/B.java"), citation.language("x.py"), citation.language("q.sql")) == ("//", "#", None)


def _keyed(td):
    inst, led, _ = _setup(td)
    root = inst / check_root(inst)
    (inst / "code_map.toml").write_text((inst / "code_map.toml").read_text(encoding="utf-8").replace('include = ["**/*.py"]', 'include = ["**/*.py", "**/*.java"]')
                                        + '\n[[map]]\nglob = "hand/**"\napp = "APP-0001"\n', encoding="utf-8")
    (root / "hand").mkdir()
    (root / "hand" / "tariff.py").write_text("# knowgov-keys: k2\nSURCHARGE = 316\n", encoding="utf-8")
    (root / "hand" / "Screen.java").write_text("// knowgov-keys: k1, k3\nclass Screen {}\n", encoding="utf-8")
    (root / "hand" / "plain.py").write_text("X = 1\n", encoding="utf-8")
    return inst, led, root


def test_register_keys_rests_on_the_keys_current_statements_and_turns_suspect_after_the_change():
    with tempfile.TemporaryDirectory() as td:
        inst, led, root = _keyed(td)
        st = KeyedStore()
        rep = _valid(trace.register(st, instance=inst, ledger=led, commit="c1", files=["hand/plain.py"], keys=["k2"], known=KNOWN))
        [r] = rep["registered"]
        assert (r["keys"], r["used"], st.derived[r["id"]]["ids"]) == (["k2"], 1, ["A:2@v1"])
        rep = _valid(trace.register(st, instance=inst, ledger=led, commit="c1", files=["hand/tariff.py", "hand/Screen.java"],
                                    cited=True, known=KNOWN))
        assert [(r["path"], r["keys"], r["used"]) for r in rep["registered"]] == [("hand/tariff.py", ["k2"], 1), ("hand/Screen.java", ["k1", "k3"], 2)]
        assert {e["path"]: e["keys"] for e in json.loads(led.read_text(encoding="utf-8"))["entries"]} == \
            {"hand/plain.py": ["k2"], "hand/tariff.py": ["k2"], "hand/Screen.java": ["k1", "k3"]}

        after = KeyedStore()   # the change: a reload invalidated k2's statement
        after.status["A:2@v1"] = "invalidated"
        rep = _valid(trace.check(after, instance=inst, ledger=led, resolve=_resolve(), known=KNOWN))
        sus = sorted((f["path"], f["related"]) for f in rep["findings"] if f["kind"] == "suspect")
        assert sus == [("hand/plain.py", ["A:2@v1"]), ("hand/tariff.py", ["A:2@v1"])], "Screen.java cites no invalidated key"
        assert all("cited key(s) k2" in f["message"] for f in rep["findings"] if f["kind"] == "suspect")
        assert {r["path"]: r["keys"] for r in rep["registered"] if "keys" in r} == \
            {"hand/plain.py": ["k2"], "hand/tariff.py": ["k2"], "hand/Screen.java": ["k1", "k3"]}
        assert rep["exit_code"] == 1


def test_register_keys_refuses_an_unknown_key_a_key_with_no_statement_and_a_disagreeing_header():
    with tempfile.TemporaryDirectory() as td:
        inst, led, root = _keyed(td)
        st = KeyedStore()
        reg = lambda files, **kw: trace.register(st, instance=inst, ledger=led, commit="c1", files=files, known=KNOWN, **kw)  # noqa: E731
        _raises(lambda: reg(["hand/plain.py"], keys=["k1", "kX"]), "unknown key(s) kX")
        st.status["A:3@v1"] = "invalidated"
        _raises(lambda: reg(["hand/plain.py"], keys=["k3"]), "no current statement")
        _raises(lambda: reg(["hand/tariff.py"], keys=["k1"]), "its header cites k2, --keys names k1")
        _raises(lambda: reg(["hand/plain.py"], cited=True), "cites no key")
        _raises(lambda: reg(["hand/plain.py"], keys=["k1"], assertions=["A:1@v1"]), "exclusive")
        (root / "hand" / "tariff.py").write_text("# knowgov-keys: kX\n", encoding="utf-8")
        _raises(lambda: reg(["hand/tariff.py"], cited=True), "unknown key(s) kX")
        assert not led.exists(), "a refused registration writes nothing"


def test_check_finds_an_unknown_key_always_and_a_missing_citation_only_where_the_instance_requires_it():
    with tempfile.TemporaryDirectory() as td:
        inst, led, root = _keyed(td)
        st = KeyedStore()
        trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=_resolve())
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve(), known=KNOWN))
        assert rep["findings"] == [], "without [citations] require, an uncited file is no finding"

        (root / "hand" / "tariff.py").write_text("# knowgov-keys: k2, kX\n", encoding="utf-8")
        (root / "hand" / "Bad.java").write_text("// knowgov-keys:\n", encoding="utf-8")
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve(), known=KNOWN))
        assert [(f["severity"], f["kind"], f["path"], f["related"]) for f in rep["findings"]] == \
            [("blocker", "unknown_key", "hand/tariff.py", ["kX"]), ("blocker", "malformed_citation", "hand/Bad.java", [])]
        assert rep["exit_code"] == 1
        (root / "hand" / "Bad.java").unlink()
        (root / "hand" / "tariff.py").write_text("# knowgov-keys: k2\n", encoding="utf-8")

        cm = inst / "code_map.toml"
        cm.write_text(cm.read_text(encoding="utf-8").replace('include = ["**/*.py", "**/*.java"]', 'include = ["**/*.py", "**/*.java", "**/*.sql"]')
                      + '\n[citations]\nrequire = true\n', encoding="utf-8")
        (root / "hand" / "load.sql").write_text("select 1;\n", encoding="utf-8")
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve(), known=KNOWN, fail_on="major"))
        assert [(f["severity"], f["kind"], f["path"]) for f in rep["findings"]] == \
            [("major", "uncited", "hand/plain.py"), ("major", "uncited", "reference_impl.py"), ("info", "uncitable", "hand/load.sql")]
        assert rep["exit_code"] == 1
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve(), known=KNOWN, changed=["hand/tariff.py"]))
        assert rep["findings"] == [], "with --changed, only the changed files' citations are read"


def test_the_code_map_citations_table_is_read_and_checked():
    with tempfile.TemporaryDirectory() as td:
        inst, led, root = _keyed(td)
        apps = code_map.register_apps(inst / "register")
        errs: list[str] = []
        assert code_map.code_map(inst, apps, errs)["citations"] == {"require": False, "apps": ["APP-0001"]} and errs == []
        cm = inst / "code_map.toml"
        base = cm.read_text(encoding="utf-8")
        cm.write_text(base + '\n[citations]\nrequire = "yes"\napps = ["APP-0002"]\n', encoding="utf-8")
        errs = []
        code_map.code_map(inst, apps, errs)
        assert any("require must be true or false" in e for e in errs) and any("APP-0002 is named by no [[map]] row" in e for e in errs), errs

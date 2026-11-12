"""task-0320 (decision-0038, accepted 2026-11-11, "(a) as advised for all six"): before the 0.9.0 freeze the gate report
names every input that decided it, a review names its giver, one key rule holds on every key argument, and an execution
verification binds to the code and the suite it ran.

- N2: ``attestations`` (the manifest's [verification], [provenance] and [capture] as the load read them), ``captures``
  (the answers and reviews the load applied) and ``register.files`` (the register's files as read), each recorded from
  what the load used, so a file it skipped moves nothing.
- N3: ``baseline.differs``, the identity fields that differ, one function for the command and the MCP reader.
- N4: the corpus digest over canonical JSON lines.
- G1, G2: a ruling records its giver, read from the capture's own content; with handles ``X`` and ``X-n`` issued,
  ``X-n``'s answer is approved and a dispute it raises settled; a ruling without it keeps the stem's fail-closed rule.
- N7: ``three_valued_answer``, ``derived_outputs`` and ``key_nodes`` take ``key`` under ``keys``' rule.
- N-b: ``[verification] execution`` lists the implementation's and the suite's digests; a change voids it, named.
- A-N1: an identity object's sub-field unknown on either side is never named.
Standard library; the store-backed parts skip without the pins. No network; the clock pinned."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402
import gate_cli  # noqa: E402
import review  # noqa: E402
import store  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote"


# ---- N4: canonical corpus lines
def test_n4_the_corpus_line_is_canonical_json_so_tab_newline_and_null_never_collide():
    row = lambda a, v, d: {"artefact": a, "version": v, "sha256": d}  # noqa: E731
    want = hashlib.sha256((json.dumps(["a.md", "v1", "1" * 64], separators=(",", ":")) + "\n").encode()).hexdigest()
    assert store.corpus_digest([row("a.md", "v1", "1" * 64)]) == want
    # the old line, <artefact>\t<version>\t<sha256>, read these pairs alike
    assert store.corpus_digest([row("a\tv1", "x", "d")]) != store.corpus_digest([row("a", "v1\tx", "d")])
    assert store.corpus_digest([row("a", "v1", "d\nb\tv1\te")]) != store.corpus_digest([row("a", "v1", "d"), row("b", "v1", "e")])
    assert store.corpus_digest([row("a", None, None)]) != store.corpus_digest([row("a", "", "")]), "null is not the empty text"
    rows = [row("b", "v1", "2"), row("a", None, "1"), row("a", "v2", "3")]
    assert store.corpus_digest(rows) == store.corpus_digest(list(reversed(rows))), "sorted, whatever the adapter's order"


# ---- N3 and A-N1: one differs, on both readers
NOW = {"task_profile": "a" * 64, "register": {"tag": "v0.2.13", "commit": "c" * 40, "why": None, "files": "f" * 64},
       "knowgov": {"version": "0.8.0", "commit": "d" * 40, "describe": "v0.8.0"}, "corpus": "e" * 64,
       "attestations": "1" * 64, "captures": "2" * 64, "as_of": "2026-10-30"}


def test_a_n1_a_sub_field_unknown_on_either_side_is_never_named():
    partly = {**NOW, "register": {"tag": None, "commit": "c" * 40, "why": None, "files": None},
              "knowgov": {"version": "0.8.0", "commit": None, "describe": None}}
    assert gate_cli.differs(partly, NOW) == [], "a partly unknown object agrees on every sub-field both know"
    assert gate_cli.differs(NOW, partly) == [], "this run's unknown sub-field is no difference either"
    assert gate_cli.differs({**NOW, "register": {k: v for k, v in NOW["register"].items() if k != "files"}}, NOW) == [], \
        "a report from before task-0320 lacks files: unknown"
    moved = {**partly, "register": {**partly["register"], "commit": "0" * 40}, "knowgov": {**partly["knowgov"], "version": "0.7.0"}}
    assert gate_cli.differs(moved, NOW) == ["register", "knowgov"]
    assert gate_cli.differs({**NOW, "register": {**NOW["register"], "files": "0" * 64}}, NOW) == ["register"], \
        "a register file edited under the same tag and commit"
    assert gate_cli.differs({**NOW, "attestations": "0" * 64, "captures": None}, NOW) == ["attestations"]
    assert gate_cli.differs(None, NOW) == [] and gate_cli.differs({}, NOW) == []


def test_n3_the_command_and_the_mcp_reader_report_one_differs_list():
    import mcp_server
    from test_mcp_server import Stub, _call, _Day
    stub = Stub()
    server = mcp_server.Server(mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(stub)))
    from subject import SUBJECT
    from tasks import TASKS
    for on, want in (("record", []), ("2026-12-31", ["as_of"])):
        got = _call(server, "gate_verdict", {"scenario": stub.scenario, "baseline": "record", "as_of": on})["result"]
        assert got["isError"] is False, got
        mcp = got["structuredContent"]["baseline"]
        with _Day():
            import cadence
            base = gate_cli._baseline("record", SUBJECT, stub.scenario, "codegen")
            cli = gate_cli.evaluate(stub, subject=SUBJECT.id, scenario=stub.scenario, task="codegen", spec=TASKS["codegen"],
                                    threshold="blocker", baseline=base, loaded=False, version="v1",
                                    as_of=cadence.as_of(on).isoformat())
        assert mcp["differs"] == cli["baseline"]["differs"] == want, (on, mcp, cli["baseline"])
        lines = gate_cli.drift_lines("record", gate_cli.identity_drift(base[0]["identity"], cli))
        assert [ln.split(": ")[2].split(" differs")[0] for ln in lines] == want, "the stderr lines name the same fields"


def test_n3_the_schema_admits_differs_and_earlier_v3_reports_still_validate():
    import schema_check
    schema = json.loads((HARNESS / "schemas" / "gate-report.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]
    assert "differs" in props["baseline"]["properties"] and "differs" not in props["baseline"]["required"]
    for f in ("attestations", "captures"):
        assert f in props and f not in schema["required"], f
    assert "files" in props["register"]["properties"] and "files" not in props["register"]["required"]
    assert props["baseline"]["properties"]["differs"]["items"]["enum"] == list(gate_cli.IDENTITY_FIELDS)
    early = {"schema_version": 3, "tool": "knowgov gate", "subject": "s", "scenario": "S1", "task": "codegen", "store": "rdflib",
             "loaded": True, "verdict": "PROCEED", "why": "", "threshold": "blocker", "findings": [],
             "counts": {s: 0 for s in gate_cli.SEVERITIES}, "keys": {"total": 0, "below_verified": 0, "flagged": 0},
             "conflicts": 0, "stale": [], "suspect_derived": [], "levels": {}, "exit_code": 0, "task_profile": None,
             "baseline": {"source": "record", "verdict": "PROCEED", "regression": False, "worse_verdict": False,
                          "regressed_keys": [], "new_suspect": []},
             "register": {"tag": None, "commit": None, "why": "x"}, "knowgov": {"version": None, "commit": None, "describe": None}}
    assert schema_check.validate(early, schema) == [], schema_check.validate(early, schema)
    later = {**early, "attestations": "1" * 64, "captures": None, "register": {**early["register"], "files": "f" * 64},
             "baseline": {**early["baseline"], "differs": ["register"]}}
    assert schema_check.validate(later, schema) == [], schema_check.validate(later, schema)


# ---- N2: what the load used, recorded in the store
def _env(root: Path | None = None, register: Path | None = None) -> dict:
    env = {**os.environ, "KG_STORE": "rdflib", "KG_CLOCK": "pinned", "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("KG_RDFLIB_FILE", None)
    if root is not None:
        env.update(KG_SUBJECT=str(root), KG_SUBJECTS=str(root.parent))
        env.setdefault("KG_REGISTER", str(HARNESS.parent / "demo" / "register"))   # a copy outside the checkout names its register (task-0334)
    if register is not None:
        env["KG_REGISTER"] = str(register)
    return env


def _gate(root: Path | None = None, register: Path | None = None, *args) -> dict:
    p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", "--as-of", "record", *args],
                       capture_output=True, text=True, env=_env(root, register), timeout=600)
    assert p.returncode in (0, 1), p.stderr[-800:]
    return json.loads(p.stdout)


CAPTURE = """format = 1

[capture]
subject = "cargo_quote"
scenario = "S1"
task = "codegen"
owner = "ORG-0002"
from = "employee-1"
on = 2026-11-02
record = "captures/2026-11-02-ORG-0002-employee-1.toml"

[[answer]]
key = "response|hold_presence"
value = "{value}"
note = ""
"""


def test_n2_each_input_moves_its_own_field_and_a_skipped_file_moves_none():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cargo_quote"
        shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
        base = _gate(root)
        for f in ("attestations", "captures"):
            assert len(base[f] or "") == 64, (f, base[f])
        assert len(base["register"]["files"] or "") == 64, base["register"]
        same = lambda a, b, but: {f: a[f] for f in gate_cli.IDENTITY_FIELDS if f not in but} == \
            {f: b[f] for f in gate_cli.IDENTITY_FIELDS if f not in but}  # noqa: E731
        # a skipped file: not a capture (no .toml), and a review of another scenario
        caps = root / "captures"
        (caps / "reviews").mkdir(parents=True)
        (caps / "README.md").write_text("notes\n", encoding="utf-8")
        (caps / "reviews" / "2026-11-03-employee-3.toml").write_text(
            'format = 1\n\n[review]\nby = "employee-3"\non = 2026-11-03\nrecord = "m.md"\nscenario = "S2"\n', encoding="utf-8")
        skipped = _gate(root)
        assert skipped["captures"] == base["captures"] and same(skipped, base, ()), "a file the load skipped moves nothing"
        # a capture the load applies, then its content edited
        (caps / "2026-11-02-ORG-0002-employee-1.toml").write_text(CAPTURE.format(value="held_unscreened only"), encoding="utf-8")
        one = _gate(root)
        assert one["captures"] != base["captures"] and same(one, base, ("captures",)), "only captures moves"
        (caps / "2026-11-02-ORG-0002-employee-1.toml").write_text(CAPTURE.format(value="held"), encoding="utf-8")
        edited = _gate(root)
        assert edited["captures"] not in (one["captures"], base["captures"])
        # [verification] as read: a scope edited, nothing else
        m = root / "subject.toml"
        text = m.read_text(encoding="utf-8")
        old = 'execution_scope = "suite scenario {scenario} on reference_impl.py (smoke 2026-10-30)"'
        assert text.count(old) == 1
        m.write_text(text.replace(old, old.replace("smoke 2026-10-30", "smoke 2026-10-31")), encoding="utf-8")
        scoped = _gate(root)
        assert scoped["attestations"] != edited["attestations"] and same(scoped, edited, ("attestations", "configuration")), \
            "subject.toml is read whole into configuration too (task-0335)"
        # a register file edited under the same tag and commit
        reg = Path(td) / "register"
        shutil.copytree(ROOT / "demo" / "register", reg)
        plain = _gate(root, reg)
        unit = next((reg / "organisation").glob("*.toml"))
        unit.write_text(unit.read_text(encoding="utf-8") + "\n# an edit under the same tag\n", encoding="utf-8")
        moved = _gate(root, reg)
        assert moved["register"]["files"] != plain["register"]["files"]
        assert {k: moved["register"][k] for k in ("tag", "commit")} == {k: plain["register"][k] for k in ("tag", "commit")}
        (Path(td) / "base.json").write_text(json.dumps(plain), encoding="utf-8")
        p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", "--as-of", "record",
                            "--baseline", str(Path(td) / "base.json")], capture_output=True, text=True, env=_env(root, reg), timeout=600)
        assert json.loads(p.stdout)["baseline"]["differs"] == ["register"], p.stderr[-600:]
        assert " register differs: " in p.stderr


def test_n2_register_files_cover_what_the_load_reads_and_nothing_else():
    """The register's ``files`` digest is over the files a load reads (its own loader's, recorded as it opens them,
    and the issued-handles list): a README, a stray file or SOURCE.md edited moves nothing; a node file, a metamodel
    file or the handles list edited moves it."""
    import register_impact
    with tempfile.TemporaryDirectory() as td:
        reg = Path(td) / "register"
        shutil.copytree(ROOT / "demo" / "register", reg, ignore=shutil.ignore_patterns("__pycache__"))
        base = register_impact.files_digest(reg)
        assert base and len(base) == 64
        read = {p.relative_to(reg.resolve()).as_posix() for p in register_impact.loaded_files(reg)}
        assert {"metamodel/types.toml", "glossary/glossary.toml", "capabilities/CAP-0001.toml", "people/handles.toml"} <= read, read
        assert not any(r.startswith(("tools/", "decisions/", "exports/")) or r == "SOURCE.md" for r in read), read
        (reg / "README.md").write_text("# notes\n", encoding="utf-8")
        (reg / "capabilities" / "notes.txt").write_text("a stray file\n", encoding="utf-8")
        (reg / "SOURCE.md").write_text((reg / "SOURCE.md").read_text(encoding="utf-8") + "\n<!-- edited -->\n", encoding="utf-8")
        assert register_impact.files_digest(reg) == base, "a file no load reads moves nothing"
        for rel in ("capabilities/CAP-0001.toml", "metamodel/lifecycle.toml", "people/handles.toml"):
            p = reg / rel
            keep = p.read_bytes()
            p.write_bytes(keep + b"\n# edited under the same tag\n")
            assert register_impact.files_digest(reg) != base, rel
            p.write_bytes(keep)
        assert register_impact.files_digest(reg) == base


def test_n2_the_inputs_survive_export_and_import_and_are_a_read_of_the_port():
    rdf = need_rdflib()
    import mcp_server
    assert "inputs" in store.READS and "inputs" in mcp_server.READS
    a = rdf.RdflibStore(path="")
    a.ensure_agents("harness", "v1", {"id": "agent:m", "name": "m"}, {"id": "agent:l", "name": "l"})
    assert a.inputs() == {"attestations": None, "captures": None, "configuration": None, "code": None, "preload": None}, \
        "a store loaded before task-0320: unknown (configuration: task-0335; code and preload: task-0341)"
    a.record_inputs({"attestations": "1" * 64, "captures": "2" * 64})
    a.record_inputs({"reviews": "3" * 64})
    got = a.inputs()
    assert got["attestations"] == "1" * 64 and len(got["captures"]) == 64
    b = rdf.RdflibStore(path="")
    b.import_turtle(a.export_turtle())
    assert b.inputs() == got
    a.record_inputs({"reviews": "4" * 64})
    assert a.inputs()["captures"] != got["captures"], "the reviews count in captures"


# ---- G1, G2: the giver from the capture's content
class Store:
    def __init__(self, rows):
        self.rows = rows

    def assertion_brief(self, aid):
        r = next((x for x in self.rows if x["id"] == aid), None)
        return None if r is None else {k: r[k] for k in ("id", "key", "value", "basis", "status")} | {"agent": r.get("agent", "harness")}

    def key_evidence(self, key, live):
        return [x for x in self.rows if x["key"] == key and x["status"] in live]

    def declared_gap(self, gid):
        return None

    def lint_gaps(self):
        return []


STATUSES = "response|statuses"
HANDLES = {**{h: {"unit": "ORG-0002", "roles": {"gives"}, "issued": None, "withdrawn": None} for h in ("ops", "ops-2")},
           "employee-3": {"unit": "ORG-0002", "roles": {"approves", "closes"}, "issued": None, "withdrawn": None}}
X_N = "A:cap:2026-11-05-ORG-0002-ops-2:1@capture"   # ops-2's first file, or ops's second the same day


def _answer(aid, handle, value="held", status="proposed", key=STATUSES):
    return {"id": aid, "key": key, "value": value, "basis": "elicited", "status": status, "fragments": [], "agent": handle}


def _doc(aid, value="quoted", status="disputed", key=STATUSES):
    return {"id": aid, "key": key, "value": value, "basis": "extracted", "status": status, "agent": "harness",
            "fragments": [{"text": f"{key}: {value}", "locator": "L1"}]}


def _check(rows, rulings, captures, strict=True):
    doc = {"review": {"by": "employee-3", "on": "2026-11-05", "record": "m.md"}, "ruling": rulings}
    return review.check(doc, Store(rows), handles=HANDLES, owners={STATUSES: ["ORG-0002"]}, units={}, captures=captures,
                        now=dt.date(2026, 11, 5), compatible=lambda a, b, _p="": "equal" if a == b else "conflict", strict=strict)


def test_g1_the_review_records_the_giver_from_the_captures_content_and_binds_by_it():
    caps = {X_N: {"from": "ops-2", "on": dt.date(2026, 11, 5), "value": "held", "note": ""}}
    errs, rv = _check([_answer(X_N, "ops-2")], [{"assertion": X_N, "outcome": "approved"}], caps)
    assert errs == [] and [r["giver"] for r in rv["rulings"]] == ["ops-2"], (errs, rv)
    text = review.review_toml({**rv, "on": dt.date(2026, 11, 5)})
    assert 'giver = "ops-2"' in text
    import tomllib
    ru = tomllib.loads(text)["ruling"][0]
    # the load binds by the giver it records: ops-2's answer, the same id or again under another
    assert review.bind(Store([_answer(X_N, "ops-2")]), ru, HANDLES)[1]["why"] == "content"
    later = "A:cap:2026-11-07-ORG-0002-ops-2:1@capture"
    b, how = review.bind(Store([_answer(later, "ops-2")]), ru, HANDLES)
    assert b["id"] == later and how["why"] == "repaired", (b, how)
    # never another person's: ops's answer under the very id the ruling names (a file renamed) binds nowhere
    assert review.bind(Store([_answer(X_N, "ops")]), ru, HANDLES)[0] is None
    # the giver comes from the content, never the file name: a capture of that stem given by ops records ops
    errs, rv = _check([_answer(X_N, "ops")], [{"assertion": X_N, "outcome": "approved"}], {X_N: {**caps[X_N], "from": "ops"}})
    assert errs == [] and rv["rulings"][0]["giver"] == "ops", (errs, rv)
    # a giver the reviewer wrote that the content contradicts is refused
    errs, _rv = _check([_answer(X_N, "ops-2")], [{"assertion": X_N, "outcome": "approved", "giver": "ops"}], caps)
    assert any("was given by ops-2 (its own content)" in e for e in errs), errs


def test_g2_a_dispute_raised_by_x_n_is_settled_by_a_review():
    rows = [_answer(X_N, "ops-2", status="disputed"), _doc("A:oas:response|statuses@v1"), _doc("A:spec:response|statuses@v1")]
    caps = {X_N: {"from": "ops-2", "on": dt.date(2026, 11, 5), "value": "held", "note": ""}}
    rulings = [{"assertion": X_N, "outcome": "approved"}, {"assertion": "A:oas:response|statuses@v1", "outcome": "rejected"},
               {"assertion": "A:spec:response|statuses@v1", "outcome": "rejected"}]
    errs, rv = _check(rows, rulings, caps)
    assert errs == [] and len(rv["rulings"]) == 3, errs
    import tomllib
    written = tomllib.loads(review.review_toml({**rv, "on": dt.date(2026, 11, 5)}))
    errs, at_load = _check(rows, written["ruling"], caps, strict=False)
    assert errs == [] and at_load["skipped"] == [] and [r["statement"] for r in at_load["rulings"]][0] == X_N, (errs, at_load)


def test_g1_a_ruling_without_its_giver_keeps_the_fail_closed_rule_and_names_decision_0038():
    ruling = {"assertion": X_N, "key": STATUSES, "value": "held", "sha256": review.content_digest([]), "outcome": "approved"}
    assert review.bind(Store([_answer(X_N, "ops-2")]), ruling, HANDLES) == (None, {"why": "ambiguous", "to": []})
    errs, rv = _check([_answer(X_N, "ops-2")], [{"assertion": X_N, "outcome": "approved"}], captures={})
    msg = " ".join(errs)
    assert "two givers" in msg and "decision-0038" in msg and "decision pending" not in msg and rv["rulings"] == [], errs


# ---- N7: one key rule on the single-key tools
def test_n7_the_single_key_tools_refuse_what_keys_refuses_with_the_value_as_sent():
    import mcp_server
    from test_mcp_server import _server
    server, _stub = _server()
    tools = {t["name"]: t for t in server.table}
    bad = ("nonsense", "a|b c", "a|b​", "a|\U0001d400", " |x", "a||b")
    for name, extra in (("three_valued_answer", {}), ("derived_outputs", {}), ("key_nodes", {})):
        schema = tools[name]["inputSchema"]["properties"]["key"]
        assert schema["pattern"] == mcp_server.KEY_ITEM["pattern"], name
        for key in bad:
            r = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": {"key": key, **extra}}})
            assert r.get("error", {}).get("code") == -32602, (name, key, r)
            assert repr(key)[1:-1] in r["error"]["message"] or key in r["error"]["message"], (name, key, r["error"]["message"])
            gate = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "gate_verdict", "arguments": {"keys": [key]}}})
            assert gate.get("error", {}).get("code") == -32602, ("keys refuses it too", key)


# ---- N-b: execution bound to the implementation and the suite
def test_n_b_the_public_subjects_and_the_claim_probe_list_their_implementation_and_suite():
    import tomllib
    import check_subject
    for root in (CQ, ROOT / "subjects" / "jef_data_load", ROOT / "tools" / "fixtures" / "claim_probe"):
        m = tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))
        ex = m["verification"]["execution"]
        for which in ("implementation", "suite"):
            rel, files = check_subject.code_digests(m, root, which)
            if rel is None:
                assert which not in ex, (root.name, which)
                continue
            assert files and set(files.values()) <= set(ex[which]), (root.name, which)
        rep = check_subject.Report(root)
        check_subject.check_execution_code(rep, m, root, ex)
        assert rep.findings == [], (root.name, rep.findings)


def test_n_b_a_changed_implementation_or_suite_is_named_by_check_subject():
    import tomllib
    import check_subject
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cargo_quote"
        shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
        m = tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))
        for which, rel in (("implementation", m["reference"]["code"]), ("suite", m["oracle"]["script"])):
            p = root / rel
            keep = p.read_bytes()
            p.write_bytes(keep + b"\n# weakened\n")
            rep = check_subject.Report(root)
            check_subject.check_execution_code(rep, m, root, m["verification"]["execution"])
            assert [f["level"] for f in rep.findings] == ["error"] and rel in rep.findings[0]["message"] \
                and "decision-0038" in rep.findings[0]["message"], (which, rep.findings)
            p.write_bytes(keep)
        rep = check_subject.Report(root)
        lacking = {k: v for k, v in m["verification"]["execution"].items() if k != "suite"}
        check_subject.check_execution_code(rep, m, root, lacking)
        assert [(f["level"], "lists no suite digests" in f["message"]) for f in rep.findings] == [("warning", True)], rep.findings


def test_n_b_the_load_voids_execution_when_the_implementation_or_suite_changed_and_the_gate_names_it():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cargo_quote"
        shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
        pristine = _gate(root)
        assert pristine["verdict"] == "PROCEED" and not [f for f in pristine["findings"] if f["kind"] == "attestation"], pristine["findings"]
        import tomllib
        m = tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))
        for rel in (m["reference"]["code"], m["oracle"]["script"]):
            p = root / rel
            keep = p.read_bytes()
            p.write_bytes(keep + b"\n# a helper changed\n")
            rep = _gate(root)
            named = [f for f in rep["findings"] if f["kind"] == "attestation" and f["ref"] == rel]
            assert len(named) == 1 and named[0]["severity"] == "major" and "decision-0038" in named[0]["message"], rep["findings"]
            assert rep["verdict"] != "PROCEED", "nothing is verified by execution any more"
            p.write_bytes(keep)
        assert _gate(root)["verdict"] == "PROCEED", "restored: verified again"

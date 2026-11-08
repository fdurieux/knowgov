"""task-0205 (doc-0030 S1, S3, S6, S7, S8, I11, I12): the store and load single fixes, each a probe from the
review turned into a test. S7 and S3 are also proven on a real file and, for S7, on Neo4j by
tools/check_snapshots.py's SNAP-09 (harness.yml on rdflib, the stack job on Neo4j)."""
from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import load_memory as lm  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402


# ---- S1: a store = false artefact with a mapper -------------------------------------------------

def test_s1_an_unstored_artefacts_statements_are_not_loaded_and_the_counts_match_the_nodes():
    store_rdflib = need_rdflib()
    import load
    from kitio import kit_for
    from subject import SUBJECT
    art = next(a["key"] for a in SUBJECT.artefacts if a["key"] in load.STORE and SUBJECT.mappers.get(a["key"]) not in (None, "links"))
    keep = load.STORE
    load.STORE = keep - {art}   # as if the manifest said store = false beside its mapper
    try:
        st = store_rdflib.RdflibStore()
        st.wipe()
        n = load.load_scenario(st, SUBJECT.order[0], kit_for(SUBJECT.order[0]), activity_note="S1 probe")
        assert not [x for x in st.nodes("Assertion") if st.prop(x, "artefact") == art], f"{art}'s statements were loaded"
        assert not [f for f in st.nodes("Fragment") if st.prop(f, "artefact") == art], f"{art}'s fragments were loaded"
        assert n["fragments"] == len(st.nodes("Fragment")), (n["fragments"], len(st.nodes("Fragment")))
        assert n["assertions"] == len(st.nodes("Assertion")), (n["assertions"], len(st.nodes("Assertion")))
        assert load.statements_of(kit_for(SUBJECT.order[0])) == n["fragments"] + n["assertions"], "the forecast counts what is loaded"
    finally:
        load.STORE = keep


# ---- S3 and S7 on the rdflib file ---------------------------------------------------------------

def _writer(store_rdflib, path):
    return store_rdflib.RdflibStore(str(path), access="write")


def test_s3_a_publication_keeps_the_files_mode_and_a_first_one_is_0644():
    store_rdflib = need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        with _writer(store_rdflib, path) as st:
            st.ensure_entity("E1", "thing", "one")
        assert stat.S_IMODE(path.stat().st_mode) == 0o644
        os.chmod(path, 0o600)   # the operator's
        with _writer(store_rdflib, path) as st:
            st.ensure_entity("E2", "thing", "two")
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, oct(path.stat().st_mode)
        r = store_rdflib.RdflibStore(str(path), access="read")
        try:
            assert r.exists("E2")
        finally:
            r.close()


def test_s7_a_writer_that_wrote_nothing_publishes_nothing():
    store_rdflib = need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        with _writer(store_rdflib, path) as st:
            st.ensure_entity("E1", "thing", "one")
        before = path.stat()
        with _writer(store_rdflib, path) as st:   # reads, and sets what is already there
            assert st.exists("E1") and st.census()["nodes"] == 1
            st.ensure_entity("E1", "thing", "one")
            st.set_props(st.node("E1"), {"name": "one"})
        after = path.stat()
        assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns), "a writer that wrote nothing republished"
        with _writer(store_rdflib, path) as st:
            st.set_props(st.node("E1"), {"name": "uno"})
        assert path.stat().st_ino != before.st_ino, "a writer that wrote publishes"
        with _writer(store_rdflib, Path(td) / "never.ttl"):
            pass
        assert not (Path(td) / "never.ttl").exists(), "an empty writer creates no store file"


class _Tx:
    def __init__(self, log):
        self.log = log

    def run(self, cypher, **params):
        self.log.append(cypher)
        return _Result()

    def commit(self):
        self.log.append("COMMIT")

    def rollback(self):
        self.log.append("ROLLBACK")

    def close(self):
        pass


class _Result:
    def consume(self):
        return None

    def __iter__(self):
        return iter(())


class _Session:
    def __init__(self, log):
        self.log = log

    def begin_transaction(self, **_kw):
        return _Tx(self.log)


def test_s7_on_neo4j_a_unit_that_only_read_rolls_back_and_publishes_nothing():
    import store_neo4j
    log: list[str] = []
    st = store_neo4j.Neo4jStore.__new__(store_neo4j.Neo4jStore)
    st.access = "write"
    st._pub = store_neo4j._Unit(None, _Session(log), "bolt://probe", "write", "r", "w")
    st._pub.token, st._pub.epoch = "t", 1
    st._pub.meta = lambda f: (_ for _ in ()).throw(AssertionError("the sequence lock was taken: a publication began"))
    st.run("MATCH (x:Assertion) RETURN x.id AS id")
    st.run("MATCH (g:Gap) WHERE g.kind = $k RETURN count(g) AS n", k="missing")
    st.commit()
    assert log[-1] == "ROLLBACK" and "COMMIT" not in log and st._pub.tx is None, log
    for cypher in ("MATCH (n {id:$id}) SET n.x = 1", "MERGE (n:Entity {id:$id})", "MATCH (n) DETACH DELETE n",
                   "CREATE (n:X)", "MATCH (n) REMOVE n.x", "UNWIND $r AS r MATCH (n {id:r}) set n.y = 2"):
        assert store_neo4j.WRITES.search(cypher), cypher
    for cypher in ("MATCH (x:Assertion) RETURN x.created_at AS c, x.offset AS o", "MATCH (r:Reset) RETURN r.settled AS s"):
        assert not store_neo4j.WRITES.search(cypher), cypher
    st._pub.dirty = False
    st.run("MATCH (n {id:$id}) SET n.x = 1", id="a")
    assert st._pub.dirty, "a write statement marks the unit"


# ---- S8: invalidated_at -------------------------------------------------------------------------

def test_s8_invalidated_at_is_the_changes_instant_on_both_adapters():
    store_rdflib = need_rdflib()
    st = store_rdflib.RdflibStore()
    st.wipe()
    st.ensure_agents("harness", "v1", {"id": "agent:h", "name": "h"}, {"id": "agent:l", "name": "l"})
    st.create_activity("act:1", "extraction", "2026-11-01T00:00:00+00:00", "harness", "probe", "agent:harness")
    st.ensure_entity("E", "thing", "E")
    st.create_assertion({"id": "A:1@v1", "predicate": "p", "value": "1", "text": "t", "basis": "authored", "artefact": "a",
                         "key": "E|p", "version": "v1"}, "E", "act:1", "agent:harness", [])
    at = "2026-11-08T00:00:00+00:00"
    st.invalidate_keys({"E|p": "the register withdrew it"}, at)
    assert st.prop(st.node("A:1@v1"), "invalidated_at") == at
    neo = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    rdf = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    assert "epochSeconds" not in neo and neo.count("x.invalidated_at=$at") == 3, "Neo4j: the change's instant, never the server's clock"
    assert '"invalidated_at": self._seq' not in rdf and rdf.count('"invalidated_at": at') == 3, "rdflib: the change's instant, never a sequence"
    change = (ROOT / "harness" / "change.py").read_text(encoding="utf-8")
    gate_cli = (ROOT / "harness" / "gate_cli.py").read_text(encoding="utf-8")
    assert "r_stale(s, version, at=now())" in change and "rc.apply(st, landed, at=now())" in gate_cli


# ---- S6: the preflight counts stage-2 loads -----------------------------------------------------

class _Mem:
    def __init__(self, limit=1 << 20, published=0):
        self.limit, self.published = limit, published

    def transaction_memory(self):
        return {"published": self.published, "limit": {"bytes": self.limit, "setting": "db.memory.transaction.max", "value": "1MiB"}}


def test_s6_the_preflight_counts_a_stage2_reload_which_adds_to_its_scenarios_graph():
    try:
        lm.preflight(_Mem(published=240), [240, [226, 50], 226])
        raise AssertionError("not refused")
    except lm.LoadTooLarge as e:   # 240+226+50+226 written; the wipes delete 240, 240 and 226+50
        assert "the run's 4 loads in one unit" in str(e) and "742 statements written and 756 deleted" in str(e), str(e)
    run = (ROOT / "harness" / "run.py").read_text(encoding="utf-8")
    assert "load_memory.preflight(d, unit_loads(SUBJECT, args.scenarios))" in run


def test_s6_unit_loads_names_each_stage2_reload():
    need_rdflib()   # the mappers (PyYAML)
    import change
    from subject import SUBJECT
    loads = dict(zip(SUBJECT.order, change.unit_loads(SUBJECT, SUBJECT.order)))
    staged = [sc for sc in SUBJECT.order if SUBJECT.scenario(sc).get("stage2")]
    assert staged and all(len(loads[sc]) == 2 and loads[sc][1] > 0 for sc in staged), loads
    assert all(len(loads[sc]) == 1 for sc in SUBJECT.order if sc not in staged)
    size = lm.sizing(SUBJECT)
    assert all(size["statements"][sc] == sum(loads[sc]) for sc in SUBJECT.order), "the sizing counts stage 2 too"


# ---- I11: a duplicate short, a duplicated row, a parse error named ------------------------------

def _subject(td: Path, rows: str, *, twin: bool = False) -> Path:
    root = td / "probe"
    root.mkdir()
    (root / "requirements.md").write_text(f"# Requirements\n\n{rows}", encoding="utf-8")
    arts = ['[[artefact]]\nkey = "kit/requirements.md"\nshort = "req"\nfamily = "requirements"\nformat = "markdown"\n'
            'label = "requirements"\nformat_label = "markdown"\npath = "requirements.md"\nmapper = "requirements"\n']
    if twin:
        (root / "more.md").write_text("# More\n\n| REQ-09 | Another. |\n", encoding="utf-8")
        arts.append('[[artefact]]\nkey = "kit/more.md"\nshort = "req"\nfamily = "requirements"\nformat = "markdown"\n'
                    'label = "more"\nformat_label = "markdown"\npath = "more.md"\nmapper = "requirements"\n')
    (root / "subject.toml").write_text('[subject]\nid = "probe"\nname = "Probe"\nlisted = false\ndescription = "I11"\n\n'
                                       + "\n".join(arts), encoding="utf-8")
    return root


def test_i11_check_subject_refuses_a_duplicate_short():
    import check_subject
    with tempfile.TemporaryDirectory() as td:
        rep = check_subject.check(_subject(Path(td), "| REQ-01 | One. |\n", twin=True), run_yield=False)
    dup = [f for f in rep["findings"] if f["rule"] == "duplicate" and "short" in f["message"]]
    assert rep["exit_code"] == 1 and len(dup) == 1 and "kit/requirements.md" in dup[0]["message"], rep["findings"]


def test_i11_check_subject_refuses_a_duplicated_row_and_the_load_names_the_document():
    need_rdflib()   # the mappers (PyYAML)
    import check_subject
    import extract
    with tempfile.TemporaryDirectory() as td:
        root = _subject(Path(td), "| REQ-01 | One. |\n| REQ-02 | Two. |\n| REQ-01 | One again. |\n")
        rep = check_subject.check(root)
    dup = [f for f in rep["findings"] if f["rule"] == "duplicate" and "row/REQ-01" in f["message"]]
    assert rep["exit_code"] == 1 and len(dup) == 1 and dup[0]["where"] == "[[artefact]] kit/requirements.md", rep["findings"]
    bag = extract.extract_requirements("kit/requirements.md", "| REQ-01 | a |\n| REQ-01 | b |\n")
    assert extract.duplicate_locators(bag) == ["row/REQ-01"]
    from subject import SUBJECT
    key, mapper = next((k, m) for k, m in SUBJECT.mappers.items() if m in ("requirements_json", "dmn", "bpmn", "openapi", "decision_table", "requirements"))
    bad = {key: "{ this is not the document" if mapper == "requirements_json" else "<not xml" if mapper in ("dmn", "bpmn")
           else "openapi: [unclosed" if mapper == "openapi" else "| REQ-01 | a |\n| REQ-01 | b |\n"}
    try:
        extract.extract_all(bad, "")
        raise AssertionError("an unreadable document loaded")
    except extract.DocumentUnreadable as e:
        assert str(e).startswith(f"{key}: ") and key in str(e), str(e)


def test_i11_the_gate_names_a_document_it_cannot_load_never_the_store():
    src = (ROOT / "harness" / "gate_cli.py").read_text(encoding="utf-8")
    body = src.split("def _gate_on(", 1)[1]
    assert body.index("except DocumentUnreadable as e:") < body.index('"the store did not answer:'), "the document named first"
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    assert "one short, " in load.split("def _artefact_of(", 1)[1].split("\ndef ", 1)[0], "two artefacts with one short refused"


# ---- I12: raw-byte digests and a BOM ------------------------------------------------------------

def test_i12_an_unchanged_crlf_document_reads_checked():
    import hashlib
    import preload
    from subject import Subject
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "inst" / "subjects" / "probe"
        root.mkdir(parents=True)
        (root / "spec.md").write_bytes(b"# Spec\r\n\r\nA line.\r\n")
        (root / "subject.toml").write_text('[subject]\nid = "probe"\nname = "Probe"\nlisted = false\ndescription = "I12"\n\n'
                                           '[[artefact]]\nkey = "contract/spec.md"\nshort = "spec"\nfamily = "prose"\nformat = "markdown"\n'
                                           'label = "spec"\nformat_label = "markdown"\npath = "spec.md"\n', encoding="utf-8")
        sub = Subject(root)
        kit = {"contract/spec.md": (root / "spec.md").read_text(encoding="utf-8")}
        assert "\r" not in kit["contract/spec.md"], "the kit reads text"
        raw = hashlib.sha256((root / "spec.md").read_bytes()).hexdigest()
        rep = {"instance": str((Path(td) / "inst").resolve()), "linters": [{"tool": "markdownlint", "version": "0.1"}],
               "files": [{"file": "subjects/probe/spec.md", "state": "clean", "tool": "markdownlint", "sha256": raw, "why": "", "findings": []}]}
        os.environ.pop("KG_INSTANCE", None)
        v = preload.verdicts(sub, kit, ["contract/spec.md"], rep, "preload-report.json")["contract/spec.md"]
        assert v["state"] == "clean", v
        edited = {"contract/spec.md": kit["contract/spec.md"] + "Planted.\n"}
        assert preload.verdicts(sub, edited, ["contract/spec.md"], rep, "r")["contract/spec.md"]["state"] == "unchecked"


def test_i12_a_line_1_citation_after_a_bom_is_read():
    import citation
    assert citation.parse("﻿# knowgov-keys: REQ-01|text, P2|value\nimport os\n", "#") == ["REQ-01|text", "P2|value"]
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "a.py"
        p.write_bytes(b"\xef\xbb\xbf# knowgov-keys: REQ-01|text\n")
        assert citation.read(p) == ["REQ-01|text"]

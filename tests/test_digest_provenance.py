"""task-0342 (decision-0041 C2-7, brought into 0.10.0 on 2026-11-16): a stale digest names the file it was last recorded for.

Each load records which file every digest it read was recorded for (``Store.record_provenance``: the documents'
Versions, a directory's files, the code and suite an execution verification is compared against), on the tool's Agent
node, on both adapters. A wipe carries what the store held to the next load for the digests a ``[verification]``
declaration still lists, so after a file changes the old digest keeps its file. ``tools/check_subject.py --store``
reads it (``digest_provenance``, a port read) and its stale-digest errors name the file; without ``--store`` it opens
no store and its report is as before. The gate never reads it."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(ROOT / "tests")]
import check_subject  # noqa: E402
import store  # noqa: E402
from _skip import need_rdflib  # noqa: E402

H = lambda t: hashlib.sha256(t.encode()).hexdigest()  # noqa: E731
HEAD = {"subject": "s", "scenario": "S1", "version": "v1"}


def _row(text: str, file: str, kind: str = "document", **kw) -> dict:
    return {"sha256": H(text), "file": file, "kind": kind, **HEAD, **kw}


def test_the_merge_carries_only_what_a_declaration_still_lists_and_a_later_row_wins():
    old, gone, kept = _row("one\n", "doc.md"), _row("x\n", "other.md"), _row("y\n", "held.md")
    now = _row("two\n", "doc.md", scenario="S2")
    got = store.merge_provenance([old, gone], [kept], [now], keep={old["sha256"]})
    assert [r["sha256"] for r in got] == sorted({old["sha256"], kept["sha256"], now["sha256"]})
    again = store.merge_provenance([], got, [{**old, "scenario": "S3"}], keep=set())
    assert next(r for r in again if r["sha256"] == old["sha256"])["scenario"] == "S3", "the later recording of a digest wins"
    assert store.provenance_of(store.provenance_text(got)) == got and store.provenance_of("not json") == []
    assert "digest_provenance" in store.READS and "record_provenance" not in store.READS


def test_the_rdflib_adapter_records_carries_across_a_wipe_and_round_trips():
    rd = need_rdflib()
    st = rd.RdflibStore(path="")
    human, llm = {"id": "agent:h", "name": "h"}, {"id": "agent:l", "name": "l"}
    st.ensure_agents("t", "v1", human, llm)
    first, other = _row("one\n", "doc.md"), _row("x\n", "other.md")
    st.record_provenance([first, other], keep=set())
    assert st.digest_provenance() == sorted([first, other], key=lambda r: r["sha256"])
    st.wipe()   # a later load: doc.md edited; its old digest is still listed, other.md's is not
    st.ensure_agents("t", "v1", human, llm)
    edited = _row("two\n", "doc.md", scenario="S2")
    st.record_provenance([edited], keep={first["sha256"], edited["sha256"]})
    assert {r["sha256"] for r in st.digest_provenance()} == {first["sha256"], edited["sha256"]}
    census = st.census()
    other_store = rd.RdflibStore(path="")
    other_store.ensure_agents("t", "v1", human, llm)
    other_store.record_provenance([_row("z\n", "z.md")], keep=set())
    other_store.import_turtle(st.export_turtle())   # the imported store's own provenance, nothing of the one it replaced
    assert other_store.digest_provenance() == st.digest_provenance() and other_store.census() == census
    other_store.record_provenance([], keep={H("z\n")})
    assert H("z\n") not in {r["sha256"] for r in other_store.digest_provenance()}


def test_a_load_records_every_digest_it_read_with_its_file_and_the_gate_never_reads_them():
    rd = need_rdflib()
    import gate_cli
    from subject import SUBJECT
    st = rd.RdflibStore(path="")
    sc = SUBJECT.order[0]
    gate_cli._load(st, sc)
    rows = {r["sha256"]: r for r in st.digest_provenance()}
    assert rows and all(r["subject"] == SUBJECT.id and r["scenario"] == sc and r["version"] == "v1" for r in rows.values())
    for v in st.version_digests():   # every Version the load holds, by its artefact
        assert rows[v["sha256"]]["file"] == v["artefact"] and rows[v["sha256"]]["kind"] == "document", v
    for p in st.part_digests():   # every file of a directory artefact, as <artefact><relative>
        assert rows[p["sha256"]]["file"] == p["artefact"] + p["part"], p
    code = SUBJECT.code() or {}
    assert code and all(rows[d] == {**rows[d], "file": f, "kind": "code"} for f, d in code.items()), "each code file by its path under the root"
    assert set(rows) == {v["sha256"] for v in st.version_digests()} | {p["sha256"] for p in st.part_digests()} | set(code.values())
    report = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=sc, task="codegen", spec=dict(SUBJECT.tasks["codegen"]), threshold="blocker",
                               baseline=None, loaded=True, version="v1", as_of="2026-11-16") if "codegen" in SUBJECT.tasks else {}
    assert "last recorded" not in json.dumps(report), "the gate never reads it"


def test_check_subject_names_the_file_a_stale_digest_was_last_recorded_for_only_when_a_store_was_read():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "doc.md").write_text("two\n", encoding="utf-8")
        m = {"artefact": [{"key": "doc", "path": "doc.md"}]}
        stale = H("one\n")
        texts = {}
        for name, prov in (("without", None), ("recorded", {stale: _row("one\n", "doc")}), ("unrecorded", {})):
            rep = check_subject.Report(root, prov)
            check_subject._stale_errors(rep, "[verification] approval", "approval", [stale], "")
            [f] = rep.findings
            texts[name] = f["message"]
        assert "recorded" not in texts["without"]
        assert f"{stale[:12]} was last recorded for doc, by the load of S1 v1" in texts["recorded"]
        assert f"{stale[:12]} was recorded by no load the store holds" in texts["unrecorded"]


def test_check_subject_reads_a_store_only_with_store_and_a_store_it_cannot_read_is_exit_2():
    need_rdflib()
    root = ROOT / "subjects" / "cargo_quote"
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "KG_STORE": "rdflib", "KG_RDFLIB_FILE": str(Path(td) / "store.ttl"), "PYTHONDONTWRITEBYTECODE": "1"}
        plain = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root), "--json"],
                               capture_output=True, text=True, env=env, timeout=600)
        read = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root), "--json", "--store"],
                              capture_output=True, text=True, env=env, timeout=600)
        assert plain.returncode == read.returncode == 0, (plain.stderr, read.stderr)
        assert json.loads(plain.stdout) == json.loads(read.stdout), "nothing stale: the report is as before"
        (Path(td) / "store.ttl").write_text("this is not turtle {", encoding="utf-8")
        bad = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root), "--store"],
                             capture_output=True, text=True, env=env, timeout=600)
        assert bad.returncode == 2 and "--store: the store cannot be read" in bad.stderr, bad.stderr
        again = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root)],
                               capture_output=True, text=True, env=env, timeout=600)
        assert again.returncode == 0, "without --store no store is opened"

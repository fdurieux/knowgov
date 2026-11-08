"""Task-0199, doc-0030 F2 (H6, R5) and doc-0032 §6 item 6: a derived output binds to what it was built on, and one
rule reads it suspect for the gate, the MCP reader and trace. tools/check_ledger_binding.py holds it end to end on
the example instance; it runs here on rdflib, and in CI on rdflib (harness.yml) and on Neo4j (demo.yml's stack
job). The unit tests below need no store."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402
import store  # noqa: E402

TOOL = "tools/check_ledger_binding.py"
ROW = "| P2 | heavy surcharge: if `weight_kg > 1244`, add `316.00` (flat) |"


class Fake:
    """What store.suspicion reads: assertion_brief and key_evidence."""

    def __init__(self, rows):
        self.rows = {r["id"]: r for r in rows}

    def assertion_brief(self, aid):
        r = self.rows.get(aid)
        return None if r is None else {"id": aid, "key": r["key"], "value": r["value"], "status": r["status"]}

    def key_evidence(self, key, live):
        return [r for r in self.rows.values() if r["key"] == key and r["status"] in live]


def _st(value="316.00", text=ROW, status="verified"):
    return Fake([{"id": "A:dt:P2|surcharge@v1", "key": "P2|surcharge", "value": value, "status": status, "fragments": [{"text": text}]}])


def _derived(recorded=None, status="verified"):
    return {"id": "derived:code@c0ffee1:x.py", "kind": "code", "sha256": "s", "used": [{"id": "A:dt:P2|surcharge@v1", "status": status}],
            "recorded": None if recorded is None else json.dumps(recorded)}


REC = [{"id": "A:dt:P2|surcharge@v1", "key": "P2|surcharge", "value": "316.00", "sha256": store.content_digest([{"text": ROW}])}]


def test_unchanged_content_is_not_suspect():
    [r] = store.suspicion(_st(), [_derived(REC)])
    assert not r["suspect"] and r["used_changed"] == [] and r["bound"]


def test_h6_the_same_id_with_another_value_is_suspect():
    [r] = store.suspicion(_st("341.00", ROW.replace("316.00", "341.00")), [_derived(REC)])
    assert r["suspect"] and r["used_changed"] == ["A:dt:P2|surcharge@v1"], r


def test_a_statement_no_longer_held_is_suspect():
    [r] = store.suspicion(Fake([]), [{**_derived(REC), "used": []}])
    assert r["suspect"] and r["used_changed"] == ["A:dt:P2|surcharge@v1"], r


def test_an_invalidated_statement_is_suspect_with_or_without_a_record_and_no_flag_decides():
    for rec in (None, REC):
        [r] = store.suspicion(_st(status="invalidated"), [_derived(rec, status="invalidated")])
        assert r["suspect"] and r["used_invalidated"] == ["A:dt:P2|surcharge@v1"] and r["used_changed"] == [], r


def test_the_read_rule_a_registration_with_no_record_reads_by_status_only():
    [r] = store.suspicion(_st("341.00", "other"), [_derived(None)])
    assert not r["suspect"] and not r["bound"], r


def test_suspect_rows_keep_the_records_shape_when_nothing_changed():
    rows = store.suspicion(_st(status="invalidated"), [_derived(None, status="invalidated")])
    assert store.suspect_rows(rows) == [{"id": "derived:code@c0ffee1:x.py", "kind": "code", "sha256": "s",
                                         "used_invalidated": ["A:dt:P2|surcharge@v1"]}]


def test_the_gate_s_suspect_message_is_unchanged_without_a_changed_statement():
    import gate_cli
    res = {"keys": {}, "verdict": "BLOCKED", "blocked_keys": [], "why": "x",
           "suspect_derived": [{"id": "d", "kind": "code", "used_invalidated": ["a", "b"]}]}
    [f] = [f for f in gate_cli.findings(res, set()) if f["kind"] == "suspect_derived"]
    assert f["message"] == ("d (code) used 2 statement(s) now invalidated (a, b): it may not be reused as it is: "
                            "regenerate it from the current statements") and f["related"] == ["a", "b"]


def test_every_reader_answers_by_the_one_rule():
    for name in ("store_rdflib.py", "store_neo4j.py"):
        src = (ROOT / "harness" / name).read_text(encoding="utf-8")
        for fn in ("suspect_derived", "all_derived", "derived_outputs"):
            body = src[src.index(f"    def {fn}(self)"):][:900]
            assert "suspicion(self" in body, f"{name} {fn}"
        assert "{suspect:true}" not in src and 'nodes("Derived", suspect=True)' not in src, f"{name}: no read on the stored flag"
    trace = (ROOT / "harness" / "trace.py").read_text(encoding="utf-8")
    assert "st.suspect_derived()" in trace and 'b.get("status") == "invalidated"' not in trace


def test_the_check_holds_on_rdflib():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "KG_STORE": "rdflib", "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("KG_RDFLIB_FILE", None)
        p = subprocess.run([sys.executable, str(ROOT / TOOL), str(Path(td) / "out")], env=env, cwd=ROOT,
                           capture_output=True, text=True, timeout=1500)
        assert p.returncode == 0 and "every check holds" in p.stdout, p.stdout[-3000:] + p.stderr[-1500:]


def test_ci_runs_it_on_both_stores():
    assert f"KG_STORE=rdflib python {TOOL} runs/ledger-binding" in (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f"python {TOOL} runs/ledger-binding" in (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")

"""Task-0144 (doc-0020 C3): the store reads over MCP. held_keys lists every held key with the gate's own
level and the classes requiring it, a key no class requires included; derived_outputs gives the outputs
built on a key, any state, or one output's statements, each read live, stale, superseded or rejected;
document_statements the statements a document yields, by version, and the outputs built on them. Stdlib on
a stub store through the server; on rdflib, the port's three reads on a store built through its writes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT), str(ROOT / "tests")]
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
import store  # noqa: E402
from tasks import TASKS  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402
import test_mcp_server as tm  # noqa: E402

EXTRA = "Z-extra|unrequired"


class Held(tm.Stub):
    """The stub store with the three reads: one key no class requires, one derived output on two statements."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rows[EXTRA] = [tm._row("xz", EXTRA, "7", status="proposed")]
        self.invalid = {"x0": {"id": "x0", "key": TASKS["codegen"]["keys"][1], "value": "41", "invalidated_by": "v2",
                               "verifications": [{"id": None, "valid_until": None}],
                               "successors": [{"id": "x0b", "value": "42", "status": "approved"}]},
                        "x1": {"id": "x1", "key": TASKS["codegen"]["keys"][2], "value": "41", "invalidated_by": "v2",
                               "verifications": [{"id": None, "valid_until": None}],
                               "successors": [{"id": "x1b", "value": "42", "status": "proposed"}]}}

    def held_keys(self):
        return [{"key": k, "n": len(v), "statuses": {r["status"]: 1 for r in v}} for k, v in sorted(self.rows.items())]

    def derived_outputs(self):
        k = TASKS["codegen"]["keys"]
        return [{"id": "derived:S1:G:run1", "kind": "python module", "sha256": "f" * 64, "suspect": True,
                 "used": [{"id": "x0", "key": k[1], "status": "invalidated", "artefact": "docs/pricing.md", "version": "v1"},
                          {"id": "x1", "key": k[2], "status": "invalidated", "artefact": "docs/pricing.md", "version": "v1"},
                          {"id": "x2", "key": k[3], "status": "verified", "artefact": "docs/pricing.md", "version": "v1"},
                          {"id": "xr", "key": k[4], "status": "rejected", "artefact": "docs/pricing.md", "version": "v1"}]}]

    def artefact_assertions(self, artefact):
        if artefact != "docs/pricing.md":
            return []
        return [{"id": r["id"], "key": k, "value": r["value"], "status": r["status"], "basis": r["basis"], "artefact": artefact,
                 "version": "v2" if r["id"] == "x2" else "v1", "fragments": [{"locator": "L3", "artefact": artefact}]}
                for k, rs in sorted(self.rows.items()) for r in rs]

    def stale_on_keys(self, keys):
        return [x for x in self.invalid.values() if x["key"] in keys]


def _server():
    st = Held()
    return mcp_server.Server(mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(st))), st


def _ok(s, name, args, schema):
    r = tm._call(s, name, args)["result"]
    assert r["isError"] is False, r["content"][0]["text"]
    got = r["structuredContent"]
    assert schema_check.validate(got, schema_check.load(schema)) == [], schema_check.validate(got, schema_check.load(schema))
    return got


def test_the_three_reads_are_the_ports_and_the_servers_view_lets_them_through():
    for name in ("held_keys", "derived_outputs", "artefact_assertions"):
        assert name in store.READS and name in mcp_server.READS and callable(getattr(store.Store, name))
    view = mcp_server.ReadOnlyStore(Held())
    assert view.held_keys() and view.derived_outputs()


def test_held_keys_lists_every_held_key_at_gate_verdicts_level_with_the_classes_requiring_it():
    s, st = _server()
    got = _ok(s, "held_keys", {}, "held-keys")
    assert [k["key"] for k in got["keys"]] == sorted(st.rows) and got["total"] == len(st.rows)
    gate = tm._call(s, "gate_verdict", {"keys": sorted(st.rows)})["result"]["structuredContent"]
    assert {k["key"]: k["level"] for k in got["keys"]} == gate["levels"]
    extra = next(k for k in got["keys"] if k["key"] == EXTRA)
    required = {k for spec in TASKS.values() for k in spec["keys"]}   # the subject's own classes: the stub's keys are CargoQuote's
    assert extra["required_by"] == [] and EXTRA in got["unrequired"]
    assert got["unrequired"] == sorted(k for k in st.rows if k not in required)
    first = next(k for k in got["keys"] if k["key"] == TASKS["codegen"]["keys"][1])
    assert "codegen" in first["required_by"]
    assert TASKS["codegen"]["keys"][0] in got["required_not_held"]   # the stub's absent key
    assert _ok(s, "held_keys", {"task": "codegen"}, "held-keys")["task"] == "codegen"
    assert tm._call(s, "held_keys", {"task": "keys"})["result"]["isError"] is True


def test_derived_outputs_from_a_key_or_an_id_reads_each_used_statement_live_stale_superseded_or_rejected():
    s, _ = _server()
    k = TASKS["codegen"]["keys"]
    by_key = _ok(s, "derived_outputs", {"key": k[1]}, "derived-outputs")
    assert [o["id"] for o in by_key["outputs"]] == ["derived:S1:G:run1"] and by_key["derived"] is None
    states = {u["id"]: (u["state"], u["superseded_by"]) for u in by_key["outputs"][0]["used"]}
    assert states == {"x0": ("superseded", ["x0b"]), "x1": ("stale", []), "x2": ("live", []), "xr": ("rejected", [])}
    one = _ok(s, "derived_outputs", {"derived": "derived:S1:G:run1"}, "derived-outputs")
    assert one["outputs"] == by_key["outputs"] and one["outputs"][0]["keys"] == sorted(k[1:5])
    assert _ok(s, "derived_outputs", {"key": EXTRA}, "derived-outputs")["outputs"] == []
    for bad in ({}, {"key": k[1], "derived": "derived:S1:G:run1"}, {"derived": "derived:nope"}, {"key": "no-bar"}):
        assert tm._refused(s, "derived_outputs", bad), bad   # a key off the rule: -32602 since task-0320 (N7)


def test_document_statements_names_what_a_document_yields_by_version_and_what_was_built_on_it():
    s, st = _server()
    got = _ok(s, "document_statements", {"document": "docs/pricing.md"}, "document-statements")
    assert got["versions"] == ["v1", "v2"] and got["total"] == sum(len(v) for v in st.rows.values())
    assert got["derived"] == ["derived:S1:G:run1"]
    assert next(x for x in got["statements"] if x["id"] == "x2")["derived"] == ["derived:S1:G:run1"]
    v2 = _ok(s, "document_statements", {"document": "docs/pricing.md", "version": "v2"}, "document-statements")
    assert [x["id"] for x in v2["statements"]] == ["x2"] and v2["version"] == "v2"
    for bad in ({"document": "nope.md"}, {"document": "docs/pricing.md", "version": "v9"}, {}):
        assert tm._refused(s, "document_statements", bad), bad


def test_the_store_reads_refuse_another_subjects_scenario_and_nothing_held():
    for held in (None, "S-other-subject"):
        st = Held(scenario=held)
        s = mcp_server.Server(mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(st)))
        for name, args in (("held_keys", {}), ("derived_outputs", {"key": "a|b"}), ("document_statements", {"document": "d"})):
            assert tm._call(s, name, args)["result"]["isError"] is True, (held, name)


def test_on_rdflib_the_ports_reads_answer_by_id_from_a_store_built_through_its_writes():
    rdf = need_rdflib()
    import test_store_order as so
    st = so._build(rdf, False)
    keys = st.held_keys()
    assert [k["key"] for k in keys] == ["k|a", "k|b", "k|c"]
    assert keys[0] == {"key": "k|a", "n": 3, "statuses": {"invalidated": 1, "proposed": 2}}
    d = st.derived_outputs()
    assert [x["id"] for x in d] == ["derived:S0:G:run1"] and d[0]["suspect"] is True
    assert [u["id"] for u in d[0]["used"]] == ["A:k|a@v1", "A:k|b@v1", "A:k|c@v1"]
    assert all(u["status"] == "invalidated" and u["version"] == "v1" for u in d[0]["used"])
    rows = st.artefact_assertions("doc.md")
    assert [r["id"] for r in rows] == sorted(r["id"] for r in rows) and len(rows) == 9
    v1 = next(r for r in rows if r["id"] == "A:k|a@v1")
    assert v1["fragments"] == [{"locator": "L0", "artefact": "doc.md"}, {"locator": "L1", "artefact": "doc.md"}]
    assert {r["version"] for r in rows} == {"v1", "v2"}
    assert st.artefact_assertions("other.md") == [] and so._build(rdf, True).derived_outputs() == d

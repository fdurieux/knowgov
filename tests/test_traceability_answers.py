"""task-0303 and task-0304 (decision-0035 B1, B2): what the trace ledger and the trace report answer.

B1: code_path's ledger leg names the entry's statement ids and keys, sorted, its state as trace check reads it
(current, drift, missing), and whether it is suspect: read from the store by the MCP reader (``trace.ledger_suspicion``,
the rule check reads, ``store.suspicion``), unchecked from the files-only command. From the keys it returns,
key_nodes reaches the register's nodes: file -> keys -> nodes.

B2: each trace finding resting on keys names their owner and route as the gate's key findings do (task-0102), one
resting on none names neither; the gate block names what it decided on (task_profile, register, knowgov) as the gate
report reads them; the CI annotations carry the owner and route.

A fake store with CargoQuote's keys, the example instance's code root, no database; the rdflib walkthrough runs in
harness.yml (tools/check_trace_walkthrough.py, tools/check_mcp_server.py)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import annotate  # noqa: E402
import example_instance  # noqa: E402
import gate_cli  # noqa: E402
import schema_check  # noqa: E402
import store  # noqa: E402
import trace  # noqa: E402
import upward  # noqa: E402
from subject import SUBJECT  # noqa: E402
from tests._skip import skip  # noqa: E402

# statement id -> key: two keys ORG-0001 owns, one ORG-0002 owns, in the example instance's subject
KEYS = {"A:3@v1": "P1|formula", "A:1@v1": "shipper_id|present", "A:2@v1": "QuoteAPI|on_store_failure"}
TRACE, CODE = schema_check.load("trace-report"), schema_check.load("code-path")


def _cargo_quote():
    if example_instance.SUBJECT.name != SUBJECT.id:
        skip("register-rows", f"the example instance is {example_instance.SUBJECT.name}'s, the subject {SUBJECT.id}")


class Store:
    """The port's reads trace and ``store.suspicion`` use, on statements keyed as the subject keys them."""
    name = "fake"

    def __init__(self, scenario: str | None = "S1"):
        self.derived: dict[str, dict] = {}
        self.status = {a: "approved" for a in KEYS}
        self.value = {a: "1" for a in KEYS}
        self.scenario = scenario

    def held(self):
        return {"scenario": self.scenario, "version": "v1"} if self.scenario else None

    def register_derived(self, did, kind, sha, ids, recorded=None):
        self.derived[did] = {"kind": kind, "sha256": sha, "ids": list(ids), "recorded": recorded}

    def _rows(self):
        return [{"id": d, "kind": x["kind"], "sha256": x["sha256"],
                 "recorded": None if x["recorded"] is None else json.dumps(x["recorded"]),
                 "used": [{"id": a, "status": self.status[a]} for a in x["ids"] if a in self.status]} for d, x in self.derived.items()]

    def all_derived(self):
        return [{"id": r["id"], "suspect": r["suspect"]} for r in store.suspicion(self, self._rows())]

    def suspect_derived(self):
        return store.suspect_rows(store.suspicion(self, self._rows()))

    def assertion_brief(self, aid):
        return {"id": aid, "key": KEYS[aid], "value": self.value[aid], "status": self.status[aid]} if aid in self.status else None

    def key_evidence(self, key, live):
        return [{"id": a, "value": self.value[a], "status": s, "fragments": [{"text": a + self.value[a]}]}
                for a, s in self.status.items() if KEYS[a] == key and s in live]

    def stale_on_keys(self, keys):
        return [{"id": a, "key": KEYS[a], "successors": []} for a, s in self.status.items() if s == "invalidated" and KEYS[a] in keys]


def _resolve(levels: dict[str, str] | None = None):
    levels = levels or {}

    def resolve(st, task, as_of=None):
        keys = {k: {"level": levels.get(k, "approved"), "flags": [], "assertions": [{"id": a} for a, kk in KEYS.items() if kk == k]}
                for k in sorted(set(KEYS.values()))}
        return {"verdict": "PROCEED", "why": "fake", "keys": keys, "blocked_keys": [], "stale": [], "suspect_derived": [],
                "below_verified": [], "flagged": []}
    return resolve


def _valid(rep, schema):
    errs = schema_check.validate(rep, schema)
    assert errs == [], errs
    return rep


def _registered(td: str, st: Store) -> tuple[Path, Path, Path]:
    inst = example_instance.build(Path(td) / "inst")
    led = Path(td) / "ledger.json"
    trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=_resolve())
    return inst, led, trace.read_map(inst)[1]


def test_code_path_names_the_entrys_ids_and_keys_sorted_and_its_state_as_trace_check_reads_it():
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        inst, led, root = _registered(td, Store())
        raw = json.loads(led.read_text(encoding="utf-8"))
        [e] = raw["entries"]
        e["assertions"] = list(reversed(sorted(e["assertions"])))   # the ledger's order is not the answer's
        led.write_text(json.dumps(raw), encoding="utf-8")
        got = _valid(upward.code_path("reference_impl.py", upward.config(inst, led)), CODE)["ledger"]["entry"]
        assert got["assertions"] == sorted(KEYS) and got["keys"] == sorted(set(KEYS.values())), got
        assert got["state"] == "current" and got["drift"] is False
        assert got["suspect"] == {"status": "unchecked", "reason": upward.SUSPECT_UNREAD, "suspect": None}, got["suspect"]
        (root / "reference_impl.py").write_text("# edited\n", encoding="utf-8")
        got = _valid(upward.code_path("reference_impl.py", upward.config(inst, led)), CODE)["ledger"]["entry"]
        assert (got["state"], got["drift"]) == ("drift", True)
        (root / "reference_impl.py").unlink()
        got = _valid(upward.code_path("reference_impl.py", upward.config(inst, led)), CODE)["ledger"]["entry"]
        assert (got["state"], got["file_present"]) == ("missing", False)
        rep = trace.check(Store(), instance=inst, ledger=led, resolve=_resolve())
        assert rep["registered"][0]["state"] == "missing", "the leg's state is the one check reads"


def test_the_code_path_schema_requires_the_ids_keys_state_and_suspect_legs():
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        inst, led, _ = _registered(td, Store())
        rep = _valid(upward.code_path("reference_impl.py", upward.config(inst, led)), CODE)
        for field in ("keys", "state", "suspect"):
            bad = json.loads(json.dumps(rep))
            del bad["ledger"]["entry"][field]
            assert schema_check.validate(bad, CODE), f"a ledger entry without {field} passes the code-path schema"
        bad = json.loads(json.dumps(rep))
        bad["ledger"]["entry"]["state"] = "unchanged"
        assert schema_check.validate(bad, CODE), "state is current, drift or missing"


def test_the_suspect_leg_is_the_rule_trace_check_reads():
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        st = Store()
        inst, led, _ = _registered(td, st)
        [e] = json.loads(led.read_text(encoding="utf-8"))["entries"]
        read = lambda raw: trace.ledger_suspicion(st, raw)   # noqa: E731  the MCP reader's, on its read handle
        leg = _valid(upward.code_path("reference_impl.py", upward.config(inst, led), suspect=read), CODE)["ledger"]["entry"]["suspect"]
        assert leg == {"status": "read", "suspect": False, "used_invalidated": [], "used_changed": []}, leg
        for change, field in ((lambda: st.status.__setitem__("A:1@v1", "invalidated"), "used_invalidated"),
                              (lambda: st.value.__setitem__("A:2@v1", "2"), "used_changed")):
            st.status, st.value = {a: "approved" for a in KEYS}, {a: "1" for a in KEYS}
            change()
            leg = trace.ledger_suspicion(st, e)
            rep = trace.check(st, instance=inst, ledger=led, resolve=_resolve())
            sus = [f for f in rep["findings"] if f["kind"] == "suspect"]
            assert leg["suspect"] is True and leg[field] and len(sus) == 1 and sus[0]["related"] == leg[field], (leg, sus)


def test_from_a_code_file_its_keys_reach_the_register_nodes():
    # file -> keys -> nodes: the keys code_path returns are the ones key_nodes takes, and each lands on register nodes
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        inst, led, _ = _registered(td, Store())
        keys = upward.code_path("reference_impl.py", upward.config(inst, led))["ledger"]["entry"]["keys"]
        rows = SUBJECT.register_map().get("row", [])
        reached = {}
        for key in keys:
            got = _valid(upward.key_nodes(key), schema_check.load("key-nodes"))
            assert got["nodes"] == sorted({n for r in rows if r["key"] == key for n in r["nodes"]}), key
            assert all(not n.get("missing") and n["state"] for r in got["rows"] for n in r["nodes"]), got["rows"]
            reached[key] = got["nodes"]
        assert keys and all(reached.values()), reached


def _gate_route(unit: str) -> str:
    from capture import finding_owners, questionnaire_route
    return questionnaire_route(SUBJECT.id, "S1", "codegen", unit, (finding_owners(SUBJECT).get("P1|formula") or {}).get("files"))


def test_trace_findings_on_keys_name_their_owner_and_route_and_the_rest_none():
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        st = Store()
        inst, led, root = _registered(td, st)
        st.status["A:3@v1"] = "invalidated"            # P1|formula, ORG-0001's: suspect
        rep = _valid(trace.check(st, instance=inst, ledger=led, changed=["reference_impl.py", "nope/unmapped.py"],
                                 resolve=_resolve({"P1|formula": "proposed"})), TRACE)
        by = {f["kind"]: f for f in rep["findings"]}
        assert {"suspect", "gate:key", "unmapped"} <= set(by), sorted(by)
        assert (by["suspect"]["owner"], by["suspect"]["route"]) == ("ORG-0001", _gate_route("ORG-0001")), by["suspect"]
        assert by["gate:key"]["owner"] == "ORG-0001" and by["gate:key"]["route"] == _gate_route("ORG-0001")
        for f in rep["findings"]:
            if f["kind"] in ("unmapped", "gate:task"):
                assert "owner" not in f and "route" not in f, f
        (root / "reference_impl.py").write_text("# edited\n", encoding="utf-8")
        st.status["A:3@v1"] = "approved"
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve()), TRACE)
        [drift] = [f for f in rep["findings"] if f["kind"] == "drift"]
        # the entry rests on keys two units own: no single owner, each unit's route
        assert drift["owner"] is None and "ORG-0001" in drift["route"] and "ORG-0002" in drift["route"], drift
        rep = _valid(trace.check(Store(scenario=None), instance=inst, ledger=led, resolve=_resolve()), TRACE)
        [drift] = [f for f in rep["findings"] if f["kind"] == "drift"]
        assert drift["route"] is None, "with no scenario held, no questionnaire to route to"


def test_the_trace_gate_names_what_it_decided_on_as_the_gate_report_does():
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        st = Store()
        inst, led, _ = _registered(td, st)
        gate = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve()), TRACE)["gate"]
        assert gate["task_profile"] == gate_cli.profile_digest(dict(SUBJECT.tasks["codegen"]))
        assert gate["register"] == gate_cli.register_identity() and gate["knowgov"] == gate_cli.knowgov_identity()
        assert gate["task_profile"] and len(gate["task_profile"]) == 64


def test_the_annotations_carry_a_findings_owner_and_route():
    _cargo_quote()
    with tempfile.TemporaryDirectory() as td:
        st = Store()
        inst, led, _ = _registered(td, st)
        st.status["A:3@v1"] = "invalidated"
        rep = trace.check(st, instance=inst, ledger=led, resolve=_resolve())
        rep["findings"].append({"severity": "major", "kind": "unmapped", "app": None, "path": "x.py", "ref": None,
                                "related": [], "message": "x.py is unmapped"})
        fs = {f["kind"]: f for f in annotate.findings(rep, instance=inst, root=Path(td))}
        assert fs["suspect"]["message"].endswith(f" Owner: ORG-0001. Route: {_gate_route('ORG-0001')}"), fs["suspect"]["message"]
        assert fs["unmapped"]["message"] == "x.py is unmapped"
        text = annotate.convert(rep, "github", instance=inst, root=Path(td))
        assert "Owner%3A" not in text and "Owner: ORG-0001." in text, "the owner is in the message, escaped as data"


def test_a_ledger_entrys_keys_are_reported_in_nfc():
    # task-0301 (decision-0034 A2): a key in a ledger written before NFC reads as key_nodes takes it
    import unicodedata
    composed = "société|adresse"
    decomposed = unicodedata.normalize("NFD", composed)
    assert decomposed != composed
    e = {"keys": [decomposed], "used": [{"id": "A:1@v1", "key": decomposed, "value": "1", "sha256": "0" * 64}]}
    assert trace.entry_keys(e) == [composed]

"""task-0342 (decision-0041 C5-1, brought into 0.10.0 on 2026-11-16): a reader of RECONCILE.json with an owner.

``harness/reconcile_reader.py`` (CLI) and the MCP reader's ``stale_nodes`` list, for each system under the register's
``exports/``, the stale nodes its newest landing names, each with its owning unit as ``register_impact`` names it, and
group them by unit. Every landing here is in a temporary copy of the vendored register; nothing is written by the
reader."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import connector  # noqa: E402
import mcp_server  # noqa: E402
import reconcile_reader as rr  # noqa: E402
import register_impact as ri  # noqa: E402
import schema_check  # noqa: E402

FIX = ROOT / "tools" / "fixtures" / "aris_cargo_quote"
SCHEMA = schema_check.load("stale-nodes")


def _instance() -> Path:
    """A register-only instance with the ARIS fixture landed twice: the second drops PROC-0005."""
    d = Path(tempfile.mkdtemp(prefix="kg-reconcile-reader-"))
    shutil.copytree(ROOT / "demo" / "register", d / "register", ignore=shutil.ignore_patterns("__pycache__"))
    (d / "connectors.toml").write_text('[system.aris]\nid_attribute = "AT_ID"\n', encoding="utf-8")
    connector.land(d, "aris", [FIX / "first"])
    connector.land(d, "aris", [FIX / "later"])
    return d


def _digests(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}


def _valid(rep: dict) -> dict:
    assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)[:5]
    assert schema_check.validate({**rep, "unschematised": 1}, SCHEMA), "the schema is closed"
    return rep


def test_the_newest_landing_names_each_stale_node_with_its_owner_and_writes_nothing():
    d = _instance()
    try:
        reg_root = d / "register"
        before = _digests(reg_root)
        rep = _valid(rr.report({}, reg_root))
        reg = ri.load_tools(reg_root)["register"].load_register(reg_root)
        aris = next(s for s in rep["systems"] if s["system"] == "aris")
        assert aris["folder"] == "exports/aris/2026-11-18" and aris["reconciled"] and aris["previous"] == "exports/aris/2026-11-04"
        (x,) = aris["stale_nodes"]
        assert x["id"] == "PROC-0005" and x["in_register"] and x["previous"] == "exports/aris/2026-11-04"
        assert x["owning_unit"] == ri.owning_unit(reg, "PROC-0005") and x["owning_unit"]["unit"]
        assert x["name"] == reg["nodes"]["PROC-0005"]["name"] and x["taxonomy"] == "processes"
        assert rep["total"] == 1 and rep["by_owner"] == [{"unit": x["owning_unit"]["unit"], "name": x["owning_unit"]["name"],
                                                          "stale": ["PROC-0005"]}]
        # the vendored register's own landings are listed too, reconciled with nothing stale; an empty system says so
        kit = next(s for s in rep["systems"] if s["system"] == "kit")
        assert kit["reconciled"] and kit["stale_nodes"] == []
        edm = next(s for s in rep["systems"] if s["system"] == "edm")
        assert edm["folder"] is None and edm["reconciled"] is False and edm["why"] == "no export landed"
        assert _digests(reg_root) == before, "the reader writes nothing"
    finally:
        shutil.rmtree(d)


def test_filters_by_system_and_owning_unit_and_refuses_what_the_register_lacks():
    d = _instance()
    try:
        reg_root = d / "register"
        reg = ri.load_tools(reg_root)["register"].load_register(reg_root)
        owner = ri.owning_unit(reg, "PROC-0005")["unit"]
        other = next(n for n, x in sorted(reg["nodes"].items()) if x.get("_taxonomy") == "organisation" and n != owner)
        mine = _valid(rr.report({"system": "aris", "owner": owner}, reg_root))
        assert [s["system"] for s in mine["systems"]] == ["aris"] and mine["total"] == 1 and mine["filters"] == {"system": "aris", "owner": owner}
        theirs = _valid(rr.report({"owner": other}, reg_root))
        assert theirs["total"] == 0 and theirs["by_owner"] == []
        for bad, said in (({"system": "nope"}, "exports/ holds"), ({"owner": "PROC-0005"}, "a unit of the register's organisation"),
                          ({"owner": "ORG-9999"}, "a unit"), ({"walk": "x"}, "unknown argument")):
            try:
                rr.report(bad, reg_root)
            except rr.ReconcileError as e:
                assert said in str(e), (bad, e)
            else:
                raise AssertionError(f"{bad} was not refused")
    finally:
        shutil.rmtree(d)


def test_a_node_the_register_no_longer_holds_an_unreconciled_landing_and_a_broken_record():
    d = _instance()
    try:
        reg_root = d / "register"
        (reg_root / "processes" / "PROC-0005.toml").unlink()   # retired by deletion after the landing
        rep = _valid(rr.report({"system": "aris"}, reg_root))
        (x,) = rep["systems"][0]["stale_nodes"]
        assert x["in_register"] is False and x["owning_unit"] is None and x["name"] is None
        assert rep["by_owner"] == [{"unit": None, "name": None, "stale": ["PROC-0005"]}]
        later = reg_root / "exports" / "aris" / "2026-11-18" / "RECONCILE.json"
        later.write_text("{not json", encoding="utf-8")
        try:
            rr.report({}, reg_root)
        except rr.ReconcileError as e:
            assert "exports/aris/2026-11-18/RECONCILE.json cannot be read" in str(e)
        else:
            raise AssertionError("a broken RECONCILE.json was read")
        later.unlink()
        rep = _valid(rr.report({"system": "aris"}, reg_root))
        assert rep["systems"][0]["reconciled"] is False and "tools/reconcile.py has not been run" in rep["systems"][0]["why"]
    finally:
        shutil.rmtree(d)


def test_the_systems_own_id_is_named_when_the_registers_rule_found_the_node():
    d = _instance()
    try:
        reg_root = d / "register"
        later = reg_root / "exports" / "aris" / "2026-11-18" / "RECONCILE.json"
        rec = json.loads(later.read_text(encoding="utf-8"))
        rec["stale_nodes"] = [{"id": "PROC-0005", "aris_guid": "0000-guid"}]   # the register's GUID rule's own entry
        later.write_text(json.dumps(rec), encoding="utf-8")
        (x,) = _valid(rr.report({"system": "aris"}, reg_root))["systems"][0]["stale_nodes"]
        assert x["source_id"] == "0000-guid" and x["previous"] is None
    finally:
        shutil.rmtree(d)


def test_the_cli_and_the_mcp_tool_give_the_same_report_and_refuse_alike():
    d = _instance()
    try:
        reg_root = d / "register"
        env = {**os.environ, "KG_REGISTER": str(reg_root), "PYTHONDONTWRITEBYTECODE": "1"}
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "reconcile_reader.py")], capture_output=True, text=True, env=env)
        assert p.returncode == 0, p.stderr
        cli = _valid(json.loads(p.stdout))
        bad = subprocess.run([sys.executable, str(ROOT / "harness" / "reconcile_reader.py"), "--system", "nope"],
                             capture_output=True, text=True, env=env)
        assert bad.returncode == 2 and "exports/ holds" in bad.stderr and not bad.stdout
        gone = subprocess.run([sys.executable, str(ROOT / "harness" / "reconcile_reader.py")], capture_output=True, text=True,
                              env={**env, "KG_REGISTER": str(d / "nowhere")})
        assert gone.returncode == 2 and "cannot run" in gone.stderr
        keep = os.environ.get("KG_REGISTER")
        os.environ["KG_REGISTER"] = str(reg_root)
        try:
            s = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(OSError("no store here"))))

            def call(args):
                return s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "stale_nodes", "arguments": args}})
            got = call({})["result"]
            assert got["isError"] is False and got["structuredContent"] == cli
            assert call({"system": "nope"})["result"]["isError"] is True
            for args in ({"systen": "aris"}, {"owner": "an owner"}, {"system": 3}):   # outside the inputSchema
                assert call(args)["error"]["code"] == -32602, args
        finally:
            os.environ.pop("KG_REGISTER", None) if keep is None else os.environ.__setitem__("KG_REGISTER", keep)
    finally:
        shutil.rmtree(d)


def test_the_tool_is_files_only_listed_and_names_its_schema():
    t = next(t for t in mcp_server.TOOLS if t["name"] == "stale_nodes")
    assert t["_meta"][mcp_server.META_STORE] is False and "stale_nodes" not in mcp_server.STORE_BACKED
    assert "harness/schemas/stale-nodes.schema.json" in t["description"] and mcp_server.OUTPUT_SCHEMAS["stale_nodes"] == "stale-nodes"

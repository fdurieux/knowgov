"""The connector (task-0063): an export lands in an instance's register as a dated, append-only
mirror in ieam-register's format; a vanished id is stale and deletes nothing; a renamed object is an
update; identity comes from the configured attribute, a process @id and <documentation> only; the
system is named only by the instance. Every landing here is in a temporary example instance: the
record, the committed example instance's sources and their digests are never touched."""
import atexit
import hashlib
import json
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import connector  # noqa: E402

FIX = ROOT / "tools" / "fixtures" / "aris_cargo_quote"
CONFIG = '[system.aris]\nid_attribute = "AT_ID"\n'
_INSTANCE: dict = {}


def _digests(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def _mini(config: str = CONFIG, sources: str = "") -> Path:
    """A register-only instance: the vendored register copied, a connectors.toml."""
    d = Path(tempfile.mkdtemp(prefix="kg-connector-"))
    shutil.copytree(ROOT / "demo" / "register", d / "register", ignore=shutil.ignore_patterns("__pycache__"))
    if sources:
        p = d / "register" / "metamodel" / "sources.toml"
        p.write_text(p.read_text(encoding="utf-8") + sources, encoding="utf-8")
    (d / "connectors.toml").write_text(config, encoding="utf-8")
    return d


def _landed() -> dict:
    """The example instance with first, then later, landed (once per run)."""
    if not _INSTANCE:
        import example_instance
        top = Path(tempfile.mkdtemp(prefix="kg-connector-instance-"))
        atexit.register(shutil.rmtree, top, True)
        d = top / "instance"
        example_instance.build(d)
        (d / "connectors.toml").write_text(CONFIG, encoding="utf-8")
        reg = d / "register"
        nodes_before = {k: v for k, v in _digests(reg).items() if not k.startswith("exports/")}
        first = connector.land(d, "aris", [FIX / "first"])
        first_bytes = _digests(reg / "exports" / "aris" / "2026-11-04")
        later = connector.land(d, "aris", [FIX / "later"])
        _INSTANCE.update(dir=d, first=first, later=later, first_bytes=first_bytes, nodes_before=nodes_before)
    return _INSTANCE


def test_an_export_lands_dated_with_its_manifest_and_reconcile_and_the_second_beside_the_first():
    s = _landed()
    base = s["dir"] / "register" / "exports" / "aris"
    assert sorted(p.name for p in base.iterdir() if not p.name.startswith(".")) == ["2026-11-04", "2026-11-18"]
    for day, variant, prev in (("2026-11-04", "first", ""), ("2026-11-18", "later", "exports/aris/2026-11-04")):
        folder = base / day
        man = tomllib.loads((folder / "MANIFEST.toml").read_text(encoding="utf-8"))
        # ieam-register's MANIFEST keys (exports/README.md), the files byte for byte with their digests
        assert {"exported_on", "source", "source_version", "tool", "tool_version", "previous", "files", "ids"} <= set(man)
        assert str(man["exported_on"]).startswith(day) and man["source"] == "aris" and man["previous"] == prev
        assert man["tool_version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        src = _digests(FIX / variant)
        assert man["files"] == src and {k: v for k, v in _digests(folder).items() if k in src} == src
        assert "ARIS 10.0.0.320027101" in man["source_version"]
        rec = json.loads((folder / "RECONCILE.json").read_text(encoding="utf-8"))
        assert rec["folder"] == f"exports/aris/{day}" and rec["previous"] == prev and rec["source"] == "aris"
        assert set(rec) >= {"files", "ids", "stale_nodes"} and set(rec["ids"]) == {"added", "renamed", "deleted"}
    assert not list(base.glob(".*partial*")), "no partial folder left behind"
    # the first folder is exactly what it was before the second landed: never overwritten
    assert _digests(base / "2026-11-04") == s["first_bytes"]


def _man(day: str) -> dict:
    return tomllib.loads((_landed()["dir"] / "register" / "exports" / "aris" / day / "MANIFEST.toml").read_text(encoding="utf-8"))


def _guid(rid: str) -> str:
    return {v: k for k, v in _man("2026-11-04")["register_ids"].items()}[rid]


def test_the_manifest_follows_the_registers_format_ids_by_guid_register_ids_apart():
    # decision-0010: [ids] is every AML object by GUID (the aris_guid id_field) with its name; the
    # register ids sit in their own tables, never in [ids]
    for day, objects, carrying, bpmn in (("2026-11-04", 41, 14, 5), ("2026-11-18", 38, 13, 4)):
        man = _man(day)
        assert len(man["ids"]) == objects and all(re.fullmatch(r"[0-9a-f-]{36}", g) for g in man["ids"])
        assert len(man["register_ids"]) == carrying and set(man["register_ids"]) <= set(man["ids"])
        assert len(man["bpmn_ids"]) == bpmn and set(man["bpmn_ids"]) <= set(man["register_ids"].values())
        assert "guids" not in man and not any(connector.REGISTER_ID.fullmatch(k) for k in man["ids"])
    assert _man("2026-11-04")["ids"][_guid("PROC-0004")] == "Price the quote"
    assert _man("2026-11-18")["ids"][_guid("PROC-0004")] == "Calculate the quote price"


def test_the_first_export_adds_every_object_and_finds_nothing_stale():
    r = _landed()["first"]
    assert r["files"]["added"] == ["cargo_quote.aml", "quote_process.aris.bpmn", "quote_process.bpmn"]
    assert r["ids"]["added"] == sorted(_man("2026-11-04")["ids"]) and len(r["ids"]["added"]) == 41
    assert r["stale_nodes"] == [] and r["unknown_ids"] == [] and r["ids"]["deleted"] == []


def test_a_vanished_id_is_stale_and_deletes_nothing():
    s = _landed()
    r = s["later"]
    # the register's own diff, by GUID: PROC-0005's object and the two events that went with it
    assert _guid("PROC-0005") in r["ids"]["deleted"] and len(r["ids"]["deleted"]) == 3
    assert not set(r["ids"]["deleted"]) & set(_man("2026-11-18")["register_ids"])
    # no node of the example carries [source] aris_guid: the connector's stale-by-register-id finds it
    assert r["stale_nodes"] == [{"id": "PROC-0005", "previous": "exports/aris/2026-11-04"}]
    reg = s["dir"] / "register"
    after = {k: v for k, v in _digests(reg).items() if not k.startswith("exports/")}
    assert after == s["nodes_before"], "no node, link or register file changed"
    assert (reg / "processes" / "PROC-0005.toml").is_file()


def test_a_renamed_object_is_an_update_not_a_delete_and_an_add():
    r = _landed()["later"]
    g = _guid("PROC-0004")
    assert r["ids"]["renamed"] == [g], "the same object, its GUID unchanged, its name changed"
    assert g not in r["ids"]["added"] and g not in r["ids"]["deleted"]
    assert r["ids"]["added"] == []
    assert sorted(r["files"]["updated"]) == ["cargo_quote.aml", "quote_process.aris.bpmn", "quote_process.bpmn"]
    assert _man("2026-11-18")["register_ids"][g] == "PROC-0004"


def test_unregistered_is_every_object_no_node_carries_and_unknown_ids_the_register_ids_it_lacks():
    # the register's decision 0017 (v0.2.10), computed by the vendored reconcile.py on the GUID-keyed
    # [ids]: no node of the example carries [source] aris_guid, so every object reads unregistered,
    # 41 then 38 (27 and 25 of them events, rules and steps no register id names). unknown_ids reads
    # the register-id tables and is empty: every carried register id is a node.
    s = _landed()
    reg = connector.REG.load_register(s["dir"] / "register")
    for day, r, n in (("2026-11-04", s["first"], 41), ("2026-11-18", s["later"], 38)):
        rec = json.loads((s["dir"] / "register" / "exports" / "aris" / day / "RECONCILE.json").read_text(encoding="utf-8"))
        assert rec["unregistered"] == r["unregistered"] == connector.REC.unregistered(reg, _man(day))
        assert [e["aris_guid"] for e in rec["unregistered"]] == sorted(_man(day)["ids"]) and len(rec["unregistered"]) == n
        assert all(e["name"] == _man(day)["ids"][e["aris_guid"]] for e in rec["unregistered"])
        assert rec["unknown_ids"] == []
    # a node the register drops: its carried id becomes unknown
    d = _mini()
    (d / "register" / "processes" / "PROC-0005.toml").unlink()
    r = connector.land(d, "aris", [FIX / "first"])
    assert r["unknown_ids"] == ["PROC-0005"] and len(r["unregistered"]) == 41
    shutil.rmtree(d)


def test_nodes_that_carry_their_aris_guid_are_registered_and_the_registers_own_rule_finds_the_stale():
    # decision-0010's point: once the nodes name ARIS as their source, with their object's GUID, the
    # register's reconcile.py does the work: the 14 objects with a node leave unregistered (41-14,
    # 38-13), and its own stale_nodes finds PROC-0005 by its GUID; the connector's stale-by-register-id
    # adds nothing then
    d = _mini()
    first = connector.read_aml((FIX / "first" / "cargo_quote.aml").read_bytes(), "AT_ID")["guids"]
    for g, rid in first.items():
        p = next((d / "register").glob(f"*/{rid}.toml"))
        text = p.read_text(encoding="utf-8")
        head, rest = text.split("[source]\n", 1)
        tail = rest[rest.index("\n[") :] if "\n[" in rest else "\n"
        p.write_text(f'{head}[source]\nsystem = "aris"\naris_guid = "{g}"\n{tail}', encoding="utf-8")
    a = connector.land(d, "aris", [FIX / "first"])
    b = connector.land(d, "aris", [FIX / "later"])
    assert len(a["unregistered"]) == 41 - 14 and len(b["unregistered"]) == 38 - 13
    assert not {e["aris_guid"] for e in a["unregistered"]} & set(first)
    gone = {v: k for k, v in first.items()}["PROC-0005"]
    assert a["stale_nodes"] == [] and b["stale_nodes"] == [{"id": "PROC-0005", "aris_guid": gone}]
    shutil.rmtree(d)


def test_the_instance_still_holds_its_layout_and_the_register_its_checks():
    import contextlib
    import io
    import check_instance
    d = _landed()["dir"]
    with contextlib.redirect_stdout(io.StringIO()):
        assert check_instance.main([str(d)]) == 0
    import importlib.util
    spec = importlib.util.spec_from_file_location("kg_connector_check_register", d / "register" / "tools" / "check_register.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    with contextlib.redirect_stdout(io.StringIO()):
        assert m.main(["--root", str(d / "register"), "--today", "2026-11-01"]) == 0


def test_landing_over_an_export_or_before_the_newest_is_refused():
    d = _mini()
    assert connector.main([str(d), "--system", "aris", str(FIX / "later")]) == 0
    before = _digests(d / "register" / "exports")
    assert connector.main([str(d), "--system", "aris", str(FIX / "later")]) == 1      # the same date
    assert connector.main([str(d), "--system", "aris", str(FIX / "first")]) == 1      # an earlier date
    assert _digests(d / "register" / "exports") == before
    assert connector.main([str(d), "--system", "nowhere", str(FIX / "first")]) == 1   # not configured
    shutil.rmtree(d)


def test_the_system_is_named_only_by_the_instance():
    # the same export under a name the instance chose lands under that name; nothing defaults a system
    d = _mini('[system.repo_x]\n', '\n[system.repo_x]\ndescription = "x"\nid_field = "x_guid"\n')
    r = connector.land(d, "repo_x", [FIX / "first"])
    assert r["folder"] == "exports/repo_x/2026-11-04" and (d / "register" / "exports" / "repo_x" / "2026-11-04" / "MANIFEST.toml").is_file()
    assert connector.main([str(d), "--system", "aris", str(FIX / "first")]) == 1     # configured in the register, not here
    (d / "connectors.toml").unlink()
    assert connector.main([str(d), "--system", "repo_x", str(FIX / "later")]) == 2   # no configuration at all
    shutil.rmtree(d)
    assert not re.search(r"""default\s*=\s*["']aris|system\s*=\s*["']aris""", (ROOT / "tools" / "connector.py").read_text(encoding="utf-8"))


def test_the_id_attribute_is_configuration():
    data = (FIX / "first" / "cargo_quote.aml").read_bytes()
    assert "PROC-0001" in connector.read_aml(data, "AT_ID")["ids"]
    assert connector.read_aml(data, "AT_SOMETHING_ELSE")["ids"] == {}
    renamed = data.replace(b'AttrDef.Type="AT_ID"', b'AttrDef.Type="AT_REG"')
    assert connector.read_aml(renamed, "AT_REG")["ids"] == connector.read_aml(data, "AT_ID")["ids"]
    assert connector.DEFAULT_ID_ATTRIBUTE == "AT_ID"
    d = _mini("[system.aris]\n")
    assert connector.system_config(d, "aris")["id_attribute"] == "AT_ID"
    shutil.rmtree(d)


def test_both_bpmn_dialects_carry_the_same_ids():
    for v in ("first", "later"):
        own = connector.read_bpmn((FIX / v / "quote_process.bpmn").read_bytes())
        aris = connector.read_bpmn((FIX / v / "quote_process.aris.bpmn").read_bytes())
        assert own["ids"] == aris["ids"] and own["dialect"] == "bpmn" and aris["dialect"] == "aris"
        assert "PROC-0001" in own["ids"] and ("PROC-0005" in own["ids"]) == (v == "first")


def test_namespaces_are_matched_by_uri_and_ids_never_come_from_element_ids_or_coordinates():
    text = (FIX / "first" / "quote_process.aris.bpmn").read_text(encoding="utf-8")
    want = connector.read_bpmn(text.encode())["ids"]
    # another prefix for the same URIs reads the same
    other = text.replace("semantic:", "m:").replace("xmlns:semantic=", "xmlns:m=").replace("aris:", "a:").replace("xmlns:aris=", "xmlns:a=")
    r = connector.read_bpmn(other.encode())
    assert r["ids"] == want and r["dialect"] == "aris"
    # the familiar prefix on another URI is not BPMN
    wrong = text.replace('xmlns:semantic="http://www.omg.org/spec/BPMN/20100524/MODEL"', 'xmlns:semantic="urn:not-bpmn"')
    try:
        connector.read_file(wrong.encode(), "AT_ID")
        raise AssertionError("a file whose prefix only looks like BPMN was read")
    except connector.Refused:
        pass
    # every element id rewritten and every coordinate moved: the same ids
    moved = re.sub(r'ID-[0-9a-f-]{36}', lambda m: "ID-" + hashlib.md5(m.group().encode()).hexdigest(), text)
    moved = re.sub(r'(x|y)="(\d+)\.0"', lambda m: f'{m.group(1)}="{int(m.group(2)) + 999}.0"', moved)
    assert connector.read_bpmn(moved.encode())["ids"] == want
    # an element id that looks like a register id is not identity; only documentation and process @id are
    own = (FIX / "first" / "quote_process.bpmn").read_text(encoding="utf-8")
    nodoc = re.sub(r"<bpmn:documentation>[^<]*</bpmn:documentation>", "", own)
    assert set(connector.read_bpmn(nodoc.encode())["ids"]) == {"PROC-0001"}, "kg:registerId and element ids are not read"


def test_nothing_under_harness_or_demo_app_names_the_vendor():
    # the connector's vendor stays in tools/ and the instance's configuration (AC #4). The three lines
    # allowed quote the register's own mapping-matrix fields (aris_status beside archi_status) and its
    # glossary of sources of record; they read the register, not an export.
    allowed = {
        ("demo/app/register_view.py", "ARIS {t.get('aris_status')}"),
        ("demo/app/index.html", "<th>ARIS</th>"),
        ("demo/app/views.py", "The system that authors a node's content: ARIS, Archi"),
    }
    vendor = re.compile(r"\baris\b|softwareag|arisebpmn|\bAT_ID\b|\.aml\b|\bconnector\.py\b|import connector", re.I)
    found = []
    for top in ("harness", "demo/app"):
        for p in sorted((ROOT / top).rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts or p.suffix in (".pyc",):
                continue
            rel = p.relative_to(ROOT).as_posix()
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if vendor.search(line) and not any(rel == a and frag in line for a, frag in allowed):
                    found.append(f"{rel}:{n}: {line.strip()[:100]}")
    assert not found, found


def test_a_folder_landed_before_decision_0010_still_gives_its_register_ids():
    # an instance's older folders keep their bytes (append-only): [ids] by register id beside [guids]
    old = {"ids": {"PROC-0001": "Quote process"}, "guids": {"g-1": "PROC-0001"}}
    new = {"ids": {"g-1": "Quote process", "g-2": "an event"}, "register_ids": {"g-1": "PROC-0001"}, "bpmn_ids": {"PROC-0002": "x"}}
    assert connector.carried_register_ids(old) == {"PROC-0001"}
    assert connector.carried_register_ids(new) == {"PROC-0001", "PROC-0002"}


def test_two_inputs_that_map_to_one_relative_path_are_refused():
    """task-0206 (doc-0030 P10): two export files that share a basename, or a file and a folder entry at
    the same relative path, used to keep one and drop the other silently. Now refused, naming both."""
    first = sorted(p for p in (FIX / "first").rglob("*") if p.is_file())[0]
    tmp = Path(tempfile.mkdtemp(prefix="kg-p10-"))
    try:
        (tmp / "a").mkdir()
        (tmp / "b").mkdir()
        twin_a, twin_b = tmp / "a" / first.name, tmp / "b" / first.name
        shutil.copy(first, twin_a)
        shutil.copy(first, twin_b)
        for inputs in ([twin_a, twin_b], [FIX / "first", twin_a]):
            try:
                connector.read_export(inputs, "AT_ID")
            except connector.Refused as e:
                assert first.name in str(e) and "two inputs" in str(e), e
            else:
                raise AssertionError(f"{inputs}: two inputs at {first.name} were not refused")
        d = _mini()
        before = _digests(d / "register" / "exports") if (d / "register" / "exports").exists() else {}
        assert connector.main([str(d), "--system", "aris", str(twin_a), str(twin_b)]) == 1, "the command refuses, exit 1"
        after = _digests(d / "register" / "exports") if (d / "register" / "exports").exists() else {}
        assert after == before, "nothing landed"
        shutil.rmtree(d)
        # one file named twice is one input, not two: nothing is lost, and it is read as before
        assert list(connector.read_export([twin_a, twin_a], "AT_ID")["files"]) == [first.name]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_stale_persists_until_the_id_returns():
    """task-0313, C5-1: a node found stale stays so in the next landing while its id is still absent,
    and is cleared once an export carries it again."""
    s = _landed()
    d = Path(tempfile.mkdtemp(prefix="kg-connector-stale-")) / "instance"
    atexit.register(shutil.rmtree, d.parent, True)
    shutil.copytree(s["dir"], d)
    again = connector.land(d, "aris", [FIX / "later"], exported_on="2026-12-02")
    assert [n["id"] for n in again["stale_nodes"]] == ["PROC-0005"]
    back = connector.land(d, "aris", [FIX / "first"], exported_on="2026-12-16")
    assert back["stale_nodes"] == []


def test_a_stale_node_whose_guid_returns_without_its_at_id_is_back():
    """task-0313 R1: a node found stale by the register's GUID rule is cleared when its object returns, whether or
    not the export still carries the AT_ID."""
    d = _mini()
    first = connector.read_aml((FIX / "first" / "cargo_quote.aml").read_bytes(), "AT_ID")["guids"]
    for g, rid in first.items():
        p = next((d / "register").glob(f"*/{rid}.toml"))
        text = p.read_text(encoding="utf-8")
        head, rest = text.split("[source]\n", 1)
        tail = rest[rest.index("\n[") :] if "\n[" in rest else "\n"
        p.write_text(f'{head}[source]\nsystem = "aris"\naris_guid = "{g}"\n{tail}', encoding="utf-8")
    connector.land(d, "aris", [FIX / "first"])
    b = connector.land(d, "aris", [FIX / "later"])
    assert [n["id"] for n in b["stale_nodes"]] == ["PROC-0005"]
    gone = {v: k for k, v in first.items()}["PROC-0005"]
    text = (FIX / "first" / "cargo_quote.aml").read_text(encoding="utf-8")
    i = text.index(f'<GUID>{gone}</GUID>')
    j = text.index('<AttrDef AttrDef.Type="AT_ID">', i)
    k = text.index("</AttrDef>", j) + len("</AttrDef>")
    export = Path(tempfile.mkdtemp(prefix="kg-connector-export-"))
    (export / "cargo_quote.aml").write_text(text[:j] + text[k:], encoding="utf-8")
    c = connector.land(d, "aris", [export], exported_on="2026-12-02")
    assert c["stale_nodes"] == [], c["stale_nodes"]
    shutil.rmtree(d)
    shutil.rmtree(export)

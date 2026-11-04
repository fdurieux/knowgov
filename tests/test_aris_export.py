"""The synthetic CargoQuote ARIS export (task-0119): deterministic, its committed fixtures the
generator's bytes, every register object identified, GUIDs stable, the later variant the first
less one process and with one function renamed. Standard library only (xml.etree)."""
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import aris_export as ax  # noqa: E402

BPMN = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
KG = "{" + ax.KG_NS + "}"
_GEN: dict = {}


def gen(variant: str) -> dict[str, str]:
    if variant not in _GEN:
        _GEN[variant] = ax.generate(variant)
    return _GEN[variant]


def aml(variant: str) -> ET.Element:
    return ET.fromstring(gen(variant)["cargo_quote.aml"].encode("utf-8"))


def attr(el: ET.Element, t: str) -> str | None:
    v = el.find(f"AttrDef[@AttrDef.Type='{t}']/AttrValue")
    return None if v is None else v.text


def objdefs(root: ET.Element) -> dict[str, ET.Element]:
    return {o.find("GUID").text: o for o in root.iter("ObjDef")}


def test_two_runs_are_byte_identical_and_equal_the_committed_fixtures():
    for v in ax.VARIANTS:
        again = ax.generate(v)
        assert again == gen(v)
        for name, text in again.items():
            assert (ax.FIXTURES / v / name).read_bytes() == text.encode("utf-8"), (v, name)
    assert ax.main(["--check"]) == 0


def test_the_header_says_synthetic_and_the_format_is_arises_xml():
    text = gen("first")["cargo_quote.aml"]
    assert '<!DOCTYPE AML SYSTEM "ARIS-Export.dtd">' in text.splitlines()[1]
    root = aml("first")
    h = root.find("Header-Info")
    assert "SYNTHETIC" in h.get("ArisExeVersion") and "SYNTHETIC" in h.get("DatabaseName")
    assert root.find("Language").get("LocaleId") == "1033"
    assert [m.get("Model.Type") for m in root.iter("Model")] == ["MT_EEPC"]
    types = {o.get("TypeNum") for o in root.iter("ObjDef")}
    assert types == {"OT_EVT", "OT_FUNC", "OT_RULE", "OT_APPL_SYS_TYPE", "OT_PERS_TYPE"}, types
    assert {r.get("SymbolNum") for r in root.iter("ObjDef") if r.get("TypeNum") == "OT_RULE"} == {"ST_OPR_XOR_1"}
    cxn = {c.get("CxnDef.Type") for c in root.iter("CxnDef")}
    assert cxn == {"CT_ACTIV_1", "CT_CRT_1", "CT_IS_EVAL_BY_1", "CT_LEADS_TO_1", "CT_LNK_2",
                   "CT_CAN_SUPP_1", "CT_EXEC_1"}, cxn
    # the docstring says the names are unverified
    assert "UNVERIFIED" in ax.__doc__


def test_counts_and_register_ids_follow_the_register():
    reg = ax.read_register()
    assert list(reg["procs"]) == [f"PROC-000{i}" for i in range(1, 6)]
    assert list(reg["caps"]) == [f"CAP-000{i}" for i in range(1, 6)]
    assert list(reg["apps"]) == ["APP-0002", "APP-0003", "APP-0004"]
    for v, procs in (("first", 5), ("later", 4)):
        root = aml(v)
        ids = [attr(o, ax.ID_ATTR) for o in root.iter("ObjDef") if attr(o, ax.ID_ATTR)]
        assert len(ids) == len(set(ids)), "one definition per register id"
        assert sum(i.startswith("PROC-") for i in ids) == procs
        assert sum(i.startswith("CAP-") for i in ids) == 5
        assert sorted(i for i in ids if i[:4] in ("APP-", "ORG-")) == ["APP-0002", "APP-0003", "APP-0004", "ORG-0001"]
        for o in root.iter("ObjDef"):
            i = attr(o, ax.ID_ATTR)
            if i and i[:4] in ("PROC", "CAP-"):
                folder = "processes" if i.startswith("PROC") else "capabilities"
                node = tomllib.loads((ax.REGISTER / folder / f"{i}.toml").read_text(encoding="utf-8"))
                assert o.get("TypeNum") == "OT_FUNC"
                if not (v == "later" and i == "PROC-0004"):
                    assert attr(o, "AT_NAME") == node["name"], (v, i)
        # every kit task, gateway and event has an occurrence; the end-to-end process links its model
        model = root.find(".//Model")
        e2e = next(o for o in root.iter("ObjDef") if attr(o, ax.ID_ATTR) == "PROC-0001")
        assert e2e.get("LinkedModels.IdRefs") == model.get("Model.ID")
        nodes, _ = ax.variant_flow(ax.read_kit(), ax.VARIANTS[v])
        assert len(nodes) == (21 if v == "first" else 19)
        assert len(model.findall("ObjOcc")) >= len(nodes)
    root = aml("first")
    assert len(list(root.iter("ObjDef"))) == 41 and len(list(root.iter("CxnDef"))) == 45
    assert len(list(root.iter("ObjOcc"))) == 44 and len(list(root.iter("CxnOcc"))) == 43
    root = aml("later")
    assert len(list(root.iter("ObjDef"))) == 38 and len(list(root.iter("CxnDef"))) == 39
    assert len(list(root.iter("ObjOcc"))) == 38 and len(list(root.iter("CxnOcc"))) == 37


def test_every_object_has_a_unique_guid_and_every_reference_resolves():
    for v in ax.VARIANTS:
        root = aml(v)
        ids, guids = set(), []
        for tag, idattr in (("Group", "Group.ID"), ("ObjDef", "ObjDef.ID"), ("CxnDef", "CxnDef.ID"),
                            ("Model", "Model.ID"), ("ObjOcc", "ObjOcc.ID"), ("CxnOcc", "CxnOcc.ID")):
            for el in root.iter(tag):
                g = el.find("GUID").text
                assert el.get(idattr) == f"{tag}.{g}", (tag, g)
                guids.append(g)
                ids.add(el.get(idattr))
        assert len(guids) == len(set(guids))
        for el in root.iter():
            for k, val in el.attrib.items():
                if k.endswith((".IdRef", ".IdRefs")):
                    assert all(x in ids for x in val.split()), (v, k, val)
        # an occurrence's connection is an occurrence of a definition between the same two definitions
        occ_def = {o.get("ObjOcc.ID"): o.get("ObjDef.IdRef") for o in root.iter("ObjOcc")}
        cxn = {c.get("CxnDef.ID"): (d.get("ObjDef.ID"), c.get("ToObjDef.IdRef"))
               for d in root.iter("ObjDef") for c in d.findall("CxnDef")}
        for o in root.iter("ObjOcc"):
            for co in o.findall("CxnOcc"):
                assert cxn[co.get("CxnDef.IdRef")] == (occ_def[o.get("ObjOcc.ID")], occ_def[co.get("ToObjOcc.IdRef")])


def test_the_later_variant_drops_one_process_and_renames_one_function_guids_stable():
    first, later = objdefs(aml("first")), objdefs(aml("later"))
    gone = set(first) - set(later)
    assert not set(later) - set(first), "the later export adds nothing"
    gone_ids = {attr(first[g], ax.ID_ATTR) for g in gone} - {None}
    assert gone_ids == {"PROC-0005"}, gone_ids
    # the notification function and the two events only it created; capabilities all stay
    assert {first[g].get("TypeNum") for g in gone} == {"OT_FUNC", "OT_EVT"} and len(gone) == 3
    renamed = [(attr(first[g], "AT_NAME"), attr(later[g], "AT_NAME"), attr(later[g], ax.ID_ATTR))
               for g in later if attr(first[g], "AT_NAME") != attr(later[g], "AT_NAME")]
    assert renamed == [("Price the quote", "Calculate the quote price", "PROC-0004")], renamed
    for g in later:   # same GUID, same type, same register id
        assert later[g].get("TypeNum") == first[g].get("TypeNum")
        assert attr(later[g], ax.ID_ATTR) == attr(first[g], ax.ID_ATTR)
    assert aml("later").find("Header-Info").get("CreateDate") == ax.LATER_DATE > ax.FIRST_DATE


def test_the_bpmn_files_carry_the_kit_flow_the_register_ids_and_the_aml_guids():
    for v in ax.VARIANTS:
        root = ET.fromstring(gen(v)["quote_process.bpmn"].encode("utf-8"))
        proc = root.find(f"{BPMN}process")
        assert proc.get(f"{KG}registerId") == "PROC-0001"
        guids = set(objdefs(aml(v)))
        tasks = proc.findall(f"{BPMN}task")
        for el in proc:
            if el.get(f"{KG}guid"):
                assert el.get(f"{KG}guid") in guids, el.get("id")
        rid = {t.get("id"): t.get(f"{KG}registerId") for t in tasks if t.get(f"{KG}registerId")}
        want = {t: p for t, p in ax.TASK_PROC.items() if p != ax.VARIANTS[v]["drop"]}
        assert rid == want, rid
        assert root.find("{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram") is not None
    # the bpmnlint the pre-load check runs, when it is installed here (CI: harness.yml's Node step)
    import preload_check
    cmd = preload_check.bpmnlint_cmd()
    if cmd:
        files = [str(ax.FIXTURES / v / "quote_process.bpmn") for v in ax.VARIANTS]
        r = subprocess.run([*cmd, "-c", str(ROOT / "instance" / "ci" / "bpmnlintrc"), *files],
                           capture_output=True, text=True)
        assert r.returncode == 0 and "problem" not in r.stdout, r.stdout + r.stderr


def test_the_generator_reads_only_public_cargo_quote_material_and_writes_no_vendored_tree():
    text = (ROOT / "tools" / "aris_export.py").read_text(encoding="utf-8")
    assert ax.KIT_BPMN.is_relative_to(ROOT / "subjects" / "cargo_quote" / "vendor")
    assert ax.REGISTER == ROOT / "demo" / "register"
    assert not ax.FIXTURES.is_relative_to(ROOT / "demo" / "register")
    assert not ax.FIXTURES.is_relative_to(ROOT / "subjects")
    for word in ("jef", "akantai", "J-F"):
        assert word not in text, word

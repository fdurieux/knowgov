"""Tasks 0355-0357: three bundle mappers a reverse-engineering run's kits wrote past. requirements_json refuses a top
level it cannot read, by name and with the shape, and reads an object whose one list-valued key holds the items;
plantuml_realises reads a ``' realises:`` comment line beside the footer; dmn_decisions reads a decision's own
citations. ``tools/check_subject.py`` refuses the shape (rule ``shape``) and warns on a malformed citation (rule
``citation``): a realises line naming no id, or an id-shaped token the subject's pattern does not read. The mappers
need the pins (PyYAML, pumllint): skipped naming rdflib where they are absent, required in the rdflib job."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import skip  # noqa: E402
from test_claim import DMN, _extract, _part, _run  # noqa: E402

PROBE = ROOT / "tools" / "fixtures" / "claim_probe"


def _keys(bag) -> dict[str, str]:
    return {f"{a['entity']}|{a['predicate']}": a["value"] for a in bag.assertions}


def _refused(x, text: str) -> str:
    try:
        _run(x, "requirements_json", "reqs.json", text)
    except x.ShapeRefused as e:
        assert isinstance(e, x.DocumentUnreadable) and not isinstance(e, TypeError)
        return str(e)
    raise AssertionError(f"not refused: {text!r}")


def test_requirements_json_reads_a_list_or_an_objects_one_list_and_refuses_anything_else_by_name():
    x = _extract()
    items = [{"id": "AB-001", "statement": "One."}, {"id": "AB-002", "statement": "Two.", "kind": "contract"}]
    flat = _keys(_run(x, "requirements_json", "reqs.json", json.dumps(items)))
    assert flat == {"AB-001|statement": "One.", "AB-002|statement": "Two."}
    wrapped = json.dumps({"version": "1", "source": "kit", "requirements": items})
    assert _keys(_run(x, "requirements_json", "reqs.json", wrapped)) == flat, "the kits' object form reads as the list"
    for text, why in ((json.dumps({"a": items, "b": []}), "2 list-valued keys ('a', 'b')"),
                      (json.dumps({"version": "1"}), "0 list-valued keys"),
                      ('"AB-001"', "a JSON string"), ("{not json", "not JSON"),
                      (json.dumps([{"id": "AB-001"}]), 'item 0 is not an object with string "id" and "statement"'),
                      (json.dumps(["AB-001"]), "item 0")):
        msg = _refused(x, text)
        assert msg.startswith("reqs.json: ") and why in msg and "requirements_json reads a JSON list of items" in msg, msg


def test_the_load_refuses_the_shape_naming_the_file_never_a_typeerror():
    x = _extract()

    class Bound:   # extract_all as the load calls it, with one artefact mapped by requirements_json
        mappers = {"reqs.json": "requirements_json"}
    saved, x.SUBJECT = x.SUBJECT, Bound
    x._SHORT["reqs.json"] = "tc"
    try:
        x.extract_all({"reqs.json": "42"}, "")
    except x.ShapeRefused as e:
        assert str(e).startswith("reqs.json: the top level is a JSON int; requirements_json reads"), e
    else:
        raise AssertionError("the load read a bare number")
    finally:
        x.SUBJECT = saved
        x._SHORT.pop("reqs.json", None)


PUML = "@startuml\ntitle Gate\nparticipant A\nparticipant B\nA -> B: go\n{lines}@enduml"


def test_plantuml_realises_reads_the_comment_form_beside_the_footer_each_id_once():
    x = _extract()
    try:
        import pumllint  # noqa: F401
    except ModuleNotFoundError:
        skip("rdflib", "pumllint is not installed: plantuml_realises needs the pins")
    foot = _run(x, "plantuml_realises", "uml/", _part("gate.puml", PUML.format(lines="footer owner: x — realises AB-001, AB-002\n")))
    both = _run(x, "plantuml_realises", "uml/", _part("gate.puml", PUML.format(
        lines="' realises: AB-002, AB-003\nfooter owner: x — realises AB-001, AB-002\n' Realises: AB-004\n")))
    assert _keys(foot)["AB-001|realised_by"] == "gate"
    assert {k: v for k, v in _keys(both).items() if k.endswith("realised_by")} == \
        {f"AB-00{i}|realised_by": "gate" for i in (1, 2, 3, 4)}, "a requirement both forms name is cited once"
    locs = [f["locator"] for f in both.fragments]
    assert "gate.puml:footer" in locs and "gate.puml:realises/1" in locs and "gate.puml:realises/2" in locs, locs
    comment = _run(x, "plantuml_realises", "uml/", _part("gate.puml", PUML.format(lines="' realises: AB-005\n")))
    assert _keys(comment)["AB-005|realised_by"] == "gate", "the comment form alone links"


def test_dmn_decisions_reads_a_rules_citations_and_not_a_decisions_own():
    """task-0357: reading a decision's own citations would move the public J-F record (actions_gate's description
    cites JDL-088, which no rule of it does), so the mapper is unchanged and check_subject warns instead."""
    x = _extract()
    plain = _keys(_run(x, "dmn_decisions", "dmn/", _part("g.dmn", DMN.format(dec="", r1=""))))
    cited = _keys(_run(x, "dmn_decisions", "dmn/", _part("g.dmn", DMN.format(
        dec="<description>Gate on AB-001 and AB-007.</description>", r1=""))))
    assert cited == plain and plain["AB-001|decided_by"] == "gate/r1" and "AB-007|decided_by" not in cited
    warns = x.convention_warnings("dmn_decisions", "dmn/", _part("g.dmn", DMN.format(
        dec="<description>Gate on AB-001 and AB-007.</description>", r1="")))
    assert warns == ["g.dmn: decision gate's own description cites AB-007, which no rule of it cites: dmn_decisions "
                     "reads citations from a rule's description only, so it links nothing"], warns
    assert x.convention_warnings("dmn_decisions", "dmn/", _part("g.dmn", DMN.format(dec="", r1=""))) == []


def _probe(td: str) -> Path:
    root = Path(td) / "claim_probe"
    shutil.copytree(PROBE, root)
    return root


def _findings(rep: dict, rule: str) -> list[dict]:
    return [f for f in rep["findings"] if f["rule"] == rule]


def test_check_subject_refuses_the_shape_and_warns_on_a_malformed_citation_only():
    import check_subject
    import schema_check
    with tempfile.TemporaryDirectory() as td:
        root = _probe(td)
        rep = check_subject.check(root, ROOT / "demo" / "register")
        if rep["yield"]["state"] != "checked":
            skip("rdflib", f"the yield is unchecked here: {rep['yield'].get('why')}")
        assert not _findings(rep, "citation") and not _findings(rep, "shape"), rep["findings"]

        req = root / "kit" / "requirements.json"
        req.write_text(json.dumps({"requirements": json.loads(req.read_text(encoding="utf-8"))}), encoding="utf-8")
        uml = root / "kit" / "uml" / "inferred.puml"
        uml.write_text(uml.read_text(encoding="utf-8").replace("@enduml", "' realises: CLM-004\n@enduml"), encoding="utf-8")
        rep = check_subject.check(root, ROOT / "demo" / "register")
        assert not _findings(rep, "citation") and not _findings(rep, "shape"), "the read forms are no finding"

        req.write_text(json.dumps({"a": [], "b": []}), encoding="utf-8")
        uml.write_text(uml.read_text(encoding="utf-8").replace("' realises: CLM-004\n", "' realises: the gate\n' realises: CLM-004, CLM-04\n"),
                       encoding="utf-8")
        dmn = root / "kit" / "dmn" / "values.dmn"
        text = dmn.read_text(encoding="utf-8")
        dmn.write_text(text.replace("<description>", "<description>See CLM-1234 and CLM-005. ", 1), encoding="utf-8")
        rep = check_subject.check(root, ROOT / "demo" / "register")
        [shape] = _findings(rep, "shape")
        assert shape["level"] == "error" and shape["where"] == "[[artefact]] requirements.json" and \
            "requirements.json: the top level is an object with 2 list-valued keys" in shape["message"], shape
        msgs = [f["message"] for f in _findings(rep, "citation")]
        assert all(f["level"] == "warning" for f in _findings(rep, "citation"))
        assert any("diagram inferred.puml: \"' realises: the gate\" names no requirement id" in m for m in msgs), msgs
        assert any("diagram inferred.puml" in m and "cites CLM-04," in m for m in msgs), msgs
        assert any("values.dmn" in m and "CLM-1234" in m for m in msgs), msgs
        assert any("decision value_gate's own description cites CLM-005, which no rule of it cites" in m for m in msgs), msgs
        assert rep["exit_code"] == 1 and schema_check.validate(rep, schema_check.load("subject-check")) == []


def test_the_public_kit_holds_one_citation_warning_a_decision_level_one():
    """J-F's actions_gate cites JDL-088 in its own description and in no rule: the one warning the public kits hold."""
    import check_subject
    rep = check_subject.check(ROOT / "subjects" / "jef_data_load", ROOT / "demo" / "register")
    if rep["yield"]["state"] != "checked":
        skip("rdflib", f"the yield is unchecked here: {rep['yield'].get('why')}")
    assert not _findings(rep, "shape"), rep["findings"]
    assert [(f["where"], f["message"].split(":")[1].strip()) for f in _findings(rep, "citation")] == \
        [("[[artefact]] contracts/dmn/", "decision actions_gate's own description cites JDL-088, which no rule of it cites")]

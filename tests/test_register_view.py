"""The demo's register view (demo/app/register_view.py): built from the vendored
IEAM register, read only, in the glossary's terms. Plain asserts, no fixtures, stdlib only."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
sys.path.insert(0, str(DEMO / "app"))
import register_view  # noqa: E402
import views  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _subject_pin import on_cargo_quote  # noqa: E402  (these tests are about CargoQuote's record; task-0032.01)


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text.strip()) if s]



def _forbidden_in(sentence):
    low = sentence.lower()
    return [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", low)]


@on_cargo_quote
def test_register_view_builds_from_the_vendored_copy_at_the_pinned_date():
    v = register_view.build()
    assert v["source"]["repo"] == "fdurieux/ieam-register" and len(v["source"]["commit"]) == 40 and v["source"]["digest_ok"]
    assert v["source"]["kind"] == "copy" and register_view.REGISTER == (DEMO / "register").resolve()
    assert v["source"]["tag"] == "v0.2.2" and v["source"]["commit"].startswith("0242646")  # the tag sits on the vendored commit
    assert v["pinned"] and v["run_date"] == v["source"]["pinned_date"]
    assert v["summary"] == {"nodes": 56, "links": 65, "errors": 0, "warnings": 7}   # the J-F slice (decisions 0005 and 0006): 29 nodes, 37 links, seven parentless nodes
    assert v["coverage_lines"][0] == "C1: 7/8 covered, 1 excepted, 0 uncovered"
    assert v["coverage"]["C2"]["uncovered"] == [] and v["coverage"]["C3"]["uncovered"] == []
    assert sorted(v["nodes_by_taxonomy"]) == sorted(["capabilities", "products", "journeys", "processes", "applications", "information", "organisation"])
    assert sum(len(ns) for ns in v["nodes_by_taxonomy"].values()) == 56 and len(v["links"]) == 65
    for ns in v["nodes_by_taxonomy"].values():
        for n in ns:
            p = n["panel"]
            assert p["title"].startswith(n["id"]) and p["intro"] and p["sections"], n["id"]
            assert f"Name: {n['name']}." in p["intro"]
            for sec in p["sections"]:
                if "table" in sec:
                    assert all(len(r) == len(sec["table"]["cols"]) for r in sec["table"]["rows"]), (n["id"], sec["heading"])
    cap = {n["id"]: n for n in v["nodes_by_taxonomy"]["capabilities"]}["CAP-0002"]
    assert cap["links_in"] == 2 and cap["links_out"] == 0 and cap["state"] == "approved"
    assert v["exceptions"][0]["id"] == "EXC-0001" and "until 2027-01-31" in v["exceptions"][0]["sentence"]
    assert v["matrix"] == {"rows": 16, "unverified": 16, "sentence": v["matrix"]["sentence"]} and "every row is unverified" in v["matrix"]["sentence"]
    assert len(v["relationship_types"]) == 10 and all(t["aris_status"] == "unverified" for t in v["relationship_types"])
    assert {t["term"] for t in v["glossary"]} <= set(views.GLOSSARY), "every register term is in the demo glossary"
    # one register per organisation: the view says which nodes are this subject's slice and offers its application to the impact walk
    assert v["subject_system"] == "kit" and v["slice"] == {"nodes": 27, "links": 28, "other_nodes": 29, "other_systems": ["jef_kit"]}
    assert v["impact_default"] == "APP-0002" and "This subject's slice is the source system kit: 27 nodes and 28 links." in v["intro"]
    assert all(n["subject"] == (n["system"] == "kit") for ns in v["nodes_by_taxonomy"].values() for n in ns)


def test_register_view_at_the_wall_clock_shows_an_expired_exception():
    w = register_view.build("2027-03-01")
    assert not w["pinned"] and w["run_date"] == "2027-03-01"
    assert w["coverage"]["C1"]["uncovered"] == ["JRN-0004"] and w["coverage"]["C1"]["excepted"] == 0
    assert "wall-clock date" in w["intro"] and w["pinned_date"] == "2026-11-01"
    same = register_view.build("2026-11-01")
    assert not same["pinned"] and "which is the pinned date" in same["intro"]
    assert any(f["check"] == "exceptions" and "expired" in f["message"] for f in w["findings"])


def test_register_view_sentences_obey_the_glossary_and_the_limit():
    for v in (register_view.build(), register_view.build("2027-03-01")):
        assert len(v["text_registry"]) > 100
        for item in v["text_registry"]:
            if item["kind"] == "data":
                continue
            for s in _sentences(item["text"]):
                assert len(s.split()) <= 20, s
                assert not _forbidden_in(s), (s, _forbidden_in(s))
    # the register's own forbidden synonyms are in the demo's list, reconciled (GLOSSARY.md)
    for syn in ("element record", "mapping row", "golden source", "an extract", "sign-off", "waiver", "completeness rule"):
        assert syn in views.FORBIDDEN
    for keep in ("extract", "item", "object", "ok"):
        assert keep not in views.FORBIDDEN, f"{keep} keeps its demo sense"


def test_register_impact_walk_reaches_the_product_and_says_when_it_does_not():
    w = register_view.impact("APP-0002")
    assert "PRD-0002" in w["reached"]["products"] and "JRN-0002" in w["reached"]["journeys"] and len(w["edges"]) == 5
    assert w["panel"]["title"] == "Impact of retiring APP-0002" and "does not climb a node's parent" in w["panel"]["intro"]
    cols = w["panel"]["sections"][0]["table"]["cols"]
    assert all(len(r) == len(cols) for r in w["panel"]["sections"][0]["table"]["rows"])
    # the register tool's own limit, shown honestly: TariffEngine reaches a journey step but no product
    t = register_view.impact("APP-0003")
    assert t["reached"]["products"] == [] and "JRN-0003" in t["reached"]["journeys"]
    assert "No product is reached" in t["panel"]["sections"][0]["text"]
    assert register_view.impact("APP-9999") is None
    leaf = register_view.impact("ENT-0004")
    assert leaf["edges"] == [] and "No link starts at this node" in leaf["panel"]["sections"][0]["text"]
    for v in (w, t, leaf):
        for item in v["text_registry"]:
            if item["kind"] == "data":
                continue
            for s in _sentences(item["text"]):
                assert len(s.split()) <= 20 and not _forbidden_in(s), s


@on_cargo_quote
def test_register_footprint_per_scenario():
    from pathlib import Path as _P
    NO_RUNS = ROOT / "nonexistent-demo-runs"
    fps = {sc: register_view.footprint(views.build(sc, views.default_source(sc), NO_RUNS)) for sc in views.ORDER}
    m = register_view.load_map()
    assert m["map"]["status"] == "approved" and m["map"]["approved_by"] and len(m["row"]) == 36
    assert {r["key"] for r in m["row"]} == set(json_keys())
    assert fps["S1"]["keys_below"] == {} and fps["S1"]["uncited"] == 0 and fps["S1"]["box"]["colour"] == "ok"
    s2 = fps["S2"]
    assert "QuoteAPI|on_screening_outage" in s2["keys_below"] and "response|hold_presence" in s2["keys_below"]
    # since the register's v0.1.1 (decision 0003) REL-06002 cites REQ-06, so S2 has no uncited gap and is amber, not red
    assert any(r["subject"] == "REQ-06" and "REL-06002" in r["cited_by"] for r in s2["requirements"]) and s2["uncited"] == 0
    assert any(r["subject"] == "REQ-05" and "REL-08002" in r["cited_by"] for r in s2["requirements"])
    assert s2["box"]["colour"] == "warn" and "APP-0002" in s2["touched"]
    assert fps["S4"]["box"]["colour"] == "warn" and fps["S5"]["box"]["colour"] == "warn"
    s3 = fps["S3"]
    assert "ENT-0005" in s3["not_approved"] and s3["box"]["colour"] == "bad"
    s6 = fps["S6"]
    assert len(s6["table_links"]) >= 4 and "REL-10001" in s6["table_links"] and s6["keys_below"] == {}
    assert any("changed decision table" in sec["heading"] for sec in s6["panel"]["sections"])
    assert len(fps["S7"]["keys_below"]) == 36 and len(fps["S7"]["touched"]) == 20
    for fp in fps.values():
        assert fp["box"]["id"] == "footprint" and fp["panel"]["title"].startswith("Register footprint of")
        for sec in fp["panel"]["sections"]:
            if "table" in sec:
                assert all(len(r) == len(sec["table"]["cols"]) for r in sec["table"]["rows"]), (fp["scenario"], sec["heading"])
        for item in fp["text_registry"]:
            if item["kind"] == "data":
                continue
            for s in _sentences(item["text"]):
                assert len(s.split()) <= 20 and not _forbidden_in(s), s
        for ln in fp["box"]["lines"]:
            assert len(ln.split()) <= 20 and not _forbidden_in(ln), ln


def _cells(panel):
    for sec in panel["sections"]:
        for row in sec.get("table", {}).get("rows", []):
            for c in row:
                yield from (c if isinstance(c, list) else [c])


def _refs(panel):
    return [c["ref"] for c in _cells(panel) if isinstance(c, dict) and "ref" in c]


def _check_sentences(items):
    for item in items:
        if item["kind"] == "data":
            continue
        for s in _sentences(item["text"]):
            assert len(s.split()) <= 20 and not _forbidden_in(s), s


@on_cargo_quote
def test_footprint_cells_are_references_and_tips():
    NO_RUNS = ROOT / "nonexistent-demo-runs"
    fp = register_view.footprint(views.build("S2", views.default_source("S2"), NO_RUNS))
    refs = _refs(fp["panel"])
    assert "req:REQ-06" in refs and "req:REQ-05" in refs and "link:REL-08002" in refs
    assert "key:QuoteAPI|on_screening_outage" in refs and "node:APP-0002" in refs and "doc:contract/openapi.yaml" in refs
    tips = [c for c in _cells(fp["panel"]) if isinstance(c, dict) and "tip" in c]
    assert any(c["text"] == "declared_gap" for c in tips) and any(c["text"] == "approved" for c in tips) and any(c["text"] in ("yes", "no") for c in tips)
    assert all(c["tip"] for c in tips)
    s6 = register_view.footprint(views.build("S6", views.default_source("S6"), NO_RUNS))
    assert "doc:contract/decision_table.md" in _refs(s6["panel"]) and "link:REL-10001" in _refs(s6["panel"])
    # the data part stays plain for the API's readers
    assert all(isinstance(r["cited_by"], str) for r in fp["requirements"])


@on_cargo_quote
def test_reference_panels():
    NO_RUNS = ROOT / "nonexistent-demo-runs"
    s2 = views.build("S2", views.default_source("S2"), NO_RUNS)
    link = register_view.ref("link", "REL-08002")
    assert link["panel"]["title"].startswith("REL-08002, a manages link") and "node:APP-0002" in _refs(link["panel"]) and "node:ENT-0003" in _refs(link["panel"]) and "req:REQ-05" in _refs(link["panel"])
    assert any(sec["heading"] == "Approval" for sec in link["panel"]["sections"])
    ext = register_view.ref("link", "REL-10001")
    assert "doc:contract/decision_table.md" in _refs(ext["panel"])
    req = register_view.ref("req", "REQ-06", s2)
    heads = [sec["heading"] for sec in req["panel"]["sections"]]
    assert "Rule hits in S2: 2" in heads and "Links citing it: 1" in heads and "Map rows anchored on it: 1" in heads
    assert "link:REL-06002" in _refs(req["panel"])
    assert "REQ-06: screening outage" in req["panel"]["intro"] and "key:QuoteAPI|on_screening_outage" in _refs(req["panel"])
    req5 = register_view.ref("req", "REQ-05", s2)
    assert "link:REL-08002" in _refs(req5["panel"])
    req_no_sc = register_view.ref("req", "REQ-05")
    assert not any(h.startswith("Rule hits") for h in [sec["heading"] for sec in req_no_sc["panel"]["sections"]])
    key = register_view.ref("key", "QuoteAPI|on_screening_outage", s2)
    assert "level declared_gap" in key["panel"]["intro"] and "blocks the verdict" in key["panel"]["intro"]
    assert any(sec["heading"] == "Gaps on this key: 1" for sec in key["panel"]["sections"]) and "req:REQ-06" in _refs(key["panel"])
    s3 = views.build("S3", views.default_source("S3"), NO_RUNS)
    k3 = register_view.ref("key", "S-review|max", s3)
    assert "level proposed" in k3["panel"]["intro"] and "node:ENT-0005" in _refs(k3["panel"])
    s6 = views.build("S6", views.default_source("S6"), NO_RUNS)
    doc = register_view.ref("doc", "contract/decision_table.md", s6)
    heads = [sec["heading"] for sec in doc["panel"]["sections"]]
    assert "Changed in the second stage" in heads and "Links citing it: 8" in heads and "27e9fe7ece26" in doc["panel"]["intro"]
    node = register_view.ref("node", "APP-0002")
    assert node["panel"]["title"].startswith("APP-0002") and any(r.startswith("link:REL-") for r in _refs(node["panel"]))
    for bad in (("node", "APP-9999"), ("link", "REL-99999"), ("req", "REQ-99"), ("key", "nope|nope"), ("doc", "nope.md"), ("nope", "x")):
        assert register_view.ref(*bad) is None, bad
    for r in (link, ext, req, req5, key, k3, doc, node):
        _check_sentences(r["text_registry"])
        for sec in r["panel"]["sections"]:
            if "table" in sec:
                assert all(len(row) == len(sec["table"]["cols"]) for row in sec["table"]["rows"]), sec["heading"]
    assert register_view.ref("key", "QuoteAPI|on_screening_outage", s2)["scenario"] == "S2"


@on_cargo_quote
def test_projection_rows_and_statements():
    import register_project as rp
    r = rp.rows(loaded_at="2026-10-31T00:00:00+00:00")
    c = r["counts"]
    assert c["nodes"] == 56 and c["links"] == 65 and c["types"] == 10 and c["documents"] == 10 and c["externals"] == 1 and c["exceptions"] == 1
    assert r["stamp"]["tag"] == "v0.2.2" and r["stamp"]["commit"].startswith("0242646") and r["stamp"]["export_date"] == "2026-10-30"   # the subject's export, not the newest
    assert len(r["parents"]) == sum(1 for n in r["nodes"] if n["parent"]) and len(r["owners"]) == 56
    assert sum(len(v) for v in r["typed"].values()) == 64 and len(r["maps_to"]) == 1 and len(r["link_of"]) == 129 and len(r["of_type"]) == 65
    assert {"reg_id": "REL-08002", "path": "kit/requirements.md", "anchor": "kit:requirements.md#REQ-05"} in r["cites"]
    assert r["excepts"] == [{"reg_id": "EXC-0001", "node": "JRN-0004", "rule": "C1", "expires": "2027-01-31"}]
    assert c["relationships"] == 64 + 1 + 129 + 65 + len(r["cites"]) + len(r["parents"]) + 56 + 1
    # every property is what Neo4j can hold: a string, number, boolean or list of strings; every row is stamped
    ok = (str, int, float, bool)
    for key in ("nodes", "types", "links", "documents", "externals", "exceptions"):
        for row in r[key]:
            assert row["tag"] == "v0.2.2" and row["commit"] and row["loaded_at"] and len(row["digest"]) == 64, (key, row["reg_id"])
            for k, v in row.items():
                assert isinstance(v, ok) or (isinstance(v, list) and all(isinstance(x, str) for x in v)), (key, row["reg_id"], k, v)
    # the load is the Neo4j adapter's project_register, read as source: the tests job has no driver
    src = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    body = src[src.index("def project_register("):src.index("def register_census(")]
    assert '"MATCH (n:Register) DETACH DELETE n"' in body
    harness = ("Artefact", "Version", "Fragment", "Assertion", "Activity", "Agent", "Verification", "Approval", "Gap", "Derived", "Entity")
    statements = [ln for ln in body.splitlines() if "MATCH (" in ln or "CREATE (" in ln]
    assert len(statements) >= 10
    for cypher in statements:  # the loader never names a harness label: the namespace is the whole discipline
        assert not any(f":{lbl}" in cypher for lbl in harness), cypher
        assert "Reg" in cypher, cypher
    assert "REG_MAPS_TO" in body and "{rtype}" in body
    assert set(r["typed"]) >= {"REG_IS_SUPPORTED_BY", "REG_CRUD"} and r["maps_to"]


def test_projection_is_wired_and_named():
    import re as _re
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    server = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    ci = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert '["api", "register", "project"]' in server and "s.register_census()" in server and '"register": None' in server
    assert 'id="project-btn"' in page and "/api/register/project" in page and "register ${s.register ? 'projected at '" in page
    assert "POST localhost:8080/api/register/project" in ci and '"tag"]=="v0.2.2"' in ci
    assert "projection" in views.GLOSSARY and "**The projection.**" in (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    adapter = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")   # the saved queries are the adapter's
    ids = [m.group(1) for m in _re.finditer(r'\{"id": "([a-z0-9-]+)", "needs": "[^"]+", "title"', adapter)]
    assert ids[-5:] == ["register-tag", "register-impact", "register-impact-paths", "register-c1", "register-cites"], ids
    for cy in ("REG_DELIVERS|REG_REALIZES", "<-[:REG_IS_SUPPORTED_BY]-", "REG_EXCEPTS", "Artefact {id:d.path}", "v.sha256 = d.digest THEN 'same as tag'"):
        assert cy in adapter
    # task-0023: the saved query is the walk impact.py makes, not a one-direction chain
    assert "REG_SUPPORTS|REG_IS_SUPPORTED_BY|REG_DELIVERS*1..4" not in adapter
    import store_neo4j as sn
    impact = {q["id"]: q for q in sn.SAVED_QUERIES}["register-impact"]
    assert impact["text"] == sn.IMPACT_ROWS and sn.IMPACT_START in impact["title"] and "tools/impact.py" in impact["title"]
    assert f"{{reg_id:'{sn.IMPACT_START}'}}" in sn.IMPACT_ROWS and f"{{reg_id:'{sn.IMPACT_START}'}}" in sn.IMPACT_PATHS
    assert ";" not in sn.IMPACT_ROWS and ";" not in sn.IMPACT_PATHS, "one statement each: check_saved_queries.py splits on ';'"


@on_cargo_quote
def test_saved_queries_say_what_they_need():
    import importlib.util, re as _re
    import server  # the page's generic queries plus the subject's queries.toml
    listed = server.cypher_list()
    needs = {q["id"]: q["needs"] for q in listed}
    assert len(needs) == 13 and set(needs.values()) <= {"scenario", "S6", "S4", "register", "register+scenario"}
    assert all(q["needs_text"] for q in listed)
    assert {q["id"]: q["needs_text"] for q in listed}["invalidation"] == "S6 loaded deterministically"
    assert {q["id"] for q in views.SUBJECT.queries} == {"three-valued", "gate", "invalidation", "contradiction"}, "the subject's own queries"
    assert needs["invalidation"] == "S6" and needs["contradiction"] == "S4" and needs["register-cites"] == "register+scenario"
    assert all(needs[k] == "register" for k in ("register-tag", "register-impact", "register-impact-paths", "register-c1"))
    assert all(needs[k] == "scenario" for k in ("loaded", "three-valued", "gate", "gaps", "gaps-concerns", "census"))
    # every need has its text: the page's generic ones in NEEDS_TEXT, a scenario's in the subject's queries.toml
    for q in listed:
        assert q["needs"] in server.NEEDS_TEXT or q.get("needs_text"), q["id"]
    server_text = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "function canRun(n)" in page and "'runs now' : 'needs ' + esc(needsText)" in page and "cypher_list()" in server_text


def test_runner_gives_s6_the_derived_output_in_both_modes():
    # a deterministic S6 without S1/run1_G.py in its folder has no Derived node to mark suspect,
    # which the maintainer's invalidation traversal showed as an empty derived column (2026-11-01)
    server = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert "if derived:" in server and 'ps.record_dir / derived["from_scenario"] / derived["file"]' in server and "mode == \"arms\"" not in server.split("if derived:")[1].split("cmd = ")[0]
    assert (ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results" / "S1" / "run1_G.py").exists()
    # and the harness reads that file in both modes: the deterministic branch used to pass none
    run_py = (ROOT / "harness" / "run.py").read_text(encoding="utf-8")
    assert "s6_stage2(d, None, [])" not in run_py and 'derived_ids = [a["id"] for v in gate["keys"].values() for a in v["assertions"]] if derived_code else []' in run_py


def json_keys():
    import json
    return list(json.loads((ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results" / "S1" / "deterministic.json").read_text(encoding="utf-8"))["gate_keys"])


def test_register_card_is_wired_on_the_page_and_the_server():
    page = (DEMO / "app" / "index.html").read_text(encoding="utf-8")
    assert "/api/register" in page and 'id="register-detail"' in page and "renderRegisterCard" in page and "showRegister" in page
    assert "function registerEntry" in page and 'data-id="register"' in page and ' id="register"' not in page, "the register is an entry in the Scenarios list, not a sidebar card"
    server = (DEMO / "app" / "server.py").read_text(encoding="utf-8")
    assert 'parts == ["api", "register"]' in server and "import register_view" in server
    assert '["api", "register", "impact"]' in server and 'id="impact-form"' in page and "/api/register/impact/" in page
    ci = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "/api/register" in ci and '"digest_ok"' in ci and "/api/register/impact/APP-0002" in ci and "/api/register/footprint/S2" in ci
    assert "v.footprint ? stageBox(v.footprint.box)" in page and '["api", "register", "footprint"]' in server
    assert "function wireRefs" in page and "function cell" in page and 'class="xref" data-ref=' in page and '["api", "register", "ref"]' in server
    assert "/api/register/ref/req/REQ-06?scenario=S2" in ci and "reference" in views.GLOSSARY
    # the strip stays one row and scrolls sideways; it never wraps the Oracle column under Ingest
    assert ".strip{display:grid;grid-auto-flow:column;" in page and "overflow-x:auto" in page.split(".strip{")[1].split("}")[0]
    # the oracle tables scroll inside their column instead of pushing past the card
    assert ".two>*{min-width:0}" in page and '<div class="tw ot"><div class="twin">' in page and ".tw{overflow-x:auto" in page
    assert '<div class="tw ot"><table>' not in page  # the two verdict tables share one scroll container
    readme = (DEMO / "README.md").read_text(encoding="utf-8")
    assert "**The register.**" in readme
    glossary = (DEMO / "GLOSSARY.md").read_text(encoding="utf-8")
    assert "Terms shared with the IEAM register" in glossary


@on_cargo_quote
def test_register_root_comes_from_the_environment_and_a_checkout_has_no_note():
    """task-0006.01: KG_REGISTER selects the register root, one register per organisation shared
    by every subject. A root without SOURCE.md is an instance's own checkout: reported as such,
    no digest checked, the checker run at the wall-clock date, and the checks, the impact walk
    and the footprint reading it as they read the vendored copy."""
    import datetime as dt
    import importlib
    import os
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "register"
        shutil.copytree(DEMO / "register", root, ignore=shutil.ignore_patterns("SOURCE.md", "__pycache__"))
        os.environ["KG_REGISTER"] = str(root)
        try:
            rv = importlib.reload(register_view)
            assert rv.REGISTER == root.resolve()
            src = rv.source_info()
            assert src["kind"] == "checkout" and src["digest_ok"] is None and src["mismatched"] == [] and src["pinned_date"] == ""
            assert src["repo"] == "" and src["commit"] == "" and src["describe"] == "", "no git repository, nothing invented"
            v = rv.build()
            assert not v["pinned"] and v["pinned_date"] == "" and v["run_date"] == dt.date.today().isoformat()
            assert "own checkout" in v["intro"] and "no pinned date" in v["intro"]
            assert v["summary"]["nodes"] == 56 and len(v["links"]) == 65, "the same content, read from the other root"
            assert rv.impact("APP-0002")["reached"]["products"]
            fp = rv.footprint(views.build("S2", views.default_source("S2"), ROOT / "nonexistent-demo-runs"))
            assert fp["box"]["colour"] == "warn" and fp["uncited"] == 0, "the subject's map and manifest join the mounted register"
        finally:
            del os.environ["KG_REGISTER"]
            rv = importlib.reload(register_view)
    assert rv.REGISTER == (DEMO / "register").resolve() and rv.source_info()["kind"] == "copy"


# ---- task-0023: the saved query register-impact is the walk impact.py makes
# The Cypher's CALL { } UNION block is parsed (one chain per branch: typed relationship sets with
# their direction, the taxonomy and state filters on the start and the intermediate nodes) and
# simulated over the projection's rows, so the test reads the adapter's text, not a copy of it.
_STEP = re.compile(r"(<-|-)\[(\w*):([A-Z_|]+)\](->|-)\((\w*):RegNode\)")
_BRANCH = re.compile(r"WITH a MATCH p = \(a\)(.*?) WHERE (.*?) RETURN p", re.S)
sys.path.insert(0, str(ROOT / "harness"))


def _parse_chains(text):
    """The branches of the CALL block: [(steps, filters)], a step (inverse?, {types}, node var, link
    var), the filters {var: (taxonomy, live_only?, approved_only?)}, a node var carrying the first two
    and a link var the third (v0.2.2: an intermediate link must be approved). Every branch must be
    understood: an unparsed piece fails."""
    block = text[text.index("CALL {") + len("CALL {"):text.index("\n}\n")]
    chains = []
    for branch in block.split("UNION"):
        m = _BRANCH.fullmatch(branch.strip())
        assert m, branch
        pattern, conds = m.group(1), m.group(2)
        steps, pos = [], 0
        for st in _STEP.finditer(pattern):
            assert st.start() == pos, pattern
            pos = st.end()
            assert (st.group(1), st.group(4)) in (("-", "->"), ("<-", "-")), pattern
            steps.append((st.group(1) == "<-", set(st.group(3).split("|")), st.group(5), st.group(2)))
        assert pos == len(pattern) and steps, pattern
        filters = {}
        for c in conds.split(" AND "):
            t = re.fullmatch(r"(\w+)\.taxonomy = '(\w+)'", c)
            l = re.fullmatch(r"NOT (\w+)\.state IN \['deprecated','retired'\]", c)
            o = re.fullmatch(r"(\w+)\.state = 'approved'", c)
            assert t or l or o, c
            v = (t or l or o).group(1)
            tax, live, ok = filters.get(v, (None, False, False))
            filters[v] = (t.group(2) if t else tax, live or bool(l), ok or bool(o))
        for steps_, filters_ in [(steps, filters)]:
            link_vars = {rv for *_, rv in steps_ if rv}
            assert all(filters_[rv] == (None, False, True) for rv in link_vars), "a named link is named to be filtered on approved"
            assert all(not filters_.get(nv, (None, False, False))[2] for *_, nv, _ in steps_), "approved is a link filter"
        chains.append((steps, filters))
    return chains


def _simulate(chains, rows, start):
    """The rows the Cypher gives from ``start`` over the projection's rows: the distinct relationships
    of every path of every branch, each as (from, relationship, to, link state, owner, evidence, live),
    live as the rows form's ``followed`` column computes it."""
    nodes = {n["reg_id"]: n for n in rows["nodes"]}
    evidence = {l["reg_id"]: tuple(l["evidence"]) for l in rows["links"]}
    by_source, by_target = {}, {}
    for rtype, items in rows["typed"].items():
        for it in items:
            rel = (rtype, it["source"], it["target"], it["props"]["reg_id"], it["props"]["state"], it["props"]["owner"])
            by_source.setdefault(it["source"], []).append(rel)
            by_target.setdefault(it["target"], []).append(rel)

    def ok(var, nid, filters):
        tax, live, _ = filters.get(var, (None, False, False))
        n = nodes[nid]
        return (tax is None or n["taxonomy"] == tax) and not (live and n["state"] in ("deprecated", "retired"))

    found = set()
    for steps, filters in chains:
        if start not in nodes or not ok("a", start, filters):
            continue
        partial = [(start, ())]
        for inverse, types, var, rvar in steps:
            nxt = []
            for cur, path in partial:
                for rel in (by_target if inverse else by_source).get(cur, []):
                    if rel[0] not in types:
                        continue
                    if rvar and filters[rvar][2] and rel[4] != "approved":
                        continue
                    other = rel[1] if inverse else rel[2]
                    if ok(var, other, filters) if var else True:
                        nxt.append((other, path + (rel,)))
            partial = nxt
        for _, path in partial:
            found.update(path)
    out = []
    for rtype, src, tgt, link, state, owner in found:
        inv = rtype == "REG_IS_SUPPORTED_BY"
        label = rtype.replace("REG_", "").lower() + (" (inverse)" if inv else "")
        far = src if inv else tgt
        live = state == "approved" and nodes[far]["state"] not in ("deprecated", "retired")
        out.append(((tgt if inv else src), label, far, state, owner, evidence[link], live))
    return sorted(out)


def _walk_rows(reg, start):
    T = register_view._load_tools()
    return sorted((e["from"], e["rel"], e["to"], e["state"], e["owner"], tuple(e["evidence"]), e["live"]) for e in T["impact"].walk(reg, start))


def test_register_impact_cypher_equals_the_walk_on_every_node():
    import register_project as rp
    import store_neo4j as sn
    rows = rp.rows(loaded_at="2026-10-31T00:00:00+00:00")
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    chains = _parse_chains(sn.IMPACT_ROWS)
    assert len(chains) == 8 and _parse_chains(sn.IMPACT_PATHS) == chains, "the paths form is the same walk"
    assert sum(1 for steps, _ in chains for *_, rv in steps if rv) == 5, "every intermediate link is filtered on approved: 4 two-step chains and the three-step chain's two"
    assert "AS followed" in sn.IMPACT_ROWS and "'no, withdrawn'" in sn.IMPACT_ROWS
    assert sn.IMPACT_PATHS.count("OPTIONAL CALL {") == 1 and sn.IMPACT_PATHS.rstrip().endswith("RETURN a, p")
    walked = 0
    for nid in reg["nodes"]:
        expect = _walk_rows(reg, nid)
        assert _simulate(chains, rows, nid) == expect, nid
        walked += len(expect)
    assert walked > 0 and len(_walk_rows(reg, "APP-0002")) == 5 and len(_walk_rows(reg, "JRN-0002")) == 0
    assert _simulate(chains, rows, "APP-0002") == _walk_rows(reg, "APP-0002") and any("(inverse)" in r[1] for r in _simulate(chains, rows, "APP-0002"))
    # the walk's depth is bounded by the register's own kinds: every chain ends on a product or a capability
    rels = {r: reg["relationships"][r]["type"] for r in ("supports", "delivers", "realizes", "is_supported_by", "concerns")}
    assert set(rels["supports"]["target_kind"]) | set(rels["is_supported_by"]["target_kind"]) <= {"activity", "subprocess", "end_to_end_process"}
    assert set(rels["delivers"]["target_kind"]) | set(rels["concerns"]["target_kind"]) <= {"product", "variant"}
    assert set(rels["realizes"]["target_kind"]) <= {"capability", "sub_capability"}


def _fixture():
    """A small register with what the vendored copy lacks: a deprecated intermediate node (PROC-2,
    reached and not expanded), a retired journey step (JRN-2, the same), a deprecated start (APP-2,
    nothing walked), two links of one type between one pair (both reported), a parent (never climbed)
    and, since v0.2.2, a proposed link as the only route to a process (PROC-3: the edge reported as
    withdrawn, the process not expanded, so PRD-4 behind it is never reached)."""
    N = {"APP-1": ("applications", "approved"), "APP-2": ("applications", "deprecated"), "MOD-1": ("applications", "approved"),
         "PROC-1": ("processes", "approved"), "PROC-2": ("processes", "deprecated"), "PROC-3": ("processes", "approved"),
         "PRD-1": ("products", "approved"), "PRD-2": ("products", "approved"), "PRD-3": ("products", "approved"), "PRD-4": ("products", "approved"),
         "CAP-1": ("capabilities", "approved"), "JRN-1": ("journeys", "approved"), "JRN-2": ("journeys", "retired")}
    L = [("supports", "REL-1", "APP-1", "PROC-1", "approved"), ("supports", "REL-2", "APP-1", "PROC-1", "proposed"),
         ("supports", "REL-3", "APP-1", "PROC-2", "approved"), ("supports", "REL-4", "APP-2", "PROC-1", "approved"),
         ("delivers", "REL-5", "PROC-1", "PRD-1", "approved"), ("delivers", "REL-6", "PROC-2", "PRD-2", "approved"),
         ("realizes", "REL-7", "PROC-1", "CAP-1", "approved"), ("is_supported_by", "REL-8", "JRN-1", "PROC-1", "approved"),
         ("is_supported_by", "REL-9", "JRN-2", "PROC-1", "approved"), ("concerns", "REL-10", "JRN-1", "PRD-1", "approved"),
         ("concerns", "REL-11", "JRN-2", "PRD-3", "approved"),
         ("supports", "REL-12", "APP-1", "PROC-3", "proposed"), ("delivers", "REL-13", "PROC-3", "PRD-4", "approved")]
    reg = {"nodes": {k: {"_taxonomy": t, "state": s, "parent": "APP-1" if k == "MOD-1" else ""} for k, (t, s) in N.items()},
           "relationships": {}}
    for rel, lid, src, tgt, st in L:
        reg["relationships"].setdefault(rel, {"links": []})["links"].append({"id": lid, "source": src, "target": tgt, "state": st, "owner": "ORG-1", "evidence": [f"kit:{lid}"]})
    rows = {"nodes": [{"reg_id": k, "taxonomy": t, "state": s, "name": k} for k, (t, s) in N.items()],
            "links": [{"reg_id": lid, "evidence": [f"kit:{lid}"]} for _, lid, *_ in L], "typed": {}}
    for rel, lid, src, tgt, st in L:
        rows["typed"].setdefault("REG_" + rel.upper(), []).append({"source": src, "target": tgt, "props": {"reg_id": lid, "state": st, "owner": "ORG-1"}})
    rows["typed"]["REG_PARENT"] = [{"source": "MOD-1", "target": "APP-1", "props": {"reg_id": "", "state": "", "owner": ""}}]
    return reg, rows


def test_register_impact_cypher_stops_at_a_deprecated_node_like_the_walk():
    import store_neo4j as sn
    reg, rows = _fixture()
    chains = _parse_chains(sn.IMPACT_ROWS)
    for nid in reg["nodes"]:
        assert _simulate(chains, rows, nid) == _walk_rows(reg, nid), nid
    app1 = _walk_rows(reg, "APP-1")
    assert [r[2] for r in app1].count("PROC-1") == 2 and "PROC-2" in [r[2] for r in app1], "two supports links reported; the deprecated process reached"
    assert "PRD-2" not in [r[2] for r in app1] and "PRD-3" not in [r[2] for r in app1], "neither the deprecated nor the retired node is expanded"
    assert ("PROC-1", "is_supported_by (inverse)", "JRN-2", "approved", "ORG-1", ("kit:REL-9",), False) in app1, "a retired far node: reported, withdrawn"
    assert ("APP-1", "supports", "PROC-3", "proposed", "ORG-1", ("kit:REL-12",), False) in app1 and "PRD-4" not in [r[2] for r in app1], "a proposed link: reported, withdrawn, not followed"
    assert ("APP-1", "supports", "PROC-1", "proposed", "ORG-1", ("kit:REL-2",), False) in app1 and ("APP-1", "supports", "PROC-1", "approved", "ORG-1", ("kit:REL-1",), True) in app1
    assert _walk_rows(reg, "APP-2") == [] and _walk_rows(reg, "MOD-1") == [], "a deprecated start walks nothing; a parent is never climbed"
    assert len(app1) == 9 and sum(1 for r in app1 if not r[6]) == 4
    assert register_view._load_tools()["impact"].reached(register_view._load_tools()["impact"].walk(reg, "APP-1")) == {"PROC-1", "PROC-2", "PROC-3", "PRD-1", "CAP-1", "JRN-1", "JRN-2"} - {"PROC-2", "PROC-3", "JRN-2"} | {"PRD-1"}


# ---- task-0024.01: the impact panel carries the walk's Cypher; the listed text uses the register's default start
@on_cargo_quote
def test_listed_impact_query_uses_the_registers_default_start_and_the_panel_carries_the_typed_id():
    import os
    import server
    import store_neo4j as sn
    default = register_view.impact_default()
    assert default == register_view.build()["impact_default"] == "APP-0002"
    listed = {q["id"]: q for q in server.cypher_list()}
    for qid, raw in (("register-impact", sn.IMPACT_ROWS), ("register-impact-paths", sn.IMPACT_PATHS)):
        assert listed[qid]["text"] == raw.replace(f"'{sn.IMPACT_START}'", f"'{default}'") and default in listed[qid]["title"]
        assert f"{{reg_id:'{default}'}}" in listed[qid]["text"] and listed[qid]["text"].count("reg_id:'") == 1
    # the adapter's literal is the anchor the server replaces; the server itself names no id
    assert "APP-0002" not in (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    # the panel for a typed id: the same two forms with that id, the needs chip's data and a code section the page renders
    w = server.impact_view("APP-0003")
    assert w["cypher"]["rows"] == listed["register-impact"]["text"].replace(f"'{default}'", "'APP-0003'")
    assert w["cypher"]["paths"] == listed["register-impact-paths"]["text"].replace(f"'{default}'", "'APP-0003'")
    assert w["cypher"]["needs"] == "register" and w["cypher"]["needs_text"] == server.NEEDS_TEXT["register"]
    sec = w["panel"]["sections"][-1]
    assert sec["heading"] == "The walk in Cypher" and sec["needs"] == "register" and [c["text"] for c in sec["code"]] == [w["cypher"]["rows"], w["cypher"]["paths"]]
    assert "The page runs nothing" not in sec["text"] and "wipes the projection" in sec["text"]
    assert len(w["edges"]) == len(register_view.impact("APP-0003")["edges"]) and w["panel"]["sections"][0]["heading"] == "Edges walked"
    _check_sentences(w["text_registry"])
    assert all(any(item["text"] == c["label"] for item in w["text_registry"]) for c in sec["code"]), "the labels are controlled sentences"
    assert server.impact_view("APP-9999") is None
    # the rdflib store has no console: no Cypher on the panel, the walk unchanged
    os.environ["KG_STORE"] = "rdflib"
    try:
        r = server.impact_view("APP-0003")
    finally:
        del os.environ["KG_STORE"]
    assert r["cypher"] is None and [sec["heading"] for sec in r["panel"]["sections"]] == ["Edges walked", "Reached"]
    # the page: a code section renders a copy button and the chip; the copy buttons are wired where a panel opens
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "x.code ? x.code.map(" in page and 'class="codebox"' in page and "needsChip(x.needs, x.needs_text)" in page
    assert "wireRefs(host); wireCopy(host);" in page and "function wireCopy(root)" in page and "function needsChip(" in page
    ci = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert 'w["cypher"]["rows"]' in ci


# ---- task-0024.02 and task-0025: a Browser link per form opens a served guide whose click fills the editor,
# verified in the stack job; the manual's edit command raced the editor in Browser 5.26.0 (doc-0003)
def test_impact_browser_links_open_a_served_guide_and_the_stack_job_runs_them():
    import os
    import re as _re
    import threading
    import urllib.parse
    import urllib.request
    from http.server import ThreadingHTTPServer
    import server
    sys.path.insert(0, str(ROOT / "demo" / "tools"))
    import check_impact_cypher as cic
    w = server.impact_view("APP-0003", "http://demo.test:8080")
    links, guides = w["cypher"]["browser"], w["cypher"]["guide"]
    assert set(links) == set(guides) == {"rows", "paths"} and [c["browser"] for c in w["panel"]["sections"][-1]["code"]] == [links["rows"], links["paths"]]
    host = urllib.parse.urlparse(server.BROWSER_URL).hostname
    for form, link in links.items():
        u = urllib.parse.urlsplit(link)
        assert link.startswith(server.BROWSER_URL + "/browser/?") and u.path == "/browser/"
        q = urllib.parse.parse_qs(u.query)
        assert q["connectURL"] == [f"bolt://neo4j@{host}:7687"] and q["cmd"] == ["play"] and q["arg"] == ["http://demo.test:8080" + guides[form]]
        assert guides[form] == f"/api/register/impact/APP-0003/guide/{form}" and cic.guide_url_of(link) == q["arg"][0]
        # the Browser's own reading of a URL command (5.26.0): literal + to space, the whole URL decoded, the arg up to & or #
        assert _re.findall(r"[\?&]arg=([^&#]*)", urllib.parse.unquote(link.replace("+", " "))) == [q["arg"][0]]
        # the guide's block is the form's text, as the Browser would put it in the editor (textContent, trimmed)
        guide = server.impact_guide("APP-0003", form)
        assert guide.startswith('<article class="guide">') and 'class="pre-scrollable code runnable"' in guide and "<script" not in guide
        assert cic.block_of(guide) == w["cypher"][form] == w["cypher"][form].strip()
        assert "Nothing runs until you press play." in guide and "project the register again first" in guide
    assert "A click on the guide's query puts it in the editor; nothing runs until you press play." in w["panel"]["sections"][-1]["text"]
    assert "cmd=edit" not in (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8").split("def guide_html")[1].split("def browser_play_url")[0].replace("(?cmd=edit&arg=)", "")
    _check_sentences(w["text_registry"])
    assert register_view.with_cypher(register_view.impact("APP-0003"), {"rows": "r", "paths": "p"}, "x")["cypher"]["browser"] is None
    assert server.impact_guide("APP-9999", "rows") is None and server.impact_guide("APP-0003", "edit") is None
    os.environ["KG_STORE"] = "rdflib"
    try:
        assert server.impact_view("APP-0003")["cypher"] is None and server.impact_guide("APP-0003", "rows") is None
    finally:
        del os.environ["KG_STORE"]
    # the route as the Browser fetches it: cross-origin, the preflight answered, the header on the guide and nowhere else
    class Quiet(server.Handler):
        def log_message(self, fmt, *args):
            pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        w2 = json.loads(urllib.request.urlopen(base + "/api/register/impact/APP-0003").read())
        assert cic.guide_url_of(w2["cypher"]["browser"]["paths"]) == base + guides["paths"], "the link names the host the viewer used"
        with urllib.request.urlopen(base + "/api/register/impact/APP-0003") as r:
            assert r.headers.get("Access-Control-Allow-Origin") is None
        assert cic.block_of(cic.fetch_guide(base + guides["rows"])) == w["cypher"]["rows"]
        assert cic.block_of(cic.fetch_guide(base + guides["paths"])) == w["cypher"]["paths"]
        for bad in ("/api/register/impact/APP-9999/guide/rows", "/api/register/impact/APP-0003/guide/edit"):
            for method in ("GET", "OPTIONS"):
                try:
                    urllib.request.urlopen(urllib.request.Request(base + bad, method=method))
                except urllib.error.HTTPError as e:
                    assert e.code == 404 and e.headers.get("Access-Control-Allow-Origin") is None, (bad, method)
                else:
                    raise AssertionError((bad, method))
        try:
            urllib.request.urlopen(urllib.request.Request(base + "/api/register", method="OPTIONS"))
        except urllib.error.HTTPError as e:
            assert e.code == 404
        else:
            raise AssertionError("OPTIONS answered off the guide route")
    finally:
        httpd.shutdown()
        httpd.server_close()
    # the comparator's shapes: the walk's edges as the rows form returns them, the paths' distinct relationships and starts
    edges = [{"from": "A", "rel": "supports", "to": "P", "state": "approved", "owner": "O", "evidence": ["e1"]}]
    rows = [{"from": "A", "relationship": "supports", "to": "P", "link state": "approved", "owner": "O", "evidence": None}]
    assert cic.row_keys(rows) == [("A", "supports", "P", "approved", "O", ())] and cic.edge_keys(edges) == [("A", "supports", "P", "approved", "O", ("e1",))]

    class Rel:
        def __init__(self, i):
            self.element_id = i

    class P:
        relationships = (Rel("r1"), Rel("r2"), Rel("r1"))
    assert cic.path_shape([{"a": {"reg_id": "A"}, "p": P()}, {"a": {"reg_id": "A"}, "p": None}]) == (2, {"A"})
    for bad in ("http://x/browser/?connectURL=b&cmd=edit&arg=a", "http://x/browser/?cmd=play&arg=http://d/g"):
        try:
            cic.guide_url_of(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(bad)
    assert cic.block_of('<article><pre class="code runnable"> MATCH (a) &amp;&lt; x\n</pre></article>') == "MATCH (a) &< x"
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert 'href="${esc(c.browser)}" target="_blank" rel="noopener">open in the Browser</a>' in page
    ci = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "demo/tools/check_impact_cypher.py" in ci and ci.index("check_saved_queries.py") < ci.index("check_impact_cypher.py")
    compose = (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "NEO4J_browser_remote__content__hostname__whitelist: guides.neo4j.com,localhost,${KG_DEMO_HOST:-localhost}" in compose
    readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    assert "**The impact panel's Browser links.**" in readme and "cmd=play" in readme and "wipes the projection first" in readme and "KG_DEMO_HOST" in readme


def test_register_tools_load_once_under_concurrent_requests():
    """The page asks for the saved queries and the register at the same time, and since task-0025
    both load the register's tools: on the threading server two imports at once saw each other's
    half-built modules ("cannot import name 'ROOT' from 'register'"). One lock, one load."""
    import threading
    register_view._tools = None
    results, errors = [], []

    def load():
        try:
            results.append(id(register_view._load_tools()))
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))
    threads = [threading.Thread(target=load) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors
    assert len(set(results)) == 1 and register_view._tools is not None
    assert register_view.impact("APP-0002")["reached"]["products"]

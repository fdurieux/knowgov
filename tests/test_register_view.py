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
    assert v["source"]["tag"] == "v0.2.10" and v["source"]["commit"].startswith("4149e06")  # the tag sits on the vendored commit
    assert v["pinned"] and v["run_date"] == v["source"]["pinned_date"]
    assert v["summary"] == {"nodes": 57, "links": 65, "errors": 0, "warnings": 7}   # the J-F slice (decisions 0005 and 0006): 29 nodes, 37 links, seven parentless nodes; ORG-0004 (decision 0011)
    assert v["coverage_lines"][0] == "C1: 7/8 covered, 1 excepted, 0 uncovered"
    assert v["coverage"]["C2"]["uncovered"] == [] and v["coverage"]["C3"]["uncovered"] == []
    assert sorted(v["nodes_by_taxonomy"]) == sorted(["capabilities", "products", "journeys", "processes", "applications", "information", "organisation"])
    assert sum(len(ns) for ns in v["nodes_by_taxonomy"].values()) == 57 and len(v["links"]) == 65
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
    assert v["subject_system"] == "kit" and v["slice"] == {"nodes": 28, "links": 28, "other_nodes": 29, "other_systems": ["jef_kit"]}
    assert v["impact_default"] == "APP-0002" and "This subject's slice is the source system kit: 28 nodes and 28 links." in v["intro"]
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
    assert "PRD-0002" in w["reached"]["products"] and "JRN-0002" in w["reached"]["journeys"] and len(w["edges"]) == 10
    assert w["panel"]["title"] == "Impact of retiring APP-0002" and "does not climb a node's parent" in w["panel"]["intro"]
    cols = w["panel"]["sections"][0]["table"]["cols"]
    assert all(len(r) == len(cols) for r in w["panel"]["sections"][0]["table"]["rows"])
    # since v0.2.6 (decision 0010) TariffEngine's journey step leads on to the product it concerns;
    # the J-F slice's application reaches its process and no product, and says so
    t = register_view.impact("APP-0003")
    assert t["reached"]["products"] == ["PRD-0002"] and "JRN-0003" in t["reached"]["journeys"]
    assert "No product is reached" not in t["panel"]["sections"][0]["text"]
    n = register_view.impact("APP-0009")
    assert n["reached"]["products"] == [] and n["reached"]["processes"] == ["PROC-0009"]
    assert "No product is reached" in n["panel"]["sections"][0]["text"]
    assert register_view.impact("APP-9999") is None
    # an information entity now walks to what uses it; a capability domain has no link of its own
    assert "PROC-0001" in register_view.impact("ENT-0004")["reached"]["processes"]
    leaf = register_view.impact("CAP-0001")
    assert leaf["edges"] == [] and "No link starts at this node" in leaf["panel"]["sections"][0]["text"]
    for v in (w, t, n, leaf):
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
    assert c["nodes"] == 57 and c["links"] == 65 and c["types"] == 10 and c["documents"] == 10 and c["externals"] == 1 and c["exceptions"] == 1
    assert r["stamp"]["tag"] == "v0.2.10" and r["stamp"]["commit"].startswith("4149e06") and r["stamp"]["export_date"] == "2026-10-30"   # the subject's export, not the newest
    assert len(r["parents"]) == sum(1 for n in r["nodes"] if n["parent"]) and len(r["owners"]) == 57
    assert sum(len(v) for v in r["typed"].values()) == 64 and len(r["maps_to"]) == 1 and len(r["link_of"]) == 129 and len(r["of_type"]) == 65
    assert {"reg_id": "REL-08002", "path": "kit/requirements.md", "anchor": "kit:requirements.md#REQ-05"} in r["cites"]
    assert r["excepts"] == [{"reg_id": "EXC-0001", "node": "JRN-0004", "rule": "C1", "expires": "2027-01-31"}]
    assert c["relationships"] == 64 + 1 + 129 + 65 + len(r["cites"]) + len(r["parents"]) + 57 + 1
    # every property is what Neo4j can hold: a string, number, boolean or list of strings; every row is stamped
    ok = (str, int, float, bool)
    for key in ("nodes", "types", "links", "documents", "externals", "exceptions"):
        for row in r[key]:
            assert row["tag"] == "v0.2.10" and row["commit"] and row["loaded_at"] and len(row["digest"]) == 64, (key, row["reg_id"])
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
    assert "POST localhost:8080/api/register/project" in ci and '"tag"]=="v0.2.10"' in ci
    assert "projection" in views.GLOSSARY and "**The projection.**" in (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    adapter = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")   # the saved queries are the adapter's
    ids = [m.group(1) for m in _re.finditer(r'\{"id": "([a-z0-9-]+)", "needs": "[^"]+", "title"', adapter)]
    assert ids[-5:] == ["register-tag", "register-impact", "register-impact-paths", "register-c1", "register-cites"], ids
    for cy in ("MATCH SHORTEST 1 (a)", '("REG_DELIVERS", "REG_REALIZES")', "REG_EXCEPTS", "a.id ENDS WITH '/' AND d.path STARTS WITH a.id", "v.sha256 = d.digest THEN 'same as tag'"):
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
    assert len(needs) == 20 and set(needs.values()) <= {"scenario", "S6", "S4", "register", "register+scenario"}
    assert all(q["needs_text"] for q in listed)
    assert {q["id"]: q["needs_text"] for q in listed}["invalidation"] == "S6 loaded deterministically"
    assert {q["id"] for q in views.SUBJECT.queries} == {"three-valued", "gate", "invalidation", "contradiction"}, "the subject's own queries"
    assert needs["invalidation"] == "S6" and needs["contradiction"] == "S4" and needs["register-cites"] == "register+scenario"
    assert all(needs[k] == "register" for k in ("register-tag", "register-impact", "register-impact-paths", "register-c1", "register-impact-children",
                                               "register-realisers", "register-realisers-children",
                                               "register-dependants-capability", "register-dependants-information"))
    assert needs["register-node-store"] == needs["register-node-statements"] == "register+scenario"
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
            assert v["summary"]["nodes"] == 57 and len(v["links"]) == 65, "the same content, read from the other root"
            assert rv.impact("APP-0002")["reached"]["products"]
            fp = rv.footprint(views.build("S2", views.default_source("S2"), ROOT / "nonexistent-demo-runs"))
            assert fp["box"]["colour"] == "warn" and fp["uncited"] == 0, "the subject's map and manifest join the mounted register"
        finally:
            del os.environ["KG_REGISTER"]
            rv = importlib.reload(register_view)
    assert rv.REGISTER == (DEMO / "register").resolve() and rv.source_info()["kind"] == "copy"


# ---- task-0023, task-0044: the saved query register-impact is the walk impact.py makes
# The Cypher's CALL (a) { } block is parsed (the step predicate, one term per taxonomy and direction,
# read twice: in the quantified path that finds the expanded nodes and in the match of the edges met
# from each; the filters on the start, the quantified step's link and far node) and simulated over the
# projection's rows, so the test reads the adapter's text, not a copy of it.
_TERM = re.compile(r"(\w+)\.taxonomy = '(\w+)' AND type\((\w+)\) IN \[([^\]]*)\] AND (startNode|endNode)\((\w+)\) = (\w+)")
_REACH = re.compile(r"MATCH SHORTEST 1 \(a\) \(\(x:RegNode\)-\[s\]-\(y:RegNode\) WHERE \((.*?)\)\s+AND s\.state = 'approved' "
                    r"AND NOT y\.state IN \['deprecated','retired'\]\)\* \(n:RegNode\)\s+WHERE NOT a\.state IN \['deprecated','retired'\]", re.S)
_MEET = re.compile(r"MATCH p = \(n\)-\[r\]-\(t:RegNode\) WHERE \((.*?)\)\s+RETURN p\s*$", re.S)
sys.path.insert(0, str(ROOT / "harness"))


def _terms(pred, node, rel):
    """The predicate's terms as {(taxonomy, relationship type, the node is the source?)}; every term
    must be understood and name ``node`` and ``rel`` only."""
    out = set()
    for term in pred.split(" OR "):
        m = _TERM.fullmatch(" ".join(term.split()))
        assert m, term
        assert (m.group(1), m.group(3), m.group(6), m.group(7)) == (node, rel, rel, node), term
        for t in m.group(4).split(","):
            out.add((m.group(2), t.strip().strip("'"), m.group(5) == "startNode"))
    return out


def _parse_walk(text):
    """The walk's steps, from the CALL block; the two readings of the predicate must be the same steps."""
    block = text[text.index("CALL (a) {") + len("CALL (a) {"):text.index("\n}\n")]
    block = "\n".join(ln for ln in block.splitlines() if not ln.strip().startswith("//"))
    reach, meet = _REACH.search(block), _MEET.search(block)
    assert reach and meet and block.index(reach.group(0)) < block.index(meet.group(0)), block
    assert block.replace(reach.group(0), "").replace(meet.group(0), "").strip() == "", "nothing else in the block"
    steps = _terms(reach.group(1), "x", "s")
    assert _terms(meet.group(1), "n", "r") == steps, "the expanded nodes and the edges met follow one predicate"
    return steps


def _simulate(steps, rows, start):
    """The rows the Cypher gives from ``start`` over the projection's rows: the nodes the quantified
    path reaches over live steps (the start, if live, included), then every step from each, as
    (from, relationship, to, link state, owner, evidence, live), live as ``followed`` computes it."""
    nodes = {n["reg_id"]: n for n in rows["nodes"]}
    evidence = {l["reg_id"]: tuple(l["evidence"]) for l in rows["links"]}
    dead = lambda nid: nodes[nid]["state"] in ("deprecated", "retired")  # noqa: E731
    by_node = {}
    for rtype, items in rows["typed"].items():
        for it in items:
            rel = (rtype, it["source"], it["target"], it["props"]["reg_id"], it["props"]["state"], it["props"]["owner"])
            by_node.setdefault(it["source"], []).append((rel, True))
            by_node.setdefault(it["target"], []).append((rel, False))

    def met(nid):   # (rel, the node is the source?) for every step the predicate allows from nid
        return [(rel, src) for rel, src in by_node.get(nid, []) if (nodes[nid]["taxonomy"], rel[0], src) in steps]

    if start not in nodes or dead(start):
        return []
    expanded, frontier = {start}, [start]
    while frontier:
        nxt = []
        for nid in frontier:
            for rel, src in met(nid):
                far = rel[2] if src else rel[1]
                if rel[4] == "approved" and not dead(far) and far not in expanded:
                    expanded.add(far)
                    nxt.append(far)
        frontier = nxt
    out = []
    for nid in expanded:
        for (rtype, s, t, link, state, owner), src in met(nid):
            far = t if src else s
            label = rtype.replace("REG_", "").lower() + ("" if src else " (inverse)")
            out.append((nid, label, far, state, owner, evidence[link], state == "approved" and not dead(far)))
    return sorted(out)


def _walk_rows(reg, start):
    T = register_view._load_tools()
    return sorted((e["from"], e["rel"], e["to"], e["state"], e["owner"], tuple(e["evidence"]), e["live"]) for e in T["impact"].walk(reg, start))


def test_register_impact_cypher_equals_the_walk_on_every_node():
    import register_project as rp
    import store_neo4j as sn
    rows = rp.rows(loaded_at="2026-10-31T00:00:00+00:00")
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    steps = _parse_walk(sn.IMPACT_ROWS)
    assert _parse_walk(sn.IMPACT_PATHS) == steps, "the paths form is the same walk"
    # the steps are the vendored walk's FORWARD table, every kind and direction, nothing more
    forward = register_view._load_tools()["impact"].FORWARD
    assert steps == {(tax, "REG_" + rel.upper(), fwd) for tax, rels in forward.items() for rel, fwd in rels} and len(steps) == 11
    assert "AS followed" in sn.IMPACT_ROWS and "'no, withdrawn'" in sn.IMPACT_ROWS
    assert sn.IMPACT_PATHS.count("OPTIONAL CALL (a) {") == 1 and "WITH a MATCH" not in sn.IMPACT_WALK and sn.IMPACT_PATHS.rstrip().endswith("RETURN a, p")
    walked = 0
    for nid in reg["nodes"]:
        expect = _walk_rows(reg, nid)
        assert _simulate(steps, rows, nid) == expect, nid
        walked += len(expect)
    assert walked == 469 and len(_walk_rows(reg, "APP-0002")) == 10 and len(_walk_rows(reg, "JRN-0002")) == 8
    assert _simulate(steps, rows, "APP-0002") == _walk_rows(reg, "APP-0002") and any("(inverse)" in r[1] for r in _simulate(steps, rows, "APP-0002"))
    # from every kind something rests on (decision 0010): a capability, an information entity and a product reach something
    assert all(_walk_rows(reg, nid) for nid in ("CAP-0002", "ENT-0002", "PRD-0002"))
    # the kinds form cycles (a process delivers a product, the product walks back over delivers), so no
    # fixed set of chains is the walk: the quantified path is, its shortest path per node found breadth first
    assert ("processes", "REG_DELIVERS", True) in steps and ("products", "REG_DELIVERS", False) in steps


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
    steps = _parse_walk(sn.IMPACT_ROWS)
    for nid in reg["nodes"]:
        assert _simulate(steps, rows, nid) == _walk_rows(reg, nid), nid
    app1 = _walk_rows(reg, "APP-1")
    assert [r[2] for r in app1 if r[1] == "supports"].count("PROC-1") == 2 and "PROC-2" in [r[2] for r in app1], "two supports links reported; the deprecated process reached"
    assert "PRD-2" not in [r[2] for r in app1] and "PRD-3" not in [r[2] for r in app1], "neither the deprecated nor the retired node is expanded"
    assert ("PROC-1", "is_supported_by (inverse)", "JRN-2", "approved", "ORG-1", ("kit:REL-9",), False) in app1, "a retired far node: reported, withdrawn"
    assert ("APP-1", "supports", "PROC-3", "proposed", "ORG-1", ("kit:REL-12",), False) in app1 and "PRD-4" not in [r[2] for r in app1], "a proposed link: reported, withdrawn, not followed"
    assert ("APP-1", "supports", "PROC-1", "proposed", "ORG-1", ("kit:REL-2",), False) in app1 and ("APP-1", "supports", "PROC-1", "approved", "ORG-1", ("kit:REL-1",), True) in app1
    assert _walk_rows(reg, "APP-2") == [] and _walk_rows(reg, "MOD-1") == [], "a deprecated start walks nothing; a parent is never climbed"
    assert len(app1) == 12 and sum(1 for r in app1 if not r[6]) == 4
    assert ("PRD-1", "delivers (inverse)", "PROC-1", "approved", "ORG-1", ("kit:REL-5",), True) in app1, "one link met from both ends, once per end"
    assert _walk_rows(reg, "PRD-2") == [("PRD-2", "delivers (inverse)", "PROC-2", "approved", "ORG-1", ("kit:REL-6",), False)], "a product walks back to a deprecated process and stops"
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
    assert r["cypher"] is None and [sec["heading"] for sec in r["panel"]["sections"]] == ["Edges walked", "Reached", "Who to inform", "Assertions its cited anchors name"]
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
    edges = [{"from": "A", "rel": "supports", "to": "P", "state": "approved", "owner": "O", "evidence": ["e1"], "live": True, "to_start": False}]
    rows = [{"from": "A", "relationship": "supports", "to": "P", "link state": "approved", "followed": "yes", "owner": "O", "evidence": None,
             "unit": "ORG-1", "unit name": "Unit", "owns links": ["ORG-2", "ORG-1"]}]
    owners = {"P": {"unit": "ORG-1", "name": "Unit", "owns": ["ORG-1", "ORG-2"]}}
    assert cic.row_keys(rows) == [("A", "supports", "P", "approved", "yes", "O", (), "ORG-1", "Unit", ("ORG-1", "ORG-2"))]
    assert cic.edge_keys(edges, owners) == [("A", "supports", "P", "approved", "yes", "O", ("e1",), "ORG-1", "Unit", ("ORG-1", "ORG-2"))]
    assert cic.row_keys([dict(rows[0], unit=None, **{"unit name": None, "owns links": []})])[0][-3:] == ("", "", ())

    class Rel(dict):   # the driver's relationship: an element id, its properties by get
        def __init__(self, i, link):
            super().__init__(reg_id=link)
            self.element_id = i

    class P:
        relationships = (Rel("r1", "REL-1"), Rel("r2", "REL-2"), Rel("r1", "REL-1"))
    assert cic.path_shape([{"a": {"reg_id": "A"}, "p": P()}, {"a": {"reg_id": "A"}, "p": None}]) == (2, {"REL-1", "REL-2"}, {"A"})
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


# ---- the walk's other direction (doc-0008 §4): saved queries from a capability, an information node,
# and from a node to the store, each listed from the register's own default for its taxonomy
@on_cargo_quote
def test_dependants_and_node_store_queries_are_listed_from_the_registers_defaults():
    import server
    import store_neo4j as sn
    assert register_view.start_default("capabilities") == "CAP-0002"
    assert register_view.start_default("information") == "ENT-0002"
    assert register_view.start_default("applications") == register_view.impact_default() == "APP-0002"
    listed = {q["id"]: q for q in server.cypher_list()}
    for qid, raw, literal, tax, needs in (
            ("register-dependants-capability", sn.DEPENDANTS_CAPABILITY, sn.CAPABILITY_START, "capabilities", "register"),
            ("register-dependants-information", sn.DEPENDANTS_INFORMATION, sn.INFORMATION_START, "information", "register"),
            ("register-node-store", sn.MODULE_STORE, sn.IMPACT_START, "applications", "register+scenario"),
            ("register-node-statements", sn.NODE_STATEMENTS, sn.INFORMATION_START, "information", "register+scenario")):
        q = listed[qid]
        start = register_view.start_default(tax)
        assert q["needs"] == needs and q["start"] == tax and sn.START_LITERALS[tax] == literal
        assert q["text"] == raw.replace(f"'{literal}'", f"'{start}'") and q["text"].count("reg_id:'") == 1 and start in q["title"]
        assert ";" not in q["text"], "the console checker splits on ';'"
    for raw in (sn.DEPENDANTS_CAPABILITY, sn.DEPENDANTS_INFORMATION):
        # one step on only over an approved link to a live node; every edge met is a row and says whether it was followed
        assert raw.count("r0.state = 'approved'") == 2 and raw.count("NOT p.state IN ['deprecated','retired']") == 2
        assert "'no, withdrawn'" in raw and "CALL (" in raw
    assert "{state:'approved'}" in sn.MODULE_STORE and "Derived" in sn.MODULE_STORE
    # the server names no start of its own: the adapter's literals are the anchors it replaces
    srv = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert not any(x in srv for x in ("CAP-0002", "ENT-0002", "APP-0002"))


# ---- the store join at the grain of the cited anchor (task-0046; doc-0011 point 1)
def test_node_statements_query_is_the_ports_cypher_at_anchor_grain():
    import store_neo4j as sn
    raw = sn._NODE_STATEMENTS
    assert raw.count("$start") == 1 and sn.NODE_STATEMENTS == raw.replace("$start", f"'{sn.INFORMATION_START}'")
    assert ";" not in raw, "the console checker splits on ';'"
    # approved links only; an anchor narrows to the fragments whose locator holds it as a path segment,
    # a citation with none reaches the whole document; every version, so an invalidated statement still shows its code
    assert "RegLink {state:'approved'}" in raw and "anchor IS NULL OR anchor IN split(substring(f.locator, size(file)), '/')" in raw
    # a document is a file artefact, or a file of a directory artefact read after its "<name>:" (task-0077)
    join = "MATCH (a:Artefact) WHERE a.id = d.path OR (a.id ENDS WITH '/' AND d.path STARTS WITH a.id)"
    assert join in raw and join in sn.MODULE_STORE and "Artefact {id:d.path}" not in raw + sn.MODULE_STORE
    assert "f.locator STARTS WITH file" in raw and "substring(d.path, size(a.id)) + ':'" in raw
    assert "[:HAS_VERSION]->(v:Version)" in raw and ":CURRENT" not in raw and "USED_ASSERTION" in raw
    for k in ("statement", "status", "document", "anchors", "links", "versions", "fragments", "derived"):
        assert f" AS {k}" in raw, k
    src = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    body = src[src.index("def register_node_statements("):src.index("# ---- what the page shows")]
    assert 'anchor not in loc[len(file):].split("/")' in body and '"HAS_VERSION"' in body and 'self.prop(l, "state") != "approved"' in body
    assert 'aid.endswith("/") and path.startswith(aid)' in body and 'file = path[len(aid):] + ":"' in body and "not loc.startswith(file)" in body


# ---- task-0078: the statements view carries a Browser link that pre-fills register-node-statements, as the walk's does
def test_statements_view_has_a_browser_link_to_a_served_guide_of_register_node_statements():
    import os
    import urllib.parse
    import server
    import store_neo4j as sn
    sys.path.insert(0, str(ROOT / "demo" / "tools"))
    import check_impact_cypher as cic
    text = sn.node_statements_cypher("ENT-0009")
    assert text == sn._NODE_STATEMENTS.replace("$start", "'ENT-0009'") and text.count("reg_id:'") == 1
    listed = {q["id"]: q for q in sn.SAVED_QUERIES}["register-node-statements"]
    assert sn.node_statements_cypher(sn.INFORMATION_START) == listed["text"], "the saved query, from the node typed"
    assert server.GUIDE_FORMS == ("rows", "paths", "statements") and server.WALK_FORMS == ("rows", "paths")
    w = server.impact_view("ENT-0009", "http://demo.test:8080", statements=False)
    assert "statements" not in w and set(w["cypher"]["browser"]) == {"rows", "paths"}
    w = server.impact_view("ENT-0009", "http://demo.test:8080")
    sv = w["statements"]["cypher"]
    sec = [x for x in w["panel"]["sections"] if x["heading"] == "Assertions its cited anchors name"][0]
    assert set(w["cypher"]["browser"]) == {"rows", "paths"}, "the walk's links are unchanged"
    assert sv["text"] == text and sv["guide"] == "/api/register/impact/ENT-0009/guide/statements"
    assert sec["code"] == [{"label": "Rows, one per assertion and cited document", "text": text, "browser": sv["browser"]}]
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(sv["browser"]).query)
    assert q["cmd"] == ["play"] and cic.guide_url_of(sv["browser"]) == "http://demo.test:8080" + sv["guide"]
    guide = server.impact_guide("ENT-0009", "statements")
    assert cic.block_of(guide) == text and "the assertions its cited anchors name" in guide and "<script" not in guide
    assert "A click on the guide's query puts it in the editor; nothing runs until you press play." in sec["text"]
    _check_sentences(w["text_registry"])
    assert server.impact_guide("APP-9999", "statements") is None
    # the page draws a section's code with its Browser link, whichever section holds it
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "${code(x)}" in page and "c.browser ?" in page
    os.environ["KG_STORE"] = "rdflib"
    try:
        w = server.impact_view("ENT-0009")
        assert "cypher" not in w["statements"] and server.impact_guide("ENT-0009", "statements") is None
        assert "code" not in [x for x in w["panel"]["sections"] if x["heading"] == "Assertions its cited anchors name"][0]
    finally:
        del os.environ["KG_STORE"]
    # the stack job follows every node's statements link as it follows the walk's
    src = (ROOT / "demo" / "tools" / "check_impact_cypher.py").read_text(encoding="utf-8")
    assert 'sv["browser"]' in src and "statement_keys(st_rows) != statement_keys(shown)" in src
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "every node agrees: 57 nodes, 4 walks in both forms and the statements view \\(17 nodes reach statements\\)" in demo
# ---- task-0088: register-cites joins a citation to the store as register_node_statements does
def test_register_cites_joins_directory_artefacts_by_path_and_checks_a_jef_directory_citation():
    import store_neo4j as sn
    sys.path.insert(0, str(DEMO / "tools"))
    import check_saved_queries as csq
    raw = sn.REGISTER_CITES
    assert ";" not in raw and "{id:d.path}" not in raw
    listed = {q["id"]: q for q in sn.SAVED_QUERIES}["register-cites"]
    assert listed["text"] == raw and listed["needs"] == "register+scenario" and "as a file of a directory artefact" in listed["title"]
    # the artefact join is _NODE_STATEMENTS's; a directory part's digest is the file's own from part_sha256 (task-0094)
    assert "MATCH (a:Artefact) WHERE a.id = d.path OR (a.id ENDS WITH '/' AND d.path STARTS WITH a.id)" in raw
    assert "x ENDS WITH '  ' + substring(d.path, size(a.id)) | left(x, 64)" in raw and "a.id <> d.path" in raw
    assert "WHEN a.id = d.path THEN v.tag + ': ' + CASE WHEN v.sha256 = d.digest" in raw
    assert "CASE WHEN part = d.digest THEN 'same as tag' ELSE 'differs, ' + left(part, 12)" in raw
    assert "no file digest in the store" not in raw and "f.locator" not in raw
    import subject as subject_mod
    keys = subject_mod.load(ROOT / "subjects" / "jef_data_load").store_keys
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    cited = sorted({ev.split(":", 1)[1].split("#")[0] for rel in reg["relationships"].values() for ln in rel["links"]
                    if ln.get("state") == "approved" for ev in ln.get("evidence", []) if ev.startswith("jef_kit:")})
    parts = [p for p in cited if p not in keys and csq.loaded(p, keys)]
    assert "contracts/chain.md" in parts and "contracts/dmn/actions_gate.dmn" in parts and "uml/sync_run.puml" in parts, parts
    assert len(parts) == 13 and [p for p in cited if p in keys] == ["requirements.json"] and not csq.loaded("README.md", keys)
    # the check: a J-F directory citation reaches a version named by its directory and compared by the file's digest
    good = [{"document": "contracts/chain.md", "versions_in_store": ["v1: in contracts/, same as tag"]},
            {"document": "uml/sync_run.puml", "versions_in_store": ["v1: in uml/, differs, 792dc9e05c44"]},
            {"document": "requirements.json", "versions_in_store": ["v1: same as tag"]},
            {"document": "README.md", "versions_in_store": []}]
    assert csq.cites_failures(good, keys) == []
    assert csq.cites_summary(good, keys) == ("register-cites: 4 documents, 1 file artefacts, 2 files of a directory artefact, "
                                             "1 the subject does not load; 2 same as tag, 1 differ")
    bad = [{"document": "contracts/chain.md", "versions_in_store": []},
           {"document": "contracts/leg.md", "versions_in_store": ["v1: in contracts/, 31 fragments, no file digest in the store"]},
           {"document": "uml/sync_run.puml", "versions_in_store": ["v1: differs, 0123456789ab"]}]
    assert [f.split(":")[0] for f in csq.cites_failures(bad, keys)] == ["contracts/chain.md", "contracts/leg.md", "uml/sync_run.puml"]
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "-e KG_SUBJECT=/repo/subjects/jef_data_load app python demo/tools/check_saved_queries.py" in demo
    assert ("register-cites: 15 documents, 1 file artefacts, 13 files of a directory artefact, 1 the subject does not load; "
            "14 same as tag, 0 differ$") in demo


# ---- task-0077: the projection cites by the subject's own source-system prefix, never a literal kit:
def test_projection_cites_every_evidence_anchor_of_the_subjects_system():
    import register_project as rp
    ps = register_view._ps()
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    files = register_view._load_tools()["register"].load_toml(register_view.REGISTER / ps.export_manifest).get("files", {})
    want = sorted((ln["id"], ev) for rel in reg["relationships"].values() for ln in rel["links"] for ev in ln.get("evidence", [])
                  if ev.startswith(ps.sys) and rp._doc_key(ev, files, ps.sys))
    got = sorted((c["reg_id"], c["anchor"]) for c in rp.rows(loaded_at="2026-11-04T00:00:00+00:00")["cites"])
    assert want and got == want, (ps.sys, len(want), len(got))
    assert all(c["path"] in files for c in rp.rows(loaded_at="2026-11-04T00:00:00+00:00")["cites"])
    assert rp._doc_key("jef_kit:contracts/chain.md", {"contracts/chain.md": "x"}, "jef_kit:") == "contracts/chain.md"
    assert rp._doc_key("kit:contract/decision_table.md#DT-P", {"contract/decision_table.md": "x"}) == "contract/decision_table.md"
    assert 'startswith("kit:")' not in (DEMO / "app" / "register_project.py").read_text(encoding="utf-8")


def test_node_statements_are_checked_per_subject_on_both_stores():
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "python tools/check_node_statements.py --node ENT-0004 --expect 13 --total 392" in harness
    assert "KG_SUBJECT=subjects/jef_data_load KG_RDFLIB_FILE=runs/anchor-jef/store.ttl python tools/check_node_statements.py --node ENT-0009 --expect 28 --total 707" in harness
    assert "python tools/check_node_statements.py --node ENT-0004 --expect 13 --total 392" in demo
    assert "-e KG_SUBJECT=/repo/subjects/jef_data_load app python tools/check_node_statements.py --node ENT-0009 --expect 28 --total 707" in demo


# ---- task-0047: the impact panel names the owning unit of each reached node, and who to inform
def test_impact_panel_shows_the_owning_unit_from_the_registers_owner_field_on_every_node():
    import register_project as rp
    import store_neo4j as sn
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    owns = {}
    for ln in reg["relationships"]["owns"]["links"]:
        if ln["state"] == "approved":
            owns.setdefault(ln["target"], set()).add(ln["source"])
    shown = 0
    for nid in reg["nodes"]:
        w = register_view.impact(nid)
        cols = w["panel"]["sections"][0]["table"]["cols"]
        assert cols[4] == "owning unit" and cols[8] == "owner", "the node's owning unit beside its name; the link's owner where it was"
        for e, row in zip(w["edges"], w["panel"]["sections"][0]["table"]["rows"]):
            node = reg["nodes"][e["to"]]
            o = w["owners"][e["to"]]
            assert o["unit"] == node["owner"] and o["name"] == reg["nodes"][node["owner"]]["name"], e["to"]
            assert o["owns"] == sorted(owns.get(e["to"], ())) and row[4] == f"{node['owner']} {o['name']}", (e["to"], row[4])
            shown += 1
        reached = w["reached"]["all"]
        assert [i for i in w["panel"]["sections"][1]["list"] if i != "nothing"] == [
            f"{x}: {reg['nodes'][x]['name']}, owned by {reg['nodes'][x]['owner']} {reg['nodes'][reg['nodes'][x]['owner']]['name']}" for x in reached]
        inform = w["panel"]["sections"][2]
        assert inform["heading"] == "Who to inform"
        if reached:
            listed = [x for item in inform["list"] for x in item.split(": ", 1)[1].split(", ")]
            assert sorted(listed) == reached, (nid, inform["list"])
            assert all(item.startswith(reg["nodes"][item.split(": ", 1)[1].split(", ")[0]]["owner"] + " ") for item in inform["list"])
        else:
            assert inform["list"] == ["nobody: nothing is reached"]
        _check_sentences(w["text_registry"])
    assert shown == 469
    import views
    glossary = (DEMO / "GLOSSARY.md").read_text(encoding="utf-8")
    assert "| owning unit |" in glossary and views.GLOSSARY["owning unit"] in glossary and "owner field" in views.GLOSSARY["owning unit"]
    for s in _sentences(views.GLOSSARY["owning unit"]):
        assert len(s.split()) <= 25 and not _forbidden_in(s), s
    a = register_view.impact("APP-0002")
    assert a["owners"]["PRD-0002"]["unit"] == "ORG-0001" and a["owners"]["PRD-0002"]["owns"] == ["ORG-0001"], "field and owns link agree"
    assert any(i.startswith("ORG-0001 ") and "PRD-0002" in i for i in a["panel"]["sections"][2]["list"])
    # an owns link that names another unit is said beside the owning unit, and a node without an owner field says none
    fake = {"nodes": {"P": {"owner": "ORG-1"}, "ORG-1": {"name": "One"}, "Q": {}}, "relationships": {"owns": {"links": [
        {"source": "ORG-2", "target": "P", "state": "approved"}, {"source": "ORG-3", "target": "P", "state": "proposed"}]}}}
    assert register_view.owning_unit(fake, "P") == {"unit": "ORG-1", "name": "One", "owns": ["ORG-2"]}
    assert register_view.unit_text(register_view.owning_unit(fake, "P")) == "ORG-1 One (owns link: ORG-2)"
    assert register_view.unit_text(register_view.owning_unit(fake, "Q")) == "none"
    # the saved Cypher returns the same three, from the projection's owner field and its approved owns links
    for frag in ("OPTIONAL MATCH (u:RegNode {reg_id: t.owner})", "t.owner AS unit, u.name AS `unit name`",
                 "[(o:RegNode)-[w:REG_OWNS]->(t) WHERE w.state = 'approved' | o.reg_id] AS `owns links`"):
        assert frag in sn.IMPACT_ROWS and frag not in sn.IMPACT_PATHS, frag
    rows = rp.rows(loaded_at="2026-10-31T00:00:00+00:00")
    by_id = {n["reg_id"]: n for n in rows["nodes"]}
    proj_owns = {}
    for it in rows["typed"]["REG_OWNS"]:
        if it["props"]["state"] == "approved":
            proj_owns.setdefault(it["target"], set()).add(it["source"])
    assert all("state" not in o for o in rows["owners"]), "the owner field's REG_OWNS edge carries no state, so the Cypher counts owns links only"
    for nid in reg["nodes"]:
        o = register_view.owning_unit(reg, nid)
        assert (by_id[nid]["owner"], by_id.get(by_id[nid]["owner"], {}).get("name", ""), sorted(proj_owns.get(nid, ()))) == (o["unit"], o["name"], o["owns"]), nid


# ---- task-0047: beside the walk, the assertions the typed node's cited anchors name (register_node_statements, #95)
def test_impact_panel_shows_the_ports_node_statements_beside_the_walk():
    import contextlib
    import server
    calls = []

    class Fake:
        def __init__(self, census, acts):
            self.census, self.acts = census, acts
        def register_census(self):
            return self.census
        def extraction_activities(self):
            return self.acts
        def register_node_statements(self, start):
            calls.append(start)
            return [{"statement": "a:1", "status": "invalidated", "document": "contract/decision_table.md", "anchors": ["DT-P"], "links": ["REL-1"],
                     "versions": ["v1", "v2"], "fragments": ["DT-P/row/P1"], "derived": ["derived:S1:G:run1 (suspect)"]}]

    def opener(store):
        @contextlib.contextmanager
        def _open(timeout=3):
            if isinstance(store, Exception):
                raise store
            yield store
        return _open

    real = server._store
    try:
        server._store = opener(Fake({"nodes": 1}, ["act:extract:S6"]))
        w = server.impact_view("ENT-0004", statements=True)
        sec = [x for x in w["panel"]["sections"] if x["heading"] == "Assertions its cited anchors name"][0]
        assert calls == ["ENT-0004"] and w["statements"]["missing"] is None and sec["needs"] == "register+scenario"
        assert sec["table"]["cols"] == register_view.STATEMENT_COLS and sec["table"]["rows"] == [
            ["a:1", "invalidated", "contract/decision_table.md", "DT-P", "REL-1", "v1, v2", "DT-P/row/P1", "derived:S1:G:run1 (suspect)"]]
        assert "1 assertion found in the loaded scenario." in sec["text"] and "ENT-0004" in sec["text"]
        assert w["panel"]["sections"][-1]["heading"] == ("The walk in Cypher" if server._console_store() else sec["heading"])
        _check_sentences(w["text_registry"])
        for store, missing in ((Fake(None, []), "register"), (Fake({"nodes": 1}, []), "scenario"), (ImportError("no driver"), "driver"), (OSError("refused"), "store")):
            server._store = opener(store)
            w = server.impact_view("ENT-0004")
            sec = [x for x in w["panel"]["sections"] if x["heading"] == "Assertions its cited anchors name"][0]
            assert w["statements"]["missing"] == missing and w["statements"]["rows"] is None and "table" not in sec and "so no assertion is shown." in sec["text"], missing
            _check_sentences(w["text_registry"])
        assert [x["heading"] for x in server.impact_view("ENT-0004", statements=False)["panel"]["sections"]][:3] == ["Edges walked", "Reached", "Who to inform"]
        assert "Assertions its cited anchors name" not in [x["heading"] for x in server.impact_view("ENT-0004", statements=False)["panel"]["sections"]]
    finally:
        server._store = real


# ---- task-0112: the realiser walk beside the dependants walk, and the children option (decision 0014), on the page

def _starts(rows, start, children):
    """The starts the Cypher walks from: the node, and with children every approved descendant by
    parent, read off the projection's parent rows independently of the query text."""
    if not children:
        return [start]
    nodes = {n["reg_id"]: n for n in rows["nodes"]}
    kids = {}
    for r in rows["parents"]:
        kids.setdefault(r["parent"], []).append(r["child"])
    seen, stack = set(), list(kids.get(start, []))
    while stack:
        c = stack.pop()
        if c in seen or c == start:
            continue
        seen.add(c)
        stack.extend(kids.get(c, []))
    return [start] + sorted(c for c in seen if nodes[c]["state"] == "approved")


def _variant_rows(reg, start, walk, children):
    T = register_view._load_tools()
    rows_of = T["impact"].WALKS[walk]
    edges = T["impact"].walk_children(reg, start, rows_of)["edges"] if children else T["impact"].walk(reg, start, rows_of)
    return sorted((e["from"], e["rel"], e["to"], e["state"], e["owner"], tuple(e["evidence"]), e["live"]) for e in edges)


def _children_fixture():
    """_fixture's register with descendants: MOD-1 approved under APP-1, MOD-2 deprecated under APP-1
    (listed, not walked from), MOD-3 approved under MOD-2 (walked: the descent goes on at any depth)."""
    reg, rows = _fixture()
    for k, s, parent in (("MOD-2", "deprecated", "APP-1"), ("MOD-3", "approved", "MOD-2")):
        reg["nodes"][k] = {"_taxonomy": "applications", "state": s, "parent": parent}
        rows["nodes"].append({"reg_id": k, "taxonomy": "applications", "state": s, "name": k})
    reg["nodes"]["MOD-1"]["parent"] = "APP-1"
    for lid, src, tgt in (("REL-20", "MOD-1", "PROC-3"), ("REL-21", "MOD-2", "PROC-1"), ("REL-22", "MOD-3", "PROC-3")):
        reg["relationships"]["supports"]["links"].append({"id": lid, "source": src, "target": tgt, "state": "approved", "owner": "ORG-1", "evidence": [f"kit:{lid}"]})
        rows["links"].append({"reg_id": lid, "evidence": [f"kit:{lid}"]})
        rows["typed"]["REG_SUPPORTS"].append({"source": src, "target": tgt, "props": {"reg_id": lid, "state": "approved", "owner": "ORG-1"}})
    rows["parents"] = [{"child": "MOD-1", "parent": "APP-1"}, {"child": "MOD-2", "parent": "APP-1"}, {"child": "MOD-3", "parent": "MOD-2"}]
    return reg, rows


def test_every_walk_variant_in_cypher_equals_the_registers_on_every_node():
    """Each of the four (dependants or realisers, with or without children): its steps are the vendored
    walk's table, the children form's starts the node and its approved descendants, and over the
    projection's rows it gives the edges impact.walk or impact.walk_children gives, every node."""
    import register_project as rp
    import store_neo4j as sn
    T = register_view._load_tools()
    rows = rp.rows(loaded_at="2026-10-31T00:00:00+00:00")
    reg = T["register"].load_register(register_view.REGISTER)
    fx_reg, fx_rows = _children_fixture()
    totals = {}
    for walk in register_view.WALKS:
        table = T["impact"].WALKS[walk]
        for children in (False, True):
            texts = sn.impact_texts(walk, children)
            steps = _parse_walk(texts["rows"])
            assert _parse_walk(texts["paths"]) == steps and texts["paths"].rstrip().endswith("RETURN a, p")
            assert steps == {(tax, "REG_" + rel.upper(), fwd) for tax, rels in table.items() for rel, fwd in rels}
            head = sn._CHILDREN_STARTS.format(start=sn.IMPACT_START)
            assert (head in texts["rows"] and head in texts["paths"]) == children
            assert texts["rows"].count("reg_id:'") == 1 and ";" not in texts["rows"] + texts["paths"]
            for r, g in ((reg, rows), (fx_reg, fx_rows)):
                for nid in r["nodes"]:
                    got = sorted(x for s in _starts(g, nid, children) for x in _simulate(steps, g, s))
                    assert got == _variant_rows(r, nid, walk, children), (walk, children, nid)
            totals[(walk, children)] = sum(len(_variant_rows(reg, nid, walk, children)) for nid in reg["nodes"])
    assert totals[("dependants", False)] == 469 and totals[("realisers", False)] < totals[("realisers", True)]
    assert sn.impact_texts() == {"rows": sn.IMPACT_ROWS, "paths": sn.IMPACT_PATHS}, "the default walk's text is the saved query's"
    # the fixture: the deprecated module is listed, not walked from; the approved grandchild under it is walked
    fx = _variant_rows(fx_reg, "APP-1", "dependants", True)
    assert not any(r[0] == "MOD-2" for r in fx) and any(r[0] == "MOD-3" for r in fx) and any(r[0] == "MOD-1" for r in fx)
    assert _starts(fx_rows, "APP-1", True) == ["APP-1", "MOD-1", "MOD-3"]


def _subjects():
    from _subject_pin import CARGO_QUOTE
    import subject
    return [CARGO_QUOTE, subject.Subject(ROOT / "subjects" / "jef_data_load")]


def test_impact_panel_reaches_what_register_impact_reaches_on_both_walks_both_options_both_subjects():
    import page_subject
    import register_impact as ri
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    lands = {"cargo_quote": {("CAP-0001", "dependants"): 31, ("CAP-0001", "realisers"): 36},
             "jef_data_load": {("CAP-0006", "dependants"): 30, ("CAP-0006", "realisers"): 80}}
    for s in _subjects():
        with page_subject.using(s):
            for nid in reg["nodes"]:
                for walk in register_view.WALKS:
                    for children in (False, True):
                        p = register_view.impact(nid, walk, children)
                        r = ri.walk(nid, walk, children=children)
                        assert p["reached"]["all"] == r["reached_ids"] and p["edges"] == r["edges"], (s.id, nid, walk, children)
                        assert p["walk"] == walk and p["children"] is children
                        if children:
                            assert [(d["id"], d["state"], d["walked"], d["withdrawn"]) for d in p["descendants"]] == \
                                [(c["id"], c["state"], c["walked"], c["withdrawn"]) for c in r["children"]]
                            withdrawn = {d["id"] for d in p["descendants"] if d["withdrawn"]}
                            assert not withdrawn & {e["from"] for e in p["edges"]}, "a withdrawn descendant is not walked from"
                            sec = p["panel"]["sections"][0]
                            assert sec["heading"] == "Descendants by parent" and len(sec["table"]["rows"]) == len(p["descendants"])
                            assert all(row[4] == ("no, withdrawn" if row[0] in withdrawn else "yes") for row in sec["table"]["rows"])
                        else:
                            assert "descendants" not in p
            # the keys the panel's reach lands, as register_impact lands them (task-0118's counts)
            for (start, walk), n in lands[s.id].items():
                for children, want in ((False, 0), (True, n)):
                    p = register_view.impact(start, walk, children)
                    walked = [d["id"] for d in p.get("descendants", []) if d["walked"]]
                    assert len(ri.landed_rows(s.register_map(), start, p["reached"]["all"], walked)) == want, (s.id, start, walk, children)


@on_cargo_quote
def test_cap_0001_with_children_and_three_distinct_realiser_answers():
    off = register_view.impact("CAP-0001")
    assert off["edges"] == [] and "No link starts at this node" in off["panel"]["sections"][0]["text"], "the default, unchanged"
    on = register_view.impact("CAP-0001", children=True)
    assert on["reached"]["all"] == ["JRN-0001", "PRD-0002", "PROC-0001"] and on["panel"]["title"] == "Impact of retiring CAP-0001, with its descendants"
    assert [(d["id"], d["walked"]) for d in on["descendants"]] == [("CAP-0002", True), ("CAP-0003", True), ("CAP-0004", True), ("CAP-0005", False)]
    assert "CAP-0005" not in {e["from"] for e in on["edges"]} and "It also starts from every descendant by parent" in on["panel"]["intro"]
    assert [s["heading"] for s in on["panel"]["sections"]] == ["Descendants by parent", "Edges walked", "Reached", "Who to inform"]
    real = register_view.impact("CAP-0001", "realisers", True)
    assert real["reached"]["processes"] and real["reached"]["applications"] and real["panel"]["title"] == "What realises CAP-0001, with its descendants"
    # AC #1: CAP-0002/3/4 give three distinct realiser answers, as impact.py --walk realisers does
    T = register_view._load_tools()
    reg = T["register"].load_register(register_view.REGISTER)
    answers = []
    for nid in ("CAP-0002", "CAP-0003", "CAP-0004"):
        w = register_view.impact(nid, "realisers")
        assert w["reached"]["all"] == sorted(T["impact"].reached(T["impact"].walk(reg, nid, T["impact"].REALISERS)))
        assert w["reached"]["processes"] and w["panel"]["title"] == f"What realises {nid}" and "realiser walk" in w["panel"]["intro"]
        assert "application" in w["panel"]["sections"][0]["text"]
        answers.append(tuple(w["reached"]["all"]))
    assert len(set(answers)) == 3, answers
    assert register_view.impact("CAP-0001", "ancestors") is None and register_view.impact("CAP-9999", "realisers", True) is None
    for v in (on, real, register_view.impact("CAP-0002", "realisers")):
        _check_sentences(v["text_registry"])


@on_cargo_quote
def test_impact_view_serves_every_variants_cypher_guides_and_saved_queries():
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer
    import server
    import store_neo4j as sn
    sys.path.insert(0, str(ROOT / "demo" / "tools"))
    import check_impact_cypher as cic
    for variant, (walk, children) in sn.IMPACT_VARIANTS.items():
        w = server.impact_view("CAP-0001", "http://demo.test:8080", walk=walk, children=children)
        assert w["cypher"]["rows"] == sn.impact_cypher("CAP-0001", walk, children)["rows"] and "{reg_id:'CAP-0001'}" in w["cypher"]["paths"]
        mid = "" if variant == "dependants" else f"/{variant}"
        for form in server.WALK_FORMS:
            assert w["cypher"]["guide"][form] == f"/api/register/impact/CAP-0001{mid}/guide/{form}"
            assert cic.guide_url_of(w["cypher"]["browser"][form]) == "http://demo.test:8080" + w["cypher"]["guide"][form]
            assert cic.block_of(server.impact_guide("CAP-0001", form, variant)) == w["cypher"][form]
        assert w["statements"]["cypher"]["guide"] == "/api/register/impact/CAP-0001/guide/statements"
        _check_sentences(w["text_registry"])
    assert server.impact_guide("CAP-0001", "rows", "ancestors") is None and server.impact_guide("CAP-0001", "statements", "realisers") is None
    assert server.impact_view("CAP-0001", walk="ancestors") is None
    # both adapters: the rdflib store has no console, so no Cypher, and the same walk for every variant
    import os
    os.environ["KG_STORE"] = "rdflib"
    try:
        for walk, children in sn.IMPACT_VARIANTS.values():
            r = server.impact_view("CAP-0001", statements=False, walk=walk, children=children)
            assert r["cypher"] is None and r["edges"] == server.impact_view("CAP-0001", statements=False, walk=walk, children=children)["edges"]
            assert server.impact_guide("CAP-0001", "rows", f"{walk}-children" if children else walk) is None
    finally:
        del os.environ["KG_STORE"]
    for walk, children in sn.IMPACT_VARIANTS.values():
        assert server.impact_view("CAP-0001", statements=False, walk=walk, children=children)["edges"] == register_view.impact("CAP-0001", walk, children)["edges"]
    # the saved queries: each variant listed from the register's default for its start
    listed = {q["id"]: q for q in server.cypher_list()}
    for qid, start, walk, children in (("register-impact", "APP-0002", "dependants", False), ("register-impact-children", "CAP-0001", "dependants", True),
                                       ("register-realisers", "CAP-0002", "realisers", False), ("register-realisers-children", "CAP-0001", "realisers", True)):
        assert listed[qid]["text"] == sn.impact_cypher(start, walk, children)["rows"] and start in listed[qid]["title"], qid
    assert register_view.start_default("capabilities+children") == "CAP-0001"
    # over HTTP: the query string picks the walk, a bad one is refused, a variant's guide is served cross-origin
    class Quiet(server.Handler):
        def log_message(self, fmt, *args):
            pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        got = json.loads(urllib.request.urlopen(base + "/api/register/impact/CAP-0001?walk=realisers&children=1").read())
        assert got["walk"] == "realisers" and got["children"] is True and got["reached"]["all"] == register_view.impact("CAP-0001", "realisers", True)["reached"]["all"]
        assert json.loads(urllib.request.urlopen(base + "/api/register/impact/CAP-0001").read())["edges"] == []
        assert cic.block_of(cic.fetch_guide(base + got["cypher"]["guide"]["rows"])) == got["cypher"]["rows"]
        for bad in ("/api/register/impact/CAP-0001?walk=ancestors", "/api/register/impact/CAP-0001?children=maybe"):
            try:
                urllib.request.urlopen(base + bad)
            except urllib.error.HTTPError as e:
                assert e.code == 400, bad
            else:
                raise AssertionError(bad)
        for bad in ("/api/register/impact/CAP-0001/ancestors/guide/rows", "/api/register/impact/CAP-0001/dependants/guide/rows",
                    "/api/register/impact/CAP-0001/realisers/guide/statements"):
            try:
                urllib.request.urlopen(base + bad)
            except urllib.error.HTTPError as e:
                assert e.code == 404, bad
            else:
                raise AssertionError(bad)
    finally:
        httpd.shutdown()
        httpd.server_close()
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert 'id="impact-walk"' in page and 'id="impact-children"' in page and "?walk=${encodeURIComponent(walk)}&children=${children}" in page


# ---- the register's decision 0016 (v0.2.9): the start is never counted among what a walk reaches

@on_cargo_quote
def test_the_start_is_never_reached_and_an_edge_back_to_it_is_marked():
    """0016's table, measured on the page: 19 starts close a cycle of approved links back to themselves
    on the dependants walk, none on the realisers walk; each lists the edge back, marked, and never
    counts itself. The rows form's followed column marks it the same way (t = a, the CALL's start)."""
    import store_neo4j as sn
    T = register_view._load_tools()
    reg = T["register"].load_register(register_view.REGISTER)
    back = {"dependants": set(), "realisers": set()}
    for nid in reg["nodes"]:
        for walk in back:
            w = register_view.impact(nid, walk)
            assert nid not in w["reached"]["all"], (nid, walk)
            marked = [r for r in w["rows"] if r[7] == "yes, back to the start, not counted"]
            assert len(marked) == sum(1 for e in w["edges"] if e["live"] and e["to"] == nid), (nid, walk)
            if marked:
                back[walk].add(nid)
                assert all(r[2] == nid for r in marked)
    assert len(back["dependants"]) == 19 and back["realisers"] == set(), back
    assert {"JRN-0001", "PRD-0002", "PROC-0006", "PROC-0010"} <= back["dependants"]
    assert register_view.impact("JRN-0001")["reached"]["all"] == ["PRD-0002", "PROC-0001"], "0016: reaches 2, not 3"
    assert "An edge back to the start is listed and not counted" in register_view.impact("JRN-0001")["panel"]["intro"]
    for walk in ("dependants", "realisers"):
        for children in (False, True):
            assert "WHEN t = a THEN 'yes, back to the start, not counted'" in sn.impact_texts(walk, children)["rows"]

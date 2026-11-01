"""The J-F data-load subject (task-0021): its plants are the tool's output from the vendored
patches and apply exactly once; its cards keep to the glossary and the limits; its manifest's
conventions hold. Standard library only; the harness runs it in harness.yml."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBJ = ROOT / "subjects" / "jef_data_load"
DEMO = ROOT / "demo"
sys.path.insert(0, str(DEMO / "app"))
sys.path.insert(0, str(ROOT / "tools"))


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text.strip()) if s]


def test_plants_are_the_tools_output_from_the_vendored_patches():
    import tempfile
    import plants_from_patch as pfp
    patches = SUBJ / "vendor" / "recreate_experiment" / "degradation-2026-10-28" / "plant" / "patches"
    env = dict(os.environ, KG_SUBJECT=str(SUBJ))
    with tempfile.TemporaryDirectory() as td:   # a fresh checkout has no runs/
        target = Path(td) / "plants.toml"
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "plants_from_patch.py"), str(SUBJ),
                              *(f"{a}={patches / (a + '.patch')}" for a in ("D1", "D2", "D3", "D4", "D5")),
                              "-o", str(target)], env=env, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        written = target.read_text(encoding="utf-8")
    assert written == (SUBJ / "plants.toml").read_text(encoding="utf-8"), "plants.toml is not the tool's output; regenerate it"
    d = tomllib.loads(written)
    assert {k: len(v) for k, v in d["plant"].items()} == {"D1": 4, "D2": 12, "D3": 27, "D4": 10, "D5": 29}
    assert all(p["op"] == "replace" for v in d["plant"].values() for p in v)
    assert all("within" in p for v in d["plant"].values() for p in v if p["path"].endswith("/")), "a hunk on a part is confined to it"
    # the parser reads a hunk by its header's counts, so the patch's blank lines never leak into a hunk
    hunks = pfp.parse_patch((patches / "D1.patch").read_text(encoding="utf-8"))
    assert sorted(hunks) == ["MANIFEST.sha256", "uml/basis_and_adjustment.puml", "uml/series_state.puml", "uml/sync_leg.puml", "uml/sync_run.puml"]
    old, new = hunks["uml/basis_and_adjustment.puml"][0]
    assert old.endswith(":copy the raw columns into the mains;\n") and "close raw by F" in old and "close by F" in new


def test_every_plant_applies_exactly_once_and_changes_only_its_layers():
    code = """
import json, sys
sys.path.insert(0, 'harness')
from kitio import kit_for, pristine
base = pristine()
out = {}
for sc in ('D1', 'D2', 'D3', 'D4', 'D5'):
    kit = kit_for(sc)
    out[sc] = sorted(k for k in kit if kit[k] != base[k])
print(json.dumps(out))
"""
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=dict(os.environ, KG_SUBJECT=str(SUBJ)), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    changed = json.loads(r.stdout)
    assert changed == {"D1": ["uml/"], "D2": ["contracts/", "requirements.json"],
                       "D3": ["contracts/", "features/", "requirements.json", "uml/"], "D4": ["features/"],
                       "D5": ["contracts/", "contracts/dmn/", "features/", "requirements.json", "uml/"]}, changed


def test_cards_keep_to_the_glossary_and_the_limits():
    import views   # the default subject's view module: its FORBIDDEN list is the glossary's
    sc = tomllib.loads((SUBJ / "scenarios.toml").read_text(encoding="utf-8"))["scenario"]
    assert [s["id"] for s in sc] == ["C", "D1", "D2", "D3", "D4", "D5"]
    assert [s["gate"] for s in sc] == ["PROCEED", "PROCEED", "QUALIFIED", "QUALIFIED", "QUALIFIED", "QUALIFIED"]
    for s in sc:
        for field, lim in (("title", 20), ("represented", 20), ("defect", 20), ("plant", 20), ("plain", 25)):
            for sent in _sentences(s[field]):
                low = sent.lower()
                bad = [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", low)]
                assert len(sent.split()) <= lim and not bad, (s["id"], field, bad, sent)
        for text in (s["systemic"]["family"], s["systemic"]["G"]["note"], s["systemic"]["B"]["note"]):
            for sent in _sentences(text):
                assert len(sent.split()) <= 20, (s["id"], sent)
        assert s["plant"].endswith(".") and s["defect"].endswith(".") and s["represented"].endswith("."), s["id"]
        assert s["systemic"]["entry"] in ("", "updef", "deriveddef", "testdef", "codedef")


def test_manifest_conventions_and_record():
    m = tomllib.loads((SUBJ / "subject.toml").read_text(encoding="utf-8"))
    assert m["rules"]["requirement_id_pattern"] == "JDL-\\d{3}"
    assert m["verification"]["derive_execution"] == {"from_predicate": "verified_by", "key_predicate": "statement", "separator": "; "}
    assert m["oracle"]["script"] == "oracle/jef_suite.py" and len(m["oracle"]["suite_order"]) == 12
    assert m["page"]["title"].startswith("J-F") and m["page"]["reference"]["numbers"]["planted"] == 15
    for sc in ("C", "D1", "D2", "D3", "D4", "D5"):
        d = json.loads((SUBJ / "record" / sc / "deterministic.json").read_text(encoding="utf-8"))
        assert d["scenario"] == sc and d["store"] == "neo4j", "the record is the platform's own deterministic run on Neo4j"
        assert len(d["gate_keys"]) == 163
    assert (SUBJ / "record" / "SOURCE.md").exists()
    for name in ("system", "task_codegen_baseline", "task_codegen_governed"):
        assert (SUBJ / "prompts" / f"{name}.md").exists()


def test_generated_prose_on_the_subject_keeps_to_the_glossary_and_the_limits():
    """views.build for every scenario of the subject, from its record: controlled sentences at
    most 20 words, readings 25, no forbidden synonym. The subject maps its keys onto the register
    (0021.04), but the vendored register copy predates its slice, so the footprint says so rather
    than failing: the touched nodes are not in the copy and the copy carries no export of the
    subject. Run in a subprocess, since the view modules bind the subject at import."""
    code = r"""
import json, re, sys
sys.path.insert(0, 'demo/app')
import views, register_view
from pathlib import Path
def sentences(t): return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", t.strip()) if s]
limits = {"controlled": 20, "reading": 25}
seen = {"controlled": 0, "reading": 0, "data": 0}
bad = []
assert register_view.has_map() and register_view.SYS == "jef_kit:" and register_view.REQ_ID.fullmatch("JDL-047")
fp_seen = 0
for sc in views.ORDER:
    v = views.build(sc, views.default_source(sc), Path('runs') / 'nonexistent')
    assert v["gate"]["verdict"] == views.SCENARIOS[sc]["gate"], (sc, v["gate"]["verdict"])
    fp = register_view.footprint(v)
    fp_seen += 1
    lines = fp["box"]["lines"]
    assert "the register copy carries no export of this subject" in lines, (sc, lines)
    if sc != "C" and sc != "D1":
        assert any("not in the register copy" in ln for ln in lines) and fp["box"]["colour"] == "bad", (sc, lines)
    for item in fp["text_registry"]:
        if item["kind"] != "data":
            for s in sentences(item["text"]):
                low = s.lower()
                forb = [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", low)]
                if len(s.split()) > 20 or forb:
                    bad.append((sc, "footprint", forb, s))
    for item in v["text_registry"]:
        seen[item["kind"]] += 1
        if item["kind"] == "data":
            continue
        for s in sentences(item["text"]):
            low = s.lower()
            forb = [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", low)]
            if len(s.split()) > limits[item["kind"]] or forb:
                bad.append((sc, item["kind"], forb, s))
assert fp_seen == 6
print(json.dumps({"seen": seen, "bad": bad[:8], "scenarios": len(views.ORDER)}))
"""
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=dict(os.environ, KG_SUBJECT=str(SUBJ)), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["scenarios"] == 6 and out["seen"]["controlled"] > 300 and out["seen"]["data"] > 20, out["seen"]   # no arm ran: no readings yet
    assert not out["bad"], out["bad"]


def test_oracle_module_presents_the_kits_suite_in_the_harness_interface():
    """oracle/jef_suite.py imports with the standard library alone, names the twelve feature files
    as the suite's scenarios, and attributes every scenario title to its feature under pytest-bdd's
    naming (the run itself needs the pins and runs in harness.yml: 258 of 258 on the reference)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("jef_suite", SUBJ / "oracle" / "jef_suite.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = tomllib.loads((SUBJ / "subject.toml").read_text(encoding="utf-8"))
    assert mod.FEATURES == m["oracle"]["suite_order"] == sorted(mod.suite_mod.SUITE["scenarios"]) and len(mod.FEATURES) == 12
    assert mod.build_spec("seam") == {"family": "jef_data_load", "feature": "seam"} and mod.suite_mod.OVERLAYS == {}
    feat = mod._feature_of_slug()
    assert len(feat) == 130 and set(feat.values()) == set(mod.FEATURES)
    assert mod._slug("A two-split equity is stored raw (manifest.json)") == "a_twosplit_equity_is_stored_raw_manifestjson"
    assert mod.REBUILD.is_dir() and (mod.REBUILD / "deploy" / "daily.sh").exists() and (mod.REBUILD / "jdl_adapter.py").exists()
    assert mod.ADAPTER_FUNCTIONS[0] == "make_collector" and len(mod.ADAPTER_FUNCTIONS) == 10
    # the arms are on only with a key: the switch now has an oracle to grade a reply
    assert m["page"]["subtitle"].startswith("Six scenarios, a gate")
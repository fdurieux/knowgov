"""Task-0301 (decision-0034 Amendment A2): a key is compared, stored and reported in Unicode NFC, wherever it enters.

Two keys that are canonically equivalent are one key: ``soci\u00e9t\u00e9|adresse`` composed (15 characters) and
decomposed (17) read alike, and knowgov stores and reports the composed form. Not NFKC, which would merge
full-width forms and ligatures into other names. The decomposed form comes from macOS paths and clipboards, PDF
copies and some exports. Every entry point normalises; a subject copy whose document spells its names decomposed
yields the keys its manifest names composed, and the other way round. Every public key is ASCII and unchanged."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import key_rule  # noqa: E402
import mcp_server  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

NFC = "soci\u00e9t\u00e9|adresse"
NFD = unicodedata.normalize("NFD", NFC)
SOCIETE, ADRESSE, ENTREPOT = "soci\u00e9t\u00e9", "adresse", "entrep\u00f4t"
KEYS = [f"{SOCIETE}|uses:{ADRESSE}", f"{SOCIETE}|technology", f"{ENTREPOT}|technology", f"{ADRESSE}|uses:{ENTREPOT}"]


def nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


def test_normalise_is_nfc_and_two_equivalent_keys_are_one():
    assert NFD != NFC and (len(NFC), len(NFD)) == (15, 17)
    assert key_rule.normalise(NFD) == NFC == key_rule.normalise(NFC)
    assert key_rule.is_key(NFD) and key_rule.is_key(NFC)
    assert key_rule.normalise("\uff21|b") == "\uff21|b" and key_rule.normalise("\ufb01x|y") == "\ufb01x|y"   # not NFKC
    assert key_rule.normalise(7) == 7 and key_rule.normalise_all("x") == "x"
    assert "NFC" in key_rule.DESCRIPTION and "canonically equivalent" in key_rule.DESCRIPTION


def test_each_entry_point_normalises():
    """The loaders and parsers a key enters by: the mappers' Doc, the task policy, the register map, the three-valued
    keys, the verification map, code-header citations, trace's --keys, the MCP reader's key arguments and the
    upward key join."""
    import citation
    import extract
    import task_policy
    import trace
    bag = extract.Bag("doc")
    bag.ent(nfd(SOCIETE), "container")
    a = bag.assertion(nfd(SOCIETE), nfd(f"uses:{ADRESSE}"), "v", "t", [])
    assert (a["entity"], a["predicate"]) == (SOCIETE, f"uses:{ADRESSE}") and set(bag.entities) == {SOCIETE}
    assert extract.mapped_text(nfd(f"Rel({SOCIETE}, {ADRESSE}, \"x\")")) == f"Rel({SOCIETE}, {ADRESSE}, \"x\")"
    assert task_policy.build("codegen", {"keys": [NFD], "block_levels": ["absent"], "max_unverified_share": 0.25})["keys"] == [NFC]
    assert citation.parse(f"# knowgov-keys: {nfd(NFC)}, P2|surcharge\n", "#") == [NFC, "P2|surcharge"]
    assert trace._nfc(NFD) == NFC
    assert mcp_server.nfc_keys({"key": NFD, "keys": [NFD, "a|b"], "task": "x"}) == {"key": NFC, "keys": [NFC, "a|b"], "task": "x"}
    assert mcp_server.nfc_keys({"keys": "not a list"}) == {"keys": "not a list"} and mcp_server.nfc_keys([]) == []
    with tempfile.TemporaryDirectory() as d:
        root = _subject(Path(d), document_nfd=False, keys_nfd=True)
        import subject as subject_mod
        s = subject_mod.Subject(root)
        assert s.register_map()["row"][0]["key"] == KEYS[0] and s.three_valued == [KEYS[1]]
        assert s.verification_map()["review"]["keys"] == [KEYS[0]]


def _subject(root: Path, *, document_nfd: bool, keys_nfd: bool) -> Path:
    """A subject copy: one C4 document whose aliases are French names, its task keys, register map, three-valued
    keys and verification map spelled in the other form (or the same) as asked."""
    doc = "\n".join(["@startuml", f"Container({SOCIETE}, \"Soci\u00e9t\u00e9\", \"Python\")",
                     f"ContainerDb({ADRESSE}, \"Adresse\", \"PostgreSQL\")", f"Container({ENTREPOT}, \"Entrep\u00f4t\", \"Go\")",
                     f"Rel({SOCIETE}, {ADRESSE}, \"lit l'adresse\")", f"Rel({ADRESSE}, {ENTREPOT}, \"exp\u00e9die\")", "@enduml", ""])
    k = (lambda x: nfd(x)) if keys_nfd else (lambda x: x)
    (root / "containers.puml").write_text(nfd(doc) if document_nfd else doc, encoding="utf-8")
    keys = ", ".join(json.dumps(k(x), ensure_ascii=False) for x in KEYS)
    (root / "subject.toml").write_text(f"""[format]
version = 1

[subject]
id = "nfc_probe"
name = "NFC probe"
listed = false
description = "task-0301: French names spelled composed and decomposed."

[[artefact]]
key = "structure/containers.puml"
short = "c4"
family = "structure"
format = "c4-plantuml"
label = "structure"
format_label = "C4 PlantUML"
path = "containers.puml"
mapper = "containers"

[tasks.codegen]
keys = [{keys}]
block_levels = ["absent", "declared_gap", "disputed", "invalidated"]
max_unverified_share = 1.0

[three_valued]
keys = [{json.dumps(k(KEYS[1]), ensure_ascii=False)}]

[verification]
map = "verification_map.toml"

[register]
map = "register_map.toml"

[record]
as_of = 2026-11-04
""", encoding="utf-8")
    (root / "verification_map.toml").write_text(f"""[review]
keys = [{json.dumps(k(KEYS[0]), ensure_ascii=False)}]
""", encoding="utf-8")
    (root / "register_map.toml").write_text(f"""[[row]]
key = {json.dumps(k(KEYS[0]), ensure_ascii=False)}
nodes = ["CAP-0002"]
""", encoding="utf-8")
    (root / "scenarios.toml").write_text("""[[scenario]]
id = "S0"
title = "the C4 document as written"
represented = "One C4 document."
gate = "QUALIFIED"
defect = "None."
plant = "Nothing was planted."
plain = "The document names French containers."
extraction = "pristine"
""", encoding="utf-8")
    return root


def _env(**kw) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
    return {**env, "KG_CLOCK": "pinned", "KG_TODAY": "2026-11-04", **kw}


def test_check_subject_reads_a_decomposed_document_against_composed_keys_and_back():
    """check_subject's yield: the keys a decomposed document yields are the manifest's composed keys, and a
    manifest spelled decomposed matches a composed document; no key reads unyielded either way."""
    for document_nfd, keys_nfd in ((True, False), (False, True), (True, True)):
        with tempfile.TemporaryDirectory() as d:
            root = _subject(Path(d), document_nfd=document_nfd, keys_nfd=keys_nfd)
            p = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root), "--json"],
                               capture_output=True, text=True, env=_env(), cwd=ROOT, timeout=300)
            rep = json.loads(p.stdout)
            said = [f for f in rep["findings"] + rep.get("notes", []) if f["rule"] in ("yield", "unyielded", "key-syntax")]
            assert said == [], (document_nfd, keys_nfd, said)
            assert rep["yield"]["state"] == "checked" and rep["yield"]["keys"] >= len(KEYS), rep["yield"]


def _gate(root: Path, store: Path, extra=()) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--subject", str(root), "--scenario", "S0",
                        "--as-of", "2026-11-04", "--publish", "-f", "json", *extra], capture_output=True, text=True,
                       env=_env(KG_STORE="rdflib", KG_RDFLIB_FILE=str(store), KG_SUBJECT=str(root)), cwd=ROOT, timeout=300)
    assert p.returncode in (0, 1), p.stderr[-800:]
    return json.loads(p.stdout)


def test_the_gate_and_the_mcp_reader_read_one_key_whichever_form_enters():
    """A decomposed document under composed task keys, and the reverse: the gate reads every key present, never
    absent, and reports it composed; over MCP, gate_verdict, three_valued_answer, evidence_bundle and key_nodes
    asked with the decomposed key answer for the composed one."""
    need_rdflib()
    for document_nfd, keys_nfd in ((True, False), (False, True)):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s").mkdir()
            root = _subject(Path(d) / "s", document_nfd=document_nfd, keys_nfd=keys_nfd)
            store = Path(d) / "store.ttl"
            rep = _gate(root, store)
            assert set(rep["levels"]) == set(KEYS), (document_nfd, keys_nfd, sorted(rep["levels"]))
            assert all(lv != "absent" for lv in rep["levels"].values()), rep["levels"]
            calls = [("gate_verdict", {"keys": [nfd(KEYS[0])], "as_of": "2026-11-04"}),
                     ("three_valued_answer", {"key": nfd(KEYS[0])}),
                     ("evidence_bundle", {"keys": [nfd(KEYS[0])], "verbatim": False, "as_of": "2026-11-04"}),
                     ("key_nodes", {"key": nfd(KEYS[0])})]
            lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})]
            lines += [json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": n, "arguments": a}})
                      for i, (n, a) in enumerate(calls, 1)]
            p = subprocess.run([sys.executable, str(ROOT / "harness" / "mcp_server.py"), "--as-of", "2026-11-04"],
                               input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=300,
                               env=_env(KG_STORE="rdflib", KG_RDFLIB_FILE=str(store), KG_SUBJECT=str(root)), cwd=ROOT)
            got = {r["id"]: r for r in map(json.loads, p.stdout.splitlines())}
            for i, (name, _) in enumerate(calls, 1):
                res = got[i].get("result") or {}
                assert res.get("isError") is False, (name, got[i])
            sc = {i: got[i]["result"]["structuredContent"] for i in got if i}
            assert sc[1]["levels"] == {KEYS[0]: rep["levels"][KEYS[0]]}, sc[1]["levels"]
            assert sc[2]["key"] == KEYS[0] and sc[2]["answer"] == "asserted", sc[2]
            assert any((":" + KEYS[0] + "@") in i for i in sc[3]["assertion_ids"]), sc[3]["assertion_ids"]
            assert sc[4]["key"] == KEYS[0] and sc[4]["mapped"] is True, sc[4]


def test_every_public_key_is_ascii_and_so_unchanged():
    import glob
    import tomllib
    seen = 0
    for st in glob.glob(str(ROOT / "subjects" / "*" / "subject.toml")):
        for spec in tomllib.loads(Path(st).read_text(encoding="utf-8")).get("tasks", {}).values():
            for k in spec.get("keys", []):
                assert k.isascii() and key_rule.normalise(k) == k, k
                seen += 1
    assert seen > 200


def test_the_docs_and_the_changelog_say_so():
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    assert "git config core.precomposeunicode true" in readme and "NFC" in readme
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0301" in contract and "NFC" in contract


def test_a_capture_answers_a_decomposed_key_as_the_composed_one():
    """An answered questionnaire whose editor saved the key decomposed answers the task's composed key, and the
    capture written holds it composed."""
    import datetime as dt
    import capture
    doc = {"questionnaire": {"subject": "nfc_probe", "task": "codegen"}, "answered": {"from": "H-0001", "on": "2026-11-04"},
           "item": [{"key": nfd(NFC), "answer": "rue de la Paix"}]}
    errs, cap = capture.check_answers(doc, r"^H-\d{4}$", {NFC}, dt.date(2026, 11, 4))
    assert errs == [] and cap["answers"][0]["key"] == NFC, (errs, cap)
    assert nfd(NFC) not in capture.capture_toml(cap, "t") and NFC in capture.capture_toml(cap, "t")

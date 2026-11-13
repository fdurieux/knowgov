"""Task-0221, decision-0019: an attestation is bound to the Versions it attests. tools/check_attestation_binding.py
holds it end to end on the example instance; it runs here on rdflib, and in CI on rdflib (harness.yml) and on Neo4j
(demo.yml's stack job). The unit tests below need no store."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

TOOL = "tools/check_attestation_binding.py"


def _rows(bound, unattested):
    return [{"declaration": "authored", "bound": bound, "attester": "agent:maintainer", "unattested": unattested}]


def test_a_declaration_without_versions_is_the_read_rule_at_info():
    import gate_cli
    [f] = gate_cli.attestation_findings(_rows(False, []), None, None)
    assert f["severity"] == "info" and f["kind"] == "attestation" and "decision-0019" in f["message"] and f["ref"] == "attest:authored"


def test_an_unattested_version_behind_keys_is_major_and_names_the_owner_and_the_listing():
    import gate_cli
    u = [{"artefact": "contract/t.md", "sha256": "a" * 64, "parts": [], "keys": ["k|a", "k|b"]}]
    owners = {"k|a": {"unit": "ORG-1", "files": ["ORG-1"]}, "k|b": {"unit": "ORG-1", "files": ["ORG-1"]}}
    [f] = gate_cli.attestation_findings(_rows(True, u), owners, lambda unit, key: f"questionnaire for {unit}")
    assert f["severity"] == "major" and f["ref"] == "contract/t.md" and f["related"] == ["k|a", "k|b"] and f["owner"] == "ORG-1"
    assert "a" * 64 in f["route"] and "decision-0019" in f["route"] and "questionnaire for ORG-1" in f["route"]


def test_a_bound_declaration_attesting_everything_says_nothing():
    import gate_cli
    assert gate_cli.attestation_findings(_rows(True, []), {}, None) == []


def test_the_load_attests_only_the_listed_versions_and_none_without_a_list_reads_every_one():
    src = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_verifications")
    body = ast.get_source_segment(src, fn)
    assert "attested_artefacts(" in body and "st.record_attestation(" in body
    for name in ("store_rdflib.py", "store_neo4j.py"):
        a = (ROOT / "harness" / name).read_text(encoding="utf-8")
        assert "def verify_authored(self, at, scope, agent_id, artefacts=None)" in a
        assert "def approve_verified(self, at, record, agent_id, artefacts=None)" in a
        assert "def record_attestation(self, row)" in a and "def attestations(self)" in a, name


def test_check_subject_reads_the_lists_from_the_files_alone():
    import check_subject
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "doc.md").write_text("one\n", encoding="utf-8")
        (root / "plants.toml").write_text('[[plant.S2]]\npath = "doc"\nop = "replace"\nold = "one"\nnew = "two"\n', encoding="utf-8")
        m = {"artefact": [{"key": "doc", "path": "doc.md"}]}
        import hashlib
        got = check_subject.subject_versions(m, root)
        assert hashlib.sha256(b"one\n").hexdigest() in got and hashlib.sha256(b"two\n").hexdigest() in got


def test_the_check_holds_on_rdflib():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "KG_STORE": "rdflib", "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("KG_RDFLIB_FILE", None)
        p = subprocess.run([sys.executable, str(ROOT / TOOL), str(Path(td) / "out")], env=env, cwd=ROOT,
                           capture_output=True, text=True, timeout=1500)
        assert p.returncode == 0 and "every check holds" in p.stdout, p.stdout[-3000:] + p.stderr[-1500:]


def test_ci_runs_it_on_both_stores():
    assert f"KG_STORE=rdflib python {TOOL} runs/attestation-binding" in (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f"python {TOOL} runs/attestation-binding" in (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")


def test_stage_two_takes_back_the_construction_acts_of_an_unlisted_version():
    """decision-0019: "An unlisted Version is not attested: its authored statements read proposed, and nothing in it is
    approved by construction" -- the unchanged statements of a changed Version too (the coordinator's (a), 2026-11-08)."""
    src = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    assert "st.withdraw_construction(unlisted)" in src and "r_corroborate(st)" in src
    for name in ("store_rdflib.py", "store_neo4j.py"):
        a = (ROOT / "harness" / name).read_text(encoding="utf-8")
        body = a[a.index("def withdraw_construction(self, artefacts)"):][:1500]
        assert "ver:review:" in body and "appr:" in body, name
    import store
    assert "withdraw_construction" not in store.READS


def test_a_directory_whose_every_file_changed_and_a_plant_of_a_re_attested_document_are_named_task_0312():
    """Reviewer A's F1 (a directory fully changed is named once a stale digest exists, as a file is) and F2 (a plant's
    Version of a re-attested document is named with the digest to list)."""
    import hashlib
    import check_subject
    h = lambda t: hashlib.sha256(t.encode()).hexdigest()  # noqa: E731
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "uml").mkdir()
        (root / "uml" / "a.puml").write_text("a2\n", encoding="utf-8")
        (root / "doc.md").write_text("one\n", encoding="utf-8")
        (root / "plants.toml").write_text('[[plant.S2]]\npath = "doc"\nop = "replace"\nold = "one"\nnew = "two"\n', encoding="utf-8")
        m = {"artefact": [{"key": "uml", "path": "uml"}, {"key": "doc", "path": "doc.md"}]}
        # F1: the one file of the directory changed; an old digest is listed, so the directory is named
        rep = check_subject.Report(root)
        assert check_subject._changed_artefacts(rep, m, root, "[verification] approval", [h("a1\n"), h("one\n")], True)
        assert [f for f in rep.findings if f["message"].startswith("uml changed since it was attested")], rep.findings
        # F2: doc.md is listed as it is now, its plant's Version is not
        rep = check_subject.Report(root)
        check_subject._unlisted_plants(rep, m, root, "[verification] approval", [h("a2\n"), h("one\n")], "approval")
        [f] = rep.findings
        assert "a scenario plant of doc" in f["message"] and h("two\n") in f["message"] and h("two\n") in f["fix"], f
        rep = check_subject.Report(root)
        check_subject._unlisted_plants(rep, m, root, "[verification] approval", [h("a2\n"), h("one\n"), h("two\n")], "approval")
        assert rep.findings == []


def test_the_plants_artefact_is_the_exact_key_then_the_longest_prefix_task_0312_r3():
    import hashlib
    import check_subject
    h = lambda t: hashlib.sha256(t.encode()).hexdigest()  # noqa: E731
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "doc.md").write_text("one\n", encoding="utf-8")
        (root / "doc2.md").write_text("uno\n", encoding="utf-8")
        (root / "plants.toml").write_text('[[plant.S2]]\npath = "doc2"\nop = "replace"\nold = "uno"\nnew = "dos"\n', encoding="utf-8")
        m = {"artefact": [{"key": "doc", "path": "doc.md"}, {"key": "doc2", "path": "doc2.md"}]}
        # doc is listed, doc2 is too: the plant of doc2 is the gap, and it is doc2's, not doc's
        assert check_subject._plant_gaps(m, root, [h("one\n"), h("uno\n")]) == [("doc2", h("dos\n"))]
        # nested keys: contracts/ and contracts/dmn/ (directories), the plant on the deeper one
        (root / "c" / "dmn").mkdir(parents=True)
        (root / "c" / "a.md").write_text("a\n", encoding="utf-8")
        (root / "c" / "dmn" / "b.md").write_text("b\n", encoding="utf-8")
        (root / "plants.toml").write_text('[[plant.S2]]\npath = "c/dmn/"\nwithin = "b.md"\nop = "replace"\nold = "b"\nnew = "x"\n', encoding="utf-8")
        m = {"artefact": [{"key": "c/", "path": "c", "include": ["a.md"]}, {"key": "c/dmn/", "path": "c/dmn"}]}
        got = check_subject._plant_gaps(m, root, [h("a\n"), h("b\n")])
        assert [a for a, _ in got] == ["c/dmn/"], got


def test_wholly_unlisted_artefacts_are_named_only_when_the_stale_digests_cover_them_all_task_0312_r4_l1():
    import hashlib
    import check_subject
    h = lambda t: hashlib.sha256(t.encode()).hexdigest()  # noqa: E731
    for uml in ("a_uml", "z_uml"):   # the answer must not depend on the order of the keys
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "doc.md").write_text("new\n", encoding="utf-8")
            (root / "never").mkdir()
            (root / "never" / "x.puml").write_text("never attested\n", encoding="utf-8")
            m = {"artefact": [{"key": uml, "path": "never"}, {"key": "doc", "path": "doc.md"}]}
            listed = [h("old\n")]
            # one stale digest cannot account for the edited doc and the never-attested directory: none is named, and
            # the per-digest error is left to say what is stale
            rep = check_subject.Report(root)
            assert not check_subject._changed_artefacts(rep, m, root, "[verification] approval", listed, 1) and rep.findings == []
            rep = check_subject.Report(root)
            check_subject._check_versions(rep, m, root, "approval", listed, [None])
            assert [f["message"].split(" ")[0] for f in rep.findings] == ["versions"], (uml, rep.findings)
            # the directory attested, the doc edited: one stale digest, one artefact named
            rep = check_subject.Report(root)
            assert check_subject._changed_artefacts(rep, m, root, "[verification] approval", [h("never attested\n"), h("old\n")], 1)
            assert [f["message"].split(" ")[0] for f in rep.findings] == ["doc"], (uml, rep.findings)
            rep = check_subject.Report(root)
            assert not check_subject._changed_artefacts(rep, m, root, "[verification] approval", [h("new\n"), h("never attested\n")], 0)


def test_a_stale_digest_says_it_may_have_been_a_plants_version_task_0312_r6():
    import hashlib
    import check_subject
    h = lambda t: hashlib.sha256(t.encode()).hexdigest()  # noqa: E731
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "doc.md").write_text("one\n", encoding="utf-8")
        (root / "plants.toml").write_text('[[plant.S2]]\npath = "doc"\nop = "replace"\nold = "one"\nnew = "two"\n', encoding="utf-8")
        m = {"artefact": [{"key": "doc", "path": "doc.md"}]}
        hint = check_subject._plant_hint(m, root, [h("one\n"), h("old plant\n")], ["x"])
        assert "scenario plant's Version of doc" in hint and h("two\n") in hint
        assert check_subject._plant_hint(m, root, [h("one\n"), h("two\n")], ["x"]) == "" and check_subject._plant_hint(m, root, [h("one\n")], []) == ""

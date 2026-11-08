"""Route (c), task-0041: a transcript read by a model gives candidates, never knowledge. The store
half, on the example instance with a stub model, is tools/check_transcript_route.py: harness.yml
runs it on rdflib, the stack job on Neo4j."""
from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import transcript  # noqa: E402

KEYS = ["response|hold_presence", "QuoteAPI|on_screening_outage"]


def test_only_the_keys_asked_about_with_a_value_are_kept():
    asked = []

    def stub(system, user):
        asked.append((system, user))
        return {"proposals": [{"key": KEYS[0], "value": " held_unscreened only "}, {"key": KEYS[0], "value": "again"},
                              {"key": "response|statuses", "value": "x"}, {"key": KEYS[1], "value": ""},
                              {"key": KEYS[1], "value": "y" * 301}, "junk"]}
    out = transcript.propose("A: only for held_unscreened.", KEYS, stub)
    assert out == [{"key": KEYS[0], "value": "held_unscreened only"}], out
    assert "never guess" in asked[0][0] and "never name anyone" in asked[0][0] and "- QuoteAPI|on_screening_outage" in asked[0][1]
    assert transcript.propose("text", [], stub) == [] and len(asked) == 1, "no empty key, no call"
    assert transcript.propose("text", KEYS, lambda s, u: None) == []


def test_only_empty_keys_are_proposed_so_a_guess_never_lowers_what_the_documents_state():
    res = {"keys": {"a|b": {"level": "absent"}, "c|d": {"level": "declared_gap"}, "e|f": {"level": "validated"},
                    "g|h": {"level": "proposed"}, "i|j": {"level": "disputed"}}}
    assert transcript.open_keys(res) == ["a|b", "c|d"]


def test_the_file_keeps_the_digest_and_never_the_transcript():
    meta = {"subject": "cargo_quote", "scenario": "S2", "task": "codegen", "model": "m", "host": "h",
            "transcript_sha256": "ab" * 32, "on": "2026-11-03"}
    doc = tomllib.loads(transcript.proposals_toml(meta, [{"key": KEYS[0], "value": 'say "x"'}]))
    assert doc["inference"]["transcript_sha256"] == "ab" * 32 and doc["proposal"] == [{"key": KEYS[0], "value": 'say "x"'}]
    assert set(doc["inference"]) == set(meta), "no field for the transcript's text"


def test_with_no_model_key_it_refuses_with_exit_2():
    env = dict(os.environ, KG_MODEL_API_KEY_VAR="KG_TRANSCRIPT_TEST_NO_KEY", PYTHONDONTWRITEBYTECODE="1")
    env.pop("KG_TRANSCRIPT_TEST_NO_KEY", None)
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "transcript.py"), str(ROOT / "README.md")], env=env,
                       capture_output=True, text=True)
    assert p.returncode == 2 and "no model key" in p.stderr, (p.returncode, p.stderr)


def test_both_adapters_take_a_candidate_for_nothing_and_ci_runs_the_route():
    rdf = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    neo = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    assert "if candidate_for:" in rdf and "WITH x WHERE $gid IS NOT NULL" in neo
    for wf in ("harness.yml", "demo.yml"):
        assert "tools/check_transcript_route.py" in (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8"), wf


def test_the_file_records_the_model_that_answered_not_the_one_configured():
    """task-0207, doc-0030 R12: route (c) records the model the endpoint answered with, the usage's model
    from the stream (a gateway or an alias can differ from KG_ARMS_MODEL), through the arms' own call,
    stubbed here: no model is called. On CargoQuote's S2, the scenario route (c) is proven on, rdflib."""
    import argparse
    import re
    import tempfile
    from tests._skip import need_rdflib, skip
    need_rdflib()
    import arms
    from subject import SUBJECT
    if SUBJECT.id != "cargo_quote":
        skip("cargo-quote-subject", "route (c)'s scenario S2 is CargoQuote's; this pass runs another subject")
    names = ("KG_STORE", "KG_TODAY", "KG_MODEL_API_KEY_VAR", "KG_TRANSCRIPT_R12_KEY", "KG_ARMS_MODEL")
    keep, keep_call = {k: os.environ.get(k) for k in names}, arms.call
    os.environ.update(KG_STORE="rdflib", KG_TODAY="2026-11-08", KG_MODEL_API_KEY_VAR="KG_TRANSCRIPT_R12_KEY",
                      KG_TRANSCRIPT_R12_KEY="not-a-key", KG_ARMS_MODEL="configured-alias")

    def stub(system, user, *, tag):
        key = re.findall(r"^- (\S+)$", user, re.M)[0]
        return {"raw": "", "parsed": {"proposals": [{"key": key, "value": "only when held"}]}, "parse_error": None,
                "usage": {"model": "answered-model-2026-11-01"}}
    arms.call = stub
    try:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t.txt"
            t.write_text("A: only when held.", encoding="utf-8")
            assert transcript.run(argparse.Namespace(transcript=t, scenario="S2", task="codegen", into=Path(td) / "out")) == 0
            (out,) = (Path(td) / "out").glob("*.toml")
            meta = tomllib.loads(out.read_text(encoding="utf-8"))["inference"]
        assert meta["model"] == "answered-model-2026-11-01", meta
    finally:
        arms.call = keep_call
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

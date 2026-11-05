"""task-0139 (doc-0019 C1): route (c) over a document, measured against the withheld mapper. The pure
half here (forms, prompt, filter, score, bar); the measured run is the maintainer's, with a model key,
and its outputs stay outside the repository."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]
import route_c_documents as rc  # noqa: E402


def eq(a, b, pred=""):
    return "equal" if a == b else "conflict"


def test_the_prompt_states_the_language_it_reads_and_forbids_filling_or_resolving():
    s = rc.SYSTEM.format(language="English")
    assert "written in English; read it as English" in s
    assert "never guess" in s and "open, not yet specified or undecided" in s and "give its words as written" in s
    assert rc.LANGUAGE == "English"
    u = rc.user_prompt("a.md", "one\ntwo", ["x|max", "y|text"], {"max": "a number as written, without unit"})
    assert "- x|max: a number as written, without unit" in u and "- y|text: the document's words" in u
    assert "    2| two" in u


def test_forms_name_shapes_and_never_values():
    f = rc.forms({"max": ["41", "19400"], "behaviour": ["priced=no;status=x", "priced=yes;hold=true"],
                  "priced": ["yes", "NONE"], "text": ["anything at all"]})
    assert f["max"] == "a number as written, without unit"
    assert f["behaviour"] == "name=value pairs joined by ';', names among: hold, priced, status"
    assert f["priced"] == "the document's words; NONE where the document states there is none"
    assert "anything" not in " ".join(f.values()) and "41" not in " ".join(f.values())


def test_only_asked_keys_with_a_value_are_kept_once():
    parsed = {"proposals": [{"key": "a|b", "value": " 1 ", "line": 3}, {"key": "a|b", "value": "2"},
                            {"key": "z|z", "value": "x"}, {"key": "c|d", "value": ""}, "junk",
                            {"key": "c|d", "value": "y" * (rc.MAX_VALUE + 1)}]}
    assert rc.parse_proposals(parsed, ["a|b", "c|d"]) == [{"key": "a|b", "value": "1", "line": 3}]
    assert rc.parse_proposals(None, ["a|b"]) == []


def test_score_splits_matches_wrong_and_inventions_and_counts_fills_and_silent_resolutions():
    truth = {"S-accept|max": [{"value": "below the low forties", "raw_value": None, "vague": True}],
             "P2|surcharge": [{"value": "316.00", "raw_value": None, "vague": False}],
             "S-review|min": [{"value": "42", "raw_value": "REVIEW_MIN", "vague": False}]}
    props = [{"key": "P2|surcharge", "value": "316.00"}, {"key": "S-review|min", "value": "REVIEW_MIN"},
             {"key": "S-accept|max", "value": "40"}, {"key": "outage|behaviour", "value": "priced=no"}]
    s = rc.score(props, truth, eq, declared={"outage|behaviour"}, vague_keys={"S-accept|max"}, vague_words=["low forties"])
    assert [r["verdict"] for r in s["proposals"]] == ["match", "match", "wrong", "invention"]
    assert (s["proposed"], s["matches"], s["wrong"], s["inventions"]) == (4, 2, 1, 1)
    assert s["precision"] == 0.5 and s["recall"] == round(2 / 3, 4)
    assert s["fills"] == 1 and s["silent_resolutions"] == 1
    kept = rc.score([{"key": "S-accept|max", "value": "below the low forties"}], truth, eq,
                    vague_keys={"S-accept|max"}, vague_words=["low forties"])
    assert kept["silent_resolutions"] == 0 and kept["matches"] == 1
    none = rc.score([], truth, eq)
    assert none["precision"] is None and none["recall"] == 0.0


def test_the_bar_is_the_one_recorded_before_the_run():
    ok = {"proposed": 10, "matches": 9, "precision": 0.9, "fills": 0, "silent_resolutions": 0}
    pooled = {"S1/single": ok, "S1/all": {**ok, "precision": 0.5}, "S2/single": ok, "S2/all": ok, "S3/all": ok}
    assert rc.bar(pooled)["met"] is True, "S1's precision is read on single; all is reported beside it"
    assert rc.bar({**pooled, "S2/all": {**ok, "fills": 1}})["met"] is False
    assert rc.bar({**pooled, "S3/all": {**ok, "silent_resolutions": 1}})["met"] is False
    assert rc.bar({**pooled, "S1/single": {**ok, "precision": 0.89}})["met"] is False
    assert rc.bar({"S1/single": ok})["met"] is False, "a check not measured is not met"


def test_pool_totals_precision_over_proposals_and_recall_over_stated_keys():
    a = {"proposed": 4, "matches": 2, "wrong": 1, "inventions": 1, "asked_stated": 3, "recall": round(2 / 3, 4),
         "fills": 0, "silent_resolutions": 1}
    b = {"proposed": 0, "matches": 0, "wrong": 0, "inventions": 0, "asked_stated": 2, "recall": 0.0,
         "fills": 0, "silent_resolutions": 0}
    p = rc.pool([a, b])
    assert (p["precision"], p["recall"], p["silent_resolutions"]) == (0.5, 0.4, 1)


def test_it_refuses_without_a_key_and_keeps_its_outputs_outside_the_repository():
    env = dict(os.environ, KG_MODEL_API_KEY_VAR="KG_ROUTE_C_TEST_NO_KEY", PYTHONDONTWRITEBYTECODE="1",
               KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"))
    env.pop("KG_ROUTE_C_TEST_NO_KEY", None)
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "route_c_documents.py"), "--on", "2026-11-05",
                        "--scenarios", "S1", "--out", "/nonexistent-route-c"], env=env, capture_output=True, text=True)
    assert p.returncode == 2 and "no model key" in p.stderr, (p.returncode, p.stderr)
    keep = {k: os.environ.get(k) for k in ("KG_SUBJECT", "KG_TODAY", "KG_CLOCK", "KG_STORE")}
    os.environ["KG_SUBJECT"] = str(ROOT / "subjects" / "cargo_quote")
    try:
        args = argparse.Namespace(on="2026-11-05", scenarios=["S1"], tasks=["codegen"], modes=["single"],
                                  language="English", workers=1, out=ROOT / "runs" / "route-c")
        try:
            rc.run(args, call=lambda s, u: {})
            raise AssertionError("an output folder inside the repository was accepted")
        except rc.CannotRun as e:
            assert "outside the repository" in str(e)
        assert not (ROOT / "runs" / "route-c").exists()
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def test_nothing_is_ingested_or_written_into_a_capture_folder():
    text = (ROOT / "tools" / "route_c_documents.py").read_text(encoding="utf-8")
    assert "capture_dir" not in text and "inferred/" not in text.replace("``inferred``/``proposed``", "")
    assert 'os.environ.pop("KG_RDFLIB_FILE", None)' in text and "from rules import VAGUE, compatible" in text
    assert "review.pinned(" in text, "the run's date is --on; the loads read no clock (task-0075)"


def test_a_failed_call_is_reported_and_never_scored():
    text = (ROOT / "tools" / "route_c_documents.py").read_text(encoding="utf-8")
    assert '"error": f"{type(e).__name__}' in text and 'if r.get("error"):\n            continue' in text
    assert '"errors": [{**_head(r), "error": r["error"]} for r in results if r.get("error")]' in text


def test_none_is_no_symbol_as_the_load_reads_it():
    import re
    sym = re.compile(r"^[A-Z][A-Z_]+$")   # load.SYMBOL_RE
    assert rc._symbol("ACCEPT_MAX", sym) and not rc._symbol("NONE", sym) and not rc._symbol("41", sym)
    assert rc._parse('{"proposals": []}') == {"proposals": []} and rc._parse("not json") is None and rc._parse(None) is None

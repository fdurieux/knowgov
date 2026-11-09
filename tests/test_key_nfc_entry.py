"""Task-0309 (the re-check of task-0301): NFC at the remaining entry points. B1 a baseline's level keys, B2 a ruling's
assertion id, B3 the published pattern against what was sent, B4 a task class's keys equal after NFC. Stdlib only."""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(ROOT)]
import key_rule  # noqa: E402
from tests._skip import skip  # noqa: E402

NFC = "société|adresse"
NFD = unicodedata.normalize("NFD", NFC)


def test_b1_a_baseline_with_decomposed_level_keys_still_regresses():
    import gate_cli
    for data in ({"tool": "knowgov gate", "verdict": "PROCEED", "levels": {NFD: "approved"}},
                 {"D6_gate": {"verdict": "PROCEED"}, "gate_keys": {NFD: {"level": "approved"}}}):
        base = gate_cli.baseline_of(data)
        assert list(base["levels"]) == [NFC], base
        res = {"verdict": "PROCEED", "keys": {NFC: {"level": "proposed"}}, "suspect_derived": []}
        assert [r["key"] for r in gate_cli.compare(res, base, "f")["regressed_keys"]] == [NFC]
    held = [{"kind": "key", "key": NFC, "severity": "blocker"}]
    gate_cli.mark_held(held, {"regressed_keys": [{"key": NFD}]})
    assert held[0]["held"] is False


def test_b2_a_decomposed_assertion_id_binds_as_the_composed_one():
    import review
    from tests.test_act_binding import Store, _row
    key = NFC
    aid = f"A:dt:{key}@v1"
    row = _row(aid, "41", "t", key=key)
    ru = {"assertion": unicodedata.normalize("NFD", aid), "key": key, "value": "41", "sha256": review.content_digest(row["fragments"])}
    b, how = review.bind(Store([row]), ru)
    assert b is not None and how["why"] == "content", (b, how)
    old = {"assertion": unicodedata.normalize("NFD", aid), "outcome": "approved"}
    b, how = review.bind(Store([row]), old)
    assert b is not None and how["why"] == "unbound", (b, how)


def test_b3_the_published_pattern_holds_of_what_was_sent():
    import mcp_server
    schema = {"type": "object", "properties": {"key": {"type": "string", "pattern": key_rule.PATTERN}}, "required": ["key"],
              "additionalProperties": False}
    compat = "𤋮|x"   # BMP raw, astral in NFC
    astral = "\U0002f800|x"   # astral raw, a BMP ideograph in NFC
    for sent in (compat, astral):
        msg = mcp_server.sent_refusal("t", {"key": sent}, schema)
        assert msg and repr(sent) in msg, (sent, msg)
    assert mcp_server.sent_refusal("t", {"key": NFD}, schema) is None and mcp_server.sent_refusal("t", {"key": NFC}, schema) is None


def test_b4_check_subject_warns_on_a_task_key_listed_twice_after_nfc():
    import tempfile
    import check_subject
    for keys in ([NFC, NFC], [NFC, NFD]):
        m = {"tasks": {"t": {"keys": keys, "block_levels": ["proposed"], "max_unverified_share": 1.0}}}
        with tempfile.TemporaryDirectory() as d:
            rep = check_subject.Report(Path(d))
            check_subject.check_manifest(rep, m, Path(d), set())
        assert any(f["rule"] == "duplicate" and f["level"] == "warning" for f in rep.findings), (keys, rep.findings)

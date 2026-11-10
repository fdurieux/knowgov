"""Task-0316 (decision-0034): the one key rule holds at every entry, raw and in NFC, naming the value as written.

N8: a task class's keys by ``task_policy.build`` (TaskPolicyError, exit 2 under the gate contract) and by
check_subject (``key-syntax``), plus a ``duplicate`` warning on ``[three_valued] keys`` equal after NFC.
N9: ``trace.read_ledger`` reports a ledger entry's keys and statement ids in NFC."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import key_rule  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402
from tests.test_key_nfc import KEYS, _env, _subject, need_yaml  # noqa: E402

ASTRAL = "\U0002F800|technology"        # NFC is U+4E3D, in the BMP: raw fails, NFC passes
NFC_ASTRAL = "\U000242EE|technology"    # U+FA6C's NFC: raw passes?, NFC fails
BAD = ["nonsense", "thing​|x", ASTRAL]


def test_refusal_applies_the_rule_raw_and_in_nfc_and_names_the_value_as_written():
    assert unicodedata.normalize("NFC", ASTRAL) == "丽|technology"
    assert key_rule.refusal("A|b") is None and key_rule.refusal(KEYS[0]) is None
    for bad in BAD + [NFC_ASTRAL, 7, ""]:
        why = key_rule.refusal(bad)
        assert why and repr(bad) in why, (bad, why)


def test_task_policy_refuses_a_malformed_key_naming_the_class_and_the_value():
    import task_policy
    for bad in BAD:
        try:
            task_policy.build("codegen", {"keys": ["A|b", bad], "block_levels": ["declared_gap"]})
        except task_policy.TaskPolicyError as e:
            assert e.task == "codegen" and e.field == "keys" and repr(bad) in str(e), str(e)
        else:
            raise AssertionError(f"{bad!r} was accepted")


def _write(root: Path, keys: list[str], tv: list[str]) -> None:
    s = (root / "subject.toml").read_text(encoding="utf-8")
    s = s.replace("block_levels = [\"absent\", ", "block_levels = [")
    head, rest = s.split("[tasks.codegen]\nkeys = [", 1)
    _, tail = rest.split("]\n", 1)
    tail = tail.split("[three_valued]\nkeys = [", 1)
    tail = tail[0] + "[three_valued]\nkeys = [" + ", ".join(json.dumps(k, ensure_ascii=False) for k in tv) + "]\n" + tail[1].split("]\n", 1)[1]
    (root / "subject.toml").write_text(head + "[tasks.codegen]\nkeys = [" + ", ".join(json.dumps(k, ensure_ascii=False) for k in keys) + "]\n" + tail,
                                       encoding="utf-8")


def test_gate_cli_exits_2_on_a_malformed_task_key():
    need_rdflib()
    for bad in BAD:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s").mkdir()
            root = _subject(Path(d) / "s", document_nfd=False, keys_nfd=False)
            _write(root, [KEYS[0], bad], [KEYS[1]])
            p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--subject", str(root), "--scenario", "S0",
                                "--as-of", "2026-11-04", "-f", "json"], capture_output=True, text=True, cwd=ROOT, timeout=300,
                               env=_env(KG_STORE="rdflib", KG_RDFLIB_FILE=str(Path(d) / "st.ttl"), KG_SUBJECT=str(root)))
            assert p.returncode == 2 and repr(bad) in p.stderr, (bad, p.returncode, p.stderr[-400:])


def _check(root: Path) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root), "--json"],
                       capture_output=True, text=True, env=_env(), cwd=ROOT, timeout=300)
    return json.loads(p.stdout)


def test_check_subject_names_the_key_as_written_and_warns_on_three_valued_duplicates():
    need_yaml()
    for bad in (ASTRAL, NFC_ASTRAL, "nonsense"):
        with tempfile.TemporaryDirectory() as d:
            root = _subject(Path(d), document_nfd=False, keys_nfd=False)
            _write(root, [KEYS[0], bad], [KEYS[1], bad])
            rep = _check(root)
            hit = [f for f in rep["findings"] if f["rule"] == "key-syntax"]
            assert len(hit) == 2 and all(repr(bad) in f["message"] for f in hit), (bad, hit)
    with tempfile.TemporaryDirectory() as d:
        root = _subject(Path(d), document_nfd=False, keys_nfd=False)
        nfd = unicodedata.normalize("NFD", KEYS[1])
        _write(root, [KEYS[0]], [KEYS[1], nfd])
        rep = _check(root)
        dup = [f for f in rep["findings"] if f["rule"] == "duplicate" and "three_valued" in f["where"]]
        assert len(dup) == 1 and repr(nfd) in dup[0]["message"], rep["findings"]


def test_a_ledger_is_read_in_nfc():
    import trace
    nfc = KEYS[0]
    nfd = unicodedata.normalize("NFD", nfc)
    entry = {"id": "f1", "path": "a.py", "app": "x", "sha256": "0", "commit": "c", "assertions": [f"assertion:{nfd}@1"],
             "keys": [nfd], "used": [{"id": f"assertion:{nfd}@1", "key": nfd, "value": "v", "sha256": "0"}]}
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "ledger.json"
        p.write_text(json.dumps({"tool": trace.LEDGER_TOOL, "schema_version": trace.SCHEMA_VERSION, "entries": [entry]}),
                     encoding="utf-8")
        e = trace.read_ledger(p, missing_ok=False)["entries"][0]
    assert e["keys"] == [nfc] and e["assertions"] == [f"assertion:{nfc}@1"], e
    assert e["used"][0]["id"] == f"assertion:{nfc}@1" and e["used"][0]["key"] == nfc
    assert trace.entry_keys(e) == [nfc]

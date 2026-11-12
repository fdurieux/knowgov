"""Task-0296 (decision-0034 choice 3(a)): one rule for a knowledge key, entity|attribute.

Each side of the | is non-empty and holds no |, no whitespace and no format character (U+200B to U+200D,
U+2060, U+FEFF). ``harness/key_rule.py`` holds it; ``tools/check_subject.py``'s ``KEY_RE`` and the ``keys`` items
of ``gate_verdict`` and ``evidence_bundle`` carry it; a key outside it is a check_subject error and -32602 on
the wire, over stdio and HTTP, in both eras. Every key in the public subjects and the record matches."""
from __future__ import annotations

import glob
import json
import sys
import threading
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import check_subject  # noqa: E402
import key_rule  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
from tests.test_http_limits import _post as _raw_post, _send  # noqa: E402
from tests.test_mcp_server import _Day, _meta, _server  # noqa: E402

GOOD = ("P2|surcharge", "QuoteAPI|on_screening_outage", "shipper|uses:quote_api", "REQ-06|text", "S-accept|max",
        "worked_example|price", "Ünïcode|名前")
BAD = ("nonsense", "", "|b", "a|", "a|b|c", "a |b", "a| b", "a\t|b", "a|b\n", "thing\u200b|property", "a\u200c|b",
       "a|\u200db", "a\u2060|b", "\ufeffa|b", "a\u00a0|b",
       # task-0297: the spot check at 946c72e, and the engines' \s gap (K2)
       "thing\u200e|property", "thing\u202e|property", "thing\u00ad|property", "a\u2061|b", "a\u180e|b",
       "a\x00|b", "thing\x1c|property", "a\x1f|b", "a\x85|b", "a\u2028|b", "a\u3000|b", "a\U000e0001|b",
       "a\U0001f600|b")
TOOLS = ("gate_verdict", "evidence_bundle")


def _keys_item(name: str) -> dict:
    tool = next(t for t in mcp_server.TOOLS if t["name"] == name)
    return tool["inputSchema"]["properties"]["keys"]["items"]


def test_one_pattern_in_check_subject_and_both_tools():
    """AC1: the same pattern, by identity and by text; the source carries escapes, not invisible characters."""
    assert check_subject.KEY_RE is key_rule.KEY_RE
    assert key_rule.PATTERN == "^" + key_rule.KEY_RE.pattern + "$"
    for name in TOOLS:
        assert _keys_item(name)["pattern"] == key_rule.PATTERN, name
    src = (ROOT / "harness" / "key_rule.py").read_text(encoding="utf-8")
    assert all(ord(c) < 0x7f for c in src), "the rule's source is ASCII: \\uXXXX escapes, no invisible character"


def test_the_rule_and_the_schema_agree_on_every_case():
    """AC1, AC3: is_key and the schema's pattern accept the same keys and refuse the same."""
    for k in GOOD:
        assert key_rule.is_key(k) and not schema_check.validate(k, _keys_item("gate_verdict")), k
    for k in BAD:
        assert not key_rule.is_key(k) and schema_check.validate(k, _keys_item("gate_verdict")), repr(k)


def test_check_subject_reports_a_key_outside_the_rule_as_an_error():
    """AC3: a zero-width space, or any other key outside the rule, is a key-syntax error in check_subject."""
    for k in ("thing\u200b|property", "nonsense", "a\ufeff|b", "thing\u202e|property"):   # RLO: task-0297
        rep = check_subject.Report(ROOT)
        assert check_subject._key(rep, "[tasks.codegen] keys", k) is False
        assert any(f["rule"] == "key-syntax" and f["level"] == "error" for f in rep.findings), (k, rep.findings)
    rep = check_subject.Report(ROOT)
    assert check_subject._key(rep, "[tasks.codegen] keys", "P2|surcharge") is True and not rep.findings


def _tools_call(s, name, args, modern):
    params = {"name": name, "arguments": args, **({"_meta": _meta()} if modern else {})}
    with _Day():
        return s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})


def test_a_key_outside_the_rule_is_minus_32602_over_stdio_and_http_in_both_eras():
    """AC2, AC3: gate_verdict and evidence_bundle refuse "nonsense" and a zero-width space before dispatch."""
    s, _ = _server()
    for name in TOOLS:
        for k in ("nonsense", "thing\u200b|property"):
            for modern in (False, True):
                r = _tools_call(s, name, {"keys": [k]}, modern)
                assert r.get("error", {}).get("code") == -32602 and "keys[0]" in r["error"]["message"], (name, k, modern, r)
        ok = _tools_call(s, name, {"keys": ["P2|surcharge"], "as_of": "2026-11-04"}, False)
        assert "result" in ok and ok["result"]["isError"] is False, (name, ok)
    httpd = mcp_server.serve_http(s, "127.0.0.1", 0, None)
    httpd.RequestHandlerClass.log_message = lambda self, *a: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    try:
        for name in TOOLS:
            for modern in (False, True):
                params = {"name": name, "arguments": {"keys": ["thing\u200b|property"]}, **({"_meta": _meta()} if modern else {})}
                body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": params}).encode()
                extra = (b"MCP-Protocol-Version: 2026-07-28\r\nMcp-Method: tools/call\r\nMcp-Name: " + name.encode() + b"\r\n") if modern else b""
                got, data = _send(port, _raw_post(port, "/mcp", body, extra=extra))
                assert b"-32602" in data and b"keys[0]" in data, (name, modern, got, data[-300:])
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_every_key_in_the_public_subjects_and_the_record_matches():
    """AC4: the task classes' keys, the register maps' rows and every key the record's gate reports name."""
    seen = 0
    for st in sorted(glob.glob(str(ROOT / "subjects" / "*" / "subject.toml"))):
        for name, spec in tomllib.loads(Path(st).read_text(encoding="utf-8")).get("tasks", {}).items():
            for k in spec.get("keys", []):
                assert key_rule.is_key(k), (st, name, k)
                seen += 1
    for rm in sorted(glob.glob(str(ROOT / "subjects" / "*" / "register_map.toml"))):
        for row in tomllib.loads(Path(rm).read_text(encoding="utf-8")).get("row", []):
            assert key_rule.is_key(row["key"]), (rm, row["key"])
            seen += 1
    for det in sorted(glob.glob(str(ROOT / "subjects" / "**" / "deterministic.json"), recursive=True)):
        keys = json.loads(Path(det).read_text(encoding="utf-8")).get("gate_keys") or {}
        for k in keys:
            assert key_rule.is_key(k), (det, k)
            seen += 1
    assert seen > 400, seen


def test_the_changelog_names_the_pattern_under_contract_changes():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## 0.9.0 ", 1)[1].split("\n## ", 1)[0]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0296" in contract and "entity|attribute" in contract


# ---- task-0297 (decision-0034 Amendment A1): every control and format character, read alike by both engines

def _ranges(allowed: str) -> list[tuple[int, int]]:
    import re
    return [(int(a, 16), int(b or a, 16)) for a, b in re.findall(r"\\u([0-9a-f]{4})(?:-\\u([0-9a-f]{4}))?", allowed)]


def test_every_control_and_format_character_is_refused_and_combining_marks_are_kept():
    """Every code point of category Cc or Cf the interpreter's Unicode tables name, beyond the BMP too, and every
    Zs, Zl and Zp one, is refused on either side of the |; nothing ALLOWED holds belongs to them, so a later Unicode
    version cannot open a gap unseen. A combining mark (Mn) is kept: an NFD accented name needs it."""
    import unicodedata
    refused = [c for c in range(0x110000) if (unicodedata.category(chr(c)) in key_rule.REFUSED_CATEGORIES
                                              or chr(c).isspace()) and not 0xD800 <= c <= 0xDFFF]
    # every Cc, Cf, Zs, Zl and Zp code point, and every character str.isspace() names; a lone surrogate is no
    # character of a key read from JSON
    assert {c for c in range(0x110000) if chr(c).isspace()} <= set(refused)
    assert len([c for c in refused if unicodedata.category(chr(c)) in ("Cc", "Cf")]) > 200
    item = _keys_item("gate_verdict")
    for c in refused:
        ch = chr(c)
        assert not key_rule.is_key(f"thing{ch}|property") and not key_rule.is_key(f"thing|{ch}property"), hex(c)
        assert schema_check.validate(f"thing{ch}|property", item), hex(c)
    for a, b in _ranges(key_rule.ALLOWED):
        assert b <= 0xFFFF and not (a <= 0xDFFF and b >= 0xD800), (hex(a), hex(b))
        for c in range(a, b + 1):
            assert c != 0x7C and unicodedata.category(chr(c)) not in key_rule.REFUSED_CATEGORIES, hex(c)
    for k in ("name͏|attr", unicodedata.normalize("NFD", "Écrit|élevé"), "Ünïcode|名前"):
        assert key_rule.is_key(k) and not schema_check.validate(k, item), repr(k)


def test_the_pattern_reads_alike_in_ecma_262():
    """No \\s, \\d or \\w, whose sets differ between engines (Python's \\s holds U+001C to U+001F and U+0085, ECMA-262's
    does not); its only escapes are \\uXXXX and \\|. A character beyond the BMP is refused also when read as two
    UTF-16 surrogates, as ECMA-262 without the u flag reads it, since ALLOWED leaves the surrogates out."""
    import re
    import struct
    p = key_rule.PATTERN
    assert not re.search(r"\\[sSdDwWbB]", p), p
    assert set(re.findall(r"\\(.)", p)) <= {"u", "|"}, set(re.findall(r"\\(.)", p))
    compiled = re.compile(p)
    for k in ("a\U0001f600|b", "a\U000e0001|b", "\U00020000x|y"):
        raw = k.encode("utf-16-le")
        units = "".join(chr(u) for u in struct.unpack(f"<{len(raw) // 2}H", raw))   # surrogates as their own code points
        assert compiled.search(k) is None and compiled.search(units) is None, repr(k)

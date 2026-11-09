"""task-0275 (decision-0033 choice 1, amending decision-0016 point 3): instance/README.md's settings table has one
row for every KG_* setting instance/README.md or docs/security.md names, each with its group and whether it is a
contract. A setting either file names without a row fails; so does a row for a setting no code reads, or a row
whose only mention is the table unless it is one of the settings the table itself documents (TABLE_ONLY), so the
table cannot invent a name. decision-0027's twenty are contracts; the wording says the table decides."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_adopter_docs as adopter  # noqa: E402

README = ROOT / "instance" / "README.md"
SECURITY = ROOT / "docs" / "security.md"
HEADING = "## The settings an instance may rely on"
KG = re.compile(r"\bKG_[A-Z0-9_]*[A-Z0-9_]")
# Settings whose description is their row: the CI-template, hook, store and model rows task-0234 wrote as tables.
TABLE_ONLY = {"KG_GATE", "KG_TASK", "KG_STAGE", "KG_CODE_REPO", "KG_SUBJECT_IN", "KG_HOME",
              "KG_NEO4J_URI", "KG_NEO4J_USER", "KG_SUBJECT_CALL_TIMEOUT", "KG_ARMS_MODEL", "KG_MODEL_API_KEY_VAR",
              "KG_MODEL_API_KEY", "KG_MODELS"}


def _section(text: str) -> str:
    a = text.index(HEADING)
    return text[a:text.index("\n## ", a + len(HEADING))]


def _rows() -> list[list[str]]:
    lines = [ln for ln in _section(README.read_text(encoding="utf-8")).splitlines() if ln.startswith("| `KG_")]
    return [[c.strip() for c in ln.strip().strip("|").split(" | ")] for ln in lines]


def _named_outside_the_table() -> set[str]:
    text = README.read_text(encoding="utf-8")
    table = "\n".join(ln for ln in _section(text).splitlines() if ln.startswith("| `KG_"))
    return set(KG.findall(text.replace(table, ""))) | set(KG.findall(SECURITY.read_text(encoding="utf-8")))


def test_one_table_with_a_row_per_setting_the_two_files_name():
    rows = _rows()
    names = [r[0].strip("`") for r in rows]
    assert len(names) == len(set(names)), "one row per setting"
    assert all(len(r) == 5 for r in rows), [r[0] for r in rows if len(r) != 5]   # setting, group, what, default, contract
    both = set(KG.findall(README.read_text(encoding="utf-8"))) | set(KG.findall(SECURITY.read_text(encoding="utf-8")))
    missing = sorted(both - set(names))
    assert not missing, f"named in instance/README.md or docs/security.md, with no row in the settings table: {missing}"
    outside = _named_outside_the_table()
    invented = sorted(set(names) - outside - TABLE_ONLY)
    assert not invented, f"a row for a setting neither file mentions outside the table: {invented}"
    stale = sorted(TABLE_ONLY & outside)
    assert not stale, f"named elsewhere now, so drop it from TABLE_ONLY: {stale}"
    unread = sorted(n for n in names if n not in set(KG.findall(adopter._code_text())))
    assert not unread, f"a row for a setting no code reads: {unread}"
    assert len(names) >= 75, len(names)


def test_each_row_has_a_group_and_says_contract_or_why_not():
    for setting, group, what, default, contract in _rows():
        assert group and what and default, setting
        assert contract == "yes" or re.fullmatch(r"no: [a-z].+", contract), (setting, contract)
    marked = {r[0].strip("`"): r[4] for r in _rows()}
    assert all(marked[n] == "yes" for n in adopter.CONTRACT_SETTINGS), "decision-0027's twenty are contracts"
    for n in ("KG_STORE", "KG_SUBJECT", "KG_REGISTER", "KG_BIND", "KG_MCP_TOKEN", "KG_PAGE_TOKEN", "KG_AS_OF",
              "KG_PUBLISH", "KG_REPORT", "KG_ANNOTATE", "KG_CLOCK", "KG_TODAY"):
        assert marked[n] == "yes", n
    for n in ("KG_PORT_APP", "KG_PUBLIC_PORT", "KG_STORE_READ_ATTEMPTS", "KG_ALLOW_UNCONTAINED_EXECUTION"):
        assert marked[n].startswith("no: "), n
    assert sum(v == "yes" for v in marked.values()) == 63 and len(marked) == 75, "as the maintainer confirmed (2026-11-09)"


def test_the_wording_says_the_table_decides():
    text = " ".join(README.read_text(encoding="utf-8").split())
    section = " ".join(_section(README.read_text(encoding="utf-8")).split())
    assert "contracts from 1.0 (decision-0027). The others this guide names" not in text, "task-0234's wording"
    assert ("A setting is a contract when the table marks it so** (decision-0016 point 3, as amended by "
            "decision-0033 choice 1)") in section
    row = next(ln for ln in README.read_text(encoding="utf-8").splitlines() if ln.startswith("| the `KG_*` settings this file or"))
    assert "that the settings table marks as contracts (decision-0016 point 3, as amended by decision-0033 choice 1)" in row
    assert "one they name is a contract only when the table in \"The settings an instance may rely on\" marks it so" in text

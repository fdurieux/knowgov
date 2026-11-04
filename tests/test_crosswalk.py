"""task-0072: the provenance crosswalk. docs/guide.md and demo/GLOSSARY.md carry one table, held
equal here, and it names every basis the harness writes and every level the gate orders."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- provenance crosswalk: begin", "<!-- provenance crosswalk: end -->"

# every basis the harness writes: extract.py (extracted, authored), load.py load_captures (elicited),
# store create_inferred (inferred); gate.py flags inferred, assumed and hypothesised
BASES = {"authored", "extracted", "elicited", "inferred", "assumed", "hypothesised"}


def _table(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.count(BEGIN) == 1 and text.count(END) == 1, path
    return text[text.index(BEGIN):text.index(END) + len(END)]


def _order() -> list[str]:
    src = (ROOT / "harness" / "gate.py").read_text(encoding="utf-8")
    return re.findall(r'"(\w+)"', re.search(r"^ORDER = \[(.*)\]$", src, re.M).group(1))


def test_the_guide_and_the_glossary_carry_one_table():
    assert _table(ROOT / "docs" / "guide.md") == _table(ROOT / "demo" / "GLOSSARY.md")


def test_every_basis_status_and_level_has_a_row():
    rows = _table(ROOT / "docs" / "guide.md")
    for b in BASES:
        assert f"| basis `{b}` |" in rows, b
    for s in _order():
        assert f"| status `{s}` |" in rows or f"| key level `{s}` |" in rows, s
    assert "| status `rejected` |" in rows   # decision-0002: out of the live set, not in ORDER
    for b in BASES:   # the gate's flag list is the code's, not the table's
        if b in ("inferred", "assumed", "hypothesised"):
            assert f'"{b}"' in (ROOT / "harness" / "gate.py").read_text(encoding="utf-8")


def test_every_row_answers_both_vocabularies():
    rows = [r for r in _table(ROOT / "docs" / "guide.md").splitlines() if r.startswith("| ") and "`" in r.split("|")[1]]
    assert len(rows) >= len(BASES) + len(_order()) + 1
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        assert len(cells) == 4 and all(cells), r

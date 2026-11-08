"""task-0218: the pre-registration template (docs/reverse-engineering-preregistration.md) carries every
field step 1 of the reverse-engineering process names, each with what to write and J-F's first run as the
worked example, and its skeleton has exactly the fields the page explains, in the same order.

Plain assert functions, stdlib only, for tests/run_tests.py.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "reverse-engineering-preregistration.md"
GUIDE = ROOT / "docs" / "reverse-engineering.md"
# task-0218's description, step 1's fields (doc-0032 §2 step 1): each must be a field of the template
STEP_1 = ("The original and its commit", "The lane's file set", "The roles", "The clean room", "The bars",
          "The bounded inventories", "The bundle")


def _between(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def _fields() -> list[str]:
    return re.findall(r"^### (\d+\. .+)$", _between(TEMPLATE.read_text(encoding="utf-8"), "## The fields", "## The skeleton"),
                      re.M)


def _skeleton() -> list[str]:
    block = _between(TEMPLATE.read_text(encoding="utf-8").split("## The skeleton", 1)[1], "```markdown\n", "\n```")
    return re.findall(r"^## (\d+\. .+)$", block, re.M)


def test_the_fields_are_numbered_in_order():
    fields = _fields()
    assert fields, "no field found under 'The fields'"
    assert [int(f.split(".", 1)[0]) for f in fields] == list(range(1, len(fields) + 1)), fields


def test_every_field_step_1_names_is_a_field():
    titles = {f.split(". ", 1)[1] for f in _fields()}
    for name in STEP_1:
        assert name in titles, f"step 1 names '{name}', which the template has no field for"


def test_every_field_says_what_to_write_and_shows_jf():
    body = _between(TEMPLATE.read_text(encoding="utf-8"), "## The fields", "## The skeleton")
    sections = re.split(r"^### \d+\. .+$", body, flags=re.M)[1:]
    assert len(sections) == len(_fields())
    for title, text in zip(_fields(), sections):
        assert "**What to write.**" in text, f"field {title} does not say what to write"
        assert "**J-F's first run.**" in text, f"field {title} has no worked example"


def test_the_skeleton_has_the_fields_the_page_explains():
    assert _skeleton() == _fields()
    block = TEMPLATE.read_text(encoding="utf-8").split("## The skeleton", 1)[1]
    assert "## Results" in block and "Frozen <date> at <commit>, sha256 <digest>" in block


def test_the_guide_and_the_template_link_each_other():
    assert "(reverse-engineering-preregistration.md)" in GUIDE.read_text(encoding="utf-8")
    assert "(reverse-engineering.md)" in TEMPLATE.read_text(encoding="utf-8")

"""The annotated proposal template (instance/templates/proposal.toml; instance/README.md, "Writing a proposal
before the pull request"). ``harness/proposal_impact.py`` reads it once its placeholders are filled from the
example instance's register (tools/example_instance.py), and every field the reader accepts appears in it, so
the template cannot fall behind the reader. Standard library only: the register's own tools are loaded by
path, as the reader loads them."""
from __future__ import annotations

import datetime as dt
import re
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import proposal_impact  # noqa: E402

TEMPLATE = ROOT / "instance" / "templates" / "proposal.toml"
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
# each placeholder, and the register node that fills it: (taxonomy folder, kind)
FILLS = {"OWNER_UNIT": ("organisation", "business_unit"), "PRODUCT_PORTFOLIO": ("products", "portfolio"),
         "CAPABILITY_DOMAIN": ("capabilities", "capability_domain"), "REUSED_CAPABILITY": ("capabilities", "capability"),
         "REUSED_PROCESS": ("processes", "activity")}


def _approved(register: Path, taxonomy: str, kind: str) -> str:
    for p in sorted((register / taxonomy).glob("*.toml")):
        n = tomllib.loads(p.read_text(encoding="utf-8"))
        if n.get("kind") == kind and n.get("state") == "approved":
            return n["id"]
    raise AssertionError(f"the example register holds no approved {kind} under {taxonomy}/")


def _filled(register: Path) -> tuple[str, dict]:
    text = TEMPLATE.read_text(encoding="utf-8")
    names = set(PLACEHOLDER.findall(text))
    assert names == set(FILLS), f"placeholders {sorted(names)}; the test fills {sorted(FILLS)}"
    ids = {k: _approved(register, *v) for k, v in FILLS.items()}
    return PLACEHOLDER.sub(lambda m: ids[m.group(1)], text), ids


def test_proposal_impact_reads_the_template_filled_from_the_example_register():
    import example_instance
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        reg = inst / "register"
        text, ids = _filled(reg)
        assert "{{" not in text
        proposal = tomllib.loads(text)
        filled = Path(t) / "proposal.toml"
        filled.write_text(text, encoding="utf-8")
        assert proposal_impact.read_proposal(filled) == proposal   # the command's own reader, TOML by its suffix
        r = proposal_impact.evaluate(proposal, root=reg, today=dt.date(2026, 11, 9))
        o = r["overlay"]
        assert o["title"] == proposal["title"]
        assert (o["nodes"], o["links"], o["exceptions"]) == (len(proposal["nodes"]), len(proposal["links"]), len(proposal["exceptions"]))
        reused = {x["node"]: x["mode"] for x in r["keys"]["by_node"]}
        assert reused[ids["REUSED_CAPABILITY"]] == "as_is" and reused[ids["REUSED_PROCESS"]] == "changed", reused
        # the provisional ids are kept as written, and none is a register id
        held = {tomllib.loads(p.read_text(encoding="utf-8")).get("id") for p in reg.rglob("*.toml") if "tools" not in p.parts}
        assert [n["id"] for n in r["nodes"]] == [n["id"] for n in proposal["nodes"]] and all(n["hypothetical"] for n in r["nodes"])
        provisional = [n["id"] for n in proposal["nodes"]] + [x["id"] for x in proposal["links"] + proposal["exceptions"] if "id" in x]
        assert not set(provisional) & held
        assert {u["id"] for u in r["unmapped"]} == {n["id"] for n in proposal["nodes"]}
        # the template's placement problems are warnings or notes, never an error the reader would raise
        assert all(p["level"] != "error" for p in r["placement"]), r["placement"]


def test_every_field_the_reader_accepts_is_in_the_template():
    doc = tomllib.loads(PLACEHOLDER.sub("X", TEMPLATE.read_text(encoding="utf-8")))
    src = (ROOT / "harness" / "proposal_impact.py").read_text(encoding="utf-8")
    top = re.search(r"extra = set\(proposal\) - \{([^}]*)\}", src)
    assert top, "the reader's top-level fields are no longer one literal set: update this test"
    accepted = set(re.findall(r'"(\w+)"', top.group(1)))
    assert set(doc) == accepted, (sorted(doc), sorted(accepted))
    union = lambda rows: set().union(*(set(r) for r in rows))  # noqa: E731
    assert union(doc["nodes"]) == proposal_impact.NODE_FIELDS, union(doc["nodes"]) ^ proposal_impact.NODE_FIELDS
    assert union(doc["links"]) == proposal_impact.LINK_FIELDS, union(doc["links"]) ^ proposal_impact.LINK_FIELDS
    assert union(doc["reused"]) == {"id", "mode"}
    assert {r["mode"] for r in doc["reused"]} == set(proposal_impact.MODES)
    assert union(doc["exceptions"]) == proposal_impact.EXC_FIELDS, union(doc["exceptions"]) ^ proposal_impact.EXC_FIELDS
    text = TEMPLATE.read_text(encoding="utf-8")
    for said in ("register_nodes", "provisional", "proposal_impact.py", "never mints"):   # the comments' plain-English guide
        assert said in text, said

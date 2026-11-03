"""Task-0006: the instance layout. The kinds table covers every mapper the harness has, the guide
lists every kind, the public example instance checks clean and is listed by the page, and a
document no mapper reads is reported absent, never skipped. The deterministic half (S1 to S7 from
the example instance against the record, the instance unchanged) runs in harness.yml, which has
the store's dependencies; the read-only mount runs in the stack job."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import check_instance  # noqa: E402
import example_instance  # noqa: E402
import server  # noqa: E402  (imported here, in the default environment: its module tables are the public subjects')
import views  # noqa: E402


def _mappers() -> set[str]:
    src = (ROOT / "harness" / "extract.py").read_text(encoding="utf-8")
    block = re.search(r"^EXTRACTORS = \{(.*?)^\}", src, re.M | re.S).group(1)
    return set(re.findall(r'^\s+"(\w+)":', block, re.M)) | {"links"}


def _digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def test_every_mapper_reads_exactly_one_kind_and_the_guide_lists_every_kind():
    table = check_instance.kinds()
    assert len(table) == 20 and len({k["row"] for k in table.values()}) == 20
    placed = [m for k in table.values() for m in k["mappers"]]
    assert sorted(placed) == sorted(_mappers()), "a mapper is in no kind, in two, or no longer exists"
    guide = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    for folder, k in table.items():
        row = re.search(rf"^\| `{re.escape(folder)}` \| {re.escape(k['row'])} \| (.*) \|$", guide, re.M)
        assert row, folder
        assert set(re.findall(r"`(\w+)`", row.group(1))) == set(k["mappers"]), folder



def test_every_kind_names_its_linter_as_doc_0008_section_5_does():
    """task-0045: the lint field per kind is the brief's table, tool and gate column word for word,
    and capable says whether the tool exits non-zero on a finding today."""
    doc = next((ROOT / "backlog" / "docs").glob("doc-0008*")).read_text(encoding="utf-8")
    sec = doc.split("### Kinds and the tool Legible names")[1].split("### The route")[0]
    brief = {m.group(1): (m.group(2).strip(), m.group(3).strip())
             for m in re.finditer(r"^\| ([a-z0-9-]+) \| [^|]+ \| ([^|]+) \| ([^|]+) \|", sec, re.M)}
    table = check_instance.kinds()
    assert list(brief) == list(table), "the brief's kinds and kinds.toml differ, or their order does"
    for folder, k in table.items():
        lint = k["lint"]
        assert set(lint) == {"tool", "gate", "capable"}, folder
        assert (lint["tool"], lint["gate"]) == brief[folder], folder
        assert lint["capable"] is lint["gate"].startswith(("yes", "via")), folder
    assert sum(k["lint"]["capable"] for k in table.values()) == 10

def test_the_example_instance_holds_and_its_sources_are_untouched():
    before = _digest(ROOT / "subjects" / "cargo_quote"), _digest(ROOT / "demo" / "register")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        rep = check_instance.check(out)
        assert rep["errors"] == [] and rep["absent"] == [] and rep["unread"] == [], rep
        [s] = rep["subjects"]
        assert s["id"] == "cargo_quote" and s["record"] and len(s["artefacts"]) == 10
        assert all(a["state"] == "read" and a["path"].startswith("artefacts/") for a in s["artefacts"])
        assert sorted(rep["kinds"]) == ["acceptance-scenarios", "api-contracts", "bpmn-process-models", "cross-artefact-links",
                                        "decision-tables", "plantuml-models", "specification-prose", "textual-requirements"]
        assert not (out / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results").exists(), "the record moved to record/"
        assert check_instance.main([str(out)]) == 0
    assert (_digest(ROOT / "subjects" / "cargo_quote"), _digest(ROOT / "demo" / "register")) == before


def test_a_document_no_mapper_reads_is_reported_absent_never_skipped():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        (out / "artefacts" / "user-stories").mkdir()
        (out / "artefacts" / "user-stories" / "quote.md").write_text("As a shipper, I want a quote.\n", encoding="utf-8")
        (out / "artefacts" / "architecture-decisions").mkdir()
        (out / "artefacts" / "architecture-decisions" / "0001.md").write_text("# ADR 1\n", encoding="utf-8")
        m = out / "subjects" / "cargo_quote" / "subject.toml"
        text = m.read_text(encoding="utf-8")
        story = ('\n[[artefact]]\nkey = "stories/quote.md"\nfamily = "stories"\nformat = "markdown"\nlabel = "user story"\n'
                 'format_label = "markdown"\npath = "../../artefacts/user-stories/quote.md"\n')
        m.write_text(text.replace("\n# the code the oracle verified", story + "\n# the code the oracle verified", 1), encoding="utf-8")
        rep = check_instance.check(out)
        assert rep["errors"] == [], rep["errors"]
        absent = {(a["key"], a["kind"], a["subject"]) for a in rep["absent"]}
        assert absent == {("stories/quote.md", "user-stories", "cargo_quote"),
                          ("artefacts/architecture-decisions/0001.md", "architecture-decisions", None)}, absent
        assert [u["file"] for u in rep["unread"]] == ["artefacts/architecture-decisions/0001.md"]
        text = check_instance.render(rep)
        assert "ABSENT stories/quote.md [user-stories]" in text and "UNREAD artefacts/architecture-decisions/0001.md" in text
        assert check_instance.main([str(out)]) == 0, "absent and unread are findings, not errors"


def test_what_breaks_the_layout_is_an_error_and_a_missing_folder_cannot_run():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        (out / "artefacts" / "slides").mkdir()
        (out / "artefacts" / "slides" / "deck.pptx").write_bytes(b"x")
        (out / "artefacts" / "decision-tables" / "decision_table.md").unlink()
        rep = check_instance.check(out)
        errs = " | ".join(rep["errors"])
        assert "artefacts/slides/: not a kind" in errs and "decision_table.md does not exist" in errs, errs
        assert check_instance.main([str(out)]) == 1
        assert check_instance.main([str(Path(td) / "nope")]) == 2


def test_the_page_lists_the_instance_subjects_only_and_reads_its_record():
    import os
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        saved = {k: os.environ.get(k) for k in ("KG_SUBJECTS", "KG_SUBJECT")}
        os.environ["KG_SUBJECTS"] = str(out / "subjects")
        os.environ.pop("KG_SUBJECT", None)
        try:
            subs = server._load_subjects()
            assert [p.id for p in subs] == ["cargo_quote"] and subs[0].root == (out / "subjects" / "cargo_quote").resolve()
            scen = views.scenario_list(Path(td) / "no-runs", subject=subs[0])
            assert [s["id"] for s in scen] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
            v = views.build("S6", "record", Path(td) / "no-runs", subject=subs[0])
            assert v["gate"]["verdict"] == "PROCEED" and len(v["stage2"]["invalidated"]) == 4, json.dumps(v["gate"])[:200]
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v


def test_the_example_instance_maps_cargoquote_reference_code_to_its_application():
    """task-0050: code_map.toml maps code path globs to register APP ids; the example maps the
    reference code clean, nothing unmapped, nothing unmatched."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        cm = check_instance.check(out)["code_map"]
        assert cm["root"] == "subjects/cargo_quote/vendor/stack_experiment/cargo_quote", cm
        assert [(r["glob"], r["app"], r["files"]) for r in cm["rows"]] == [("reference_impl.py", "APP-0001", ["reference_impl.py"])]
        assert cm["unmapped"] == [] and cm["unmatched"] == []
        assert "APP-0001" in check_instance.register_apps(out / "register")
        (out / "code_map.toml").unlink()
        rep = check_instance.check(out)
        assert rep["code_map"] is None and rep["errors"] == [], "the file is optional"


def _with_code_map(out: Path, rows: str, root: str = "code") -> None:
    (out / "code" / "quote" / "pricing").mkdir(parents=True)
    for f in ("quote/api.py", "quote/pricing/tariff.py", "quote/screening.py", "quote/README.md"):
        (out / "code" / f).write_text("#\n", encoding="utf-8")
    (out / "code_map.toml").write_text(f'[code]\nroot = "{root}"\ninclude = ["**/*.py"]\n\n' + rows, encoding="utf-8")


def test_the_code_map_refuses_an_unknown_app_and_an_overlap_and_lists_unmapped_code():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        _with_code_map(out, '[[map]]\nglob = "quote/api.py"\napp = "APP-0002"\n\n'
                            '[[map]]\nglob = "quote/pricing/**"\napp = "APP-0003"\n\n'
                            '[[map]]\nglob = "lost/*.py"\napp = "APP-0004"\n')
        rep = check_instance.check(out)
        assert rep["errors"] == [], rep["errors"]
        cm = rep["code_map"]
        assert cm["unmapped"] == ["quote/screening.py"], "README.md is not code: include says *.py"
        assert cm["unmatched"] == ["lost/*.py"]
        text = check_instance.render(rep)
        assert "UNMAPPED quote/screening.py" in text and "UNMATCHED lost/*.py" in text
        assert check_instance.main([str(out)]) == 0, "unmapped and unmatched are findings, not errors"

        (out / "code_map.toml").write_text('[code]\nroot = "code"\ninclude = ["**/*.py"]\n\n'
                                           '[[map]]\nglob = "quote/**/*.py"\napp = "APP-0002"\n\n'
                                           '[[map]]\nglob = "quote/pricing/*.py"\napp = "APP-0003"\n\n'
                                           '[[map]]\nglob = "quote/s*.py"\napp = "APP-0099"\n', encoding="utf-8")
        errs = " | ".join(check_instance.check(out)["errors"])
        assert "APP-0099 is no application or module of register/applications" in errs, errs
        assert "quote/**/*.py (APP-0002) and quote/pricing/*.py (APP-0003) overlap: one covers the other" in errs, errs
        assert "quote/**/*.py (APP-0002) and quote/s*.py (APP-0099) overlap" in errs, errs
        assert check_instance.main([str(out)]) == 1

        (out / "code_map.toml").write_text('[code]\nroot = "code"\n\n[[map]]\nglob = "quote/*i.py"\napp = "APP-0002"\n\n'
                                           '[[map]]\nglob = "quote/a*"\napp = "APP-0003"\n', encoding="utf-8")
        errs = check_instance.check(out)["errors"]
        assert errs == ["code_map.toml: quote/*i.py (APP-0002) and quote/a* (APP-0003) overlap: both match quote/api.py"], errs

        (out / "code_map.toml").write_text('[code\n', encoding="utf-8")
        assert check_instance.check(out)["errors"][0].startswith("code_map.toml: does not parse")
        (out / "code_map.toml").write_text('[code]\nroot = "nowhere"\n', encoding="utf-8")
        assert check_instance.check(out)["errors"] == ["code_map.toml: root nowhere: not a directory"]


def test_glob_semantics():
    r = check_instance.glob_re
    assert r("src/**/*.py").match("src/a.py") and r("src/**/*.py").match("src/a/b/c.py")
    assert not r("src/*.py").match("src/a/b.py") and not r("*.py").match("a/b.py")
    assert r("src/**").match("src/a/b") and not r("src/a?.py").match("src/a/.py")

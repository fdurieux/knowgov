"""Task-0222: stage 2 re-reads every review file. A close of a gap a load already closed, on the same declaration,
is a no-op; one whose declaration changed is set aside and reported (task-0199). tools/check_stage2_reload.py
holds it end to end (R1 to R3) on rdflib here, through test_stage2_reload, and on both stores in CI."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import review  # noqa: E402

GID = "gap:declared:OD-1"
TEXT = "REQ-06 is NOT YET SPECIFIED (open decision OD-1, owner: compliance)"


class Gaps:
    def __init__(self, kind, text=TEXT):
        self.g = {"id": GID, "kind": kind, "declared": kind == "missing", "text": text, "keys": ["QuoteAPI|on_screening_outage"]}

    def declared_gap(self, gid):
        return self.g if gid == GID and self.g["kind"] == "missing" else None

    def gap_brief(self, gid):
        return self.g if gid == GID else None


def _check(st, sha, strict=False):
    reg = ROOT / "demo" / "register"
    doc = {"review": {"by": "employee-4", "on": "2026-11-03", "record": "m.md"}, "closes": [{"gap": GID, "sha256": sha}]}
    return review.check(doc, st, handles=review.issued_handles(reg), owners={"QuoteAPI|on_screening_outage": ["ORG-0004"]},
                        units=review.organisation_units(reg), captures={}, now=dt.date(2026, 11, 3),
                        compatible=lambda a, b, _p="": "equal", strict=strict)


def test_a_close_of_a_gap_already_closed_on_the_same_declaration_is_a_no_op():
    errs, rv = _check(Gaps("closed"), review._sha(TEXT))
    assert not errs and not rv["skipped"] and [c["already"] for c in rv["closes"]] == [True], (errs, rv)


def test_a_close_of_a_gap_closed_on_another_declaration_is_set_aside_changed():
    errs, rv = _check(Gaps("closed", TEXT + " restated"), review._sha(TEXT))
    assert not errs and not rv["closes"] and [(x["act"], x["why"]) for x in rv["skipped"]] == [("close", "changed")], rv


def test_an_open_gap_is_closed_and_the_day_a_review_is_written_a_closed_one_is_refused():
    errs, rv = _check(Gaps("missing"), review._sha(TEXT))
    assert not errs and [c["already"] for c in rv["closes"]] == [False]
    errs, _ = _check(Gaps("closed"), review._sha(TEXT), strict=True)
    assert any("no open declared gap" in e for e in errs), errs


def test_stage_two_reads_every_review_file_again_after_clearing_stage_ones_acts():
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    body = load[load.index("def load_reviews("):load.index("def _act(")]
    assert "st.clear_act_findings()" in body and 'k != "closes"' not in body and 'c.get("already")' in body
    assert "load_reviews(s, sc, again=True)" in (ROOT / "harness" / "change.py").read_text(encoding="utf-8")
    for name in ("store_rdflib.py", "store_neo4j.py"):
        src = (ROOT / "harness" / name).read_text(encoding="utf-8")
        assert "def clear_act_findings(self)" in src and "def gap_brief(self, gid)" in src, name
    import store
    assert "gap_brief" in store.READS and "clear_act_findings" not in store.READS


def test_the_stage2_check_names_the_review_cases():
    src = (ROOT / "tools" / "check_stage2_reload.py").read_text(encoding="utf-8")
    assert "def reviews_case(" in src and all(f'"{c}"' in src or f"{c}:" in src for c in ("R1", "R2", "R3"))

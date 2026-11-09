"""Task-0243 (doc-0033 R2, doc-0028 G9-16): two values of a key compare exactly.

``rules.compatible`` compared numeric strings with ``float``: 9007199254740992 and 9007199254740993, or 1e309
and 2e309, read equal, so R-CORROBORATE promoted and R-CONFLICT stayed silent; and inf and nan passed as
numbers. Now the comparison is ``decimal.Decimal``'s, exact with no tolerance (316.00 is still 316), and a
non-finite value is incomparable, R-VAGUE's reading. The reviewer's probes run through both rules on a store
double, beside a genuine corroboration that still promotes. Stdlib."""
from __future__ import annotations

import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
try:
    import extract  # noqa: F401  (needs PyYAML, which the stdlib test job lacks)
except ImportError:
    # rules.py takes only NONE from extract.py; stand in with the value the file defines, as test_pairing does
    _none = re.search(r'^NONE = "([^"]*)"$', (ROOT / "harness" / "extract.py").read_text(encoding="utf-8"), re.M).group(1)
    sys.modules["extract"] = types.SimpleNamespace(NONE=_none)
import rules  # noqa: E402


def test_integers_past_two_to_the_53_compare_exactly():
    assert float("9007199254740992") == float("9007199254740993")   # the defect's cause
    for pred in ("max", "threshold", ""):
        assert rules.compatible("9007199254740992", "9007199254740993", pred) == "conflict"
        assert rules.compatible("9007199254740993", "9007199254740993.0", pred) == "equal"


def test_values_past_the_double_range_compare_exactly():
    assert float("1e309") == float("2e309")   # both inf
    for pred in ("max", ""):
        assert rules.compatible("1e309", "2e309", pred) == "conflict"
        assert rules.compatible("1e309", "10e308", pred) == "equal"


def test_numbers_written_differently_are_still_equal_and_no_tolerance_is_added():
    assert rules.compatible("316.00", "316", "max") == "equal"
    assert rules.compatible("0.1", "1e-1", "factor") == "equal"
    assert rules.compatible("-0", "0", "min") == "equal"
    assert rules.compatible("316", "316.0000000000001", "max") == "conflict"   # no tolerance
    assert rules.compatible("0.30000000000000004", "0.3", "factor") == "conflict"


def test_a_non_finite_value_is_incomparable_whatever_its_spelling():
    for v in ("inf", "-inf", "Infinity", "+INF", "nan", "NaN", "-nan", "sNaN"):
        assert not rules._is_num(v), v
        for pred in ("max", "threshold", ""):
            assert rules.compatible(v, "300", pred) == "incomparable", (v, pred)
            assert rules.compatible("300", v, pred) == "incomparable", (v, pred)
            assert rules.compatible(v, v, pred) == "incomparable", (v, pred)   # nan is not nan, inf no measure
    assert rules.compatible("inf", "Infinity", "max") == "incomparable"


def test_what_was_not_numeric_reads_as_before():
    assert rules.compatible("about 300", "300", "max") == "incomparable"   # R-VAGUE's
    assert rules.compatible("300", "300", "max") == "equal"
    assert rules.compatible("quoted", "review_hold", "") == "conflict"
    assert rules.compatible("a=1;b=2", "a=1;b=2", "") == "equal"
    assert rules.compatible("a=1;b=2", "a=1;b=3", "") == "conflict"


class Store:
    """The two rules' port, on one candidate pair per probe: two documents' extracted statements of one key."""
    name = "double"

    def __init__(self, pairs):
        self._pairs = pairs
        self.corroborated, self.conflicts = [], []

    def candidate_pairs(self, across=None):
        return list(self._pairs)

    def corroborate(self, a, b, promote=True):
        self.corroborated.append((a, b, promote))

    def mark_conflict(self, a, b, gid, key, scenario, text):
        self.conflicts.append((gid, key))


def _pair(n, key, va, vb):
    return {"a": f"s:{n}:a", "b": f"s:{n}:b", "key": key, "pred": key.split("|", 1)[1], "va": va, "vb": vb,
            "ba": "extracted", "bb": "extracted", "aa": "doc-a", "ab": "doc-b"}


def test_the_reviewers_probes_through_r_corroborate_and_r_conflict():
    probes = [_pair(1, "P1|max", "9007199254740992", "9007199254740993"),
              _pair(2, "P1|threshold", "1e309", "2e309"),
              _pair(3, "P1|max", "inf", "inf"),
              _pair(4, "P1|min", "nan", "nan")]
    st = Store(probes)
    assert rules.r_corroborate(st) == 0 and st.corroborated == []   # nothing promotes
    got = rules.r_conflict(st, "S1")
    assert [g["key"] for g in got] == ["P1|max", "P1|threshold"]     # the two exact differences conflict
    assert [c[1] for c in st.conflicts] == ["P1|max", "P1|threshold"]  # the non-finite pairs are neither


def test_a_genuine_corroboration_still_promotes():
    st = Store([_pair(1, "P1|max", "316.00", "316"), _pair(2, "P1|threshold", "9007199254740993", "9007199254740993")])
    assert rules.r_corroborate(st) == 2
    assert st.corroborated == [("s:1:a", "s:1:b", True), ("s:2:a", "s:2:b", True)]
    assert rules.r_conflict(st, "S1") == [] and st.conflicts == []

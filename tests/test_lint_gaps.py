"""Task-0216 (decision-0018 point 5): each pre-load finding on a loaded document is a gap with an owner and a route.

Stdlib, on stubs: a finding of the report becomes a lint gap with an id stable across stores and loads; the gate
lists the gaps behind the keys and never lowers a key's level for one; the finding's severity follows the linter,
at most major, info when the baseline holds it or a review resolved it as a choice or an exception; a review's
``[[resolves]]`` binds to the finding's text and is the document's owners' to make, under the role closes; a
re-lint's delta at the same tool versions names what is new, gone (a slip when the bytes changed) and kept. The
whole route on a store, both kinds, is tools/check_lint_gaps.py's (harness.yml on rdflib, the stack on Neo4j)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import gate  # noqa: E402
import gate_cli  # noqa: E402
import preload  # noqa: E402
import preload_check  # noqa: E402
import review  # noqa: E402
import schema_check  # noqa: E402

FINDING = {"rule": "SEQ002", "severity": "minor", "line": 91, "message": "Participant 'Idle' is declared but never used"}
VERDICT = {"state": "clean", "tool": "pumllint", "tool_version": "0.33.0", "digest": "d" * 64, "report": "preload-report.json",
           "file": "artefacts/plantuml-models/quote_flow.puml", "why": "", "findings": [FINDING]}


def _gap(**kw) -> dict:
    return {**preload.lint_gaps("behavior/quote_flow.puml", "v1", VERDICT)[0], "resolution": None, "resolved_by": None,
            "resolved_on": None, "record": None, "review": None, "note": None, **kw}


class Store:
    """A store holding one lint gap and the statements of its document."""
    name = "stub"

    def __init__(self, gaps=None):
        self.gaps = [_gap()] if gaps is None else gaps

    def lint_gaps(self):
        return self.gaps

    def artefact_assertions(self, artefact):
        return [{"id": "A:seq:S-review|notified@v1", "key": "S-review|notified", "version": "v1"},
                {"id": "A:seq:QuoteAPI|on_store_failure@v1", "key": "QuoteAPI|on_store_failure", "version": "v1"}]


def test_each_finding_is_a_gap_whose_id_is_the_findings_own():
    a, b = preload.lint_gaps("behavior/quote_flow.puml", "v1", VERDICT), preload.lint_gaps("behavior/quote_flow.puml", "v1", copy.deepcopy(VERDICT))
    assert a == b and len(a) == 1 and a[0]["id"].startswith("lint:behavior/quote_flow.puml@v1:")
    g = a[0]
    assert (g["rule"], g["severity"], g["line"], g["held"], g["tool"]) == ("SEQ002", "minor", 91, False, "pumllint")
    assert preload.lint_gaps("behavior/quote_flow.puml", "v2", VERDICT)[0]["id"] != g["id"]   # a new version, a new gap
    held = dict(VERDICT, findings=[dict(FINDING, held=True)])
    assert preload.lint_gaps("behavior/quote_flow.puml", "v1", held)[0]["held"] is True
    assert preload.lint_gaps("x", "v1", {"state": "unchecked"}) == []   # bytes not judged: no finding of them


def test_the_gate_lists_the_gaps_behind_the_keys_and_never_lowers_a_level():
    keys = {"S-review|notified": {"level": "approved", "flags": [], "assertions": [{"id": "A:seq:S-review|notified@v1",
                                                                                  "artefact": "behavior/quote_flow.puml"}]},
            "P1|formula": {"level": "approved", "flags": [], "assertions": [{"id": "A:dt:P1|formula@v1", "artefact": "contract/decision_table.md"}]}}
    got = gate.lint_behind(Store(), keys)
    assert [g["keys"] for g in got] == [["S-review|notified"]]
    assert gate.lint_behind(Store(gaps=[]), keys) is None   # no lint gap held: the result has no lint field, as before
    assert all(v["level"] == "approved" for v in keys.values())
    fs = gate_cli.findings({"keys": keys, "verdict": "PROCEED", "blocked_keys": [], "lint": got}, set())
    assert [(f["kind"], f["severity"]) for f in fs] == [("lint", "minor")]


def test_the_severity_follows_the_linter_at_most_major_and_info_once_held_or_resolved():
    def sev(**kw):
        return gate_cli.lint_finding({**_gap(**kw), "keys": ["S-review|notified"]})["severity"]
    assert sev() == "minor" and sev(severity="blocker") == "major" and sev(severity="critical") == "major"
    assert sev(held=True) == "info"
    assert sev(resolution="choice", resolved_by="employee-3", resolved_on="2026-11-03", record="decisions/x.md") == "info"
    assert sev(resolution="exception", resolved_by="employee-3", resolved_on="2026-11-03", record="r") == "info"
    assert sev(resolution="open", resolved_by="employee-3", resolved_on="2026-11-03", record="r") == "minor"
    f = gate_cli.lint_finding({**_gap(), "keys": ["S-review|notified"]})
    schema = schema_check.load("gate-report")["$defs"]["finding"]
    assert schema_check.validate(f, {**schema, "$defs": schema_check.load("gate-report")["$defs"]}) == []


def test_owners_and_routes_come_from_routing_one_unit_or_each_of_several():
    route = lambda unit, key: f"route of {unit} for {key}"  # noqa: E731
    keys = {"a|x": {"level": "approved", "flags": [], "assertions": []}}
    one = {"a|x": {"unit": "ORG-0001"}, "b|y": {"unit": "ORG-0001"}}
    two = {"a|x": {"unit": "ORG-0001"}, "b|y": {"unit": "ORG-0002"}}
    res = {"keys": keys, "verdict": "PROCEED", "blocked_keys": [], "lint": [{**_gap(), "keys": ["a|x", "b|y"]}]}
    f = gate_cli.findings(res, set(), owners=one, route=route)[0]
    assert f["owner"] == "ORG-0001" and f["route"] == "route of ORG-0001 for a|x"
    f = gate_cli.findings(res, set(), owners=two, route=route)[0]
    assert f["owner"] is None and "ORG-0001, ORG-0002" in f["route"] and "route of ORG-0002 for b|y" in f["route"]


def test_a_review_resolves_a_lint_gap_by_its_text_and_only_its_documents_owner_with_closes():
    import datetime as dt
    handles = {"employee-3": {"unit": "ORG-0001", "roles": {"gives", "approves", "closes"}, "issued": dt.date(2026, 11, 2), "withdrawn": None},
               "employee-2": {"unit": "ORG-0002", "roles": {"gives", "approves"}, "issued": dt.date(2026, 11, 2), "withdrawn": None},
               "employee-9": {"unit": "ORG-0009", "roles": {"closes"}, "issued": dt.date(2026, 11, 2), "withdrawn": None}}
    owners = {"S-review|notified": ["ORG-0001"], "QuoteAPI|on_store_failure": ["ORG-0002"]}
    g = _gap()

    def check(by, **kw):
        doc = {"review": {"by": by, "on": dt.date(2026, 11, 3), "record": "decisions/lint.md"},
               "resolves": [{"gap": g["id"], "resolution": "choice", "sha256": g["sha256"], **kw}]}
        return review.check(doc, Store(), handles=handles, owners=owners, units={}, captures={}, now=dt.date(2026, 11, 3),
                            compatible=lambda *a: "agree")
    errs, norm = check("employee-3")
    assert errs == [] and norm["resolves"][0]["resolution"] == "choice" and norm["resolves"][0]["keys"]
    assert "[[resolves]]" in review.review_toml(norm) and f'gap = "{g["id"]}"' in review.review_toml(norm)
    assert [e for e in check("employee-2")[0] if "role closes" in e]       # an owner without closes
    assert [e for e in check("employee-9")[0] if "document's owners" in e]   # closes, but owning none of its keys
    assert [e for e in check("employee-3", resolution="slip")[0] if "slip is a new version" in e]
    assert [e for e in check("employee-3", sha256="0" * 64)[0] if "no longer the one" in e]
    errs, norm = review.check({"review": {"by": "employee-3", "on": dt.date(2026, 11, 3), "record": "r"},
                               "resolves": [{"gap": g["id"], "resolution": "choice", "sha256": "0" * 64}]},
                              Store(), handles=handles, owners=owners, units={}, captures={}, now=None,
                              compatible=lambda *a: "agree", strict=False)
    assert errs == [] and norm["skipped"][0]["act"] == "resolve" and norm["skipped"][0]["why"] == "changed"


def test_a_relint_at_the_same_tool_versions_shows_the_delta():
    def report(findings, sha="a" * 64, version="0.33.0"):
        return {"files": [{"file": "artefacts/plantuml-models/quote_flow.puml", "tool": "pumllint", "sha256": sha, "findings": findings}],
                "linters": [{"tool": "pumllint", "version": version}]}
    other = dict(FINDING, rule="SEQ001", message="an arrow to nowhere")
    d = preload_check.delta(report([FINDING]), report([other], sha="b" * 64), "first.json")
    assert d["comparable"] and [x["rule"] for x in d["new"]] == ["SEQ001"] and [(x["rule"], x["slip"]) for x in d["gone"]] == [("SEQ002", True)]
    d = preload_check.delta(report([FINDING]), report([dict(FINDING, line=95)]))
    assert d["kept"] == 1 and not d["new"] and not d["gone"]   # a line moved by an edit above is the same finding
    d = preload_check.delta(report([FINDING]), report([]))
    assert d["gone"][0]["slip"] is False                       # the same bytes, the rule no longer fires
    d = preload_check.delta(report([FINDING]), report([], version="0.34.0"))
    assert not d["comparable"] and "0.33.0 -> 0.34.0" in d["why"] and not d["gone"]
    schema = schema_check.load("preload-report")
    assert schema_check.validate(json.loads(json.dumps(d)), schema["properties"]["delta"] | {"$defs": schema["$defs"]}) == []


def test_the_changelog_names_it_under_contract_changes_and_the_check_runs_in_both_workflows():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0216" in contract and "lint" in contract
    for wf in ("harness.yml", "demo.yml"):
        assert "tools/check_lint_gaps.py" in (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8"), wf

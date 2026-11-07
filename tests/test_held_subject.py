"""task-0195 (doc-0030 F1, H1, S5; decision-0013 A1): the store records whose load it holds, and one port read,
``held()``, gives the subject, the scenario, each artefact's current version and when it was loaded. Every
reader decides by ``harness/held.py``. Two subjects sharing a scenario id never answer each other's gates;
``tools/check_held_subject.py`` proves it on both adapters (harness.yml on rdflib, the stack on Neo4j)."""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import held as held_state  # noqa: E402
import store  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

ARTS = ["contract/a.md", "contract/b.md", "kit/c.md"]


def _acts(*rows):
    return [dict(zip(("id", "at", "subject", "scenario"), r)) for r in rows]


def test_held_reads_the_version_from_the_current_edges_not_the_activities_order():
    one = store.held_from(_acts(("act:extract:S1:v1", "2026-11-07T08:00:00+00:00", "a", "S1")),
                          [{"artefact": x, "tag": "v1", "versions": 1} for x in ARTS])
    assert one == {"subject": "a", "scenario": "S1", "version": "v1", "versions": {x: "v1" for x in ARTS},
                   "loaded_at": "2026-11-07T08:00:00+00:00"}
    # S5: a stage-2 change whose tag sorts before v1 ("a2"), both loads at the same second: the current
    # version is the reloaded artefact's, whatever the tags' order or the activities'
    tie = "2026-11-07T08:00:00+00:00"
    for tag in ("a2", "v2", "z9"):
        h = store.held_from(_acts(("act:extract:S6:v1", tie, "a", "S6"), (f"act:extract:S6:{tag}", tie, "a", "S6")),
                            [{"artefact": "contract/a.md", "tag": tag, "versions": 2},
                             {"artefact": "contract/b.md", "tag": "v1", "versions": 1}])
        assert h["version"] == tag and h["versions"] == {"contract/a.md": tag, "contract/b.md": "v1"}, (tag, h)
    assert store.held_from([], []) is None


def test_a_store_loaded_before_the_subject_was_recorded_reads_unknown():
    h = store.held_from(_acts(("act:extract:S1:v1", "2026-11-01T00:00:00+00:00", None, None)),
                        [{"artefact": "contract/a.md", "tag": "v1", "versions": 1}])
    assert h["subject"] is None and h["scenario"] == "S1"


class _Env:
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kw}
        for k, v in self.kw.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def test_the_rule_every_reader_applies():
    a = {"subject": "cargo_quote", "scenario": "S1", "version": "v1", "versions": {}, "loaded_at": None}
    assert held_state.scenario_for(a, "cargo_quote") == "S1" and held_state.refusal(a, "cargo_quote") is None
    assert held_state.scenario_for(a, "twin") is None and held_state.foreign(a, "twin")
    assert "of subject cargo_quote, not of twin" in held_state.refusal(a, "twin")
    assert held_state.refusal(a, "cargo_quote", "S2") == "the store holds S1, not 'S2'"
    assert held_state.refusal(None, "cargo_quote") == "the store holds no scenario" and not held_state.foreign(None, "x")
    legacy = dict(a, subject=None)
    # more than one subject under KG_SUBJECTS (the public two): unknown, refused for every subject
    with _Env(KG_SUBJECTS=str(ROOT / "subjects")):
        assert held_state.owner(legacy) is None
        assert "unknown subject" in held_state.refusal(legacy, "cargo_quote") and held_state.foreign(legacy, "cargo_quote")
    # the instance's only subject, declaring the held scenario: it is that subject's
    with tempfile.TemporaryDirectory() as td:
        os.symlink(ROOT / "subjects" / "cargo_quote", Path(td) / "cargo_quote")
        with _Env(KG_SUBJECTS=td):
            assert held_state.owner(legacy) == "cargo_quote" and held_state.refusal(legacy, "cargo_quote") is None
            assert held_state.owner(dict(legacy, scenario="D3")) is None, "a scenario the only subject does not declare"


def test_the_load_records_its_subject_and_held_is_a_read_of_the_port_on_both_adapters():
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    assert 'subject=SUBJECT.id, scenario=scenario)' in load.split("def load_scenario(", 1)[1].split("\ndef ", 1)[0]
    assert "held" in store.READS
    import mcp_server
    assert "held" in mcp_server.READS
    for path, cls in (("store_neo4j.py", "Neo4jStore"), ("store_rdflib.py", "RdflibStore")):
        src = (ROOT / "harness" / path).read_text(encoding="utf-8")
        assert "    def held(self)" in src and "held_from(acts, current)" in src and "CURRENT" in src, path


def test_no_reader_parses_the_activity_id_any_more():
    """The five ``split(":")[2]`` parsers and held_version's ``[3]`` are gone; the one read of an id is
    store.held_from's, for a store loaded before the subject was recorded."""
    found = []
    for base in ("harness", "demo/app", "tools"):
        for p in sorted((ROOT / base).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r'split\(":"\)\[[23]\]', line):
                    found.append(f"{p.relative_to(ROOT)}:{i}")
    assert found == ["harness/store.py:" + str(_line(ROOT / "harness" / "store.py", 'a["id"].split(":")[2]'))], found


def _line(path: Path, text: str) -> int:
    return next(i for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if text in line)


def test_both_workflows_run_the_check_and_the_round_trip_carries_the_subject():
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "KG_STORE=rdflib python tools/check_held_subject.py --disposable" in harness
    assert "docker compose exec -T app python tools/check_held_subject.py --disposable" in demo
    RdflibStore = need_rdflib().RdflibStore
    st = RdflibStore(path="")
    st.create_node("agent:harness", "Agent", {})
    st.create_activity("act:extract:S1:v1", "extraction", "2026-11-07T08:00:00+00:00", "t", "", "agent:harness", subject="twin", scenario="S1")
    back = RdflibStore(path="")
    back.import_turtle(st.export_turtle())
    assert back.held()["subject"] == "twin" and back.held()["scenario"] == "S1"

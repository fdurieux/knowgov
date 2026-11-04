"""Guards for demo/: the report view builds from the vendored record for every
scenario, the systemic view renders, the vendored model and the layout tables
are the ones model/SOURCE.md names, and the image pins the record's versions.
Standard library only; nothing here touches a store or the network."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
APP = DEMO / "app"
RESULTS = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results"   # the vendored record
NO_RUNS = ROOT / "nonexistent-demo-runs"

sys.path.insert(0, str(APP))
import cascade  # noqa: E402
import views  # noqa: E402

sys.path.insert(0, str(DEMO / "tools"))
import compare_deterministic  # noqa: E402

sys.path.insert(0, str(DEMO / "model"))
import cascade_layout as slide  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _subject_pin import on_cargo_quote  # noqa: E402  (these tests are about CargoQuote's record; task-0032.01)


@on_cargo_quote
def test_every_scenario_replays_from_the_record():
    for sc in views.ORDER:
        v = views.build(sc, views.default_source(sc), NO_RUNS)
        assert [s["id"] for s in v["stages"]] == ["ingest", "extract", "load", "rules", "gaps", "gate"], sc
        assert v["gate"]["verdict"] == views.SCENARIOS[sc]["gate"], (sc, v["gate"])
        assert v["required_keys"] == 36, sc
        for arm in ("G", "B"):
            assert v["arms"][arm]["summary"]["n"] == 5, (sc, arm)
        assert v["bundle"] and v["bundle"].startswith("GATE VERDICT: "), sc
        assert v["stage2" if sc == "S6" else "scenario"]


@on_cargo_quote
def test_s6_sources_and_stage_two():
    rerun = views.build("S6", "rerun", NO_RUNS)
    assert views.default_source("S6") == "rerun"
    assert [x["key"] for x in rerun["stage2"]["invalidated"]] == ["P2|surcharge", "P2|threshold", "worked_example|price", "P3|order"]
    assert rerun["stage2"]["kept"] == 31
    assert rerun["stage2"]["gate_before"]["verdict"] == "BLOCKED" and rerun["stage2"]["gate_after"]["verdict"] == "PROCEED"
    assert rerun["stage2"]["suspect_derived"] == [{"id": "derived:S1:G:run1", "suspect": True}]
    d3 = views.build("S6", "d3check", NO_RUNS)
    assert d3["stage2"]["suspect_derived"] == [] and d3["arms"]["G"]["summary"]["n"] == 0
    assert {s["id"] for s in rerun["sources"]} == {"record", "rerun", "d3check"}


@on_cargo_quote
def test_demo_runs_are_listed_as_sources(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        runs = Path(td)
        (runs / "2026-10-30-1200" / "S4").mkdir(parents=True)
        (runs / "2026-10-30-1200" / "S4" / "deterministic.json").write_bytes((RESULTS / "S4" / "deterministic.json").read_bytes())
        v = views.build("S4", "demo-runs/2026-10-30-1200", runs)
        assert v["source_dir"].endswith("S4") and v["arms"]["G"]["summary"]["n"] == 0
        assert any(s["id"] == "demo-runs/2026-10-30-1200" and "(deterministic)" in s["label"] for s in v["sources"])


@on_cargo_quote
def test_systemic_placements_use_the_models_nodes_and_edges():
    node_ids = set(slide.nodes)
    edge_pairs = {(a, b) for _, a, b in slide.edges}
    for sc, spec in views.SYSTEMIC.items():
        assert spec["entry"] in node_ids or spec["entry"] is None, sc
        for arm in ("G", "B"):
            a = spec[arm]
            assert a["stop"] in node_ids or a["stop"] is None, (sc, arm)
            path = a["path"]
            for x, y in zip(path, path[1:]):
                assert (x, y) in edge_pairs, (sc, arm, x, y)
            assert a["note"]


def test_every_cascade_renders_well_formed_svg():
    for sc in views.ORDER:
        for arm in ("G", "B"):
            svg = cascade.render(views.SYSTEMIC[sc], arm, title=f"{sc} {arm}")
            xml.dom.minidom.parseString(svg)
            assert svg.startswith("<svg") and "People and intent" in svg, (sc, arm)
            assert "<title>Knowledge held only by people: " in svg and ". Click for this node" in svg, "a node's hover carries the model's definition"
            if views.SYSTEMIC[sc]["entry"]:
                assert "defect enters here" in svg, (sc, arm)


def test_vendored_model_matches_its_source_note():
    model_path = DEMO / "model" / "model.json"
    note = (DEMO / "model" / "SOURCE.md").read_text(encoding="utf-8")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    assert digest in note, "SOURCE.md must carry the sha256 of the vendored model.json"
    m = json.loads(model_path.read_text(encoding="utf-8"))
    assert m["version"] == "0.3" and f"version | 0.3" in note
    assert re.search(r"commit \| `[0-9a-f]{40}`", note)
    assert len(m["edges"]) == 79 and len(m["nodes"]) == 51


def test_layout_tables_match_their_source_note():
    """demo/model/cascade_layout.py is a byte-for-byte copy of the deck generator in pumllint
    that model/SOURCE.md names; the note carries its sha256."""
    note = (DEMO / "model" / "SOURCE.md").read_text(encoding="utf-8")
    digest = hashlib.sha256((DEMO / "model" / "cascade_layout.py").read_bytes()).hexdigest()
    assert digest in note, "SOURCE.md must carry the sha256 of cascade_layout.py"
    assert "gen_cascade_slide.py" in note
    assert slide.W == 1664 and len(slide.nodes) >= 10 and slide.edges


def test_compare_tool_finds_the_record_identical_to_itself():
    n, lines = compare_deterministic.compare(RESULTS, RESULTS, compare_deterministic.SCENARIOS,
                                             record_for={"S6": RESULTS / "S6"})
    assert n == 0, lines
    # and the deterministic-mode S6 record differs from the scored one by the Derived node and by
    # valid_until on the three ended verifications (the scored run's loader reset it, d3check/S6 is
    # the re-establishment after the fix: pumllint's pre-registration, run notes, "a third harness
    # defect"); by default the comparator reports that leaf, as it does every non-volatile one
    n, lines = compare_deterministic.compare(RESULTS / "d3check", RESULTS, ["S6"], record_for={"S6": RESULTS / "S6"})
    assert n > 0 and all("derived" in ln.lower() or "census_after" in ln or "valid_until" in ln or "S6" in ln for ln in lines), lines
    stale = [ln for ln in lines if ".stale[" in ln]
    assert len(stale) == 3 and all("'valid_until': None" in ln.split("record=")[1] or '"valid_until": null' in ln.split("record=")[1] for ln in stale), stale
    # set aside on request, only the Derived node remains between the two
    n2, lines2 = compare_deterministic.compare(RESULTS / "d3check", RESULTS, ["S6"], record_for={"S6": RESULTS / "S6"},
                                               ignore_keys=["valid_until"])
    assert 0 < n2 == n - 3 and not [ln for ln in lines2 if ".stale[" in ln], lines2
    assert "valid_until" not in compare_deterministic.VOLATILE_KEYS, "the default comparison keeps reading it"


def _derived_registering_s6(td: Path, name: str) -> Path:
    """What a deterministic S6 writes since the runner copies S1's code into the run folder:
    the scored record's deterministic.json with the ended verifications carrying the new tag,
    which is what r_stale sets and what the scored run's loader reset to null."""
    det = json.loads((RESULTS / "S6" / "deterministic.json").read_text(encoding="utf-8"))
    assert det["stage2"]["suspect_derived"], "the scored record registered the Derived"
    for x in det["stage2"]["gate_after_reverification"]["stale"]:
        for v in x["verifications"]:
            assert v["valid_until"] is None, "the record holds the defect's null"
            v["valid_until"] = "v2"
    d = td / "demo-runs" / name / "S6"
    d.mkdir(parents=True)
    (d / "deterministic.json").write_text(json.dumps(det), encoding="utf-8")
    return d


@on_cargo_quote
def test_record_check_sets_the_scored_records_valid_until_aside_for_a_derived_registering_run():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = _derived_registering_s6(Path(td), "2026-11-01-1200")
        # the comparator by itself still sees the three leaves: the command line is unchanged
        n, lines = compare_deterministic.compare(d.parent, RESULTS, ["S6"], record_for={"S6": RESULTS / "S6"})
        assert n == 3 and all(".stale[" in ln for ln in lines if ln.startswith("  ")), lines
        # the page reads the run against the scored record with that leaf set aside, and says so
        rc = views.record_check("S6", d, "demo-runs/2026-11-01-1200")
        assert rc["differ"] == 0 and rc["compared"] > 100 and rc["against"].endswith("results/S6"), rc
        assert rc["aside"] == ["valid_until"] == views.SUBJECT.scenarios["S6"]["scored_record_volatile"]
        v = views.build("S6", "demo-runs/2026-11-01-1200", Path(td) / "demo-runs")
        text = " ".join(v["narrative"])
        assert "identical on all" in text and "timestamps and valid_until aside" in text, text
        # any other leaf still counts: the run's stage-2 verdict is not set aside
        det = json.loads((d / "deterministic.json").read_text(encoding="utf-8"))
        det["stage2"]["gate_after_reverification"]["verdict"] = "BLOCKED"
        (d / "deterministic.json").write_text(json.dumps(det), encoding="utf-8")
        rc = views.record_check("S6", d, "demo-runs/2026-11-01-1200")
        assert rc["differ"] == 1 and "gate_after_reverification.verdict" in rc["lines"][0], rc
        # a run that registered no Derived goes to the deterministic-mode record with nothing aside
        d2 = Path(td) / "demo-runs" / "2026-11-01-1300" / "S6"; d2.mkdir(parents=True)
        d2.joinpath("deterministic.json").write_bytes((RESULTS / "d3check" / "S6" / "deterministic.json").read_bytes())
        rc = views.record_check("S6", d2, "demo-runs/2026-11-01-1300")
        assert rc["differ"] == 0 and rc["against"].endswith("d3check/S6") and rc["aside"] == [], rc
        assert "timestamps aside" in " ".join(views.build("S6", "demo-runs/2026-11-01-1300", Path(td) / "demo-runs")["narrative"])


def test_compare_tool_command_line_reads_every_leaf():
    """The CLI has no way to set a leaf aside: a derived-registering run against the scored
    record exits 1 with the three valid_until leaves, as before (the page is the one reader
    that sets them aside, and only against that record)."""
    import contextlib, io, tempfile
    with tempfile.TemporaryDirectory() as td:
        d = _derived_registering_s6(Path(td), "2026-11-01-1400")
        argv, out = sys.argv, io.StringIO()
        try:
            sys.argv = ["compare_deterministic.py", str(d.parent), "--scenarios", "S6", "--record-for", f"S6={RESULTS / 'S6'}"]
            with contextlib.redirect_stdout(out):
                code = compare_deterministic.main()
        finally:
            sys.argv = argv
        text = out.getvalue()
        assert code == 1 and "DIFF: 3 differing" in text and text.count("valid_until") >= 3, text


def test_image_pins_the_versions_the_record_names():
    # pumllint docs/neo4j-governed-knowledge-evaluation.md §12, the record's versions
    named = {"neo4j": "6.4.1", "rdflib": "7.6.0", "pyshacl": "0.40.2", "openai": "3.41.0"}
    dockerfile = (DEMO / "Dockerfile").read_text(encoding="utf-8")
    for pkg, ver in named.items():
        assert f'"{pkg}=={ver}"' in dockerfile, (pkg, ver)
    assert "pip install -e ." not in dockerfile and '"pumllint==0.33.0"' in dockerfile, "pumllint is a pinned library here, not a checkout"
    # the J-F subject's oracle: its kit's pins (contracts/pins.md) and the suite's tooling, on the interpreter the kit names
    assert "FROM python:3.12-slim" in dockerfile
    for pkg, ver in {"pandas": "3.0.5", "numpy": "2.4.6", "requests": "2.34.2", "pyarrow": "25.0.1", "pytest": "9.1.1", "pytest-bdd": "9.0.1"}.items():
        assert f'"{pkg}=={ver}"' in dockerfile, (pkg, ver)
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert 'python-version: "3.12"' in harness and '"pandas==3.0.5"' in harness and "jef_suite.py" in harness
    assert 'CMD ["python", "demo/app/server.py"]' in dockerfile and "KG_DEMO_RUNS=/repo/runs" in dockerfile


def test_the_mcp_server_adds_no_dependency_to_the_image():
    """task-0056: the MCP server is standard library and the harness's own modules, so the image
    gains no package for it; were it ever to need one, the pin would belong in the list above."""
    import ast
    harness = {p.stem for p in (ROOT / "harness").glob("*.py")}
    tree = ast.parse((ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8"))
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module and n.level == 0}
    foreign = {m for m in mods - harness - {"__future__"} if m not in sys.stdlib_module_names}
    assert not foreign, foreign
    dockerfile = (DEMO / "Dockerfile").read_text(encoding="utf-8")
    assert '"mcp' not in dockerfile and "fastmcp" not in dockerfile


def test_compose_files_agree():
    compose = (DEMO / "docker-compose.yml").read_text(encoding="utf-8")
    override = (DEMO / "docker-compose.override.yml").read_text(encoding="utf-8")
    assert re.search(r"image: ghcr\.io/fdurieux/knowgov:v\d+\.\d+\.\d+@sha256:[0-9a-f]{64}", compose), "the app image is a release, pinned by digest (task-0092)"
    assert "neo4j:5.26-community" in compose and "condition: service_healthy" in compose
    assert "OPENAI_API_KEY: ${OPENAI_API_KEY:-}" in compose, "the key is passed through, never baked in"
    assert "KG_REGISTER: ${KG_REGISTER:-/repo/demo/register}" in compose, "one register per organisation: the root is configuration"
    # task-0031: the three published ports are variables with today's defaults, so a second stack for
    # another subject runs beside the default one under its own project name; the README shows it
    for var, port in (("KG_PORT_APP", 8080), ("KG_PORT_BROWSER", 7474), ("KG_PORT_BOLT", 7687)):
        assert f'${{{var}:-{port}}}:{port}"' in compose, var
    readme = (DEMO / "README.md").read_text(encoding="utf-8")
    assert "docker compose -p knowgov-jef up" in readme and "KG_PORT_APP=8081" in readme and "KG_BROWSER_URL=http://localhost:7475" in readme
    instance = (DEMO / "docker-compose.instance.yml").read_text(encoding="utf-8")
    assert "KG_REGISTER: /instance/register" in instance and ":/instance:ro" in instance and "docker compose -f docker-compose.yml" in instance
    assert "dockerfile: demo/Dockerfile" in override and "context: .." in override
    workflow = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "ghcr.io/fdurieux/knowgov:${{ steps.sha.outputs.short }}" in workflow
    assert "packages: write" in workflow and "compare_deterministic.py" in workflow



def test_the_ports_bind_loopback_and_a_wider_bind_refuses_the_default_password():
    """Task-0090: every port a compose file publishes carries the host address ${KG_BIND:-127.0.0.1},
    and Neo4j starts through the guard, which refuses a wider bind while the password is the default
    and otherwise hands over to the image's own entrypoint."""
    import subprocess
    for path in sorted(DEMO.glob("docker-compose*.yml")):
        text = path.read_text(encoding="utf-8")
        for block in re.findall(r"\n    ports:\n((?:      - .*\n)+)", text):
            for line in block.splitlines():
                assert line.strip().startswith('- "${KG_BIND:-127.0.0.1}:'), (path.name, line)
    compose = (DEMO / "docker-compose.yml").read_text(encoding="utf-8")
    neo4j = compose.split("\n  neo4j:\n", 1)[1].split("\n  app:\n", 1)[0]
    assert '"/bin/sh", "/knowgov/bind-guard.sh", "tini", "-g", "--", "/startup/docker-entrypoint.sh"' in neo4j
    assert 'command: ["neo4j"]' in neo4j and "./neo4j/bind-guard.sh:/knowgov/bind-guard.sh:ro" in neo4j
    assert "KG_BIND: ${KG_BIND:-127.0.0.1}" in neo4j
    guard = DEMO / "neo4j" / "bind-guard.sh"

    def run(bind, auth):
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "NEO4J_AUTH": auth}
        if bind is not None:
            env["KG_BIND"] = bind
        return subprocess.run(["sh", str(guard), "echo", "started"], env=env, capture_output=True, text=True)

    for bind in (None, "127.0.0.1", "localhost", "[::1]"):
        r = run(bind, "neo4j/kgpoc2026")
        assert r.returncode == 0 and r.stdout.strip() == "started", (bind, r.stderr)
    for bind in ("0.0.0.0", "[::]", "192.0.2.10"):
        r = run(bind, "neo4j/kgpoc2026")
        assert r.returncode == 78 and "started" not in r.stdout and "KG_NEO4J_PASSWORD" in r.stderr, (bind, r)
        r = run(bind, "neo4j/example-not-the-default")
        assert r.returncode == 0 and r.stdout.strip() == "started", (bind, r.stderr)
    readme = (DEMO / "README.md").read_text(encoding="utf-8")
    assert "KG_BIND=0.0.0.0" in readme and "127.0.0.1" in readme

def test_readme_paste_block_is_zsh_safe():
    text = (DEMO / "README.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    block = max(blocks, key=len)
    assert "docker compose up" in block
    assert "#" not in block and "!" not in block, "a pasted zsh block must carry no # and no !"
    for tool in ("git", "docker"):
        assert f"command -v {tool}" in block


@on_cargo_quote
def test_arms_model_defaults_to_the_records_and_is_overridable():
    """The harness's model comes from KG_ARMS_MODEL with the record's model as the
    default, the view names the same record model, and the page offers the toggle."""
    arms = (ROOT / "harness" / "arms.py").read_text(encoding="utf-8")
    assert "RECORD_MODEL = SUBJECT.record_model" in arms, "the record's model is the subject's"
    assert views.RECORD_MODEL == views.SUBJECT.record_model == "gpt-5.1-2025-11-13"
    assert 'MODEL = os.environ.get("KG_ARMS_MODEL") or RECORD_MODEL' in arms
    page = (APP / "index.html").read_text(encoding="utf-8")
    assert 'id="am-row"' in page and 'id="am-effort"' in page, "task-0029: a drop-down of rows and one of the row's efforts"
    assert "Model deviation" in page
    compose = (DEMO / "docker-compose.yml").read_text(encoding="utf-8")
    assert "KG_ARMS_MODEL: ${KG_ARMS_MODEL:-}" in compose
    # a run answered by another model is a deviation; the record's runs are not
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "2026-10-30-1700" / "S1"; d.mkdir(parents=True)
        shutil.copy(RESULTS / "S1" / "deterministic.json", d / "deterministic.json")
        rec = json.loads((RESULTS / "S1" / "run1_G.json").read_text(encoding="utf-8"))
        rec["usage"]["model"] = "gpt-5.5-2026-04-01"
        (d / "run1_G.json").write_text(json.dumps(rec), encoding="utf-8")
        v = views.build("S1", "demo-runs/2026-10-30-1700", Path(td))
        assert v["model_deviation"] == ["gpt-5.5-2026-04-01"] and v["arms"]["G"]["runs"][0]["model"] == "gpt-5.5-2026-04-01"
        assert any("gpt-5.5-2026-04-01" in s_["label"] for s_ in v["sources"])
        # task-0028: an effort other than the record's ("" here, the API default) is a deviation too, named in the narrative
        assert v["effort_deviation"] == [] and v["record_effort"] == ""
        rec["usage"]["model"] = "gpt-5.1-2025-11-13"; rec["usage"]["effort"] = "high"
        (d / "run1_G.json").write_text(json.dumps(rec), encoding="utf-8")
        v = views.build("S1", "demo-runs/2026-10-30-1700", Path(td))
        assert v["model_deviation"] == [] and v["effort_deviation"] == ["high"]
        assert any("ran at effort high, not the record's API default" in s_ for s_ in v["narrative"]), v["narrative"]
    assert views.build("S1", "record", NO_RUNS)["model_deviation"] == [] and views.build("S1", "record", NO_RUNS)["effort_deviation"] == []
    assert "Effort deviation" in page and "effort: mode === 'arms' ? armsEffort()" in page and "row: mode === 'arms' ? (armsRow() || {}).id" in page


def test_models_table_rows_resolve_to_the_harness_variables_and_never_carry_a_key():
    """Task-0029: the operator's rows (demo/models.toml), the record's row first and the instance's
    settings when set; key_set per row, never a value; a row whose variable is empty is listed with
    "set VAR" and refused; an effort the row does not list is refused; resolve() gives the four
    variables the harness reads and whether the run is a deviation from the record."""
    import models
    table = models.load_table()
    assert [r["id"] for r in table][:1] == ["openai-gpt-5.5"] and all("key" not in r and "price" not in r for r in table)
    keep = {k: os.environ.pop(k, None) for k in ("OPENAI_API_KEY", "GEMINI_API_KEY", "KG_MODEL_API_KEY", "KG_MODEL_BASE_URL", "KG_MODEL_API_KEY_VAR", "KG_ARMS_MODEL", "KG_ARMS_EFFORT", "KG_MODELS")}
    try:
        rows = models.rows("gpt-5.1-2025-11-13", "", "reply")
        assert rows[0]["id"] == "record" and [r["id"] for r in rows][1:] == [r["id"] for r in table], "no instance row while the defaults stand"
        assert not any(r["available"] for r in rows) and rows[1]["why"] == "set OPENAI_API_KEY"
        try:
            models.resolve("openai-gpt-5.5", "", "gpt-5.1-2025-11-13", "", "reply"); raise AssertionError("a row without its key ran")
        except ValueError as e:
            assert "set OPENAI_API_KEY" in str(e)
        os.environ["OPENAI_API_KEY"] = "sk-test-not-a-key"
        pub = [models.public(r) for r in models.rows("gpt-5.1-2025-11-13", "", "reply")]
        assert all(r["key_set"] for r in pub if r["key_var"] == "OPENAI_API_KEY") and "sk-test-not-a-key" not in json.dumps(pub)
        # task-0036: the Gemini row is live, on its own key variable, Google's endpoint, both arm kinds, no xhigh
        gem = next(r for r in pub if r["provider"] == "Google")
        assert gem["model"] == "gemini-3.8-flash" and gem["key_var"] == "GEMINI_API_KEY" and not gem["key_set"] and gem["why"] == "set GEMINI_API_KEY"
        assert gem["host"] == "generativelanguage.googleapis.com" and gem["arms"] == ["reply", "agent"] and gem["efforts"] == ["", "low", "medium", "high"]
        row, env, dev = models.resolve("record", None, "gpt-5.1-2025-11-13", "", "reply")
        assert env == {"KG_MODEL_BASE_URL": "https://api.openai.com/v1", "KG_MODEL_API_KEY_VAR": "OPENAI_API_KEY",
                       "KG_ARMS_MODEL": "gpt-5.1-2025-11-13", "KG_ARMS_EFFORT": "", "KG_THINKING_UNCOUNTED": ""} and dev is False
        row, env, dev = models.resolve("openai-gpt-5.5", "high", "gpt-5.1-2025-11-13", "", "reply")
        assert env["KG_ARMS_MODEL"] == "gpt-5.5" and env["KG_ARMS_EFFORT"] == "high" and dev is True
        for bad in (("openai-gpt-5.5", "maximum"), ("record", "high"), ("no-such-row", "")):
            try:
                models.resolve(bad[0], bad[1], "gpt-5.1-2025-11-13", "", "reply"); raise AssertionError(bad)
            except ValueError:
                pass
        # a subject whose record ran no arm: the record's row is listed first, unavailable, with the reason
        rows = models.rows("", "", "agent")
        assert rows[0]["id"] == "record" and not rows[0]["available"] and rows[0]["why"] == "the record ran no arm"
        row, env, dev = models.resolve(None, None, "", "", "agent")
        assert row["id"] == "openai-gpt-5.5" and dev is False, "the first available row, compared with nothing"
        # the three instance variables, set, are a row of their own
        os.environ.update({"KG_MODEL_BASE_URL": "http://gateway.internal:4000/v1", "KG_MODEL_API_KEY_VAR": "KG_MODEL_API_KEY", "KG_ARMS_MODEL": "local-model"})
        rows = models.rows("", "", "reply")
        assert rows[1]["id"] == "custom" and rows[1]["host"] == "gateway.internal:4000" and rows[1]["why"] == "set KG_MODEL_API_KEY"
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        for body in ('[[row]]\nid = "x"\nlabel = "x"\nprovider = "x"\nbase_url = "https://e/v1"\nmodel = "m"\nefforts = [""]\nkey_var = "K"\narms = ["reply"]\napi_key = "sk-oops"\n',
                     '[[row]]\nid = "x"\nlabel = "x"\nprovider = "x"\nbase_url = "https://e/v1"\nmodel = "m"\nefforts = [""]\nkey_var = "sk-live-123"\narms = ["reply"]\n'):
            p = Path(td) / "m.toml"; p.write_text(body, encoding="utf-8")
            try:
                models.load_table(p); raise AssertionError("a key rode in on the table")
            except ValueError:
                pass


@on_cargo_quote
def test_plain_english_narrative_is_built_from_the_files():
    for sc in views.ORDER:
        v = views.build(sc, views.default_source(sc), NO_RUNS)
        text = " ".join(v["narrative"])
        assert views.SCENARIOS[sc]["plain"] in text, sc
        assert "None" not in text and "{" not in text, (sc, text[:200])
        assert f"The gate's verdict is {v['gate']['verdict']}" in text, sc
    assert "invalidated the 4 assertions" in " ".join(views.build("S6", "rerun", NO_RUNS)["narrative"])
    # a deterministic demo run is checked against the record, in words
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "demo-runs" / "2026-10-30-1800" / "S4"; d.mkdir(parents=True)
        shutil.copy(RESULTS / "S4" / "deterministic.json", d / "deterministic.json")
        v = views.build("S4", "demo-runs/2026-10-30-1800", Path(td) / "demo-runs")
        assert v["record_check"]["differ"] == 0 and v["record_check"]["compared"] > 100
        assert "identical on all" in " ".join(v["narrative"]) and "arms were not called" in " ".join(v["narrative"])


def _sentences(text):
    import re
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text.strip()) if s]


def _forbidden_in(sentence):
    import re
    low = sentence.lower()
    return [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", low)]


@on_cargo_quote
def test_generated_prose_keeps_to_the_glossary_and_the_length_limits():
    """Controlled sentences: 20 words, no forbidden synonym. Readings: 25 words,
    no forbidden synonym. Data is exempt. Checked on the text actually produced
    for every scenario, the S6 rerun and a deterministic-only demo run."""
    import tempfile, shutil
    limits = {"controlled": 20, "reading": 25}
    seen = {"controlled": 0, "reading": 0, "data": 0}
    builds = [(sc, views.default_source(sc), NO_RUNS) for sc in views.ORDER] + [("S6", "rerun", NO_RUNS)]
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "demo-runs" / "2026-10-30-1900" / "S2"; d.mkdir(parents=True)
        shutil.copy(RESULTS / "S2" / "deterministic.json", d / "deterministic.json")
        builds.append(("S2", "demo-runs/2026-10-30-1900", Path(td) / "demo-runs"))
        # a run whose load names a stored document no mapper reads (task-0006): the ingest panel's extra section
        d = Path(td) / "demo-runs" / "2026-11-02-2300" / "S2"; d.mkdir(parents=True)
        j = json.loads((RESULTS / "S2" / "deterministic.json").read_text(encoding="utf-8"))
        j["load"]["unmapped"] = ["stories/quote.md"]
        (d / "deterministic.json").write_text(json.dumps(j), encoding="utf-8")
        builds.append(("S2", "demo-runs/2026-11-02-2300", Path(td) / "demo-runs"))
        # a run whose load had a pre-load report (task-0064): the ingest panel lists the verdict per document
        d = Path(td) / "demo-runs" / "2026-11-04-0100" / "S2"; d.mkdir(parents=True)
        j = json.loads((RESULTS / "S2" / "deterministic.json").read_text(encoding="utf-8"))
        j["load"]["preload"] = {"report": "preload-report.json", "documents": [
            {"artefact": "behavior/quote_flow.puml", "version": "v1", "state": "clean", "tool": "pumllint", "tool_version": "0.33.0", "why": "no finding at or above major"},
            {"artefact": "contract/spec.md", "version": "v1", "state": "unchecked", "tool": None, "tool_version": None, "why": "the report does not cover this document"}]}
        (d / "deterministic.json").write_text(json.dumps(j), encoding="utf-8")
        builds.append(("S2", "demo-runs/2026-11-04-0100", Path(td) / "demo-runs"))
        pre = views.build("S2", "demo-runs/2026-11-04-0100", Path(td) / "demo-runs")["details"]["ingest"]["sections"][-1]
        assert pre["heading"] == "Form checked before the load" and pre["table"]["cols"] == ["document", "version", "form", "tool", "why"], pre
        assert pre["table"]["rows"][1][:4] == ["contract/spec.md", "v1", "unchecked", "none"], pre["table"]["rows"]
        assert all(s["heading"] != "Form checked before the load" for s in views.build("S2", views.default_source("S2"), NO_RUNS)["details"]["ingest"]["sections"])
        for sc, src, runs in builds:
            v = views.build(sc, src, runs)
            for item in v["text_registry"]:
                seen[item["kind"]] += 1
                if item["kind"] == "data":
                    continue
                for s in _sentences(item["text"]):
                    n = len(s.split())
                    assert n <= limits[item["kind"]], (sc, src, item["kind"], n, s)
                    assert not _forbidden_in(s), (sc, src, _forbidden_in(s), s)
            # the registry covers what the page shows: narrative, panels, gap kinds
            shown = " ".join(v["narrative"]) + " " + " ".join(v["gaps"]["explain"].values())
            for det in v["details"].values():
                shown += " " + det["title"] + " " + det["intro"] + " " + " ".join(sec["heading"] + " " + sec.get("text", "") for sec in det["sections"])
            for det in v["systemic_details"].values():
                shown += " " + det["title"] + " " + det["intro"] + " " + " ".join(sec["heading"] + " " + sec.get("text", "") for sec in det["sections"])
            boxes = v["stages"] + (v["stage2"]["stages"] if v.get("stage2") else [])
            shown += " " + " ".join(b["label"] + " " + " ".join(b["lines"]) for b in boxes)
            shown += " " + " ".join(" ".join(v["arms"][a][part]["lines"]) for a in ("G", "B") for part in ("generate", "oracle"))
            for item in v["text_registry"]:
                assert item["text"] in shown, (sc, src, item["text"][:80])
    assert seen["controlled"] > 500 and seen["reading"] >= 7 and seen["data"] > 20, seen
    # the pipeline boxes are in the registry too: every label and every line of every box
    v = views.build("S6", "record", NO_RUNS)
    texts = {it["text"] for it in v["text_registry"]}
    for b in v["stages"] + v["stage2"]["stages"]:
        assert b["label"] in texts and all(ln in texts for ln in b["lines"]), b["id"]
    for a in ("G", "B"):
        assert all(ln in texts for part in ("generate", "oracle") for ln in v["arms"][a][part]["lines"]), a
    # the scenario descriptions: the sidebar cards and the Planted line are controlled, the reading is looser
    for sc, meta in views.SCENARIOS.items():
        for field, lim in (("title", 20), ("represented", 20), ("defect", 20), ("plant", 20), ("plain", 25)):
            for s in _sentences(meta[field]):
                assert len(s.split()) <= lim and not _forbidden_in(s), (sc, field, s)
        assert meta["plant"].endswith(".") and meta["defect"].endswith(".") and meta["represented"].endswith("."), sc
    # the systemic placements: the captions' notes and the entry families are controlled too
    for sc, spec in views.SYSTEMIC.items():
        for text in (spec["family"], spec["G"]["note"], spec["B"]["note"]):
            for s in _sentences(text):
                assert len(s.split()) <= 20 and not _forbidden_in(s), (sc, s)
    for texts in (views.RULE_TEXT.values(), views.GAP_KIND_TEXT.values(), views.VERDICT_MEANING.values()):
        for group in texts:
            for s in group:
                assert len(s.split()) <= 20 and not _forbidden_in(s), s


@on_cargo_quote
def test_glossary_document_matches_the_view_tables():
    md = (DEMO / "GLOSSARY.md").read_text(encoding="utf-8")
    for term, meaning in views.GLOSSARY.items():
        assert f"| {term} |" in md, term
        assert meaning in md, term
    for syn in views.FORBIDDEN:
        assert syn in md, syn
    assert "ASD-STE100" in md and "20" in md and "25" in md
    page = (DEMO / "app" / "index.html").read_text(encoding="utf-8")
    assert "v.glossary" in page and "GLOSSARY.md" in page
    # the page's own strings obey the glossary too (data from the files is not in the page source)
    import re
    for syn in views.FORBIDDEN:
        assert not re.search(r"\b" + re.escape(syn) + r"\b", page, re.I), syn
    assert "GLOSSARY.md" in (DEMO / "README.md").read_text(encoding="utf-8")


@on_cargo_quote
def test_every_pipeline_box_has_a_detail_panel():
    for sc in views.ORDER:
        v = views.build(sc, views.default_source(sc), NO_RUNS)
        ids = [st["id"] for st in v["stages"]] + [f"{part}_{arm}" for part in ("generate", "oracle") for arm in ("G", "B")]
        if sc == "S6":
            ids += [st["id"] for st in v["stage2"]["stages"]]
        for i in ids:
            d = v["details"][i]
            assert d["title"] and d["intro"] and isinstance(d["sections"], list), (sc, i)
            for sec in d["sections"]:
                assert sec["heading"], (sc, i)
                if "table" in sec:
                    assert all(len(r) == len(sec["table"]["cols"]) for r in sec["table"]["rows"]), (sc, i, sec["heading"])
        assert len(v["details"]["gate"]["sections"][1]["table"]["rows"]) == 36, sc
    s4 = views.build("S4", "record", NO_RUNS)["details"]["rules"]
    assert any(sec.get("table") and len(sec["table"]["rows"]) == 4 for sec in s4["sections"] if sec["heading"].startswith("R-CONFLICT"))


@on_cargo_quote
def test_gaps_view_matches_the_census_by_kind():
    for sc in views.ORDER:
        v = views.build(sc, views.default_source(sc), NO_RUNS)
        g = v["gaps"]
        from_groups = {"missing": g["counts"]["declared missing"] + g["counts"]["undeclared missing"],
                       "ambiguous": g["counts"]["ambiguous"], "conflict": g["counts"]["conflict"], "unverified": g["counts"]["unverified"]}
        assert {k: n for k, n in from_groups.items() if n} == g["census"], (sc, from_groups, g["census"])
        assert len(g["groups"]["ambiguous"]) == g["census"].get("ambiguous", 0), sc
        assert len(g["groups"]["conflict"]) == g["census"].get("conflict", 0), sc
        assert len(g["groups"]["declared missing"]) + len(g["groups"]["undeclared missing"]) == g["census"].get("missing", 0), sc
        for k, rows in g["groups"].items():
            assert k in g["explain"]
            for r in rows:
                assert r["id"].startswith("gap:") and r["text"], (sc, k, r)
        assert len(g["required_keys"]) == 36
    s4 = views.build("S4", "record", NO_RUNS)["gaps"]["groups"]["conflict"]
    assert all(r["sides"] and r["sides"]["key"] == "QuoteAPI|on_screening_outage" for r in s4)
    s7 = views.build("S7", "record", NO_RUNS)["gaps"]["unverified"]
    assert s7["count"] == 145 and len(s7["required_below_verified"]) == 36


@on_cargo_quote
def test_every_systemic_node_has_a_panel():
    for sc in views.ORDER:
        v = views.build(sc, views.default_source(sc), NO_RUNS)
        sd = v["systemic_details"]
        assert set(sd) == set(slide.nodes), sc
        for nid, d in sd.items():
            assert d["title"] and d["intro"] and d["sections"], (sc, nid)
            heads = [sec["heading"] for sec in d["sections"]]
            assert any(h.startswith("Edges in the model") for h in heads) and any(h.startswith("Arm G") for h in heads) and any(h.startswith("Arm B") for h in heads), (sc, nid)
            edges = next(sec for sec in d["sections"] if sec["heading"].startswith("Edges in the model"))["table"]
            for r in edges["rows"]:   # the edge, from and to explain themselves on hover; no reference, the panel wires none
                for c in (r[0], r[1], r[2]):
                    assert "ref" not in c and c["text"] and c["tip"], (sc, nid, c)
                assert r[5]["text"] and r[5]["tip"], (sc, nid, r[5])   # M, H, or a composite the model writes
            for sec in d["sections"]:
                if "table" in sec:
                    assert all(len(r) == len(sec["table"]["cols"]) for r in sec["table"]["rows"]), (sc, nid, sec["heading"])
        # the entry node says so, for both arms
        entry = views.SYSTEMIC[sc]["entry"]
        if entry:
            for sec in sd[entry]["sections"]:
                if sec["heading"].startswith("Arm "):
                    assert "entered the model here" in sec["text"], (sc, sec["heading"])
        # every node is clickable in both drawings
        for arm in ("G", "B"):
            svg = cascade.render(views.SYSTEMIC[sc], arm)
            assert all(f'data-node="{nid}"' in svg for nid in slide.nodes), (sc, arm)
    s3 = views.build("S3", "record", NO_RUNS)["systemic_details"]["deriveddef"]
    assert any(sec.get("table") and len(sec["table"]["rows"]) == 17 for sec in s3["sections"])
    s4 = views.build("S4", "record", NO_RUNS)["systemic_details"]["explderived"]
    assert any(sec.get("table") and len(sec["table"]["rows"]) == 4 for sec in s4["sections"])
    s6 = views.build("S6", "record", NO_RUNS)["systemic_details"]["drift"]
    assert any(sec.get("table") and len(sec["table"]["rows"]) == 4 for sec in s6["sections"])
    s2 = views.build("S2", "record", NO_RUNS)["systemic_details"]["unknown"]
    assert any(sec.get("list") and any(x.startswith("B run 1, question") for x in sec["list"]) for sec in s2["sections"])
    page = (DEMO / "app" / "index.html").read_text(encoding="utf-8")
    assert "systemic-detail" in page and "wireSystemic" in page


def test_vendored_register_matches_its_source_note_and_checks_clean():
    """demo/register/ is a byte-for-byte copy of fdurieux/ieam-register at the
    commit SOURCE.md names: every file's sha256 is in the note, the note lists no file that is
    missing, and the register's own checker reads the copy clean at the pinned date."""
    import datetime as dt
    import hashlib
    import importlib.util
    import re
    reg = DEMO / "register"
    note = (reg / "SOURCE.md").read_text(encoding="utf-8")
    files = sorted(p for p in reg.rglob("*") if p.is_file() and p.name != "SOURCE.md" and "__pycache__" not in p.parts)
    assert len(files) >= 50
    for p in files:
        rel = p.relative_to(reg).as_posix()
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        assert f"| `{rel}` | `{digest}` |" in note, f"{rel} is not in SOURCE.md with its digest"
    listed = set(re.findall(r"^\| `([^`]+)` \| `[0-9a-f]{64}` \|$", note, re.M))
    assert listed == {p.relative_to(reg).as_posix() for p in files}, "SOURCE.md lists files the copy does not hold"
    assert re.search(r"\| commit \| `[0-9a-f]{40}`", note)
    pinned = re.search(r"pinned date for the checker \| `(\d{4}-\d{2}-\d{2})`", note).group(1)
    spec = importlib.util.spec_from_file_location("vendored_check_register", reg / "tools" / "check_register.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    findings, summary = mod.run(reg, today=dt.date.fromisoformat(pinned))
    assert [f for f in findings.items if f["level"] == "error"] == [], findings.items
    assert summary["nodes"] == 57 and summary["links"] == 65
    assert summary["C1"]["uncovered"] == [] and summary["C1"]["excepted"] == 1
    assert summary["C2"]["uncovered"] == [] and summary["C3"]["uncovered"] == []



@on_cargo_quote
def test_run_tables_show_other_tokens_and_say_when_thinking_goes_uncounted():
    """Task-0034: the per-run table shows the tokens the endpoint counts beyond prompt and reply, and
    says so in a sentence when the endpoint leaves thinking out of streamed usage; no dollar column."""
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "demo-runs" / "2026-11-02-2100" / "S1"; d.mkdir(parents=True)
        shutil.copy(RESULTS / "S1" / "deterministic.json", d / "deterministic.json")
        rec = json.loads((RESULTS / "S1" / "run1_G.json").read_text(encoding="utf-8"))
        rec["usage"].update(hidden_tokens=212, thinking_uncounted=True)
        (d / "run1_G.json").write_text(json.dumps(rec), encoding="utf-8")
        v = views.build("S1", "demo-runs/2026-11-02-2100", Path(td) / "demo-runs")
    sec = v["details"]["generate_G"]["sections"][0]
    assert "other tokens" in sec["table"]["cols"] and "est. $" not in sec["table"]["cols"]
    assert sec["table"]["rows"][0][sec["table"]["cols"].index("other tokens")] == "212"   # cells are strings
    assert "leaves thinking out of streamed usage" in sec["text"]
    assert v["arms"]["G"]["summary"]["tokens"] >= rec["usage"]["prompt_tokens"] + rec["usage"]["completion_tokens"] + 212


def test_the_claude_row_goes_through_a_pinned_gateway_started_only_by_its_profile():
    """Task-0035: the gateway is a compose service behind the profile "claude", its image pinned by
    tag and digest; its config names the upstream model as the alias, adds the cache marks, and reads
    both keys by name; the Claude row points at it with the gateway's key; no key in any file."""
    import re
    compose = (DEMO / "docker-compose.yml").read_text(encoding="utf-8")
    svc = compose.split("\n  litellm:\n", 1)[1].split("\nvolumes:", 1)[0]
    assert 'profiles: ["claude"]' in svc and re.search(r"image: ghcr\.io/berriai/litellm:v[\d.]+@sha256:[0-9a-f]{64}", svc)
    assert "KG_ANTHROPIC_KEY: ${KG_ANTHROPIC_KEY:-}" in svc and "LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY:-}" in svc and "./litellm/config.yaml:/app/config.yaml:ro" in svc
    assert "ANTHROPIC_API_KEY" not in compose.replace("KG_ANTHROPIC_KEY", ""), "never the name a Claude Code session reads"
    assert "depends_on:\n      litellm" not in compose, "the app starts without the gateway"
    cfg = (DEMO / "litellm" / "config.yaml").read_text(encoding="utf-8")
    assert "model_name: claude-sonnet-5-5" in cfg and "model: anthropic/claude-sonnet-5-5" in cfg, "the alias is the upstream name"
    assert "api_key: os.environ/KG_ANTHROPIC_KEY" in cfg and "master_key: os.environ/LITELLM_MASTER_KEY" in cfg
    assert "cache_control_injection_points" in cfg and "role: system" in cfg and "index: -1" in cfg
    assert not re.search(r"sk-ant-|sk-[A-Za-z0-9]{20,}", cfg + compose), "no key value in a file"
    import models
    row = next(r for r in models.load_table() if r["id"] == "anthropic-claude-sonnet-5-5")
    assert row["base_url"] == "http://litellm:4000/v1" and row["model"] == "claude-sonnet-5-5" and row["key_var"] == "LITELLM_MASTER_KEY"
    assert row["arms"] == ["reply", "agent"] and not row["thinking_uncounted"]
    readme = (DEMO / "README.md").read_text(encoding="utf-8")
    assert "docker compose --profile claude up" in readme and "KG_ANTHROPIC_KEY" in readme and "LITELLM_MASTER_KEY" in readme

"""register_impact reads each key as gate_verdict reports it (task-0260, doc-0032 group 3 CB1), on the store KG_STORE
names (rdflib persisted to a file under OUT_DIR), the public example instance built under OUT_DIR:

    python tools/check_owned_findings.py OUT_DIR

1. Group 3's reproduction. employee-1 answers ORG-0002's S2 questionnaire (a capture); employee-2 approves the
   first and third answers (a review); the review file's digest for the first, on ``QuoteAPI|on_screening_outage``,
   is then changed, so that ruling no longer binds. S2 published. ``gate_verdict`` lists the act finding
   (major) on the key; ``register_impact`` from ENT-0003 lands the key and lists the same act finding, as it lists
   the key, stale and lapsed ones, and its answer is valid under ``register-impact.schema.json``.
2. S1, S4 and S6 published as they are: on every landed key of every node the subject's register map names,
   register_impact's findings equal gate_verdict's findings of the owned kinds for that key, over the same key set,
   task and as_of.

Both read the store the gate published, through the MCP server's tools and a read handle. Exit 0 when all hold.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import check_review_walkthrough as w  # noqa: E402  (its instance, answers and review files: one fixture)
import review  # noqa: E402

ON = w.ON
KEY = "QuoteAPI|on_screening_outage"   # employee-1's first answer
NODE = "ENT-0003"

PROBE = """
import json, sys
sys.path.insert(0, '.')
import mcp_server, schema_check
nodes, as_of = json.loads(sys.argv[1]), sys.argv[2]
tools = mcp_server.Tools(as_of=as_of)
schema = schema_check.load("register-impact")
out = {}
for node in nodes:
    ri = tools.register_impact({"node": node, "as_of": as_of})
    keys = [k["key"] for k in ri["keys"]]
    gv = tools.gate_verdict({"keys": keys, "as_of": as_of}) if keys else {"findings": []}
    out[node] = {"impact": {k["key"]: k.get("findings") for k in ri["keys"]}, "gate": gv["findings"],
                 "invalid": schema_check.validate(json.loads(json.dumps(ri, default=str)), schema)[:3]}
print(json.dumps(out))
"""


def gate(env: dict, scenario: str) -> None:
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", scenario, "--as-of", ON, "--publish", "-f", "json"],
                       cwd=w.HARNESS, env=env, capture_output=True, text=True)
    if p.returncode == 2:
        sys.exit(f"FAIL: gate_cli --scenario {scenario} --publish could not run:\n{p.stderr[-2000:]}")


def read(env: dict, nodes: list[str]) -> dict:
    p = subprocess.run([sys.executable, "-c", PROBE, json.dumps(nodes), ON], cwd=w.HARNESS, env=env, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAIL: the MCP tools could not read the published store:\n{p.stderr[-2000:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def differences(got: dict) -> list[str]:
    """Each landed key whose register_impact findings are not gate_verdict's of the owned kinds for that key."""
    import gate_cli
    out = []
    for node, r in got.items():
        if r["invalid"]:
            out.append(f"{node}: register_impact's answer is not valid under its schema: {r['invalid']}")
        for key, mine in r["impact"].items():
            want = [f for f in r["gate"] if f["kind"] in gate_cli.OWNED and f["key"] == key]
            if mine != want:
                out.append(f"{node} {key}: register_impact {[f['kind'] for f in mine or []]}, gate_verdict {[f['kind'] for f in want]}")
    return out


def main(out: Path) -> int:
    errs: list[str] = []
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("KG_STORE", "neo4j") == "rdflib":
        os.environ.setdefault("KG_RDFLIB_FILE", str(out / "store.ttl"))

    print("== 1: group 3's reproduction: a capture, a review whose digest does not bind, S2 published")
    env = review.pinned(w.instance(out, "s2", decided=True), ON)   # every command on the walkthrough's day (task-0075)
    d = out / "s2"
    cap = w.answer(env, d)
    got = w.expect(env, 0, "2 ruling(s)", "capture.py", "review",
                   str(w.write_review(d / "r-2.toml", "employee-2", "S2", [(f"{cap}:{i}@capture", "approved") for i in (1, 3)])))
    written = Path(re.search(r"into (\S+\.toml)", got).group(1))
    text = written.read_text(encoding="utf-8")
    ruling = text[text.index(f'assertion = "{cap}:1@capture"'):]
    key = re.search(r'key = "([^"]+)"', ruling).group(1)
    digest = re.search(r'sha256 = "([0-9a-f]{64})"', ruling).group(1)
    written.write_text(text.replace(digest, "0" * 64, 1), encoding="utf-8")   # the ruling no longer binds to the answer
    if key != KEY:
        errs.append(f"1: the first answer's key is {key}, not {KEY}")
    gate(env, "S2")
    r = read(env, [NODE])[NODE]
    acts = [f for f in r["gate"] if f["kind"] == "act" and f["key"] == KEY]
    mine = [f for f in (r["impact"].get(KEY) or []) if f["kind"] == "act"]
    if len(acts) != 1 or acts[0]["severity"] != "major":
        errs.append(f"1: want gate_verdict to list one major act finding on {KEY}; got {[(f['kind'], f['severity']) for f in acts]}")
    if KEY not in r["impact"]:
        errs.append(f"1: register_impact from {NODE} does not land {KEY}: {sorted(r['impact'])}")
    elif mine != acts:
        errs.append(f"1: register_impact from {NODE} lists {len(mine)} act finding(s) on {KEY}, gate_verdict {len(acts)}")
    errs += [f"1: {x}" for x in differences({NODE: r})]
    print(f"    gate_verdict: {len(acts)} act finding(s) on {KEY}; register_impact from {NODE}: {len(mine)}")

    print("== 2: S1, S4 and S6: every landed key reads as gate_verdict reports it")
    env = review.pinned(w.instance(out, "plain", decided=False), ON)
    import subject
    nodes = sorted({n for row in subject.Subject(Path(env["KG_SUBJECT"])).register_map().get("row", []) for n in row.get("nodes", [])})
    for scenario in ("S1", "S4", "S6"):
        gate(env, scenario)
        got = read(env, nodes)
        diff = differences(got)
        errs += [f"2 {scenario}: {x}" for x in diff]
        print(f"    {scenario}: {sum(len(r['impact']) for r in got.values())} landed key reading(s) over {len(nodes)} node(s); "
              f"{len(diff)} differ")

    for e in errs:
        print(f"FAIL {e}")
    store = os.environ.get("KG_STORE") or "neo4j"
    print(f"register_impact's findings on {store}: " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):   # task-0314 B-X7: --help is not an output directory
        sys.exit(__doc__)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))

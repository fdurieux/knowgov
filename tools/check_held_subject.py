"""Two subjects that share a scenario id never answer each other's gates (task-0195, doc-0030 F1, H1).

    python tools/check_held_subject.py --disposable                 # KG_STORE=neo4j: the database it names
    KG_STORE=rdflib python tools/check_held_subject.py --disposable  # a file-backed store in a temporary folder

A subject A (CargoQuote) and a twin B, a copy of it under another id, both declare S1. With A's S1 loaded and
published by ``gate_cli --publish``, this holds:

- ``held()`` names A as the subject, S1 as the scenario and v1 as the version, and ``export_turtle`` into a
  fresh rdflib store carries all three (the round trip carries the subject);
- for B, ``gate_cli --no-load`` exits 2 naming A, every store-backed tool of the MCP reader refuses it but
  ``store_status``, which reports S1 as another subject's and nothing held of B's, and the page shows the
  load as A's and serves B no gaps;
- for A, the same gate, a tool and the page answer from the load.

It wipes and reloads the store, so it runs only against a disposable one and refuses without
``--disposable``. No model is called; the clock is pinned.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import _outcomes  # noqa: E402
os.environ.setdefault("KG_CLOCK", "pinned")

FAILURES: list[str] = []
A = ROOT / "subjects" / "cargo_quote"


def check(cond, label: str) -> bool:
    _outcomes.check(label, cond)
    print(("ok   " if cond else "FAIL ") + label, flush=True)
    if not cond:
        FAILURES.append(label)
    return bool(cond)


def _env(subject: Path, subjects: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI", "GEMINI", "AWS", "KG_ANTHROPIC", "KG_MODEL_API"))}
    env.update(KG_SUBJECT=str(subject), KG_SUBJECTS=str(subjects), PYTHONPATH=os.pathsep.join([str(ROOT / "harness"), str(ROOT / "demo" / "app")]))
    return env


def _py(code: str, subject: Path, subjects: Path) -> dict:
    """``code`` in a child process for ``subject`` (the process's SUBJECT is fixed at import); its last line, JSON."""
    p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=600, env=_env(subject, subjects))
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": f"exit {p.returncode}: {(p.stderr or p.stdout)[-400:]}"}


def _gate(subject: Path, subjects: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--subject", str(subject), "--scenario", "S1",
                           "--as-of", "record", "-f", "json", *flags],
                          cwd=ROOT, capture_output=True, text=True, timeout=600, env=_env(subject, subjects))


HELD = """
import json
from store import open_store, ReadOnly
from store_rdflib import RdflibStore
from subject import SUBJECT
with open_store(instance=SUBJECT.id, access="read") as st:
    h = st.held()
    ttl = st.export_turtle()
fresh = RdflibStore(path="")
fresh.import_turtle(ttl)
print(json.dumps({"held": h, "round_trip": fresh.held()}, default=str))
"""

TOOLS = """
import json
import mcp_server
from subject import SUBJECT
from tasks import TASKS
key = TASKS["codegen"]["keys"][0]
node = (SUBJECT.register_map().get("row") or [{"nodes": ["CAP-0001"]}])[0]["nodes"][0]
proposal = json.loads(open("tools/fixtures/proposal_contract_quote.json", encoding="utf-8").read())
args = {"gate_verdict": {}, "three_valued_answer": {"key": key}, "evidence_bundle": {}, "register_impact": {"node": node, "task": "codegen"},
        "proposal_impact": {"proposal": proposal, "task": "codegen"}, "held_keys": {}, "derived_outputs": {"key": key},
        "document_statements": {"document": SUBJECT.artefacts[0]["key"]}, "store_status": {}}
tools = mcp_server.Tools(as_of="record")
out = {}
for t in mcp_server.TOOLS:
    if not t["_meta"][mcp_server.META_STORE]:
        continue
    try:
        r = tools.call(t["name"], args[t["name"]]) if hasattr(tools, "call") else getattr(tools, t["name"])(args[t["name"]])
        out[t["name"]] = {"error": None, "result": {k: r.get(k) for k in ("scenario", "held_by_other_subject", "verdict")} if isinstance(r, dict) else None}
    except mcp_server.ToolError as e:
        out[t["name"]] = {"error": str(e)}
print(json.dumps(out, default=str))
"""

PAGE = """
import json
import server
st = server.store_status()
g = server.store_gaps("S1")
print(json.dumps({"loaded": st["loaded"], "loaded_subject": st["loaded_subject"], "error": st["error"],
                  "match": g["match"], "gaps": len(g["gaps"]), "gaps_error": g["error"]}))
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--disposable", action="store_true", help="confirm the store may be wiped (required)")
    args = ap.parse_args()
    if not args.disposable:
        print("check_held_subject: wipes and reloads the store; run it only against a disposable one, with --disposable", file=sys.stderr)
        return 2
    sys.path.insert(0, str(ROOT / "harness"))
    import cadence
    os.environ.update(cadence.pin_record({}))
    with tempfile.TemporaryDirectory() as td:
        if (os.environ.get("KG_STORE") or "neo4j").lower() == "rdflib":
            os.environ["KG_RDFLIB_FILE"] = str(Path(td) / "store.ttl")
        subjects = Path(td) / "subjects"
        subjects.mkdir()
        a = subjects / "cargo_quote"
        b = subjects / "twin"
        shutil.copytree(A, a, symlinks=True)
        shutil.copytree(A, b, symlinks=True)
        manifest = b / "subject.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace('id = "cargo_quote"', 'id = "twin"', 1), encoding="utf-8")
        p = _gate(a, subjects, "--publish")
        check(p.returncode in (0, 1), f"A's S1 loaded and published by gate_cli --publish (exit {p.returncode}) {p.stderr[-200:]}")

        h = _py(HELD, a, subjects)
        held = h.get("held") or {}
        check(held.get("subject") == "cargo_quote" and held.get("scenario") == "S1" and held.get("version") == "v1" and held.get("loaded_at"),
              f"held() names the subject, the scenario, the version and the time of the load: {h.get('held') or h}")
        check(h.get("round_trip") == h.get("held"), f"the Turtle round trip carries the held state, the subject included: {h.get('round_trip')}")

        p = _gate(b, subjects, "--no-load")
        check(p.returncode == 2 and "of subject cargo_quote" in p.stderr,
              f"gate_cli --no-load --subject twin exits 2, naming the held load's subject: exit {p.returncode}, {p.stderr.strip()[-200:]}")
        p = _gate(a, subjects, "--no-load")
        check(p.returncode in (0, 1) and json.loads(p.stdout or "{}").get("scenario") == "S1",
              f"gate_cli --no-load --subject cargo_quote answers from its own load (exit {p.returncode})")

        tb = _py(TOOLS, b, subjects)
        backed = sorted(tb)
        refused = [n for n in backed if n != "store_status" and tb[n].get("error") and "cargo_quote" in tb[n]["error"]]
        check(backed and refused == [n for n in backed if n != "store_status"],
              f"every store-backed tool for twin refuses, naming cargo_quote: {refused} of {backed} {tb.get('error', '')}")
        ss = (tb.get("store_status") or {}).get("result") or {}
        check(ss.get("scenario") is None and ss.get("held_by_other_subject") == "S1",
              f"store_status for twin reports nothing of its own held and S1 another subject's: {ss}")
        ta = _py(TOOLS, a, subjects)
        gv = ta.get("gate_verdict") or {}
        check(not gv.get("error") and (gv.get("result") or {}).get("verdict"), f"for cargo_quote the gate answers from its load: {gv}")

        pb = _py(PAGE, b, subjects)
        check(pb.get("loaded") == "S1" and pb.get("loaded_subject") == "cargo_quote" and pb.get("match") is False and pb.get("gaps") == 0,
              f"the page for twin shows the load as cargo_quote's and serves it no gaps: {pb}")
        pa = _py(PAGE, a, subjects)
        check(pa.get("loaded_subject") == "cargo_quote" and pa.get("match") is True and pa.get("gaps", 0) > 0,
              f"the page for cargo_quote serves its own load's gaps: {pa}")
    kind = (os.environ.get("KG_STORE") or "neo4j").lower()
    print(f"held subject ({kind}): " + ("every check holds" if not FAILURES else f"{len(FAILURES)} failure(s)"))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(_outcomes.run(main))

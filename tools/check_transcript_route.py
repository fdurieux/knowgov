"""Route (c) end to end (task-0041), on the store KG_STORE names: CI runs it on rdflib (harness.yml)
and on Neo4j (the stack job). No model key is needed: a stub model stands in.

    python tools/check_transcript_route.py OUT_DIR

It builds the public example instance into OUT_DIR, then on S2:

- with no model key configured, transcript.py refuses: exit 2, nothing written;
- a fixture transcript of a conversation with employee-1 (handles only), read by the stub model,
  gives candidates on the two keys S2 holds nothing on (response|hold_presence absent,
  QuoteAPI|on_screening_outage a declared gap); a proposal on a key the documents state, or on a
  key it was not asked about, is dropped;
- the candidates load as basis inferred, status proposed, attributed to the model, and stay
  proposed after the rules and the verifications; no capture is written;
- the questionnaire generated afterwards lists each in ``known``;
- the transcript's text is nowhere: not in the store, the captures folder or the register.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "the hold flag only matters when screening is down, said in passing at 10:42"
TRANSCRIPT = f"""Interview, 2026-11-02. Interviewer: architecture stewardship. Interviewee: employee-1.

Q: When does the response carry the hold flag?
A: Only for held_unscreened. {MARKER}.
Q: And when screening is out?
A: We price it, hold it, set held_unscreened, and send nothing.
"""
STUB = {"proposals": [
    {"key": "response|hold_presence", "value": "held_unscreened only"},
    {"key": "QuoteAPI|on_screening_outage", "value": "priced=yes;status=held_unscreened;notified=no;hold=true"},
    {"key": "response|statuses", "value": "held_unscreened"},           # stated by the documents: not asked, dropped
    {"key": "made|up", "value": "x"},                                    # not a key it was asked about: dropped
]}
HOLD, OUT = "response|hold_presence", "QuoteAPI|on_screening_outage"


def inside(transcript: Path, qdir: Path) -> dict:
    sys.path.insert(0, str(ROOT / "harness"))
    import argparse
    import capture
    import gate_cli
    import transcript as tr
    from gate import resolve
    from store import open_store
    from subject import SUBJECT
    asked = []

    def stub(system, user):
        asked.append(user)
        return STUB
    code = tr.run(argparse.Namespace(transcript=transcript, scenario="S2", task="codegen", into=None), call=stub)
    st = open_store()
    try:
        gate_cli._load(st, "S2")
        res = resolve(st, "codegen")
        from load import LLM
        inferred = [{"id": a["id"], "key": k, "status": a["status"], "basis": a["basis"], "agent": a["agent"]}
                    for k, v in res["keys"].items() for a in v["assertions"] if a["id"].startswith("A:inf:")]
        dump = json.dumps(res, default=str) + json.dumps(st.assertion_rows()) + json.dumps([g["text"] for g in st.gaps_with_concerns()])
        if hasattr(st, "g"):
            dump += st.g.serialize(format="nt")
        qs = capture.questionnaires(res, SUBJECT, "S2", "codegen", capture.register_nodes(capture.register_root()), capture.dt.date(2026, 11, 2))
    finally:
        st.close()
    qdir.mkdir(parents=True, exist_ok=True)
    for owner, text in qs.items():
        (qdir / f"{owner}.toml").write_text(text, encoding="utf-8")
    return {"code": code, "asked": asked, "inferred": inferred, "levels": {k: v["level"] for k, v in res["keys"].items()},
            "marker_in_store": MARKER in dump, "store": st.name,
            "model": LLM["name"]}


def main(out: Path) -> int:
    root = out / "instance"
    subprocess.run([sys.executable, str(ROOT / "tools" / "example_instance.py"), str(root)], check=True, capture_output=True)
    sys.path.insert(0, str(ROOT / "harness"))
    import review
    env = review.pinned(dict(os.environ, KG_SUBJECT=str(root / "subjects" / "cargo_quote"), KG_REGISTER=str(root / "register"),
                             PYTHONDONTWRITEBYTECODE="1", KG_MODEL_API_KEY_VAR="KG_TRANSCRIPT_CHECK_NO_KEY"),
                        "2026-11-03")   # the walkthrough's day, the wall clock refused (task-0075)
    env.pop("KG_TRANSCRIPT_CHECK_NO_KEY", None)
    t = out / "transcript.txt"
    t.write_text(TRANSCRIPT, encoding="utf-8")
    caps = root / "subjects" / "cargo_quote" / "captures"
    errs = []

    p = subprocess.run([sys.executable, str(ROOT / "harness" / "transcript.py"), str(t), "--scenario", "S2"], env=env,
                       cwd=ROOT / "harness", capture_output=True, text=True)
    print(f"exit {p.returncode} with no model key: {p.stderr.strip()}")
    if p.returncode != 2 or "no model key" not in p.stderr or (caps / "inferred").exists():
        errs.append(f"want exit 2 and nothing written with no key, got {p.returncode}: {p.stdout}{p.stderr}")

    q = subprocess.run([sys.executable, __file__, "--inside", str(t), str(out / "questionnaires")], env=env, capture_output=True, text=True)
    if q.returncode:
        sys.exit(f"FAIL: the stub run:\n{q.stdout}{q.stderr}")
    r = json.loads(q.stdout.strip().splitlines()[-1])
    print(f"store {r['store']}: transcript.py exit {r['code']}; {len(r['inferred'])} candidate(s) loaded")
    if r["code"] != 0:
        errs.append(f"the stub run exited {r['code']}")
    asked = r["asked"][0] if r["asked"] else ""
    if not (f"- {HOLD}" in asked and f"- {OUT}" in asked and "- response|statuses" not in asked):
        errs.append(f"the model was asked about the wrong keys:\n{asked}")
    got = {x["id"]: (x["key"], x["status"], x["basis"]) for x in r["inferred"]}
    want = {(HOLD, "proposed", "inferred"), (OUT, "proposed", "inferred")}
    if set(got.values()) != want:
        errs.append(f"want two inferred candidates at proposed on {HOLD} and {OUT}, got {got}")
    if {x["agent"] for x in r["inferred"]} != {r["model"]}:
        errs.append(f"a candidate is not attributed to the model ({r['model']}): {r['inferred']}")
    if r["levels"][HOLD] != "proposed" or r["levels"][OUT] != "declared_gap" or r["levels"]["response|statuses"] != "validated":
        errs.append(f"levels moved wrongly: {HOLD} {r['levels'][HOLD]}, {OUT} {r['levels'][OUT]}, statuses {r['levels']['response|statuses']}")
    if [f.name for f in caps.glob("*.toml")]:
        errs.append(f"a capture was written: {[f.name for f in caps.glob('*.toml')]}")
    qtext = (out / "questionnaires" / "ORG-0002.toml").read_text(encoding="utf-8")
    for key, value in ((HOLD, "held_unscreened only"), (OUT, "priced=yes;status=held_unscreened;notified=no;hold=true")):
        part = next((s for s in qtext.split("[[item]]") if f'key = "{key}"' in s), "")
        if f"{value} (proposed, inferred, transcript:" not in part:
            errs.append(f"the questionnaire does not list the candidate on {key} in known:\n{part}")
    print(f"questionnaire ORG-0002 lists the candidates in known for {HOLD} and {OUT}")
    hits = [str(f) for d in (caps, root / "register") for f in d.rglob("*") if f.is_file() and MARKER in f.read_text(encoding="utf-8", errors="ignore")]
    if r["marker_in_store"] or hits:
        errs.append(f"the transcript's text was copied: store {r['marker_in_store']}, files {hits}")
    if errs:
        sys.exit("FAIL:\n  " + "\n  ".join(errs))
    print("OK: no key, exit 2; a transcript read by the model gives candidates on the empty keys only, inferred and proposed, "
          "listed in the questionnaire's known; no capture written, the transcript's text nowhere")
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--inside"]:
        print(json.dumps(inside(Path(sys.argv[2]), Path(sys.argv[3])), default=str))
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))

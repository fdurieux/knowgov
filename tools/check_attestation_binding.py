"""An attestation is bound to the Versions it attests (task-0221, decision-0019), on the store KG_STORE names
(rdflib persisted to a file under OUT_DIR, so a --no-load reads back what was published), the public example
instance built under OUT_DIR:

    python tools/check_attestation_binding.py OUT_DIR

1. The read rule: the subject's ``[verification] authored`` and ``approval`` with no ``versions`` (any list removed):
   S1 attests per load, PROCEED, the gate lists each declaration at info as not bound, and check_subject notes them.
2. Bound: both declarations list the digest of every artefact Version S1 loads. S1 reads as under the read rule,
   level for level, with no attestation finding beyond none at info.
3. An edit after the attestation: a note added to the decision table, whose Version the lists do not name. Its
   authored statements read proposed and none of its statements is approved by construction; the gate names
   ``contract/decision_table.md`` (major) behind its keys, with the attester's listing as the route.
4. check_subject refuses a digest that is no Version of the subject.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]
import cadence  # noqa: E402
import example_instance  # noqa: E402

TABLE = "contract/decision_table.md"
TABLE_FILE = "artefacts/decision-tables/decision_table.md"
STATEMENT = "A:dt:weight_kg|max@v1"


def run(env: dict, *args: str) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, *args], cwd=HARNESS, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def gate(env: dict, scenario: str = "S1") -> dict:
    """The gate on a private load; with KG_STORE set, also published and read back, the two reports equal."""
    def one(*extra):
        code, so, se = run(env, "gate_cli.py", "--scenario", scenario, "--as-of", "record", "-f", "json", *extra)
        if code == 2:
            sys.exit(f"FAIL: gate_cli {' '.join(extra)} could not run:\n{se[-1500:]}")
        return json.loads(so)
    private = one()
    if os.environ.get("KG_STORE"):
        one("--publish")
        held = one("--no-load")
        if held["findings"] != private["findings"] or held["levels"] != private["levels"]:
            sys.exit(f"FAIL: the published store's report differs from the private load's on {scenario}")
    return private


def probe(env: dict, code: str):
    p = subprocess.run([sys.executable, "-c", "import json, sys; sys.path.insert(0, '.')\n" + code], cwd=HARNESS, env=env,
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAIL: probe could not run:\n{p.stderr[-1500:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def statuses(env: dict, artefact: str) -> dict:
    """statement id -> (status, approved by construction) for ``artefact``'s statements, on a private load of S1."""
    return probe(env, "import gate_cli, store, gate\n"
                      "with store.scratch_store() as st:\n"
                      "    gate_cli._load(st, 'S1')\n"
                      "    out = {r['id']: [r['status'], any(a['id'] == 'appr:' + r['id'] for a in r['approvals'])]\n"
                      f"           for k in {{x['key'] for x in st.artefact_assertions({artefact!r})}}\n"
                      "           for r in st.key_evidence(k, gate.LIVE) if r['artefact'] == " + repr(artefact) + "}\n"
                      "print(json.dumps(out))")


def names_every_declaration(named: list) -> list[str]:
    """task-0318: the finding names execution and review beside authored and approval (decision-0036); the store's read
    of them is what is measured, Neo4j's in the stack job."""
    if named and not all(w in named[0]["message"] for w in ("execution", "review", "decision-0036")):
        return [f"edited: want the finding to name execution and review beside authored and approval (decision-0036); got {named[0]['message'][:160]}"]
    return []


def main(out: Path) -> int:
    errs: list[str] = []
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True)
    inst = example_instance.build(out / "inst")
    subject = inst / "subjects" / "cargo_quote"
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(subject), KG_REGISTER=str(inst / "register"),
                                    KG_RDFLIB_FILE=str(out / "store.ttl"), PYTHONDONTWRITEBYTECODE="1"))   # task-0075

    print("== 1. the read rule: no versions listed")
    mf = subject / "subject.toml"   # the read rule, whatever the subject as committed lists
    # authored and approval only: execution's versions, followed by its implementation and suite (task-0320), stay
    mf.write_text(re.sub(r"^((?:authored|approval) = \{[^\n]*?)versions = \[[^\]]*\], ", r"\1", mf.read_text(encoding="utf-8"), flags=re.M),
                  encoding="utf-8")
    rule = gate(env)
    info = [f for f in rule["findings"] if f["kind"] == "attestation"]
    if rule["verdict"] != "PROCEED" or sorted(f["ref"] for f in info) != ["attest:approval", "attest:authored"] \
            or any(f["severity"] != "info" for f in info):
        errs.append(f"read rule: want PROCEED and two info attestation findings; got {rule['verdict']}, {[(f['severity'], f['ref']) for f in info]}")
    code, so, se = run(env, str(ROOT / "tools" / "check_subject.py"), str(subject), "--register", env["KG_REGISTER"], "--json")
    notes = [n for n in (json.loads(so).get("notes", []) if so.strip().startswith("{") else []) if n.get("rule") == "attestation"]
    if len(notes) != 2 or not all("decision-0019" in n["message"] for n in notes):
        errs.append(f"read rule: check_subject does not note both declarations naming decision-0019: {notes}")
    print(f"    {rule['verdict']}; {len(info)} info attestation finding(s); check_subject notes {len(notes)}")

    print("== 2. bound: every Version S1 loads is listed")
    digests = probe(env, "from kitio import kit_for\nfrom subject import SUBJECT\n"   # as the load digests each Version
                         "out = set()\nfor path, text in kit_for('S1').items():\n"
                         "    out.add(SUBJECT.version_digest(path, text)[0])\n"
                         "    out |= set(SUBJECT.part_digests(path, text).values()) if path.endswith('/') else set()\n"
                         "print(json.dumps(sorted(out)))")
    text = mf.read_text(encoding="utf-8")
    listed = ", ".join(json.dumps(d) for d in digests)
    bound, n = re.subn(r'^((?:authored|approval) = \{ at = "[^"]*", )', rf'\1versions = [{listed}], ', text, flags=re.M)
    assert n == 2, n
    mf.write_text(bound, encoding="utf-8")
    now = gate(env)
    left = [f for f in now["findings"] if f["kind"] == "attestation"]
    if now["verdict"] != rule["verdict"] or now["levels"] != rule["levels"] or left:
        errs.append(f"bound: want the read rule's verdict and levels and no attestation finding; got {now['verdict']}, "
                    f"{sorted(k for k in now['levels'] if now['levels'][k] != rule['levels'].get(k))}, {[f['message'][:80] for f in left]}")
    print(f"    {len(digests)} digest(s) listed: {now['verdict']}, levels as the read rule's: {now['levels'] == rule['levels']}")

    print(f"== 3. {TABLE} edited after the attestation: its Version is unlisted")
    tf = inst / TABLE_FILE
    pristine_table = tf.read_text(encoding="utf-8")
    tf.write_text(pristine_table + "\nA note added after the attestation.\n", encoding="utf-8")
    edited = gate(env)
    named = [f for f in edited["findings"] if f["kind"] == "attestation" and f["ref"] == TABLE]
    st = statuses(env, TABLE)
    authored = probe(env, "import gate_cli, store, gate\nwith store.scratch_store() as st:\n    gate_cli._load(st, 'S1')\n"
                          f"    print(json.dumps(sorted(r['id'] for r in st.artefact_assertions({TABLE!r}) if r['basis'] == 'authored' and r['status'] != 'proposed')))")
    if not named or named[0]["severity"] != "major" or not named[0]["related"] or "decision-0019" not in (named[0].get("route") or ""):
        errs.append(f"edited: want a major attestation finding naming {TABLE} behind its keys with the attester's route; got {named}")
    errs += names_every_declaration(named)
    if authored or any(appr for _s, appr in st.values()) or st.get(STATEMENT, [None])[0] == "approved":
        errs.append(f"edited: {TABLE}'s statements are still attested: authored not proposed {authored[:4]}, "
                    f"approved by construction {[k for k, v in st.items() if v[1]][:4]}")
    if edited["levels"].get("weight_kg|max") == rule["levels"].get("weight_kg|max"):
        errs.append(f"edited: weight_kg|max still reads {edited['levels'].get('weight_kg|max')}")
    print(f"    {edited['verdict']}; {STATEMENT} {st.get(STATEMENT)}; finding: {named[0]['message'][:110] if named else None}")

    print("== 4. check_subject refuses a digest that is no Version of the subject")
    tf.write_text(pristine_table, encoding="utf-8")   # task-0318: an edited document is named as changed; this measures a digest of nothing
    mf.write_text(bound.replace(f"versions = [{listed}]", f"versions = [{listed}, \"{'0' * 64}\"]", 1), encoding="utf-8")
    code, so, se = run(env, str(ROOT / "tools" / "check_subject.py"), str(subject), "--register", env["KG_REGISTER"], "--json")
    bad = [f for f in (json.loads(so).get("findings", []) if so.strip().startswith("{") else []) if f.get("rule") == "attestation"]
    if code == 0 or not any("0" * 64 in f["message"] for f in bad):
        errs.append(f"check_subject accepts a digest of nothing: exit {code}, {bad}")
    print(f"    exit {code}: {bad[0]['message'][:100] if bad else 'accepted'}")

    for x in errs:
        print("FAIL", x)
    print(f"attestations bound to their Versions ({'on ' + os.environ['KG_STORE'] if os.environ.get('KG_STORE') else 'private loads'}): "
          + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):   # task-0314 B-X7: --help is not an output directory
        sys.exit(__doc__)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))

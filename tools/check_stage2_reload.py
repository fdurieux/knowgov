"""Stage 2 as a whole re-load (task-0197, doc-0030 F3): a scenario's later version, brought in by
``change.apply_change`` on a store holding its first, gives the gate a fresh load of the later documents
gives, plus the stale statements and the suspect derived outputs the change leaves. Held on the store
``KG_STORE`` names (rdflib in memory by default, Neo4j where it runs), for the subject ``KG_SUBJECT`` names.

    python tools/check_stage2_reload.py

CargoQuote:

- S6, the record's change (the decision table's tariff): equal after the owner's re-verification, and
  before it on every key the change left alone.
- H4, a cross-version plant on S1: the table's accept row at 45 against 41 in the DMN and the sequence
  diagram reads disputed, as a fresh load reads it.
- I5, symbols: changing only ``ACCEPT_MAX`` (the definition the sequence diagram reads) invalidates the
  sequence diagram's statement resolved through it, and re-ingesting the sequence diagram alone flags no
  symbol undefined.
- G5, on S2: a requirements v2 that specifies REQ-06 withdraws the declared gap OD-1 its old row declared.
- H2, on S2: a close of OD-1 survives a stage-2 re-ingestion of another document; R-REQ never reopens it.

J-F (``KG_SUBJECT=subjects/jef_data_load``): I6, one ``@JDL-001`` tag removed from the feature bundle gives
``JDL-001|verified_by`` a live successor, and the gate equals a fresh load's.

A report is compared on its verdict, every key's level and its findings by severity, kind, key and level
(statement ids carry their version, which differs by construction); the stale and suspect findings are
the change's own. Exit 0 when every check holds, 1 naming each that does not.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "harness")]

CHANGE_KINDS = {"stale", "suspect_derived"}


def open_kind():
    from store import open_store
    kind = (os.environ.get("KG_STORE") or "rdflib").lower()
    return open_store(kind, access="write", **({"path": ""} if kind == "rdflib" else {}))


def load_fresh(st, sc: str, kit: dict, tag: str = "v1") -> None:
    """What a deterministic run does before its gate (gate_cli._load), on ``kit`` and tagged ``tag``."""
    from load import load_captures, load_inferred, load_reviews, load_scenario, load_verifications, pristine_values
    from plant import INFERRED
    from rules import run_all
    from subject import SUBJECT
    cfg = SUBJECT.scenario(sc)
    st.wipe()
    st.apply_constraints()
    load_scenario(st, sc, kit, activity_note=f"{sc}: fresh load for the stage-2 check", version_tag=tag)
    if cfg.get("verifications", True):
        load_verifications(st, sc, pristine_values(), kit)
    if cfg.get("inferred") and INFERRED:
        load_inferred(st, sc, INFERRED)
    load_captures(st, sc)
    run_all(st, sc)
    load_reviews(st, sc)


def reports(st, sc: str) -> dict:
    import cadence
    import gate_cli
    from subject import SUBJECT
    from tasks import TASKS
    on = cadence.as_of("record").isoformat()
    return {t: gate_cli.evaluate(st, subject=SUBJECT.id, scenario=sc, task=t, spec=TASKS[t], threshold="blocker",
                                 baseline=None, loaded=True, as_of=on) for t in sorted(TASKS)}


def shape(rep: dict, keys: set[str] | None = None) -> tuple:
    """A report without its statement ids and without the change's own findings; ``keys`` narrows it."""
    fs = Counter((f["severity"], f["kind"], f.get("key"), f.get("level"), f["message"] if f["kind"] == "task" else None)
                 for f in rep["findings"] if f["kind"] not in CHANGE_KINDS and (keys is None or f.get("key") in keys))
    levels = {k: v for k, v in rep["levels"].items() if keys is None or k in keys}
    return (rep["verdict"] if keys is None else None, levels, sorted(fs.items()))


def compare(stage2: dict, fresh: dict, label: str, keys: set[str] | None = None) -> list[str]:
    out = []
    for t in sorted(stage2):
        a, b = shape(stage2[t], keys), shape(fresh[t], keys)
        if a != b:
            lv = sorted(k for k in set(a[1]) | set(b[1]) if a[1].get(k) != b[1].get(k))
            out.append(f"{label} [{t}]: stage 2 {a[0]} {[(k, a[1].get(k)) for k in lv]} != fresh {b[0]} {[(k, b[1].get(k)) for k in lv]}; "
                       f"findings only in stage 2 {sorted(set(a[2]) - set(b[2]))[:4]}, only fresh {sorted(set(b[2]) - set(a[2]))[:4]}")
    return out


def stage2(st, sc: str, cfg2: dict, kit1: dict, kit2: dict, reverify: bool, derived: bool = False, before=None) -> dict:
    """Stage 1 on ``kit1``, then the change to ``kit2``; with ``reverify``, change.reverify (the owner's keys,
    then the verifications against the pristine values, which a fresh load runs at its load)."""
    from change import apply_change, reverify as rever
    from gate import resolve
    from load import pristine_values
    from subject import SUBJECT
    load_fresh(st, sc, kit1)
    if before:
        before(st)
    code, ids = None, []
    if derived:
        d = cfg2.get("derived", {})
        code = (SUBJECT.record_dir / d.get("from_scenario", sc) / d.get("file", "run1_G.py")).read_text(encoding="utf-8")
        ids = [a["id"] for v in resolve(st, "codegen")["keys"].values() for a in v["assertions"]]
    ch = apply_change(sc, cfg2, st, code, ids, kit2=kit2, kit1=kit1)
    if reverify:
        rever(sc, cfg2, pristine_values(), st, kit2)
    return ch


def fresh_like(st, sc: str, cfg2: dict, kit2: dict, reverify: bool) -> dict:
    """A fresh load of ``kit2`` tagged as the change's version, so the owner's re-verification finds its statements."""
    from change import version_of
    from load import HUMAN
    load_fresh(st, sc, kit2, version_of(cfg2))
    if reverify and cfg2.get("reverify_keys"):
        st.reverify(version_of(cfg2), list(cfg2["reverify_keys"]), HUMAN["id"], cfg2.get("at", ""),
                    cfg2.get("reverify_scope", "re-verification"), cfg2.get("reapproval_record", "re-approval"))
    return reports(st, sc)


def cargo_quote(st) -> list[str]:
    from kitio import kit_for
    from subject import SUBJECT
    errs = []
    table, seq, req = "contract/decision_table.md", "behavior/quote_flow.puml", "kit/requirements.md"

    # S6, the record's change, after the re-verification and before it
    cfg6 = SUBJECT.scenario("S6")["stage2"]
    k1, k2 = kit_for("S6"), kit_for("S6", 2)
    ch = stage2(st, "S6", cfg6, k1, k2, reverify=False, derived=True)
    touched = {x["key"] for x in ch["D3_stale"]["invalidated"]}
    held = st.held()   # task-0195: the stage-2 load stamps its subject, and held() reads v2 current through CURRENT
    if not held or (held["subject"], held["scenario"], held["version"]) != (SUBJECT.id, "S6", "v2"):
        errs.append(f"S6: after stage 2 the store reads held {held and {k: held[k] for k in ('subject', 'scenario', 'version')}}, not {SUBJECT.id} S6 v2")
    before = reports(st, "S6")
    from change import reverify as rever
    from load import pristine_values
    rever("S6", cfg6, pristine_values(), st, k2)
    after = reports(st, "S6")
    if not any(f["kind"] == "stale" for f in after["codegen"]["findings"]) or not any(f["kind"] == "suspect_derived" for f in after["codegen"]["findings"]):
        errs.append("S6: the change's stale and suspect findings are missing")
    errs += compare(after, fresh_like(st, "S6", cfg6, k2, reverify=True), "S6 after re-verification")
    others = set(before["codegen"]["levels"]) - touched
    errs += compare(before, fresh_like(st, "S6", cfg6, k2, reverify=False), "S6 before re-verification, the keys the change left", others)
    print(f"S6: stage 2 equals a fresh load of its later documents (after re-verification: {after['codegen']['verdict']}; "
          f"{len(touched)} key(s) changed)")

    # H4: a cross-version contradiction reads disputed
    k1 = kit_for("S1")
    cfg = {"artefact": table, "version": "v2"}
    k2 = {**k1, table: k1[table].replace("`risk_index <= 41`", "`risk_index <= 45`", 1)}
    assert k2[table] != k1[table]
    stage2(st, "S1", cfg, k1, k2, reverify=True)
    got = reports(st, "S1")
    if got["codegen"]["levels"].get("S-accept|max") != "disputed":
        errs.append(f"H4: S-accept|max reads {got['codegen']['levels'].get('S-accept|max')} after the table's accept row went to 45, not disputed")
    errs += compare(got, fresh_like(st, "S1", cfg, k2, reverify=True), "H4 (accept row 45 against 41)")
    print(f"H4: the accept row at 45 against 41 elsewhere reads {got['codegen']['levels'].get('S-accept|max')}, as a fresh load")

    # I5 (b): only the symbol's definition changes; the sequence diagram's statement resolved through it is replaced
    k2 = {**k1, table: k1[table].replace("`ACCEPT_MAX = 41`", "`ACCEPT_MAX = 45`", 1)}
    assert k2[table] != k1[table]
    ch = stage2(st, "S1", cfg, k1, k2, reverify=True)
    via = [x for x in ch["D3_stale"]["invalidated"] if x["id"].startswith("A:seq:")]
    if not via:
        errs.append(f"I5: changing ACCEPT_MAX invalidated nothing resolved through it: {ch['D3_stale']['invalidated']}")
    errs += compare(reports(st, "S1"), fresh_like(st, "S1", cfg, k2, reverify=True), "I5 (ACCEPT_MAX 45)")
    print(f"I5: ACCEPT_MAX = 45 invalidates {sorted(x['id'] for x in via)}")

    # I5 (a): re-ingesting the sequence diagram alone resolves its symbols from the whole kit
    cfg_seq = {"artefact": seq, "version": "v2"}
    # the fragment reading the symbol (alt/37-52) reworded where its value is not read: its note
    k2 = {**k1, seq: k1[seq].replace("Notification is fire-and-forget", "Notification is sent fire-and-forget", 1)}
    assert k2[seq] != k1[seq]
    stage2(st, "S1", cfg_seq, k1, k2, reverify=True)
    undefined = [g for k in ("S-accept|max", "S-review|max", "S-refuse|min") for x in st.key_evidence(k, ["proposed", "validated", "verified", "approved", "disputed"])
                 for g in x["gaps"] if "has no definition" in (g["text"] or "")]
    if undefined:
        errs.append(f"I5: re-ingesting the sequence diagram flags a symbol undefined: {undefined[:2]}")
    back = [x for x in st.key_evidence("S-accept|max", ["proposed", "validated", "verified", "approved", "disputed"]) if x["id"].startswith("A:seq:")]
    if [x["value"] for x in back] != ["41"]:
        errs.append(f"I5: the reworded sequence-diagram statement on S-accept|max is not back, resolved: {[(x['id'], x['value']) for x in back]}")
    errs += compare(reports(st, "S1"), fresh_like(st, "S1", cfg_seq, k2, reverify=True), "I5 (the sequence diagram re-ingested)")
    print("I5: the sequence diagram re-ingested alone flags no symbol undefined")

    # G5: a requirements v2 that specifies REQ-06 withdraws OD-1
    k1, k_spec = kit_for("S2"), kit_for("S1")
    cfg_req = {"artefact": req, "version": "v2"}
    k2 = {**k1, req: k_spec[req]}
    assert k2[req] != k1[req]
    ch = stage2(st, "S2", cfg_req, k1, k2, reverify=True)
    gid = SUBJECT.rules.get("declared_gap_id", "gap:declared:open")
    if st.declared_gap(gid) is not None:
        errs.append(f"G5: {gid} is still open after the requirement it declared was specified")
    errs += compare(reports(st, "S2"), fresh_like(st, "S2", cfg_req, k2, reverify=True), "G5 (REQ-06 specified)")
    print(f"G5: REQ-06 specified withdraws {ch['D3_stale'].get('withdrawn')}")

    # H2: a close of OD-1 survives a stage-2 re-ingestion of another document
    def close(s):
        s.close_declared_gap(gid, "review:check", "2026-11-02", "minutes/check.md")
    k2 = {**k1, table: k1[table] + "\nA note added in stage 2.\n"}
    cfg = {"artefact": table, "version": "v2"}
    key = next(k for k, v in SUBJECT.rules.get("requirement_keys", {}).items())   # the requirement the gap governs
    gkey = SUBJECT.rules["requirement_keys"][key]
    load_fresh(st, "S2", k1)
    close(st)
    lvl1 = reports(st, "S2")["codegen"]["levels"].get(gkey)
    stage2(st, "S2", cfg, k1, k2, reverify=True, before=close)
    lvl2 = reports(st, "S2")["codegen"]["levels"].get(gkey)
    if st.declared_gap(gid) is not None or lvl2 != lvl1 or lvl2 == "declared_gap":
        errs.append(f"H2: {gid} closed by a review reads {lvl1} after stage 1 and {lvl2} after stage 2 (open again: {st.declared_gap(gid) is not None})")
    print(f"H2: OD-1 closed stays closed through stage 2; {gkey} reads {lvl2}")
    return errs


def jef(st) -> list[str]:
    from kitio import kit_for
    from subject import SUBJECT
    errs = []
    sc = SUBJECT.order[0]
    k1 = kit_for(sc)
    folder = next(p for p, t in k1.items() if p.endswith("/") and "@JDL-001" in t)
    text = k1[folder]
    i = text.index("@JDL-001")
    k2 = {**k1, folder: text[:i] + text[i + len("@JDL-001"):].lstrip(" ")}   # one tag of several removed
    cfg = {"artefact": folder, "version": "v2"}
    stage2(st, sc, cfg, k1, k2, reverify=True)
    live = [x for x in st.key_evidence("JDL-001|verified_by", ["proposed", "validated", "verified", "approved", "disputed"])]
    if not any(x["id"].endswith("@v2") for x in live):
        errs.append(f"I6: JDL-001|verified_by has no v2 successor after one of its tags was removed: {[x['id'] for x in live]}")
    errs += compare(reports(st, sc), fresh_like(st, sc, cfg, k2, reverify=True), "I6 (one @JDL-001 tag removed)")
    print(f"I6: one @JDL-001 tag removed gives {[x['id'] for x in live if x['id'].endswith('@v2')]}")
    return errs


def main() -> int:
    import cadence
    from subject import SUBJECT
    os.environ.update(cadence.pin_record({}))   # the subject's record date, the wall clock refused (task-0075)
    st = open_kind()
    try:
        errs = cargo_quote(st) if SUBJECT.id == "cargo_quote" else jef(st) if SUBJECT.id == "jef_data_load" else []
        st.commit()
    finally:
        st.close()
    for e in errs:
        print("FAIL", e)
    print(f"stage 2 as a whole re-load on {SUBJECT.id}: " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))

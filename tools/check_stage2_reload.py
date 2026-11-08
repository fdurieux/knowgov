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
- Review files read again at stage 2 (task-0222), on the example instance through ``gate_cli``: R1, a ruling
  written for S6's later version applies at stage 2, with no act left from stage 1; R2, a close of OD-1 survives
  a stage 2 of S2's own and closing it again is a no-op; R3, a stage 2 that rewords OD-1's declaration reports
  the close changed. The gate commands run on their own private loads, whatever ``KG_STORE``.

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


def reviews_case(out: Path) -> list[str]:
    """task-0222: stage 2 re-reads every review file, on the public example instance through ``gate_cli`` (a review
    file lives in a subject's capture folder, so not in the vendored subject). R1, S6: a ruling written for the later
    version (P2's surcharge at 341.00, @v2) applies at stage 2 and leaves no act finding from stage 1. R2, S2 with a
    stage 2 of its own: employee-4's close of OD-1 survives a re-ingestion of the table, closing it again is a no-op,
    and nothing is reported. R3: the same close, read after the subject's declaration of OD-1 changed (its rules'
    ``declared_gap_text``, where a gap's text comes from): at both stages it is not applied, the gate reports it
    changed, and OD-1 stays open."""
    import json
    import subprocess
    import example_instance
    import review
    errs: list[str] = []
    ON = "2026-11-03"   # the day the handles' reviews may carry (the register issues them then); every gate reads as of it

    def gate(env, *args):
        p = subprocess.run([sys.executable, "gate_cli.py", "--as-of", ON, "-f", "json", *args], cwd=ROOT / "harness",
                           env=env, capture_output=True, text=True)
        if p.returncode == 2:
            raise SystemExit(f"FAIL: gate_cli {' '.join(args)} could not run:\n{p.stderr[-1500:]}")
        return json.loads(p.stdout)

    def instance(name):
        inst = example_instance.build(out / name)
        env = review.pinned(dict(os.environ, KG_SUBJECT=str(inst / "subjects" / "cargo_quote"), KG_REGISTER=str(inst / "register"),
                                 PYTHONDONTWRITEBYTECODE="1"), ON)
        env.pop("KG_RDFLIB_FILE", None)
        return inst / "subjects" / "cargo_quote", env

    def write(subject, name, by, scenario, rulings=(), closes=()):
        d = subject / "captures" / "reviews"
        d.mkdir(parents=True, exist_ok=True)
        text = f'[review]\nby = "{by}"\non = {ON}\nrecord = "minutes/stage2.md"\nscenario = "{scenario}"\n'
        for r in rulings:
            text += "\n[[ruling]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in r.items())
        for c in closes:
            text += "\n[[closes]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in c.items())
        (d / f"{name}.toml").write_text(text, encoding="utf-8")

    acts = lambda rep: [f for f in rep["findings"] if f["kind"] == "act"]   # noqa: E731

    # R1: a ruling for the later version
    subject, env = instance("r1")
    row = "| P2 | heavy surcharge: if `weight_kg > 1244`, add `341.00` (flat) |"
    v2 = {"assertion": "A:dt:P2|surcharge@v2", "key": "P2|surcharge", "value": "341.00", "outcome": "approved"}
    probe = ("import json, sys; sys.path.insert(0, '.'); import gate_cli, review, store; from change import apply_change; "
             "from subject import SUBJECT; st = store.scratch_store(); st.__enter__(); gate_cli._load(st, 'S6'); "
             "apply_change('S6', SUBJECT.scenario('S6')['stage2'], st, None, []); "
             "b = review.statement(st, 'A:dt:P2|surcharge@v2'); print(json.dumps(b))")
    p = subprocess.run([sys.executable, "-c", probe], cwd=ROOT / "harness", env=env, capture_output=True, text=True)
    b = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else {}
    if not b or b.get("value") != "341.00":
        return [f"R1: the later version's P2 statement could not be read: {b or p.stderr[-600:]}"]
    write(subject, "2026-10-30-employee-3", "employee-3", "S6", rulings=[{**v2, "sha256": b["sha256"]}])
    one, two = gate(env, "--scenario", "S6"), gate(env, "--scenario", "S6", "--stage", "2")
    if [f["act"]["why"] for f in acts(one)] != ["changed"] or acts(two) or two["levels"].get("P2|surcharge") != "approved":
        errs.append(f"R1: a ruling written for v2 reads {[f['act']['why'] for f in acts(one)]} at stage 1 (want changed), then at stage 2 "
                    f"{[(f['act']['why'], f['ref']) for f in acts(two)]} (want none) with P2|surcharge {two['levels'].get('P2|surcharge')} (want approved)")
    print(f"R1: a ruling written for v2: stage 1 {[f['act']['why'] for f in acts(one)]}, stage 2 {len(acts(two))} act(s), "
          f"P2|surcharge {two['levels'].get('P2|surcharge')} ({row[:30]}...)")

    # R2 and R3: a close of OD-1 through a stage 2 of S2's own
    gid = "gap:declared:OD-1"
    old, new = "A request is **valid** iff every row holds:", "A request is **valid** iff every row holds (stage 2 note):"
    path = "contract/decision_table.md"
    for case in ("R2", "R3"):
        subject, env = instance(case.lower())
        sc = subject / "scenarios.toml"
        t = sc.read_text(encoding="utf-8")
        i = t.index('id = "S2"')
        j = t.index("\n[[scenario]]", i)
        sc.write_text(t[:j] + f'\n\n[scenario.stage2]\nartefact = "{path}"\nversion = "v2"\nnote = "{case}: a stage 2 of S2"\n' + t[j:], encoding="utf-8")
        pl = subject / "plants.toml"   # a stage-2 kit is the pristine kit with its own patches: S2's, then this change
        import tomllib
        patches = [dict(x) for x in tomllib.loads(pl.read_text(encoding="utf-8")).get("plant", {}).get("S2", [])]
        patches.append({"path": path, "op": "replace", "old": old, "new": new})
        pl.write_text(pl.read_text(encoding="utf-8") + "".join(
            "\n[[stage2.S2]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in x.items()) for x in patches), encoding="utf-8")
        probe = ("import json, sys; sys.path.insert(0, '.'); import gate_cli, store; st = store.scratch_store(); st.__enter__(); "
                 f"gate_cli._load(st, 'S2'); g = st.declared_gap({gid!r}); print(json.dumps(g))")
        p = subprocess.run([sys.executable, "-c", probe], cwd=ROOT / "harness", env=env, capture_output=True, text=True)
        g = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else None
        if not g:
            errs.append(f"{case}: S2 holds no open {gid}: {p.stderr[-400:]}")
            continue
        write(subject, "2026-10-30-employee-4", "employee-4", "S2", closes=[{"gap": gid, "sha256": review._sha(g["text"] or "")}])
        if case == "R3":   # the declaration changes after the close was written
            mf = subject / "subject.toml"
            t = mf.read_text(encoding="utf-8")
            assert "owner: compliance)" in t
            mf.write_text(t.replace("owner: compliance)", "owner: compliance; restated)", 1), encoding="utf-8")
        one, two = gate(env, "--scenario", "S2"), gate(env, "--scenario", "S2", "--stage", "2")
        w1, w2 = ([(f["act"]["act"], f["act"]["why"]) for f in acts(r)] for r in (one, two))
        gkey = next(k for k, v in two["levels"].items() if v == "declared_gap") if "declared_gap" in two["levels"].values() else None
        if case == "R2" and (w1 or w2 or two["levels"] != one["levels"]):
            errs.append(f"R2: the close of {gid} reads {w1} at stage 1 and {w2} at stage 2 (want none), levels moved "
                        f"{sorted(k for k in one['levels'] if one['levels'][k] != two['levels'].get(k))}")
        if case == "R3" and (w1 != [("close", "changed")] or w2 != [("close", "changed")] or not gkey):
            errs.append(f"R3: a close of a declaration that changed reads {w1} at stage 1 and {w2} at stage 2 (want one changed close each), "
                        f"OD-1's key {'open' if gkey else 'not open'}")
        print(f"{case}: OD-1's close, {'the declaration restated' if case == 'R3' else 'a table note in stage 2'}: stage 1 {w1 or 'no act'}, stage 2 {w2 or 'no act'}")
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
    if SUBJECT.id == "cargo_quote":   # task-0222: the review files, read again at stage 2
        import tempfile
        sys.path.insert(0, str(ROOT / "tools"))
        with tempfile.TemporaryDirectory() as td:
            errs += reviews_case(Path(td))
    for e in errs:
        print("FAIL", e)
    print(f"stage 2 as a whole re-load on {SUBJECT.id}: " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))

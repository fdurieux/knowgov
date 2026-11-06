"""The lighthouse evaluation protocol's public evidence (task-0069, doc-0013 §5 candidate 8).

    python tools/lighthouse_evidence.py OUT_DIR [--scenarios-cap N] [--only SUBJECT=ID,ID ...] [--transport stdio|http]

The rehearsal half of docs/lighthouse-evaluation.md, on public, synthetic content only. It builds the
example instance (tools/example_instance.py) under OUT_DIR/instance and collects, for CargoQuote
from that instance and for the J-F kit from its subject root, the evidence the protocol's criteria
cite:

    walk           the register's impact walk (the vendored tools/impact.py) from every node the
                   subject's register map names, and the statements a node's anchor reaches in the
                   store (task-0046), on the subject's first scenario
    gate           harness/gate_cli.py on every scenario, verdict and exit code beside the record's;
                   then every other task class the subject declares (CargoQuote's design, task-0101)
                   on the same store with --no-load, its verdict recorded and compared with nothing,
                   since the record's gate is codegen's
    mcp            the read-only MCP server, over stdio or Streamable HTTP (--transport), on the store
                   each gate left: gate_verdict equal to gate_cli --no-load, the three-valued answer
                   with provenance, the evidence bundle an agent reads (evidence_bundle, as of the
                   record; task-0095) with the gate's verdict and date, the census unchanged
    invalidation   a scenario's later version (--stage 2, then --reverify): what was invalidated,
                   what supersedes it, the derived output marked suspect; "none" for a subject
                   without one
    export         the register's export manifest of the subject: each file's digest against the
                   subject's bytes, and its reconciliation record
    cost           wall-clock time per step and the store's size; no model is called

Each subject is collected in a child process (a subject is fixed per process, KG_SUBJECT), each on
its own store (KG_STORE as everywhere; rdflib gets a Turtle file under OUT_DIR). The instance is
digested before and after: the collection writes nothing into it. OUT_DIR/evidence.json holds
everything, OUT_DIR/evidence.md a summary per criterion. Exit 0 when every item was collected and
agrees with the record, 1 when one does not, 2 when the collection could not run.

The pilot half of the protocol is a checklist whose evidence stays in the pilot's private record;
nothing of it is collected here or written into this repository.

Each child reads as of its subject's pinned record date (KG_TODAY at ``[record] as_of``, KG_CLOCK=pinned;
task-0075), so the evidence never moves by the calendar. ``--only jef_data_load=C,D3`` limits one subject
to named scenarios: a pull request's rdflib job runs J-F's subset (task-0084), every other event the full set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
TOOLS = ROOT / "tools"
SETTLED = ("verified", "approved")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(root)).encode() + b"\0" + sha256(p).encode() + b"\n")
    return h.hexdigest()


# ---- the child: one subject -----------------------------------------------------------------------

def gate_cli(*args: str) -> tuple[int, dict | None, str]:
    p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), *args, "-f", "json"],
                       capture_output=True, text=True, env=os.environ.copy())
    try:
        return p.returncode, json.loads(p.stdout), p.stderr.strip()
    except json.JSONDecodeError:
        return p.returncode, None, (p.stderr or p.stdout).strip()


def timed(fn, *a, **k):
    t = time.perf_counter()
    r = fn(*a, **k)
    return r, round(time.perf_counter() - t, 2)


def collect_walk(subject, register: Path, failures: list[str]) -> dict:
    """The register's own walk, from every node the subject's map names (register-only, no store)."""
    import importlib.util
    tools = register / "tools"
    sys.path.insert(0, str(tools))
    mods = {}
    for name in ("register", "impact"):
        spec = importlib.util.spec_from_file_location(name, tools / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        mods[name] = mod
    reg = mods["register"].load_register(register)
    starts = sorted({n for row in subject.register_map().get("row", []) for n in row.get("nodes", [])})
    walks = {}
    for nid in starts:
        if nid not in reg["nodes"]:
            failures.append(f"walk: {nid}, named by the register map, is not in the register")
            continue
        edges = mods["impact"].walk(reg, nid)
        walks[nid] = {"edges": len(edges), "withdrawn": sum(1 for e in edges if not e["live"]),
                      "reached": sorted(mods["impact"].reached(edges))}
    if not walks:
        failures.append("walk: the register map names no node of the register")
    return {"register_nodes": len(reg["nodes"]), "starts": walks}


def node_statements(starts: list[str]) -> dict:
    """task-0046: a register node to the statements its cited anchor names, through the store port."""
    sys.path[:0] = [str(HARNESS), str(ROOT / "demo" / "app")]
    from store import open_store
    import register_project
    register_project.project(open_store(access="write"))   # projects the register, published, and releases the store it is given
    st = open_store(access="read")
    try:
        out = {}
        for nid in starts:
            rows = st.register_node_statements(nid)
            if rows:
                out[nid] = {"statements": len(rows), "documents": sorted({r["document"] for r in rows}),
                            "statuses": {s: sum(1 for r in rows if r["status"] == s) for s in sorted({r["status"] for r in rows})}}
        return out
    finally:
        st.close()


def collect_mcp(sc: str, keys: list[str], expected: dict, failures: list[str], transport: str = "stdio",
                declared: list[str] | None = None) -> dict:
    sys.path.insert(0, str(TOOLS))
    from check_mcp_server import HttpClient, StdioClient, census
    if declared is None:
        from tasks import TASKS
        declared = list(TASKS)
    before = census()
    client = HttpClient() if transport == "http" else StdioClient()
    try:
        status = client.call("store_status", {})
        classes = sorted(status["tasks"])
        if classes != sorted(declared):
            failures.append(f"mcp {sc}: store_status lists task classes {classes}, the subject declares {sorted(declared)}")
        verdict = client.call("gate_verdict", {"scenario": sc})
        equal = verdict == expected
        if not equal:
            failures.append(f"mcp {sc}: gate_verdict differs from gate_cli --no-load")
        answers = {}
        for key in keys:
            ans = client.call("three_valued_answer", {"key": key, "scenario": sc})
            prov = all(s.get("artefact") and "fragments" in s for s in ans["statements"])
            if not prov:
                failures.append(f"mcp {sc} {key}: a statement without provenance")
            answers[key] = {"answer": ans["answer"], "statements": len(ans["statements"]), "provenance": prov,
                            "invalidated": ans.get("invalidated", [])}
        # criterion 4 by the agent's path (task-0095): the bundle as the server hands it. Its text equals the
        # governed arm's bundle by tools/check_mcp_server.py (task-0080), in the same job on the same
        # scenarios; rebuilding it here would read the store twice more per scenario for the same proof
        got = client.call("evidence_bundle", {"scenario": sc, "as_of": "record"})
        agrees = got["verdict"] == verdict["verdict"] and got["as_of"] == verdict["as_of"] and bool(got["bundle"])
        if not agrees:
            failures.append(f"mcp {sc}: evidence_bundle says {got['verdict']} as of {got['as_of']}, "
                            f"gate_verdict {verdict['verdict']} as of {verdict['as_of']}")
        bundle = {"verdict": got["verdict"], "as_of": got["as_of"], "version": got["version"],
                  "characters": len(got["bundle"]), "sha256": hashlib.sha256(got["bundle"].encode("utf-8")).hexdigest(),
                  "assertions": len(got["assertion_ids"]), "verbatim": got["verbatim"], "agrees_with_gate": agrees}
    finally:
        client.close()
    unchanged = census() == before
    if not unchanged:
        failures.append(f"mcp {sc}: the store changed while the server read it")
    return {"transport": transport, "task_classes": classes, "gate_verdict_equals_gate_cli": equal, "three_valued": answers,
            "evidence_bundle": bundle, "store_unchanged": unchanged}


def child(out: Path, cap: int | None, only: list[str] | None = None, transport: str = "stdio") -> int:
    sys.path.insert(0, str(HARNESS))
    import cadence
    from subject import SUBJECT
    from tasks import TASKS
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075)
    failures: list[str] = []
    ev: dict = {"subject": SUBJECT.id, "root": os.environ.get("KG_SUBJECT"), "store": (os.environ.get("KG_STORE") or "neo4j").lower(),
                "register": os.environ.get("KG_REGISTER"), "timings_s": {}}
    register = Path(os.environ.get("KG_REGISTER") or ROOT / "demo" / "register")

    ev["walk"], ev["timings_s"]["walk"] = timed(collect_walk, SUBJECT, register, failures)

    scenarios = list(SUBJECT.order)[:cap] if cap else list(SUBJECT.order)
    if only:
        unknown = [sc for sc in only if sc not in SUBJECT.order]
        if unknown:
            failures.append(f"--only names scenarios {SUBJECT.id} does not declare: {unknown}")
        scenarios = [sc for sc in scenarios if sc in only]
    ev["scenarios"] = scenarios
    gates, mcp = {}, {}
    for i, sc in enumerate(scenarios):
        (code, rep, err), t = timed(gate_cli, "--scenario", sc, "--publish")   # the MCP reads below read this load (decision-0017)
        ev["timings_s"][f"gate {sc}"] = t
        if rep is None or code == 2:
            failures.append(f"gate {sc}: could not run: {err}")
            continue
        rel = SUBJECT.scenario(sc).get("deterministic_record") or sc
        rec_p = SUBJECT.record_dir / rel / "deterministic.json"
        rec = json.loads(rec_p.read_text(encoding="utf-8")) if rec_p.exists() else None
        rec_verdict = rec["D6_gate"]["verdict"] if rec else None
        if rec_verdict and rec_verdict != rep["verdict"]:
            failures.append(f"gate {sc}: {rep['verdict']}, the record says {rec_verdict}")
        gates[sc] = {"verdict": rep["verdict"], "exit_code": code, "record_verdict": rec_verdict, "counts": rep["counts"],
                     "keys": rep["keys"], "classes": {"codegen": {"verdict": rep["verdict"], "exit_code": code}}}
        # every other class on the store this gate loaded (task-0101): the record holds codegen's only
        for t in sorted(set(TASKS) - {"codegen"}):
            (c_t, r_t, e_t), tt = timed(gate_cli, "--scenario", sc, "--task", t, "--no-load")
            ev["timings_s"][f"gate {sc} {t}"] = tt
            if r_t is None or c_t == 2:
                failures.append(f"gate {sc} --task {t}: could not run: {e_t}")
                continue
            gates[sc]["classes"][t] = {"verdict": r_t["verdict"], "exit_code": c_t, "counts": r_t["counts"]}
        if i == 0:
            starts = sorted(ev["walk"]["starts"])
            ev["walk"]["statements_at_anchor"], ev["timings_s"]["walk statements"] = timed(node_statements, starts)
            ev["walk"]["statements_scenario"] = sc
        nl_code, expected, err = gate_cli("--scenario", sc, "--no-load")
        if expected is None:
            failures.append(f"mcp {sc}: gate_cli --no-load could not run: {err}")
            continue
        # the subject's three-valued keys; a subject that names none is asked of its codegen task's first keys
        keys = list(SUBJECT.three_valued) or (list(TASKS["codegen"]["keys"])[:3] if "codegen" in TASKS else [])
        mcp[sc], ev["timings_s"][f"mcp {sc}"] = timed(collect_mcp, sc, keys, expected, failures, transport, list(TASKS))
    ev["gate"], ev["mcp"] = gates, mcp

    inval = {}
    for sc in scenarios:
        cfg2 = SUBJECT.scenario(sc).get("stage2")
        if not cfg2:
            continue
        (c1, before, e1), t1 = timed(gate_cli, "--scenario", sc, "--stage", "2", "--publish")
        (c2, after, e2), t2 = timed(gate_cli, "--scenario", sc, "--stage", "2", "--reverify", "--publish")
        ev["timings_s"][f"stage 2 {sc}"] = round(t1 + t2, 2)
        if before is None or after is None:
            failures.append(f"invalidation {sc}: could not run: {e1 or e2}")
            continue
        rec2 = json.loads((SUBJECT.record_dir / (SUBJECT.scenario(sc).get("deterministic_record") or sc) / "deterministic.json")
                          .read_text(encoding="utf-8")).get("stage2", {})
        want = sorted(x["id"] for x in rec2.get("D3_stale", {}).get("invalidated", []))
        if before["change"]["invalidated"] != want:
            failures.append(f"invalidation {sc}: invalidated {before['change']['invalidated']}, the record {want}")
        inval[sc] = {"artefact": before["change"]["artefact"], "version": before["version"],
                     "invalidated": before["change"]["invalidated"],
                     "before_reverification": {"verdict": before["verdict"], "exit_code": c1},
                     "after_reverification": {"verdict": after["verdict"], "exit_code": c2,
                                              "reverified": after["change"]["reverified_statements"],
                                              "suspect_derived": after["suspect_derived"],
                                              "superseded_by": after.get("superseded_by")}}
    ev["invalidation"] = inval or "none: the subject declares no later version of a document"

    ev["export"] = collect_export(SUBJECT, register, failures)

    sys.path.insert(0, str(TOOLS))
    from check_mcp_server import census
    ev["store_census"] = census()
    ev["failures"] = failures
    out.write_text(json.dumps(ev, indent=1, default=str) + "\n", encoding="utf-8")
    return 1 if failures else 0


def collect_export(subject, register: Path, failures: list[str]) -> dict:
    """The register's export manifest of the subject: every file's digest against the subject's bytes."""
    import tomllib
    rel = subject.register.get("export_manifest")
    if not rel:
        return {"manifest": None, "note": "the subject names no export manifest"}
    mp = register / rel
    if not mp.exists():
        failures.append(f"export: {mp} does not exist")
        return {"manifest": rel}
    man = tomllib.loads(mp.read_text(encoding="utf-8"))
    files = man.get("files", {})
    arts = [(a["key"], a.get("path")) for a in subject.artefacts if a.get("path")]
    match, differ, missing = 0, [], []
    for name, digest in files.items():
        hit = next(((k, p) for k, p in arts if k == name or (k.endswith("/") and name.startswith(k))), None)
        path = None
        if hit:
            k, p = hit
            path = subject.path(p) if k == name else subject.path(p) / name[len(k):]
        if path is None or not path.exists():
            # a file of the export that is not one of the subject's documents (a README, a revision record)
            kit = subject.path(arts[0][1]).parent if arts else None
            cand = kit / name if kit else None
            if cand is not None and cand.exists():
                path = cand
        if path is None or not path.exists():
            missing.append(name)
        elif sha256(path) == digest:
            match += 1
        else:
            differ.append(name)
    if differ:
        failures.append(f"export: {len(differ)} file(s) differ from the manifest's digests: {differ[:5]}")
    rec = mp.parent / "RECONCILE.json"
    reconcile = json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else None
    return {"manifest": rel, "exported_on": str(man.get("exported_on")), "source": man.get("source"),
            "source_version": man.get("source_version"), "files": len(files), "digest_match": match,
            "digest_differ": differ, "not_found_in_subject": missing,
            "reconcile": {"present": reconcile is not None,
                          "files_added": len((reconcile or {}).get("files", {}).get("added", []))}}


# ---- the parent: build the instance, run each subject, summarise --------------------------------

def summary(ev: dict) -> str:
    out = ["# Lighthouse evaluation: public evidence", "",
           f"Collected by `tools/lighthouse_evidence.py` on the {ev['store']} store. "
           f"Example instance unchanged: {'yes' if ev['instance_unchanged'] else 'NO'}.", ""]
    for s in ev["subjects"]:
        out.append(f"## {s['subject']}")
        out.append("")
        w = s["walk"]
        out.append(f"- **Walk**: {len(w['starts'])} register node(s) the subject's map names, out of {w['register_nodes']}; "
                   + ", ".join(f"{n} reaches {len(v['reached'])}" for n, v in list(w["starts"].items())[:6])
                   + (" …" if len(w["starts"]) > 6 else ""))
        if w.get("statements_at_anchor"):
            out.append(f"- **Statements at an anchor** ({w.get('statements_scenario')}): "
                       + ", ".join(f"{n}: {v['statements']}" for n, v in w["statements_at_anchor"].items()))
        out.append("- **Gate**: " + ", ".join(f"{sc} {g['verdict']} (exit {g['exit_code']}; record {g['record_verdict'] or '-'})" for sc, g in s["gate"].items()))
        others = sorted({t for g in s["gate"].values() for t in g.get("classes", {})} - {"codegen"})
        for t in others:
            out.append(f"- **Gate, {t} class** (no record): " + ", ".join(
                f"{sc} {g['classes'][t]['verdict']} (exit {g['classes'][t]['exit_code']})" for sc, g in s["gate"].items() if t in g.get("classes", {})))
        eq = all(m["gate_verdict_equals_gate_cli"] for m in s["mcp"].values())
        un = all(m["store_unchanged"] for m in s["mcp"].values())
        answers = sorted({a["answer"] for m in s["mcp"].values() for a in m["three_valued"].values()})
        bundles = [m["evidence_bundle"] for m in s["mcp"].values() if m.get("evidence_bundle")]
        transport = next((m.get("transport") for m in s["mcp"].values()), None) or "stdio"
        listed = sorted({c for m in s["mcp"].values() for c in m.get("task_classes", [])})
        out.append(f"- **MCP** (over {transport}): task classes store_status lists: {', '.join(listed) or 'not collected'}; gate_verdict equal to gate_cli on {len(s['mcp'])} scenario(s): {'yes' if eq else 'NO'}; "
                   f"three-valued answers seen: {', '.join(answers) or 'none'}; store unchanged by the server: {'yes' if un else 'NO'}")
        if bundles:
            same = all(b["agrees_with_gate"] for b in bundles)
            out.append(f"- **Evidence bundle over MCP**: evidence_bundle's verdict and date those of gate_verdict on {len(bundles)} scenario(s): "
                       f"{'yes' if same else 'NO'}; " + ", ".join(f"{sc} {m['evidence_bundle']['verdict']} "
                       f"({m['evidence_bundle']['assertions']} assertion(s), {m['evidence_bundle']['characters']:,} characters)"
                       for sc, m in s["mcp"].items() if m.get("evidence_bundle")))
        inv = s["invalidation"]
        if isinstance(inv, dict):
            for sc, v in inv.items():
                a = v["after_reverification"]
                out.append(f"- **Invalidation** ({sc}, {v['artefact']} {v['version']}): {len(v['invalidated'])} statement(s) invalidated; "
                           f"before re-verification {v['before_reverification']['verdict']}, after {a['verdict']} (exit {a['exit_code']}); "
                           f"suspect: {', '.join(a['suspect_derived']) or 'none'}; superseded_by: "
                           + (", ".join(f"{k} → {', '.join(x)}" for k, x in (a['superseded_by'] or {}).items()) or "not reported"))
        else:
            out.append(f"- **Invalidation**: {inv}")
        e = s["export"]
        out.append(f"- **Export manifest** {e.get('manifest')}: {e.get('files')} file(s), {e.get('digest_match')} digest(s) match the subject's bytes"
                   + (f", {len(e['not_found_in_subject'])} not among the subject's documents" if e.get("not_found_in_subject") else "")
                   + f"; reconciliation record {'present' if e.get('reconcile', {}).get('present') else 'absent'}")
        total = sum(s["timings_s"].values())
        out.append(f"- **Cost**: {total:.0f} s wall clock for the whole collection, no model call; store "
                   f"{s['store_census'].get('nodes')} nodes, {s['store_census'].get('relationships')} relationships after the last step")
        out.append("")
    out.append("Criterion 6, executing business actions, is out of scope: knowgov executes none (docs/lighthouse-evaluation.md).")
    if ev["failures"]:
        out += ["", "## Failures", ""] + [f"- {f}" for f in ev["failures"]]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", help="a directory that does not exist or is empty")
    ap.add_argument("--scenarios-cap", type=int, help="only the first N scenarios of each subject (a quicker rehearsal)")
    ap.add_argument("--only", action="append", default=[], metavar="SUBJECT=ID,ID",
                    help="only these scenarios of that subject (repeatable; a pull request's J-F subset, task-0084)")
    ap.add_argument("--transport", choices=("stdio", "http"), default="stdio",
                    help="how the MCP client reaches the server: stdio (default) or Streamable HTTP on loopback")
    ap.add_argument("--child", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    only: dict[str, list[str]] = {}
    for o in args.only:
        name, _, ids = o.partition("=")
        if not ids:
            ap.error(f"--only {o!r}: want SUBJECT=ID,ID")
        only[name] = [x for x in ids.split(",") if x]
    if args.child:
        return child(Path(args.child), args.scenarios_cap, next(iter(only.values()), None), args.transport)
    unknown = sorted(set(only) - {"cargo_quote", "jef_data_load"})
    if unknown:
        ap.error(f"--only: no subject {unknown[0]!r} here; cargo_quote or jef_data_load")
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        print(f"lighthouse: {out} is not empty", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    inst = out / "instance"
    p = subprocess.run([sys.executable, str(TOOLS / "example_instance.py"), str(inst)], capture_output=True, text=True)
    if p.returncode != 0:
        print(f"lighthouse: the example instance could not be built:\n{p.stdout}{p.stderr}", file=sys.stderr)
        return 2
    before = tree_digest(inst)
    store = (os.environ.get("KG_STORE") or "neo4j").lower()
    runs = [("cargo_quote", inst / "subjects" / "cargo_quote", inst / "register"),
            ("jef_data_load", ROOT / "subjects" / "jef_data_load", ROOT / "demo" / "register")]
    subjects, failures = [], []
    for name, root, register in runs:
        env = os.environ.copy()
        env.update({"KG_SUBJECT": str(root), "KG_REGISTER": str(register), "PYTHONDONTWRITEBYTECODE": "1"})
        if store == "rdflib":
            env["KG_RDFLIB_FILE"] = str(out / f"store-{name}.ttl")
        part = out / f"evidence-{name}.json"
        cmd = [sys.executable, str(Path(__file__).resolve()), str(out), "--child", str(part), "--transport", args.transport]
        if args.scenarios_cap:
            cmd += ["--scenarios-cap", str(args.scenarios_cap)]
        if name in only:
            cmd += ["--only", f"{name}={','.join(only[name])}"]
        r = subprocess.run(cmd, env=env, cwd=ROOT, text=True, capture_output=True)
        if not part.exists():
            print(f"lighthouse: {name} could not be collected:\n{r.stdout}{r.stderr}", file=sys.stderr)
            return 2
        ev = json.loads(part.read_text(encoding="utf-8"))
        subjects.append(ev)
        failures += [f"{name}: {f}" for f in ev["failures"]]
        print(f"{name}: collected, {len(ev['failures'])} failure(s)")
    unchanged = tree_digest(inst) == before
    if not unchanged:
        failures.append("the example instance changed during the collection")
    ev = {"tool": "knowgov lighthouse evidence", "store": store, "instance_unchanged": unchanged,
          "subjects": subjects, "failures": failures}
    (out / "evidence.json").write_text(json.dumps(ev, indent=1, default=str) + "\n", encoding="utf-8")
    text = summary(ev)
    (out / "evidence.md").write_text(text, encoding="utf-8")
    print(text)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

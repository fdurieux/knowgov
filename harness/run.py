"""Orchestration: per scenario, load -> rules -> D measures -> arms -> grade.

    python run.py --deterministic            # D1-D6 only, no model
    python run.py --scenarios S1 --n 1       # calibration
    python run.py --n 5                      # the scored run

Results land in runs/<scenario>/ (or --out) with SHA256SUMS of
the harness and kit written beside them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arms
import measures
import shacl
from gate import resolve, render_bundle
from kitio import kit_for, kit_text, sha256, verbatim_documents
import agent
from load import PROV, HUMAN, load_inferred, load_scenario, load_verifications, pristine_values
from store import open_store
from plant import INFERRED
from rules import census, r_stale, run_all
from subject import HERE as HARNESS, ROOT, SUBJECT

RESULTS = SUBJECT.record_dir       # the subject's record, vendored and never written
RUNS = ROOT / "runs"               # where a run lands unless --out says otherwise
ORDER = SUBJECT.order_keys         # the baseline arm concatenates the documents in this order
SCENARIOS = SUBJECT.order


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


def d5(s) -> dict:
    """The three-valued answer for the keys the subject names."""
    out = {}
    for key in SUBJECT.three_valued:
        rows = s.assertions_on_key(key, ["verified", "approved", "validated", "proposed"])
        if not rows:
            out[key] = {"answer": "unknown", "why": "no assertion for this key (not a documented absence)"}
        elif all(r["value"] == "NONE" for r in rows):
            out[key] = {"answer": "documented_absent", "assertions": rows}
        else:
            out[key] = {"answer": "asserted", "assertions": rows}
    return out


def deterministic(sc: str, pv: dict, s) -> dict:
    cfg = SUBJECT.scenario(sc)
    s.wipe()
    d1 = s.apply_constraints()
    kit = kit_for(sc)
    planted = cfg.get("extraction", "pristine") == "planted"
    load = load_scenario(s, sc, kit, activity_note=f"{sc}: extraction of the {'planted' if planted else 'pristine'} kit")
    ver = load_verifications(s, sc, pv, kit) if cfg.get("verifications", True) else {"skipped": f"{sc}: extraction only"}
    if cfg.get("inferred") and INFERRED:
        load_inferred(s, sc, INFERRED)
    rules = run_all(s, sc)
    cen = census(s)
    gate = resolve(s, "codegen")
    out = {"scenario": sc, "store": s.name, "D1_constraints": d1, "load": load, "verifications": ver, "rules": rules,
           "D2_census": cen, "D4_shacl": shacl.run(s), "D6_gate": {k: v for k, v in gate.items() if k != "keys"},
           "gate_keys": {k: {"level": v["level"], "flags": v["flags"], "n": len(v["assertions"])} for k, v in gate["keys"].items()}}
    if cfg.get("three_valued"):
        out["D5_three_valued"] = d5(s)
    return out, gate, kit


def stage2(sc: str, cfg2: dict, pv: dict, s, derived_code: str | None, derived_ids: list[str]) -> tuple[dict, dict, dict]:
    """The scenario's second stage (the subject's ``[scenario.stage2]``): register the earlier
    governed output as derived, re-ingest the changed artefact as a new version, invalidate what
    rested on the changed fragments, then record the re-verification of the named keys."""
    version = cfg2.get("version", "v2")
    derived = cfg2.get("derived", {})
    if derived_code:
        s.register_derived(derived.get("id", f"derived:{sc}"), derived.get("kind", "artefact"), sha256(derived_code), derived_ids)
    kit2 = kit_for(sc, 2)
    art = cfg2["artefact"]
    load2 = load_scenario(s, sc, {art: kit2[art]}, activity_note=cfg2.get("note", f"{sc} stage 2: re-ingestion of the changed {art}"),
                          version_tag=version, reingest=True)
    stale = r_stale(s, version)
    rules2 = {"R-STRUCT": run_all(s, sc)["R-STRUCT"]}
    gate_blocked = resolve(s, "codegen")
    # the recorded re-verification of the new assertions on the named keys, by the owner stand-in
    rever = s.reverify(version, list(cfg2.get("reverify_keys", [])), HUMAN["id"], cfg2.get("at", ""),
                       cfg2.get("reverify_scope", "re-verification"), cfg2.get("reapproval_record", "re-approval"))
    # new-version assertions of unchanged fragments inherit nothing automatically: they are new statements.
    # Corroboration and verification of them against the pristine values:
    load_verifications(s, sc, dict(pv), kit2)
    gate_after = resolve(s, "codegen")
    stage2 = {"load_v2": load2, "D3_stale": stale, "R-STRUCT_after": rules2["R-STRUCT"],
              "gate_before_reverification": {k: v for k, v in gate_blocked.items() if k != "keys"},
              "reverified": rever,
              "gate_after_reverification": {k: v for k, v in gate_after.items() if k != "keys"},
              "census_after": census(s),
              "suspect_derived": s.all_derived()}
    return stage2, gate_after, kit2


def arm_runs(sc: str, arm: str, n: int, kit: dict, gate: dict, task_name: str, out_dir: Path,
             resume: bool = False) -> list[dict]:
    system = arms.prompt("system")
    if arm == "B":
        user = arms.prompt(f"{task_name}_baseline") + arms.baseline_documents(kit, ORDER)
        bundle_ids: set[str] = set()
    else:
        # the documents the task names as needed verbatim (subject.toml [tasks.<task>] verbatim), as the
        # scenario's kit holds them: the bundle carries assertions, and a parser table or a packaged
        # configuration file is not an assertion; without them the arm asks for them and abstains
        verbatim = verbatim_documents(kit, task_name)   # task_name is the prompt prefix; the table's key is the class
        bundle = render_bundle(gate, arms.policy(), verbatim)
        user = arms.prompt(f"{task_name}_governed") + bundle
        bundle_ids = {a["id"] for v in gate["keys"].values() for a in v["assertions"]}
        (out_dir / f"bundle_{arm}.txt").write_text(bundle, encoding="utf-8")
    (out_dir / f"prompt_{arm}.txt").write_text(user, encoding="utf-8")
    print(f"    {arm}: {n} call(s) to {arms.MODEL}, {len(user):,} characters of prompt each; the suite runs on each reply", flush=True)

    agent_kind = SUBJECT.arms.get("kind", "reply") == "agent"
    if agent_kind:
        cfg = SUBJECT.arms.get("agent", {})
        system = arms.prompt(cfg.get("system_prompt", "system_agent"))
        user = user + "\n\n" + cfg.get("layout", "")
        feedback = measures.feedback_runner(kit, cfg["feedback"])
        docs_g = verbatim_documents(kit, task_name)

        def read_text(path: str) -> str:
            """B reads any kit document; G reads the documents the task names verbatim, the bundle holding the knowledge."""
            if arm == "B":
                return kit_text(kit, path)
            if path in docs_g:
                return docs_g[path]
            raise KeyError(f"{path}: not a document the task names verbatim; the bundle holds the knowledge")
        (out_dir / f"prompt_{arm}.txt").write_text(user, encoding="utf-8")
        print(f"    {arm}: agent loop, ceiling {agent.ceiling()}", flush=True)

    def one(i: int) -> dict:
        done = out_dir / f"run{i}_{arm}.json"
        if resume and done.exists():
            prev = json.loads(done.read_text(encoding="utf-8"))
            if "api_error" not in prev:
                return prev
        if agent_kind:
            return one_agent(i)
        try:
            r = arms.call(system, user, tag=f"{sc}/{arm}/{i}")
        except Exception as e:  # noqa: BLE001 — recorded as a failed cell, never silently dropped
            rec = {"scenario": sc, "arm": arm, "run": i, "api_error": str(e)[:300], "M1_decision": None,
                   "M2_code": False, "M3_flagged": {"flagged": False, "hits": []}, "M4_suite": {"ran": False, "passed": 0, "total": 11, "per_scenario": {}},
                   "M4_targets": {}, "outage_status": None, "M5_refs": {"total": 0, "resolved": 0, "share": None},
                   "M6_noncompliance": False, "questions": None, "assumptions": None, "claims": None,
                   "usage": {"prompt_tokens": 0, "completion_tokens": 0, "attempts": 4}}
            dump(done, rec)
            return rec
        p = r["parsed"] if isinstance(r["parsed"], dict) else None
        code = p.get("code") if p else None
        if code is not None and not isinstance(code, str):
            code = None
        suite = measures.run_suite(code, sc)
        rec = {"scenario": sc, "arm": arm, "run": i, "parse_error": r["parse_error"],
               "M1_decision": (p or {}).get("decision"), "M2_code": bool(code),
               "M3_flagged": measures.flagged(sc, p), "M4_suite": suite,
               "M4_targets": {t: suite["per_scenario"].get(t, {}).get("passed") for t in (measures.TARGETS[sc] or [])},
               "outage_status": measures.outage_status(suite) if suite["ran"] else None,
               "M5_refs": measures.resolvable_refs(arm, p, bundle_ids, kit),
               "M6_noncompliance": (arm == "G" and ((gate["verdict"] == "BLOCKED" and bool(code)) or
                                                     (gate["verdict"] == "QUALIFIED" and (p or {}).get("decision") == "generate"))),
               "questions": (p or {}).get("questions"), "assumptions": (p or {}).get("assumptions"),
               "claims": (p or {}).get("claims"), "usage": r["usage"]}
        dump(out_dir / f"run{i}_{arm}.json", rec)
        (out_dir / f"run{i}_{arm}.raw.json").write_text(r["raw"], encoding="utf-8")
        if code:
            (out_dir / f"run{i}_{arm}.py").write_text(code, encoding="utf-8")
        return rec
    def one_agent(i: int) -> dict:
        box = out_dir / f"run{i}_{arm}_sandbox"
        res = agent.run(system, user, sandbox=box, read_text=read_text, feedback=feedback, tag=f"{sc}/{arm}/{i}")
        p = res["parsed"]
        suite = measures.run_suite_dir(box, sc) if res["files"] else {"ran": False, "passed": 0, "total": measures.SUITE_TOTAL, "per_scenario": {}}
        code_text = agent.Sandbox(box).text() if res["files"] else None
        tt = res["totals"]
        rec = {"scenario": sc, "arm": arm, "run": i, "parse_error": None,
               "M1_decision": p.get("decision"), "M2_code": bool(res["files"]),
               "M3_flagged": measures.flagged(sc, p), "M4_suite": suite,
               "M4_targets": {t: suite["per_scenario"].get(t, {}).get("passed") for t in (measures.TARGETS[sc] or [])},
               "outage_status": measures.outage_status(suite) if suite["ran"] else None,
               "M5_refs": measures.resolvable_refs(arm, p, bundle_ids, kit),
               "M6_noncompliance": (arm == "G" and ((gate["verdict"] == "BLOCKED" and bool(res["files"])) or
                                                     (gate["verdict"] == "QUALIFIED" and p.get("decision") == "generate"))),
               "questions": p.get("questions"), "assumptions": p.get("assumptions"), "claims": p.get("claims"),
               "usage": {"model": tt["model"], "prompt_tokens": tt["prompt_tokens"], "completion_tokens": tt["completion_tokens"],
                         "seconds": tt["seconds"], "usd_est": tt["usd"], "attempts": tt["calls"]},
               "agent": {"finished": res["finished"], "stopped_by": res["stopped_by"], "turns": tt["turns"], "calls": tt["calls"],
                         "tool_calls": tt["tool_calls"], "files": res["files"], "ceiling": res["ceiling"], "sandbox": box.name}}
        if res["stopped_by"] and res["stopped_by"].startswith("api error"):
            rec["api_error"] = res["stopped_by"]
        dump(out_dir / f"run{i}_{arm}.json", rec)
        dump(out_dir / f"run{i}_{arm}.trace.json", res["trace"])
        if code_text:
            (out_dir / f"run{i}_{arm}.py").write_text(code_text, encoding="utf-8")
        return rec

    with ThreadPoolExecutor(max_workers=int(__import__("os").environ.get("KG_WORKERS", "5"))) as ex:
        return list(ex.map(one, range(1, n + 1)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--out", default=str(RUNS))
    ap.add_argument("--resume", action="store_true", help="skip cells whose run json exists")
    args = ap.parse_args()
    out_root = Path(args.out)
    pv = pristine_values()
    d = open_store(instance=SUBJECT.id)
    summary = {}
    for sc in args.scenarios:
        out_dir = out_root / sc
        out_dir.mkdir(parents=True, exist_ok=True)
        det, gate, kit = deterministic(sc, pv, d)   # one store, one scenario at a time
        cfg = SUBJECT.scenario(sc)
        task = cfg.get("prompts", "task_codegen")
        runs = {}
        if cfg.get("stage2"):
            # stage 1 is the pristine graph; the derived artefact is an earlier scenario's governed
            # output if it exists, in both modes: the file is an input of the deterministic stage 2,
            # not an arm call (pumllint's record under d3check shows the state before that held)
            derived = cfg["stage2"].get("derived", {})
            code_path = out_root / derived.get("from_scenario", sc) / derived.get("file", "run1_G.py")
            derived_code = code_path.read_text(encoding="utf-8") if code_path.exists() else None
            derived_ids = [a["id"] for v in gate["keys"].values() for a in v["assertions"]] if derived_code else []
            s2, gate, kit = stage2(sc, cfg["stage2"], pv, d, derived_code, derived_ids)
            det["stage2"] = s2
        dump(out_dir / "deterministic.json", det)
        print(f"{sc}: gate {det['D6_gate']['verdict']} — {det['D6_gate']['why']}", flush=True)
        if cfg.get("stage2"):
            print(f"    stage 2: invalidated {[x['key'] for x in det['stage2']['D3_stale']['invalidated']]}; "
                  f"before re-verification {det['stage2']['gate_before_reverification']['verdict']}, after {det['stage2']['gate_after_reverification']['verdict']}", flush=True)
        if not args.deterministic:
            for arm in ("B", "G"):
                runs[arm] = arm_runs(sc, arm, args.n, kit, gate, task, out_dir, resume=args.resume)
                print(f"    {arm}: decisions {[r['M1_decision'] for r in runs[arm]]}; code {[r['M2_code'] for r in runs[arm]]}; "
                      f"suite {[r['M4_suite']['passed'] for r in runs[arm]]}; flagged {[r['M3_flagged']['flagged'] for r in runs[arm]]}", flush=True)
        summary[sc] = {"gate": det["D6_gate"]["verdict"],
                       "runs": {arm: [{k: r[k] for k in ("run", "M1_decision", "M2_code", "M3_flagged", "M4_targets", "outage_status", "M5_refs", "M6_noncompliance")} | {"suite": f"{r['M4_suite']['passed']}/{r['M4_suite']['total']}"} for r in rs] for arm, rs in runs.items()}}
    d.close()
    dump(out_root / "summary.json", summary)
    prev_usage = json.loads((out_root / "usage.json").read_text()) if (out_root / "usage.json").exists() else None
    u = arms.usage()
    if prev_usage:
        u = {"calls": prev_usage["calls"] + u["calls"], "usd_est": round(prev_usage["usd_est"] + u["usd_est"], 4),
             "retries": prev_usage.get("retries", []) + u["retries"], "per_call": prev_usage["per_call"] + u["per_call"],
             "segments": prev_usage.get("segments", 1) + 1}
    dump(out_root / "usage.json", u)
    # digests of what ran
    lines = []
    for p in sorted([*HARNESS.rglob("*.py"), *HARNESS.rglob("*.md"), *SUBJECT.definition_files()]):
        if p.is_file() and "__pycache__" not in str(p):
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}")
    (out_root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("usage:", arms.usage()["calls"], "calls, est $", arms.usage()["usd_est"])


if __name__ == "__main__":
    main()

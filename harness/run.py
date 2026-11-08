"""Orchestration: per scenario, load -> rules -> D measures -> arms -> grade.

    python run.py --deterministic            # D1-D6 only, no model
    python run.py --scenarios S1 --n 1       # calibration
    python run.py --n 5                      # the scored run
    python run.py --deterministic --as-of 2027-09-01   # read review currency as of that date (decision-0005)

Results land in runs/<scenario>/ (or --out) with SHA256SUMS of
the harness and kit written beside them.
"""

from __future__ import annotations

if __name__ == "__main__":   # task-0200: a failure while loading (a pin not installed) is exit 2, its cause in one line
    import cli_exit
    cli_exit.guard("run")

import argparse
import hashlib
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arms
import cadence
import execution
import measures
import shacl
from gate import resolve, render_bundle, render_index, knowledge_reader, three_valued
from kitio import kit_for, kit_text, verbatim_documents
import agent
from load import PROV, load_captures, load_inferred, load_reviews, load_scenario, load_verifications, pristine_values
from store import open_store
import load_memory
from change import apply_change, reverify, unit_loads
from plant import INFERRED
from rules import census, run_all
from subject import HERE as HARNESS, ROOT, SUBJECT

RESULTS = SUBJECT.record_dir       # the subject's record, vendored and never written
RUNS = ROOT / "runs"               # where a run lands unless --out says otherwise
ORDER = SUBJECT.order_keys         # the baseline arm concatenates the documents in this order
SCENARIOS = SUBJECT.order


# The code files this invocation wrote (task-0203, R3): stage 2 reads its derived output from here, or from
# --stage2-derived, never from a file an earlier attempt left in a reused --out
WRITTEN: set[Path] = set()


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


def gate_summary(g: dict) -> dict:
    """The gate's result as the record holds it: without its keys and without the as-of date, which
    the run records once, at its top (decision-0005), and without how each attestation was read (decision-0019,
    task-0221), whose effect the record holds in its levels and verdict."""
    return {k: v for k, v in g.items() if k not in ("keys", "as_of", "attestation")}


def d5(s) -> dict:
    """The three-valued answer for the keys the subject names."""
    return {key: three_valued(s, key) for key in SUBJECT.three_valued}


def deterministic(sc: str, pv: dict, s, as_of=None) -> dict:
    cfg = SUBJECT.scenario(sc)
    s.wipe()
    d1 = s.apply_constraints()
    kit = kit_for(sc)
    planted = cfg.get("extraction", "pristine") == "planted"
    load = load_scenario(s, sc, kit, activity_note=f"{sc}: extraction of the {'planted' if planted else 'pristine'} kit")
    ver = load_verifications(s, sc, pv, kit) if cfg.get("verifications", True) else {"skipped": f"{sc}: extraction only"}
    if cfg.get("inferred") and INFERRED:
        load_inferred(s, sc, INFERRED)
    captures = load_captures(s, sc)   # answered questionnaires (task-0009); none in a subject without captures/
    rules = run_all(s, sc)
    reviews = load_reviews(s, sc)   # a person's rulings, after the rules (task-0037); none without captures/reviews/
    cen = census(s)
    gate = resolve(s, "codegen", as_of)
    out = {"scenario": sc, "store": s.name, "as_of": gate["as_of"], "D1_constraints": d1, "load": load, "verifications": ver, "rules": rules,
           "D2_census": cen, "D4_shacl": shacl.run(s), "D6_gate": gate_summary(gate),
           "gate_keys": {k: {"level": v["level"], "flags": v["flags"], "n": len(v["assertions"])} for k, v in gate["keys"].items()}}
    if captures["files"]:
        out["captures"] = captures
    if reviews["files"] or reviews["refused"]:
        out["reviews"] = reviews
    if cfg.get("three_valued"):
        out["D5_three_valued"] = d5(s)
    return out, gate, kit


def stage2(sc: str, cfg2: dict, pv: dict, s, derived_code: str | None, derived_ids: list[str], as_of=None) -> tuple[dict, dict, dict]:
    """The scenario's second stage (the subject's ``[scenario.stage2]``): register the earlier
    governed output as derived, re-ingest the changed artefact as a new version, invalidate what
    rested on the changed fragments, then record the re-verification of the named keys. The two
    steps are ``change.py``'s, which the gate command's ``--stage 2`` shares (task-0049)."""
    ch = apply_change(sc, cfg2, s, derived_code, derived_ids)
    gate_blocked = resolve(s, "codegen", as_of)
    rever = reverify(sc, cfg2, pv, s, ch["kit2"])
    gate_after = resolve(s, "codegen", as_of)
    stage2 = {"load_v2": ch["load_v2"], "D3_stale": ch["D3_stale"], "R-STRUCT_after": ch["R-STRUCT_after"],
              "gate_before_reverification": gate_summary(gate_blocked),
              "reverified": rever,
              "gate_after_reverification": gate_summary(gate_after),
              "census_after": census(s),
              "suspect_derived": s.all_derived()}
    return stage2, gate_after, ch["kit2"]


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
        context = cfg.get("context", "push")   # push: the whole bundle or every document in the first message; pull: an index, the reads logged
        system = arms.prompt(cfg.get("system_prompt", "system_agent"))
        feedback = measures.feedback_runner(kit, cfg["feedback"])
        docs_g = verbatim_documents(kit, task_name)
        readers = {}
        consulted_ids: list[str] = []
        if context == "pull":
            if arm == "B":
                index = "\n".join(f"  {k}  ({len(v):,} characters)" for k, v in kit.items())
                user = arms.prompt(f"{task_name}_baseline") + "\nDOCUMENTS, by path; call read_document(path) for each you need (a directory artefact's part is its key plus the part's path):\n" + index
            else:
                user = arms.prompt(f"{task_name}_governed") + render_index(gate, arms.policy(), list(docs_g))
                readers["read_knowledge"], consulted_ids = knowledge_reader(gate)   # the gate's result is the port's; no store call per read
        user = user + "\n\n" + cfg.get("layout", "")

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
            if isinstance(e, arms.PromptCut):   # task-0185: the endpoint read the prompt short; marked, never scored
                rec["prompt_cut"] = e.detail
                rec["usage"] = e.usage or rec["usage"]
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
               "M7_adopted": measures.adopted(arm, p, gate.get("below_verified", []), sc),
               "questions": (p or {}).get("questions"), "assumptions": (p or {}).get("assumptions"),
               "claims": (p or {}).get("claims"), "usage": r["usage"]}
        dump(out_dir / f"run{i}_{arm}.json", rec)
        (out_dir / f"run{i}_{arm}.raw.json").write_text(r["raw"], encoding="utf-8")
        if code:
            (out_dir / f"run{i}_{arm}.py").write_text(code, encoding="utf-8")
            WRITTEN.add((out_dir / f"run{i}_{arm}.py").resolve())
        return rec
    def one_agent(i: int) -> dict:
        box = out_dir / f"run{i}_{arm}_sandbox"
        shutil.rmtree(box, ignore_errors=True)   # task-0203, R3: a fresh cell starts from an empty sandbox, never an earlier attempt's
        res = agent.run(system, user, sandbox=box, read_text=read_text, feedback=feedback, tag=f"{sc}/{arm}/{i}", readers=readers)
        p = res["parsed"]
        cut = res.get("prompt_cut")   # task-0185: a turn the endpoint read short; the run is marked and never graded
        suite = measures.run_suite_dir(box, sc) if res["files"] and not cut else {"ran": False, "passed": 0, "total": measures.SUITE_TOTAL, "per_scenario": {}}
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
               "M7_adopted": measures.adopted(arm, p, gate.get("below_verified", []), sc),
               "questions": p.get("questions"), "assumptions": p.get("assumptions"), "claims": p.get("claims"),
               "usage": {"model": tt["model"], "host": tt["host"], "effort": tt["effort"], "prompt_tokens": tt["prompt_tokens"], "cached_tokens": tt["cached_tokens"], "completion_tokens": tt["completion_tokens"],
                         "hidden_tokens": tt["hidden_tokens"], "counted_tokens": tt["counted_tokens"], "thinking_uncounted": tt["thinking_uncounted"],
                         "seconds": tt["seconds"], "attempts": tt["calls"]},
               "agent": {"finished": res["finished"], "stopped_by": res["stopped_by"], "turns": tt["turns"], "calls": tt["calls"],
                         "tool_calls": tt["tool_calls"], "files": res["files"], "ceiling": res["ceiling"], "sandbox": box.name,
                         "context": context, "consulted": res["consulted"],
                         "consulted_assertions": sorted(set(consulted_ids)) if context == "pull" and arm == "G" else [],
                         # the keys below verified the arm read (G, through read_knowledge) and marked as assumptions (M7)
                         "below_verified": {k: {"read": k in (res["consulted"].get("read_knowledge") or []),
                                                "assumed": k in measures.adopted(arm, p, gate.get("below_verified", []), sc)["adopted"]}
                                            for k in gate.get("below_verified", [])}}}
        if res["stopped_by"] and res["stopped_by"].startswith("api error"):
            rec["api_error"] = res["stopped_by"]
        if cut:
            rec.update(unscored(), api_error=res["stopped_by"], prompt_cut=cut)
        dump(out_dir / f"run{i}_{arm}.json", rec)
        dump(out_dir / f"run{i}_{arm}.trace.json", res["trace"])
        if code_text:
            (out_dir / f"run{i}_{arm}.py").write_text(code_text, encoding="utf-8")
            WRITTEN.add((out_dir / f"run{i}_{arm}.py").resolve())
        return rec

    with ThreadPoolExecutor(max_workers=int(__import__("os").environ.get("KG_WORKERS", "5"))) as ex:
        return list(ex.map(one, range(1, n + 1)))


def unscored() -> dict:
    """The measures of a cell that holds no answer to score (task-0185): no decision, no code, no grade."""
    return {"M1_decision": None, "M2_code": False, "M3_flagged": {"flagged": False, "hits": []},
            "M4_suite": {"ran": False, "passed": 0, "total": measures.SUITE_TOTAL, "per_scenario": {}}, "M4_targets": {},
            "outage_status": None, "M5_refs": {"total": 0, "resolved": 0, "share": None}, "M6_noncompliance": False,
            "M7_adopted": None, "questions": None, "assumptions": None, "claims": None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--out", default=str(RUNS))
    ap.add_argument("--resume", action="store_true", help="skip cells whose run json exists; usage.json then adds to the earlier one")
    ap.add_argument("--stage2-derived", metavar="FILE",
                    help="stage 2's derived output (the code an earlier scenario built, which the change marks suspect): "
                         "this file; by default the one this invocation wrote, never a file left in a reused --out (task-0203)")
    ap.add_argument("--as-of", default="record",
                    help="the date review currency is read on (decision-0005): 'record' (the subject's pinned date, "
                         "the default, which the comparator reads), 'today' or YYYY-MM-DD; the run records it as as_of")
    args = ap.parse_args()
    try:
        as_of = cadence.as_of(args.as_of).isoformat()
    except ValueError as e:
        ap.error(str(e))
    if not args.deterministic and (why := execution.refusal()):
        # task-0141.07: before the store is opened and before the first model call; a run that cannot run (exit 2)
        print(f"run: {why}", file=sys.stderr)
        sys.exit(2)
    out_root = Path(args.out)
    pv = pristine_values()
    d = open_store(instance=SUBJECT.id, access="write")
    summary = {}
    try:
        # before the first load and the first model call: the whole run is one unit (task-0176)
        load_memory.preflight(d, unit_loads(SUBJECT, args.scenarios))   # each scenario's loads, its stage 2's too (doc-0030 S6)
        _run_all(args, d, pv, as_of, out_root, summary)
    except load_memory.LoadTooLarge as e:   # task-0176: refused before the unit's first write; nothing published
        d.close()
        print(f"run: cannot run: {e}", file=sys.stderr)
        sys.exit(2)
    d.commit()   # task-0141.02: published once every scenario ran; an exception above publishes nothing
    d.close()
    _write_usage(out_root, summary, resume=args.resume)


def _run_all(args, d, pv, as_of, out_root, summary) -> None:
    for sc in args.scenarios:
        out_dir = out_root / sc
        out_dir.mkdir(parents=True, exist_ok=True)
        det, gate, kit = deterministic(sc, pv, d, as_of)   # one store, one scenario at a time
        cfg = SUBJECT.scenario(sc)
        task = cfg.get("prompts", "task_codegen")
        runs = {}
        if cfg.get("stage2"):
            # stage 1 is the pristine graph; the derived artefact is an earlier scenario's governed
            # output if it exists, in both modes: the file is an input of the deterministic stage 2,
            # not an arm call (pumllint's record under d3check shows the state before that held)
            derived = cfg["stage2"].get("derived", {})
            code_path = stage2_derived(args, out_root, sc, derived)
            derived_code = code_path.read_text(encoding="utf-8") if code_path is not None and code_path.exists() else None
            derived_ids = [a["id"] for v in gate["keys"].values() for a in v["assertions"]] if derived_code else []
            s2, gate, kit = stage2(sc, cfg["stage2"], pv, d, derived_code, derived_ids, as_of)
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


def stage2_derived(args, out_root: Path, sc: str, derived: dict) -> Path | None:
    """Stage 2's derived output (task-0203, doc-0030 R3): the file ``--stage2-derived`` names, else the one
    this invocation wrote for the scenario the subject names (or, under ``--resume``, its earlier attempt's,
    whose cells are this run's), never a file an earlier attempt left in a reused ``--out``."""
    if getattr(args, "stage2_derived", None):
        return Path(args.stage2_derived)
    path = out_root / derived.get("from_scenario", sc) / derived.get("file", "run1_G.py")
    return path if path.resolve() in WRITTEN or getattr(args, "resume", False) else None


def _write_usage(out_root, summary, resume: bool = False) -> None:
    dump(out_root / "summary.json", summary)
    # task-0203, R3: an earlier attempt's usage adds only under --resume; a fresh run in a reused --out is its own
    prev_usage = json.loads((out_root / "usage.json").read_text()) if resume and (out_root / "usage.json").exists() else None
    u = arms.usage()
    if prev_usage:
        u = {"calls": prev_usage["calls"] + u["calls"], "tokens": prev_usage.get("tokens", 0) + u["tokens"],
             "retries": prev_usage.get("retries", []) + u["retries"], "per_call": prev_usage["per_call"] + u["per_call"],
             "segments": prev_usage.get("segments", 1) + 1}
    dump(out_root / "usage.json", u)
    # digests of what ran
    # an instance's subject and its artefacts live outside the repository (task-0006): such a path is
    # named from the subject root, prefixed with the subject's id; the artefacts are listed too
    def label(p: Path) -> str:
        return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else f"{SUBJECT.id}:{os.path.relpath(p, SUBJECT.root)}"
    arts = [f for _k, a in SUBJECT.kit_files for f in ([a] if a.is_file() else a.rglob("*"))]
    seen, lines = set(), []
    for p in sorted([*HARNESS.rglob("*.py"), *HARNESS.rglob("*.md"), *SUBJECT.definition_files(), *(a.resolve() for a in arts)]):
        if p.is_file() and "__pycache__" not in p.parts and p.resolve() not in seen:
            seen.add(p.resolve())
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {label(p)}")
    (out_root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("usage:", arms.usage()["calls"], "calls,", arms.usage()["tokens"], "tokens")


if __name__ == "__main__":
    import cli_exit   # task-0200 (doc-0030 F6): every failure to run is exit 2 with its cause, never 1
    sys.exit(cli_exit.run(main, "run"))

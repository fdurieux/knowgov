"""M3 keyword sets and M4 targets (frozen in the pre-registration §8, read from the subject's
scenarios), M5 reference resolution, and the suite runner for M4 (the subject's oracle)."""

from __future__ import annotations

import base64
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from subject import SUBJECT

FLAG_WORDS = {sc: list(s.get("flag_words", [])) for sc, s in SUBJECT.scenarios.items()}
# some scenarios need a second word family named as well (pre-registration §8)
CO_WORDS = {sc: list(s["co_words"]) for sc, s in SUBJECT.scenarios.items() if s.get("co_words")}
TARGETS = {sc: (list(s.get("targets", [])) or None) for sc, s in SUBJECT.scenarios.items()}
OVERLAYS = {sc: dict(s["suite_overlays"]) for sc, s in SUBJECT.scenarios.items() if s.get("suite_overlays")}
SUITE_TOTAL = len(SUBJECT.suite_order)


def flagged(scenario: str, parsed: dict | None) -> dict:
    if not parsed:
        return {"flagged": False, "hits": [], "text_len": 0}
    text = " ".join([*(parsed.get("questions") or []),
                     *(a.get("text", "") for a in (parsed.get("assumptions") or []) if isinstance(a, dict))]).lower()
    hits = [w for w in FLAG_WORDS.get(scenario, []) if w in text]
    co = CO_WORDS.get(scenario)
    ok = bool(hits) and (not co or any(w in text for w in co))
    return {"flagged": ok, "hits": hits, "co_hit": (any(w in text for w in co) if co else None), "text_len": len(text)}


def resolvable_refs(arm: str, parsed: dict | None, bundle_ids: set[str], kit: dict[str, str]) -> dict:
    if not parsed:
        return {"total": 0, "resolved": 0, "share": None}
    refs = [x.get("ref", "") for k in ("claims", "assumptions") for x in (parsed.get(k) or []) if isinstance(x, dict)]
    total = len(refs)
    ok = 0
    for ref in refs:
        ref = (ref or "").strip()
        if arm == "G":
            if ref in bundle_ids or ref.split("@")[0] in {b.split("@")[0] for b in bundle_ids}:
                ok += 1
        else:
            m = re.match(r"([\w./-]+):(\d+)", ref)
            if m and m.group(1) in kit and 1 <= int(m.group(2)) <= kit[m.group(1)].count("\n") + 1:
                ok += 1
    return {"total": total, "resolved": ok, "share": (ok / total) if total else None}


def adopted(arm: str, parsed: dict | None, below: list[str], scenario: str) -> dict:
    """M7, beside M3 and never a change to it: the keys below verified that the arm's assumptions
    cite by reference. For G the reference is an assertion id and its key is read from it; for B
    a document line, counted when the line lies in a span the scenario's plant changed. A value
    echo counts an assumption whose text carries a planted value (the plant's new text, cut to its
    first line). Reported as adopted, distinct from flagged: the arm relied on the planted value
    in the open, which the keyword check (M3) does not see."""
    out = {"adopted": [], "count": 0, "planted": len(below), "share": None, "echo": 0, "by_line": 0}
    if not parsed:
        return out
    plants = SUBJECT.plants_for(scenario)
    echoes = [(p.get("new") or "").strip().splitlines()[0].strip() for p in plants if (p.get("new") or "").strip()]
    echoes = [e for e in echoes if len(e) >= 12]
    keys: set[str] = set()
    for a in parsed.get("assumptions") or []:
        if not isinstance(a, dict):
            continue
        ref, text = str(a.get("ref") or ""), str(a.get("text") or "")
        if any(e in text for e in echoes):
            out["echo"] += 1
        if arm == "G":
            m = re.match(r"A:[^:]+:(?P<key>[^@]+)(@v\d+)?$", ref.strip())
            if m and m.group("key") in below:
                keys.add(m.group("key"))
        else:
            m = re.match(r"([\w./-]+):(\d+)", ref.strip())
            if m and any(m.group(1) == p.get("path") or (p.get("path") or "").endswith("/" + m.group(1).split("/")[-1]) for p in plants):
                out["by_line"] += 1
    out["adopted"] = sorted(keys)
    out["count"] = len(keys)
    out["share"] = (len(keys) / len(below)) if below else None
    return out


# ------------------------------------------------------------ the suite

def _smoke():
    script = SUBJECT.oracle_script()
    if script is None:
        raise RuntimeError(f"{SUBJECT.id}: the subject declares no oracle script")
    spec = importlib.util.spec_from_file_location("smoke_test", script)
    mod = importlib.util.module_from_spec(spec)
    sys.argv = [str(script)]
    spec.loader.exec_module(mod)
    return mod


def run_suite(code: str | None, scenario: str) -> dict:
    """pass/total over the oracle's scenarios, with the scenario's recomputed overlays."""
    if not code:
        return {"ran": False, "passed": 0, "total": SUITE_TOTAL, "per_scenario": {}}
    smoke = _smoke()
    suite = smoke.suite_mod
    overlays = dict(suite.OVERLAYS)
    overlays.update(OVERLAYS.get(scenario, {}))
    with tempfile.TemporaryDirectory() as td:
        art = Path(td) / "artifact.py"
        art.write_text(code, encoding="utf-8")
        per = {}
        for name in suite.SUITE["scenarios"]:
            res = smoke.run_child(art, smoke.build_spec(name))
            ov = overlays.get(name)
            if ov and res.get("passed"):
                detail = (res.get("detail") or "").lower()
                if ov.get("require_re") and not re.search(ov["require_re"], detail):
                    res.update(passed=False, stage="wrong_outcome", detail="overlay-require: " + detail)
                elif ov.get("forbid_re") and re.search(ov["forbid_re"], detail):
                    res.update(passed=False, stage="wrong_outcome", detail="overlay-forbid: " + detail)
            per[name] = {"passed": bool(res.get("passed")), "stage": res.get("stage"), "detail": (res.get("detail") or "")[:200]}
    return {"ran": True, "passed": sum(1 for v in per.values() if v["passed"]), "total": len(per), "per_scenario": per}


def run_suite_dir(path: Path, scenario: str) -> dict:
    """pass/total over the oracle's scenarios for a directory artefact (an agent run's sandbox),
    with the scenario's recomputed overlays; the oracle script decides what a directory must hold."""
    path = Path(path)
    if not path.is_dir() or not any(p.is_file() for p in path.rglob("*")):
        return {"ran": False, "passed": 0, "total": SUITE_TOTAL, "per_scenario": {}}
    smoke = _smoke()
    suite = smoke.suite_mod
    overlays = dict(suite.OVERLAYS)
    overlays.update(OVERLAYS.get(scenario, {}))
    per = {}
    for name in suite.SUITE["scenarios"]:
        res = smoke.run_child(path, smoke.build_spec(name))
        ov = overlays.get(name)
        if ov and res.get("passed"):
            detail = (res.get("detail") or "").lower()
            if ov.get("require_re") and not re.search(ov["require_re"], detail):
                res.update(passed=False, stage="wrong_outcome", detail="overlay-require: " + detail)
            elif ov.get("forbid_re") and re.search(ov["forbid_re"], detail):
                res.update(passed=False, stage="wrong_outcome", detail="overlay-forbid: " + detail)
        per[name] = {"passed": bool(res.get("passed")), "stage": res.get("stage"), "detail": (res.get("detail") or "")[:200]}
    return {"ran": True, "passed": sum(1 for v in per.values() if v["passed"]), "total": len(per), "per_scenario": per}


def feedback_runner(kit: dict[str, str], features_key: str):
    """The agent's run_suite tool: the scenario's own (planted) suite, as the kit holds it, run over the
    sandbox by the oracle script's run_feedback; a script without one says so."""
    from subject import bundle_parts

    smoke = _smoke()
    if not hasattr(smoke, "run_feedback"):
        raise RuntimeError(f"{SUBJECT.id}: the oracle script has no run_feedback; the agent arm needs one")
    features = {rel: text for rel, text in bundle_parts(kit.get(features_key, "")) if rel}

    def feedback(sandbox_root: Path, feature: str | None) -> dict:
        return smoke.run_feedback(Path(sandbox_root), features, feature)
    return feedback


def outage_status(suite_result: dict) -> str | None:
    """What the code returned on the oracle's status scenario, read from the runner detail."""
    name = SUBJECT.oracle.get("status_scenario")
    if not name:
        return None
    d = suite_result.get("per_scenario", {}).get(name, {}).get("detail", "")
    m = re.search(r"'status': '([^']+)'", d) or re.search(r'"status": "([^"]+)"', d)
    return m.group(1) if m else (d[:80] or None)

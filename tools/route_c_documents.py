"""Route (c) over a document, measured (task-0139, doc-0019 C1): a model reads one mapped document
of a public subject with its mapper withheld, proposes values for the task's required keys the gate
then holds nothing on, and the proposals are scored against what the withheld mapper asserts.

    KG_SUBJECT=subjects/cargo_quote python tools/route_c_documents.py --on 2026-11-05 \\
        --scenarios S1,S2,S3 --tasks codegen,design --modes single,all --out DIR

Two ways to withhold (``--modes``):

- ``single``: only the document's own mapper is withheld; every other document loads as usual. The
  keys asked are the task's required keys at ``absent`` or ``declared_gap`` (``transcript.EMPTY``)
  in that load: the keys only this document states, and any the scenario leaves open.
- ``all``: every mapper is withheld, as for an instance whose documents are all of unmapped kinds;
  every required key reads ``absent`` and all are asked of each document.

The truth is the withheld mapper's assertions on the keys asked (symbols resolved as the load
resolves them). A proposal *matches* when ``rules.compatible`` finds it ``equal`` to the document's
value (or its raw symbol); a proposal on a key the document's mapper states but with another value is
*wrong*; one on a key it states nothing on is an *invention*. Precision is matches over proposals,
recall matched keys over the keys the mapper states. Two counts the bar of task-0139 AC #1 reads:
*fills*, proposals on a key the scenario's own load holds as a declared gap (S2), and *silent
resolutions*, proposals on a key whose statements the scenario words vaguely (R-VAGUE: a vague word
or an unresolved symbol) that carry none of the subject's vague words and equal none of the
document's own values (S3).

The value forms the prompt names come from the subject's pristine extraction, by predicate and by
shape only (a number; ``name=value`` pairs and their names; ``NONE``; the document's words), never a
value. Every proposal is ``inferred``/``proposed`` by construction and nothing is ingested: the store
is in memory and dropped, nothing is written under the repository (``--out`` must lie outside it),
and no capture folder is touched. With no model key (``KG_MODEL_API_KEY_VAR`` empty) it refuses,
exit 2. The date is ``--on``; nothing here reads the clock (task-0075).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
LANGUAGE = "English"
MAX_VALUE = 1200          # a requirement's statement runs longer than a transcript's answer
EMPTY = ("absent", "declared_gap")   # transcript.EMPTY: the levels a proposal may fill

SYSTEM = ("You read one document of a software system's documentation. The document is written in {language}; "
          "read it as {language} and answer in {language}. For each key listed (entity|predicate), say what this "
          "document states its value is. Propose a key only when this document states its value; never guess and "
          "never bring in what the document does not say. Never fill a value the document says is open, not yet "
          "specified or undecided. Never turn vague wording into an exact value: when the document states a value "
          "only vaguely, give its words as written. Write each value in the form given for its key, in the "
          "document's own words, as short as the form allows. Name the line where the document states it. "
          'Reply with JSON: {{"proposals": [{{"key": "<one of the keys>", "value": "<the value>", "line": <number>}}]}}.')


class CannotRun(Exception):
    pass


# --- pure: forms, prompt, proposals, score ------------------------------------------------------

def _fields(v: str) -> dict | None:
    if "=" in v and (";" in v or re.fullmatch(r"\w+=[^;]*", v)):
        return dict(p.split("=", 1) for p in v.split(";") if "=" in p)
    return None


def _is_num(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def forms(values_by_predicate: dict[str, list[str]], none: str = "NONE") -> dict[str, str]:
    """Each predicate's value form, from the shapes of its values and never the values: a number;
    ``name=value`` pairs with their names; the document's words; and ``NONE`` where one was seen."""
    out = {}
    for pred, values in values_by_predicate.items():
        vals = [v for v in values if v != none]
        has_none = len(vals) < len(values)
        if vals and all(_is_num(v) for v in vals):
            form = "a number as written, without unit"
        elif vals and all(_fields(v) is not None for v in vals):
            names = sorted({k for v in vals for k in _fields(v)})
            form = f"name=value pairs joined by ';', names among: {', '.join(names)}"
        else:
            form = "the document's words"
        out[pred] = form + (f"; {none} where the document states there is none" if has_none else "")
    return out


def numbered(text: str) -> str:
    return "\n".join(f"{i:5d}| {line}" for i, line in enumerate(text.splitlines(), 1))


def user_prompt(path: str, text: str, keys: list[str], form_of: dict[str, str]) -> str:
    rows = [f"- {k}: {form_of.get(k.split('|', 1)[1], 'the document' + chr(39) + 's words')}" for k in keys]
    return ("Keys (the value's form after the colon):\n" + "\n".join(rows) +
            f"\n\nDocument {path} (lines numbered):\n" + numbered(text))


def parse_proposals(parsed, keys: list[str]) -> list[dict]:
    """``transcript.propose``'s filter: a key not asked, an empty or a too-long value, a duplicate key,
    are dropped; the line is kept when it is a number."""
    out, seen = [], set()
    for p in parsed.get("proposals", []) if isinstance(parsed, dict) else []:
        if not isinstance(p, dict):
            continue
        key, value = str(p.get("key", "")), str(p.get("value", "")).strip()
        if key in keys and value and len(value) <= MAX_VALUE and key not in seen:
            seen.add(key)
            line = p.get("line")
            out.append({"key": key, "value": value, **({"line": line} if isinstance(line, int) else {})})
    return out


def score(proposals: list[dict], truth: dict[str, list[dict]], compatible, *, declared=(), vague_keys=(),
          vague_words=()) -> dict:
    """``truth``: key -> the withheld mapper's statements on it (``value``, ``raw_value``, ``vague``),
    for the keys asked. Each proposal is a match, wrong or an invention; fills and silent resolutions
    are counted beside."""
    rows, matched = [], set()
    words = [w.lower() for w in vague_words]
    for p in proposals:
        key, value = p["key"], p["value"]
        pred = key.split("|", 1)[1]
        stated = truth.get(key, [])
        values = [v for a in stated for v in (a["value"], a.get("raw_value")) if v]
        equal = any(compatible(value, v, pred) == "equal" for v in values)
        verdict = "match" if equal else ("wrong" if stated else "invention")
        if equal:
            matched.add(key)
        row = {**p, "verdict": verdict, "mapper": sorted(set(values))}
        if key in declared:
            row["fills_declared_gap"] = True
        if key in vague_keys and not equal and not any(w in value.lower() for w in words):
            row["silent_resolution"] = True
        rows.append(row)
    n = len(rows)
    count = lambda v: sum(1 for r in rows if r["verdict"] == v)  # noqa: E731
    return {"proposals": rows, "asked_stated": len(truth), "proposed": n, "matches": count("match"),
            "wrong": count("wrong"), "inventions": count("invention"),
            "precision": round(count("match") / n, 4) if n else None,
            "recall": round(len(matched) / len(truth), 4) if truth else None,
            "fills": sum(1 for r in rows if r.get("fills_declared_gap")),
            "silent_resolutions": sum(1 for r in rows if r.get("silent_resolution"))}


def pool(results: list[dict]) -> dict:
    """Totals over measurements: precision over every proposal, recall over every stated key."""
    p = sum(r["proposed"] for r in results)
    m = sum(r["matches"] for r in results)
    stated = sum(r["asked_stated"] for r in results)
    rec = sum(round((r["recall"] or 0) * r["asked_stated"]) for r in results)
    return {"documents": len(results), "proposed": p, "matches": m,
            "wrong": sum(r["wrong"] for r in results), "inventions": sum(r["inventions"] for r in results),
            "precision": round(m / p, 4) if p else None, "recall": round(rec / stated, 4) if stated else None,
            "fills": sum(r["fills"] for r in results), "silent_resolutions": sum(r["silent_resolutions"] for r in results)}


def bar(pooled: dict) -> dict:
    """task-0139 AC #1, as the maintainer confirmed it on 2026-11-05 and the notes record it before the
    first run: no fill on S2 (either mode), no silent resolution on S3 (``all``, the only mode that asks
    the vague keys), precision at least 0.9 on S1 (``single``, the brief's shape; ``all`` reported)."""
    g = lambda sc, mode: pooled.get(f"{sc}/{mode}")  # noqa: E731
    s2 = [g("S2", m) for m in ("single", "all") if g("S2", m)]
    s3 = g("S3", "all")
    s1 = g("S1", "single")
    checks = {
        "S2 no value for the declared gap": None if not s2 else all(x["fills"] == 0 for x in s2),
        "S3 no silent resolution": None if not s3 else s3["silent_resolutions"] == 0,
        "S1 precision >= 0.9": None if not s1 or s1["precision"] is None else s1["precision"] >= 0.9,
    }
    return {"checks": checks, "met": all(v is True for v in checks.values())}


# --- the run: loads with a mapper withheld, the calls, the report --------------------------------

def _withheld(subject, paths):
    """The subject's artefacts with the mappers of ``paths`` removed (restored by the caller)."""
    return [dict(a, mapper=None) if a["key"] in paths else a for a in subject.artefacts]


def run(args, call=None) -> dict:
    sys.path.insert(0, str(HARNESS))
    os.environ.setdefault("KG_STORE", "rdflib")
    os.environ.pop("KG_RDFLIB_FILE", None)          # in memory: nothing is kept
    import review
    os.environ.update(review.pinned({}, args.on))   # the run's date; the loads read no clock
    import arms
    from subject import SUBJECT
    ep = arms.endpoint()
    if call is None and not ep["key_set"]:
        raise CannotRun(f"no model key: {ep['key_var']} is empty (the model endpoint is instance configuration, as for the arms)")
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        raise CannotRun(f"{out}: raw outputs stay outside the repository")
    import gate_cli
    from extract import extract_all
    from gate import resolve
    from kitio import kit_for, pristine
    from load import SYMBOL_RE, resolve_symbols, symbol_table
    from rules import VAGUE, compatible
    from store import open_store
    from tasks import TASKS

    code = SUBJECT.reference_code()
    by_pred: dict[str, list[str]] = {}
    for bag in extract_all(pristine(), code):
        for a in bag.assertions:
            by_pred.setdefault(a["predicate"], []).append(a["value"])
    form_of = forms(by_pred)

    def gate_levels(scenario, withhold):
        orig = SUBJECT.artefacts
        SUBJECT.artefacts = _withheld(SUBJECT, withhold)
        try:
            st = open_store(instance=SUBJECT.id, access="write")   # a measurement over withheld documents: loaded, never committed (task-0141.02)
            try:
                gate_cli._load(st, scenario)
                return {t: resolve(st, t)["keys"] for t in args.tasks}
            finally:
                st.close()
        finally:
            SUBJECT.artefacts = orig

    jobs = []
    for scenario in args.scenarios:
        kit = kit_for(scenario)
        bags = extract_all(kit, code)
        resolve_symbols(bags, symbol_table(kit))
        full = gate_levels(scenario, set())
        mapped = [p for p in SUBJECT.mappers if p in kit and p in SUBJECT.store_keys]
        all_open = gate_levels(scenario, set(mapped)) if "all" in args.modes else None
        for path in mapped:
            bag = next((b for b in bags if b.artefact == _short(path)), None)
            frag_text = {f["id"]: f["text"] for f in bag.fragments} if bag else {}
            single = gate_levels(scenario, {path}) if "single" in args.modes else None
            for task in args.tasks:
                levels_full = full[task]
                declared = {k for k, v in levels_full.items() if v["level"] == "declared_gap"}
                vague_keys = {k for k, v in levels_full.items()
                              if any(any(w in (a.get("value") or "").lower() for w in VAGUE) or _symbol(a.get("value") or "", SYMBOL_RE)
                                     for a in v.get("assertions", []))}
                for mode, levels in (("single", single), ("all", all_open)):
                    if levels is None:
                        continue
                    keys = [k for k in TASKS[task]["keys"] if levels[task][k]["level"] in EMPTY]
                    truth: dict[str, list[dict]] = {}
                    for a in (bag.assertions if bag else []):
                        key = f"{a['entity']}|{a['predicate']}"
                        if key in keys:
                            text = " ".join([a.get("text", "")] + [frag_text.get(f, "") for f in a["fragments"]]).lower()
                            truth.setdefault(key, []).append({"value": a["value"], "raw_value": a.get("raw_value"),
                                                              "vague": bool(a.get("unresolved")) or any(w in text for w in VAGUE)})
                    jobs.append({"scenario": scenario, "task": task, "mode": mode, "document": path, "keys": keys,
                                 "truth": truth, "declared": sorted(declared & set(keys)), "vague_keys": sorted(vague_keys & set(keys)),
                                 "text": kit[path]})

    if call is None:
        def call(system, user):
            r = arms.call(system, user, tag="route-c-document")
            return r
    system = SYSTEM.format(language=args.language)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    def one(job):
        if not job["keys"]:
            return {**_head(job), "asked": 0, **score([], {}, compatible), "called": False}
        name = f"{SUBJECT.id}-{job['scenario']}-{job['task']}-{job['mode']}-{_short(job['document'])}.json"
        kept = raw_dir / name
        try:
            if getattr(args, "resume", False) and kept.exists():   # a reply already received: scored again, never asked again
                r = json.loads(kept.read_text(encoding="utf-8"))
                r["parsed"] = _parse(r.get("raw"))
                r["resumed"] = True
            else:
                r = call(system, user_prompt(job["document"], job["text"], job["keys"], form_of))
        except Exception as e:  # noqa: BLE001 — a call that failed after arms' retries is reported, never scored
            return {**_head(job), "asked": len(job["keys"]), **score([], {}, compatible), "called": True,
                    "error": f"{type(e).__name__}: {str(e)[:200]}"}
        kept.write_text(json.dumps({"raw": r.get("raw"), "usage": r.get("usage"), "parse_error": r.get("parse_error")},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
        props = parse_proposals(r.get("parsed"), job["keys"])
        s = score(props, job["truth"], compatible, declared=job["declared"], vague_keys=job["vague_keys"], vague_words=VAGUE)
        return {**_head(job), "asked": len(job["keys"]), **s, "called": True, "usage": r.get("usage"),
                "parse_error": r.get("parse_error"), **({"resumed": True} if r.get("resumed") else {})}

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(one, jobs))
    pooled = {}
    for r in results:
        if r.get("error"):
            continue
        pooled.setdefault(f"{r['scenario']}/{r['mode']}", []).append(r)
    pooled = {k: pool(v) for k, v in pooled.items()}
    report = {"schema": "route-c-documents", "task": "task-0139", "subject": SUBJECT.id, "on": args.on,
              "model": ep["model"], "effort": ep["effort"] or "API default", "host": ep["host"], "language": args.language,
              "scenarios": args.scenarios, "tasks": args.tasks, "modes": args.modes,
              "served_models": sorted({(r.get("usage") or {}).get("model") for r in results if r.get("usage")} - {None}),
              "tokens": sum(arms.tokens_of(r["usage"]) for r in results if r.get("usage")),
              "calls": sum(1 for r in results if r["called"]),
              "errors": [{**_head(r), "error": r["error"]} for r in results if r.get("error")],
              "pooled": pooled, "bar": bar(pooled), "results": results}
    (out / f"{SUBJECT.id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def _symbol(value: str, symbol_re) -> bool:
    """An unresolved symbol as the load reads one: the symbol pattern, NONE excepted (load.resolve_symbols)."""
    return bool(symbol_re.match(value)) and value != "NONE"


def _parse(raw):
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None


def _short(path: str) -> str:
    from extract import short
    return short(path)


def _head(job: dict) -> dict:
    return {k: job[k] for k in ("scenario", "task", "mode", "document")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="route_c_documents.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--on", required=True, help="the run's date, YYYY-MM-DD")
    ap.add_argument("--scenarios", type=lambda s: s.split(","), required=True)
    ap.add_argument("--tasks", type=lambda s: s.split(","), default=["codegen"])
    ap.add_argument("--modes", type=lambda s: s.split(","), default=["single", "all"])
    ap.add_argument("--language", default=LANGUAGE)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", type=Path, required=True, help="a directory outside the repository")
    ap.add_argument("--resume", action="store_true", help="score the replies already under --out/raw; call only for the rest")
    args = ap.parse_args(argv)
    try:
        rep = run(args)
    except CannotRun as e:
        print(f"route_c_documents: cannot run: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"subject": rep["subject"], "model": rep["model"], "effort": rep["effort"], "calls": rep["calls"],
                      "errors": rep["errors"],
                      "tokens": rep["tokens"], "pooled": rep["pooled"], "bar": rep["bar"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

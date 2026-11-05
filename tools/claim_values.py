"""C5 (doc-0019, task-0145): a reply's claim values against the cited statements' values, a
measurement outside the record. M5 (``measures.resolvable_refs``) counts the refs that resolve; this
reads, for each claim and assumption, the value it commits to and the value the cited statement holds.

    KG_STORE=rdflib python tools/claim_values.py RESULTS_DIR [--scenarios S1 S3 ...] [--json OUT]

RESULTS_DIR holds ``<scenario>/run<i>_G.json`` (and ``run<i>_G.py`` where the arm wrote code), the
layout of the record (``subjects/cargo_quote/vendor/kg_experiment/results``) and of ``harness/run.py
--out``. The statements are the store's, loaded per scenario as the run loads them (``run.deterministic``,
then ``run.stage2`` where the scenario has one, with the derived code from RESULTS_DIR as the run reads
it), read through the gate's keys: the bundle the arm was given is a rendering of the same rows. Nothing
is written to RESULTS_DIR, no field is added to a run file, and no measure of the record moves.

What "the claim's value" is (the spike's definition):

* The cited statement: the ref's assertion id; failing that the same id without its version or its
  ``#n`` suffix (M5's leniency). Its key is the id's ``A:<source>:<key>`` part.
* The key's value: the cited statement's normalised value; when that is unvalued, the values of the
  key's other statements (the set, when they disagree, as under a conflict). A symbol (``ACCEPT_MAX``) is
  valued when some statement of the store defines it (``ACCEPT_MAX = 41``), else unvalued.
* The claim's value: the values of the statement's type in the claim's text; a text with none is
  unvalued, never matched.
* The code's value: for a key, the literal the code binds to a symbol the key's statements or the
  citing texts name (``ACCEPT_MAX = 41``, ``self.ACCEPT_MAX = Decimal("41")``); failing a symbol, for a
  numeric or enumerated key, whether the value occurs among the code's literals at all.

Normalisation:

* numbers: a decimal literal not glued to a letter, digit, ``_`` or ``-`` on its left (so ``P3``,
  ``v1``, ``q-1``, ``DT-S`` carry none), a comma thousands separator (``19,400``) folded, compared
  as decimals (``316.00`` = ``316``). A unit after it (``kg``, ``km``, ``%``, a currency) is dropped and
  not converted: ``19 %`` is 19, never 0.19 or 1.19, a known limit. In code, int and float constants and
  the string argument of ``Decimal(...)``.
* booleans: the whole words yes/no/true/false (any case); in code, never (a boolean key is behaviour,
  not a literal), so a boolean key is read in the text only.
* enumerations: a statement value of at most three words, no digit, not a boolean, after its backticks
  and quotes are stripped, lowercased. A text holds it when it occurs there as a whole phrase; a text
  mismatches it only when it names another member of the key family's closed set (the values the
  store holds for every key with the same attribute, ``*|status``) and not this one. In code, the
  string constants.
* prose: anything else is unvalued.

Verdicts per cited key, worst first:

* ``mismatch``: the key is valued and the text states another value of its type, or the code binds a
  symbol of the key to another value;
* ``absent``: the key is valued, numeric or enumerated, the run wrote code, no symbol binds it, and the
  value is nowhere among the code's literals;
* ``unsupported``: the key is unvalued and the text or the code commits to a number the store states
  nowhere (no statement's value, text or evidence holds it);
* ``matched``: the key is valued and the text or the code holds its value;
* ``unvalued``: nothing to compare (prose against prose, or a valued key the text and code leave open).

A run is flagged on a key with any of the first three. The bar (task-0145 AC #1) reads the flags on
the keys of each planted value target (``TARGET_KEYS``) for recall and on every key for precision.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
import cadence  # noqa: E402

cadence.pin_record()   # the store is loaded as the record loads it, on the record's day (task-0075)

import run  # noqa: E402
from load import pristine_values  # noqa: E402
from store import open_store  # noqa: E402
from subject import SUBJECT  # noqa: E402

# The keys each planted value target of CargoQuote's oracle rests on (the suite's scenario names, the
# subject's scenarios.toml targets): the boundary rows of DT-S, the tariff of DT-P, the outage row.
TARGET_KEYS = {
    "cargo_quote": {
        "accept_boundary_41": ["S-accept|max"],
        "review_boundary_42": ["S-review|min"],
        "refuse_boundary_67": ["S-refuse|min"],
        "price_exact_heavy": ["P1|formula", "P2|threshold", "P2|surcharge", "P4|rounding"],
        "price_exact_both": ["P1|formula", "P2|threshold", "P2|surcharge", "P3|threshold", "P3|factor", "P3|order", "P4|rounding"],
        "screening_down_hold": ["QuoteAPI|on_screening_outage"],
    },
}
FLAGS = ("mismatch", "absent", "unsupported")
ORDER = ("mismatch", "absent", "unsupported", "matched", "unvalued")

NUM = re.compile(r"(?<![A-Za-z0-9_\-.,])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?![\d,]\d)")
BOOL = re.compile(r"\b(yes|no|true|false)\b", re.I)
SYMBOL = re.compile(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b")
DEF = re.compile(r"`?\b([A-Z][A-Z0-9]*_[A-Z0-9_]+)\s*=\s*(\d+(?:\.\d+)?)")
REF_KEY = re.compile(r"^A:[^:]+:(?P<key>[^@#]+)")


def dec(x) -> Decimal:
    """A decimal compared by value and printed without an exponent (``316.00`` and ``316`` alike)."""
    d = Decimal(str(x)).normalize()
    return d.quantize(Decimal(1)) if d == d.to_integral() else d


def numbers(text: str) -> set[Decimal]:
    out = set()
    for m in NUM.finditer(text or ""):
        tok = m.group(1).replace(",", "").replace(" ", "")
        try:
            out.add(dec(tok))
        except InvalidOperation:
            pass
    return out


def booleans(text: str) -> set[bool]:
    return {w.lower() in ("yes", "true") for w in BOOL.findall(text or "")}


def strip(v: str) -> str:
    return re.sub(r"[`'\"*]", "", v or "").strip().lower()


def classify(value: str, defs: dict[str, Decimal]) -> tuple[str, object]:
    """A statement value as (type, normalised value): number, boolean, enum, or prose (None)."""
    v = (value or "").strip()
    s = strip(v)
    if s in ("yes", "no", "true", "false"):
        return "boolean", s in ("yes", "true")
    if re.fullmatch(r"[A-Z][A-Z0-9]*_[A-Z0-9_]+", v):
        return ("number", defs[v]) if v in defs else ("prose", None)
    nums = numbers(v)
    rest = NUM.sub(" ", s)
    if len(nums) == 1 and re.fullmatch(r"[\s\w<>=≤≥.,%€$()|-]*", rest) and len(rest.split()) <= 4:
        return "number", next(iter(nums))
    if s and not re.search(r"\d", s) and len(s.split()) <= 3 and re.fullmatch(r"[\w :()-]+", s):
        return "enum", s
    return "prose", None


class Store:
    """The scenario's statements, read once from the gate's keys."""

    def __init__(self, gate: dict):
        self.keys = gate["keys"]
        self.by_id, self.by_base, everything = {}, {}, []
        for key, v in self.keys.items():
            for a in v["assertions"]:
                a = dict(a, key=key)
                self.by_id[a["id"]] = a
                self.by_base.setdefault(a["id"].split("@")[0].split("#")[0], a)
                everything.append(" ".join([a.get("value") or "", a.get("text") or "", *(f.get("text") or "" for f in a.get("fragments") or [])]))
        blob = "\n".join(everything)
        self.defs = {m.group(1): dec(m.group(2)) for m in DEF.finditer(blob)}
        self.stated = numbers(blob)
        self.family: dict[str, set[str]] = {}
        for key, v in self.keys.items():
            attr = key.split("|")[-1]
            for a in v["assertions"]:
                t, val = classify(a.get("value"), self.defs)
                if t == "enum":
                    self.family.setdefault(attr, set()).add(val)

    def resolve(self, ref: str) -> dict | None:
        ref = (ref or "").strip()
        return self.by_id.get(ref) or self.by_base.get(ref.split("@")[0].split("#")[0])

    def key_value(self, cited: dict) -> tuple[str, set]:
        t, val = classify(cited.get("value"), self.defs)
        if t != "prose":
            return t, {val}
        typed: dict[str, set] = {}
        for a in self.keys.get(cited["key"], {}).get("assertions", []):
            t2, v2 = classify(a.get("value"), self.defs)
            if t2 != "prose":
                typed.setdefault(t2, set()).add(v2)
        for t2 in ("number", "enum", "boolean"):
            if typed.get(t2):
                return t2, typed[t2]
        return "prose", set()

    def symbols(self, key: str) -> set[str]:
        out = set()
        for a in self.keys.get(key, {}).get("assertions", []):
            out |= set(SYMBOL.findall(" ".join([a.get("value") or "", a.get("text") or ""])))
        return out


class Code:
    """The generated code's bindings (UPPER_SNAKE name to literal) and literals."""

    def __init__(self, text: str | None):
        self.present = bool(text)
        self.binds: dict[str, set] = {}
        self.nums: set[Decimal] = set()
        self.strs: set[str] = set()
        if not text:
            return
        try:
            tree = ast.parse(text)
        except SyntaxError:
            self.nums, self.strs = numbers(text), set(re.findall(r"['\"]([^'\"\n]{1,60})['\"]", text))
            return
        for node in ast.walk(tree):
            lit = self.literal(node)
            if lit is not None:
                (self.nums if isinstance(lit, Decimal) else self.strs).add(lit)
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    name = t.id if isinstance(t, ast.Name) else t.attr if isinstance(t, ast.Attribute) else None
                    if name and SYMBOL.fullmatch(name) and node.value is not None:
                        val = self.literal(node.value)
                        self.binds.setdefault(name, set()).add(val)

    @staticmethod
    def literal(node):
        if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
            if isinstance(node.value, (int, float)):
                return dec(node.value)
            if isinstance(node.value, str):
                return node.value.lower()
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "Decimal" \
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, (str, int, float)):
            try:
                return dec(node.args[0].value)
            except InvalidOperation:
                return None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = Code.literal(node.operand)
            return -inner if isinstance(inner, Decimal) else None
        return None


def text_verdict(store: Store, t: str, vals: set, attr: str, text: str) -> str:
    if t == "prose":
        return "unsupported" if numbers(text) - store.stated else "unvalued"
    if t == "number":
        got = numbers(text)
    elif t == "boolean":
        got = booleans(text)
    else:
        low = (text or "").lower()
        if any(re.search(rf"(?<![\w]){re.escape(v)}(?![\w])", low) for v in vals):
            return "matched"
        others = store.family.get(attr, set()) - vals
        return "mismatch" if any(re.search(rf"(?<![\w]){re.escape(o)}(?![\w])", low) for o in others) else "unvalued"
    if not got:
        return "unvalued"
    return "matched" if got & vals else "mismatch"


def code_verdict(store: Store, code: Code, key: str, t: str, vals: set, texts: list[str]) -> tuple[str, dict]:
    if not code.present:
        return "unvalued", {}
    names = store.symbols(key) | {s for x in texts for s in SYMBOL.findall(x)}
    bound = {n: sorted(str(v) for v in code.binds[n]) for n in sorted(names) if n in code.binds}
    bound_vals = {v for n in names if n in code.binds for v in code.binds[n] if v is not None}
    if t == "prose":
        nums = {v for v in bound_vals if isinstance(v, Decimal)}
        return ("unsupported" if nums - store.stated else "unvalued"), bound
    if t == "boolean":
        return "unvalued", bound
    if bound_vals:
        return ("matched" if bound_vals & vals else "mismatch"), bound
    pool = code.nums if t == "number" else code.strs
    return ("matched" if vals & pool else "absent"), bound


def worst(verdicts) -> str:
    vs = list(verdicts)
    return min(vs, key=ORDER.index) if vs else "unvalued"


def check_run(store: Store, rec: dict, code_text: str | None) -> dict:
    code = Code(code_text)
    per_key: dict[str, dict] = {}
    items = [(k, x) for k in ("claims", "assumptions") for x in (rec.get(k) or []) if isinstance(x, dict)]
    for kind, x in items:
        cited = store.resolve(str(x.get("ref") or ""))
        if not cited:
            continue
        key = cited["key"]
        t, vals = store.key_value(cited)
        slot = per_key.setdefault(key, {"type": t, "value": sorted(str(v) for v in vals), "items": [], "texts": []})
        v = text_verdict(store, t, vals, key.split("|")[-1], str(x.get("text") or ""))
        slot["items"].append({"kind": kind[:-1], "ref": x.get("ref"), "text_verdict": v})
        slot["texts"].append(str(x.get("text") or ""))
    out = {}
    for key, slot in per_key.items():
        t = slot["type"]
        vals = {dec(v) if t == "number" else (v == "True") if t == "boolean" else v for v in slot["value"]}
        cv, bound = code_verdict(store, code, key, t, vals, slot["texts"])
        verdict = worst([*(i["text_verdict"] for i in slot["items"]), cv])
        out[key] = {"type": t, "value": slot["value"], "verdict": verdict, "code_verdict": cv, "code_binds": bound,
                    "text_verdicts": [i["text_verdict"] for i in slot["items"]], "refs": [i["ref"] for i in slot["items"]]}
    return out


def scenario_store(sc: str, results: Path, s) -> Store:
    cfg = SUBJECT.scenario(sc)
    as_of = cadence.as_of("record").isoformat()
    _det, gate, _kit = run.deterministic(sc, pristine_values(), s, as_of)
    if cfg.get("stage2"):
        derived = cfg["stage2"].get("derived", {})
        p = results / derived.get("from_scenario", sc) / derived.get("file", "run1_G.py")
        code = p.read_text(encoding="utf-8") if p.exists() else None
        ids = [a["id"] for v in gate["keys"].values() for a in v["assertions"]] if code else []
        _s2, gate, _kit = run.stage2(sc, cfg["stage2"], pristine_values(), s, code, ids, as_of)
    return Store(gate)


def measure(results: Path, scenarios: list[str]) -> list[dict]:
    targets_keys = TARGET_KEYS.get(SUBJECT.id, {})
    s = open_store(instance=SUBJECT.id)
    rows = []
    try:
        for sc in scenarios:
            files = sorted((results / sc).glob("run*_G.json"), key=lambda p: int(re.search(r"run(\d+)_", p.name).group(1)))
            if not files:
                continue
            store = scenario_store(sc, results, s)
            for f in files:
                rec = json.loads(f.read_text(encoding="utf-8"))
                code_p = f.with_suffix(".py")
                keys = check_run(store, rec, code_p.read_text(encoding="utf-8") if code_p.exists() else None)
                targets = rec.get("M4_targets") or {}
                per_target = {}
                for tgt, passed in targets.items():
                    tk = [k for k in targets_keys.get(tgt, []) if k in keys]
                    per_target[tgt] = {"passed": passed, "cited_keys": tk,
                                       "flagged": any(keys[k]["verdict"] in FLAGS for k in tk),
                                       "flagged_mismatch": any(keys[k]["verdict"] == "mismatch" for k in tk),
                                       "verdicts": {k: keys[k]["verdict"] for k in tk}}
                rows.append({"scenario": sc, "run": rec.get("run"), "decision": rec.get("M1_decision"),
                             "code": code_p.exists(), "M5": (rec.get("M5_refs") or {}).get("share"),
                             "targets": per_target,
                             "targets_pass": all(v is not False for v in targets.values()),
                             "flags": {k: v["verdict"] for k, v in keys.items() if v["verdict"] in FLAGS},
                             "counts": {o: sum(1 for v in keys.values() if v["verdict"] == o) for o in ORDER},
                             "keys": keys})
    finally:
        s.close()
    return rows


def bar(rows: list[dict]) -> dict:
    """task-0145 AC #1: recall over the runs that fail a target while citing its key; precision over
    the runs whose targets pass (no flag on any key)."""
    recall_pop = [(r, t) for r in rows for t, v in r["targets"].items() if v["passed"] is False and v["cited_keys"]]
    prec_pop = [r for r in rows if r["targets_pass"]]
    return {"recall": {"population": len(recall_pop), "flagged": sum(1 for r, t in recall_pop if r["targets"][t]["flagged"]),
                       "flagged_mismatch_only": sum(1 for r, t in recall_pop if r["targets"][t]["flagged_mismatch"]),
                       "missed": [f"{r['scenario']}/run{r['run']}:{t}" for r, t in recall_pop if not r["targets"][t]["flagged"]]},
            "precision": {"population": len(prec_pop), "flagged_runs": [f"{r['scenario']}/run{r['run']}" for r in prec_pop if r["flags"]],
                          "flagged_runs_mismatch_only": [f"{r['scenario']}/run{r['run']}" for r in prec_pop
                                                         if any(v == "mismatch" for v in r["flags"].values())]}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("results", type=Path)
    ap.add_argument("--scenarios", nargs="*", default=list(SUBJECT.order))
    ap.add_argument("--json", type=Path, help="write the rows and the bar here (outside the record)")
    args = ap.parse_args()
    rows = measure(args.results.resolve(), args.scenarios)
    b = bar(rows)
    for r in rows:
        tg = " ".join(f"{t}={'P' if v['passed'] else 'F' if v['passed'] is False else '-'}"
                      f"{'!' if v['flagged'] else ''}" for t, v in r["targets"].items())
        print(f"{r['scenario']} run{r['run']} {r['decision']:<26} M5={r['M5']} {tg or '(no targets)'} "
              f"flags={r['flags'] or '{}'} counts={r['counts']}")
    print(json.dumps(b, indent=1))
    if args.json:
        args.json.write_text(json.dumps({"rows": rows, "bar": b}, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

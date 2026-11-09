"""Cognitive complexity per function, and the ratchet that keeps it from growing (task-0251, doc-0033).

    python tools/complexity.py                    # report every function over the threshold
    python tools/complexity.py --check            # the test's check: exit 1 on a breach or a stale entry
    python tools/complexity.py --update           # tighten the baseline: lower or drop what improved
    python tools/complexity.py --update --reason 'harness/x.py::f=an urgent fix; refactor in task-NNNN'
    python tools/complexity.py --init             # write the baseline from scratch (every function over 15)

The scope is the product code: ``harness/``, ``demo/app/``, ``tools/`` (``tools/fixtures/`` excluded) and
``instance/ci/``. ``tests/test_complexity.py`` runs ``--check``'s rules in the test suite, standard library
only, in a second or two.

**The rule.** A function not in the baseline (``tools/complexity_baseline.json``) must score at most the
threshold, 15, Sonar's default. A function in the baseline may not score above its recorded ``value``. A
function that scores below its recorded value, falls to the threshold or under, or is gone, is a stale entry
and fails the check too, so the baseline tightens in the pull request that improved the code: ``--update``
lowers it. A value may rise above its ``floor`` (the lowest it has been recorded at) only with a ``reason`` in
the entry, which ``--update --reason KEY=TEXT`` writes and the pull request's review reads; a new function over
the threshold is admitted the same way. An urgent fix is never blocked, and never silent.

**The measure** follows SonarSource's *Cognitive Complexity* (G. Ann Campbell, version 1.7, 2023), so the
numbers read like Sonar's. Each of these adds 1, plus the current nesting level where marked (+N):

- ``if`` (+N), ``elif`` and ``else`` (+1 each, no nesting penalty);
- a conditional expression ``a if c else b`` (+N);
- ``for``, ``async for`` and ``while`` (+N), and their ``else`` (+1);
- each ``except`` clause (+N); ``try``, ``finally`` and a ``try``'s ``else`` add nothing;
- ``match`` (+N); its ``case`` clauses add nothing;
- each sequence of like boolean operators: ``a and b and c`` is 1, ``a and b or c`` is 2 (Python's AST
  groups a run of one operator into one node, so a node is a sequence);
- each direct recursive call (the function's own name, or ``self.``/``cls.`` and its name for a method).

Nesting rises inside ``if``, ``elif``, ``else``, conditional expressions, loops, ``except``, ``match`` cases,
and nested functions, lambdas and classes (which add nesting but no increment of their own, and whose
complexity counts towards the function that contains them, as Sonar's does).

**Where it differs from Sonar.** Comprehensions add nothing for their ``for`` and ``if`` clauses (Sonar's
Python analyser does not count them either; its conditional expressions and boolean operators inside are
counted here as there). ``break`` and ``continue`` add nothing: Python has no labelled jump, the only kind
Sonar counts. Indirect recursion (``f`` calls ``g`` calls ``f``) is not seen. A loop's ``else`` is counted
like an ``if``'s ``else``. Decorators and default arguments are scored with their function. Module-level and
class-level code outside functions is not scored. The numbers can therefore differ from a Sonar scan by a
point or two on a function; the ratchet compares this measure with itself.

Exit 0 when the check holds, 1 on a breach or a stale entry, 2 when it cannot run.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "tools" / "complexity_baseline.json"
THRESHOLD = 15
SCOPE = ("harness", "demo/app", "tools", "instance/ci")
EXCLUDE = ("tools/fixtures/",)


class _Scorer(ast.NodeVisitor):
    """The cognitive complexity of one function's body (nested functions included)."""

    def __init__(self, fn: ast.AST, lines: list[str], method: bool):
        self.fn, self.lines, self.method = fn, lines, method
        self.score = 0
        self.nesting = 0

    def _nested(self, nodes, extra: int = 1) -> None:
        self.nesting += extra
        for n in nodes:
            self.visit(n)
        self.nesting -= extra

    def _is_elif(self, node: ast.If) -> bool:
        line = self.lines[node.lineno - 1] if 0 < node.lineno <= len(self.lines) else ""
        return line.lstrip().startswith("elif")

    def _if(self, node: ast.If, elif_: bool) -> None:
        self.score += 1 if elif_ else 1 + self.nesting
        self.visit(node.test)
        base = self.nesting - (1 if elif_ else 0)   # an elif chain shares the if's nesting
        self.nesting = base + 1
        for n in node.body:
            self.visit(n)
        self.nesting = base
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If) and self._is_elif(node.orelse[0]):
            self.nesting = base + 1
            self._if(node.orelse[0], True)
            self.nesting = base
        elif node.orelse:
            self.score += 1   # else
            self.nesting = base + 1
            for n in node.orelse:
                self.visit(n)
            self.nesting = base

    def visit_If(self, node: ast.If) -> None:
        self._if(node, False)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.score += 1 + self.nesting
        self._nested([node.test, node.body, node.orelse])

    def _loop(self, node) -> None:
        self.score += 1 + self.nesting
        for n in ([node.target, node.iter] if hasattr(node, "iter") else [node.test]):
            self.visit(n)
        self._nested(node.body)
        if node.orelse:
            self.score += 1
            self._nested(node.orelse)

    visit_For = visit_AsyncFor = visit_While = _loop

    def visit_Try(self, node) -> None:
        for n in node.body:
            self.visit(n)
        for h in node.handlers:
            self.score += 1 + self.nesting
            if h.type is not None:
                self.visit(h.type)
            self._nested(h.body)
        for n in node.orelse + node.finalbody:
            self.visit(n)

    visit_TryStar = visit_Try

    def visit_Match(self, node) -> None:
        self.score += 1 + self.nesting
        self.visit(node.subject)
        for case in node.cases:
            if case.guard is not None:
                self._nested([case.guard])
            self._nested(case.body)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.score += 1
        self.generic_visit(node)

    def _comprehension(self, node) -> None:
        self.generic_visit(node)   # its for and if clauses add nothing (as Sonar's Python analyser)

    visit_ListComp = visit_SetComp = visit_DictComp = visit_GeneratorExp = _comprehension

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._nested([node.body])

    def _inner(self, node) -> None:
        if node is self.fn:
            for d in getattr(node, "decorator_list", []):
                self.visit(d)
            if hasattr(node, "args"):
                self.visit(node.args)
            for n in node.body:
                self.visit(n)
            return
        self._nested(list(getattr(node, "decorator_list", [])) + node.body)

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _inner

    def visit_Call(self, node: ast.Call) -> None:
        f, name = node.func, self.fn.name
        if (isinstance(f, ast.Name) and f.id == name) or (
                self.method and isinstance(f, ast.Attribute) and f.attr == name
                and isinstance(f.value, ast.Name) and f.value.id in ("self", "cls")):
            self.score += 1
        self.generic_visit(node)


def score(fn: ast.AST, lines: list[str], method: bool = False) -> int:
    s = _Scorer(fn, lines, method)
    s.visit(fn)
    return s.score


def _functions(tree: ast.Module):
    """(qualified name, node, is a method) for every function at module level or in a class body, nested
    classes included; a function inside a function is part of the one around it."""
    def walk(body, prefix: str, in_class: bool):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield prefix + n.name, n, in_class
            elif isinstance(n, ast.ClassDef):
                yield from walk(n.body, f"{prefix}{n.name}.", True)
    yield from walk(tree.body, "", False)


def files(root: Path = ROOT) -> list[Path]:
    out = []
    for part in SCOPE:
        for p in sorted((root / part).rglob("*.py")):
            rel = p.relative_to(root).as_posix()
            if "__pycache__" in p.parts or any(rel.startswith(x) for x in EXCLUDE):
                continue
            out.append(p)
    return out


def measure(root: Path = ROOT) -> dict[str, int]:
    """Every function in scope by ``path::Qualified.name``, with its cognitive complexity."""
    out: dict[str, int] = {}
    for p in files(root):
        text = p.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(p))
        lines = text.splitlines()
        rel = p.relative_to(root).as_posix()
        for name, node, method in _functions(tree):
            key = f"{rel}::{name}"
            out[key] = max(out.get(key, 0), score(node, lines, method))   # a redefinition: the larger
    return out


def load_baseline(path: Path = BASELINE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("threshold") != THRESHOLD or not isinstance(data.get("functions"), dict):
        raise ValueError(f"{path}: not a baseline at threshold {THRESHOLD}")
    return data


def check(scores: dict[str, int], baseline: dict) -> dict:
    """The ratchet's findings: new hotspots, raises, stale entries, and raises without a reason."""
    entries = baseline["functions"]
    new = sorted(k for k, v in scores.items() if v > THRESHOLD and k not in entries)
    raised = sorted(k for k, e in entries.items() if k in scores and scores[k] > e["value"])
    stale = sorted(k for k, e in entries.items()
                   if k not in scores or scores[k] < e["value"] or scores[k] <= THRESHOLD)
    unexplained = sorted(k for k, e in entries.items()
                         if e["value"] > e.get("floor", e["value"]) and not str(e.get("reason") or "").strip())
    return {"new": new, "raised": raised, "stale": stale, "unexplained": unexplained,
            "ok": not (new or raised or stale or unexplained)}


def describe(findings: dict, scores: dict[str, int], baseline: dict) -> list[str]:
    e = baseline["functions"]
    out = [f"new over {THRESHOLD}: {k} scores {scores[k]}; bring it to {THRESHOLD} or under, or admit it with "
           f"--update --reason '{k}=why'" for k in findings["new"]]
    out += [f"raised: {k} scores {scores[k]}, recorded {e[k]['value']}; lower it, or record the raise with "
            f"--update --reason '{k}=why'" for k in findings["raised"]]
    out += [f"stale: {k} " + ("is gone" if k not in scores else f"scores {scores[k]}, recorded {e[k]['value']}")
            + "; run python tools/complexity.py --update to tighten the baseline" for k in findings["stale"]]
    out += [f"no reason: {k} is recorded at {e[k]['value']} above its floor {e[k]['floor']}" for k in findings["unexplained"]]
    return out


def updated(scores: dict[str, int], baseline: dict, reasons: dict[str, str]) -> dict:
    """The baseline tightened to the scores: a lowered entry lowered (its floor with it), one at or under the
    threshold or gone dropped; a raise or a new hotspot only where ``reasons`` names it."""
    out = {}
    for k, e in baseline["functions"].items():
        if k not in scores or scores[k] <= THRESHOLD:
            continue
        v = scores[k]
        if v < e["value"]:
            out[k] = {"value": v, "floor": min(v, e.get("floor", v))}
            if v > out[k]["floor"] and e.get("reason"):
                out[k]["reason"] = e["reason"]
        elif v > e["value"]:
            if k not in reasons:
                raise ValueError(f"{k} rose from {e['value']} to {v}: give --reason '{k}=why'")
            out[k] = {"value": v, "floor": e.get("floor", e["value"]), "reason": reasons[k]}
        else:
            out[k] = dict(e)
    for k, v in scores.items():
        if v > THRESHOLD and k not in baseline["functions"]:
            if k not in reasons:
                raise ValueError(f"{k} is new at {v}, over {THRESHOLD}: give --reason '{k}=why' to admit it")
            out[k] = {"value": v, "floor": v, "reason": reasons[k]}
    return {"threshold": THRESHOLD, "functions": dict(sorted(out.items()))}


def initial(scores: dict[str, int]) -> dict:
    return {"threshold": THRESHOLD,
            "functions": {k: {"value": v, "floor": v} for k, v in sorted(scores.items()) if v > THRESHOLD}}


def write(baseline: dict, path: Path = BASELINE) -> None:
    path.write_text(json.dumps(baseline, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="exit 1 on a new hotspot, a raise, a stale entry or a raise without a reason")
    g.add_argument("--update", action="store_true", help="tighten the baseline to the code; a raise or a new hotspot needs --reason")
    g.add_argument("--init", action="store_true", help="write the baseline from scratch")
    ap.add_argument("--reason", action="append", default=[], metavar="KEY=TEXT", help="the reason a function may rise or join the baseline")
    a = ap.parse_args(argv)
    try:
        scores = measure()
        if a.init:
            write(initial(scores))
            print(f"baseline: {sum(1 for v in scores.values() if v > THRESHOLD)} function(s) over {THRESHOLD}, of {len(scores)}")
            return 0
        baseline = load_baseline()
        if a.update:
            reasons = {}
            for r in a.reason:
                key, sep, text = r.partition("=")
                if not sep or not text.strip():
                    raise ValueError(f"--reason {r!r}: give KEY=TEXT")
                reasons[key.strip()] = text.strip()
            new = updated(scores, baseline, reasons)
            write(new)
            print(f"baseline: {len(new['functions'])} function(s) over {THRESHOLD} (was {len(baseline['functions'])})")
            return 0
        findings = check(scores, baseline)
    except (OSError, ValueError, SyntaxError) as e:
        print(f"cannot run: {e}", file=sys.stderr)
        return 2
    lines = describe(findings, scores, baseline)
    if a.check:
        for ln in lines:
            print(ln)
        print("complexity: " + ("the ratchet holds" if findings["ok"] else f"{len(lines)} finding(s)")
              + f" ({len(scores)} functions, {len(baseline['functions'])} in the baseline)")
        return 0 if findings["ok"] else 1
    for k, v in sorted(scores.items(), key=lambda kv: -kv[1]):
        if v > THRESHOLD:
            print(f"{v:4d}  {k}" + ("" if k in baseline["functions"] else "  (not in the baseline)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""task-0251 (doc-0033): the complexity ratchet. tools/complexity.py measures each function's cognitive
complexity as Sonar's rules count it; tools/complexity_baseline.json records today's hotspots. A function
not in the baseline stays at or under 15; one in it stays at or under its recorded value; a lowered,
dropped-to-15 or vanished one is stale until the baseline is tightened; a value above its floor carries a
reason. The measure is held to Sonar's own worked examples."""
from __future__ import annotations

import ast
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import complexity as cx  # noqa: E402


def _score(src: str, name: str | None = None) -> int:
    tree = ast.parse(src)
    fns = list(cx._functions(tree))
    key, node, method = next(f for f in fns if name is None or f[0] == name)
    return cx.score(node, src.splitlines(), method)


def test_the_ratchet_holds_on_the_code_as_committed():
    t0 = time.monotonic()
    scores = cx.measure()
    base = cx.load_baseline()
    findings = cx.check(scores, base)
    assert findings["ok"], "\n".join(cx.describe(findings, scores, base))
    assert time.monotonic() - t0 < 10, "a few seconds in the tests job"
    assert not any(k.startswith("tools/fixtures/") for k in scores), "fixtures are out of scope"
    assert {k.split("/")[0] for k in scores} <= {"harness", "demo", "tools", "instance"}
    assert any(k.startswith("instance/ci/") for k in scores) and any(k.startswith("demo/app/") for k in scores)


def test_the_measure_reads_like_sonars():
    """Campbell's examples (Cognitive Complexity 1.7, §§2-3), in Python."""
    # sumOfPrimes: for +1, for +2 (nesting 1), if +3 (nesting 2); Java's labelled continue (+1) has no Python form
    assert _score("def f(m):\n t = 0\n for i in range(m):\n  for j in range(2, i):\n   if i % j == 0:\n    continue\n  t += i\n return t\n") == 6
    # getWords: a switch is +1 for the whole; match likewise
    assert _score("def f(n):\n match n:\n  case 1:\n   return 'one'\n  case 2:\n   return 'a couple'\n  case _:\n   return 'lots'\n") == 1
    # if / elif / else: +1 each, no nesting penalty for elif and else
    assert _score("def f(a, b):\n if a:\n  pass\n elif b:\n  pass\n else:\n  pass\n") == 3
    # inside a loop the if pays its nesting (+2), elif and else stay +1
    assert _score("def f(xs):\n for x in xs:\n  if x:\n   pass\n  elif x > 1:\n   pass\n  else:\n   pass\n") == 5
    # boolean sequences: a and b and c is one; a and b or c is two; not is nothing
    assert _score("def f(a, b, c):\n return a and b and c\n") == 1
    assert _score("def f(a, b, c):\n return a and b or c\n") == 2
    assert _score("def f(a, b, c, d):\n return a and b or c and d\n") == 3
    assert _score("def f(a):\n return not a\n") == 0
    # try adds nothing; each except pays its nesting
    assert _score("def f():\n try:\n  g()\n except ValueError:\n  pass\n except OSError:\n  pass\n finally:\n  pass\n") == 2
    # a conditional expression nests; a nested function adds nesting, not an increment
    assert _score("def f(a):\n def g():\n  if a:\n   return 1\n return g\n") == 2
    assert _score("def f(a, b):\n return 1 if a else (2 if b else 3)\n") == 3
    # direct recursion, a function or a method
    assert _score("def fact(n):\n return 1 if n < 2 else n * fact(n - 1)\n") == 2
    assert _score("class C:\n def walk(self, n):\n  return [self.walk(c) for c in n]\n", "C.walk") == 1
    # comprehensions' for and if clauses add nothing; their boolean operators do
    assert _score("def f(xs):\n return [x for x in xs if x and x > 1]\n") == 1
    # a loop's else is +1, a while +N
    assert _score("def f(xs):\n while xs:\n  for x in xs:\n   pass\n  else:\n   pass\n") == 4


def _tree(td: str, text: str) -> Path:
    r = Path(td)
    (r / "harness").mkdir()
    (r / "harness" / "m.py").write_text(text, encoding="utf-8")
    return r


HOT = "def hot(a):\n" + "".join(f" if a == {i}:\n  pass\n" for i in range(17))   # 17 ifs, 17
COOL = "def hot(a):\n" + "".join(f" if a == {i}:\n  pass\n" for i in range(16))  # 16


def test_a_new_hotspot_and_a_raise_fail_and_a_reason_admits_them():
    with tempfile.TemporaryDirectory() as td:
        root = _tree(td, HOT)
        scores = cx.measure(root)
        assert scores == {"harness/m.py::hot": 17}
        empty = {"threshold": 15, "functions": {}}
        f = cx.check(scores, empty)
        assert f["new"] == ["harness/m.py::hot"] and not f["ok"], "a new function over 15 fails"
        try:
            cx.updated(scores, empty, {})
            raise AssertionError("--update admitted a new hotspot without a reason")
        except ValueError as e:
            assert "--reason" in str(e)
        admitted = cx.updated(scores, empty, {"harness/m.py::hot": "an urgent fix"})
        assert admitted["functions"]["harness/m.py::hot"] == {"value": 17, "floor": 17, "reason": "an urgent fix"}
        assert cx.check(scores, admitted)["ok"]
        recorded = {"threshold": 15, "functions": {"harness/m.py::hot": {"value": 16, "floor": 16}}}
        f = cx.check(scores, recorded)
        assert f["raised"] == ["harness/m.py::hot"] and not f["ok"], "a baseline function above its value fails"
        try:
            cx.updated(scores, recorded, {})
            raise AssertionError("--update raised a value without a reason")
        except ValueError:
            pass
        raised = cx.updated(scores, recorded, {"harness/m.py::hot": "hotfix; refactor in a follow-up"})
        assert raised["functions"]["harness/m.py::hot"] == {"value": 17, "floor": 16, "reason": "hotfix; refactor in a follow-up"}
        assert cx.check(scores, raised)["ok"]
        bare = {"threshold": 15, "functions": {"harness/m.py::hot": {"value": 17, "floor": 16}}}
        assert cx.check(scores, bare)["unexplained"] == ["harness/m.py::hot"], "above its floor without a reason fails"


def test_a_lowered_or_vanished_function_is_stale_until_the_baseline_tightens():
    with tempfile.TemporaryDirectory() as td:
        root = _tree(td, COOL)
        scores = cx.measure(root)
        recorded = {"threshold": 15, "functions": {"harness/m.py::hot": {"value": 17, "floor": 17},
                                                    "harness/m.py::gone": {"value": 20, "floor": 20}}}
        f = cx.check(scores, recorded)
        assert f["stale"] == ["harness/m.py::gone", "harness/m.py::hot"] and not f["ok"], f
        text = "\n".join(cx.describe(f, scores, recorded))
        assert "is gone" in text and "scores 16, recorded 17" in text and "--update" in text
        tight = cx.updated(scores, recorded, {})
        assert tight["functions"] == {"harness/m.py::hot": {"value": 16, "floor": 16}}, "lowered, its floor with it; the gone one dropped"
        assert cx.check(scores, tight)["ok"]
        (root / "harness" / "m.py").write_text("def hot(a):\n return a\n", encoding="utf-8")
        low = cx.measure(root)
        assert cx.check(low, tight)["stale"] == ["harness/m.py::hot"], "at or under the threshold, it leaves the baseline"
        assert cx.updated(low, tight, {})["functions"] == {}


def test_the_baseline_is_well_formed_and_the_tool_is_standard_library():
    data = json.loads(cx.BASELINE.read_text(encoding="utf-8"))
    assert data["threshold"] == 15 == cx.THRESHOLD
    for k, e in data["functions"].items():
        assert "::" in k and set(e) <= {"value", "floor", "reason"} and e["value"] > 15, (k, e)
        assert e["floor"] <= e["value"], k
    assert list(data["functions"]) == sorted(data["functions"]), "sorted, so a diff reads"
    tree = ast.parse((ROOT / "tools" / "complexity.py").read_text(encoding="utf-8"))
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert mods <= set(sys.stdlib_module_names) | {"__future__"}, mods
    doc = ast.get_docstring(tree)
    for part in ("Where it differs from Sonar", "Cognitive Complexity", "--update", "reason", "floor"):
        assert part in doc, part


def test_the_command_checks_the_tree():
    assert cx.main(["--check"]) == 0

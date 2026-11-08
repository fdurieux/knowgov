"""Step 4's checks (decision-0018 point 1, task-0217): what a reverse-engineering pass reads across documents,
beside each kind's own linter in tools/preload_check.py.

- ``pumllint trace``: pumllint's requirement-coverage matrix with ``--features`` (pumllint 0.35.0 or later, the
  harness's pinned library, called and never copied; an older one leaves the trace unchecked, naming 0.35.0): a requirement no diagram realises, one realised and
  verified by no feature, a reference to an id the inventory lacks, a diagram, feature or scenario that cites none.
- ``glossary``: a term (a code span or a bold phrase) recurring in three or more requirements with no row in the
  instance's glossary.
- ``dmn gaps``: each DMN decision table's input space split into cells at the bounds its rules name; a cell no
  rule matches is a gap, one two rules match under hit policy UNIQUE an overlap (under ANY, when their outputs
  differ), an output column without a type or a rule leaving an output empty an untyped output.

The glossary and DMN checks are this repository's own, written from the published description of the checks
pumllint's recreation experiment ran (subjects/jef_data_load/vendor/docs/recreate-experiment.md); nothing of the
lab's code is copied (pumllint is GPL-3.0-or-later). Each check returns
``{"state", "why", "version", "files", "findings", "read"}`` (read: the files it judged, when it ran), state ``ran``, ``unchecked`` (it cannot run here, or the
instance has nothing it reads; never passed silently) or ``cannot_run`` (it is installed and failed); a finding
is ``{file, rule, severity, line, message}``, the file relative to the instance. Standard library, plus pumllint
for the trace.
"""
from __future__ import annotations

import itertools
import json
import math
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

TRACE_NEEDS = (0, 35, 0)   # the first pumllint whose trace reads --features
TRACE = "pumllint trace"
GLOSSARY = "glossary"
DMN = "dmn gaps"
RECUR = 3                  # a term recurring in this many requirements wants a glossary row
CELLS = 20000              # a table whose input space splits into more cells is not analysed (an info finding)
LISTED = 20                # gaps or overlaps listed per table; the rest counted in one more finding


def _files(inst: Path, kind: str, suffixes: tuple[str, ...] | None = None) -> list[Path]:
    d = inst / "artefacts" / kind
    if not d.is_dir():
        return []
    return sorted(p for p in d.rglob("*") if p.is_file() and not p.name.startswith(".")
                  and (suffixes is None or p.suffix.lower() in suffixes))


def _rel(p: Path, inst: Path) -> str:
    return p.resolve().relative_to(inst).as_posix()


def _line_of(text: str, needle: str) -> int:
    i = text.find(needle)
    return text.count("\n", 0, i) + 1 if i >= 0 else 0


# ---------------------------------------------------------------- pumllint trace --features

def trace_cmd() -> list[str] | None:
    """The pumllint preload_check's linter runs (the harness's pin, else pumllint on PATH), or None."""
    import preload_check
    return preload_check.pumllint_cmd()


def _version(text: str) -> tuple[int, ...] | None:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def run_trace(inst: Path) -> dict:
    """pumllint trace over the instance's diagrams, its requirements as the inventory (--requirements-scan) and its
    feature files (--features). The requirement-id pattern is the instance's own pumllint configuration
    (``rules.requirement-link.pattern`` in pumllint.toml at its root), which pumllint finds itself."""
    need = ".".join(map(str, TRACE_NEEDS))
    diagrams, features = _files(inst, "plantuml-models"), _files(inst, "acceptance-scenarios", (".feature",))
    reqs = _files(inst, "textual-requirements")
    out = {"state": "unchecked", "why": "", "version": None, "files": 0, "findings": []}
    if not diagrams or not features:
        out["why"] = "the instance holds no " + ("diagrams under artefacts/plantuml-models/" if not diagrams
                                                 else "feature files under artefacts/acceptance-scenarios/")
        return out
    cmd = trace_cmd()
    if cmd is None:
        out["why"] = f"pumllint is not installed here; the trace needs pumllint {need} or later"
        return out
    ver = subprocess.run(cmd + ["--version"], cwd=inst, capture_output=True, text=True)
    v = _version(ver.stdout + ver.stderr) if ver.returncode == 0 else None
    out["version"] = ".".join(map(str, v)) if v else None
    if v is None or v < TRACE_NEEDS:
        out["why"] = (f"trace --features needs pumllint {need} or later; the one here is {out['version'] or 'of no readable version'} "
                      "(the harness pins it in demo/Dockerfile)")
        return out
    args = [_rel(p, inst) for p in diagrams] + ["--features", "artefacts/acceptance-scenarios"]
    if reqs:
        args += ["--requirements-scan", "artefacts/textual-requirements"]
    with tempfile.TemporaryDirectory() as td:
        rep = Path(td) / "trace.json"
        p = subprocess.run(cmd + ["trace", *args, "-f", "json", "-o", str(rep)], cwd=inst, capture_output=True, text=True)
        if p.returncode != 0:   # no --fail-on flag is passed: anything but 0 is the trace's own refusal (task-0200 F6 maps the rest)
            err = (p.stderr or p.stdout).strip()
            if "requirement-ID pattern" in err or "requirement-id pattern" in err.lower():
                out["why"] = ("the trace needs a requirement-id pattern: set rules.requirement-link.pattern in pumllint.toml "
                              "at the instance's root")
                return out
            return {**out, "state": "cannot_run", "why": f"{TRACE}: {err[-500:] or f'exit {p.returncode}'}"}
        try:
            raw = json.loads(rep.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            return {**out, "state": "cannot_run", "why": f"{TRACE}: no readable report: {e}"}
    texts = {_rel(p, inst): p.read_text(encoding="utf-8", errors="replace") for p in reqs}

    def where(rid: str) -> tuple[str, int]:
        pat = re.compile(rf"(?<![\w-]){re.escape(rid)}(?![\w-])")
        for f, t in texts.items():
            m = pat.search(t)
            if m:
                return f, t.count("\n", 0, m.start()) + 1
        return "", 0

    fs = out["findings"]
    for r in raw.get("requirements", []):
        f, line = where(r["id"])
        if not f:
            continue
        if not r.get("covered"):
            fs.append({"file": f, "rule": "TRACE-UNCOVERED", "severity": "minor", "line": line,
                       "message": f"{r['id']} is realised by no diagram"})
        elif not r.get("verified"):
            fs.append({"file": f, "rule": "TRACE-UNVERIFIED", "severity": "minor", "line": line,
                       "message": f"{r['id']} is modelled but referenced by no feature"})
    for key, rule in (("unknownReferences", "TRACE-UNKNOWN-REF"), ("unknownFeatureReferences", "TRACE-UNKNOWN-FEATURE-REF")):
        for r in raw.get(key, []):
            for c in r.get("citedBy", []):
                fs.append({"file": c["file"], "rule": rule, "severity": "major", "line": c.get("scenarioLine") or c.get("line") or 0,
                           "message": f"{r['id']} is cited but is in no requirement of the inventory"})
    for r in raw.get("unlinkedDiagrams", []):
        fs.append({"file": r["file"], "rule": "TRACE-UNLINKED-DIAGRAM", "severity": "minor", "line": 0,
                   "message": f"diagram {r.get('name') or r['file']} cites no requirement"})
    for r in raw.get("unlinkedFeatures", []):
        fs.append({"file": r["file"], "rule": "TRACE-UNLINKED-FEATURE", "severity": "minor", "line": 0,
                   "message": f"feature {r.get('name') or r['file']} cites no requirement"})
    for r in raw.get("unlinkedScenarios", []):
        fs.append({"file": r["file"], "rule": "TRACE-UNLINKED-SCENARIO", "severity": "minor", "line": r.get("scenarioLine") or 0,
                   "message": f"scenario {r.get('scenario')!r} cites no requirement"})
    out.update(state="ran", files=len(diagrams) + len(features) + len(reqs), read=[_rel(p, inst) for p in diagrams + features + reqs])
    return out


# ---------------------------------------------------------------- glossary

ID = re.compile(r"(?<![\w-])([A-Z][A-Z0-9]*-\d+)(?![\w-])")
TERM = re.compile(r"`([^`\n]+)`|\*\*([^*\n]+)\*\*")


def _norm(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip().strip("`*_").strip()).lower()


def requirements(text: str) -> list[tuple[str, int, str]]:
    """(id, line, text) for each requirement: a line that opens with an id, in a table's first cell or a list item."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        head = re.match(r"^\s*(?:\|\s*|[-*]\s+|#+\s+)?\**`?([A-Z][A-Z0-9]*-\d+)\b", line)
        if head:
            out.append((head.group(1), n, line))
    return out


def glossary_terms(text: str) -> set[str]:
    """The terms a glossary defines: a table row's first cell (not its header), a heading, or a bold or code term
    opening a list item or a line (``**term**: ...``, ``- `term` - ...``)."""
    out: set[str] = set()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if not cells or set(cells[0]) <= set("-: ") or re.match(r"^\|?\s*:?-{3,}", nxt):
                continue   # a separator, or the header above one
            out.add(_norm(cells[0]))
        elif s.startswith("#"):
            out.add(_norm(s.lstrip("#")))
        else:
            m = re.match(r"^(?:[-*]\s+)?(?:\*\*([^*]+)\*\*|`([^`]+)`)", s)
            if m:
                out.add(_norm(m.group(1) or m.group(2)))
    return {t for t in out if t}


def run_glossary(inst: Path) -> dict:
    reqs = _files(inst, "textual-requirements", (".md", ".txt", ".rst", ".adoc"))
    gloss = _files(inst, "glossary", (".md", ".txt", ".rst", ".adoc"))
    out = {"state": "unchecked", "why": "", "version": None, "files": 0, "findings": []}
    if not reqs or not gloss:
        out["why"] = ("the instance holds no " + ("requirements under artefacts/textual-requirements/" if not reqs
                                                  else "glossary under artefacts/glossary/") + ": nothing to compare")
        return out
    defined: set[str] = set()
    for g in gloss:
        defined |= glossary_terms(g.read_text(encoding="utf-8", errors="replace"))
    uses: dict[str, list[tuple[str, str, int]]] = {}   # term -> (requirement, file, line), one per requirement
    for f in reqs:
        for rid, line, text in requirements(f.read_text(encoding="utf-8", errors="replace")):
            for m in TERM.finditer(text):
                t = _norm(m.group(1) or m.group(2))
                if not t or ID.fullmatch(t.upper()) or re.fullmatch(r"[\d.,%\s<>=-]+", t):
                    continue
                if all(u[0] != rid for u in uses.get(t, [])):
                    uses.setdefault(t, []).append((rid, _rel(f, inst), line))
    for t, us in sorted(uses.items()):
        if len(us) >= RECUR and t not in defined:
            ids = ", ".join(u[0] for u in us)
            out["findings"].append({"file": us[0][1], "rule": "GLOSSARY-UNDEFINED", "severity": "minor", "line": us[0][2],
                                    "message": f"'{t}' recurs in {len(us)} requirements ({ids}) and the glossary defines it nowhere"})
    out.update(state="ran", files=len(reqs) + len(gloss), read=[_rel(p, inst) for p in reqs])   # its findings land on requirements only
    return out


# ---------------------------------------------------------------- DMN gaps, overlaps, untyped outputs

NUMERIC = {"number", "integer", "long", "double", "decimal", "int", "float"}
INTEGRAL = {"integer", "long", "int"}


class Unparsed(ValueError):
    pass


def _local(el: ET.Element) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _kids(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if _local(c) == name]


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    t = next((c for c in el if _local(c) == "text"), None)
    return ((t.text if t is not None else el.text) or "").strip()


def _split(entry: str) -> list[str]:
    """A FEEL unary test list split at its top-level commas (none inside quotes or brackets)."""
    parts, depth, quote, cur = [], 0, False, ""
    for ch in entry:
        if ch == '"':
            quote = not quote
        elif not quote and ch in "[(":
            depth += 1
        elif not quote and ch in "])" and depth:
            depth -= 1
        if ch == "," and not quote and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    parts.append(cur.strip())
    return [p for p in parts if p]


def _num(s: str) -> float:
    try:
        return float(s.strip())
    except ValueError:
        raise Unparsed(s) from None


def numeric(entry: str) -> list[tuple[float, bool, float, bool]] | None:
    """A numeric unary test as intervals (lo, lo closed, hi, hi closed); None for '-' (any)."""
    e = entry.strip()
    if e in ("", "-"):
        return None
    out = []
    for p in _split(e):
        m = re.fullmatch(r"(<=|>=|<|>|=)?\s*(-?[\d.]+)", p)
        r = re.fullmatch(r"([\[\]\(])\s*(-?[\d.]+)\s*\.\.\s*(-?[\d.]+)\s*([\[\]\)])", p)
        if m:
            op, n = m.group(1) or "=", _num(m.group(2))
            out.append({"<": (-math.inf, False, n, False), "<=": (-math.inf, False, n, True), ">": (n, False, math.inf, False),
                        ">=": (n, True, math.inf, False), "=": (n, True, n, True)}[op])
        elif r:
            out.append((_num(r.group(2)), r.group(1) == "[", _num(r.group(3)), r.group(4) == "]"))
        else:
            raise Unparsed(p)
    return out


def discrete(entry: str) -> set[str] | None:
    """A string or boolean unary test as the set of literals it names; None for '-' (any)."""
    e = entry.strip()
    if e in ("", "-"):
        return None
    out = set()
    for p in _split(e):
        if re.fullmatch(r'"[^"]*"', p) or p in ("true", "false"):
            out.add(p)
        else:
            raise Unparsed(p)
    return out


def _inside(x: float, iv: tuple[float, bool, float, bool]) -> bool:
    lo, lc, hi, hc = iv
    return (x > lo or (lc and x == lo)) and (x < hi or (hc and x == hi))


def _fmt(n: float) -> str:
    return "-inf" if n == -math.inf else "inf" if n == math.inf else (str(int(n)) if n == int(n) else repr(n))


def numeric_cells(bounds: set[float], integral: bool) -> list[tuple[float, str]]:
    """The input's cells at the bounds its rules name: each bound, and the open interval between two, each with a
    value inside it; an integral input's interval with no integer in it is no cell."""
    bs = sorted(bounds)
    edges = [-math.inf, *bs, math.inf]
    out = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if lo == -math.inf and hi == math.inf:
            rep = 0.0
        elif lo == -math.inf:
            rep = hi - 1
        elif hi == math.inf:
            rep = lo + 1
        elif integral:
            rep = math.floor(lo) + 1
            if rep >= hi:
                rep = None
        else:
            rep = (lo + hi) / 2
        if rep is not None:
            out.append((rep, f"in ({_fmt(lo)}, {_fmt(hi)})"))
        if i < len(bs):
            out.append((bs[i], f"= {_fmt(bs[i])}"))
    return out


def check_table(table: ET.Element, text: str, file: str) -> list[dict]:
    """One decisionTable's findings."""
    fs: list[dict] = []
    name = table.get("id") or "decisionTable"
    policy = (table.get("hitPolicy") or "UNIQUE").upper()
    inputs = _kids(table, "input")
    outputs = _kids(table, "output")
    rules = _kids(table, "rule")
    line = _line_of(text, f'id="{name}"')

    def rline(r):
        return _line_of(text, f'id="{r.get("id")}"') if r.get("id") else line

    for o in outputs:
        if not o.get("typeRef"):
            fs.append({"file": file, "rule": "DMN-UNTYPED-OUTPUT", "severity": "minor", "line": _line_of(text, f'id="{o.get("id")}"') or line,
                       "message": f"{name}: output {o.get('name') or o.get('label') or o.get('id')} has no typeRef"})
    for r in rules:
        entries = _kids(r, "outputEntry")
        for i, o in enumerate(outputs):
            v = _text(entries[i]) if i < len(entries) else ""
            if v in ("", "-", "null"):
                fs.append({"file": file, "rule": "DMN-UNTYPED-OUTPUT", "severity": "minor", "line": rline(r),
                           "message": f"{name}: rule {r.get('id')} gives output {o.get('name') or o.get('label') or o.get('id')} no value"})
    if not inputs or not rules:
        return fs

    kinds, domains, tests = [], [], []
    try:
        for j, inp in enumerate(inputs):
            expr = next((c for c in inp if _local(c) == "inputExpression"), None)
            tref = (expr.get("typeRef") if expr is not None else None) or inp.get("typeRef") or ""
            label = inp.get("label") or _text(expr) or inp.get("id") or f"input {j + 1}"
            col = [_text(_kids(r, "inputEntry")[j]) if j < len(_kids(r, "inputEntry")) else "-" for r in rules]
            allowed = _text(next((c for c in inp if _local(c) == "inputValues"), None))
            num = tref.lower() in NUMERIC or (not tref and all(re.fullmatch(r"[-\d.\s<>=\[\]().,]*", c) for c in col))
            if tref.lower() == "boolean" or (not num and all(c in ("", "-", "true", "false") for c in col)):
                parsed = [discrete(c) for c in col]
                kinds.append(("bool", label))
                domains.append([(v, f"= {v}") for v in ("true", "false")])
            elif num:
                parsed = [numeric(c) for c in col]
                dom = numeric(allowed) if allowed else None
                bounds = {b for p in parsed + [dom] if p for iv in p for b in (iv[0], iv[2]) if math.isfinite(b)}
                cells = numeric_cells(bounds, tref.lower() in INTEGRAL)
                if dom:
                    cells = [c for c in cells if any(_inside(c[0], iv) for iv in dom)]
                kinds.append(("num", label))
                domains.append(cells)
            else:
                parsed = [discrete(c) for c in col]
                dom = discrete(allowed) if allowed else None
                values = sorted(dom) if dom else sorted({v for p in parsed if p for v in p})
                kinds.append(("str", label))
                domains.append([(v, f"= {v}") for v in values] or [("*", "any value")])
            tests.append(parsed)
    except Unparsed as e:
        fs.append({"file": file, "rule": "DMN-UNREAD", "severity": "info", "line": line,
                   "message": f"{name}: the entry {str(e)!r} is not a unary test this check reads; gaps and overlaps not analysed"})
        return fs
    total = math.prod(len(d) for d in domains)
    if total > CELLS:
        fs.append({"file": file, "rule": "DMN-UNREAD", "severity": "info", "line": line,
                   "message": f"{name}: {total} cells exceed the check's {CELLS}; gaps and overlaps not analysed"})
        return fs

    def matches(ri: int, cell) -> bool:
        for j, (value, _) in enumerate(cell):
            t = tests[j][ri]
            if t is None:
                continue
            if kinds[j][0] == "num":
                if not any(_inside(value, iv) for iv in t):
                    return False
            elif value not in t:
                return False
        return True

    def where(cell) -> str:
        return "; ".join(f"{kinds[j][1]} {d}" for j, (_, d) in enumerate(cell))

    def outs(r) -> tuple[str, ...]:
        return tuple(_text(e) for e in _kids(r, "outputEntry"))

    gaps, overlaps = [], []
    for cell in itertools.product(*domains):
        hit = [i for i in range(len(rules)) if matches(i, cell)]
        if not hit:
            gaps.append(cell)
        elif len(hit) > 1 and (policy == "UNIQUE" or (policy == "ANY" and len({outs(rules[i]) for i in hit}) > 1)):
            overlaps.append((cell, hit))
    for cell in gaps[:LISTED]:
        fs.append({"file": file, "rule": "DMN-GAP", "severity": "minor", "line": line,
                   "message": f"{name}: no rule matches {where(cell)}"})
    for cell, hit in overlaps[:LISTED]:
        fs.append({"file": file, "rule": "DMN-OVERLAP", "severity": "major", "line": rline(rules[hit[1]]),
                   "message": f"{name} ({policy}): rules {', '.join(rules[i].get('id') or str(i + 1) for i in hit)} all match {where(cell)}"})
    for what, items in (("DMN-GAP", gaps), ("DMN-OVERLAP", overlaps)):
        if len(items) > LISTED:
            fs.append({"file": file, "rule": what, "severity": "minor" if what == "DMN-GAP" else "major", "line": line,
                       "message": f"{name}: {len(items) - LISTED} further cells, beyond the {LISTED} listed"})
    return fs


def run_dmn(inst: Path) -> dict:
    files = _files(inst, "decision-tables", (".dmn",))
    out = {"state": "unchecked", "why": "", "version": None, "files": 0, "findings": []}
    if not files:
        out["why"] = "the instance holds no .dmn file under artefacts/decision-tables/"
        return out
    read = []   # the files holding a decision table: one with none (or not XML, dmnlint's to say) is not this check's
    for f in files:
        rel, text = _rel(f, inst), f.read_text(encoding="utf-8", errors="replace")
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            continue
        tables = [t for t in root.iter() if _local(t) == "decisionTable"]
        if tables:
            read.append(rel)
        for table in tables:
            out["findings"].extend(check_table(table, text, rel))
    if not read:
        out["why"] = "no .dmn file under artefacts/decision-tables/ holds a decision table this check reads"
        return out
    out.update(state="ran", files=len(read), read=read)
    return out


# check -> (the kinds it reads, the runner); tools/preload_check.py runs each after the kinds' own linters
CHECKS = {TRACE: (("plantuml-models", "acceptance-scenarios", "textual-requirements"), run_trace),
          GLOSSARY: (("textual-requirements", "glossary"), run_glossary),
          DMN: (("decision-tables",), run_dmn)}

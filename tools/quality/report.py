"""The advisory SonarQube scan's export and debt delta (task-0250, doc-0033). Standard library only.

    python tools/quality/report.py export OUT_DIR       # from the scan's server: issues, hotspots, measures
    python tools/quality/report.py delta OUT_DIR [--previous DIR] [--baseline FILE]   # Markdown on stdout

``export`` reads the server at ``SONAR_HOST_URL`` (the workflow's service container on loopback, by default
``http://127.0.0.1:9000``) with the token in ``SONAR_TOKEN``, for the project ``SONAR_PROJECT`` (``knowgov``),
and writes ``issues.json``, ``hotspots.json``, ``measures.json`` and ``meta.json`` (``KG_QUALITY_REF``, the
commit, the server's version). It asks that server and nothing else.

``delta`` compares one export with the previous release's (``--previous``, when the workflow found its
artefact) and with the in-repository triage baseline (``--baseline``, ``tools/quality/baseline.json``): new and
gone issues by type and severity, the cognitive-complexity hotspots, duplication and coverage. An issue is
known by its rule, file and message, not its line, so an edit above it does not make it new. A baseline entry
accepts up to ``count`` issues of its rule in its file with its reason (``rule``, ``path``, optional ``message``
and ``count``, ``reason``); in code, ``# NOSONAR(<rule>) <why>`` does the same for one line (the form SonarQube's
Python analyser reads: ``# NOSONAR: <why>`` suppresses nothing and is itself flagged, python:S7632). The delta is advice: it never fails, and a missing previous export
is said, not an error.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

DEFAULT_SERVER = "http://127.0.0.1:9000"
METRICS = ["ncloc", "bugs", "vulnerabilities", "code_smells", "security_hotspots", "sqale_index", "cognitive_complexity",
           "duplicated_lines_density", "duplicated_blocks", "coverage", "line_coverage", "branch_coverage",
           "lines_to_cover", "uncovered_lines", "conditions_to_cover", "uncovered_conditions"]
COMPLEXITY_RULE = "python:S3776"
TYPES = ["BUG", "VULNERABILITY", "CODE_SMELL"]
SEVERITIES = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]


def _get(path: str, params: dict) -> dict:
    base = os.environ.get("SONAR_HOST_URL", DEFAULT_SERVER).rstrip("/")
    req = urllib.request.Request(f"{base}{path}?{urllib.parse.urlencode(params)}")
    token = os.environ.get("SONAR_TOKEN", "")
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{token}:".encode()).decode())
    with urllib.request.urlopen(req, timeout=60) as r:   # the scan's own server, on loopback
        return json.load(r)


def _pages(path: str, params: dict, key: str) -> list[dict]:
    out, page = [], 1
    while True:
        d = _get(path, {**params, "ps": 500, "p": page})
        out += d.get(key, [])
        total = d.get("paging", {}).get("total", d.get("total", 0))
        if page * 500 >= min(total, 10000) or not d.get(key):
            return out
        page += 1


def _path(component: str, project: str) -> str:
    return component.split(":", 1)[1] if component.startswith(project + ":") else component


def export(out: Path) -> dict:
    project = os.environ.get("SONAR_PROJECT", "knowgov")
    issues = [{"rule": i["rule"], "type": i.get("type"), "severity": i.get("severity"),
               "path": _path(i["component"], project), "line": i.get("line"), "message": i.get("message", "")}
              for i in _pages("/api/issues/search", {"componentKeys": project, "issueStatuses": "OPEN,CONFIRMED"}, "issues")]
    hotspots = [{"rule": h.get("ruleKey"), "path": _path(h["component"], project), "line": h.get("line"),
                 "category": h.get("securityCategory"), "probability": h.get("vulnerabilityProbability"),
                 "message": h.get("message", "")}
                for h in _pages("/api/hotspots/search", {"project": project}, "hotspots")]
    comp = _get("/api/measures/component", {"component": project, "metricKeys": ",".join(METRICS)})["component"]
    measures = {m["metric"]: m.get("value") for m in comp.get("measures", [])}
    meta = {"ref": os.environ.get("KG_QUALITY_REF", ""), "commit": os.environ.get("GITHUB_SHA", ""),
            "server": os.environ.get("SONAR_SERVER_VERSION", ""),
            "scanner": os.environ.get("SONAR_SCANNER_VERSION", ""), "profile": os.environ.get("SONAR_PROFILE", "knowgov")}
    out.mkdir(parents=True, exist_ok=True)
    for name, data in (("issues", issues), ("hotspots", hotspots), ("measures", measures), ("meta", meta)):
        (out / f"{name}.json").write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return {"issues": len(issues), "hotspots": len(hotspots), "measures": measures}


def _load(d: Path | None, name: str):
    if d is None or not (d / f"{name}.json").is_file():
        return None
    return json.loads((d / f"{name}.json").read_text(encoding="utf-8"))


def fingerprint(i: dict) -> tuple:
    return (i["rule"], i["path"], i.get("message", ""))


def _matches(b: dict, i: dict) -> bool:
    return b["rule"] == i["rule"] and b["path"] == i["path"] and b.get("message", i.get("message", "")) == i.get("message", "")


def split(issues: list[dict], baseline: list[dict]) -> tuple[list[dict], list[dict]]:
    """(open, accepted): each baseline entry accepts at most ``count`` issues (1 by default) of its rule in its
    file, in line order, so a further one in the same file is still open and shows in the delta."""
    left = {n: b.get("count", 1) for n, b in enumerate(baseline)}
    open_, acc = [], []
    for i in sorted(issues, key=lambda x: (x["path"], x.get("line") or 0, x["rule"])):
        n = next((n for n, b in enumerate(baseline) if left[n] > 0 and _matches(b, i)), None)
        if n is None:
            open_.append(i)
        else:
            left[n] -= 1
            acc.append(i)
    return open_, acc


def _complexity(i: dict) -> int:
    m = re.search(r"from (\d+) to", i.get("message", ""))
    return int(m.group(1)) if m else 0


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _intro(meta: dict, pmeta: dict, prev_dir: Path | None, has_prev: bool, baseline: list[dict]) -> list[str]:
    if has_prev:
        against = f"Compared with **{pmeta.get('ref') or prev_dir}**."
    else:
        against = "No previous release's export was found, so this run is the baseline."
    return [f"## Advisory SonarQube scan: {meta.get('ref') or '(this run)'}", "",
            f"Advice, never a gate (task-0250). {against} "
            f"{len(baseline)} finding(s) accepted in `tools/quality/baseline.json`.", ""]


def _by_type(open_: list[dict], prev_open: list[dict] | None) -> list[str]:
    out = ["### Issues by type and severity", "",
           "| type | " + " | ".join(SEVERITIES) + " | total | previous | change |", "|---|" + "---:|" * (len(SEVERITIES) + 3)]
    for t in TYPES:
        row = Counter(i["severity"] for i in open_ if i["type"] == t)
        n = sum(row.values())
        if prev_open is None:
            was, change = "—", "—"
        else:
            p = sum(1 for i in prev_open if i["type"] == t)
            was, change = str(p), f"{n - p:+d}"
        out.append(f"| {t} | " + " | ".join(str(row.get(s, 0)) for s in SEVERITIES) + f" | {n} | {was} | {change} |")
    return out


def _new_and_gone(open_: list[dict], prev_open: list[dict], prev_ref: str) -> list[str]:
    now_fp = Counter(fingerprint(i) for i in open_)
    new = now_fp - Counter(fingerprint(i) for i in prev_open)
    gone = Counter(fingerprint(i) for i in prev_open) - now_fp
    out = [f"### New since {prev_ref}: {sum(new.values())}; gone: {sum(gone.values())}", ""]
    by_rule = Counter()
    for (rule, _p, _m), n in new.items():
        by_rule[rule] += n
    out += [f"- `{rule}` +{n}" for rule, n in by_rule.most_common(15)]
    listed = [i for i in open_ if new.get(fingerprint(i))][:25]
    out += [f"  - new: `{i['rule']}` {i['path']}:{i.get('line') or '?'} {i.get('message', '')[:120]}" for i in listed]
    return out + [""]


def _hotspots(cur: list[dict], prev: list[dict] | None) -> list[str]:
    cx = sorted((i for i in cur if i["rule"] == COMPLEXITY_RULE), key=_complexity, reverse=True)
    was = [i for i in (prev or []) if i["rule"] == COMPLEXITY_RULE]
    seen = {(i["path"], _complexity(i)) for i in was}
    head = f"{len(cx)} function(s) over the threshold" + ("" if prev is None else f", {len(was)} at the previous release")
    out = ["### Cognitive-complexity hotspots (threshold 15)", "", head + ".", "",
           "| complexity | where | since previous |", "|---:|---|---|"]
    for i in cx[:15]:
        mark = "same" if (i["path"], _complexity(i)) in seen else "changed or new"
        out.append(f"| {_complexity(i)} | {i['path']}:{i.get('line') or '?'} | {'—' if prev is None else mark} |")
    return out


def _measures(m_now: dict, m_prev: dict) -> list[str]:
    out = ["### Measures", "", "| measure | now | previous | change |", "|---|---:|---:|---:|"]
    for k in METRICS:
        a, b = _num(m_now.get(k)), _num(m_prev.get(k))
        ch = "—" if a is None or b is None else f"{a - b:+g}"
        out.append(f"| {k} | {m_now.get(k, '—')} | {m_prev.get(k, '—')} | {ch} |")
    return out + ["", "Coverage is `tools/coverage_stdlib.py`'s, in-process, against its declared denominator "
                  "(the counted modules; child processes not instrumented), imported through `tools/quality/coverage_xml.py`.", ""]


def delta(cur_dir: Path, prev_dir: Path | None, baseline: list[dict]) -> str:
    """The Markdown debt delta: issues by type and severity, new and gone, complexity hotspots, measures."""
    cur = _load(cur_dir, "issues") or []
    prev = _load(prev_dir, "issues")
    meta, pmeta = _load(cur_dir, "meta") or {}, _load(prev_dir, "meta") or {}
    open_, acc = split(cur, baseline)
    prev_open = None if prev is None else split(prev, baseline)[0]
    hot = _load(cur_dir, "hotspots") or []
    lines = _intro(meta, pmeta, prev_dir, prev is not None, baseline) + _by_type(open_, prev_open)
    lines += ["", f"{len(open_)} open, {len(acc)} accepted by the baseline, {len(hot)} security hotspot(s) to review.", ""]
    if prev_open is not None:
        lines += _new_and_gone(open_, prev_open, pmeta.get("ref") or "the previous release")
    lines += _hotspots(cur, prev) + [""] + _measures(_load(cur_dir, "measures") or {}, _load(prev_dir, "measures") or {})
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("out")
    d = sub.add_parser("delta")
    d.add_argument("current")
    d.add_argument("--previous")
    d.add_argument("--baseline", default=str(Path(__file__).with_name("baseline.json")))
    a = ap.parse_args(argv)
    if a.cmd == "export":
        got = export(Path(a.out))
        print(f"export: {got['issues']} issue(s), {got['hotspots']} hotspot(s), {len(got['measures'])} measure(s) -> {a.out}")
    else:
        base = json.loads(Path(a.baseline).read_text(encoding="utf-8")).get("accepted", []) if Path(a.baseline).is_file() else []
        prev = Path(a.previous) if a.previous and Path(a.previous, "issues.json").is_file() else None
        sys.stdout.write(delta(Path(a.current), prev, base))
    return 0   # export raises when the server cannot answer; the delta is advice and never fails


if __name__ == "__main__":
    sys.exit(main())

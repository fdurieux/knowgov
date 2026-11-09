"""A knowgov report as a CI platform's annotations (task-0083): standard library only.

    python harness/annotate.py REPORT -t github|summary|gitlab|sarif [-o FILE]
                               [--instance DIR] [--subject DIR] [--root DIR]

REPORT is what ``KG_REPORT`` holds: the gate's (``gate_cli.py -o``), the trace's (``trace.py -o``)
or the pre-load check's (``preload_check.py -o``), read by its ``tool`` field.

- ``github``: workflow commands, one per finding (``::error``, ``::warning``, ``::notice``), for
  the job's log; GitHub shows them on the run and on the pull request's changed files.
- ``summary``: a Markdown table of the verdict and the findings, for ``$GITHUB_STEP_SUMMARY``.
- ``gitlab``: a code-quality report (an array of issues), for ``artifacts:reports:codequality``;
  the severity ladder is GitLab's own, one to one.
- ``sarif``: SARIF 2.1.0, one run, a rule per finding kind, for any SARIF viewer (GitHub code
  scanning among them).

A finding at or above the report's threshold is an error (it is what made the command exit 1);
below it, a warning, and ``info`` a notice. A finding the report marks ``held`` (the gate's under
``--baseline``, which exits on a regression only; the pre-load check's baseline) did not fail the
command, so it is at most a warning (task-0106, task-0207). Where a finding points: a trace finding's ``path``
under the code map's root (the report's ``code_root``, relative to ``--instance``); a pre-load
finding's file and line (relative to ``--instance``), and with its ``layout`` block each layout problem's
file (task-0115; only a layout error is an error, the rest warnings and notices); anything else (a key, a statement, the
task, a derived output) at the subject's ``subject.toml`` (``--subject``), since the report names
statements, not their place in a document. Paths are written relative to ``--root`` (default the
working directory, the repository's root in a CI job). A finding that names its keys' owner and route (the
gate's key findings, task-0102; the trace's, task-0304) carries them at the end of its message, so the
annotation says who answers and how. Exit 0, or 2 when the report cannot be read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

LADDER = ("blocker", "critical", "major", "minor", "info")
FORMATS = ("github", "summary", "gitlab", "sarif")
TOOLS = {"knowgov gate": "gate", "knowgov trace": "trace", "knowgov preload check": "preload"}


class CannotRun(Exception):
    pass


def read(path: Path) -> dict:
    try:
        rep = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CannotRun(f"cannot read the report {path}: {e}") from e
    if not isinstance(rep, dict) or rep.get("tool") not in TOOLS:
        raise CannotRun(f"{path} is not a knowgov gate, trace or pre-load report")
    return rep


def _rel(p: Path, root: Path) -> str:
    return Path(os.path.relpath(p.resolve(), root.resolve())).as_posix()


def findings(rep: dict, instance: Path | None = None, subject: Path | None = None, root: Path | None = None) -> list[dict]:
    """Every finding of the report, flat: severity, kind, title, message, path (or None), line."""
    root = root or Path.cwd()
    fallback = _rel(subject / "subject.toml", root) if subject else None
    tool = TOOLS[rep["tool"]]
    out = []
    if tool == "preload":
        for f in rep["files"]:
            where = _rel(instance / f["file"], root) if instance else f["file"]
            for x in f["findings"]:
                out.append({"severity": x["severity"], "kind": f"preload:{x['rule']}", "id": x["rule"], "path": where,
                            "line": max(int(x["line"]), 1), "title": f"{f['tool'] or 'lint'} {x['rule']}" + (" (held by the baseline)" if x.get("held") else ""),
                            "message": x["message"], "held": bool(x.get("held"))})
            if f["state"] in ("unchecked", "cannot_run") and not f["findings"]:
                out.append({"severity": "info", "kind": f"preload:{f['state']}", "id": f["state"], "path": where, "line": 1,
                            "title": f"pre-load {f['state'].replace('_', ' ')}", "message": f["why"]})
        for x in (rep.get("layout") or {}).get("problems", []):   # task-0115: the layout check's, with --layout
            where = (_rel(instance / x["path"], root) if instance else x["path"]) if x["path"] else None
            out.append({"severity": x["severity"], "kind": f"layout:{x['kind']}", "id": x["kind"], "path": where, "line": 1,
                        "title": f"knowgov layout {x['kind']}", "message": x["message"],
                        "held": not x["fails"]})   # only a layout error failed the step: the rest is never an error
        return out
    for f in rep["findings"]:
        path = f.get("path")
        if path and tool == "trace":
            base = (instance / rep["code_root"]) if instance else Path(rep["code_root"])
            path = _rel(base / path, root) if instance else (base / path).as_posix()
        ident = f.get("ref") or f.get("key") or path or f.get("app") or ""
        subject_of = f.get("app") or f.get("key") or f.get("ref")
        held = bool(f.get("held"))   # task-0207, R8: under --baseline, a finding the baseline held did not fail the gate
        title = f"knowgov {tool} {f['kind']}" + (f" {subject_of}" if subject_of else "") + (" (held by the baseline)" if held else "")
        out.append({"severity": f["severity"], "kind": f["kind"], "id": ident, "path": path or fallback,
                    "line": 1, "title": title, "message": f["message"] + _answers(f), "held": held})
    return out


def _answers(f: dict) -> str:
    """Who answers for the keys a finding rests on, and how (task-0304): its owner and route, as the gate and the
    trace name them; nothing for a finding that names none."""
    if "owner" not in f and "route" not in f:
        return ""
    owner = f.get("owner") or "no single unit (several, or none in the register map)"
    return f" Owner: {owner}." + (f" Route: {f['route']}" if f.get("route") else "")


def level(severity: str, threshold: str | None, held: bool = False) -> str:
    """error, warning or notice: at or above the threshold an error, info a notice; a finding the
    pre-load baseline holds did not fail the check, so it is at most a warning (task-0106)."""
    t = threshold if threshold in LADDER else "major"
    if LADDER.index(severity) <= LADDER.index(t) and not held:
        return "error"
    return "notice" if severity == "info" else "warning"


def _esc_data(s: str) -> str:
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _esc_prop(s: str) -> str:
    return _esc_data(s).replace(":", "%3A").replace(",", "%2C")


def github(rep: dict, fs: list[dict]) -> str:
    lines = []
    for f in fs:
        props = []
        if f["path"]:
            props += [f"file={_esc_prop(f['path'])}", f"line={f['line']}"]
        props.append(f"title={_esc_prop(f['title'] + ' (' + f['severity'] + ')')}")
        lines.append(f"::{level(f['severity'], rep.get('threshold'), f.get('held', False))} {','.join(props)}::{_esc_data(f['message'])}")
    return "\n".join(lines) + ("\n" if lines else "")


def _verdict(rep: dict) -> str:
    tool = TOOLS[rep["tool"]]
    if tool == "gate":
        return f"{rep['verdict']}: {rep['why']}"
    if tool == "trace" and rep.get("gate"):
        return f"trace {rep['command']}; the task's gate {rep['gate']['verdict']}: {rep['gate']['why']}"
    if tool == "trace":
        return f"trace {rep['command']}"
    return rep.get("note", "pre-load check")


def summary(rep: dict, fs: list[dict]) -> str:
    cell = lambda s: str(s).replace("|", "\\|").replace("\n", " ")   # noqa: E731
    out = [f"### {rep['tool']}: exit {rep['exit_code']}", "", cell(_verdict(rep)), ""]
    if fs:
        out += ["| severity | kind | where | finding |", "|---|---|---|---|"]
        out += [f"| {f['severity']} | {cell(f['kind'])} | {cell(f['path'] or '')} | {cell(f['message'])} |" for f in fs]
    else:
        out.append("No findings.")
    return "\n".join(out) + "\n\n"


def _fingerprint(rep: dict, f: dict, seen: set[str]) -> str:
    base = "|".join([rep["tool"], f["kind"], f["id"], f["path"] or "", str(f["line"])])
    fp, n = hashlib.md5(base.encode(), usedforsecurity=False).hexdigest(), 1   # an identifier GitLab compares, not a secret
    while fp in seen:
        n += 1
        fp = hashlib.md5(f"{base}|{n}".encode(), usedforsecurity=False).hexdigest()
    seen.add(fp)
    return fp


def gitlab(rep: dict, fs: list[dict]) -> str:
    seen: set[str] = set()
    issues = [{"description": f"{f['title']}: {f['message']}", "check_name": f"knowgov-{f['kind']}",
               "fingerprint": _fingerprint(rep, f, seen), "severity": f["severity"],
               "location": {"path": f["path"] or ".", "lines": {"begin": f["line"]}}} for f in fs]
    return json.dumps(issues, indent=1) + "\n"


def sarif(rep: dict, fs: list[dict]) -> str:
    sl = {"error": "error", "warning": "warning", "notice": "note"}
    rules = sorted({f["kind"] for f in fs})
    results = []
    for f in fs:
        r = {"ruleId": f["kind"], "ruleIndex": rules.index(f["kind"]), "level": sl[level(f["severity"], rep.get("threshold"), f.get("held", False))],
             "message": {"text": f["message"]}, "properties": {"severity": f["severity"], "ref": f["id"]}}
        if f["path"]:
            r["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": f["path"]}, "region": {"startLine": f["line"]}}}]
        results.append(r)
    doc = {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": rep["tool"], "informationUri": "https://github.com/fdurieux/knowgov",
                            "rules": [{"id": k, "shortDescription": {"text": f"knowgov finding of kind {k}"}} for k in rules]}},
        "results": results}]}
    return json.dumps(doc, indent=1) + "\n"


RENDER = {"github": github, "summary": summary, "gitlab": gitlab, "sarif": sarif}


def convert(rep: dict, fmt: str, **where) -> str:
    return RENDER[fmt](rep, findings(rep, **where))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("report", type=Path)
    ap.add_argument("-t", "--to", choices=FORMATS, required=True)
    ap.add_argument("-o", "--out", type=Path, help="write here (default stdout)")
    ap.add_argument("--instance", type=Path, help="the instance checkout a trace or pre-load report's paths hang from")
    ap.add_argument("--subject", type=Path, help="the subject root: findings without a file point at its subject.toml")
    ap.add_argument("--root", type=Path, help="write paths relative to this directory (default the working directory)")
    a = ap.parse_args(argv)
    try:
        text = convert(read(a.report), a.to, instance=a.instance, subject=a.subject, root=a.root)
    except CannotRun as e:
        print(f"knowgov annotate: {e}", file=sys.stderr)
        return 2
    if a.out:
        try:
            a.out.write_text(text, encoding="utf-8")
        except OSError as e:   # task-0267: a file it cannot write is a message, never a traceback
            print(f"knowgov annotate: cannot write {a.out}: {e.strerror or e}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

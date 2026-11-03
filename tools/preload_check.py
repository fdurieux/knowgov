"""Check each document's form with its kind's linter before the load (task-0045; doc-0008 §5).

    python tools/preload_check.py <instance> [--changed FILE ...] [--since REF]
                                  [--fail-on blocker|critical|major|minor|info] [-f text|json] [-o FILE]

For each file under the instance's artefacts/<kind>/ (every file, or only those named by
--changed, or only those changed since the git ref REF in the instance's checkout), run the
linter instance/kinds.toml names for the kind, when this environment can run it. Today one can:
pumllint, for plantuml-models, the harness's own pin. Every other kind's files are reported
*unchecked*, naming the tool the programme's table names (or saying it names none): an
unchecked file does not fail the check, and it is never passed silently.

The programme's gate contract:

    0  every checked file is clean at the threshold (unchecked files are listed, not failed)
    1  a finding at or above --fail-on (default major, pumllint's own) in a checked file
    2  cannot run: no such instance, a kind folder instance/kinds.toml does not know, a file at
       the top of artefacts/, a named file that does not exist or lies outside the instance, a
       linter this kind needs that is not installed or could not run, a --since git cannot diff

A --changed file outside artefacts/ (a subject manifest, a register row) is listed as skipped:
it is not a document of a kind. The JSON report (-f json) is pinned by
harness/schemas/preload-report.schema.json through harness/schema_check.py.

What it is not: it checks form, one file at a time, for its kind. It does not check knowledge;
two well-formed documents that disagree, or a fact nobody wrote down, pass it. That is the
knowgov gate's question (harness/gate_cli.py), after the load; neither replaces the other. The
check reads the instance and never writes to it; the linter runs with the instance as its
working directory, so an instance's own linter configuration applies.
Standard library, plus the linters it runs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_instance  # noqa: E402

SEVERITIES = ["blocker", "critical", "major", "minor", "info"]   # the contract's ladder, worst first
STATES = ["clean", "findings", "unchecked", "cannot_run", "skipped"]
NAMES_NONE = {"none", "none maintained"}


def pumllint_cmd() -> list[str] | None:
    """The command that runs pumllint here, or None when it is not installed."""
    if importlib.util.find_spec("pumllint") is not None:
        return [sys.executable, "-m", "pumllint"]
    exe = shutil.which("pumllint")
    return [exe] if exe else None


def run_pumllint(files: list[Path], cwd: Path, threshold: str) -> dict:
    """{rc, version, findings: [{file, rule, severity, line, message}], error}; rc 2 when it cannot run."""
    cmd = pumllint_cmd()
    if cmd is None:
        return {"rc": 2, "version": None, "findings": [], "error": "pumllint is not installed (pip install pumllint)"}
    ver = subprocess.run(cmd + ["--version"], cwd=cwd, capture_output=True, text=True)
    version = (ver.stdout.strip() or ver.stderr.strip()).split()[-1] if ver.returncode == 0 else None
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "report.json"
        p = subprocess.run(cmd + ["-f", "json", "-o", str(out), "--fail-on", threshold] + [str(f) for f in files],
                           cwd=cwd, capture_output=True, text=True)
        if p.returncode not in (0, 1):
            return {"rc": 2, "version": version, "findings": [], "error": (p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}"}
        try:
            raw = json.loads(out.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            return {"rc": 2, "version": version, "findings": [], "error": f"no readable report: {e}"}
    findings = [{"file": str((cwd / f["file"]).resolve()), "rule": f.get("ruleId", ""), "severity": f["severity"],
                 "line": f.get("line") or 0, "message": f.get("message", "")} for f in raw]
    return {"rc": p.returncode, "version": version, "findings": findings, "error": None}


# kind folder -> (the tool's name as kinds.toml names it, the runner). The only linter this
# repository's environment installs; a kind added here must name the same tool in kinds.toml.
RUNNERS = {"plantuml-models": ("pumllint", run_pumllint)}


def _since(instance: Path, ref: str) -> list[str]:
    p = subprocess.run(["git", "-C", str(instance), "diff", "--name-only", "-z", "--diff-filter=d", f"{ref}...HEAD", "--", "artefacts/"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError(f"--since {ref}: git diff failed: {p.stderr.strip()}")
    return [f for f in p.stdout.split("\0") if f]


def check(instance: Path, changed: list[str] | None = None, threshold: str = "major", table: dict | None = None) -> dict:
    """The report. changed: paths relative to the instance (or absolute); None: every file under artefacts/."""
    table = table or check_instance.kinds()
    inst = instance.resolve()
    arte = inst / "artefacts"
    rows: list[dict] = []
    targets: dict[str, list[Path]] = {}   # kind -> files to lint

    def add(rel: str, kind: str | None, state: str, why: str, tool: str | None = None) -> dict:
        r = {"file": rel, "kind": kind, "tool": tool, "state": state, "why": why, "findings": []}
        rows.append(r)
        return r

    if changed is None:
        paths = [f for f in check_instance._files(arte)] if arte.is_dir() else []
    else:
        paths = [Path(c) if Path(c).is_absolute() else inst / c for c in changed]
    for p in paths:
        p = p.resolve() if p.exists() else p
        rel = p.relative_to(inst).as_posix() if p.is_relative_to(inst) else str(p)
        if not p.is_relative_to(arte):
            if p.is_relative_to(inst):
                add(rel, None, "skipped", "not under artefacts/: not a document of a kind")
            else:
                add(rel, None, "cannot_run", "outside the instance")
            continue
        parts = p.relative_to(arte).parts
        if len(parts) < 2:
            add(rel, None, "cannot_run", "a file at the top of artefacts/: no kind to read it by")
            continue
        kind = parts[0]
        if kind not in table:
            add(rel, kind, "cannot_run", f"artefacts/{kind}/ is not a kind of instance/kinds.toml")
            continue
        if not p.is_file():
            add(rel, kind, "cannot_run", "does not exist or is not a file")
            continue
        lint = table[kind].get("lint", {})
        tool = lint.get("tool", "")
        if kind in RUNNERS:
            targets.setdefault(kind, []).append(p)
            add(rel, kind, "clean", "", RUNNERS[kind][0])
        elif not tool or tool in NAMES_NONE:
            add(rel, kind, "unchecked", "form unchecked: the programme's table names no linter for this kind", tool or None)
        else:
            add(rel, kind, "unchecked", f"form unchecked: the table names {tool} (gate: {lint.get('gate', '?')}); "
                                        "it does not run in this environment", tool)

    linters = []
    by_file = {r["file"]: r for r in rows}
    for kind, files in targets.items():
        tool, runner = RUNNERS[kind]
        res = runner(files, inst, threshold)
        linters.append({"kind": kind, "tool": tool, "version": res["version"], "files": len(files), "exit": res["rc"], "error": res["error"]})
        rels = [f.relative_to(inst).as_posix() for f in files]
        if res["rc"] == 2:
            for rel in rels:
                by_file[rel].update(state="cannot_run", why=f"{tool}: {res['error']}")
            continue
        for f in res["findings"]:
            rel = Path(f["file"]).relative_to(inst).as_posix() if Path(f["file"]).is_relative_to(inst) else f["file"]
            row = by_file.get(rel)
            if row is None:
                continue   # a finding on a file pumllint read and this check did not name (none today)
            row["findings"].append({k: f[k] for k in ("rule", "severity", "line", "message")})
        for rel in rels:
            row = by_file[rel]
            row["findings"].sort(key=lambda f: (SEVERITIES.index(f["severity"]), f["line"]))
            hits = [f for f in row["findings"] if SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold)]
            if hits:
                row.update(state="findings", why=f"{len(hits)} finding(s) at or above {threshold}")
            else:
                row["why"] = f"no finding at or above {threshold}" + (f" ({len(row['findings'])} below)" if row["findings"] else "")
        if res["rc"] == 1 and not any(by_file[r]["state"] == "findings" for r in rels):
            for rel in rels:   # the linter's own exit is the authority: never pass what it failed
                by_file[rel].update(state="findings", why=f"{tool} exited 1 at --fail-on {threshold}")

    counts = {s: sum(1 for r in rows if r["state"] == s) for s in STATES}
    code = 2 if counts["cannot_run"] else 1 if counts["findings"] else 0
    return {"schema_version": 1, "tool": "knowgov preload check", "instance": str(inst),
            "scope": "changed" if changed is not None else "all", "threshold": threshold,
            "files": rows, "linters": linters, "counts": counts, "exit_code": code,
            "note": "form, not knowledge: this does not replace harness/gate_cli.py"}


def render(rep: dict) -> str:
    out = [f"preload check {rep['instance']} ({rep['scope']} files; fail on {rep['threshold']} and above)"]
    for lt in rep["linters"]:
        out.append(f"linter {lt['tool']} {lt['version'] or '?'} on {lt['kind']}: {lt['files']} file(s), exit {lt['exit']}"
                   + (f": {lt['error']}" if lt["error"] else ""))
    for r in rep["files"]:
        tag = r["state"].upper().replace("_", " ")
        out.append(f"{tag:10s} {r['file']} [{r['kind'] or '-'}]" + (f" {r['tool']}" if r["state"] in ("clean", "findings") else "")
                   + (f": {r['why']}" if r["why"] else ""))
        for f in r["findings"]:
            out.append(f"    {f['line']}: [{f['rule']}/{f['severity']}] {f['message']}")
    c = rep["counts"]
    out.append(", ".join(f"{c[s]} {s.replace('_', ' ')}" for s in STATES) + f"; exit {rep['exit_code']}")
    out.append("form only: this checks each document against its kind's linter, not the knowledge in it (harness/gate_cli.py)")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check each document's form with its kind's linter before the load.")
    ap.add_argument("instance", type=Path)
    ap.add_argument("--changed", nargs="+", metavar="FILE", help="only these files, relative to the instance")
    ap.add_argument("--since", metavar="REF", help="only the files under artefacts/ changed since REF in the instance's git checkout")
    ap.add_argument("--fail-on", choices=SEVERITIES, default="major", help="the severity at or above which a finding exits 1 (default: major)")
    ap.add_argument("-f", "--format", choices=["text", "json"], default="text")
    ap.add_argument("-o", "--output", help="also write the JSON report to this file")
    args = ap.parse_args(argv)
    if not args.instance.is_dir():
        print(f"cannot run: {args.instance} is not a directory", file=sys.stderr)
        return 2
    try:
        table = check_instance.kinds()
    except (OSError, tomllib.TOMLDecodeError, KeyError) as e:
        print(f"cannot run: instance/kinds.toml: {e}", file=sys.stderr)
        return 2
    changed = args.changed
    if args.since:
        try:
            changed = (changed or []) + _since(args.instance, args.since)
        except (OSError, ValueError) as e:
            print(f"cannot run: {e}", file=sys.stderr)
            return 2
    rep = check(args.instance, changed, args.fail_on, table)
    if args.output:
        Path(args.output).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=1) if args.format == "json" else render(rep))
    return rep["exit_code"]


if __name__ == "__main__":
    sys.exit(main())

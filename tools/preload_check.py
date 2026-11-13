"""Check each document's form with its kind's linter before the load (task-0045; doc-0008 §5).

    python tools/preload_check.py <instance> [--changed FILE ...] [--since REF]
                                  [--fail-on blocker|critical|major|minor|info] [-f text|json] [-o FILE]
                                  [--baseline FILE] [--layout]

For each file under the instance's artefacts/<kind>/ (every file, or only those named by
--changed, or only those changed since the git ref REF in the instance's checkout), run the
linter instance/kinds.toml names for the kind, when this environment can run it (RUNNERS, the
kind's lint.runs): pumllint for plantuml-models, the harness's own pin; Spectral for api-contracts
(task-0066); markdownlint (markdownlint-cli2) for specification-prose, gplint for acceptance-scenarios,
bpmnlint for bpmn-process-models and dmnlint for the .dmn files of decision-tables (task-0082). Each
Node linter is KG_<TOOL> (KG_SPECTRAL, KG_MARKDOWNLINT, KG_GPLINT, KG_BPMNLINT, KG_DMNLINT) or the
command on PATH, with the instance's own configuration at its root when it has one, else the one
under instance/ci/. Every other kind's files, a decision table that is not .dmn, and a kind whose
linter is not installed here, are reported *unchecked*, naming the tool (or saying the table names
none): an unchecked file does not fail the check, and it is never passed silently.

After the kinds' linters, step 4's checks (task-0217, decision-0018 point 1; tools/step4_checks.py) read
documents together: pumllint's trace with --features (the linter's own pumllint, 0.35.0 or later; an older
one leaves the trace unchecked, naming 0.35.0), the glossary check and the DMN
gap check. Each finding names its check as its ``tool``; the report's ``checks`` block says whether each ran; a
document its kind's linter left unchecked and a check read is judged by that check alone, and says so. A check
that is installed and fails is cannot-run, exit 2. Provisional on task-0200 (F6): a check's own failure is caught
here and reported; F6's one exit wrapper will map whatever escapes (today a traceback, exit 1) to exit 2.

The programme's gate contract:

    0  every checked file is clean at the threshold (unchecked files are listed, not failed)
    1  a finding at or above --fail-on (default major, pumllint's own) in a checked file; with
       --baseline, only one the baseline does not hold
    2  cannot run: no such instance, a kind folder instance/kinds.toml does not know, a file at
       the top of artefacts/, a named file that does not exist or lies outside the instance, a
       linter that is installed and could not run, a --since git cannot diff, a --baseline that is
       not a report

A --changed file outside artefacts/ (a subject manifest, a register row) is listed as skipped:
it is not a document of a kind. The JSON report (-f json) is pinned by
harness/schemas/preload-report.schema.json through harness/schema_check.py.

--layout (task-0115) also runs tools/check_instance.py on the instance and carries its problems in the
report's ``layout`` block, each with a severity, a kind, the file it concerns and whether it breaks the
layout, so harness/annotate.py shows them beside the lint findings; the exit code stays the lint's alone
(the layout's is check_instance.py's, as instance/ci/preload-check.sh runs it).

--baseline FILE is an earlier report of this command (-o), which the instance's owner chose to
commit: a finding it holds (same file, rule and message, at the same severity or worse; lines are
not compared) is listed as held and does not fail, so an organisation can adopt the check over
documents that already have findings and fail only on a regression (task-0065). The command never
writes the baseline: -o naming it is refused, and moving it on is a commit, not a flag. pumllint's
own ratchet (`pumllint score --baseline`) is not used: it ratchets maturity levels from `score`,
not lint findings, and records the file itself when it is missing.

What it is not: it checks form: each file by its kind's linter, and step 4's checks read documents together
(above). It does not check knowledge;
two well-formed documents that disagree, or a fact nobody wrote down, pass it. That is the
knowgov gate's question (harness/gate_cli.py), after the load; neither replaces the other. The
check reads the instance and never writes to it; the linter runs with the instance as its
working directory, so an instance's own linter configuration applies.
Standard library, plus the linters it runs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_instance  # noqa: E402
import step4_checks  # noqa: E402

sys.path.insert(0, str(ROOT / "harness"))
import schema_check  # noqa: E402

SEVERITIES = ["blocker", "critical", "major", "minor", "info"]   # the contract's ladder, worst first
STATES = ["clean", "findings", "held", "unchecked", "cannot_run", "skipped"]
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
        return {"rc": 2, "missing": True, "version": None, "findings": [], "error": "pumllint is not installed here (pip install pumllint)"}
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


# Spectral's severities (0 error, 1 warn, 2 info, 3 hint) on the contract's ladder: an error is major,
# so the default threshold fails on Spectral's own errors and lists its warnings.
SPECTRAL_SEVERITY = {0: "major", 1: "minor", 2: "info", 3: "info"}
SPECTRAL_RULESETS = (".spectral.yaml", ".spectral.yml", ".spectral.json")


def spectral_cmd() -> list[str] | None:
    """The command that runs Spectral here (KG_SPECTRAL, else spectral on PATH), or None."""
    exe = os.environ.get("KG_SPECTRAL") or shutil.which("spectral")
    return [exe] if exe and Path(exe).exists() else None


def run_spectral(files: list[Path], cwd: Path, threshold: str) -> dict:
    """Spectral over API contracts (task-0066), with the instance's own ruleset (.spectral.yaml at its
    root) when it has one, else instance/ci/spectral.yaml (spectral:oas and spectral:asyncapi).
    rc is 1 when a finding reaches the threshold on the contract's ladder, 0 otherwise, 2 when it
    cannot run; Spectral's own exit only says whether it ran."""
    cmd = spectral_cmd()
    if cmd is None:
        return {"rc": 2, "missing": True, "version": None, "findings": [],
                "error": "Spectral is not installed here (npm install -g @stoplight/spectral-cli)"}
    ver = subprocess.run(cmd + ["--version"], cwd=cwd, capture_output=True, text=True)
    version = ver.stdout.strip().split()[-1] if ver.returncode == 0 and ver.stdout.strip() else None
    ruleset = next((cwd / r for r in SPECTRAL_RULESETS if (cwd / r).is_file()), ROOT / "instance" / "ci" / "spectral.yaml")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "report.json"
        p = subprocess.run(cmd + ["lint", "-r", str(ruleset), "-f", "json", "-o", str(out), "-q", "--fail-severity", "hint"]
                           + [str(f) for f in files], cwd=cwd, capture_output=True, text=True)
        if p.returncode not in (0, 1):
            return {"rc": 2, "version": version, "findings": [], "error": (p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}"}
        try:
            raw = json.loads(out.read_text(encoding="utf-8") or "[]")
        except (OSError, ValueError) as e:
            return {"rc": 2, "version": version, "findings": [], "error": f"no readable report: {e}"}
    findings = [{"file": str(Path(x["source"]).resolve()), "rule": x.get("code", ""), "severity": SPECTRAL_SEVERITY.get(x.get("severity"), "info"),
                 "line": (x.get("range") or {}).get("start", {}).get("line", -1) + 1, "message": x.get("message", "")} for x in raw]
    hit = any(SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold) for f in findings)
    return {"rc": 1 if hit else 0, "version": version, "findings": findings, "error": None}


NAMED = ("KG_SPECTRAL", "KG_MARKDOWNLINT", "KG_GPLINT", "KG_BPMNLINT", "KG_DMNLINT")   # a linter named by its setting


def unrunnable() -> list[str]:
    """The linter settings that name something this check cannot run (task-0267, N6; as decision-0033 choice 5 has
    it for a named register): set, but not an executable file. Unset keeps PATH's answer and "not installed"."""
    out = []
    for var in NAMED:
        v = os.environ.get(var)
        if v and not (Path(v).is_file() and os.access(v, os.X_OK)):
            out.append(f"{var}={v}")
    return out


def _exe(var: str, name: str) -> list[str] | None:
    """The command for a Node linter: the variable's path (an install outside PATH), else name on PATH, else None."""
    exe = os.environ.get(var) or shutil.which(name)
    return [exe] if exe and Path(exe).exists() else None


def _rel(path: str, cwd: Path) -> str:
    """A path as the linter printed it, absolute, so findings land on the file this check named."""
    return str((cwd / path).resolve())


def _on_ladder(findings: list[dict], threshold: str) -> int:
    return 1 if any(SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold) for f in findings) else 0


# markdownlint's error is major, its warning minor (a rule an instance sets to warning lists, never fails)
LEVEL = {"error": "major", "warning": "minor"}
MARKDOWNLINT_CONFIGS = tuple(f".markdownlint{s}" for s in ("-cli2.jsonc", "-cli2.yaml", "-cli2.cjs", "-cli2.mjs",
                                                             ".jsonc", ".json", ".yaml", ".yml", ".cjs", ".mjs"))
MARKDOWNLINT_LINE = re.compile(r"^(?P<file>.+?):(?P<line>\d+)(?::\d+)? (?P<sev>error|warning) (?P<rule>\S+) (?P<msg>.*)$")


def markdownlint_cmd() -> list[str] | None:
    """markdownlint-cli2 here (KG_MARKDOWNLINT, else markdownlint-cli2 on PATH), or None."""
    return _exe("KG_MARKDOWNLINT", "markdownlint-cli2")


def run_markdownlint(files: list[Path], cwd: Path, threshold: str) -> dict:
    """markdownlint (markdownlint-cli2) over specification prose (task-0082): the instance's own configuration
    at its root when it has one (markdownlint-cli2 reads it from the working directory), else
    instance/ci/markdownlint.jsonc, markdownlint's defaults less line length and table column style. Its own
    exit 0/1 says whether it ran; 2 or anything else is cannot-run."""
    cmd = markdownlint_cmd()
    if cmd is None:
        return {"rc": 2, "missing": True, "version": None, "findings": [],
                "error": "markdownlint is not installed here (npm install -g markdownlint-cli2)"}
    env = {**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0"}
    ver = subprocess.run(cmd + ["--help"], cwd=cwd, capture_output=True, text=True, env=env)
    m = re.search(r"markdownlint-cli2 v(\S+)", ver.stdout + ver.stderr)
    version = m.group(1) if m else None
    config = [] if any((cwd / c).is_file() for c in MARKDOWNLINT_CONFIGS) else ["--config", str(ROOT / "instance" / "ci" / "markdownlint.jsonc")]
    # ':' makes each path literal, never a glob
    p = subprocess.run(cmd + config + [":" + f.relative_to(cwd).as_posix() for f in files], cwd=cwd, capture_output=True, text=True, env=env)
    if p.returncode not in (0, 1):
        return {"rc": 2, "version": version, "findings": [], "error": (p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}"}
    findings = []
    for line in (p.stdout + "\n" + p.stderr).splitlines():
        x = MARKDOWNLINT_LINE.match(line)
        if x:
            findings.append({"file": _rel(x["file"], cwd), "rule": x["rule"].split("/")[0], "severity": LEVEL[x["sev"]],
                             "line": int(x["line"]), "message": f"{x['rule']} {x['msg']}"})
    return {"rc": _on_ladder(findings, threshold), "version": version, "findings": findings, "error": None}


# gplint's levels: 2 error (major), 1 warn (minor)
GPLINT_LEVEL = {2: "major", 1: "minor"}


def gplint_cmd() -> list[str] | None:
    """gplint here (KG_GPLINT, else gplint on PATH), or None."""
    return _exe("KG_GPLINT", "gplint")


def run_gplint(files: list[Path], cwd: Path, threshold: str) -> dict:
    """gplint over Gherkin (task-0082), with the instance's .gplintrc at its root when it has one, else
    instance/ci/gplintrc (the structural rules: names, duplicates, empty files and backgrounds, outlines
    without examples, unused variables, keyword order). A file gplint cannot parse is its own error."""
    cmd = gplint_cmd()
    if cmd is None:
        return {"rc": 2, "missing": True, "version": None, "findings": [], "error": "gplint is not installed here (npm install -g gplint)"}
    env = {**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0"}
    ver = subprocess.run(cmd + ["--version"], cwd=cwd, capture_output=True, text=True, env=env)
    version = ver.stdout.strip().split()[-1] if ver.returncode == 0 and ver.stdout.strip() else None
    config = cwd / ".gplintrc" if (cwd / ".gplintrc").is_file() else ROOT / "instance" / "ci" / "gplintrc"
    p = subprocess.run(cmd + ["-c", str(config), "-f", "json"] + [str(f) for f in files], cwd=cwd, capture_output=True, text=True, env=env)
    try:
        raw = json.loads(p.stdout)   # gplint exits 1 on a finding and on a bad configuration alike: the report decides
    except ValueError:
        return {"rc": 2, "version": version, "findings": [], "error": (p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}"}
    if p.returncode not in (0, 1):
        return {"rc": 2, "version": version, "findings": [], "error": (p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}"}
    prefix = str(cwd.resolve()) + os.sep   # a message naming a file names it relative to the instance, so a baseline holds anywhere
    findings = [{"file": str(Path(r["filePath"]).resolve()), "rule": e.get("rule", ""), "severity": GPLINT_LEVEL.get(e.get("level"), "info"),
                 "line": e.get("line") or 0, "message": e.get("message", "").replace(prefix, "")}
                for r in raw for e in r.get("errors", [])]
    return {"rc": _on_ladder(findings, threshold), "version": version, "findings": findings, "error": None}


# bpmnlint's and dmnlint's text report (neither writes JSON): a line naming the file, then one per
# finding, `  <element id>  <error|warning>  <message>  <rule>`, columns two spaces or more apart; a
# parse error has no element and no rule. The element id leads the message: models have no lines.
BPMN_IO_LINE = re.compile(r"^\s+(?:(?P<id>\S+)\s+)?(?P<sev>error|warning)\s{2,}(?P<msg>.+?)(?:\s{2,}(?P<rule>[a-z0-9/:@.-]+))?\s*$")


def _run_bpmn_io(tool: str, cmd: list[str] | None, rc_name: str, files: list[Path], cwd: Path, threshold: str) -> dict:
    """bpmnlint or dmnlint, with the instance's .bpmnlintrc (.dmnlintrc) at its root when it has one, else
    the one under instance/ci/ (the tool's recommended rules). Exit 1 with no report, or anything but 0
    and 1, is cannot-run."""
    if cmd is None:
        return {"rc": 2, "missing": True, "version": None, "findings": [],
                "error": f"{tool} is not installed here (npm install -g {tool})"}
    env = {**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0"}
    ver = subprocess.run(cmd + ["--version"], cwd=cwd, capture_output=True, text=True, env=env)
    version = ver.stdout.strip().split()[-1] if ver.returncode == 0 and ver.stdout.strip() else None
    config = cwd / f".{rc_name}" if (cwd / f".{rc_name}").is_file() else ROOT / "instance" / "ci" / rc_name
    p = subprocess.run(cmd + ["-c", str(config)] + [str(f) for f in files], cwd=cwd, capture_output=True, text=True, env=env)
    if p.returncode not in (0, 1) or (p.returncode == 1 and "problem" not in p.stdout):
        return {"rc": 2, "version": version, "findings": [], "error": (p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}"}
    findings, current = [], None
    for line in p.stdout.splitlines():
        if line and not line[0].isspace() and not line.startswith("✖"):
            current = _rel(line.strip(), cwd)
            continue
        x = BPMN_IO_LINE.match(line)
        if x and current:
            msg = x["msg"].strip()
            findings.append({"file": current, "rule": x["rule"] or ("parse-error" if msg.startswith("Parse error") else ""),
                             "severity": LEVEL[x["sev"]], "line": 0, "message": f"{x['id']}: {msg}" if x["id"] else msg})
    return {"rc": _on_ladder(findings, threshold), "version": version, "findings": findings, "error": None}


def bpmnlint_cmd() -> list[str] | None:
    """bpmnlint here (KG_BPMNLINT, else bpmnlint on PATH), or None."""
    return _exe("KG_BPMNLINT", "bpmnlint")


def run_bpmnlint(files: list[Path], cwd: Path, threshold: str) -> dict:
    """bpmnlint over BPMN process models (task-0082): its errors major, its warnings minor."""
    return _run_bpmn_io("bpmnlint", bpmnlint_cmd(), "bpmnlintrc", files, cwd, threshold)


def dmnlint_cmd() -> list[str] | None:
    """dmnlint here (KG_DMNLINT, else dmnlint on PATH), or None."""
    return _exe("KG_DMNLINT", "dmnlint")


def run_dmnlint(files: list[Path], cwd: Path, threshold: str) -> dict:
    """dmnlint over DMN decision tables (task-0082), .dmn files only (SUFFIXES): its errors major."""
    return _run_bpmn_io("dmnlint", dmnlint_cmd(), "dmnlintrc", files, cwd, threshold)


# kind folder -> (the tool's name, the runner): the linters this repository's environment can run.
# The tool is the kind's lint.runs in instance/kinds.toml, one of the tools its lint.tool names;
# tests/test_preload.py holds the two equal. A runner whose tool is not installed leaves the kind's
# files unchecked, naming it (task-0066), never passed and never cannot-run.
RUNNERS = {"plantuml-models": ("pumllint", run_pumllint), "api-contracts": ("Spectral", run_spectral),
           "specification-prose": ("markdownlint", run_markdownlint), "acceptance-scenarios": ("gplint", run_gplint),
           "bpmn-process-models": ("bpmnlint", run_bpmnlint), "decision-tables": ("dmnlint", run_dmnlint)}
# kind folder -> the suffixes its runner reads; a file of the kind with another suffix stays unchecked
# (a decision table written as Markdown is not DMN XML: dmnlint cannot read it, task-0082)
SUFFIXES = {"decision-tables": (".dmn",)}


def _refused(args) -> str | None:
    """Why the check cannot run on what it was given, before it reads anything (task-0267); None when it can."""
    if not args.instance.is_dir():
        return f"{args.instance} is not a directory"
    named = unrunnable()
    if named:
        return f"{', '.join(named)}: the linter named there is not an executable file; unset it to use PATH's"
    if not (args.instance / "subjects").is_dir():   # refused whether or not --layout is given
        return f"{args.instance} is not an instance: it holds no subjects/ (instance/README.md)"
    outside = _outside(args.instance, args.changed or [])
    if outside:   # an absolute path and one escaping by .. are the same refusal, each named
        return f"--changed {', '.join(outside)}: outside the instance {args.instance.resolve()}"
    return None


def _outside(instance: Path, changed: list[str]) -> list[str]:
    """The --changed paths that name nothing inside the instance, absolute or relative alike: each joined to the
    instance (an absolute one stays itself), its .. and symlinks resolved, then held to the instance's own root."""
    inst = instance.resolve()
    return [c for c in changed if not (inst / c).resolve().is_relative_to(inst)]


def _since(instance: Path, ref: str) -> list[str]:
    if ref.startswith("-"):   # task-0267 (N2): a ref, never an option git would act on
        raise ValueError(f"--since {ref}: not a git ref: it starts with '-'")
    p = subprocess.run(["git", "-C", str(instance), "-c", "core.quotepath=off", "diff", "--name-only", "-z", "--diff-filter=d",
                        "--end-of-options", f"{ref}...HEAD", "--", "artefacts/"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError(f"--since {ref}: git diff failed: {p.stderr.strip()}")
    return [f for f in p.stdout.split("\0") if f]


def _baseline_index(baseline: dict) -> dict[tuple, list[int]]:
    """(file, rule, message) -> the severities (ladder index) the baseline holds for it, one per finding."""
    held: dict[tuple, list[int]] = {}
    for r in baseline.get("files", []):
        for f in r.get("findings", []):
            held.setdefault((r["file"], f["rule"], f["message"]), []).append(SEVERITIES.index(f["severity"]))
    return held


def delta(previous: dict, rep: dict, name: str = "") -> dict:
    """What a re-lint changed (task-0216, decision-0018 point 5): each finding of ``rep`` against ``previous``, an
    earlier report of this command, matched as the baseline matches (file, tool, rule, message; lines are not
    compared). Comparable only when every tool that ran in both ran at the same version: a newer linter's
    findings are not a document's change. A finding gone from a file whose bytes changed is a slip, mended by a
    new version; gone from bytes unchanged, the rule no longer fires on them."""
    def ran(r):
        return {**{lt["tool"]: lt.get("version") for lt in r.get("linters", []) if lt.get("version")},
                **{c["check"]: c["version"] for c in r.get("checks", []) if c.get("version")}}
    a, b = ran(previous), ran(rep)
    moved = sorted(t for t in set(a) & set(b) if a[t] != b[t])
    out = {"previous": name, "comparable": not moved,
           "why": None if not moved else "tool versions differ: " + ", ".join(f"{t} {a[t]} -> {b[t]}" for t in moved),
           "new": [], "gone": [], "kept": 0}
    if moved:
        return out

    def index(r):
        found = {}
        for row in r.get("files", []):
            for f in row.get("findings", []):
                found.setdefault((row["file"], f.get("tool") or row.get("tool"), f["rule"], f["message"]), []).append(f)
        return found
    before, after = index(previous), index(rep)
    digest = {r["file"]: r.get("sha256") for r in rep.get("files", [])}
    was = {r["file"]: r.get("sha256") for r in previous.get("files", [])}
    for k in sorted(set(before) | set(after), key=lambda k: tuple(str(x) for x in k)):
        n0, n1 = len(before.get(k, [])), len(after.get(k, []))
        out["kept"] += min(n0, n1)
        row = {"file": k[0], "tool": k[1], "rule": k[2], "message": k[3]}
        for f in after.get(k, [])[n0:]:
            out["new"].append({**row, "severity": f["severity"], "line": f["line"]})
        for f in before.get(k, [])[n1:]:
            out["gone"].append({**row, "severity": f["severity"], "line": f["line"],
                                "slip": bool(was.get(k[0]) and digest.get(k[0]) and was[k[0]] != digest[k[0]])})
    return out


def check(instance: Path, changed: list[str] | None = None, threshold: str = "major", table: dict | None = None,
          baseline: dict | None = None, baseline_name: str = "") -> dict:
    """The report. changed: paths relative to the instance (or absolute); None: every file under artefacts/.
    baseline: an earlier report of this command (-o), committed by the instance's owner; a finding it
    holds (same file, rule and message, at the same severity or worse) is listed as held and does not
    fail. Lines are not compared: an edit above a finding moves it without making it new."""
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
        if kind in RUNNERS and kind in SUFFIXES and p.suffix.lower() not in SUFFIXES[kind]:
            add(rel, kind, "unchecked", f"form unchecked: {RUNNERS[kind][0]} reads {', '.join(SUFFIXES[kind])} files only; "
                                        f"the table names no linter for a {p.suffix or 'suffixless'} file of this kind", tool)
        elif kind in RUNNERS:
            targets.setdefault(kind, []).append(p)
            add(rel, kind, "clean", "", RUNNERS[kind][0])
        elif not tool or tool in NAMES_NONE:
            add(rel, kind, "unchecked", "form unchecked: the programme's table names no linter for this kind", tool or None)
        else:
            add(rel, kind, "unchecked", f"form unchecked: the table names {tool} (gate: {lint.get('gate', '?')}); "
                                        "it does not run in this environment", tool)

    linters = []
    by_file = {r["file"]: r for r in rows}
    held = _baseline_index(baseline) if baseline is not None else None
    settled: list[str] = []          # the rows a linter or a check judged, settled once every finding is in
    failed: set[str] = set()
    failed_by: dict[str, str] = {}
    failed_checks: list[str] = []
    only: dict[str, str] = {}        # a row no linter of its kind judged, judged by a check: why its linter did not
    for kind, files in targets.items():
        tool, runner = RUNNERS[kind]
        res = runner(files, inst, threshold)
        linters.append({"kind": kind, "tool": tool, "version": res["version"], "files": len(files), "exit": res["rc"], "error": res["error"]})
        rels = [f.relative_to(inst).as_posix() for f in files]
        if res.get("missing"):
            for rel in rels:
                by_file[rel].update(state="unchecked", tool=tool, why=f"form unchecked: {res['error']}")
            continue
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
        settled.extend(rels)
        parsed = any(SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold) for r in rels for f in by_file[r]["findings"])
        if res["rc"] == 1 and not parsed:
            failed.update(rels)   # the linter's own exit is the authority: never pass what it failed
            failed_by.update({rel: tool for rel in rels})

    checks = []
    for name, (reads, runner) in step4_checks.CHECKS.items():   # step 4's checks, across the kinds they read (task-0217)
        try:
            res = runner(inst)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:   # task-0200 F6 maps the rest to exit 2
            res = {"state": "cannot_run", "why": f"{name}: {type(e).__name__}: {e}", "version": None, "files": 0, "findings": []}
        if res["state"] == "ran":
            read = set(res.get("read", []))
            for r in rows:   # a document the check read and its kind's linter left unchecked is judged by the check alone
                if r["file"] in read and r["state"] == "unchecked":
                    only[r["file"]] = f"judged by {name} alone; {r['why']}"
                    r.update(tool=name)   # task-0312 C4-1: its kind's linter never ran, so it stays unchecked unless a finding lands
                    settled.append(r["file"])
        landed = 0
        for f in res["findings"]:
            row = by_file.get(f["file"])
            if row is None or not _takes_findings(row, only):
                continue   # a document outside this run's scope (--changed, --since), or one no tool could read
            row["findings"].append({**{k: f[k] for k in ("rule", "severity", "line", "message")}, "tool": name})
            settled.append(f["file"])
            landed += 1
        checks.append({"check": name, "reads": list(reads), "state": res["state"], "why": res["why"], "version": res["version"],
                       "files": res["files"], "findings": landed})
        if res["state"] == "cannot_run":
            failed_checks.append(f"{name}: {res['why']}")

    for rel in dict.fromkeys(settled):
        row = by_file[rel]
        row["findings"].sort(key=lambda f: (SEVERITIES.index(f["severity"]), f["line"]))
        if held is not None:
            for f in row["findings"]:   # worst first, so the worst finding claims the worst entry the baseline holds
                entries = held.get((rel, f["rule"], f["message"]), [])
                match = next((s for s in sorted(entries) if s <= SEVERITIES.index(f["severity"])), None)
                f["held"] = match is not None
                if match is not None:
                    entries.remove(match)
        hits = [f for f in row["findings"] if SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold)]
        new = [f for f in hits if not f.get("held")]
        if new:
            row.update(state="findings", why=f"{len(new)} finding(s) at or above {threshold}"
                       + (f" not in the baseline ({len(hits) - len(new)} held)" if held is not None else ""))
        elif hits:
            row.update(state="held", why=f"{len(hits)} finding(s) at or above {threshold}, every one held by the baseline")
        else:
            row["why"] = f"no finding at or above {threshold}" + (f" ({len(row['findings'])} below)" if row["findings"] else "")
        if rel in failed:
            row.update(state="findings", why=f"{failed_by[rel]} exited 1 at --fail-on {threshold}")
        if rel in only:
            row["why"] = f"{row['why']} ({only[rel]})"

    for r in rows:   # the bytes judged, so the load can tell a verdict from a later edit (task-0064)
        f = inst / r["file"]
        if r["kind"] and f.is_file():
            r["sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
    counts = {s: sum(1 for r in rows if r["state"] == s) for s in STATES}
    code = 2 if counts["cannot_run"] or failed_checks else 1 if counts["findings"] else 0
    out = {"schema_version": 1, "tool": "knowgov preload check", "instance": str(inst),
           "scope": "changed" if changed is not None else "all", "threshold": threshold,
           "files": rows, "linters": linters, "checks": checks, "counts": counts, "exit_code": code,
           "note": "form, not knowledge: this does not replace harness/gate_cli.py"}
    if baseline is not None:
        fs = [f for r in rows for f in r["findings"] if SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold)]
        out["baseline"] = {"file": baseline_name, "held": sum(1 for f in fs if f.get("held")),
                           "new": sum(1 for f in fs if not f.get("held"))}
    return out


def _takes_findings(row: dict, only: dict) -> bool:
    """A row a linter judged takes a check's findings; so does one its linter never ran on and a check judged alone
    (task-0312 C4-1: it stays unchecked unless a finding lands)."""
    return row["state"] in ("clean", "findings", "held") or (row["state"] == "unchecked" and row["file"] in only)


def _where(inst: Path, text: str) -> str | None:
    """The file a layout error names by its leading path (``subjects/x: ...``, ``artefacts/k/``,
    ``code_map.toml: ...``): that file, or a subject root's subject.toml; None when it names no file."""
    head = text.split(": ", 1)[0].strip().rstrip("/")
    if not head or head.startswith("/") or ".." in Path(head).parts:
        return None
    p = inst / head
    if p.is_file():
        return head
    if (p / "subject.toml").is_file():
        return f"{head}/subject.toml"
    return None


def layout(instance: Path, table: dict | None = None) -> dict:
    """The layout check's problems (tools/check_instance.py, task-0115) for the pre-load report: each
    with a severity on the report's ladder, a kind, the file it concerns relative to the instance (or
    None), a message, and ``fails``: whether it breaks the layout (check_instance.py's exit 1). A layout
    error is a blocker that fails; the rest are what check_instance.py lists to read, never failing:
    a subject check's warning (minor) or note (info), an absent document (minor), an unread one (info),
    an unmapped code file (minor), an unmatched code-map row (info)."""
    inst = instance.resolve()
    rep = check_instance.check(inst, table)
    out = []

    def add(severity, kind, path, message, fails=False):
        out.append({"severity": severity, "kind": kind, "path": path, "message": message, "fails": fails})
    for e in rep["errors"]:
        add("blocker", "error", _where(inst, e), e, True)
    for sub in rep["subjects"]:
        manifest = f"{sub['root']}/subject.toml"
        chk = sub.get("check") or {}
        for f in chk.get("findings", []):
            if f["level"] == "warning":
                add("minor", f"warning:{f['rule']}", manifest, f"{f['where']}: {f['message']}; fix: {f['fix']}")
        for n in chk.get("notes", []):
            add("info", "note", manifest, f"{n['where']}: {n['message']}")
    paths = {(s["id"], a["key"]): a["path"] for s in rep["subjects"] for a in s["artefacts"]}
    for a in rep["absent"]:
        path = paths.get((a["subject"], a["key"])) if a["subject"] else a["key"]
        add("minor", "absent", path if path and (inst / path).is_file() else None,
            f"{a['key']} [{a['kind']}]: {a['why']}" + (f" (subject {a['subject']})" if a["subject"] else ""))
    for u in rep["unread"]:
        add("info", "unread", u["file"], f"{u['file']} [{u['kind']}]: no subject names it, so nothing loads it")
    cm = rep.get("code_map")
    if cm:
        root = cm["root"] if cm["root"] not in (None, ".") else ""
        for f in cm["unmapped"]:
            add("minor", "unmapped", f"{root}/{f}" if root else f, f"{f}: no row of {check_instance.CODE_MAP} names its application")
        for g in cm["unmatched"]:
            add("info", "unmatched", check_instance.CODE_MAP, f"{g}: no code file matches this row's glob")
    return {"holds": not rep["errors"], "exit_code": 1 if rep["errors"] else 0, "problems": out}


def render(rep: dict) -> str:
    out = [f"preload check {rep['instance']} ({rep['scope']} files; fail on {rep['threshold']} and above)"]
    for lt in rep["linters"]:
        out.append(f"linter {lt['tool']} {lt['version'] or '?'} on {lt['kind']}: {lt['files']} file(s), exit {lt['exit']}"
                   + (f": {lt['error']}" if lt["error"] else ""))
    for r in rep["files"]:
        tag = r["state"].upper().replace("_", " ")
        out.append(f"{tag:10s} {r['file']} [{r['kind'] or '-'}]" + (f" {r['tool']}" if r["state"] in ("clean", "findings", "held") else "")
                   + (f": {r['why']}" if r["why"] else ""))
        for f in r["findings"]:
            out.append(f"    {f['line']}: [{f['rule']}/{f['severity']}] {f['message']}" + (" (held by the baseline)" if f.get("held") else ""))
    lay = rep.get("layout")
    if lay is not None:   # the layout check prints its own report; here, what the pre-load report carries (task-0115)
        fails = sum(1 for x in lay["problems"] if x["fails"])
        out.append(f"layout: {'holds' if lay['holds'] else 'does not hold'}; {len(lay['problems'])} problem(s) in the report, {fails} failing")
    c = rep["counts"]
    if rep.get("baseline"):
        b = rep["baseline"]
        out.append(f"baseline {b['file']}: {b['held']} finding(s) at or above {rep['threshold']} held, {b['new']} new")
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
    ap.add_argument("-o", "--output", help="also write the JSON report to this file (commit one as a baseline: the owner's decision)")
    ap.add_argument("--baseline", metavar="FILE", help="an earlier report (-o): exit 1 only on a finding it does not hold; never written by this command")
    ap.add_argument("--previous", metavar="FILE", help="an earlier report (-o): also report the delta, each finding new, gone (a slip "
                                                       "when its file's bytes changed) or kept, at the same tool versions only (task-0216)")
    ap.add_argument("--layout", action="store_true", help="also carry tools/check_instance.py's layout problems in the report "
                                                           "(its layout block, for annotation; task-0115); the exit code stays the lint's")
    args = ap.parse_args(argv)
    refused = _refused(args)
    if refused:
        print(f"cannot run: {refused}", file=sys.stderr)
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
    baseline = None
    if args.baseline:
        if args.output and Path(args.output).resolve() == Path(args.baseline).resolve():
            print("cannot run: -o names the baseline; the check never writes its own baseline", file=sys.stderr)
            return 2
        try:
            baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
            errors = schema_check.validate(baseline, schema_check.load("preload-report"))
        except (OSError, ValueError) as e:
            errors = [str(e)]
        if errors:
            print(f"cannot run: --baseline {args.baseline} is not a preload report: {errors[0]}", file=sys.stderr)
            return 2
    rep = check(args.instance, changed, args.fail_on, table, baseline, args.baseline or "")
    if args.previous:
        try:
            prev = json.loads(Path(args.previous).read_text(encoding="utf-8"))
            errors = schema_check.validate(prev, schema_check.load("preload-report"))
        except (OSError, ValueError) as e:
            errors = [str(e)]
        if errors:
            print(f"cannot run: --previous {args.previous} is not a preload report: {errors[0]}", file=sys.stderr)
            return 2
        rep["delta"] = delta(prev, rep, args.previous)
    if args.layout:
        rep["layout"] = layout(args.instance, table)
    if args.output:   # an unwritable -o is a failure to run, exit 2, never 1 (task-0228, doc-0030 F6)
        try:
            Path(args.output).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        except OSError as e:
            print(f"cannot run: -o {args.output} cannot be written ({e.__class__.__name__}: {e.strerror or e})", file=sys.stderr)
            return 2
    print(json.dumps(rep, indent=1) if args.format == "json" else render(rep))
    return rep["exit_code"]


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    import cli_exit    # task-0228: anything else that escapes main is a failure to run, exit 2 (doc-0030 F6)
    sys.exit(_outcomes.run(lambda: cli_exit.run(main, "preload check")))

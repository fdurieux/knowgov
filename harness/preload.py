"""The pre-load check's verdict, read at the load (task-0064; doc-0008 §5).

tools/preload_check.py runs on an instance's pull request and leaves a report (-o). The load never
re-runs a linter: the merge is the check. It reads the report the instance's CI left and records,
on each document version it loads, what that report says about those exact bytes: the tool, its
version, the state (clean, findings, held) and the digest judged. A version the report does not
cover, or whose bytes differ from the digest judged, is recorded as unchecked, never as clean.

The report is ``KG_PRELOAD_REPORT`` when set (a path), else ``preload-report.json`` at the root of
the instance the subject sits in (``<instance>/subjects/<id>/``), when that file exists. With no
report nothing is recorded, and the load's output carries no ``preload`` key, so a run without one
reads exactly as before. Standard library, plus the harness's schema checker.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import hashlib

from kitio import sha256

DEFAULT_NAME = "preload-report.json"
JUDGED = {"clean", "findings", "held"}     # states a linter gave; anything else is unchecked
NOT_CLEAN = {"unchecked", "findings", "held"}


def instance_root(subject) -> Path | None:
    """The instance a subject root sits in (``<instance>/subjects/<id>``), or None."""
    root = Path(subject.root).resolve()
    inst = root.parent.parent
    return inst if root.parent.name == "subjects" and (inst / "artefacts").is_dir() else None


def report_path(subject) -> Path | None:
    env = os.environ.get("KG_PRELOAD_REPORT")
    if env:
        return Path(env)
    inst = instance_root(subject)
    p = inst / DEFAULT_NAME if inst else None
    return p if p and p.is_file() else None


def read_report(path: Path) -> dict:
    """The report, held to harness/schemas/preload-report.schema.json; raises ValueError otherwise."""
    import schema_check
    rep = json.loads(path.read_text(encoding="utf-8"))
    errors = schema_check.validate(rep, schema_check.load("preload-report"))
    if errors:
        raise ValueError(f"{path}: not a preload report: {errors[0]}")
    return rep


def verdicts(subject, kit: dict[str, str], keys, report: dict, name: str) -> dict[str, dict]:
    """artefact key -> its verdict, for each of ``keys`` the kit holds. The report's rows are matched
    by the document's path relative to the instance (the subject's own instance, else the one the
    report names); a directory artefact is never one file the linter judged, so it stays unchecked."""
    inst = instance_root(subject) or Path(report.get("instance", "/"))
    rows = {r["file"]: r for r in report.get("files", [])}
    tools = {lt["tool"]: lt.get("version") for lt in report.get("linters", [])}
    paths = {a["key"]: (Path(subject.root) / a["path"]).resolve() for a in subject.artefacts if a.get("path")}
    out = {}
    for key in keys:
        if key not in kit:
            continue
        p = paths.get(key)
        rel = p.relative_to(inst).as_posix() if p is not None and p.is_relative_to(inst) else None
        row = rows.get(rel) if rel else None
        v = {"state": "unchecked", "tool": None, "tool_version": None, "digest": None, "report": name, "file": rel}
        if row is None:
            v["why"] = "the report does not cover this document" if rel else "the document is not in the instance the report covers"
        elif row["state"] not in JUDGED:
            v.update(tool=row.get("tool"), why=f"the report left it {row['state'].replace('_', ' ')}: {row.get('why', '')}".rstrip(": "))
        elif not row.get("sha256"):
            v.update(tool=row.get("tool"), why="the report holds no digest of the bytes it judged")
        elif row["sha256"] != sha256(kit[key]):
            v.update(tool=row.get("tool"), digest=row["sha256"], why="the bytes loaded differ from the bytes the report judged")
        else:
            v.update(state=row["state"], tool=row.get("tool"), tool_version=tools.get(row.get("tool")), digest=row["sha256"],
                     why=row.get("why", ""), findings=list(row.get("findings") or []))
        out[key] = v
    return out


def lint_gaps(artefact: str, version: str, v: dict) -> list[dict]:
    """Each finding the report gave a version's exact bytes, as the store keeps it (task-0216, decision-0018
    point 5): one gap per finding, its id stable across stores and loads (the document, its version, the tool,
    rule, line and message, never the store's order), ``held`` when the baseline holds it. A version left
    unchecked, or whose bytes differ from those judged, holds none: there is no finding of its bytes."""
    out = []
    for f in v.get("findings") or []:
        text = f"{v.get('tool')} {f['rule']} ({f['severity']}) at {v.get('file')}:{f['line']}: {f['message']}"
        fp = hashlib.sha256(f"{v.get('tool')}|{f['rule']}|{f['line']}|{f['message']}".encode("utf-8")).hexdigest()[:16]
        out.append({"id": f"lint:{artefact}@{version}:{fp}", "artefact": artefact, "version": version, "file": v.get("file"),
                    "tool": v.get("tool"), "tool_version": v.get("tool_version"), "rule": f["rule"], "severity": f["severity"],
                    "line": int(f["line"]), "message": f["message"], "held": bool(f.get("held")), "text": text,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
    return out

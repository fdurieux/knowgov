"""SPIKE (task-0151, doc-0021 S3, G4): never merged. One reader for several subjects, by two of the
three designs measured; the third, (c), is the subject as a value through the harness and is not
prototyped here (its cost is counted from the module-level ``SUBJECT`` bindings instead).

The subject is named by id and resolved under ``KG_SUBJECTS`` (a root's directory name, as the page
resolves ``?subject=``), never by a path; with no id the process's own ``KG_SUBJECT`` answers, so a
client that names none sees no change.

(a) ``via_child``: one child process per call, ``harness/mcp_child.py TOOL ARGS`` with ``KG_SUBJECT``
    set to the resolved root: the page's pattern.
(b) ``Pool``: one long-lived child per subject (``harness/mcp_server.py`` on stdio with that
    ``KG_SUBJECT``), started on its first call and kept; each call is one JSON-RPC round trip.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent


class UnknownSubject(ValueError):
    pass


def roots() -> dict[str, Path]:
    """id -> root for every subject under KG_SUBJECTS (comma or path-separator separated; a root, or a
    directory of roots), as the page lists them."""
    raw = os.environ.get("KG_SUBJECTS") or str(HERE.parent / "subjects")
    out: dict[str, Path] = {}
    for part in (p for chunk in raw.split(",") for p in chunk.split(os.pathsep)):
        p = Path(part.strip())
        if not part.strip() or not p.is_dir():
            continue
        cands = [p] if (p / "subject.toml").is_file() else sorted(c for c in p.iterdir() if (c / "subject.toml").is_file())
        for c in cands:
            out.setdefault(c.name, c.resolve())
    return out


def resolve(subject_id: str | None) -> Path | None:
    """None for the process's own subject (no id given); else the root of that id, never a path."""
    if subject_id is None:
        return None
    if "/" in subject_id or "\\" in subject_id or subject_id.startswith("."):
        raise UnknownSubject(f"subject is an id under KG_SUBJECTS, not a path: {subject_id!r}")
    r = roots()
    if subject_id not in r:
        raise UnknownSubject(f"no subject {subject_id!r} under KG_SUBJECTS; known: {sorted(r)}")
    return r[subject_id]


def _env(root: Path) -> dict:
    return {**os.environ, "KG_SUBJECT": str(root)}


def via_child(root: Path, tool: str, args: dict, timeout: float = 120) -> dict:
    """(a): the tool's result from a fresh child process for that subject."""
    p = subprocess.run([sys.executable, str(HERE / "mcp_child.py"), tool, json.dumps(args)], capture_output=True,
                       text=True, env=_env(root), timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"child for {root.name}: exit {p.returncode}: {p.stderr.strip()[-400:]}")
    return json.loads(p.stdout)


class Pool:
    """(b): one stdio child per subject, started lazily and kept until close()."""

    def __init__(self):
        self.kids: dict[Path, subprocess.Popen] = {}
        self.n = 0
        self.lock = threading.Lock()

    def _kid(self, root: Path) -> subprocess.Popen:
        k = self.kids.get(root)
        if k is None or k.poll() is not None:
            k = subprocess.Popen([sys.executable, str(HERE / "mcp_server.py")], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, text=True, env=_env(root))
            self.kids[root] = k
            self._rpc(k, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "subject_dispatch", "version": "spike"}})
            k.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            k.stdin.flush()
        return k

    def _rpc(self, k: subprocess.Popen, method: str, params: dict) -> dict:
        self.n += 1
        k.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        k.stdin.flush()
        return json.loads(k.stdout.readline())

    def call(self, root: Path, tool: str, args: dict) -> dict:
        with self.lock:
            return self._rpc(self._kid(root), "tools/call", {"name": tool, "arguments": args})["result"]

    def close(self) -> None:
        for k in self.kids.values():
            k.stdin.close()
            k.wait(timeout=30)
        self.kids.clear()


LIST = {"name": "list_subjects", "title": "Which subjects does this reader answer for?",
        "description": "The subjects under KG_SUBJECTS, by id, and the one a call that names none reads (KG_SUBJECT).",
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}}


def with_subject(table: list[dict]) -> list[dict]:
    """Every tool's schema gains an optional ``subject`` id; list_subjects is added."""
    out = []
    for t in table:
        t = json.loads(json.dumps(t))
        t["inputSchema"].setdefault("properties", {})["subject"] = {
            "type": "string", "description": "the subject's id under KG_SUBJECTS (list_subjects); default: this server's own"}
        out.append(t)
    return out + [LIST]


def own() -> Path:
    import subject
    return Path(subject.SUBJECT.root).resolve()


def route(mode: str, pool: "Pool | None", tool: str, args: dict) -> dict | None:
    """The result for another subject's call, or None when the call is the process's own subject's."""
    if tool == "list_subjects":
        r = roots()
        return {"content": [{"type": "text", "text": json.dumps(sorted(r))}],
                "structuredContent": {"subjects": sorted(r), "default": own().name}}
    root = resolve(args.pop("subject"))
    if root is None or root == own():
        return None
    return via_child(root, tool, args) if mode == "child" else pool.call(root, tool, args)

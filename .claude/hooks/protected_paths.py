#!/usr/bin/env python3
"""knowgov's own protected paths, as fail-closed Claude Code hooks (task-0105; doc-0014 §11 item 2).

    python3 .claude/hooks/protected_paths.py vendored   # a vendored file or its SOURCE.md, edited by hand
    python3 .claude/hooks/protected_paths.py backlog    # a backlog markdown file, written other than by the CLI

Each reads one PreToolUse event on stdin (``.claude/settings.json`` matches Edit, Write, MultiEdit and
NotebookEdit) and checks the path the tool would write. The check answers under the gate contract (0 the
path is not protected, 1 it is, 2 the check cannot tell) and task-0099's ``decide`` maps that to the hook's
exit: 1 and 2 both block (exit 2, the reason on stderr), 0 lets the edit through. The mapping is imported
from ``instance/ci/claude/knowgov_hook.py``, never copied; the hooks call nothing else. A tool the vendor
scripts or the ``backlog`` CLI run through Bash writes the files itself, so no Edit or Write event names
them and the hooks never see it.

The vendored trees are the vendor tools' own destinations: ``tools/vendor_register.py``'s ``DEST``,
``tools/vendor_legible_model.py``'s ``DEST`` and, for every subject with a ``[vendor]`` table,
``tools/vendor_subject.py``'s ``spec_for(subject)["dest"]``; each holds its ``SOURCE.md``. The backlog is
every ``*.md`` under ``backlog/``. The knowledge gate is not wired to this repository: no subject
describes it. Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
PROTECTED, CLEAR, CANNOT_TELL = 1, 0, 2      # the gate contract, as the check answers


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def vendored_roots(root: Path = ROOT) -> list[Path]:
    """Every tree a vendor tool writes, read from the tools themselves."""
    sys.path.insert(0, str(root / "tools"))
    reg = _load("vendor_register", root / "tools" / "vendor_register.py")
    leg = _load("vendor_legible_model", root / "tools" / "vendor_legible_model.py")
    sub = _load("vendor_subject", root / "tools" / "vendor_subject.py")
    out = [Path(reg.DEST), Path(leg.DEST)]
    for manifest in sorted((root / "subjects").glob("*/subject.toml")):
        if "vendor" in sub.tomllib.loads(manifest.read_text(encoding="utf-8")):
            out.append(Path(sub.spec_for(manifest.parent)["dest"]))
    return [p.resolve() for p in out]


def _inside(p: Path, tree: Path) -> bool:
    return p == tree or tree in p.parents


def target(event: dict) -> Path | None:
    """The path a write tool names, resolved against the event's cwd; None for any other tool."""
    if event.get("tool_name") not in WRITE_TOOLS:
        return None
    ti = event.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path")
    if not raw:
        raise ValueError(f"{event.get('tool_name')} names no path")
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = Path(str(event.get("cwd") or ROOT)) / p
    return p.resolve()


def check_vendored(p: Path, root: Path = ROOT) -> tuple[int, str]:
    for tree in vendored_roots(root):
        if _inside(p, tree):
            what = "its SOURCE.md" if p.name == "SOURCE.md" else "a vendored file"
            return PROTECTED, (f"{p.relative_to(root)} is {what} under {tree.relative_to(root)}/. Vendored bytes and their note "
                               "change only through the vendor tool at a tag (tools/vendor_register.py, "
                               "tools/vendor_legible_model.py, tools/vendor_subject.py), never by hand (CLAUDE.md).")
    return CLEAR, ""


def check_backlog(p: Path, root: Path = ROOT) -> tuple[int, str]:
    if _inside(p, (root / "backlog").resolve()) and p.suffix.lower() == ".md":
        return PROTECTED, (f"{p.relative_to(root)} is a backlog record. Write it through the backlog CLI "
                           "(backlog task edit / decision / doc ...), never by Edit or Write, so ids and metadata stay consistent.")
    return CLEAR, ""


CHECKS = {"vendored": ("knowgov protected path: vendored", check_vendored,
                       "Route: re-vendor with the tool at a tag of the source repository."),
          "backlog": ("knowgov protected path: backlog", check_backlog,
                      "Route: make the change with the backlog CLI (`backlog <command> --help`).")}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        hook = _load("knowgov_hook", ROOT / "instance" / "ci" / "claude" / "knowgov_hook.py")
    except Exception as e:   # no mapping to apply: block by hand, the one exit the hook contract reads as a block
        print(f"knowgov protected paths: task-0099's hook script cannot load ({e}); blocked, fail-closed.", file=sys.stderr)
        return 2
    if len(argv) != 1 or argv[0] not in CHECKS:
        return hook.emit(hook.decide(CANNOT_TELL, check="knowgov protected paths",
                                     unavailable=f"usage: protected_paths.py {{{','.join(CHECKS)}}}"))
    name, check, route = CHECKS[argv[0]]
    try:
        event = json.loads(sys.stdin.read())
        if not isinstance(event, dict):
            raise ValueError("the hook event is not an object")
        p = target(event)
        rc, why = (CLEAR, "") if p is None else check(p)
    except Exception as e:   # cannot tell: the mapping blocks it (fail closed)
        rc, why = CANNOT_TELL, f"{e.__class__.__name__}: {e}"
    return hook.emit(hook.decide(rc, check=name, finding=why, unavailable=why, route=route))


if __name__ == "__main__":
    sys.exit(main())

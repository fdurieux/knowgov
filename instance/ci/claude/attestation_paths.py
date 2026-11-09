#!/usr/bin/env python3
"""An instance's attestations, guarded from an assistant's own writes: a fail-closed Claude Code hook
(task-0147; doc-0018 candidate 5).

    python3 attestation_paths.py [--instance DIR]

It reads one PreToolUse event on stdin (the settings snippet beside this file matches Edit, Write,
MultiEdit and NotebookEdit) and refuses a write that would attest for a person:

- a ``subject.toml`` whose ``[verification]``, ``[provenance]`` or ``[capture]`` table the write adds or changes
  (decision-0009: a load verifies and approves by construction only what the manifest declares, and
  ``[provenance] human`` names who attests). The tables are compared parsed, before and after the
  write, so an ordinary edit (an ``[[artefact]]``, a task class, a comment) passes, and so does removing
  a table outright, which attests nothing; removing ``[provenance]`` while ``[verification]`` stays
  does not, since the declared verification would then fall to the default agent;
- anything under a ``captures/`` folder (the answers, ``reviews/``, ``inferred/``), or under the
  folder a manifest's ``[capture] dir`` names;
- the file a manifest's ``[verification] map`` names (its ``review`` rows say which keys a review covers);
- a review file anywhere: a TOML file whose content after the write has a ``[review]`` table or a
  ``[[ruling]]`` (``harness/capture.py review`` takes it as input; it is a person's ruling);
- capture-shaped TOML anywhere: ``[[answer]]`` or ``[[unknown]]`` rows, a ``[capture]`` table, or an
  ``[answered]`` table naming a handle or a date (task-0204, doc-0030 P4), since a re-pointed
  ``[capture] dir`` would otherwise make any folder a capture folder;
- ``preload-baseline.json`` at any depth (the owner's commit of the pre-load findings they accept);
- anything under the instance's ``register/`` (the register changes by its own pull request and checks).

The check answers under the gate contract (0 the write attests nothing, 1 it does, 2 the check cannot
tell: an event it cannot read, an Edit whose ``old_string`` is not in the file, a ``subject.toml`` that
does not parse before or after) and task-0099's ``decide``, imported from ``knowgov_hook.py`` beside this
file and never copied, maps that to the hook's exit: 1 and 2 both block (exit 2, the reason on stderr).

Every write tool is read, NotebookEdit included: its ``new_source`` is checked as a review or a capture would be,
and one on a ``subject.toml`` cannot be read and blocks. Every name is compared case-folded (``Register/``,
``Captures/``, ``Preload-Baseline.json``), since macOS's and Windows' default filesystems match names whatever their
case (task-0268).

The instance is ``--instance``, else ``CLAUDE_PROJECT_DIR``, else the event's ``cwd``; a path outside it
is not this hook's to judge and passes. A manifest that does not parse adds no ``[capture] dir`` or map
path (the default ``captures/`` stays guarded), so the edit that repairs it is not itself blocked.

What it does not see: a shell command (``Bash``) that writes the same file, ``harness/capture.py
ingest``/``review`` included, and any write the person makes outside the assistant. It guards the
assistant's file tools; the pull request, reviewed by someone other than its author, guards the rest.
Standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
PROTECTED, CLEAR, CANNOT_TELL = 1, 0, 2      # the gate contract, as the check answers
ATTESTING = ("verification", "provenance", "capture")   # [capture] dir re-points the guarded captures (task-0204, P4)
CHECK = "knowgov attestation paths"
ROUTE = ("Route: an attestation is a person's act (decision-0009, decision-0002). Leave the table, the capture, the "
         "review, the baseline or the register as it is; say in the pull request what is missing, and the person "
         "of record writes it in their own commit, reviewed by someone other than its author. A gap in knowledge "
         "goes to its owner: harness/capture.py questionnaire.")
UNAVAILABLE_ROUTE = ("Route: the hook could not tell whether the write attests; fix what the message names (the hook "
                     "event, the file's TOML, the Edit's old_string), then repeat the write. It is not lifted by the "
                     "session it blocked.")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _cf(p: Path) -> tuple[str, ...]:
    """A path's parts case-folded: macOS's and Windows' default filesystems match names whatever their case, so
    Register/ is register/ and Preload-Baseline.json the baseline there (task-0268)."""
    return tuple(x.casefold() for x in p.parts)


def _inside(p: Path, tree: Path) -> bool:
    t = _cf(tree)
    return _cf(p)[:len(t)] == t


def _rel(p: Path, inst: Path) -> Path:
    """``p`` under ``inst`` (which ``_inside`` has established), whatever the case of the instance's own parts."""
    return Path(*p.parts[len(inst.parts):]) if len(p.parts) > len(inst.parts) else Path(".")


def target(event: dict, cwd: Path) -> Path | None:
    """The path a write tool names, resolved against the event's cwd; None for any other tool."""
    if event.get("tool_name") not in WRITE_TOOLS:
        return None
    ti = event.get("tool_input")
    if not isinstance(ti, dict):
        raise ValueError(f"{event.get('tool_name')} carries no tool_input")
    raw = ti.get("file_path") or ti.get("notebook_path")
    if not raw:
        raise ValueError(f"{event.get('tool_name')} names no path")
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = cwd / p
    return p.resolve()


def after_text(event: dict, p: Path) -> str | None:
    """The file's text once the write is applied. A NotebookEdit on a notebook (``.ipynb``) is None: no TOML is a
    notebook. On any other file its ``new_source`` is the text the content checks read, and on a ``subject.toml``
    the check cannot tell what the file becomes, so it says so (task-0268: every write tool is read)."""
    tool, ti = event["tool_name"], event["tool_input"]
    if tool == "Write":
        c = ti.get("content")
        if not isinstance(c, str):
            raise ValueError("Write carries no content")
        return c
    if tool == "NotebookEdit":
        if p.suffix.casefold() == ".ipynb":
            return None
        if p.name.casefold() == "subject.toml":
            raise ValueError(f"a NotebookEdit on {p.name} cannot be read as the TOML it would leave")
        src = ti.get("new_source", "")
        if not isinstance(src, str):
            raise ValueError("NotebookEdit carries a new_source that is not text")
        return src
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    edits = ti.get("edits") if tool == "MultiEdit" else [ti]
    if not isinstance(edits, list) or not edits:
        raise ValueError(f"{tool} carries no edits")
    for e in edits:
        old, new = e.get("old_string"), e.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            raise ValueError(f"{tool} carries an edit without old_string or new_string")
        if old == "" and text == "":
            text = new
            continue
        if old not in text:
            raise ValueError(f"{tool}'s old_string is not in {p.name}")
        text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
    return text


def _manifests(inst: Path) -> list[tuple[Path, dict]]:
    out = []
    for m in sorted(inst.rglob("subject.toml")):
        if any(part.startswith(".") for part in m.relative_to(inst).parts):
            continue
        try:
            out.append((m.resolve(), tomllib.loads(m.read_text(encoding="utf-8"))))
        except (OSError, ValueError, UnicodeDecodeError):
            continue   # the repairing edit must pass; captures/ stays guarded by name
    return out


def guarded_files(inst: Path) -> tuple[list[Path], list[Path]]:
    """The folders and the files a manifest names as attestations: its [capture] dir and [verification] map."""
    trees, files = [], []
    for m, doc in _manifests(inst):
        cap = (doc.get("capture") or {}).get("dir") if isinstance(doc.get("capture"), dict) else None
        if isinstance(cap, str) and cap:
            trees.append((m.parent / cap).resolve())
        ver = doc.get("verification")
        vmap = ver.get("map") if isinstance(ver, dict) else None
        if isinstance(vmap, str) and vmap:
            files.append((m.parent / vmap).resolve())
    return trees, files


def _tables(text: str, where: str) -> dict:
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"{where} does not parse as TOML ({e})") from None
    return {t: doc.get(t) for t in ATTESTING}


def _is_review(text: str) -> bool:
    try:
        doc = tomllib.loads(text)
        return "review" in doc or "ruling" in doc
    except tomllib.TOMLDecodeError:   # half-written: read the headers as text
        heads = {ln.strip().replace(" ", "") for ln in text.splitlines()}
        return "[review]" in heads or "[[ruling]]" in heads


def _is_capture(text: str) -> bool:
    """Capture-shaped content (task-0204, doc-0030 P4), what ``load_captures`` reads as a person's answers
    wherever the file lies: ``[[answer]]`` or ``[[unknown]]`` rows, a ``[capture]`` table, or an
    ``[answered]`` table that names a handle or a date (a questionnaire signed for a person). A blank
    questionnaire, ``[answered]`` left empty as ``capture.py questionnaire`` writes it, is not one."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:   # half-written: read the headers as text, failing closed on [answered]
        heads = {ln.strip().replace(" ", "") for ln in text.splitlines()}
        return bool(heads & {"[[answer]]", "[[unknown]]", "[capture]", "[answered]"})
    ans = doc.get("answered")
    signed = isinstance(ans, dict) and any(str(ans.get(f) or "").strip() for f in ("from", "on"))
    return "answer" in doc or "unknown" in doc or "capture" in doc or signed


def check(event: dict, inst: Path) -> tuple[int, str]:
    p = target(event, Path(str(event.get("cwd") or inst)))
    if p is None or not _inside(p, inst):
        return CLEAR, ""
    relp = _rel(p, inst)
    rel = relp.as_posix()
    low = _cf(relp)   # every name below compared case-folded (task-0268)
    if low[:1] == ("register",):
        return PROTECTED, (f"{rel} is in the instance's register. The register changes by its own pull request, "
                           "checked by its tools/check_register.py and approved there, never by an assistant's edit.")
    if p.name.casefold() == "preload-baseline.json":
        return PROTECTED, (f"{rel} is a pre-load baseline: the owner's commit of the findings they accept "
                           "(tools/preload_check.py -o). An assistant does not write it.")
    trees, files = guarded_files(inst)
    if "captures" in low[:-1] or any(_inside(p, t) for t in trees):
        return PROTECTED, (f"{rel} is under a subject's captures: answers people gave (harness/capture.py ingest) "
                           "and the reviews that rule on them. Only a person's handle enters them.")
    if any(_cf(p) == _cf(f) for f in files):
        return PROTECTED, (f"{rel} is a subject's verification map, named by its [verification] map: which keys a "
                           "suite scenario or a dated review verifies. A person attests it.")
    after = after_text(event, p)
    if after is None:
        return CLEAR, ""
    if p.name.casefold() == "subject.toml":
        before = p.read_text(encoding="utf-8") if p.exists() else ""
        b, a = _tables(before, f"{rel} before the write"), _tables(after, f"{rel} after the write")
        changed = [t for t in ATTESTING if a[t] is not None and a[t] != b[t]]
        if a["provenance"] is None and b["provenance"] is not None and a["verification"] is not None:
            changed.append("provenance (removed while [verification] stays)")
        if changed:
            return PROTECTED, (f"{rel}: the write adds or changes [{'], ['.join(changed)}]. These tables say who "
                               "attests and when (decision-0009); the person of record writes them.")
        return CLEAR, ""
    if p.suffix.casefold() == ".toml" and _is_review(after):
        return PROTECTED, (f"{rel} would be a review file ([review] or [[ruling]]): a second person's ruling on what "
                           "the store holds (decision-0002). The reviewer writes it.")
    if p.suffix.casefold() == ".toml" and _is_capture(after):
        return PROTECTED, (f"{rel} would be capture-shaped ([[answer]], [[unknown]], [capture] or a signed [answered]): "
                           "a person's answers under their handle, which harness/capture.py ingest writes from their "
                           "questionnaire. Only a person's handle enters them, wherever the file lies.")
    return CLEAR, ""


def main(argv: list[str] | None = None) -> int:
    try:
        hook = _load("knowgov_hook", HERE / "knowgov_hook.py")
    except Exception as e:   # no mapping to apply: block by hand, the one exit the hook contract reads as a block
        print(f"{CHECK}: task-0099's hook script cannot load ({e}); blocked, fail-closed.", file=sys.stderr)
        return 2
    ap = argparse.ArgumentParser(prog="attestation_paths.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--instance", help="the instance checkout (default CLAUDE_PROJECT_DIR, else the event's cwd)")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return hook.emit(hook.decide(CANNOT_TELL, check=CHECK, unavailable="usage: attestation_paths.py [--instance DIR]",
                                     unavailable_route=UNAVAILABLE_ROUTE))
    try:
        event = json.loads(sys.stdin.read())
        if not isinstance(event, dict):
            raise ValueError("the hook event is not an object")
        raw = a.instance or os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd")
        if not raw or not Path(str(raw)).is_dir():
            raise ValueError(f"no instance checkout ({raw or 'none named'})")
        rc, why = check(event, Path(str(raw)).resolve())
    except Exception as e:   # cannot tell: the mapping blocks it (fail closed)
        rc, why = CANNOT_TELL, f"{e.__class__.__name__}: {e}"
    return hook.emit(hook.decide(rc, check=CHECK, finding=why, unavailable=why, route=ROUTE, unavailable_route=UNAVAILABLE_ROUTE))


if __name__ == "__main__":
    try:   # task-0200 (P8): any exception blocks through task-0099's entry; a hook that cannot load blocks by hand
        _hook = _load("knowgov_hook", HERE / "knowgov_hook.py")
    except Exception as e:  # noqa: BLE001
        print(f"{CHECK}: task-0099's hook script cannot load ({e}); blocked, fail-closed.", file=sys.stderr)
        sys.exit(2)
    sys.exit(_hook.entry(main, CHECK))

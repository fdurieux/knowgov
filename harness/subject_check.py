"""A proposed subject checked in the call, never stored (task-0146; doc-0018 candidate 3).

The reader's ``subject_check`` tool, for a client with no shell (Claude Desktop): the call carries a
proposed ``subject.toml``, ``register_map.toml``, ``scenarios.toml`` and the documents' text, and the
answer is ``tools/check_subject.py``'s report (schema ``subject-check``), made by that module's own
``check`` against the served register (``KG_REGISTER``, as ``register_impact`` reads it) and the
platform's kinds (``instance/kinds.toml``'s mappers).

The files are written to a temporary directory, laid out as an instance's subject root is
(``<tmp>/instance/subjects/<name>/``, so a document named ``../../artefacts/<kind>/<file>`` lands under
``<tmp>/instance/artefacts/``), checked there and removed when the call ends, answered or not. A path
that would leave ``<tmp>/instance``, an absolute path, or one with a NUL is refused. The mappers' yield
runs in a child process, as ``check_subject`` runs it (the harness binds its subject at import), so the
server's own subject is never touched. Nothing is written to the store, the register or the instance.

Every path the proposed manifest names is confined too (task-0146 H7, doc-0030): an ``[[artefact]]
path`` or ``include``, ``[reference] code``, ``[oracle] script``, ``[verification] map``, ``[register]
map``, ``[record] dir``, ``[capture] dir`` and any other path field (``PATH_KEYS``), at any depth, is
refused when it is absolute or resolves outside ``<tmp>/instance``, before anything is written and
before the yield child runs, so the report never says whether a server file exists nor quotes it. Paths
are compared normalised, so ``x/../subject.toml`` is the manifest itself and is refused as a duplicate.

The call is bounded: at most ``MAX_DOCUMENTS`` documents, ``MAX_PATH`` characters a path and
``MAX_BYTES`` bytes of text in all (UTF-8); a larger call is refused before anything is written.
The report's ``root`` is the label the call names (``root``, default ``proposed``), so a client that
names the subject root's path gets the report the CLI prints for that path.
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 1_000_000
MAX_DOCUMENTS = 64
MAX_PATH = 240
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
# the manifest's fields whose values the loader joins to the subject root (harness/subject.py): each is
# confined to the call's temporary instance (H7); ``include`` holds a list of globs
PATH_KEYS = frozenset({"path", "code", "script", "map", "dir", "export_manifest", "feedback", "manifest", "include"})


class SubjectCheckError(ValueError):
    """The call cannot be checked: a missing manifest, a path out of bounds, a call too large."""


def _check_subject():
    mod = sys.modules.get("check_subject")
    if mod is None:
        spec = importlib.util.spec_from_file_location("check_subject", ROOT / "tools" / "check_subject.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["check_subject"] = mod
        spec.loader.exec_module(mod)
    return mod


def _text(name: str, value) -> str:
    if not isinstance(value, str):
        raise SubjectCheckError(f"{name} must be a string (the file's text)")
    return value


def _rel(path) -> PurePosixPath:
    if not isinstance(path, str) or not path or len(path) > MAX_PATH or "\0" in path or "\\" in path:
        raise SubjectCheckError(f"document path {path!r} is not a relative POSIX path of at most {MAX_PATH} characters")
    p = PurePosixPath(path)
    if p.is_absolute():
        raise SubjectCheckError(f"document path {path!r} is absolute; name it relative to the subject root, as the manifest does")
    return p


def _inside(base: Path, name: str, rel: PurePosixPath) -> Path:
    """``rel`` under the subject root ``base/subjects/name``, normalised without touching the disk; it
    must stay in ``base``."""
    parts: list[str] = []
    for part in ("subjects", name, *rel.parts):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise SubjectCheckError(f"document path {rel.as_posix()!r} leaves the instance (at most ../../ from the subject root)")
            parts.pop()
        else:
            parts.append(part)
    if len(parts) < 2 or parts == ["subjects", name]:
        raise SubjectCheckError(f"document path {rel.as_posix()!r} names no file")
    return base.joinpath(*parts)


def _norm(rel: PurePosixPath, name: str) -> tuple[str, ...]:
    """``rel`` from the subject root, normalised without the disk, as parts under the instance; raises when
    it leaves the instance."""
    parts: list[str] = []
    for part in ("subjects", name, *rel.parts):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise SubjectCheckError(f"path {rel.as_posix()!r} leaves the instance (at most ../../ from the subject root)")
            parts.pop()
        else:
            parts.append(part)
    return tuple(parts)


def _manifest_paths(m, where: str = ""):
    """(where, value) for every path field of a parsed manifest, at any depth."""
    if isinstance(m, dict):
        for k, v in m.items():
            at = f"{where}.{k}" if where else str(k)
            if k in PATH_KEYS and isinstance(v, str):
                yield at, v
            elif k in PATH_KEYS and isinstance(v, list) and all(isinstance(x, str) for x in v):
                yield from ((f"{at}[{i}]", x) for i, x in enumerate(v))
            else:
                yield from _manifest_paths(v, at)
    elif isinstance(m, list):
        for i, v in enumerate(m):
            yield from _manifest_paths(v, f"{where}[{i}]")


def confine_manifest(manifest: str, name: str) -> None:
    """Refuse a manifest that names a path outside the call's temporary instance (H7): absolute, with a
    backslash or NUL, or climbing past it. A manifest that does not parse names no path the loader follows;
    the report says it does not parse."""
    cs = _check_subject()
    try:
        m = cs.tomllib.loads(manifest)
    except cs.tomllib.TOMLDecodeError:
        return
    for where, value in _manifest_paths(m):
        if not value:   # an artefact with no path is one a plant adds
            continue
        if "\0" in value or "\\" in value or value.startswith("~") or PurePosixPath(value).is_absolute():
            raise SubjectCheckError(f"subject.toml {where} is not a relative path inside the subject's instance; "
                                    "a proposed manifest names its files relative to the subject root")
        _norm(PurePosixPath(value), name)


def plan(args: dict) -> tuple[str, str, dict[PurePosixPath, str]]:
    """The call read and bounded, before anything is written: the root's name, its label and every
    file to write, relative to the subject root."""
    if not isinstance(args, dict):
        raise SubjectCheckError("the arguments must be an object")
    manifest = _text("subject_toml", args.get("subject_toml"))
    label = args.get("root", "proposed")
    if not isinstance(label, str) or not label or len(label) > MAX_PATH:
        raise SubjectCheckError(f"root must be a label of at most {MAX_PATH} characters")
    tail = PurePosixPath(label).name
    name = tail if NAME_RE.fullmatch(tail or "") and tail not in (".", "..") else "proposed"
    files: dict[PurePosixPath, str] = {PurePosixPath("subject.toml"): manifest}
    for field, fname in (("scenarios_toml", "scenarios.toml"), ("plants_toml", "plants.toml")):
        if args.get(field) is not None:
            files[PurePosixPath(fname)] = _text(field, args[field])
    if args.get("register_map_toml") is not None:
        cs = _check_subject()
        try:
            m = cs.tomllib.loads(manifest)
        except cs.tomllib.TOMLDecodeError:
            m = {}
        reg = m.get("register") if isinstance(m.get("register"), dict) else {}
        rel = reg.get("map", "register_map.toml") if isinstance(reg.get("map", "register_map.toml"), str) else "register_map.toml"
        files[_rel(rel)] = _text("register_map_toml", args["register_map_toml"])
    docs = {} if args.get("documents") is None else args["documents"]
    if not isinstance(docs, dict):
        raise SubjectCheckError("documents must be an object: {path relative to the subject root: the document's text}")
    if len(docs) > MAX_DOCUMENTS:
        raise SubjectCheckError(f"{len(docs)} documents; a call carries at most {MAX_DOCUMENTS}")
    seen = {_norm(r, name): r for r in files}
    for path, text in docs.items():
        rel = _rel(path)
        key = _norm(rel, name)
        if key in seen:   # compared normalised: x/../subject.toml is the manifest (H7)
            raise SubjectCheckError(f"document {path!r} is the same file as {seen[key].as_posix()!r}, passed already")
        seen[key] = rel
        files[rel] = _text(f"documents[{path!r}]", text)
    confine_manifest(manifest, name)
    size = sum(len(t.encode("utf-8")) for t in files.values())
    if size > MAX_BYTES:
        raise SubjectCheckError(f"the call carries {size} bytes of text; at most {MAX_BYTES}")
    return name, label, files


def evaluate(args: dict, register: Path | None = None) -> dict:
    """check_subject's report on the proposed files, from a temporary root removed before returning."""
    name, label, files = plan(args)
    cs = _check_subject()
    if register is None:
        import cadence
        register = cadence.register_root()
    tmp = Path(tempfile.mkdtemp(prefix="kg-subject-check-"))
    try:
        base = tmp / "instance"
        root = base / "subjects" / name
        root.mkdir(parents=True)
        for rel, text in files.items():
            dest = _inside(base, name, rel)
            if not dest.resolve().is_relative_to(base.resolve()):   # a symlink cannot exist here, but say so
                raise SubjectCheckError(f"document path {rel.as_posix()!r} leaves the instance")
            if dest.exists() and dest.is_dir():
                raise SubjectCheckError(f"document path {rel.as_posix()!r} is also a folder another path names")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        try:
            rep = cs.check(root, register if Path(register).is_dir() else None, cs.kinds_mappers())
        except cs.formats.FormatError as e:   # task-0174: a manifest for a newer knowgov is refused, never misread
            raise SubjectCheckError(str(e).replace(root.as_posix(), label)) from None
        rep["root"] = label
        return rep
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

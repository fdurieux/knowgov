"""What retiring a register node touches (task-0111): the register's own impact walk, the map rows
it lands on, and, with a scenario held, each key's level, stale statements and suspect derived outputs.

The walk is the vendored register's (``tools/impact.py``, loaded by path from ``KG_REGISTER``, the
register ``cadence.register_root`` reads, as ``demo/app/register_view`` loads it): approved links only,
a deprecated or retired node is not expanded, an edge not followed is listed with its state. By default
a node's ``parent`` is not descended: its children are listed, each with its state, as not walked. With
``children`` (task-0118) the descent is the register's own (its decision 0014, ``impact.walk_children``,
v0.2.8 on): the walk also starts from every descendant by ``parent``, recursively, each by its own
taxonomy's row; an approved one is walked, any other is listed not followed, with its state, and not walked from, and what
is reached is the union less the start and its descendants. Either way the start is never counted
reached (decision 0016, v0.2.9 on: an edge back to it is listed, ``to_start``, and ``impact.reached``
drops it). ``parent`` is never climbed. The rows are
the subject's ``register_map.toml``: a row whose nodes name the start, a walked descendant or a reached
node lands, with the nodes it came through; with ``children``, a row that names only a
descendant not followed lands after them, flagged ``not_followed`` (task-0120; never ``withdrawn``, which is
deprecated or retired alone, task-0305). Its owner is the row's, as the gate's
findings name it.

The levels come from the gate itself, ``gate_cli.evaluate`` over the landed keys on one ``as_of``
under one declared task class (its block levels, bar and route; codegen by default, task-0120), the
report ``gate_verdict --task`` makes for that key set, so a key reads here as ``gate_verdict`` reports it.
The keys are the reach: every mapped key a change to the node touches, whatever a class requires; the
class sets how they are read, not which are listed, so this is not a class's readiness. That is
``proposal_impact``'s slices, which keep to the class's ``[tasks.<class>]`` keys (task-0252).
Only the store port's reads are used; nothing is written. Standard library only.
"""
from __future__ import annotations

import contextlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import threading
import tomllib
from pathlib import Path

NODE_ID = re.compile(r"^[A-Z]+-\d{4,}$")
WALKS = ("dependants", "realisers")
from gate_cli import OWNED  # noqa: E402  the finding kinds that concern one key: gate_cli's own, one definition (task-0260)

_tools: dict[str, dict] = {}
_lock = threading.Lock()


class ImpactError(ValueError):
    """The question cannot be answered: a malformed or unknown id, a walk the register lacks."""


def register_root() -> Path:
    import cadence
    return cadence.register_root()


class RegisterUnreadable(ImpactError):
    """A register the reader was given that it cannot read (task-0279, decision-0033 choice 5): the commands exit
    2 and the MCP reader refuses to start, naming who named it and the path."""


def unreadable(root: Path, tools: bool = True) -> str | None:
    """Why ``root`` is not a register this knowgov reads, or None: a directory whose ``metamodel/types.toml``
    names its taxonomies and, with ``tools``, holds the register's own ``tools/register.py``, which the walks
    and the checker load from it."""
    root = Path(root)
    if not root.is_dir():
        return "no such directory"
    try:
        types = tomllib.loads((root / "metamodel" / "types.toml").read_text(encoding="utf-8"))
    except OSError:
        return "no metamodel/types.toml"
    except tomllib.TOMLDecodeError as e:
        return f"metamodel/types.toml is not TOML: {e}"
    if not types.get("taxonomy"):
        return "metamodel/types.toml names no taxonomy"
    if tools and not (root / "tools" / "register.py").is_file():
        return "no tools/register.py, the register's own loader"
    return None


def named() -> tuple[Path, str] | None:
    """(the register, who named it) when ``KG_REGISTER`` names one; None when the default is read."""
    v = os.environ.get("KG_REGISTER")
    return (Path(v), "KG_REGISTER") if v else None


def require(root: Path | None = None, by: str | None = None, tools: bool = True) -> Path:
    """``root`` (by default the register this process reads), or ``RegisterUnreadable`` naming ``by`` (by default
    KG_REGISTER when it is set, else the default register) and the path."""
    if root is None:
        root, by = register_root(), (by or ("KG_REGISTER" if named() else "the default register"))
    why = unreadable(root, tools)
    if why:
        raise RegisterUnreadable(f"{by or 'the register'} {Path(root).as_posix()} is not a readable register: {why}")
    return Path(root)


def require_named(tools: bool = True) -> None:
    """``RegisterUnreadable`` when ``KG_REGISTER`` names a register that cannot be read; nothing when it is unset."""
    n = named()
    if n:
        require(n[0], n[1], tools)


@contextlib.contextmanager
def no_bytecode():
    """Python writes no ``__pycache__`` while the register's own modules load: they sit in ``KG_REGISTER``,
    which an instance mounts read-only and the reader never writes (doc-0030 M11, task-0208). Covers the
    modules they import in turn; the interpreter's own setting is restored after."""
    global _nb_depth, _nb_before
    with _nb_lock:   # counted, so two threads loading at once never restore it under each other
        if _nb_depth == 0:
            _nb_before = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
        _nb_depth += 1
    try:
        yield
    finally:
        with _nb_lock:
            _nb_depth -= 1
            if _nb_depth == 0:
                sys.dont_write_bytecode = _nb_before


_nb_lock = threading.Lock()
_nb_depth = 0
_nb_before = False


def load_tools(root: Path | None = None) -> dict:
    """The register's ``register`` and ``impact`` modules, imported once per root, by path, from the
    register itself (``impact.py`` imports ``register`` by name, so both are put in ``sys.modules``)."""
    root = (root or register_root()).resolve()
    with _lock:
        if str(root) not in _tools:
            tools = root / "tools"
            if str(tools) not in sys.path:
                sys.path.insert(0, str(tools))
            mods = {}
            for name in ("register", "impact"):
                spec = importlib.util.spec_from_file_location(name, tools / f"{name}.py")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                with no_bytecode():
                    spec.loader.exec_module(mod)
                mods[name] = mod
            _tools[str(root)] = mods
        return _tools[str(root)]


def source(root: Path) -> dict:
    """The register's tag and commit: a vendored copy's SOURCE.md, else what git says of a checkout."""
    note = root / "SOURCE.md"
    if note.exists():
        text = note.read_text(encoding="utf-8")
        commit = re.search(r"\| commit \| `([0-9a-f]{40})`", text)
        tag = re.search(r"^\| tag \| `(v[0-9][^`]*)`", text, re.M)
        return {"tag": tag.group(1) if tag else "", "commit": commit.group(1) if commit else ""}

    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""
    return {"tag": git("describe", "--tags", "--exact-match"), "commit": git("rev-parse", "HEAD")}


def identity(root: Path) -> dict:
    """The register a gate decided on, for its report (task-0237, decision-0029): ``{tag, commit, why}``.
    A vendored copy's SOURCE.md names both. An instance's own checkout gives its git ``HEAD`` and the tag
    exactly on it, read without the network (no fetch) and only when git answers for this folder itself,
    not an enclosing repository. Otherwise ``tag`` and ``commit`` are null and ``why`` says why; ``why``
    is null when the commit is known. A tag is null when none names the commit. Nothing reads the clock."""
    root = Path(root)
    note = root / "SOURCE.md"
    if note.is_file():
        found = source(root)
        commit, tag = found["commit"] or None, found["tag"] or None
        return {"tag": tag, "commit": commit, "why": None if commit else "the register's SOURCE.md names no commit"}
    exe = shutil.which("git")
    if exe is None:
        return {"tag": None, "commit": None, "why": "the register has no SOURCE.md and git is not installed here"}

    def git(*args: str) -> str | None:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True, text=True, timeout=10,
                               env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout.strip() if p.returncode == 0 else None
    top = git("rev-parse", "--show-toplevel")
    if not top or Path(top).resolve() != root.resolve():
        return {"tag": None, "commit": None, "why": "the register has no SOURCE.md and is not a git checkout of its own"}
    commit = git("rev-parse", "HEAD")
    if not commit or not re.fullmatch(r"[0-9a-f]{40}", commit):
        return {"tag": None, "commit": None, "why": "the register's checkout has no commit"}
    return {"tag": git("describe", "--tags", "--exact-match", "HEAD") or None, "commit": commit, "why": None}


def loaded_files(root: Path) -> list[Path] | None:
    """The files a load reads from the register at ``root`` (task-0320, decision-0038 N2): every file its own loader
    opens (``tools/register.py`` ``load_register``: the metamodel, the glossary, the nodes, the relationship files, the
    exceptions), recorded as it opens them, never a list kept here; and the issued-handles list its
    ``metamodel/types.toml`` names (``[elicited] issued``), which the review rules read (``review.issued_handles``).
    None when the register has no loader of its own or it fails."""
    root = Path(root).resolve()
    try:
        mod = load_tools(root)["register"]
    except Exception:  # noqa: BLE001 — no loader to ask: unknown, never a guess
        return None
    opened: list[Path] = []
    with _lock:
        plain = mod.load_toml

        def recording(path):
            opened.append(Path(path).resolve())
            return plain(path)
        mod.load_toml = recording
        try:
            reg = mod.load_register(root)
        except Exception:  # noqa: BLE001
            return None
        finally:
            mod.load_toml = plain
    issued = (reg.get("types") or {}).get("elicited", {}).get("issued")
    if isinstance(issued, str) and (root / issued).is_file():
        opened.append((root / issued).resolve())
    return sorted(set(opened))


def files_digest(root: Path) -> str | None:
    """The register's files as a load reads them (task-0320, decision-0038 N2): the sha256, hex, of one canonical JSON
    line ``[path, sha256]`` per file ``loaded_files`` names (its POSIX path relative to the root, its raw bytes'
    digest), sorted. A loaded file edited under the same tag and commit moves it; a file no load reads (a README, a
    stray file) does not. None when the files cannot be known."""
    import hashlib
    import json
    files = loaded_files(root)
    if not files:
        return None
    root = Path(root).resolve()
    lines = [json.dumps([p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()], ensure_ascii=False,
                        separators=(",", ":")) + "\n" for p in files]
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def owning_unit(reg: dict, nid: str) -> dict:
    """The unit its owner field names, that unit's name, and the sources of the approved owns links
    to the node, sorted: the impact panel's three (``register_view.owning_unit``)."""
    unit = (reg["nodes"].get(nid) or {}).get("owner", "") or ""
    owns = sorted({ln["source"] for ln in reg["relationships"].get("owns", {}).get("links", [])
                   if ln.get("target") == nid and ln.get("state") == "approved"})
    return {"unit": unit, "name": (reg["nodes"].get(unit) or {}).get("name", ""), "owns": owns}


def walk(node: str, which: str = "dependants", root: Path | None = None, children: bool = False) -> dict:
    """The register part of the answer, without the store: the node, its children, the edges, what
    they reach. With ``children``, every descendant by ``parent`` with its parent, its state, whether
    it was walked (approved) and, if not, ``not_followed`` (task-0305), its state saying why; the edges and what is reached are
    ``impact.walk_children``'s. Raises ImpactError on a malformed or unknown id, a walk the register
    lacks, or ``children`` asked of a register without the descent."""
    if not isinstance(node, str) or not NODE_ID.match(node):
        raise ImpactError(f"node {node!r}: a register id, such as an upper-case prefix, a hyphen and four or more digits")
    if which not in WALKS:
        raise ImpactError(f"walk must be one of {list(WALKS)}")
    if not isinstance(children, bool):
        raise ImpactError("children must be true or false")
    root = (root or register_root()).resolve()
    T = load_tools(root)
    reg = T["register"].load_register(root)
    if node not in reg["nodes"]:
        raise ImpactError(f"{node}: no such node in the register")
    rows = getattr(T["impact"], "WALKS", {}).get(which)
    if rows is None and which != "dependants":
        raise ImpactError(f"the register at {source(root)['tag'] or root} offers no {which} walk")
    if children:
        if not hasattr(T["impact"], "walk_children"):
            raise ImpactError(f"the register at {source(root)['tag'] or root} does not descend parent (its decision 0014, v0.2.8 on)")
        got = T["impact"].walk_children(reg, node, rows)
        edges, reached = got["edges"], sorted(got["reached"])
        listed = [{"id": d["id"], "name": reg["nodes"][d["id"]].get("name", ""), "state": d["state"],
                   "parent": reg["nodes"][d["id"]].get("parent"), "walked": d["live"], "not_followed": not d["live"]}
                  for d in got["descendants"]]
    else:
        edges = T["impact"].walk(reg, node) if rows is None else T["impact"].walk(reg, node, rows)
        reached = sorted(T["impact"].reached(edges))
        listed = [{"id": c, "name": reg["nodes"][c].get("name", ""), "state": reg["nodes"][c].get("state", ""), "walked": False}
                  for c in sorted(nid for nid, c in reg["nodes"].items() if c.get("parent") == node)]
    n = reg["nodes"][node]
    by_prefix: dict[str, list[dict]] = {}
    for x in reached:
        r = reg["nodes"].get(x) or {}
        by_prefix.setdefault(x.split("-", 1)[0], []).append(
            {"id": x, "name": r.get("name", ""), "state": r.get("state", ""), "owning_unit": owning_unit(reg, x)})
    return {"register": source(root), "walk": which,
            "node": {"id": node, "taxonomy": n.get("_taxonomy"), "kind": n.get("kind"), "name": n.get("name"),
                     "state": n.get("state"), "owner": n.get("owner"), "parent": n.get("parent"),
                     "owning_unit": owning_unit(reg, node)},
            "children_walked": children, "children": listed,
            "edges": edges, "reached": by_prefix, "reached_ids": reached}


def landed_rows(register_map: dict, node: str, reached: list[str], walked: list[str] = (),
                not_followed: list[str] = ()) -> list[dict]:
    """The map's rows that name the start, a walked descendant or a reached node, each with the nodes it
    came through (``via``: the start first when the row names it, then the walked descendants, then the
    reached nodes it names, as ``walk`` lists them). Then (task-0120) every other row that names a
    descendant not followed, flagged ``not_followed: true`` with those descendants it names as ``via``:
    a key that rests on what the descent reached but did not walk, listed and walked no further. The far
    node of an edge not followed is not touched."""
    touched = [node, *walked, *reached]
    out, flagged = [], []
    for row in register_map.get("row", []):
        names = row.get("nodes") or []
        via = [x for x in touched if x in names]
        if via:
            out.append({"key": row["key"], "owner": row.get("owner"), "anchor": row.get("anchor"), "via": via})
        elif any(x in names for x in not_followed):
            flagged.append({"key": row["key"], "owner": row.get("owner"), "anchor": row.get("anchor"),
                            "via": [x for x in not_followed if x in names], "not_followed": True})
    return out + flagged


def with_levels(keys: list[dict], report: dict) -> list[dict]:
    """Each landed key with its level, its findings of the owned kinds (key, intended, stale, lapsed and act, as
    gate_cli.OWNED names them, task-0260), the ids of its stale
    statements and the suspect derived outputs that used one of them, all read off ``report``: the
    gate's report over the landed keys (``gate_cli.evaluate``, as ``gate_verdict`` makes it for a
    key set), so a key reads here exactly as ``gate_verdict`` reports it on the same as_of."""
    fs = report["findings"]
    suspect = [f for f in fs if f["kind"] == "suspect_derived"]
    out = []
    for k in keys:
        mine = [f for f in fs if f["kind"] in OWNED and f["key"] == k["key"]]
        stale = sorted(f["ref"] for f in mine if f["kind"] == "stale")
        out.append({**k, "level": report["levels"][k["key"]], "stale": stale,
                    "suspect": sorted(f["ref"] for f in suspect if set(f["related"]) & set(stale)), "findings": mine})
    return out

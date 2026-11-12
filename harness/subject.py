"""The subject: what the harness loads and the page shows, read from a subject root.

An artefact's ``path`` is a file, or a directory: a directory artefact is one document made of
every file under it that matches its ``include`` globs (all files by default), each part
prefixed by a ``==> <relative path> <==`` line, in path order. A kit whose layers are folders
(a suite of feature files, a set of contracts) is loaded that way: one artefact per layer, so a
statement the layer makes once is one assertion, and ``harness/extract.py``'s ``bundle_parts``
gives a mapper the parts back.

A subject root (``KG_SUBJECT``, default ``subjects/cargo_quote``) holds ``subject.toml`` (the
artefacts, the reference code, the oracle, the provenance and verification constants, the task
classes, the three-valued keys, the record), ``scenarios.toml`` (optional: the recorded scenarios,
their plants' switches, the measures' keyword sets and targets, the page's sentences and the
systemic placements), ``plants.toml`` (optional: the mechanical patches), ``queries.toml``
(optional: saved Cypher), ``register_map.toml`` (optional) and ``prompts/`` (the arms' task
prompts). The format is documented in ``subjects/README.md``. Nothing in the harness or the page
names a subject, a document or a scenario: all of it comes from here.
"""
from __future__ import annotations

import hashlib
import os
import re
import tomllib
from pathlib import Path

BUNDLE_MARK = "==> {rel} <=="   # the line that opens each part of a directory artefact
BUNDLE_MARK_RE = re.compile(r"^==> (.+?) <==$", re.M)


def bundle_parts(text: str) -> list[tuple[str, str]]:
    """(relative path, text) per part of a bundle; a plain file is one part named ''."""
    marks = list(BUNDLE_MARK_RE.finditer(text))
    if not marks:
        return [("", text)]
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1), text[m.end() + 1:end]))
    return out


def _glob_re(g: str) -> re.Pattern:
    """A relative POSIX glob as a regex: ``*`` and ``?`` never cross a slash, ``**`` does."""
    out = ""
    i = 0
    while i < len(g):
        c = g[i]
        if g.startswith("**", i):
            out += ".*"
            i += 2
            continue
        out += {"*": "[^/]*", "?": "[^/]"}.get(c, re.escape(c))
        i += 1
    return re.compile(f"^{out}$")


def bundle_files(root: Path, include: list[str] | None = None) -> list[tuple[str, Path]]:
    """(relative path, file) for every file under ``root`` matching ``include`` (relative POSIX
    globs, path-aware; all files when empty), in path order: the files ``bundle`` joins."""
    patterns = [_glob_re(g) for g in (include or [])]
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        if patterns and not any(r.match(rel) for r in patterns):
            continue
        out.append((rel, p))
    return out


REFERENCE_INCLUDE = ["*.py", "**/*.py"]   # the files of a reference implementation directory the load bundles and digests


class CodePathOutside(Exception):
    """A code or suite path leaving the instance (task-0340 R2); exits 2 under cli_exit, the message the cause."""


def suite_files(oracle) -> list[str]:
    """``[oracle] suite`` (task-0338, decision-0039 §3.5): the files the suite reads beside ``[oracle] script``, its
    expectations among them, as the manifest names them relative to the subject root, sorted by path; [] when the
    field is missing or holds no string (check_subject names a malformed one)."""
    v = oracle.get("suite") if isinstance(oracle, dict) else None
    return sorted({x for x in v if isinstance(x, str) and x}) if isinstance(v, list) else []


def _file_digests(p: Path, include: list[str] | None, prefix: str) -> dict[str, str]:
    """Each file of ``p`` by its path (``prefix`` for a file, ``prefix/<relative>`` for a directory's, the relative
    path alone with no prefix), with the SHA-256 of its raw bytes; {} when ``p`` is neither."""
    if p.is_file():
        return {prefix: hashlib.sha256(p.read_bytes()).hexdigest()}
    fs = bundle_files(p, include) if p.is_dir() else []
    return {(f"{prefix.rstrip('/')}/{r}" if prefix else r): hashlib.sha256(f.read_bytes()).hexdigest() for r, f in fs}


def code_files(root: Path, reference, oracle, which: str) -> tuple[str | None, dict[str, str], dict[str, str]]:
    """(the path, each file's raw-byte SHA-256 by relative path, the declared suite files' share of them) of what an
    execution verification ran (task-0320, decision-0038 N-b), from a manifest's ``[reference]`` and ``[oracle]``
    tables: ``implementation``, ``[reference] code``, the files ``reference_code`` bundles; ``suite``, ``[oracle]
    script`` (a file one entry named '') and, task-0338 (decision-0039 §3.5), each path ``[oracle] suite`` lists in
    sorted path order, keyed by that path (a directory's files under it), one that holds no file keyed with the digest
    '', which no listing holds. (None, {}, {}) when the manifest declares none; ``[oracle] suite`` missing, the suite
    is the script alone, as before. One reading for the load (``Subject.code_parts``) and ``check_subject``."""
    table = reference if which == "implementation" else oracle
    rel = table.get("code" if which == "implementation" else "script") if isinstance(table, dict) else None
    if not isinstance(rel, str) or not rel:
        return None, {}, {}
    parts = _file_digests(root / rel, REFERENCE_INCLUDE if which == "implementation" else None, "")
    declared: dict[str, str] = {}
    for extra in suite_files(oracle) if which == "suite" else []:
        declared.update(_file_digests(root / extra, None, extra) or {extra: ""})
    return rel, {**parts, **declared}, declared


def bundle(root: Path, include: list[str] | None = None) -> str:
    """Every file ``bundle_files`` names, in path order, each prefixed by its marker line and ended
    by a newline (added when the file lacks one, so a part's text is not always its file's bytes)."""
    parts = []
    for rel, p in bundle_files(root, include):
        text = p.read_text(encoding="utf-8")
        parts.append(BUNDLE_MARK.format(rel=rel) + "\n" + text + ("" if text.endswith("\n") else "\n"))
    return "".join(parts)

HERE = Path(__file__).resolve().parent          # harness/
ROOT = HERE.parent                              # the repository
DEFAULT = ROOT / "subjects" / "cargo_quote"


def _toml(p: Path) -> dict:
    return tomllib.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


MANIFESTS = ("subject.toml", "scenarios.toml")   # what a reader of a subject watches for an edit (task-0206)


def stamp(root: Path) -> tuple:
    """Each manifest's (mtime, size), None for one that is not there: when it moves, a Subject built
    before it is stale (task-0206, doc-0030 P3)."""
    out = []
    for name in MANIFESTS:
        try:
            st = (Path(root) / name).stat()
            out.append((st.st_mtime_ns, st.st_size))
        except OSError:
            out.append(None)
    return tuple(out)


class Subject:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        if not (self.root / "subject.toml").exists():
            raise FileNotFoundError(f"{self.root} holds no subject.toml")
        self.stamp = stamp(self.root)   # read before the files, so an edit while they are read leaves it stale
        m = _toml(self.root / "subject.toml")
        import formats   # task-0174, decision-0023: one version for the root's configuration, a newer one refused
        self.format: int = formats.version(m, (self.root / "subject.toml").as_posix(), formats.SUBJECT)
        self.manifest = m
        s = m.get("subject", {})
        self.id: str = s.get("id", self.root.name)
        self.name: str = s.get("name", self.id)
        self.description: str = s.get("description", "")
        self.record_model: str = s.get("record_model", "")
        self.record_effort: str = s.get("record_effort", "")   # the reasoning effort the record's arms ran at; "" is the API default (task-0028)
        self.artefacts: list[dict] = list(m.get("artefact", []))
        sc = _toml(self.root / "scenarios.toml")
        import scenario_ids   # task-0295, decision-0034 choice 2: an id the pattern refuses, a duplicate or none stops the load
        scenario_ids.check(sc.get("scenario", []), (self.root / "scenarios.toml").as_posix())
        self.scenarios: dict[str, dict] = {x["id"]: x for x in sc.get("scenario", [])}
        self.order: list[str] = list(self.scenarios)
        pl = _toml(self.root / "plants.toml")
        self.plants: dict[str, list[dict]] = pl.get("plant", {})
        self.stage2_plants: dict[str, list[dict]] = pl.get("stage2", {})
        self.inferred: dict | None = pl.get("inferred")
        self.queries: list[dict] = list(_toml(self.root / "queries.toml").get("query", []))
        self.reference: dict = m.get("reference", {})
        self.oracle: dict = m.get("oracle", {})
        self.provenance: dict = m.get("provenance", {})
        self.verification: dict = m.get("verification", {})
        self.tasks: dict = m.get("tasks", {})
        self.arms: dict = m.get("arms", {})   # kind = "reply" (one JSON reply, the default) or "agent" (a tool loop; [arms.agent])
        import key_rule   # task-0301: the keys the three-valued answer measures, in NFC
        self.three_valued: list[str] = key_rule.normalise_all(list(m.get("three_valued", {}).get("keys", [])))
        self.rules: dict = m.get("rules", {})
        self.register: dict = m.get("register", {})
        self.page: dict = m.get("page", {})
        rec = m.get("record", {})
        # the record: <dir>/<scenario>/deterministic.json and the arms' run files; a subject that
        # has not been run has an empty or absent record/ and the page lists nothing to replay
        self.record_dir: Path = self.root / rec.get("dir", "record")
        # the date the record is read as of (decision-0005): a deterministic run and the comparator read
        # review currency on this date, so the record never moves by the clock; absent: today
        self.record_as_of: str | None = str(rec["as_of"]) if rec.get("as_of") else None
        # answered questionnaires, normalised by harness/capture.py ingest and read by every load (task-0009)
        self.capture_dir: Path = self.root / m.get("capture", {}).get("dir", "captures")

    # ---- paths and files
    def path(self, rel: str) -> Path:
        return self.root / rel

    @property
    def kit_files(self) -> list[tuple[str, Path]]:
        """(key, path) for every artefact that has bytes on disk, in manifest order; a path may be
        a directory (a bundle, see ``bundle``)."""
        return [(a["key"], self.root / a["path"]) for a in self.artefacts if a.get("path")]

    def artefact_text(self, key: str) -> str:
        a = next(x for x in self.artefacts if x["key"] == key)
        p = self.root / a["path"]
        return bundle(p, a.get("include")) if p.is_dir() else p.read_text(encoding="utf-8")

    @property
    def order_keys(self) -> list[str]:
        """Every artefact key, in the order the baseline arm concatenates them."""
        return [a["key"] for a in self.artefacts]

    @property
    def families(self) -> dict[str, tuple[str, str]]:
        return {a["key"]: (a["family"], a["format"]) for a in self.artefacts}

    @property
    def store_keys(self) -> set[str]:
        return {a["key"] for a in self.artefacts if a.get("store", True)}

    @property
    def mappers(self) -> dict[str, str]:
        return {a["key"]: a["mapper"] for a in self.artefacts if a.get("mapper")}

    @property
    def shorts(self) -> dict[str, str]:
        return {a["key"]: a["short"] for a in self.artefacts if a.get("short")}

    def raw_part_digests(self, key: str) -> dict[str, str]:
        """A directory artefact's files by relative path, each with the SHA-256 of its raw bytes as
        they are on disk (task-0098): what the register's digest of a cited file is taken over, and
        not the part's bundled text, which gains a newline a file lacks. A file artefact: empty."""
        a = next(x for x in self.artefacts if x["key"] == key)
        p = self.root / a["path"]
        if not p.is_dir():
            return {}
        return {rel: hashlib.sha256(f.read_bytes()).hexdigest() for rel, f in bundle_files(p, a.get("include"))}

    def version_digest(self, key: str, text: str) -> tuple[str, int]:
        """A Version's (SHA-256, bytes) for ``key`` as a scenario's kit holds it (``text``), task-0160: for a
        file artefact whose kit text is the file as read, unplanted, the digest and length of its raw bytes
        on disk, which is what the register's digest of a cited file is taken over (read_text turns CRLF
        into LF); for a planted text, which has no bytes on disk, a directory artefact's bundle (its files
        keep their own raw digests in ``part_digests``) or an artefact with no file, its text's (UTF-8)."""
        a = next((x for x in self.artefacts if x["key"] == key), None)
        p = self.root / a["path"] if a and a.get("path") else None
        if p is not None and p.is_file():
            raw = p.read_bytes()
            if raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n") == text:
                return hashlib.sha256(raw).hexdigest(), len(raw)
        enc = text.encode("utf-8")
        return hashlib.sha256(enc).hexdigest(), len(enc)

    def part_digests(self, key: str, text: str) -> dict[str, str]:
        """Each file of a directory artefact as a scenario's kit holds it (``text``, its bundle), by
        relative path (task-0094): the SHA-256 of the file's raw bytes on disk when the kit's part is the
        file as bundled, unplanted (task-0098: the bundle adds a newline a file lacks and reads text, so
        its part is not the bytes the register digests); a part a plant changed has no bytes on disk, so
        its digest is its text's (UTF-8)."""
        raw = self.raw_part_digests(key)
        on_disk = dict(bundle_parts(self.artefact_text(key))) if raw else {}
        return {rel: raw[rel] if rel in raw and on_disk.get(rel) == part else hashlib.sha256(part.encode("utf-8")).hexdigest()
                for rel, part in bundle_parts(text) if rel}

    def pristine(self) -> dict[str, str]:
        return {key: self.artefact_text(key) for key, _p in self.kit_files}

    def reference_code(self) -> str:
        """The code the oracle verified: one file, or a directory bundled as its ``*.py`` files."""
        rel = self.reference.get("code")
        if not rel:
            return ""
        p = self.path(rel)
        return bundle(p, REFERENCE_INCLUDE) if p.is_dir() else p.read_text(encoding="utf-8")

    def code_parts(self, which: str) -> tuple[str | None, dict[str, str]]:
        """(the path, each file's raw-byte SHA-256 by relative path) of what an execution verification ran (task-0320,
        decision-0038 N-b): ``implementation``, ``[reference] code``, the files ``reference_code`` bundles; ``suite``,
        ``[oracle] script``, the suite that judged it, with the files ``[oracle] suite`` lists (task-0338). Each digested
        as a directory artefact is (``bundle_files``, the load's own part selection; a file one entry named '');
        ``code_files``. (None, {}) when the subject declares none."""
        rel, parts, _declared = code_files(self.root, self.reference, self.oracle, which)
        return (None if rel is None else str(rel)), parts

    def require_code_inside(self) -> None:
        """task-0340 R2 (decision-0039 §3.5): ``[reference] code``, ``[oracle] script`` and each ``[oracle] suite`` path
        lie inside the instance (relative, at most ../../ up), as ``check_subject`` requires; else ``CodePathOutside``."""
        top = self.root.resolve().parent.parent
        for name, table, field in (("[reference] code", self.reference, "code"), ("[oracle] script", self.oracle, "script")):
            v = table.get(field) if isinstance(table, dict) else None
            paths = [(name, v)] if isinstance(v, str) and v else []
            paths += [("[oracle] suite", x) for x in suite_files(self.oracle)] if field == "script" else []
            for where, x in paths:
                if Path(x).is_absolute() or "\\" in x or not (self.root / x).resolve().is_relative_to(top):
                    raise CodePathOutside(f"{self.id}: {where} names {x}, which is not a relative path inside the subject's "
                                          "instance; the load digests no file outside it (decision-0039 §3.5)")

    def suite_declared(self) -> dict[str, str]:
        """The files ``[oracle] suite`` lists, each with its raw-byte SHA-256 ('' when it holds no file), by path."""
        return code_files(self.root, self.reference, self.oracle, "suite")[2]

    def oracle_script(self) -> Path | None:
        rel = self.oracle.get("script")
        return self.path(rel) if rel else None

    @property
    def suite_order(self) -> list[str]:
        return list(self.oracle.get("suite_order", []))

    def verification_map(self) -> dict:
        rel = self.verification.get("map")
        m = _toml(self.path(rel)) if rel else {}
        import key_rule   # task-0301: the keys it verifies in NFC, as the store holds them
        for scen, keys in list((m.get("execution") or {}).items()):
            m["execution"][scen] = key_rule.normalise_all(keys)
        if isinstance(m.get("review"), dict) and "keys" in m["review"]:
            m["review"]["keys"] = key_rule.normalise_all(m["review"]["keys"])
        return m

    def prompt(self, name: str) -> str:
        return (self.root / "prompts" / f"{name}.md").read_text(encoding="utf-8")

    def scenario(self, sc: str) -> dict:
        if sc not in self.scenarios:
            raise KeyError(f"{self.id}: no scenario {sc!r}; the subject declares {self.order or 'none'}")
        return self.scenarios[sc]

    def plants_for(self, sc: str, stage: int = 1) -> list[dict]:
        if stage == 2:
            return list(self.stage2_plants.get(sc, []))
        return list(self.plants.get(sc, []))

    def register_map(self) -> dict:
        rel = self.register.get("map")
        m = _toml(self.path(rel)) if rel else {}
        import key_rule   # task-0301: each row's key in NFC, as the store holds it
        for row in m.get("row", []) if isinstance(m.get("row"), list) else []:
            if isinstance(row, dict) and "key" in row:
                row["key"] = key_rule.normalise(row["key"])
        return m

    def definition_files(self) -> list[Path]:
        """Every file of the subject root that is not the record: what a run's SHA256SUMS lists."""
        out = []
        for p in sorted(self.root.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            if self.record_dir and p.is_relative_to(self.record_dir):
                continue
            out.append(p)
        return out


def load(root: str | os.PathLike | None = None) -> Subject:
    return Subject(Path(root or os.environ.get("KG_SUBJECT") or DEFAULT))


SUBJECT = load()

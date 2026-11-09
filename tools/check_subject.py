"""Check a subject root before it is loaded (task-0135; doc-0018 F2 to F5).

    python tools/check_subject.py <subject root> [--register DIR] [--json]

The layout check (tools/check_instance.py) confirms a subject loads and its documents exist. This
checks what loading does not: the manifest's own content, and the task's keys against what the
documents say. It reads and never writes; it opens no store.

- **The manifest** (F5). Every top-level table, and every field of `[subject]`, `[[artefact]]`,
  `[tasks.<class>]` and `[record]`, is one the loader reads; an unknown one is named with the
  nearest known name (`[task.codegen]`: did you mean `[tasks]`?). An artefact has `key`, `family`
  and `format`, keys are unique, and an artefact without a `path` is one a plant adds. A task has
  `keys` (a non-empty list), `block_levels` (gate levels) and `max_unverified_share` (0 to 1), and
  `require_approved`, when given, true or false (task-0215).
  A key, in a task, in `[three_valued]` or in a map row, is `<entity>|<predicate>`.
- **A scenario** (F3). A subject that declares a task declares at least one scenario: the gate
  runs on one and exits 2 on a subject that has none. `subjects/minimal/` declares the pristine `S0`.
- **The register map** (F4). Every node a row of `register_map.toml` names is in the register, and
  a row's `owner` is one of the owners of its nodes. A register named by `--register` or `KG_REGISTER`
  that cannot be read is exit 2, naming it, by every reader's one test, `register_impact.unreadable`
  (task-0279, task-0288 N10, decision-0033 choice 5); with neither named, the default `demo/register`, and
  the rows unchecked only when it cannot be read.
- **The documents' yield** (F2). Each artefact's mapper is run on the subject's own documents, in
  a child process (the harness binds its subject at import), and every task's required key is
  looked up in what they yield. A key no document yields, with a near match the documents do
  yield, is a warning naming that match: a misspelt key otherwise reads as `absent` at the gate and
  goes to an owner as a question. Each yielded key is offered once, to the required key it matches
  best; a match on another entity (``REQ-04|text`` beside ``REQ-03|text``) is a note, not a typo
  (task-0149, doc-0021 G2). A document its mapper reads and yields nothing from is a warning naming
  the mapper's convention (``instance/mappers.toml``) and the kind's other mappers: the wrong
  convention, not an empty document (G1). An artefact with a mapper and no ``short`` is refused,
  the fix its file's stem, since the mappers index by it (G5). A key with no near match is a note: the gate will read it absent
  unless a person's answer supplies it. A document whose statements are authored, in a subject that
  declares no `[verification] authored`, is a note too: they load proposed until a person attests
  them (decision-0009). A kit statement whose claim is not observed, inferred or intended is refused
  (rule `claim`, task-0214): the load would fail on it. The mappers need PyYAML; without it the yield
  is unchecked, and the report says so.

Exit 0 when nothing is refused (warnings and notes are for reading), 1 when the manifest is refused
(an unknown table or field, a missing required field or a mapped artefact's ``short``, no scenario for a task, a key that is not
`<entity>|<predicate>`, a map row naming a node the register does not hold or an owner of none of
its nodes, a mapper that cannot read its document, an unknown claim), 2 when the check cannot run (no such directory,
no subject.toml). The report as JSON (`--json`) is pinned by harness/schemas/subject-check.schema.json.
Standard library only; the yield's child process needs what the harness's mappers need.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import scenario_ids  # noqa: E402  (task-0295: the loader's own rule for scenario ids)
import task_policy  # noqa: E402  (task-0242, doc-0033 R1: the one task-policy validator, also the runtime's)
import key_rule  # noqa: E402  (task-0296: one entity|attribute rule, the gate's keys pattern too)
import formats  # noqa: E402  (task-0174, decision-0023: [format] version, standard library, binds no subject)
KINDS_TABLE = ROOT / "instance" / "kinds.toml"
MAPPERS_TABLE = ROOT / "instance" / "mappers.toml"   # what each mapper reads, in an adopter's words (task-0149)
DEFAULT_REGISTER = ROOT / "demo" / "register"
SCHEMA_VERSION = 1

# What the loader reads (harness/subject.py Subject, harness/gate.py, tools/vendor_subject.py)
TABLES = {"subject", "artefact", "reference", "oracle", "provenance", "verification", "arms", "tasks",
          "three_valued", "rules", "register", "page", "record", "capture", "vendor", "format"}
FORMAT_FIELDS = {"version"}   # task-0174: [format] version covers the subject root's configuration
SUBJECT_FIELDS = {"id", "name", "description", "record_model", "record_effort", "listed"}
ARTEFACT_FIELDS = {"key", "short", "family", "format", "label", "format_label", "path", "include", "mapper", "store"}
ARTEFACT_REQUIRED = ("key", "family", "format")
TASK_FIELDS = {"keys", "block_levels", "max_unverified_share", "verbatim", "rationale", "require_approved"}
TASK_REQUIRED = ("keys", "block_levels", "max_unverified_share")
RECORD_FIELDS = {"dir", "as_of"}
LEVELS = task_policy.LEVELS   # harness/gate.py ORDER (task-0242: one list, the validator's)
KEY_RE = key_rule.KEY_RE   # task-0296: the one key rule, the MCP tools' keys pattern too
NEAR = 0.8   # difflib ratio for a did-you-mean
YIELD_TIMEOUT = 300


def _near(word: str, known, cutoff: float = 0.6) -> str | None:
    m = difflib.get_close_matches(word, sorted(known), n=1, cutoff=cutoff)
    return m[0] if m else None


def _toml(p: Path) -> dict:
    return tomllib.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def kinds_mappers(path: Path = KINDS_TABLE) -> set[str]:
    return {m for k in _toml(path).get("kind", []) for m in k.get("mappers", [])}


def conventions(path: Path = MAPPERS_TABLE) -> dict[str, str]:
    """mapper -> what it reads (instance/mappers.toml)."""
    return {m: row.get("reads", "") for m, row in _toml(path).get("mapper", {}).items()}


def siblings(mapper: str, path: Path = KINDS_TABLE) -> list[str]:
    """The other mappers of the kind that holds ``mapper``."""
    for k in _toml(path).get("kind", []):
        if mapper in k.get("mappers", []):
            return [m for m in k["mappers"] if m != mapper]
    return []


def register_nodes(root: Path) -> dict[str, str] | None:
    """id -> owner for every node of the register's taxonomies, as the capture module's
    register_nodes reads them; None when the register cannot be read."""
    try:
        types = _toml(root / "metamodel" / "types.toml")
    except (OSError, tomllib.TOMLDecodeError):
        return None
    if not types.get("taxonomy"):
        return None
    out = {}
    for tax in types["taxonomy"]:
        for p in sorted((root / tax).glob("*.toml")):
            try:
                n = tomllib.loads(p.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError):
                continue
            if "id" in n:
                out[n["id"]] = n.get("owner", "")
    return out


class Report:
    def __init__(self, root: Path):
        self.root = root
        self.findings: list[dict] = []
        self.notes: list[dict] = []

    def error(self, rule: str, where: str, message: str, fix: str) -> None:
        self.findings.append({"level": "error", "rule": rule, "where": where, "message": message, "fix": fix})

    def warning(self, rule: str, where: str, message: str, fix: str) -> None:
        self.findings.append({"level": "warning", "rule": rule, "where": where, "message": message, "fix": fix})

    def note(self, rule: str, where: str, message: str) -> None:
        self.notes.append({"rule": rule, "where": where, "message": message})


def _scenario_ids(rep: Report, root: Path) -> None:
    """task-0295 (decision-0034 choice 2): every scenario has an id, ``[A-Za-z0-9][A-Za-z0-9_-]{0,31}``, its own within
    the subject; the loader refuses the subject on the first breach (``harness/scenario_ids.py``)."""
    for p in scenario_ids.problems(_toml(root / "scenarios.toml").get("scenario", [])):
        rep.error(p["code"], f"scenarios.toml {p['where']}", p["message"], p["hint"])


def _class_name(rep: Report, name, where: str) -> None:
    """task-0278 (decision-0033 choice 4): a class named ``keys``, or outside ``[a-z][a-z0-9_-]{0,31}``; the runtime
    refuses the manifest on it (``task_policy.build``)."""
    p = task_policy.name_problem(name)
    if p:
        rep.error(p["code"], where, p["message"], p["hint"])


def _fields(rep: Report, where: str, table: dict, known: set[str]) -> None:
    for f in table:
        if f not in known:
            near = _near(f, known)
            rep.error("field", where, f"{f!r} is not a field the loader reads; it is ignored",
                      f"rename it to {near!r}" if near else f"remove it; the fields are {', '.join(sorted(known))}")


def _key(rep: Report, where: str, key) -> bool:
    if isinstance(key, str) and KEY_RE.fullmatch(key):
        return True
    rep.error("key-syntax", where, f"{key!r} is not a key: a key is <entity>|<predicate>, one '|', no space and no control or format character (key_rule)",
              "write it as entity|predicate, as the mappers name it (REQ-01|text, QuoteAPI|notified)")
    return False


def check_manifest(rep: Report, m: dict, root: Path, mappers: set[str]) -> None:
    for t in m:
        if t not in TABLES:
            near = _near(t, TABLES)
            rep.error("table", f"[{t}]", f"[{t}] is not a table the loader reads; everything under it is ignored",
                      f"rename it to [{near}]" if near else f"remove it; the tables are {', '.join(sorted(TABLES))}")
    if isinstance(m.get("subject"), dict):
        _fields(rep, "[subject]", m["subject"], SUBJECT_FIELDS)
    if isinstance(m.get("record"), dict):
        _fields(rep, "[record]", m["record"], RECORD_FIELDS)
    if isinstance(m.get("format"), dict):
        _fields(rep, "[format]", m["format"], FORMAT_FIELDS)

    plants = _toml(root / "plants.toml")
    added = {p.get("path") for stage in ("plant", "stage2") for ps in plants.get(stage, {}).values()
             for p in ps if p.get("op") == "add"}
    seen: set[str] = set()
    shorts: dict[str, str] = {}
    for i, a in enumerate(m.get("artefact", [])):
        where = f"[[artefact]] #{i + 1}" + (f" {a['key']}" if isinstance(a.get("key"), str) else "")
        _fields(rep, where, a, ARTEFACT_FIELDS)
        for f in ARTEFACT_REQUIRED:
            if f not in a:
                rep.error("required", where, f"no {f!r}: the loader needs it", f"add {f} = \"...\" (subjects/README.md)")
        key = a.get("key")
        if isinstance(key, str):
            if key in seen:
                rep.error("duplicate", where, f"key {key!r} is declared twice", "give each artefact its own key")
            seen.add(key)
        sh = a.get("short")
        if isinstance(sh, str) and sh:   # I11: the load attributes a bag to its artefact by short
            if sh in shorts:
                rep.error("duplicate", where, f"short {sh!r} is {shorts[sh]}'s too: the load cannot tell their statements apart",
                          "give each artefact its own short (the file's stem, unique in the subject)")
            else:
                shorts[sh] = str(key)
        mapper = a.get("mapper")
        if mapper and not a.get("short"):   # G5: extract.short() indexes it; without it the load is a KeyError
            stem = Path(str(a.get("path") or key or "doc")).name.split(".")[0] or "doc"
            rep.error("required", where, "no 'short': the mappers name every statement by it, and without it the load fails "
                      "on a KeyError that reads as the document's fault",
                      f"add short = \"{stem}\" (the file's stem, unique in the subject)")
        if mapper and mapper not in mappers:
            near = _near(mapper, mappers)
            rep.error("mapper", where, f"mapper {mapper!r} is not a mapper the harness has",
                      f"use {near!r}" if near else f"use one of {', '.join(sorted(mappers))}, or none for a document the store does not read")
        if not a.get("path"):
            if key not in added:
                rep.error("required", where, "no 'path', and no plant adds the artefact", "add path = \"...\", relative to the subject root")
        elif not (root / a["path"]).exists():
            rep.error("path", where, f"{a['path']} does not exist", "fix the path; it is relative to the subject root")

    tasks = m.get("tasks", {})
    for name, t in (tasks.items() if isinstance(tasks, dict) else []):
        where = task_policy.table(name)
        _class_name(rep, name, where)
        if not isinstance(t, dict):
            rep.error("required", where, "not a table", f"write [tasks.{name}] with keys, block_levels and max_unverified_share")
            continue
        _fields(rep, where, t, TASK_FIELDS)
        for f in TASK_REQUIRED:
            if f not in t:
                rep.error("required", where, f"no {f!r}: the gate needs it", "copy it from subjects/minimal/subject.toml and adjust")
        for p in task_policy.problems(t):   # task-0242: the one validator the runtime builds the policy with
            if p["code"] == "block-level" and isinstance(p["value"], str) and isinstance(t.get("block_levels"), list):
                near = _near(p["value"], LEVELS)
                p["hint"] = f"use {near!r}" if near else p["hint"]
            rep.error(p["code"], where, p["message"], p["hint"])
        keys = t.get("keys")
        for k in keys if isinstance(keys, list) else []:
            if isinstance(k, str) and k:
                _key(rep, f"{where} keys", k)
    tv = m.get("three_valued", {})
    for k in tv.get("keys", []) if isinstance(tv, dict) else []:
        _key(rep, "[three_valued] keys", k)

    check_attestations(rep, m, root)
    check_bindings(rep, m, root)

    _scenario_ids(rep, root)
    if tasks and not _toml(root / "scenarios.toml").get("scenario"):
        rep.error("scenario", "scenarios.toml",
                  f"the subject declares task(s) {', '.join(sorted(tasks))} and no scenario: the gate runs on a scenario and exits 2 on this subject",
                  "add scenarios.toml with the pristine scenario subjects/minimal/scenarios.toml declares (S0, extraction = \"pristine\")")


ATTESTATIONS = ("authored", "approval", "review")   # [verification]: a person's acts by construction (decision-0009)


def _dated(v) -> bool:
    """An attestation's day, as the load reads it (``harness/load.py`` ``_day``): a date, YYYY-MM-DD, alone or
    with an ISO time (task-0262)."""
    import dates
    return dates.day(v) is not None


def check_attestations(rep: Report, m: dict, root: Path) -> None:
    """task-0199, doc-0030 I9: an attestation names its day and the subject its attester. The load applies an
    undated one, or one with no attester, to nothing (no load day and no default stands in for a person), so
    each is refused here: ``[verification] authored``, ``approval`` and ``review``, and a stage-2 re-verification."""
    ver = m.get("verification") if isinstance(m.get("verification"), dict) else {}
    prov = m.get("provenance") if isinstance(m.get("provenance"), dict) else {}
    human = prov.get("human") if isinstance(prov.get("human"), dict) else {}
    stage2 = [(f"scenarios.toml [scenario.stage2] of {sc.get('id', '#' + str(i + 1))}", sc["stage2"])
              for i, sc in enumerate(_toml(root / "scenarios.toml").get("scenario", []) or [])
              if isinstance(sc, dict) and isinstance(sc.get("stage2"), dict) and sc["stage2"].get("reverify_keys")]
    acts = [(f"[verification] {n}", ver[n]) for n in ATTESTATIONS if n in ver] + stage2
    for where, a in acts:
        if not isinstance(a, dict) or not _dated(a.get("at")):
            rep.error("attestation", where, "no 'at': an attestation is a person's act on a day, and the load neither dates it "
                      "by its own day nor applies it undated (doc-0030 I9)", 'add at = "YYYY-MM-DD", the day the person attested it')
    if acts and not human.get("id"):
        rep.error("attestation", "[provenance] human", f"{', '.join(w for w, _ in acts)} attest(s) with no attester: the manifest names "
                  "no [provenance] human id, and no default stands in for a person (decision-0009, doc-0030 I9)",
                  'add [provenance] human = { id = "agent:<who>", name = "..." }, the person who attests')


def subject_versions(m: dict, root: Path) -> set[str]:
    """The digests an artefact Version of the subject can carry (decision-0019): each artefact file's raw bytes and,
    for a directory, each file's, as on disk, and each text a scenario's patches make of a file (plants.toml, stage 1
    and 2), as the load digests a planted text. Read from the files alone, never a load."""
    import hashlib
    h = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
    out: set[str] = set()
    texts: dict[str, str] = {}               # a file artefact's text, or a directory's part: "<key><rel>"
    for a in m.get("artefact", []) if isinstance(m.get("artefact"), list) else []:
        if not isinstance(a, dict) or not a.get("path"):
            continue
        p = root / a["path"]
        if p.is_file():
            out.add(h(p.read_bytes()))
            texts[str(a.get("key"))] = p.read_text(encoding="utf-8")
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    out.add(h(f.read_bytes()))
                    t = f.read_text(encoding="utf-8", errors="replace")
                    texts[str(a.get("key")) + f.relative_to(p).as_posix()] = t if t.endswith("\n") else t + "\n"   # as bundled
    plants = _toml(root / "plants.toml")
    for stage in ("plant", "stage2"):
        for patches in (plants.get(stage) or {}).values():
            kit = dict(texts)
            for x in patches if isinstance(patches, list) else []:
                path = str(x.get("path")) + (str(x["within"]) if x.get("within") else "")   # a part a plant changes (task-0094)
                if x.get("op") == "add":
                    kit[path] = str(x.get("new", ""))
                elif x.get("op", "replace") == "replace" and path in kit:
                    kit[path] = kit[path].replace(str(x.get("old", "")), str(x.get("new", "")))
            out |= {h(t.encode("utf-8")) for k, t in kit.items() if texts.get(k) != t}
    return out


def check_bindings(rep: Report, m: dict, root: Path) -> None:
    """decision-0019 (task-0221): ``[verification] authored`` and ``approval`` list in ``versions`` the digest of each
    artefact Version they attest. A listed digest that is no Version of the subject is an error; a declaration with
    no list is the read rule's, attesting per load, and noted."""
    ver = m.get("verification") if isinstance(m.get("verification"), dict) else {}
    known = None
    for name in ("authored", "approval"):
        a = ver.get(name)
        if not isinstance(a, dict):
            continue
        where = f"[verification] {name}"
        listed = a.get("versions")
        if listed is None:
            rep.note("attestation", where, "lists no Version: it attests what the documents hold at each load, so an edit made "
                     "after it inherits it (decision-0009 (a), the read rule); list the digest of each Version it attests (decision-0019)")
            continue
        if not isinstance(listed, list) or not all(isinstance(d, str) and re.fullmatch(r"[0-9a-f]{64}", d) for d in listed):
            rep.error("attestation", where, "versions is not a list of SHA-256 digests (64 lower-case hex characters)",
                      "list each attested Version's digest, as the load records it (decision-0019)")
            continue
        known = subject_versions(m, root) if known is None else known
        for d in sorted(set(listed) - known):
            rep.error("attestation", where, f"versions lists {d}, which is no Version of the subject's artefacts: it attests "
                      "nothing the load reads", "list a digest of a document as it is, or as a scenario plants it (decision-0019)")


def check_map(rep: Report, m: dict, root: Path, register: Path | None) -> None:
    rel = (m.get("register") or {}).get("map", "register_map.toml") if isinstance(m.get("register"), dict) else "register_map.toml"
    p = root / rel
    if not p.is_file():
        return
    rows = _toml(p).get("row", [])
    nodes = register_nodes(register) if register else None
    if nodes is None:
        rep.note("map", rel, f"{len(rows)} row(s) unchecked against the register: no readable register"
                 + (f" at {register.as_posix()}" if register else ""))
    for i, row in enumerate(rows):
        where = f"{rel} row #{i + 1}" + (f" {row['key']}" if isinstance(row.get("key"), str) else "")
        if "key" not in row:
            rep.error("required", where, "no 'key'", "add key = \"entity|predicate\"")
        else:
            _key(rep, where, row["key"])
        if nodes is None:
            continue
        named = [n for n in row.get("nodes", []) if isinstance(n, str)]
        for n in named:
            if n not in nodes:
                near = _near(n, nodes, 0.8)
                rep.error("map-node", where, f"node {n} is not in the register: the key's owners and walk skip it silently",
                          f"name a node the register holds{f' (did you mean {near}?)' if near else ''}, or add the node to the register first")
        owner = row.get("owner")
        if owner:
            owners = sorted({nodes[n] for n in named if n in nodes and nodes[n]})
            if owner not in owners:
                rep.error("map-owner", where,
                          f"owner {owner} owns none of the row's nodes ({', '.join(owners) or 'no owner found'}): the questionnaire ignores it and goes to every owner",
                          f"name one of {', '.join(owners)}" if owners else "name the owner of one of the row's nodes")


def _yield_child(root: Path) -> dict:
    """In a child process with KG_SUBJECT set: each artefact's yield, as the load's mappers make it."""
    env = dict(os.environ, KG_SUBJECT=str(root), PYTHONDONTWRITEBYTECODE="1")
    try:
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--yield-only", str(root)],
                            capture_output=True, text=True, env=env, timeout=YIELD_TIMEOUT, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"state": "unchecked", "why": f"the mappers did not finish within {YIELD_TIMEOUT} s"}
    try:
        return json.loads(cp.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        tail = (cp.stderr.strip().splitlines() or ["no output"])[-1]
        return {"state": "unchecked", "why": f"the mappers could not run here: {tail}"}


def yield_only(root: Path) -> dict:
    """The child's side: run each artefact's mapper on the subject's own documents. No store."""
    sys.path.insert(0, str(ROOT / "harness"))
    try:
        import extract  # noqa: PLC0415  binds KG_SUBJECT, which the parent set
        from subject import SUBJECT  # noqa: PLC0415
    except ModuleNotFoundError as e:
        return {"state": "unchecked", "why": f"the mappers need {e.name}, which is not installed here"}
    try:
        code = SUBJECT.reference_code()
    except (OSError, StopIteration, KeyError):
        code = ""
    arts, failed, claims, authored, dups, missing_mod = {}, {}, {}, [], {}, None
    for key, p in SUBJECT.kit_files:
        mapper = SUBJECT.mappers.get(key)
        if not mapper or not p.exists() or key not in SUBJECT.shorts:   # no short: refused by the manifest check (G5)
            continue
        try:
            text = SUBJECT.artefact_text(key)
            bag = extract.extract_links(key, text, code) if mapper == "links" else extract.EXTRACTORS[mapper](key, text)
        except ModuleNotFoundError as e:
            missing_mod = e.name
            continue
        except extract.UnknownClaim as e:   # task-0214: a claim the kit format does not know
            claims[key] = str(e)
            continue
        except Exception as e:  # noqa: BLE001 — a mapper that cannot read its document is the finding
            failed[key] = f"{type(e).__name__}: {e}"
            continue
        if dup := extract.duplicate_locators(bag):   # I11: a duplicated row, which the load refuses
            dups[key] = dup
        arts[key] = sorted({f"{a['entity']}|{a['predicate']}" for a in bag.assertions})
        if any(a.get("basis") == "authored" for a in bag.assertions):
            authored.append(key)
    out = {"state": "checked", "why": None, "artefacts": arts, "failed": failed, "claims": claims, "authored": authored,
           "duplicate_locators": dups}
    if missing_mod:
        out["why"] = f"some mappers need {missing_mod}, which is not installed here; their artefacts are unchecked"
    return out


def _offers(wanted: list[str], yielded: set[str]) -> dict[str, str]:
    """Each yielded key offered once, to the required key it matches best (G2): a pair at NEAR or above,
    the closest first, neither side reused."""
    pairs = sorted(((difflib.SequenceMatcher(None, k, y).ratio(), k, y) for k in wanted for y in yielded), reverse=True)
    out: dict[str, str] = {}
    used: set[str] = set()
    for r, k, y in pairs:
        if r < NEAR:
            break
        if k not in out and y not in used:
            out[k] = y
            used.add(y)
    return out


def check_yield(rep: Report, m: dict, root: Path) -> dict:
    y = _yield_child(root)
    if y.get("state") != "checked":
        rep.note("yield", "documents", f"yield unchecked: {y.get('why')}")
        return {"state": "unchecked", "why": y.get("why"), "keys": 0, "artefacts": {}}
    arts: dict[str, list[str]] = y.get("artefacts", {})
    partial = bool(y.get("why"))
    if partial:   # a key an unchecked artefact would yield must not read as a misspelling
        rep.note("yield", "documents", f"{y['why']}; the task keys are not compared with a partial yield")
    for key, why in sorted(y.get("failed", {}).items()):
        rep.error("mapper-failed", f"[[artefact]] {key}", f"its mapper cannot read it: {why}; the load fails on it",
                  "fix the document, or give the artefact the mapper of its convention (instance/kinds.toml)")
    for key, dup in sorted(y.get("duplicate_locators", {}).items()):   # doc-0030 I11
        rep.error("duplicate", f"[[artefact]] {key}",
                  f"{len(dup)} locator(s) appear twice ({', '.join(dup[:5])}): a duplicated row, so the load would write one "
                  "fragment twice and fails on it", "remove or renumber the duplicated row, so each statement's evidence has its own place")
    for key, why in sorted(y.get("claims", {}).items()):   # task-0214, decision-0018 point 3
        rep.error("claim", f"[[artefact]] {key}", f"{why}; the load fails on it rather than guess what the statement is",
                  "write observed, inferred or intended, or leave the claim out so the statement loads as before "
                  "(subjects/README.md, \"The claim\")")
    yielded = set().union(*arts.values()) if arts else set()
    mapper_of = {a.get("key"): a.get("mapper") for a in m.get("artefact", []) if isinstance(a, dict)}
    conv = conventions()
    for key, got in sorted(arts.items()):   # G1: a document its mapper reads and yields nothing from
        mapper = mapper_of.get(key)
        if got or not mapper:
            continue
        others = siblings(mapper)
        rep.warning("zero-yield", f"[[artefact]] {key}",
                    f"mapper {mapper!r} read it and yielded no key: the document is most likely not in the convention "
                    f"{mapper} reads ({conv.get(mapper) or 'see harness/extract.py'}), not empty of knowledge",
                    (f"try the kind's other mapper(s), {', '.join(others)}, and keep the one that yields; " if others else "")
                    + "if none does, leave mapper out so the document is reported ABSENT (a mapper request), "
                      "and never rewrite the document's ids or wording to suit a mapper")
    ver = m.get("verification") if isinstance(m.get("verification"), dict) else {}
    if y.get("authored") and not ver.get("authored"):   # decision-0009 (a): no attestation, no review by construction
        rep.note("attestation", "[verification]",
                 f"{', '.join(y['authored'])} hold authored statements and the manifest declares no [verification] authored: "
                 "they load proposed until a person attests them (decision-0009)")
    tasks = m.get("tasks", {}) if isinstance(m.get("tasks"), dict) else {}
    required = {k for t in tasks.values() if isinstance(t, dict) for k in (t.get("keys") or []) if isinstance(k, str)}
    best = {} if partial else _offers(sorted(k for k in required if KEY_RE.fullmatch(k) and k not in yielded), yielded - required)
    for name, t in sorted(tasks.items()):
        if not isinstance(t, dict) or partial:
            continue
        for k in t.get("keys") or []:
            if not isinstance(k, str) or not KEY_RE.fullmatch(k) or k in yielded:
                continue
            near = best.get(k)
            if near and near.split("|", 1)[0] != k.split("|", 1)[0]:   # G2: another entity's key is not a typo
                rep.note("unyielded", f"[tasks.{name}] keys",
                         f"{k}: no document states it; the nearest key the documents yield, {near}, is another entity's, "
                         "so it is not a misspelling: the gate reads the key absent and asks its owner")
            elif near:
                rep.warning("yield", f"[tasks.{name}] keys",
                            f"{k}: no document yields this key, and the gate will read it absent and ask an owner for it",
                            f"did you mean {near}? the documents yield it")
            else:
                rep.note("unyielded", f"[tasks.{name}] keys",
                         f"{k}: no document yields it; the gate reads it absent unless a person's answer supplies it")
    return {"state": "checked", "why": y.get("why"), "keys": len(yielded), "artefacts": {k: len(v) for k, v in arts.items()}}


def check(root: Path, register: Path | None = None, mappers: set[str] | None = None, run_yield: bool = True) -> dict:
    """The report for one subject root. Reads only; opens no store; writes nothing."""
    root = Path(root)
    rep = Report(root)
    out = {"schema_version": SCHEMA_VERSION, "tool": "check_subject", "subject": root.name, "root": root.as_posix(),
           "findings": rep.findings, "notes": rep.notes,
           "yield": {"state": "unchecked", "why": "not run", "keys": 0, "artefacts": {}}, "exit_code": 0}
    try:
        m = tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        rep.error("manifest", "subject.toml", f"not valid TOML: {e}", "fix the syntax the message names")
        out["exit_code"] = 1
        return out
    # task-0174, decision-0023: the root's format version, missing read as current, a newer one refused
    # (FormatTooNew: the command exits 2, the instance check and the MCP subject_check refuse the call)
    out["format"] = formats.version(m, (root / "subject.toml").as_posix(), formats.SUBJECT)
    sub = m.get("subject") if isinstance(m.get("subject"), dict) else {}
    out["subject"] = sub.get("id", root.name)
    check_manifest(rep, m, root, mappers if mappers is not None else kinds_mappers())
    check_map(rep, m, root, register)
    if run_yield:
        out["yield"] = check_yield(rep, m, root)
    out["exit_code"] = 1 if any(f["level"] == "error" for f in rep.findings) else 0
    return out


def render(rep: dict) -> str:
    out = [f"subject {rep['subject']} ({rep['root']})"]
    y = rep["yield"]
    out.append(f"yield: {y['keys']} key(s) from {len(y['artefacts'])} artefact(s)" if y["state"] == "checked"
               else f"yield: unchecked ({y['why']})")
    for f in rep["findings"]:
        out.append(f"{f['level'].upper()} {f['where']}: {f['message']}. Fix: {f['fix']}")
    for n in rep["notes"]:
        out.append(f"NOTE {n['where']}: {n['message']}")
    errs = sum(f["level"] == "error" for f in rep["findings"])
    out.append("manifest holds" if not errs else f"manifest refused: {errs} error(s)")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a subject root before it is loaded.")
    ap.add_argument("root", type=Path)
    ap.add_argument("--register", type=Path, default=None,
                    help="the register the map rows are checked against (default: KG_REGISTER, else demo/register); "
                         "a named register that cannot be read exits 2")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--yield-only", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.yield_only:
        print(json.dumps(yield_only(args.root)))
        return 0
    if not (args.root / "subject.toml").is_file():
        print(f"cannot run: {args.root} holds no subject.toml", file=sys.stderr)
        return 2
    register = args.register or Path(os.environ.get("KG_REGISTER") or DEFAULT_REGISTER)
    by = "--register" if args.register else "KG_REGISTER" if os.environ.get("KG_REGISTER") else None
    if by:   # task-0279 (decision-0033 choice 5): a register named and not readable exits 2; unchecked is for none named
        import register_impact
        why = register_impact.unreadable(register)   # task-0288 (N10): the readers' one test, the register's own loader included
        if why:
            print(f"cannot run: {by} {register.as_posix()} is not a readable register: {why}", file=sys.stderr)
            return 2
    try:
        rep = check(args.root, register)
    except formats.FormatError as e:   # task-0174: written for a newer knowgov, or no version: cannot run
        print(f"cannot run: {e}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=1) if args.json else render(rep))
    return rep["exit_code"]


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))

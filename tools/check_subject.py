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
    why = key_rule.refusal(key)   # task-0316: as written and in NFC, the value named as written
    if why is None:
        return True
    rep.error("key-syntax", where, why,
              "write it as entity|predicate, as the mappers name it (REQ-01|text, QuoteAPI|notified)")
    return False


def _task_keys(rep: Report, where: str, keys, empty: bool = False) -> None:
    """Each key of a task class by the one rule; a key listed twice, equal after NFC, warned (task-0309 B4)."""
    once: set[str] = set()
    for k in keys if isinstance(keys, list) else []:
        if isinstance(k, str) and (k or empty):   # a task class's empty key is the policy's 'required'
            _key(rep, where, k)
            if key_rule.normalise(k) in once:
                rep.warning("duplicate", where, f"key {k!r} is listed twice (equal after NFC); the gate merges them", "list each key once")
            once.add(key_rule.normalise(k))


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
        _task_keys(rep, f"{where} keys", keys)
    tv = m.get("three_valued", {})
    _task_keys(rep, "[three_valued] keys", tv.get("keys") if isinstance(tv, dict) else None, empty=True)

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


def artefact_digests(m: dict, root: Path) -> dict[str, dict[str, str]]:
    """Each artefact's current Version files as on disk, by name then raw-byte SHA-256: a file artefact one entry
    named '', a directory artefact the files the load bundles (``subject.bundle_files`` with the artefact's
    ``include``, the load's own part selection, as ``Subject.raw_part_digests`` digests them; task-0319)."""
    import hashlib
    from subject import bundle_files
    out: dict[str, dict[str, str]] = {}
    for a in m.get("artefact", []) if isinstance(m.get("artefact"), list) else []:
        if not isinstance(a, dict) or not a.get("path"):
            continue
        p = root / a["path"]
        inc = a.get("include") if isinstance(a.get("include"), list) else None
        fs = [("", p)] if p.is_file() else bundle_files(p, inc) if p.is_dir() else []
        if fs:
            out[str(a.get("key") or a["path"])] = {rel: hashlib.sha256(f.read_bytes()).hexdigest() for rel, f in fs}
    return out


def _patched(texts: dict, patches) -> dict:
    """``texts`` with one scenario's patches applied, as the load applies them."""
    kit = dict(texts)
    for x in patches if isinstance(patches, list) else []:
        path = str(x.get("path")) + (str(x["within"]) if x.get("within") else "")   # a part a plant changes (task-0094)
        if x.get("op") == "add":
            kit[path] = str(x.get("new", ""))
        elif x.get("op", "replace") == "replace" and path in kit:
            kit[path] = kit[path].replace(str(x.get("old", "")), str(x.get("new", "")))
    return kit


def _planted_versions(plants: dict, texts: dict, h, out: set, planted: dict | None) -> None:
    """The digests of the texts each scenario's patches make (``subject_versions``), added to ``out``."""
    for stage in ("plant", "stage2"):
        for patches in (plants.get(stage) or {}).values():
            kit = _patched(texts, patches)
            made = {h(t.encode("utf-8")): k for k, t in kit.items() if texts.get(k) != t}
            out.update(made)
            if planted is not None:
                planted.update(made)


def subject_versions(m: dict, root: Path, planted: dict | None = None) -> set[str]:
    """The digests an artefact Version of the subject can carry (decision-0019): each artefact file's raw bytes and,
    for a directory, each file's, as on disk, and each text a scenario's patches make of a file (plants.toml, stage 1
    and 2), as the load digests a planted text. Read from the files alone, never a load. ``planted``, when given, receives
    each planted digest's artefact key (task-0312 F2)."""
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
    _planted_versions(_toml(root / "plants.toml"), texts, h, out, planted)
    return out


BOUND = ("execution", "review")   # decision-0036 (task-0306): verifications bound to the Versions listed, no read rule


def check_bindings(rep: Report, m: dict, root: Path) -> None:
    """decision-0019 (task-0221): ``[verification] authored`` and ``approval`` list in ``versions`` the digest of each
    artefact Version they attest; one with no list is the read rule's, attesting per load, and noted. decision-0036
    (task-0306): ``execution`` and ``review`` are bound the same way with no read rule, so one that lists nothing, or a
    subject whose map has suite scenarios and no ``execution`` declaration, verifies nothing, and that is noted. A
    listed digest that is no Version of the subject is an error."""
    ver = m.get("verification") if isinstance(m.get("verification"), dict) else {}
    known: list = [None]
    if ver and (ver.get("map") or ver.get("derive_execution")) and not isinstance(ver.get("execution"), dict):
        rep.note("attestation", "[verification] execution", "is not declared: nothing is verified by execution, since no suite "
                 "runs at load; list the Versions the suite's result was attested on in execution = { versions = [...] } (decision-0036)")
    for name in ("authored", "approval", *BOUND):
        a = ver.get(name)
        if isinstance(a, dict):
            _check_versions(rep, m, root, name, a.get("versions"), known)
    check_oracle_suite(rep, m, root)
    check_code_paths(rep, m)
    check_execution_code(rep, m, root, ver.get("execution"))


EXECUTED = (("implementation", "reference", "code"), ("suite", "oracle", "script"))   # task-0320, decision-0038 N-b


def code_digests(m: dict, root: Path, which: str) -> tuple[str | None, dict[str, str]]:
    """(the path, its files' raw-byte SHA-256 by relative path) of what an execution ran, as the load digests it
    (``subject.code_files``, ``Subject.code_parts``'s own reading: ``[reference] code`` with the files ``reference_code``
    bundles, ``[oracle] script`` whole with each file ``[oracle] suite`` lists, task-0338; a file one entry named '',
    a listed suite file holding none the digest ''). (None, {}) when the manifest names none."""
    from subject import code_files
    rel, files, _declared = code_files(root, m.get("reference"), m.get("oracle"), which)
    return rel, files


def _script_in_suite(rep: Report, o: dict, v: list) -> None:
    """task-0340 R4: the script is also a path ``[oracle] suite`` lists, which binds it twice and says nothing more."""
    s = o.get("script")
    if isinstance(s, str) and s in v:
        rep.note("attestation", "[oracle] suite", f"also lists the script {s}, which the suite digest binds already; list the files the script reads beside it")


def _suite_refusal(v) -> str:
    """L5: why ``[oracle] suite`` is not a list of paths, naming the entry that is not one."""
    if not isinstance(v, list):
        return "is not a list of paths" + (f" (it is the string {v!r}): write suite = [{v!r}]" if isinstance(v, str) else f" (it is {v!r})")
    bad = next((i, x) for i, x in enumerate(v) if not (isinstance(x, str) and x))
    return f"is not a list of paths (strings, relative to the subject root): entry {bad[0]} ({bad[1]!r}) is not a path"


def check_oracle_suite(rep: Report, m: dict, root: Path) -> None:
    """task-0338 (decision-0039 §3.5): ``[oracle] suite``, optional, lists the files the suite reads beside its script
    (its expectations), each digested into ``[verification] execution``'s ``suite``; each a relative path inside the
    subject's instance (at most ../../ up, as a document's) that holds a file or a directory."""
    o = m.get("oracle") if isinstance(m.get("oracle"), dict) else {}
    if "suite" not in o:
        return
    v, where = o["suite"], "[oracle] suite"
    if not isinstance(v, list) or not all(isinstance(x, str) and x for x in v):
        rep.error("path", where, _suite_refusal(v),   # L5: the entry named
                  'list the files the suite reads beside its script, e.g. suite = ["tests/expectations.py"]')
        return
    _script_in_suite(rep, o, v)
    for x in sorted(set(v)):
        p = Path(x)
        inside = not p.is_absolute() and "\\" not in x and (root / p).resolve().is_relative_to(root.resolve().parent.parent)
        if not inside:
            rep.error("path", where, f"{x} is not a relative path inside the subject's instance",
                      "name it relative to the subject root, at most ../../ up")
        elif not (root / p).exists():
            rep.error("path", where, f"{x} does not exist", "fix the path; it is relative to the subject root")
        elif (out := _escaping(root, x)):   # L8
            rep.error("path", where, f"{x} holds {out}, which resolves outside the subject's instance",
                      "remove the link, or copy the file into the instance")


def check_code_paths(rep: Report, m: dict) -> None:
    """L4: ``[reference] code`` and ``[oracle] script`` are a path string or absent; the load refuses anything else (exit 2)."""
    for table, field in (("reference", "code"), ("oracle", "script")):
        sec = m.get(table) if isinstance(m.get(table), dict) else {}
        v = sec.get(field)
        if v is not None and not isinstance(v, str):
            rep.error("path", f"[{table}] {field}", f"is {v!r}, not a path (a string relative to the subject root)",
                      "name it relative to the subject root")


def check_execution_code(rep: Report, m: dict, root: Path, ex) -> None:
    """decision-0038 N-b (task-0320): an execution verification binds to the reference implementation and the suite that
    judged it as well as to the documents, so ``[verification] execution`` lists in ``implementation`` and ``suite`` the
    raw-byte digest of each file of ``[reference] code`` and ``[oracle] script`` the subject declares. A list left out
    is a warning (the load then verifies nothing by execution); a file it does not list as it is now is an error."""
    if not isinstance(ex, dict) or ex.get("versions") is None:
        return
    for which, table, field in EXECUTED:
        _execution_listing(rep, m, root, ex, which, table, field)


def _owner(m: dict, which: str, table: str, field: str, rel: str) -> str:
    """S3: the field that owns a listed digest, the suite's with each file ``[oracle] suite`` lists (task-0338)."""
    from subject import suite_files
    return f"[{table}] {field} {rel}" + (" or a file [oracle] suite lists" if which == "suite" and suite_files(m.get("oracle")) else "")


def _escaping(root: Path, named) -> str | None:
    from subject import escaping_file
    return escaping_file(root, named) if isinstance(named, str) and named else None


def _outside(rep: Report, m: dict, root: Path, table: str, field: str) -> bool:
    """S2: a path outside the instance is refused as the load refuses it (``require_code_inside``); True when it was."""
    sec = m.get(table) if isinstance(m.get(table), dict) else {}
    named = sec.get(field)
    if not (isinstance(named, str) and named and (Path(named).is_absolute() or "\\" in named
                                                  or not (root / named).resolve().is_relative_to(root.resolve().parent.parent))):
        out = _escaping(root, named)   # L8
        if not out:
            return False
        rep.error("path", f"[{table}] {field}", f"{named} holds {out}, which resolves outside the subject's instance",
                  "remove the link, or copy the file into the instance")
        return True
    rep.error("path", f"[{table}] {field}", f"{named} is not a relative path inside the subject's instance",
              "name it relative to the subject root, at most ../../ up")
    return True


def _execution_listing(rep: Report, m: dict, root: Path, ex: dict, which: str, table: str, field: str) -> None:
    where = "[verification] execution"
    if _outside(rep, m, root, table, field):
        return
    rel, files = code_digests(m, root, which)
    if rel is None:
        return
    rel = rel or "(an empty path)"   # L7
    listed = ex.get(which)
    now = sorted(set(files.values()) - {""})
    if listed is None:
        rep.warning("attestation", where, f"lists no {which} digests: the load verifies nothing by execution, since an "
                    f"execution binds to the [{table}] {field} it ran on ({rel}) as well as to the documents (decision-0038)",
                    f"after the suite has run on it, add {which} = {json.dumps(now)}")
        return
    if not isinstance(listed, list) or not all(isinstance(d, str) and re.fullmatch(r"[0-9a-f]{64}", d) for d in listed):
        rep.error("attestation", where, f"{which} is not a list of SHA-256 digests (64 lower-case hex characters)",
                  f"list each file's raw-byte digest: {which} = {json.dumps(now)}")
        return
    miss = {r: d for r, d in sorted(files.items()) if not d or d not in listed}
    stale = sorted(d for d in listed if d not in set(files.values()))   # task-0340 R1, as a document's "matches no current Version"
    owner = _owner(m, which, table, field, rel)
    if len(stale) > len(miss):   # more listed digests gone than files changed: a deletion
        rep.error("attestation", where, f"{which} lists {', '.join(stale)}, which matches no current file of {owner}: a file was deleted or changed, so the load verifies nothing by execution (decision-0038)",
                  "run the suite again and list the digests of the files as they are, or restore the file")
    if miss or (not files and not stale):
        also = owner[len(f"[{table}] {field} {rel}"):]   # task-0338
        gone = f"; {which} still lists {', '.join(stale)}, which matches no current file" if stale and len(stale) <= len(miss) else ""   # S3
        rep.error("attestation", where, f"[{table}] {field} {rel}{also} changed since the execution was attested: "
                  f"{_unlisted(miss)} is not listed under {which}{gone}, so the load verifies nothing by execution (decision-0038)",
                  "run the suite on it again and list the new digest, or restore it")


def _unlisted(miss: dict[str, str]) -> str:
    """The files an execution listing misses: a directory's part or an ``[oracle] suite`` file by its path and digest
    (one holding no file said so), the script or a one-file implementation as its file."""
    return ", ".join((f"{r} ({d})" if d else f"{r} (no file there)") if r else f"its file {d}" for r, d in miss.items()) or "no file is there"


def _relist_fix(name: str, restore: bool = False) -> str:
    """task-0324, task-0330: the fix per declaration. Execution means something only if the implementation and the suite
    were changed to the new Version's values and run; approval and review are the approver's and the reviewer's own acts
    (decision-0002: not the author's); authored is the author's."""
    if name == "execution":
        step = ("bring the reference implementation and the suite in line with the new Version where its values differ, run the "
                "suite on it, then list all three digests (replace the old digest with the new one under versions, then the "
                "implementation, the suite); where the values differ and they are unchanged, re-listing only asserts the old "
                "result for the new values (no oracle runs at load; decision-0038)")
    elif name == "review":
        step = ("the reviewer (not the author, decision-0002) reads the new Version and replaces the old digest with the new "
                "one (decision-0019); for a single document's re-review, the capture tool's `review` command gives it its own date, since one "
                "`at` re-dates every listed Version")
    elif name == "approval":
        step = "the approver (not the author, decision-0002) reads the new Version; to re-attest, replace the old digest with the new one (decision-0019)"
    else:
        step = "the author reads the new Version; to re-attest, replace the old digest with the new one (decision-0019)"
    return step + (", or restore the document" if restore else ", or remove it")


def _unchanged_code_note(rep: Report, m: dict, root: Path) -> None:
    """task-0330: a document edit seen under ``[verification] execution`` (a listed digest that matches no current Version,
    or an artefact that changed since it was attested) while the implementation and suite digests listed equal the files on
    disk: knowgov cannot know whether the suite covers the change. A note, never an error."""
    ex = (m.get("verification") or {}).get("execution") if isinstance(m.get("verification"), dict) else None
    if not isinstance(ex, dict):
        return
    for which, _t, _f in EXECUTED:
        rel, files = code_digests(m, root, which)
        listed = ex.get(which)
        if rel is None or not files or not isinstance(listed, list) or any(d not in listed for d in files.values()):
            return
    rep.note("attestation", "[verification] execution", "a document was edited since it was attested (an old digest is still listed, or the "
             "artefact changed) while the implementation and suite digests are the files as they are: knowgov cannot know "
             "whether the suite covers the change, so listing the new digest would assert the old result for the new values "
             "unless the implementation and suite were changed and run (decision-0038)")


def _edited(rep: Report, m: dict, root: Path, name: str, listed: list, stale: list) -> bool:
    """True when an artefact changed since it was attested (``_changed_artefacts``); under execution an edit seen, as a stale
    listed digest or a changed artefact, adds task-0330's note on unchanged code."""
    named = _changed_artefacts(rep, m, root, f"[verification] {name}", listed, len(stale))
    if name == "execution" and (stale or named):
        _unchanged_code_note(rep, m, root)
    return named


def _no_version_note(rep: Report, where: str, name: str) -> None:
    rep.note("attestation", where, "lists no Version: it verifies nothing, since an execution or a review "
             "verification holds only for the Versions it lists (decision-0036); list the digest of each Version it verifies, "
             "each document's under versions" + (", with the implementation and suite digests" if name == "execution" else "") + ".")


def _listed_files(m: dict, root: Path, listed: list) -> str:
    """Which listed digests are which file (task-0315 C2-7: a bare digest names no file), as message text."""
    files = {d: f"{art}/{rel}" if rel else art for art, fs in sorted(artefact_digests(m, root).items()) for rel, d in fs.items()}
    return ", ".join(f"{d} is {files[d]}" for d in listed if d in files)


def _stale_errors(rep: Report, where: str, name: str, stale: list, held: str, plants: str = "") -> None:
    """One error per stale digest; the listed digests that do match a file are named once per declaration (L6), and
    each says it may have been a scenario plant's Version, with the Version that plant makes now (task-0312 R6)."""
    for i, d in enumerate(stale):
        rep.error("attestation", where, f"versions lists {d}, which matches no current Version of the subject's artefacts"
                  + (f" (the listed digests that do match a file: {held})" if held and i == 0 else "") + plants
                  + ": it attests nothing the load reads", _relist_fix(name))


def _check_versions(rep: Report, m: dict, root: Path, name: str, listed, known: list) -> None:
    where = f"[verification] {name}"
    if listed is None or (name in BOUND and listed == []):   # task-0318: an empty list verifies nothing either
        if name in BOUND:
            _no_version_note(rep, where, name)
        else:
            rep.note("attestation", where, "lists no Version: it attests what the documents hold at each load, so an edit made "
                     "after it inherits it (decision-0009 (a), the read rule); list the digest of each Version it attests (decision-0019)")
        return
    if listed == []:   # task-0319 E2: authored or approval bound to nothing
        rep.note("attestation", where, "lists an empty set of Versions: it attests nothing, since a bound attestation holds "
                 "only for the Versions it lists (decision-0019); list the digest of each Version it attests")
        return
    if not isinstance(listed, list) or not all(isinstance(d, str) and re.fullmatch(r"[0-9a-f]{64}", d) for d in listed):
        rep.error("attestation", where, "versions is not a list of SHA-256 digests (64 lower-case hex characters)",
                  "list each attested Version's digest, as the load records it (decision-0019)")
        return
    known[0] = subject_versions(m, root) if known[0] is None else known[0]
    stale = sorted(set(listed) - known[0])
    if _edited(rep, m, root, name, listed, stale):   # task-0318, task-0319: the edit, by artefact and file
        return
    _stale_errors(rep, where, name, stale, _listed_files(m, root, listed), _plant_hint(m, root, listed, stale))
    _unlisted_plants(rep, m, root, where, listed, name)


def _plant_gaps(m: dict, root: Path, listed: list) -> list[tuple[str, str]]:
    """task-0312 F2, R3: (artefact, digest) of each Version a scenario's plant makes of an artefact whose own Versions the
    declaration lists but whose plant's it does not. The plant's artefact is the exact key, else the longest key it
    extends (a directory's part is named "<key><path>")."""
    planted: dict[str, str] = {}
    subject_versions(m, root, planted)
    own = artefact_digests(m, root)
    out = []
    for d, k in sorted(planted.items(), key=lambda kv: kv[1]):
        art = k if k in own else max((a for a in own if k.startswith(a)), key=len, default=None)
        if d not in listed and art is not None and all(x in listed for x in own[art].values()):
            out.append((art, d))
    return out


def _plant_hint(m: dict, root: Path, listed: list, stale: list) -> str:
    """task-0312 R6: for a stale digest, that it may have been a scenario plant's Version of an edited document, and the
    Version that plant makes now."""
    gaps = _plant_gaps(m, root, listed) if stale else []
    return ("; if it was a scenario plant's Version of " + ", ".join(sorted({a for a, _ in gaps})) + ", that plant now makes "
            + ", ".join(sorted(d for _, d in gaps))) if gaps else ""


def _unlisted_plants(rep: Report, m: dict, root: Path, where: str, listed: list, name: str) -> None:
    """task-0312 F2: an artefact whose own Versions the declaration lists, but not the Version a scenario's plant makes of
    it, attests the pristine document and fails the scenario at the load: name each, with the digest to list."""
    for art, d in _plant_gaps(m, root, listed):
        rep.error("attestation", where, f"a scenario plant of {art} makes the Version {d}, which is not listed under {where}: "
                  "the scenario loads it unattested", f"list {d} under {where} (the plant's text, as the load digests it)")


def _changed_artefacts(rep: Report, m: dict, root: Path, where: str, listed: list, stale: int) -> bool:
    """One error per artefact whose Version this declaration lists in part or, once it lists a digest no Version has any
    more, does not list as it is now (task-0318, task-0319): the artefact changed since it was attested. A directory
    artefact listed in part has a file added or changed, and the error names it. The artefacts it lists not at all are
    named only when their files together fit the digests it lists that no Version has any more (``stale``, a count), as
    they may never have been attested; otherwise none of them is, and the per-digest errors say what is stale (task-0312
    F1, R4, L1). True when it named at least one."""
    parts, wholes = [], []
    for art, files in sorted(artefact_digests(m, root).items()):
        miss = {rel: d for rel, d in files.items() if d not in listed}
        if miss:
            (wholes if len(miss) == len(files) else parts).append((art, files, miss))
    if sum(len(f) for _, f, _ in wholes) > stale:
        wholes = []
    for art, files, miss in sorted(parts + wholes, key=lambda t: t[0]):
        what = ", ".join(f"{rel} ({d})" if rel else f"its Version {d}" for rel, d in sorted(miss.items()))
        rep.error("attestation", where, f"{art} changed since it was attested: {what} is not listed under {where}"
                  + ("" if "" in files else " (a file added or changed)"),
                  _relist_fix(where.rsplit(" ", 1)[-1], restore=True))
    return bool(parts or wholes)


def check_map(rep: Report, m: dict, root: Path, register: Path | None) -> None:
    rel = (m.get("register") or {}).get("map", "register_map.toml") if isinstance(m.get("register"), dict) else "register_map.toml"
    p = root / rel
    if not p.is_file():   # task-0312 C1-1: a map nothing reads is a subject whose keys have no owner and no walk
        rep.note("map", rel, f"{rel} is not there: no key of this subject maps to a register node, so no key has an owner and none walks the register "
                 "(add it, or name its path under [register] map in subject.toml; a subject that reads no register may go without)")
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
            text = extract.mapped_text(SUBJECT.artefact_text(key))   # task-0301: NFC, as the load reads it
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
    nfc = key_rule.normalise   # task-0301: a task key and a yielded key compared in NFC, as the store compares them
    required = {nfc(k) for t in tasks.values() if isinstance(t, dict) for k in (t.get("keys") or []) if isinstance(k, str)}
    best = {} if partial else _offers(sorted(k for k in required if KEY_RE.fullmatch(k) and k not in yielded), yielded - required)
    for name, t in sorted(tasks.items()):
        if not isinstance(t, dict) or partial:
            continue
        for k in t.get("keys") or []:
            k = nfc(k)
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
    if not args.register and (why := _unnamed(args.root)):   # task-0339 R2: an instance's subject never reads the public register
        print(f"cannot run: {why}", file=sys.stderr)
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


def _unnamed(root: Path) -> str | None:
    """Why the default register may not be read for ``root`` (``instance_register.unnamed`` with the root as the subject)."""
    import instance_register
    return instance_register.unnamed({**os.environ, "KG_SUBJECT": str(root)})


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))

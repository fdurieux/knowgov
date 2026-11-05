"""The register's checks: types, directions, required metadata, hierarchy cycles, duplicate
identities, cardinalities, dangling links, lifecycle consistency, approvals, knowledge a person
gave and the handles it is given under (decisions 0008, 0009), glossary, the coverage rules C1 to C3 with expiring exceptions, and the product–journey alignment
rule A1 at warning level (decision 0018). Exit 1 on any error; warnings exit 0.

    python tools/check_register.py                 # check the working tree
    python tools/check_register.py --previous HEAD # also diff lifecycle states against a commit
    python tools/check_register.py --report reports/2026-10-30/check.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register import ROOT, TAXONOMIES, kind_taxonomy, load_register, load_toml  # noqa: E402
from reconcile import unregistered  # noqa: E402
from impact import THREAD, WITHDRAWN, walk_children  # noqa: E402

ID_RE = re.compile(r"^(CAP|PRD|JRN|PROC|APP|ENT|ORG|EXC|REL)-\d{4,}$")
COVERAGE_RULES = {
    "C1": "an approved journey step or touchpoint has at least one is_supported_by link, or an unexpired exception",
    "C2": "a capability that an approved product requires has at least one realizes link, or an unexpired exception",
    "C3": "a process with an approved realizes link names a diagram of record in its source, or an unexpired exception",
}
ALIGNMENT_RULE = ("an approved product is concerned by an approved journey, and the capabilities it requires are the ones "
                  "that journey's steps reach by the thread walk; a warning, never an error")


class Findings:
    def __init__(self):
        self.items: list[dict] = []

    def error(self, check: str, where: str, msg: str):
        self.items.append({"level": "error", "check": check, "where": where, "message": msg})

    def warn(self, check: str, where: str, msg: str):
        self.items.append({"level": "warning", "check": check, "where": where, "message": msg})

    @property
    def errors(self):
        return [i for i in self.items if i["level"] == "error"]


def _date(v) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return None


def check_nodes(reg: dict, f: Findings, today: dt.date):
    types, life = reg["types"], reg["lifecycle"]
    k2t = kind_taxonomy(reg)
    required = types["node"]["required"]
    seen = {}
    for nid, n in reg["nodes"].items():
        where = f"{n['_taxonomy']}/{n['_path'].name}"
        if n["_path"].stem != nid:
            f.error("identity", where, f"file name and id differ ({nid})")
        if not ID_RE.match(nid):
            f.error("identity", where, f"id {nid} is not <PREFIX>-<4+ digits>")
        if nid in seen:
            f.error("identity", where, f"duplicate id, also in {seen[nid]}")
        seen[nid] = where
        for field in required:
            if field not in n:
                f.error("metadata", where, f"missing required field {field}")
        kind = n.get("kind")
        tax = k2t.get(kind)
        if tax is None:
            f.error("types", where, f"unknown kind {kind!r}")
            continue
        if tax != n["_taxonomy"]:
            f.error("types", where, f"kind {kind} belongs to {tax}, file is under {n['_taxonomy']}")
        prefix = types["taxonomy"][tax]["prefix"]
        if not nid.startswith(prefix + "-"):
            f.error("identity", where, f"id prefix should be {prefix} for kind {kind}")
        parent = n.get("parent")
        if parent is not None:
            p = reg["nodes"].get(parent)
            if p is None:
                f.error("dangling", where, f"parent {parent} does not exist")
            else:
                if p["_taxonomy"] != n["_taxonomy"]:
                    f.error("hierarchy", where, f"parent {parent} is in another taxonomy")
                allowed = types["taxonomy"][tax]["parent_of"].get(kind, [])
                if p.get("kind") not in allowed:
                    f.error("hierarchy", where, f"a {kind} may not have a {p.get('kind')} parent (allowed: {allowed})")
                # decision 0015: an approved child of a deprecated or retired parent is an error; a
                # proposed or draft one a warning; a deprecated, retired or rejected one nothing
                if p.get("state") in ("deprecated", "retired") and n.get("state") in ("approved", "proposed", "draft"):
                    (f.error if n.get("state") == "approved" else f.warn)(
                        "lifecycle", where, f"{n.get('state')} node has parent {parent} in state {p.get('state')}")
        elif types["taxonomy"][tax]["parent_of"].get(kind):
            f.warn("hierarchy", where, f"a {kind} usually has a parent of kind {types['taxonomy'][tax]['parent_of'][kind]}")
        state = n.get("state")
        if state not in life["states"]:
            f.error("lifecycle", where, f"unknown state {state!r}")
        owner = n.get("owner")
        if owner and owner not in reg["nodes"]:
            f.error("dangling", where, f"owner {owner} does not exist")
        elif owner and reg["nodes"][owner]["_taxonomy"] != "organisation":
            f.error("types", where, f"owner {owner} is not an organisation node")
        if state == "approved":
            for field in types["node"]["required_when_approved"]:
                if field not in n:
                    f.error("approval", where, f"approved node lacks {field}")
            appr = n.get("approval") or {}
            for field in types["node"]["approval_fields"]:
                if field not in appr:
                    f.error("approval", where, f"approval lacks {field}")
            rec = appr.get("record")
            if rec and not (reg["root"] / rec).exists():
                f.error("approval", where, f"approval record {rec} does not exist")
            due = _date(n.get("review_due"))
            if due and due < today:
                (f.error if life["review"].get("overdue_is_error") else f.warn)("review", where, f"review overdue since {due}")
        src = n.get("source") or {}
        sysname = src.get("system")
        if sysname:
            spec = reg["sources"]["system"].get(sysname)
            if spec is None:
                f.error("sources", where, f"unknown source system {sysname!r}")
            elif spec["id_field"] not in src:
                f.error("sources", where, f"source {sysname} needs {spec['id_field']}")
            elif n["_taxonomy"] not in spec["authoritative_for"]:
                f.error("sources", where, f"{sysname} is not authoritative for {n['_taxonomy']}")
            exp = src.get("export")
            if exp and not (reg["root"] / exp).is_dir():
                f.error("sources", where, f"export folder {exp} does not exist")
    # cycles, per taxonomy
    for nid, n in reg["nodes"].items():
        seen_ids, cur = [], nid
        while cur is not None:
            if cur in seen_ids:
                f.error("hierarchy", f"{n['_taxonomy']}/{nid}.toml", "parent chain is a cycle: " + " -> ".join(seen_ids + [cur]))
                break
            seen_ids.append(cur)
            cur = reg["nodes"].get(cur, {}).get("parent")


def check_relationships(reg: dict, f: Findings, today: dt.date):
    types, life = reg["types"], reg["lifecycle"]
    ids = {}
    for name, rel in reg["relationships"].items():
        t, where = rel["type"], f"relationships/{name}.toml"
        if t.get("name") != name:
            f.error("types", where, f"type header names {t.get('name')!r}, file is {name}")
        for field in ("source_kind", "target_kind", "direction", "inverse_label", "owner", "evidence_class", "aris_status", "archi_status"):
            if field not in t:
                f.error("metadata", where, f"type header lacks {field}")
        for st in ("aris_status", "archi_status"):
            if t.get(st) not in ("unverified", "native_tested", "configuration_required", "extension_required", "unsupported"):
                f.error("metadata", where, f"{st} must be one of the five statuses, got {t.get(st)!r}")
        if t.get("owner") not in reg["nodes"]:
            f.error("dangling", where, f"type owner {t.get('owner')} does not exist")
        external = t.get("target_is_external", False)
        for ln in rel["links"]:
            lid = ln.get("id", "?")
            w = f"{where} [{lid}]"
            if not ID_RE.match(lid) or not lid.startswith("REL-"):
                f.error("identity", w, "link id is not REL-<digits>")
            if lid in ids:
                f.error("identity", w, f"duplicate link id, also in {ids[lid]}")
            ids[lid] = w
            for field in types["relationship"]["required"]:
                if field == "target" and external:
                    continue
                if field not in ln:
                    f.error("metadata", w, f"link lacks {field}")
            s = reg["nodes"].get(ln.get("source"))
            if s is None:
                f.error("dangling", w, f"source {ln.get('source')} does not exist")
            elif s.get("kind") not in t.get("source_kind", []):
                f.error("direction", w, f"source kind {s.get('kind')} not allowed for {name}")
            if external:
                if "target_external" not in ln:
                    f.error("metadata", w, "external target link lacks target_external")
            else:
                tg = reg["nodes"].get(ln.get("target"))
                if tg is None:
                    f.error("dangling", w, f"target {ln.get('target')} does not exist")
                elif tg.get("kind") not in t.get("target_kind", []):
                    f.error("direction", w, f"target kind {tg.get('kind')} not allowed for {name}")
            if ln.get("state") not in life["states"]:
                f.error("lifecycle", w, f"unknown state {ln.get('state')!r}")
            if ln.get("owner") not in reg["nodes"]:
                f.error("dangling", w, f"owner {ln.get('owner')} does not exist")
            if name == "crud" and not ln.get("mode"):
                f.error("metadata", w, "crud link needs mode, a list of C, R, U, D")
            if ln.get("state") == "approved":
                appr = ln.get("approval") or {}
                for field in types["relationship"]["required_when_approved"]:
                    if field not in ln:
                        f.error("approval", w, f"approved link lacks {field}")
                for field in types["node"]["approval_fields"]:
                    if field not in appr:
                        f.error("approval", w, f"approval lacks {field}")
                rec = appr.get("record")
                if rec and not (reg["root"] / rec).exists():
                    f.error("approval", w, f"approval record {rec} does not exist")
                # a link whose source or target is deprecated or retired is a finding
                for end in ("source", "target"):
                    nd = reg["nodes"].get(ln.get(end))
                    if nd and nd.get("state") in ("deprecated", "retired"):
                        f.error("lifecycle", w, f"approved link references {end} {nd['id']} in state {nd['state']}")
            for ev in ln.get("evidence", []):
                if "/" in ev and ":" not in ev.split("/")[0] and not (reg["root"] / ev).exists():
                    f.error("evidence", w, f"evidence path {ev} does not exist")
            if "elicited" in ln:
                check_elicited(reg, f, w, ln, today)
        # cardinality per source state: approved links counted per source
        card = t.get("cardinality", {})
        by_source: dict[str, int] = {}
        for ln in rel["links"]:
            if ln.get("state") == "approved":
                by_source[ln["source"]] = by_source.get(ln["source"], 0) + 1
        for sid, n in reg["nodes"].items():
            if n.get("kind") in t.get("source_kind", []):
                rule = card.get(n.get("state"), {})
                mn = rule.get("min_targets", 0)
                mx = rule.get("max_targets", "n")
                cnt = by_source.get(sid, 0)
                if name in ("requires", "delivers", "realizes", "is_supported_by") and n.get("state") == "approved" and cnt < mn:
                    # covered by the coverage rules with exceptions; reported there, not twice
                    continue
                if cnt < mn:
                    f.error("cardinality", f"{where} ({sid})", f"{cnt} approved {name} links, minimum {mn} in state {n.get('state')}")
                if mx != "n" and cnt > int(mx):
                    f.error("cardinality", f"{where} ({sid})", f"{cnt} approved {name} links, maximum {mx}")


def _add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(year, month, day)
        except ValueError:
            continue
    raise ValueError(d)


# decision 0009: gives (may answer for the unit), approves (may approve what another handle of the
# unit gave), closes (may close a declared gap or settle a dispute on what the unit owns)
ROLES = {"gives", "approves", "closes"}


def _issued_handles(reg: dict) -> dict | None:
    """Decision 0009: handle -> {unit, roles, issued, withdrawn} from the issued list, or None
    when the register has none (the pattern alone then applies, as before)."""
    rel = reg["types"].get("elicited", {}).get("issued")
    if not rel or not (reg["root"] / rel).exists():
        return None
    data = tomllib.loads((reg["root"] / rel).read_text(encoding="utf-8"))
    return {h["handle"]: h for h in data.get("handle", []) if "handle" in h}


def check_handles(reg: dict, f: Findings):
    """Decision 0009: the issued list holds handles, units and roles, never a name; each handle
    matches the pattern, is listed once, and names a unit the organisation taxonomy holds."""
    rel = reg["types"].get("elicited", {}).get("issued")
    if not rel or not (reg["root"] / rel).exists():
        return
    pattern = reg["types"].get("elicited", {}).get("handle", r"^[a-z][a-z0-9-]{1,39}$")
    allowed = {"handle", "unit", "roles", "issued", "withdrawn"}
    seen = set()
    for h in tomllib.loads((reg["root"] / rel).read_text(encoding="utf-8")).get("handle", []):
        w = f"{rel} [{h.get('handle', '?')}]"
        extra = sorted(set(h) - allowed)
        if extra:
            f.error("handles", w, f"fields {extra} are not allowed: the list holds handles, units and roles, never a name")
        if not re.match(pattern, str(h.get("handle", ""))):
            f.error("handles", w, "not an opaque handle")
        if h.get("handle") in seen:
            f.error("handles", w, "listed twice: a handle is issued once and never reused")
        seen.add(h.get("handle"))
        unit = reg["nodes"].get(h.get("unit", ""))
        if unit is None or unit.get("_taxonomy") != "organisation":
            f.error("handles", w, f"unit {h.get('unit')!r} is not an organisation node")
        if _date(h.get("issued")) is None:
            f.error("handles", w, "issued must be a date")
        bad = sorted(set(h.get("roles", [])) - ROLES)
        if bad:
            f.error("handles", w, f"roles {bad} unknown; a role is one of {sorted(ROLES)}")


def check_elicited(reg: dict, f: Findings, where: str, ln: dict, today: dt.date):
    """Decision 0008: knowledge a person gave carries who (an opaque handle), when, and the record
    of the answer, and is due for review sooner than the type's default."""
    spec = reg["types"].get("elicited", {})
    el = ln.get("elicited")
    if not isinstance(el, dict):
        f.error("elicited", where, "elicited must be a table: { from, on, record }")
        return
    for field in spec.get("fields", ["from", "on", "record"]):
        if field not in el:
            f.error("elicited", where, f"elicited lacks {field}")
    handle = el.get("from")
    if handle is not None and not re.match(spec.get("handle", r"^[a-z][a-z0-9-]{1,39}$"), str(handle)):
        f.error("elicited", where, f"elicited.from {handle!r} is not an opaque handle (lower case, digits, hyphens): never a name or an address")
    on = _date(el.get("on"))
    if "on" in el and on is None:
        f.error("elicited", where, "elicited.on must be a date")
    elif on and on > today:
        f.error("elicited", where, f"elicited.on {on} is in the future")
    issued = _issued_handles(reg)
    if issued is not None and handle is not None:
        h = issued.get(str(handle))
        if h is None:
            f.error("elicited", where, f"elicited.from {handle!r} is not an issued handle ({spec.get('issued')}): handles are issued, never chosen")
        elif on and (_date(h.get("issued")) is None or _date(h["issued"]) > on):
            f.error("elicited", where, f"elicited.from {handle!r} was not yet issued on {on}")
        elif on and _date(h.get("withdrawn")) and _date(h["withdrawn"]) <= on:
            f.error("elicited", where, f"elicited.from {handle!r} was withdrawn on {h['withdrawn']}, before the knowledge was given")
    rec = el.get("record")
    if rec and re.match(spec.get("external_record", r"^capture:[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"), str(rec)):
        pass   # decision 0009: a capture in the knowledge store, cited by its id, not resolved here
    elif rec and (":" in str(rec).split("/")[0]):
        f.error("elicited", where, f"elicited record {rec!r}: outside the register a record is cited as capture:<id>")
    elif rec and not (reg["root"] / rec).exists():
        f.error("elicited", where, f"elicited record {rec} does not exist")
    months = reg["lifecycle"].get("review", {}).get("evidence", {}).get("elicited", {}).get("months")
    due = _date(ln.get("review_due"))
    if on and months:
        limit = _add_months(on, int(months))
        if due is None:
            f.error("elicited", where, f"a link with elicited knowledge needs review_due, at most {limit}")
        elif due > limit:
            f.error("elicited", where, f"review_due {due} is later than {limit}, {months} months after the knowledge was given")


def check_glossary(reg: dict, f: Findings):
    forb = []
    for t in reg["glossary"].get("term", []):
        for syn in t.get("forbidden", []):
            forb.append((syn, t["term"]))
    def scan(text: str, where: str):
        low = text.lower()
        for syn, term in forb:
            if re.search(r"\b" + re.escape(syn.lower()) + r"\b", low):
                f.error("glossary", where, f"forbidden synonym {syn!r}; write {term!r}")
    for nid, n in reg["nodes"].items():
        scan(n.get("name", ""), f"{n['_taxonomy']}/{nid}.toml name")
    for name, rel in reg["relationships"].items():
        for ln in rel["links"]:
            scan(ln.get("rationale", ""), f"relationships/{name}.toml [{ln.get('id')}] rationale")
    for p in sorted((reg["root"] / "decisions").glob("*.md")):
        scan(p.read_text(encoding="utf-8"), f"decisions/{p.name}")


def _exceptions(reg: dict, f: Findings, today: dt.date) -> dict[str, set[str]]:
    live: dict[str, set[str]] = {}
    for e in reg["exceptions"]:
        where = f"exceptions/{e['_path'].name}"
        if e.get("rule") not in COVERAGE_RULES:
            f.error("exceptions", where, f"unknown coverage rule {e.get('rule')!r}")
            continue
        for sid in e.get("scope", []):
            if sid not in reg["nodes"]:
                f.error("dangling", where, f"scope {sid} does not exist")
        appr = e.get("approved") or {}
        for field in ("by", "on", "record"):
            if field not in appr:
                f.error("approval", where, f"exception approval lacks {field}")
        exp = _date(e.get("expires"))
        if exp is None:
            f.error("exceptions", where, "exception needs an expires date")
        elif exp < today:
            f.warn("exceptions", where, f"exception expired on {exp}; it no longer excuses")
            continue
        live.setdefault(e["rule"], set()).update(e.get("scope", []))
    return live


def check_coverage(reg: dict, f: Findings, today: dt.date) -> dict:
    live = _exceptions(reg, f, today)
    rels = reg["relationships"]
    def approved_links(name):
        return [ln for ln in rels.get(name, {}).get("links", []) if ln.get("state") == "approved"]
    summary = {}
    # C1
    steps = [n for n in reg["nodes"].values() if n.get("kind") in ("step", "touchpoint") and n.get("state") == "approved"]
    supported = {ln["source"] for ln in approved_links("is_supported_by")}
    miss = [n["id"] for n in steps if n["id"] not in supported and n["id"] not in live.get("C1", set())]
    for sid in miss:
        f.error("C1", f"journeys/{sid}.toml", COVERAGE_RULES["C1"])
    summary["C1"] = {"denominator": len(steps), "covered": len([n for n in steps if n["id"] in supported]), "excepted": len([n for n in steps if n["id"] in live.get("C1", set())]), "uncovered": miss}
    # C2
    required = {ln["target"] for ln in approved_links("requires") if reg["nodes"].get(ln["source"], {}).get("state") == "approved"}
    realized = {ln["target"] for ln in approved_links("realizes")}
    miss2 = sorted(c for c in required if c not in realized and c not in live.get("C2", set()))
    for cid in miss2:
        f.error("C2", f"capabilities/{cid}.toml", COVERAGE_RULES["C2"])
    summary["C2"] = {"denominator": len(required), "covered": len(required & realized), "excepted": len(required & live.get("C2", set())), "uncovered": miss2}
    # C3
    realizing = sorted({ln["source"] for ln in approved_links("realizes")})
    miss3 = [p for p in realizing if not (reg["nodes"].get(p, {}).get("source") or {}).get("diagram") and p not in live.get("C3", set())]
    for pid in miss3:
        f.error("C3", f"processes/{pid}.toml", COVERAGE_RULES["C3"])
    summary["C3"] = {"denominator": len(realizing), "covered": len(realizing) - len(miss3) - len([p for p in realizing if p in live.get("C3", set())]), "excepted": len([p for p in realizing if p in live.get("C3", set())]), "uncovered": miss3}
    return summary


def check_alignment(reg: dict, f: Findings) -> dict:
    """A1 (decision 0018): per approved product, the capabilities it requires (approved requires links)
    against the capabilities its journeys reach by the thread walk with parent descent (approved
    concerns links from a journey element neither deprecated nor retired). A product no journey
    concerns is one finding; otherwise each capability required and not reached, and each reached and
    not required, is one. Warnings only; reported with its denominator."""
    nodes = reg["nodes"]
    def approved_links(name):
        return [ln for ln in reg["relationships"].get(name, {}).get("links", []) if ln.get("state") == "approved"]
    products = sorted(nid for nid, n in nodes.items() if n.get("kind") in ("product", "variant") and n.get("state") == "approved")
    out = {"denominator": len(products), "aligned": [], "no_journey": [], "required_not_reached": [], "reached_not_required": []}
    for pid in products:
        where = f"products/{pid}.toml"
        journeys = sorted({ln["source"] for ln in approved_links("concerns") if ln.get("target") == pid
                           and nodes.get(ln["source"], {}).get("state") not in WITHDRAWN})
        if not journeys:
            out["no_journey"].append(pid)
            f.warn("A1", where, "no approved journey concerns this product")
            continue
        required = {ln["target"] for ln in approved_links("requires") if ln["source"] == pid}
        reached = set()
        for j in journeys:
            reached |= {x for x in walk_children(reg, j, THREAD)["reached"] if nodes.get(x, {}).get("_taxonomy") == "capabilities"}
        missing, extra = sorted(required - reached), sorted(reached - required)
        for c in missing:
            out["required_not_reached"].append([pid, c])
            f.warn("A1", where, f"requires {c}, which no step of {', '.join(journeys)} reaches by the thread walk")
        for c in extra:
            out["reached_not_required"].append([pid, c])
            f.warn("A1", where, f"a step of {', '.join(journeys)} reaches {c} by the thread walk; the product does not require it")
        if not missing and not extra:
            out["aligned"].append(pid)
    return out


def export_counts(reg: dict) -> dict:
    """Per system, the latest export's ids with their denominator: held by a node, or unregistered
    (decision 0017). Reported only; not a coverage rule."""
    out = {}
    for sysname in sorted(reg["sources"]["system"]):
        folders = sorted(p.parent for p in (reg["root"] / "exports" / sysname).glob("*/MANIFEST.toml"))
        if not folders:
            continue
        man = load_toml(folders[-1] / "MANIFEST.toml")
        n = len(man.get("ids", {}))
        u = len(unregistered(reg, man))
        out[sysname] = {"export": folders[-1].relative_to(reg["root"]).as_posix(), "denominator": n, "registered": n - u, "unregistered": u}
    return out


def check_transitions(reg: dict, f: Findings, previous: str):
    """Diff every node's and link's state against a git ref; a transition the lifecycle table does not allow is an error."""
    allowed = reg["lifecycle"]["transitions"]
    def prev_states() -> dict[str, str]:
        out = {}
        for tax in TAXONOMIES:
            res = subprocess.run(["git", "ls-tree", "--name-only", previous, f"{tax}/"], capture_output=True, text=True, cwd=reg["root"])
            for path in res.stdout.split():
                if not path.endswith(".toml"):
                    continue
                blob = subprocess.run(["git", "show", f"{previous}:{path}"], capture_output=True, cwd=reg["root"])
                if blob.returncode == 0:
                    try:
                        d = tomllib.loads(blob.stdout.decode("utf-8"))
                        out[d.get("id", Path(path).stem)] = d.get("state")
                    except tomllib.TOMLDecodeError:
                        pass
        res = subprocess.run(["git", "ls-tree", "--name-only", previous, "relationships/"], capture_output=True, text=True, cwd=reg["root"])
        for path in res.stdout.split():
            blob = subprocess.run(["git", "show", f"{previous}:{path}"], capture_output=True, cwd=reg["root"])
            if blob.returncode == 0:
                try:
                    for ln in tomllib.loads(blob.stdout.decode("utf-8")).get("link", []):
                        out[ln.get("id")] = ln.get("state")
                except tomllib.TOMLDecodeError:
                    pass
        return out
    before = prev_states()
    now = {nid: n.get("state") for nid, n in reg["nodes"].items()}
    for rel in reg["relationships"].values():
        for ln in rel["links"]:
            now[ln.get("id")] = ln.get("state")
    for rid, st in now.items():
        old = before.get(rid)
        if old is None or old == st:
            continue
        if st not in allowed.get(old, []):
            f.error("transition", rid, f"{old} -> {st} is not an allowed transition (allowed from {old}: {allowed.get(old, [])})")


def run(root: Path = ROOT, previous: str | None = None, today: dt.date | None = None) -> tuple[Findings, dict]:
    today = today or dt.date.today()
    reg = load_register(root)
    f = Findings()
    check_nodes(reg, f, today)
    check_relationships(reg, f, today)
    check_handles(reg, f)
    check_glossary(reg, f)
    summary = check_coverage(reg, f, today)
    summary["A1"] = check_alignment(reg, f)
    if previous:
        check_transitions(reg, f, previous)
    summary["exports"] = export_counts(reg)
    summary["nodes"] = len(reg["nodes"])
    summary["links"] = sum(len(r["links"]) for r in reg["relationships"].values())
    return f, summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--previous", help="a git ref to diff lifecycle states against")
    ap.add_argument("--report", type=Path, help="write findings and the coverage summary as JSON here")
    ap.add_argument("--today", help="YYYY-MM-DD, for reproducible runs")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else None
    f, summary = run(a.root, a.previous, today)
    for it in f.items:
        print(f"{it['level'].upper():7} {it['check']:12} {it['where']}: {it['message']}")
    for rule in ("C1", "C2", "C3"):
        s = summary[rule]
        print(f"{rule}: {s['covered']}/{s['denominator']} covered, {s['excepted']} excepted, {len(s['uncovered'])} uncovered")
    a1 = summary["A1"]
    print(f"A1: {len(a1['aligned'])}/{a1['denominator']} products aligned, {len(a1['no_journey'])} with no journey, "
          f"{len(a1['required_not_reached'])} required not reached, {len(a1['reached_not_required'])} reached not required")
    for sysname, s in summary["exports"].items():
        print(f"{sysname}: {s['registered']}/{s['denominator']} export ids held by a node, {s['unregistered']} unregistered ({s['export']})")
    print(f"{summary['nodes']} nodes, {summary['links']} links, {len(f.errors)} error(s), {len(f.items) - len(f.errors)} warning(s)")
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps({"findings": f.items, "summary": summary, "today": str(today or dt.date.today())}, indent=2, default=str) + "\n")
    return 1 if f.errors else 0


if __name__ == "__main__":
    sys.exit(main())

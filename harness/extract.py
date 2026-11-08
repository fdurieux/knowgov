"""Deterministic extraction: kit text -> fragments, entities, assertions.

One extractor per artefact family, each a hand-written mapper for this
kit (the aris2puml shape: parse what is there, invent nothing, and when
a value cannot be read, record the raw text so a rule can flag it).

An assertion is a dict:
  id, entity, predicate, value, text, basis, artefact, fragments (ids)
A fragment: id, artefact, locator, text.  An entity: id, kind, name.

Keys are ``entity|predicate``. Behaviour values are ``k=v;k=v`` strings
over the fields the artefact states; numeric values are strings of the
number; a documented absence is the sentinel ``NONE``.
"""

from __future__ import annotations

import ast
import re
import tomllib
import xml.etree.ElementTree as ET

import yaml

NONE = "NONE"


class Bag:
    def __init__(self, artefact: str):
        self.artefact = artefact
        self.fragments: list[dict] = []
        self.entities: dict[str, dict] = {}
        self.assertions: list[dict] = []
        self._n = {}

    def frag(self, locator: str, text: str) -> str:
        fid = f"F:{self.artefact}:{locator}"
        self.fragments.append({"id": fid, "artefact": self.artefact,
                               "locator": locator, "text": text.strip()})
        return fid

    def ent(self, eid: str, kind: str, name: str | None = None) -> str:
        self.entities.setdefault(eid, {"id": eid, "kind": kind, "name": name or eid})
        return eid

    def assertion(self, entity: str, predicate: str, value, text: str,
                  frags: list[str], basis: str = "extracted") -> dict:
        key = f"{entity}|{predicate}"
        n = self._n.get(key, 0)
        self._n[key] = n + 1
        aid = f"A:{self.artefact}:{key}" + (f"#{n}" if n else "")
        a = {"id": aid, "entity": entity, "predicate": predicate,
             "value": str(value), "text": text.strip(), "basis": basis,
             "artefact": self.artefact, "fragments": list(frags)}
        self.assertions.append(a)
        return a


from kitio import DocumentUnreadable  # the load's named document error (doc-0030 I11), raised here
from subject import SUBJECT, BUNDLE_MARK_RE, bundle_parts as _subject_bundle_parts

_SHORT = SUBJECT.shorts   # artefact key -> the short name assertion ids carry (the subject manifest)


def short(path: str) -> str:
    return _SHORT[path]


# ---------------------------------------------------------------- helpers

def _num(s: str):
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*", s)
    return m.group(1) if m else None


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """(1-based start line, paragraph text) for blank-line-separated blocks."""
    out, buf, start = [], [], None
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if start is None:
                start = i
            buf.append(line)
        elif buf:
            out.append((start, "\n".join(buf)))
            buf, start = [], None
    if buf:
        out.append((start, "\n".join(buf)))
    return out


def _numbered_items(text: str) -> list[tuple[int, str, str]]:
    """(1-based line, number, body) for items of the form ``n. body`` that
    continue over indented lines, in order of appearance."""
    out = []
    cur = None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"(\d+)\. (.*)", line)
        if m:
            if cur:
                out.append(cur)
            cur = [i, m.group(1), m.group(2)]
        elif cur and line.startswith("   ") and line.strip():
            cur[2] += " " + line.strip()
        else:
            if cur:
                out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    return [tuple(x) for x in out]


def _behaviour_tokens(*, priced=None, status=None, notified=None, hold=None,
                      screen=None, store=None) -> str:
    parts = []
    for k, v in (("priced", priced), ("status", status), ("notified", notified),
                 ("hold", hold), ("screen", screen), ("store", store)):
        if v is not None:
            parts.append(f"{k}={v}")
    return ";".join(parts)


# ---------------------------------------------------------- requirements

def extract_requirements(path: str, text: str) -> Bag:
    b = Bag(short(path))
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"\|\s*(REQ-\d+)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        rid, body = m.group(1), m.group(2)
        f = b.frag(f"row/{rid}", line)
        b.ent(rid, "requirement", rid)
        if "NOT YET SPECIFIED" in body:
            b.assertion(rid, "specified", NONE, body, [f], basis="authored")
            b.assertion(rid, "open_decision", "OD-1", body, [f], basis="authored")
        else:
            b.assertion(rid, "text", body, body, [f], basis="authored")
    for i, line in enumerate(text.splitlines(), 1):
        if "not yet authored" in line:
            f = b.frag(f"line/{i}", line)
            b.ent("screening_decision.dmn", "artefact_ref")
            b.assertion("screening_decision.dmn", "authored", NONE, line, [f], basis="authored")
    return b


# ------------------------------------------------------- decision tables

_DTS_STATUS = {"quoted": "quoted", "review_hold": "review_hold",
               "refused_screening": "refused_screening"}


def extract_decision_table(path: str, text: str) -> Bag:
    b = Bag(short(path))
    lines = text.splitlines()
    section = None
    for i, line in enumerate(lines, 1):
        if line.startswith("## DT-V"):
            section = "V"
        elif line.startswith("## DT-S"):
            section = "S"
        elif line.startswith("## DT-P"):
            section = "P"
        if section == "V":
            m = re.match(r"\|\s*V(\d)\s*\|\s*`(\w+)`\s*\|\s*(.+?)\s*\|\s*$", line)
            if m:
                field, rule = m.group(2), m.group(3)
                f = b.frag(f"DT-V/row/V{m.group(1)}", line)
                b.ent(field, "field", field)
                if "present" in rule:
                    b.assertion(field, "present", "yes", rule, [f])
                mm = re.search(r"`(-?[\d.]+)\s*<=\s*\w+\s*<=\s*(-?[\d.]+)`", rule)
                if mm:
                    b.assertion(field, "min", mm.group(1), rule, [f])
                    b.assertion(field, "max", mm.group(2), rule, [f])
        if section == "S":
            m = re.match(r"\|\s*(accept|review|refuse)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*`(\w+)`\s*\|\s*$", line)
            if m:
                row, cond, _dec, priced, notified, status = m.groups()
                ent = f"S-{row}"
                f = b.frag(f"DT-S/row/{row}", line)
                b.ent(ent, "decision_row", f"DT-S {row}")
                c = cond.strip("`")
                lo = re.fullmatch(r"(\d+)\s*<=\s*risk_index\s*<=\s*(\d+)", c)
                le = re.fullmatch(r"risk_index\s*<=\s*(\d+)", c)
                ge = re.fullmatch(r"risk_index\s*>=\s*(\d+)", c)
                if lo:
                    b.assertion(ent, "min", lo.group(1), cond, [f])
                    b.assertion(ent, "max", lo.group(2), cond, [f])
                elif le:
                    b.assertion(ent, "max", le.group(1), cond, [f])
                elif ge:
                    b.assertion(ent, "min", ge.group(1), cond, [f])
                else:
                    # unparsable condition: keep the raw text as the value
                    pred = {"accept": "max", "review": "min", "refuse": "min"}[row]
                    b.assertion(ent, pred, cond, cond, [f])
                    if row == "review":
                        b.assertion(ent, "max", cond, cond, [f])
                b.assertion(ent, "priced", "yes" if priced.strip("* ").lower().startswith("yes") else NONE, priced, [f])
                nt = notified.strip("* ").lower()
                nv = NONE if nt.startswith("no") else ("quote document" if "quote document" in nt else "refusal notice")
                b.assertion(ent, "notified", nv, notified, [f])
                b.assertion(ent, "status", status, status, [f])
    # notes and paragraphs
    for start, para in _paragraphs(text):
        p = " ".join(para.split())
        if p.startswith("An invalid request is rejected"):
            f = b.frag("DT-V/para/invalid", para)
            b.ent("invalid_request", "condition")
            b.assertion("invalid_request", "behaviour",
                        _behaviour_tokens(status="rejected: invalid_request", store="no", screen="no", priced="no", notified="no"),
                        p, [f])
        if p.startswith("Worked example"):
            f = b.frag("DT-P/para/worked-example", para)
            b.ent("P3", "pricing_step", "DT-P P3")
            b.assertion("P3", "order", "after P2", p, [f])
            mm = re.search(r"\*\*`([\d.]+)`\*\*", p)
            if mm:
                b.ent("worked_example", "example")
                b.assertion("worked_example", "price", mm.group(1), p, [f])
    notes_start = text.find("Notes (normative):")
    notes_end = text.find("## DT-P")
    if notes_start > 0:
        block = text[notes_start:notes_end]
        for lineno, n, body in _numbered_items(block):
            para = body
            if "storage failure" in body:
                f = b.frag("DT-S/note/3", para)
                b.ent("QuoteAPI", "service")
                b.assertion("QuoteAPI", "on_store_failure",
                            _behaviour_tokens(status="error: store_unavailable", screen="no", priced="no", notified="no"), body, [f])
            elif "fire-and-forget" in body:
                f = b.frag("DT-S/note/4", para)
                b.ent("QuoteAPI", "service")
                b.assertion("QuoteAPI", "on_notification_failure",
                            "response=unchanged;stored=unchanged", body, [f])
            elif "screening outage" in body:
                f = b.frag("DT-S/note/5", para)
                b.ent("QuoteAPI", "service")
                b.assertion("QuoteAPI", "on_screening_outage",
                            _behaviour_tokens(priced="yes", status="held_unscreened", notified="no", hold="true"), body, [f])
            elif "review hold" in body.lower():
                f = b.frag("DT-S/note/1", para)
                b.assertion("S-review", "final", "no", body, [f])
            elif "refusal" in body.lower():
                f = b.frag("DT-S/note/2", para)
                b.assertion("S-refuse", "notified", "refusal notice", body, [f])
    for i, line in enumerate(lines, 1):
        m = re.match(r"\|\s*(P\d)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        step, rule = m.groups()
        f = b.frag(f"DT-P/row/{step}", line)
        b.ent(step, "pricing_step", f"DT-P {step}")
        if step == "P1":
            mm = re.search(r"`base = (.+?)`", rule)
            b.assertion(step, "formula", mm.group(1) if mm else rule, rule, [f])
        elif step == "P2":
            mm = re.search(r"`weight_kg > ([\d.]+)`, add `([\d.]+)`", rule)
            if mm:
                b.assertion(step, "threshold", mm.group(1), rule, [f])
                b.assertion(step, "surcharge", mm.group(2), rule, [f])
            else:
                b.assertion(step, "threshold", rule, rule, [f])
                b.assertion(step, "surcharge", rule, rule, [f])
        elif step == "P3":
            mm = re.search(r"`distance_km >= ([\d.]+)`, multiply the running total by `([\d.]+)`", rule)
            if mm:
                b.assertion(step, "threshold", mm.group(1), rule, [f])
                b.assertion(step, "factor", mm.group(2), rule, [f])
            else:
                b.assertion(step, "threshold", rule, rule, [f])
                b.assertion(step, "factor", rule, rule, [f])
            if "after" in rule:
                b.assertion(step, "order", "after P2", rule, [f])
        elif step == "P4":
            mm = re.search(r"round\(result, (\d)\)", rule)
            b.assertion(step, "rounding", mm.group(1) if mm else rule, rule, [f])
    return b


# ------------------------------------------------------------------ spec

_STEP_CANON = {"Validate": "validate", "Store": "store", "Request the shipper": "screen",
               "Apply": "decide", "Price": "price", "Notify": "notify", "Return": "respond"}


def extract_spec(path: str, text: str) -> Bag:
    b = Bag(short(path))
    order = []
    flow_start = text.find("## Flow order")
    flow_end = text.find("## API contract")
    for lineno, n, body in _numbered_items(text[flow_start:flow_end]):
        canon = next((v for k, v in _STEP_CANON.items() if body.startswith(k)), None)
        if not canon:
            continue
        order.append(canon)
        f = b.frag(f"flow/step/{n}", body)
        if canon == "store" and "If storage fails" in body:
            b.ent("QuoteAPI", "service")
            b.assertion("QuoteAPI", "on_store_failure",
                        _behaviour_tokens(status="error: store_unavailable", screen="no", priced="no", notified="no"), body, [f])
        if canon == "screen" and "If screening is unavailable" in body:
            b.ent("QuoteAPI", "service")
            b.assertion("QuoteAPI", "on_screening_outage",
                        _behaviour_tokens(priced="yes", status="held_unscreened", notified="no", hold="true"), body, [f])
    if order:
        f = b.frag("flow/order", "\n".join(f"{i}. {s}" for i, s in enumerate(order, 1)))
        b.ent("flow", "process_flow", "quotation flow")
        b.assertion("flow", "order", ">".join(order), "flow order steps 1-7", [f])
    # response vocabulary
    m = re.search(r"Response \(JSON object\): `status` is exactly one of\n\n(.*?)\n\nplus (.*?)\n\n", text, re.S)
    if m:
        enum = sorted(re.findall(r'`"([^"]+)"`', m.group(1)))
        f1 = b.frag("api/response/statuses", m.group(1))
        b.ent("response", "api_response")
        b.assertion("response", "statuses", "|".join(enum), m.group(1), [f1])
        plus = " ".join(m.group(2).split())
        f2 = b.frag("api/response/fields", m.group(2))
        if "`quote_id`" in plus:
            b.assertion("response", "quote_id_presence", "whenever a draft was stored", plus, [f2])
        if "`price`" in plus:
            b.assertion("response", "price_presence", "priced rows only", plus, [f2])
        if "`hold: true`" in plus:
            b.assertion("response", "hold_presence", "held_unscreened only", plus, [f2])
    return b


# --------------------------------------------------------------- openapi

def extract_openapi(path: str, text: str) -> Bag:
    b = Bag(short(path))
    doc = yaml.safe_load(text)
    req = doc["components"]["schemas"]["QuoteRequest"]["properties"]
    for field, spec in req.items():
        b.ent(field, "field", field)
        f = b.frag(f"QuoteRequest/{field}", yaml.safe_dump({field: spec}))
        if "minimum" in spec:
            b.assertion(field, "min", spec["minimum"], f"minimum: {spec['minimum']}", [f])
        if "maximum" in spec:
            b.assertion(field, "max", spec["maximum"], f"maximum: {spec['maximum']}", [f])
        if spec.get("minLength", 0) >= 1 and field in doc["components"]["schemas"]["QuoteRequest"]["required"]:
            b.assertion(field, "present", "yes", "required, minLength 1", [f])
    resp = doc["components"]["schemas"]["QuoteResponse"]["properties"]
    enum = sorted(resp["status"]["enum"])
    f = b.frag("QuoteResponse/status", yaml.safe_dump({"status": resp["status"]}))
    b.ent("response", "api_response")
    b.assertion("response", "statuses", "|".join(enum), "status enum", [f])
    if "hold" in resp:
        f = b.frag("QuoteResponse/hold", yaml.safe_dump({"hold": resp["hold"]}))
        b.assertion("response", "hold_presence", "held_unscreened only", resp["hold"].get("description", ""), [f])
    if "price" in resp:
        f = b.frag("QuoteResponse/price", yaml.safe_dump({"price": resp["price"]}))
        b.assertion("response", "price_presence", "priced rows only", resp["price"].get("description", ""), [f])
    return b


# -------------------------------------------------------------- sequence

_STATUS_TOKEN = {"statusQuoted": "quoted", "statusReviewHold": "review_hold",
                 "statusRefusedScreening": "refused_screening",
                 "statusHeldUnscreened": "held_unscreened",
                 "statusErrorScreening": "error: screening_unavailable"}


def extract_sequence(path: str, text: str) -> Bag:
    from pumllint import parser  # the product's parser, as a library
    b = Bag(short(path))
    d = parser.parse_source(text, file_path=path)[0]
    lines = text.splitlines()
    for name in d.participants:
        p = d.participants[name]
        b.ent(name, "participant", name)
        f = b.frag(f"participant/{name}", lines[p.line - 1])
        b.assertion(name, "kind", p.kind, lines[p.line - 1], [f])
    # branches: (label, start, end)
    spans = []
    for blk in d.blocks:
        if blk.kind != "alt":
            continue
        bounds = [(blk.label, blk.start_line)] + [(br.label, br.line) for br in blk.else_branches]
        for j, (label, start) in enumerate(bounds):
            end = bounds[j + 1][1] if j + 1 < len(bounds) else blk.end_line
            spans.append((label, start, end))
    for label, start, end in spans:
        msgs = [m for m in d.messages if start < m.line < end]
        priced = "yes" if any(m.target == "TariffEngine" for m in msgs) else "no"
        status = None
        for m in msgs:
            if m.target == "QuoteStore" and "updateQuote" in m.label:
                for tok, st in _STATUS_TOKEN.items():
                    if tok in m.label:
                        status = st
        notified = NONE
        for m in msgs:
            if m.target == "NotificationService":
                notified = "quote document" if "QuoteDocument" in m.label else "refusal notice"
        key = None
        if "screening failure" in label:
            key = ("QuoteAPI", "on_screening_outage")
            value = _behaviour_tokens(priced=priced, status=status, notified="no" if notified == NONE else notified)
        elif "storeDraft failure" in label:
            key = ("QuoteAPI", "on_store_failure")
            value = _behaviour_tokens(status="error: store_unavailable", screen="no", priced="no", notified="no")
        elif "row accept" in label:
            key = ("S-accept", None)
        elif "row review" in label:
            key = ("S-review", None)
        elif "row refuse" in label:
            key = ("S-refuse", None)
        if not key:
            continue
        f = b.frag(f"alt/{start}-{end}", "\n".join(lines[start - 1:end]))
        b.ent(key[0], "service" if key[0] == "QuoteAPI" else "decision_row")
        if key[1]:
            b.assertion(key[0], key[1], value, label, [f])
        else:
            b.assertion(key[0], "priced", "yes" if priced == "yes" else NONE, label, [f])
            b.assertion(key[0], "notified", notified, label, [f])
            if status:
                b.assertion(key[0], "status", status, label, [f])
            if "<= ACCEPT_MAX" in label:
                b.assertion(key[0], "max", "ACCEPT_MAX", label, [f])
            if "REVIEW_MIN <=" in label:
                b.assertion(key[0], "min", "REVIEW_MIN", label, [f])
                b.assertion(key[0], "max", "REVIEW_MAX", label, [f])
            if ">= REFUSE_MIN" in label:
                b.assertion(key[0], "min", "REFUSE_MIN", label, [f])
    return b


# ------------------------------------------------------------- containers

def extract_containers(path: str, text: str) -> Bag:
    b = Bag(short(path))
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"\s*(Container|ContainerDb|System_Ext|Person)\((\w+), \"([^\"]+)\", \"([^\"]+)\"", line)
        if m:
            kind, alias, label, tech = m.groups()
            b.ent(alias, {"Person": "person", "System_Ext": "external_system"}.get(kind, "container"), label)
            f = b.frag(f"line/{i}", line)
            b.assertion(alias, "technology", tech, line, [f])
        m = re.match(r"\s*Rel\((\w+), (\w+), \"([^\"]+)\"", line)
        if m:
            src, dst, lbl = m.groups()
            f = b.frag(f"line/{i}", line)
            b.ent(src, "container"); b.ent(dst, "container")
            b.assertion(src, f"uses:{dst}", lbl, line, [f])
    return b


# ------------------------------------------------------------------- bpmn

def extract_bpmn(path: str, text: str) -> Bag:
    b = Bag(short(path))
    ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
    root = ET.fromstring(text)
    proc = root.find("bpmn:process", ns)
    names = {}
    for el in proc:
        tag = el.tag.split("}")[1]
        if tag in ("task", "exclusiveGateway", "startEvent", "endEvent"):
            names[el.get("id")] = (tag, el.get("name", ""))
            b.ent(f"bpmn:{el.get('id')}", tag, el.get("name", ""))
    flows = [(f.get("id"), f.get("sourceRef"), f.get("targetRef"), f.get("name", ""))
             for f in proc.findall("bpmn:sequenceFlow", ns)]
    out = {}
    for fid, s, t, n in flows:
        out.setdefault(s, []).append((t, n, fid))
    # walk a path from a node, following unnamed flows, collecting names
    def walk(node):
        seen, path_nodes = set(), []
        while node and node not in seen:
            seen.add(node)
            path_nodes.append(node)
            nxt = [t for t, n, _ in out.get(node, []) if not n or n in ("valid", "stored")]
            node = nxt[0] if nxt else None
        return path_nodes
    def tokens_from(path_nodes):
        texts = [names[n][1] for n in path_nodes if n in names]
        priced = "yes" if any(t.startswith("Price") for t in texts) else "no"
        notified = "no"
        for t in texts:
            if t.startswith("Send quote"):
                notified = "quote document"
            if t.startswith("Send refusal"):
                notified = "refusal notice"
        status = None
        for t in texts:
            m = re.search(r"Update stored quote to (.+)", t)
            if m:
                status = m.group(1)
        return priced, status, notified
    for s, targets in out.items():
        for t, n, fid in targets:
            if s != "g_screen":
                continue
            path_nodes = walk(t)
            priced, status, notified = tokens_from(path_nodes)
            f = b.frag(f"path/{fid}", " -> ".join(names[x][1] for x in path_nodes if x in names))
            if n == "screening outage":
                b.ent("QuoteAPI", "service")
                b.assertion("QuoteAPI", "on_screening_outage",
                            _behaviour_tokens(priced=priced, status=status, notified=notified), f"{n}: {f}", [f])
            elif n.endswith(" row"):
                ent = {"accept": "S-accept", "review": "S-review", "refuse": "S-refuse"}[n.split()[0]]
                b.ent(ent, "decision_row")
                b.assertion(ent, "priced", "yes" if priced == "yes" else NONE, n, [f])
                b.assertion(ent, "notified", NONE if notified == "no" else notified, n, [f])
                if status:
                    b.assertion(ent, "status", status, n, [f])
    # main-path order
    order = []
    for node in walk("start"):
        tag, name = names.get(node, ("", ""))
        if tag == "task":
            order.append({"Validate": "validate", "Store": "store", "Request": "screen"}.get(name.split()[0], name))
        if tag == "exclusiveGateway" and "DT-S" in name:
            order.append("decide")
            break
    f = b.frag("path/main", " > ".join(order))
    b.ent("flow", "process_flow")
    b.assertion("flow", "order_prefix", ">".join(order), "main path to the screening decision", [f])
    return b


# -------------------------------------------------------------------- dmn

def extract_dmn(path: str, text: str) -> Bag:
    b = Bag(short(path))
    ns = {"d": "https://www.omg.org/spec/DMN/20191111/MODEL/"}
    root = ET.fromstring(text)
    for rule in root.iter(f"{{{ns['d']}}}rule"):
        rid = rule.get("id")
        cond = rule.find("d:inputEntry/d:text", ns).text
        outs = [o.text.strip('"') for o in rule.findall("d:outputEntry/d:text", ns)]
        row = rid.split("_")[1]
        ent = f"S-{row}"
        b.ent(ent, "decision_row")
        f = b.frag(f"rule/{rid}", ET.tostring(rule, encoding="unicode"))
        m = re.fullmatch(r"<= (\d+)", cond)
        if m:
            b.assertion(ent, "max", m.group(1), cond, [f])
        m = re.fullmatch(r"\[(\d+)\.\.(\d+)\]", cond)
        if m:
            b.assertion(ent, "min", m.group(1), cond, [f])
            b.assertion(ent, "max", m.group(2), cond, [f])
        m = re.fullmatch(r">= (\d+)", cond)
        if m:
            b.assertion(ent, "min", m.group(1), cond, [f])
        b.assertion(ent, "priced", "yes" if outs[1] == "true" else NONE, outs[1], [f])
        b.assertion(ent, "notified", NONE if outs[2] == "none" else outs[2], outs[2], [f])
        b.assertion(ent, "status", outs[3], outs[3], [f])
    return b


# ---------------------------------------------------------------- gherkin

def extract_gherkin(path: str, text: str) -> Bag:
    b = Bag(short(path))
    lines = text.splitlines()
    starts = [(i, re.match(r"\s*Scenario: (G\d) - (.*)", l)) for i, l in enumerate(lines, 1)]
    starts = [(i, m.group(1), m.group(2)) for i, m in starts if m]
    for j, (i, gid, title) in enumerate(starts):
        end = starts[j + 1][0] - 1 if j + 1 < len(starts) else len(lines)
        body = "\n".join(lines[i - 1:end]).rstrip()
        f = b.frag(f"scenario/{gid}", body)
        b.ent(gid, "scenario", title)
        b.assertion(gid, "title", title, title, [f])
        m = re.search(r'the response status is "([^"]+)"', body)
        if m:
            b.assertion(gid, "expects_status", m.group(1), body, [f])
    return b


# ------------------------------------------------------------------ links

def extract_links(path: str, text: str, code_text: str) -> Bag:
    b = Bag(short(path))
    doc = tomllib.loads(text)
    tree = ast.parse(code_text)
    units = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef):
                    units[f"{node.name}.{fn.name}"] = (fn.lineno, fn.end_lineno)
        elif isinstance(node, ast.FunctionDef):
            units[node.name] = (node.lineno, node.end_lineno)
    for i, link in enumerate(doc.get("implements", [])):
        cu = link["code_unit"]
        b.ent(cu, "code_unit", cu)
        b.ent(link["requirement"], "requirement")
        f = b.frag(f"implements/{i}", f'{link["requirement"]} implemented_by {cu} (reference_impl.py lines {units.get(cu)})')
        b.assertion(link["requirement"], "implemented_by", cu, f"{cu} at {units.get(cu)}", [f], basis="authored")
    for i, link in enumerate(doc.get("verifies", [])):
        b.ent(link["scenario"], "scenario")
        b.ent(link["requirement"], "requirement")
        f = b.frag(f"verifies/{i}", f'{link["requirement"]} verified_by {link["scenario"]}')
        b.assertion(link["requirement"], "verified_by", link["scenario"], f, [f], basis="authored")
    return b


# ---------------------------------------------------------------- bundles
# A directory artefact (subject.py ``bundle``) is one document made of parts, each opened by a
# ``==> <relative path> <==`` line. The mappers below read such kits: a JSON list of identified
# requirements, markdown contracts citing requirement ids, DMN tables whose rule descriptions
# cite them, PlantUML diagrams whose footer says which they realise, and Gherkin scenarios
# tagged with them. The requirement id is the join: every layer's statement about a requirement
# becomes an assertion on that requirement's entity, one per layer, so the layers never pair
# off as conflicts on the same predicate (the store pairs assertions by entity and predicate
# across artefacts).

_BUNDLE_MARK = BUNDLE_MARK_RE   # the parser lives in subject.py (stdlib), where the marker is defined
# the shape of a requirement id, the subject's ([rules] requirement_id_pattern; JDL-047, REQ-06),
# so that a standard's name (IEEE-754) is never read as one
_REQ_ID = re.compile(r"\b(" + SUBJECT.rules.get("requirement_id_pattern", r"[A-Z]{2,}-\d{2,}") + r")\b")


bundle_parts = _subject_bundle_parts   # (relative path, text) per part of a bundle


# The claim (task-0214, decision-0018 point 3, doc-0032 §3; method 1.3 of pumllint's recreation experiment). A
# kit statement may say what it is: ``observed``, what the pinned original does; ``inferred``, a proposed
# explanation or generalised rule; ``intended``, behaviour accepted by the responsible authority. The bundle
# mappers read it into the basis. A statement that says nothing loads as before, so a kit without claims, the
# vendored ones and the scored record, does not move. Where a mapper reads it (subjects/README.md):
# requirements_json an item's ``"claim"``; contracts_markdown a part's ``Claim: <value>`` line;
# dmn_decisions ``claim: <value>`` in a decision's or a rule's description, the rule's winning; gherkin_tagged an
# ``@claim:<value>`` tag on the Feature, a Rule or a Scenario, the nearest winning; plantuml_realises a
# ``' claim: <value>`` comment line in the diagram.
CLAIMS = {"observed": "extracted", "inferred": "inferred", "intended": "authored"}
# An assertion that rests on statements of different claims (a requirement cited by two contract parts) takes
# the most conservative basis among them: an inference anywhere under it caps it at proposed, and an observation
# is not an intention. A statement with no claim counts as the mapper's own basis, as before.
_RANK = {"inferred": 0, "extracted": 1, "authored": 2}
_CLAIM_LINE = re.compile(r"^[ \t]*claim:[ \t]*(\S+)[ \t]*$", re.I | re.M)            # contracts_markdown
_CLAIM_IN_TEXT = re.compile(r"\bclaim:[ \t]*([A-Za-z_-]+)", re.I)                      # dmn_decisions descriptions
_CLAIM_COMMENT = re.compile(r"^[ \t]*'[ \t]*claim:[ \t]*(\S+)[ \t]*$", re.I | re.M)   # plantuml_realises
_CLAIM_TAG = "@claim:"                                                                 # gherkin_tagged


class UnknownClaim(ValueError):
    """A claim value the kit format does not know: tools/check_subject.py refuses it, and a load fails on it
    rather than read the statement as something it did not say."""


def claim_of(value, where: str) -> str | None:
    """``value`` as a claim, None when the statement states none; an unknown value raises UnknownClaim."""
    if value is None:
        return None
    c = str(value).strip().lower()
    if c not in CLAIMS:
        raise UnknownClaim(f"{where}: claim {value!r} is not one of {', '.join(CLAIMS)}")
    return c


def _basis(claims, default: str) -> str:
    """The basis an assertion takes from the claims of the statements it rests on (None: the statement states
    none, so it counts as ``default``, the mapper's own)."""
    return min([CLAIMS[c] if c else default for c in claims] or [default], key=_RANK.__getitem__)


def _first_claim(rx: re.Pattern, text: str, where: str) -> str | None:
    m = rx.search(text or "")
    return claim_of(m.group(1), where) if m else None


def _ids_in(text: str) -> list[str]:
    """Requirement ids cited in a text, ranges written ``JDL-023 … JDL-039`` (or ``..``, ``to``,
    an en dash) expanded, each id once, in id order."""
    found = set(_REQ_ID.findall(text))
    for a, b in re.findall(r"\b(" + _REQ_ID.pattern[3:-3] + r")\s*(?:…|\.\.\.?|–|-|to)\s*(" + _REQ_ID.pattern[3:-3] + r")\b", text):
        pa, na = a.rsplit("-", 1)
        pb, nb = b.rsplit("-", 1)
        if pa == pb and int(na) < int(nb) and int(nb) - int(na) < 200:
            found.update(f"{pa}-{i:0{len(na)}d}" for i in range(int(na), int(nb) + 1))
    return sorted(found)


def _stem(rel: str) -> str:
    return rel.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def extract_requirements_json(path: str, text: str) -> Bag:
    """A JSON list of ``{id, kind, statement, basis}``: one requirement entity per item and one
    extracted ``statement`` assertion, supported by the item as a row fragment (R-VAGUE reads
    row fragments). An item's optional ``claim`` sets the statement's basis (task-0214); the item's
    ``basis`` (where the reverse engineer read it: code logic, prose or both) is not a claim."""
    import json
    b = Bag(short(path))
    for item in json.loads(text):
        rid, stmt = item["id"], item["statement"]
        b.ent(rid, "requirement", rid)
        f = b.frag(f"row/{rid}", stmt)
        b.assertion(rid, "statement", stmt, stmt, [f], basis=_basis([claim_of(item.get("claim"), f"{path} {rid}")], "extracted"))
    return b


def _by_requirement(bag: Bag, predicate: str, cites: dict[str, list[tuple[str, str, str | None]]], text_for) -> None:
    """One assertion per requirement: ``<req>|<predicate>`` = the parts that cite it, ``; ``-separated in
    path order, supported by one fragment per citing part; authored, unless the citing statements' claims
    say otherwise (the most conservative among them, task-0214)."""
    for rid in sorted(cites):
        bag.ent(rid, "requirement", rid)
        names = [n for n, _f, _c in cites[rid]]
        frags = [f for _n, f, _c in cites[rid]]
        bag.assertion(rid, predicate, "; ".join(names), text_for(rid, names), frags,
                      basis=_basis([c for _n, _f, c in cites[rid]], "authored"))


def extract_contracts_markdown(path: str, text: str) -> Bag:
    """A bundle of prose contracts. Each part elaborates the requirements it cites anywhere
    (``Requirements: JDL-045, …`` sentences, ranges, inline citations); every markdown table row
    is a fragment, so a changed cell is a changed fragment. ``<req>|elaborated_by`` lists the
    citing parts. A part's ``Claim: <value>`` line is the claim of its citations (task-0214)."""
    b = Bag(short(path))
    cites: dict[str, list[tuple[str, str, str | None]]] = {}
    for rel, body in bundle_parts(text):
        name = rel or path
        ids = _ids_in(body)
        claim = _first_claim(_CLAIM_LINE, body, name)
        head = b.frag(f"{name}:cites", f"{name} cites {', '.join(ids)}" if ids else f"{name} cites no requirement")
        for rid in ids:
            cites.setdefault(rid, []).append((name, head, claim))
        for i, line in enumerate(body.splitlines(), 1):
            if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
                b.frag(f"{name}:row/{i}", line)
    _by_requirement(b, "elaborated_by", cites, lambda rid, names: f"{rid} is elaborated by {', '.join(names)}")
    return b


def extract_dmn_decisions(path: str, text: str) -> Bag:
    """A bundle of DMN 1.3 files: one ``decision_table`` entity per decision with its rule count
    (authored: the table's own structure), and ``<req>|decided_by`` for every requirement a rule's
    description cites, listing ``<decision>/<rule id>``. ``claim: <value>`` in a decision's own
    description is its rules' claim, in a rule's description that rule's (task-0214)."""
    b = Bag(short(path))
    ns = {"d": "https://www.omg.org/spec/DMN/20191111/MODEL/"}
    cites: dict[str, list[tuple[str, str, str | None]]] = {}
    for rel, body in bundle_parts(text):
        if not body.lstrip().startswith("<"):
            continue   # a README beside the tables
        root = ET.fromstring(body)
        for dec in root.iter(f"{{{ns['d']}}}decision"):
            dname = dec.get("name") or dec.get("id")
            ent = f"dmn:{dname}"
            b.ent(ent, "decision_table", dname)
            dclaim = _first_claim(_CLAIM_IN_TEXT, dec.findtext("d:description", default="", namespaces=ns), f"{rel or path} {dname}")
            rules = list(dec.iter(f"{{{ns['d']}}}rule"))
            frags, claims = [], []
            for r in rules:
                rid = r.get("id")
                desc = (r.findtext("d:description", default="", namespaces=ns) or "").strip()
                ins = [(i.findtext("d:text", default="", namespaces=ns) or "").strip() for i in r.findall("d:inputEntry", ns)]
                outs = [(o.findtext("d:text", default="", namespaces=ns) or "").strip() for o in r.findall("d:outputEntry", ns)]
                f = b.frag(f"{rel or path}:rule/{rid}", f"{rid}: {', '.join(ins)} -> {', '.join(outs)}" + (f" ({desc})" if desc else ""))
                frags.append(f)
                claim = _first_claim(_CLAIM_IN_TEXT, desc, f"{rel or path} {dname}/{rid}") or dclaim
                claims.append(claim)
                for req in _ids_in(desc):
                    cites.setdefault(req, []).append((f"{dname}/{rid}", f, claim))
            b.assertion(ent, "rules", str(len(rules)), f"{dname} has {len(rules)} rules", frags,
                        basis=_basis(claims or [dclaim], "authored"))
    _by_requirement(b, "decided_by", cites, lambda rid, names: f"{rid} is decided by {', '.join(names)}")
    return b


def extract_gherkin_tagged(path: str, text: str) -> Bag:
    """A bundle of feature files whose scenarios carry ``@<req>`` tags: one ``feature`` entity per
    part with its scenario count, and ``<req>|verified_by`` listing ``<feature>::<scenario>`` for
    every tagged scenario (authored: the suite's own links). The subject's ``[verification]
    derive_execution`` turns these into the execution map. An ``@claim:<value>`` tag on the Feature, a
    Rule or a Scenario is the claim of the scenarios under it, the nearest winning (task-0214)."""
    b = Bag(short(path))
    cites: dict[str, list[tuple[str, str, str | None]]] = {}
    for rel, body in bundle_parts(text):
        stem = _stem(rel) if rel else _stem(path)
        where = rel or path
        lines = body.splitlines()

        def tags_above(i: int) -> tuple[list[str], int]:
            tags, j = [], i - 1
            while j >= 0 and lines[j].strip().startswith("@"):
                tags = lines[j].split() + tags
                j -= 1
            return tags, j

        def claim_in(tags: list[str], at: str) -> str | None:
            return next((claim_of(t[len(_CLAIM_TAG):], f"{where} {at}") for t in tags if t.lower().startswith(_CLAIM_TAG)), None)

        n = 0
        frags, claims = [], []
        fclaim = rclaim = None
        for i, line in enumerate(lines):
            if re.match(r"\s*Feature:", line):
                fclaim = claim_in(tags_above(i)[0], "Feature")
                continue
            if re.match(r"\s*Rule:", line):
                rclaim = claim_in(tags_above(i)[0], line.strip())
                continue
            m = re.match(r"\s*Scenario(?: Outline)?: (.*)", line)
            if not m:
                continue
            n += 1
            title = m.group(1).strip()
            tags, j = tags_above(i)
            f = b.frag(f"{rel or path}:scenario/{n}", "\n".join(lines[j + 1:i + 1]).strip())
            frags.append(f)
            claim = claim_in(tags, f"scenario {title!r}") or rclaim or fclaim
            claims.append(claim)
            for t in tags:
                if _REQ_ID.fullmatch(t.lstrip("@")):
                    cites.setdefault(t.lstrip("@"), []).append((f"{stem}::{title}", f, claim))
        b.ent(f"feature:{stem}", "feature", stem)
        b.assertion(f"feature:{stem}", "scenarios", str(n), f"{stem} has {n} scenarios", frags,
                    basis=_basis(claims or [fclaim], "authored"))
    _by_requirement(b, "verified_by", cites, lambda rid, names: f"{rid} is verified by {', '.join(names)}")
    return b


_PUML_NAMES = {
    "sequence": re.compile(r"^\s*(?:participant|actor|boundary|control|entity|database|collections|queue)\s+(?:\"[^\"]+\"\s+as\s+)?(\w+)", re.M),
    "class": re.compile(r"^\s*(?:abstract\s+)?(?:class|interface|enum|component|package)\s+\"?([\w.]+)", re.M),
    "state": re.compile(r"^\s*state\s+\"?([\w ]+?)\"?(?:\s+as\s+(\w+))?\s*(?:\{|$)", re.M),
}


def extract_plantuml_realises(path: str, text: str) -> Bag:
    """A bundle of PlantUML diagrams: one ``diagram`` entity per part with its type (pumllint's
    parser), its title and the names it declares (authored: the diagram's own structure), and
    ``<req>|realised_by`` for every requirement the footer's ``realises`` list names. A ``' claim: <value>``
    comment line is the claim of the diagram's statements (task-0214)."""
    from pumllint import parser  # the product's parser, as a library
    b = Bag(short(path))
    cites: dict[str, list[tuple[str, str, str | None]]] = {}
    for rel, body in bundle_parts(text):
        stem = _stem(rel) if rel else _stem(path)
        claim = _first_claim(_CLAIM_COMMENT, body, rel or path)
        basis = _basis([claim], "authored")
        d = parser.parse_source(body, file_path=rel or path)[0]
        ent = f"diagram:{stem}"
        title = next((x.value for x in d.directives if getattr(x, "kind", "") == "title"), stem)
        b.ent(ent, "diagram", title)
        head = b.frag(f"{rel or path}:head", f"@startuml {stem}: {d.diagram_type}, {title}")
        b.assertion(ent, "type", d.diagram_type, title, [head], basis=basis)
        names = sorted(d.participants) if d.participants else []
        if not names:
            rx = _PUML_NAMES.get(d.diagram_type)
            if rx:
                names = sorted({(m[0] if isinstance(m, tuple) else m).strip() for m in rx.findall(body)} - {""})
        if d.diagram_type == "activity":
            names = [f"{len(d.activity_nodes or [])} activity nodes"]
        b.assertion(ent, "elements", "; ".join(names), f"{stem} declares {len(names)} elements", [head], basis=basis)
        foot = re.search(r"^\s*footer\b(.*)$", body, re.M)
        if foot:
            f = b.frag(f"{rel or path}:footer", foot.group(0).strip())
            for req in _ids_in(foot.group(1)):
                cites.setdefault(req, []).append((stem, f, claim))
    _by_requirement(b, "realised_by", cites, lambda rid, names: f"{rid} is realised by {', '.join(names)}")
    return b


EXTRACTORS = {   # mapper name (the subject manifest's) -> the deterministic mapper
    "requirements": extract_requirements,
    "decision_table": extract_decision_table,
    "spec": extract_spec,
    "openapi": extract_openapi,
    "sequence": extract_sequence,
    "containers": extract_containers,
    "bpmn": extract_bpmn,
    "dmn": extract_dmn,
    "gherkin": extract_gherkin,
    # a kit whose layers are folders, joined by requirement id (bundle_parts above)
    "requirements_json": extract_requirements_json,
    "contracts_markdown": extract_contracts_markdown,
    "dmn_decisions": extract_dmn_decisions,
    "gherkin_tagged": extract_gherkin_tagged,
    "plantuml_realises": extract_plantuml_realises,
}


def duplicate_locators(bag: Bag) -> list[str]:
    """The locators two or more of a document's fragments share (a duplicated row): the load would write
    one fragment id twice, so it is refused, by ``tools/check_subject.py`` and by ``extract_all``."""
    seen, dup = set(), []
    for f in bag.fragments:
        if f["locator"] in seen and f["locator"] not in dup:
            dup.append(f["locator"])
        seen.add(f["locator"])
    return dup


def extract_all(kit: dict[str, str], code_text: str) -> list[Bag]:
    bags = []
    mappers = SUBJECT.mappers
    for path, text in kit.items():
        mapper = mappers.get(path)
        if not mapper:
            continue
        if mapper != "links" and mapper not in EXTRACTORS:
            raise KeyError(f"{path}: no mapper named {mapper!r}; the harness has {sorted(EXTRACTORS) + ['links']}")
        try:
            bag = extract_links(path, text, code_text) if mapper == "links" else EXTRACTORS[mapper](path, text)
        except (UnknownClaim, ImportError):   # a claim names its own place; a missing library is the machine's
            raise
        except Exception as e:  # noqa: BLE001 — whatever the mapper raised, the document is named (I11)
            raise DocumentUnreadable(f"{path}: its mapper {mapper!r} cannot read it: {type(e).__name__}: {e}") from e
        if dup := duplicate_locators(bag):
            raise DocumentUnreadable(f"{path}: {len(dup)} locator(s) appear twice ({', '.join(dup[:5])}): "
                                     "a duplicated row; each statement's evidence needs its own place")
        bags.append(bag)
    return bags


if __name__ == "__main__":
    import sys
    from kitio import kit_for
    code = SUBJECT.reference_code()
    scenario = sys.argv[1] if len(sys.argv) > 1 else SUBJECT.order[0]
    for bag in extract_all(kit_for(scenario), code):
        print(f"== {bag.artefact}: {len(bag.fragments)} fragments, {len(bag.entities)} entities, {len(bag.assertions)} assertions")
        for a in bag.assertions:
            print(f"   {a['id']:48s} = {a['value'][:60]!s}")

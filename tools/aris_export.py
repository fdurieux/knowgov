"""A synthetic ARIS export of CargoQuote (task-0119): one AML file and two BPMN 2.0 files per
variant, for the ARIS connector (task-0063) to read into an instance as a dated mirror.

    python tools/aris_export.py [OUT] [--variant first|later|all] [--check]

OUT defaults to tools/fixtures/aris_cargo_quote, where the committed fixtures live; each variant
is written to OUT/<variant>/: cargo_quote.aml, quote_process.bpmn (this generator's own BPMN) and
quote_process.aris.bpmn (the same model in the dialect ARIS 10.0 was observed to write BPMN in,
render_bpmn's docstring; the reader meets both). --check writes
nothing: it regenerates in memory and exits 1 when a committed fixture differs (tests do the same).

Sources, public CargoQuote material only, read and never written:
  subjects/cargo_quote/vendor/kg_experiment/kit/quote_process.bpmn   the flow
  demo/register/{processes,capabilities,applications}/*.toml         the nodes whose [source]
                                                                     system is "kit" (CargoQuote's)
  demo/register/relationships/{realizes,supports}.toml               the links between them
The kit's BPMN carries no register ids; TASK_PROC below is this generator's reading of which kit
task is which register activity, the same reading the register's own evidence cites.

Variants:
  first  the export as of FIRST_DATE.
  later  the export as of LATER_DATE: PROC-0005 "Notify the shipper" (proposed in the register) is
         gone, with both its occurrences and its connections, the flow running from the stored
         quote's update straight to the end event; PROC-0004 is renamed "Calculate the quote
         price", its GUID and register id unchanged. task-0063's append-only and stale-id criteria
         read the pair: a vanished id is stale, a renamed object is an update, never a new one.

Identity: every GUID is uuid5(NAMESPACE, a stable key), so two runs give byte-identical files and
an object keeps its GUID across variants. The register id goes in the attribute AT_ID (ARIS's
"Identifier" attribute, which modellers fill by hand) on every process, capability, application
system type and person type that has one; step functions, events and rules carry none. The
attribute name is the connector's configuration, not a fact about any installation. In the BPMN
the end-to-end process's register id is the process @id and each activity's is its
<documentation> text: ARIS 10.0 kept both through an import and export and replaced every
element id (observed once, BPMN only); no register id is ever an element id, and nothing rests on
calledElement, timeCycle or process-level documentation, which it dropped or emptied.

SYNTHETIC: the header says so (ArisExeVersion, DatabaseName, UserName). The AML layout and the
type names (MT_EEPC, OT_EVT, OT_FUNC, OT_RULE with ST_OPR_XOR_1, OT_APPL_SYS_TYPE, OT_PERS_TYPE,
CT_ACTIV_1, CT_CRT_1, CT_IS_EVAL_BY_1, CT_LEADS_TO_1, CT_LNK_2, CT_CAN_SUPP_1, CT_EXEC_1, AT_NAME,
AT_DESC, AT_ID, the symbol numbers) follow the public descriptions of ARIS's XML export and are
UNVERIFIED against any ARIS method filter or installation. Read as used here:
  CT_ACTIV_1      event activates function           CT_CRT_1       function creates event
  CT_IS_EVAL_BY_1 event is evaluated by rule         CT_LEADS_TO_1  rule leads to event
  CT_LNK_2        process function -> the capability it realises (register `realizes`)
  CT_CAN_SUPP_1   application system type -> the process it supports (register `supports`)
  CT_EXEC_1       person type -> the process it owns (the register's `owner`)
The capability hierarchy and every other register relation stay the register's; the export does
not restate them. Standard library only.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parent.parent
KIT_BPMN = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "kit" / "quote_process.bpmn"
REGISTER = ROOT / "demo" / "register"
FIXTURES = ROOT / "tools" / "fixtures" / "aris_cargo_quote"
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/fdurieux/knowgov/aris-fixture/cargo_quote")
ID_ATTR = "AT_ID"
LOCALE = "1033"
KG_NS = "https://github.com/fdurieux/knowgov/aris-fixture"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
SYSTEM = "kit"   # the register's [source] system for CargoQuote's nodes

FIRST_DATE, LATER_DATE = "2026-11-04", "2026-11-18"
VARIANTS = {
    "first": {"date": FIRST_DATE, "drop": None, "rename": None},
    "later": {"date": LATER_DATE, "drop": "PROC-0005", "rename": ("PROC-0004", "Calculate the quote price")},
}
END_TO_END = "PROC-0001"
# the kit's tasks that are register activities; the two pricing and the two notification tasks are
# two occurrences of one function each
TASK_PROC = {"t_validate": "PROC-0002", "t_screen": "PROC-0003",
             "t_price_accept": "PROC-0004", "t_price_outage": "PROC-0004",
             "t_notify_quote": "PROC-0005", "t_notify_refusal": "PROC-0005"}
# the event a function creates before the next step (an EPC alternates events and functions; the
# kit's BPMN does not): keyed by the kit task, one event definition per name
POST = {"t_validate": "Request checked", "t_store": "Draft store attempted",
        "t_screen": "Screening answered", "t_price_accept": "Quote priced",
        "t_price_outage": "Quote priced", "t_update_quoted": "Stored quote set to quoted",
        "t_update_refused": "Stored quote set to refused_screening"}
SYMBOL = {"OT_FUNC": "ST_FUNC", "OT_EVT": "ST_EV", "OT_RULE": "ST_OPR_XOR_1",
          "OT_APPL_SYS_TYPE": "ST_APPL_SYS_TYPE", "OT_PERS_TYPE": "ST_EMPL_TYPE"}
SIZE = {"OT_FUNC": (180, 90), "OT_EVT": (180, 90), "OT_RULE": (60, 60),
        "OT_APPL_SYS_TYPE": (150, 70), "OT_PERS_TYPE": (150, 70)}
BPMN_SIZE = {"task": (100, 80), "exclusiveGateway": (50, 50), "startEvent": (36, 36), "endEvent": (36, 36)}


def guid(key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, key))


# ---- sources ----

def read_kit(path: Path = KIT_BPMN) -> tuple[dict, list]:
    """The kit's flow: nodes {id: (bpmn type, name)} in file order, flows [(id, source, target, name)]."""
    proc = ET.parse(path).getroot().find(f"{{{BPMN_NS}}}process")
    nodes, flows = {}, []
    for el in proc:
        tag = el.tag.split("}")[1]
        if tag == "sequenceFlow":
            flows.append((el.get("id"), el.get("sourceRef"), el.get("targetRef"), el.get("name") or ""))
        else:
            nodes[el.get("id")] = (tag, el.get("name"))
    return nodes, flows


def read_register(root: Path = REGISTER) -> dict:
    """CargoQuote's register nodes (processes, capabilities, application modules, the owners of
    the processes) and the realizes/supports pairs between them."""
    def folder(name: str) -> dict:
        out = {}
        for p in sorted((root / name).glob("*.toml")):
            d = tomllib.loads(p.read_text(encoding="utf-8"))
            if d.get("source", {}).get("system") == SYSTEM:
                out[d["id"]] = d
        return out
    procs, caps = folder("processes"), folder("capabilities")
    apps = {k: v for k, v in folder("applications").items() if v["kind"] == "module"}
    orgs = {}
    for p in procs.values():
        o = tomllib.loads((root / "organisation" / f"{p['owner']}.toml").read_text(encoding="utf-8"))
        orgs[o["id"]] = o
    ids = set(procs) | set(caps) | set(apps)

    def rel(name: str) -> list[tuple[str, str]]:
        rows = tomllib.loads((root / "relationships" / f"{name}.toml").read_text(encoding="utf-8"))
        rows = next(v for v in rows.values() if isinstance(v, list))
        return sorted((r["source"], r["target"]) for r in rows if r["source"] in ids and r["target"] in ids)
    return {"procs": procs, "caps": caps, "apps": apps, "orgs": dict(sorted(orgs.items())),
            "realizes": rel("realizes"), "supports": rel("supports")}


# ---- the variant's flow ----

def variant_flow(kit: tuple[dict, list], v: dict) -> tuple[dict, list]:
    """The kit's flow with the variant's dropped process bypassed (each of its tasks' incoming flow
    goes on to its single successor)."""
    nodes, flows = dict(kit[0]), list(kit[1])
    for t in [t for t, p in TASK_PROC.items() if p == v["drop"]]:
        (fin,) = [f for f in flows if f[2] == t]
        (fout,) = [f for f in flows if f[1] == t]
        flows = [(f[0], f[1], fout[2], f[3]) if f == fin else f for f in flows if f != fout]
        del nodes[t]
    return nodes, flows


def proc_name(reg: dict, pid: str, v: dict) -> str:
    return v["rename"][1] if v["rename"] and v["rename"][0] == pid else reg["procs"][pid]["name"]


# ---- the EPC as definitions, connections and occurrences ----

class Epc:
    def __init__(self) -> None:
        self.defs: dict[str, dict] = {}     # key -> {type, name, desc, rid, group, out: [(cxn key, type, target)]}
        self.occs: list[tuple[str, str]] = []   # (occ key, def key) in model order
        self.cxn_occs: list[tuple[str, str, str]] = []   # (source occ, cxn key, target occ)

    def obj(self, key: str, otype: str, name: str, group: str, desc: str = "", rid: str = "") -> str:
        self.defs.setdefault(key, {"type": otype, "name": name, "desc": desc, "rid": rid, "group": group, "out": []})
        return key

    def cxn(self, src: str, ctype: str, dst: str) -> str:
        key = f"{src}|{ctype}|{dst}"
        if (key, ctype, dst) not in self.defs[src]["out"]:
            self.defs[src]["out"].append((key, ctype, dst))
        return key

    def occ(self, key: str, d: str) -> str:
        if key not in [o for o, _ in self.occs]:
            self.occs.append((key, d))
        return key

    def link(self, so: str, ctype: str, do: str) -> None:
        sd, dd = dict(self.occs)[so], dict(self.occs)[do]
        self.cxn_occs.append((so, self.cxn(sd, ctype, dd), do))


def build_epc(reg: dict, flow: tuple[dict, list], v: dict) -> Epc:
    nodes, flows = flow
    e = Epc()
    P, C, A, O = "Processes", "Capabilities", "Application system types", "Organisation"
    # register objects first, so their order is the register's
    for pid, p in reg["procs"].items():
        if pid != v["drop"]:
            e.obj(f"node/{pid}", "OT_FUNC", proc_name(reg, pid, v), P, rid=pid)
    for cid, c in reg["caps"].items():
        e.obj(f"node/{cid}", "OT_FUNC", c["name"], C, rid=cid)
    for aid, a in reg["apps"].items():
        e.obj(f"node/{aid}", "OT_APPL_SYS_TYPE", a["name"], A, rid=aid)
    for oid, o in reg["orgs"].items():
        e.obj(f"node/{oid}", "OT_PERS_TYPE", o["name"], O, rid=oid)

    def fdef(t: str) -> str:
        pid = TASK_PROC.get(t)
        if pid:
            k = f"node/{pid}"
            kit_names = sorted({nodes[x][1] for x, q in TASK_PROC.items() if q == pid and x in nodes})
            e.defs[k]["desc"] = "Kit task: " + "; ".join(kit_names)
            return k
        return e.obj(f"func/{t}", "OT_FUNC", nodes[t][1], P)

    def evt(key: str, name: str, desc: str = "") -> str:
        return e.obj(f"evt/{key}", "OT_EVT", name, P, desc=desc)

    out = {}
    for f in flows:
        out.setdefault(f[1], []).append(f)
    # one occurrence per kit node (tasks, gateways as rules, start and end events)
    occ_of = {}
    for n, (tag, name) in nodes.items():
        if tag == "task":
            occ_of[n] = e.occ(f"occ/{n}", fdef(n))
        elif tag == "exclusiveGateway":
            occ_of[n] = e.occ(f"occ/{n}", e.obj(f"rule/{n}", "OT_RULE", "XOR", P, desc=name))
        else:
            occ_of[n] = e.occ(f"occ/{n}", evt(n, name))
    for n, (tag, name) in nodes.items():
        for fid, _, dst, label in out.get(n, []):
            dtag = nodes[dst][0]
            if tag == "startEvent":
                e.link(occ_of[n], "CT_ACTIV_1", occ_of[dst])
            elif tag == "exclusiveGateway":
                if dtag == "endEvent":
                    e.link(occ_of[n], "CT_LEADS_TO_1", occ_of[dst])
                else:
                    bo = e.occ(f"occ/{fid}", evt(f"branch/{fid}", label, desc=name))
                    e.link(occ_of[n], "CT_LEADS_TO_1", bo)
                    e.link(bo, "CT_ACTIV_1", occ_of[dst])
            elif dtag == "endEvent":
                e.link(occ_of[n], "CT_CRT_1", occ_of[dst])
            else:   # a task before a gateway or a task: the event it creates, then the next step
                po = e.occ(f"occ/post/{n}", evt(f"post/{POST[n]}", POST[n]))
                e.link(occ_of[n], "CT_CRT_1", po)
                e.link(po, "CT_IS_EVAL_BY_1" if dtag == "exclusiveGateway" else "CT_ACTIV_1", occ_of[dst])
    # register links, on definitions; the ones whose ends both have occurrences are drawn
    side = []
    for src, dst in reg["realizes"]:
        if f"node/{src}" in e.defs:
            e.cxn(f"node/{src}", "CT_LNK_2", f"node/{dst}")
    for src, dst in reg["supports"]:
        if f"node/{dst}" in e.defs:
            k = e.cxn(f"node/{src}", "CT_CAN_SUPP_1", f"node/{dst}")
            side.append((f"node/{src}", k, f"node/{dst}"))
    for pid, p in reg["procs"].items():
        if pid != v["drop"]:
            k = e.cxn(f"node/{p['owner']}", "CT_EXEC_1", f"node/{pid}")
            side.append((f"node/{p['owner']}", k, f"node/{pid}"))
    for src, k, dst in side:   # an application or owner beside every occurrence of its process
        for o, d in list(e.occs):
            if d == dst and o.startswith("occ/t_"):
                so = e.occ(f"{o}/{src}", src)
                e.cxn_occs.append((so, k, o))
    return e


# ---- layout ----

def layers(order: list[str], edges: list[tuple[str, str]]) -> dict[str, tuple[int, int]]:
    """(layer, row) per node: layer the longest path from a source, rows in order of first reach."""
    lay = {n: 0 for n in order}
    for _ in order:
        for s, d in edges:
            lay[d] = max(lay[d], lay[s] + 1)
    rows: dict[int, int] = {}
    pos = {}
    seen, queue = set(), [n for n in order if all(d != n for _, d in edges)]
    while queue:
        n = queue.pop(0)
        if n in seen:
            continue
        seen.add(n)
        pos[n] = (lay[n], rows.get(lay[n], 0))
        rows[lay[n]] = rows.get(lay[n], 0) + 1
        queue += [d for s, d in edges if s == n]
    return pos


# ---- AML ----

def _attr(t: str, value: str, ind: str) -> str:
    return f'{ind}<AttrDef AttrDef.Type="{t}">\n{ind}  <AttrValue LocaleId="{LOCALE}">{escape(value)}</AttrValue>\n{ind}</AttrDef>\n'


def _attrs(d: dict, ind: str) -> str:
    s = _attr("AT_NAME", d["name"], ind)
    if d.get("desc"):
        s += _attr("AT_DESC", d["desc"], ind)
    if d.get("rid"):
        s += _attr(ID_ATTR, d["rid"], ind)
    return s


def render_aml(reg: dict, e: Epc, v: dict) -> str:
    oid = {k: f"ObjDef.{guid('objdef/' + k)}" for k in e.defs}
    cid = {c[0]: f"CxnDef.{guid('cxndef/' + c[0])}" for d in e.defs.values() for c in d["out"]}
    incoming: dict[str, list[str]] = {}
    for k, d in e.defs.items():
        for c in d["out"]:
            incoming.setdefault(c[2], []).append(cid[c[0]])
    model_key = f"model/{END_TO_END}"
    mid = f"Model.{guid(model_key)}"
    date = v["date"]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>\n',
             '<!DOCTYPE AML SYSTEM "ARIS-Export.dtd">\n',
             "<!-- SYNTHETIC: generated by knowgov tools/aris_export.py from public CargoQuote material; not an export of any ARIS installation; type names unverified -->\n",
             "<AML>\n",
             f'  <Header-Info CreateTime="00:00:00" CreateDate="{date}" DatabaseName="SYNTHETIC CargoQuote" '
             f'UserName="synthetic" ArisExeVersion="SYNTHETIC (knowgov aris_export.py; no ARIS)" '
             f'ConfigurationName="SYNTHETIC" LanguageName="English"/>\n',
             f'  <Language Language.ID="LangID.{LOCALE}" LocaleId="{LOCALE}" Codepage="1252">\n'
             f'    <LanguageName>English</LanguageName>\n  </Language>\n']

    def group(key: str, name: str, body: str, ind: str) -> str:
        return (f'{ind}<Group Group.ID="Group.{guid("group/" + key)}">\n{ind}  <GUID>{guid("group/" + key)}</GUID>\n'
                + _attr("AT_NAME", name, ind + "  ") + body + f"{ind}</Group>\n")

    def objdef(k: str, ind: str) -> str:
        d = e.defs[k]
        extra = f' LinkedModels.IdRefs="{mid}"' if k == f"node/{END_TO_END}" else ""
        to = f' ToCxnDefs.IdRefs="{" ".join(incoming[k])}"' if k in incoming else ""
        s = (f'{ind}<ObjDef ObjDef.ID="{oid[k]}" TypeNum="{d["type"]}" SymbolNum="{SYMBOL[d["type"]]}"{to}{extra}>\n'
             f'{ind}  <GUID>{guid("objdef/" + k)}</GUID>\n' + _attrs(d, ind + "  "))
        for ck, ct, dst in d["out"]:
            s += (f'{ind}  <CxnDef CxnDef.ID="{cid[ck]}" CxnDef.Type="{ct}" ToObjDef.IdRef="{oid[dst]}">\n'
                  f'{ind}    <GUID>{guid("cxndef/" + ck)}</GUID>\n{ind}  </CxnDef>\n')
        return s + f"{ind}</ObjDef>\n"

    groups: dict[str, list[str]] = {}
    for k, d in e.defs.items():
        groups.setdefault(d["group"], []).append(k)
    # the model: occurrences laid out top to bottom along the flow
    ooid = {o: f"ObjOcc.{guid('objocc/' + o)}" for o, _ in e.occs}
    flow_edges = [(s, d) for s, _, d in e.cxn_occs if not (e.defs[dict(e.occs)[s]]["type"] in ("OT_APPL_SYS_TYPE", "OT_PERS_TYPE"))]
    flow_occs = [o for o, d in e.occs if e.defs[d]["type"] not in ("OT_APPL_SYS_TYPE", "OT_PERS_TYPE")]
    pos = layers(flow_occs, flow_edges)
    xy = {o: (100 + r * 520, 100 + l * 160) for o, (l, r) in pos.items()}
    side_n: dict[str, int] = {}
    for so, _, do in e.cxn_occs:
        if so not in xy:   # an application or owner, left of its function, one under the other
            n = side_n.get(do, 0)
            side_n[do] = n + 1
            xy[so] = (xy[do][0] + 200 + n * 160, xy[do][1] + 10)
    out_occ: dict[str, list] = {}
    for so, ck, do in e.cxn_occs:
        out_occ.setdefault(so, []).append((ck, do))
    m = (f'      <Model Model.ID="{mid}" Model.Type="MT_EEPC">\n        <GUID>{guid(model_key)}</GUID>\n'
         + _attr("AT_NAME", reg["procs"][END_TO_END]["name"], "        ")
         + _attr("AT_DESC", "SYNTHETIC end-to-end EPC read from the CargoQuote kit's quote_process.bpmn", "        "))
    for o, d in e.occs:
        w, h = SIZE[e.defs[d]["type"]]
        x, y = xy[o]
        m += (f'        <ObjOcc ObjOcc.ID="{ooid[o]}" ObjDef.IdRef="{oid[d]}" SymbolNum="{SYMBOL[e.defs[d]["type"]]}">\n'
              f'          <GUID>{guid("objocc/" + o)}</GUID>\n'
              f'          <Position Pos.X="{x}" Pos.Y="{y}"/>\n          <Size Size.dX="{w}" Size.dY="{h}"/>\n')
        for ck, do in out_occ.get(o, []):
            co = f"{o}|{ck}|{do}"
            m += (f'          <CxnOcc CxnOcc.ID="CxnOcc.{guid("cxnocc/" + co)}" CxnDef.IdRef="{cid[ck]}" ToObjOcc.IdRef="{ooid[do]}">\n'
                  f'            <GUID>{guid("cxnocc/" + co)}</GUID>\n          </CxnOcc>\n')
        m += "        </ObjOcc>\n"
    m += "      </Model>\n"
    body = ""
    for gname in ("Processes", "Capabilities", "Application system types", "Organisation"):
        inner = "".join(objdef(k, "        ") for k in groups.get(gname, []))
        if gname == "Processes":
            inner += "".join("  " + ln if ln else ln for ln in m.splitlines(keepends=True))
        body += group(f"cargo_quote/{gname}", gname, inner, "      ")
    top = group("cargo_quote", "CargoQuote (SYNTHETIC)", body, "    ")
    lines.append(group("root", "Main group", top, "  "))
    lines.append("</AML>\n")
    return "".join(lines)


# ---- BPMN ----

COLLAB = "collab_cargo_quote"   # ARIS 10.0 kept the collaboration id and the process ids
# the ARIS export dialect's extra namespaces: the prefixes are the ones ARIS 10.0 wrote; the URIs
# were not part of the evidence and are synthetic stand-ins here, so a reader must not key on them
ARIS_XMLNS = {p: f"urn:knowgov:synthetic:aris-dialect:{p}" for p in ("aris", "arisebpmn", "color", "deco", "i18n")}


def aris_id(v: dict, key: str) -> str:
    """An id of ARIS's form ID-<time-based uuid>, derived here (uuid5 bytes stamped version 1).
    Whether ARIS keeps such ids across two exports was not observed, so each variant gets its own:
    a reader that matched them across exports would fail on this fixture."""
    return "ID-" + str(uuid.UUID(bytes=uuid.uuid5(NAMESPACE, f"aris-id/{v['date']}/{key}").bytes, version=1))


def render_bpmn(reg: dict, e: Epc, flow: tuple[dict, list], v: dict, dialect: str = "knowgov") -> str:
    """The flow as BPMN 2.0 with DI. dialect "knowgov": this generator's own file (bpmn: prefix, the
    kit's ids, kg:guid and kg:registerId). dialect "aris": the same model as ARIS 10.0 writes BPMN
    after an import (observed once, BPMN only; task-0119's notes): semantic: prefix, every element,
    participant, flow and DI id replaced by ID-..., Shape_ID-..., Edge_ID-...; isExecutable and the
    kg: attributes gone; documentation with textFormat; colours, aris:port, label styles, xml:lang.
    In both, the end-to-end process's register id is the process @id, the one id that survives,
    and each activity's register id is its <documentation> text, which ARIS keeps verbatim."""
    aris = dialect == "aris"
    nodes, flows = flow
    ins: dict[str, list[str]] = {}
    outs: dict[str, list[str]] = {}
    for fid, s, d, _ in flows:
        outs.setdefault(s, []).append(fid)
        ins.setdefault(d, []).append(fid)
    pid = END_TO_END
    ident = (lambda k: aris_id(v, k)) if aris else (lambda k: k)
    q = "semantic" if aris else "bpmn"
    a = quoteattr
    part = ident("participant_cargo_quote")
    head = ("<!-- SYNTHETIC: generated by knowgov tools/aris_export.py from public CargoQuote material, "
            + ("mimicking the BPMN dialect ARIS 10.0 writes; not written by ARIS" if aris else "not an export of any ARIS installation")
            + " -->\n")
    ns = (f'xmlns:{q}="{BPMN_NS}" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
          'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
          'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    if aris:
        ns += "".join(f' xmlns:{k}="{u}"' for k, u in ARIS_XMLNS.items())
        root = (f'<{q}:definitions {ns} id="Definitions_{aris_id(v, "definitions")}" name="quote_process" '
                f'targetNamespace="http://www.softwareag.com/aris/bpmn2" exporter="ARIS" '
                f'exporterVersion="SYNTHETIC (knowgov aris_export.py, ARIS 10.0 dialect; no ARIS)" xml:lang="en">\n')
        collab_extra, proc_extra = ' arisebpmn:type="MT_ENTERPRISE_BPMN_COLLABORATION"', ""
    else:
        root = (f'<{q}:definitions {ns} xmlns:kg="{KG_NS}" id="defs_cargo_quote" targetNamespace="http://example.org/cargoquote" '
                f'exporter="SYNTHETIC knowgov aris_export.py" exporterVersion="{v["date"]}">\n')
        collab_extra = ""
        proc_extra = f' isExecutable="false" kg:registerId="{pid}" kg:guid="{guid("objdef/node/" + pid)}"'
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n', head, root,
           f'  <{q}:collaboration id="{COLLAB}"{collab_extra}>\n'
           f'    <{q}:participant id="{part}" name="CargoQuote" processRef="{pid}"/>\n  </{q}:collaboration>\n',
           f'  <{q}:process id="{pid}" name={a(proc_name(reg, pid, v))}{proc_extra}>\n']
    doc_attr = ' textFormat="text/plain"' if aris else ""
    for n, (tag, name) in nodes.items():
        p = TASK_PROC.get(n)
        if tag == "task":
            dkey = f"node/{p}" if p else f"func/{n}"
            name = proc_name(reg, p, v) if p else name
        elif tag == "exclusiveGateway":
            dkey = f"rule/{n}"
        else:
            dkey = f"evt/{n}"
        extra = "" if aris else (f' kg:registerId="{p}"' if p else "") + f' kg:guid="{guid("objdef/" + dkey)}"'
        default = ""
        if tag == "exclusiveGateway" and len(outs.get(n, [])) > 1:
            default = f' default="{ident(outs[n][-1])}"'
        s = f'    <{q}:{tag} id="{ident(n)}" name={a(name)}{default}{extra}>\n'
        if p:
            s += f"      <{q}:documentation{doc_attr}>{p}</{q}:documentation>\n"
        s += "".join(f"      <{q}:incoming>{ident(f)}</{q}:incoming>\n" for f in ins.get(n, []))
        s += "".join(f"      <{q}:outgoing>{ident(f)}</{q}:outgoing>\n" for f in outs.get(n, []))
        out.append(s + f"    </{q}:{tag}>\n")
    for fid, s, d, label in flows:
        nm = f" name={a(label)}" if label else ""
        ref = f'id="{ident(fid)}"{nm} sourceRef="{ident(s)}" targetRef="{ident(d)}"'
        if nodes[s][0] == "exclusiveGateway" and len(outs[s]) > 1 and fid != outs[s][-1]:
            out.append(f'    <{q}:sequenceFlow {ref}>\n'
                       f'      <{q}:conditionExpression xsi:type="{q}:tFormalExpression">{escape(label)}</{q}:conditionExpression>\n'
                       f'    </{q}:sequenceFlow>\n')
        else:
            out.append(f'    <{q}:sequenceFlow {ref}/>\n')
    out.append(f"  </{q}:process>\n")
    # diagram interchange: left to right along the flow, inside the participant's pool
    pos = layers(list(nodes), [(s, d) for _, s, d, _ in flows])
    box = {}
    for n, (l, r) in pos.items():
        w, h = BPMN_SIZE[nodes[n][0]]
        cx, cy = 190 + l * 170, 140 + r * 130
        box[n] = (cx - w // 2, cy - h // 2, w, h)
    px, py = 60, 60
    pw = max(x + w for x, _, w, _ in box.values()) + 40 - px
    ph = max(y + h for _, y, _, h in box.values()) + 40 - py
    num = (lambda n: f"{n}.0") if aris else str   # ARIS writes decimals
    sid = (lambda i: f"Shape_{i}") if aris else (lambda i: f"{i}_di")
    eid = (lambda i: f"Edge_{i}") if aris else (lambda i: f"{i}_di")
    colour = ' color:background-color="#FFFFFF" color:border-color="#000000"' if aris else ""
    label = '        <bpmndi:BPMNLabel labelStyle="LS_1"/>\n' if aris else ""

    def shape(el: str, x: int, y: int, w: int, h: int, more: str = "") -> str:
        return (f'      <bpmndi:BPMNShape id="{sid(el)}" bpmnElement="{el}"{more}{colour}>\n'
                f'        <dc:Bounds x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"/>\n'
                f'{label}      </bpmndi:BPMNShape>\n')
    out.append(f'  <bpmndi:BPMNDiagram id="{ident("diagram_quote_process")}">\n'
               f'    <bpmndi:BPMNPlane id="{ident("plane_quote_process")}" bpmnElement="{COLLAB}">\n')
    out.append(shape(part, px, py, pw, ph, ' isHorizontal="true"'))
    for n in nodes:
        out.append(shape(ident(n), *box[n]))
    for fid, s, d, _ in flows:
        sx, sy, sw, sh = box[s]
        dx, dy, dw, dh = box[d]
        p1, p2 = (sx + sw, sy + sh // 2), (dx, dy + dh // 2)
        pts = [p1, p2] if p1[1] == p2[1] else [p1, (p1[0] + 15, p1[1]), (p1[0] + 15, p2[1]), p2]
        port = ' aris:port="0"' if aris else ""
        out.append(f'      <bpmndi:BPMNEdge id="{eid(ident(fid))}" bpmnElement="{ident(fid)}"{port}>\n'
                   + "".join(f'        <di:waypoint x="{num(x)}" y="{num(y)}"/>\n' for x, y in pts)
                   + label + "      </bpmndi:BPMNEdge>\n")
    out.append("    </bpmndi:BPMNPlane>\n")
    if aris:
        out.append('    <bpmndi:BPMNLabelStyle id="LS_1">\n      <dc:Font name="Arial" size="8" isBold="false" '
                   'isItalic="false" isUnderline="false" isStrikeThrough="false"/>\n    </bpmndi:BPMNLabelStyle>\n')
    out.append(f"  </bpmndi:BPMNDiagram>\n</{q}:definitions>\n")
    return "".join(out)


# ---- entry points ----

def generate(variant: str) -> dict[str, str]:
    """{file name: text} for one variant."""
    v = VARIANTS[variant]
    reg = read_register()
    flow = variant_flow(read_kit(), v)
    e = build_epc(reg, flow, v)
    return {"cargo_quote.aml": render_aml(reg, e, v), "quote_process.bpmn": render_bpmn(reg, e, flow, v),
            "quote_process.aris.bpmn": render_bpmn(reg, e, flow, v, "aris")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write the synthetic CargoQuote ARIS export (task-0119).")
    ap.add_argument("out", nargs="?", type=Path, default=FIXTURES)
    ap.add_argument("--variant", choices=[*VARIANTS, "all"], default="all")
    ap.add_argument("--check", action="store_true", help="compare with OUT instead of writing; exit 1 on a difference")
    args = ap.parse_args(argv)
    bad = []
    for name in (VARIANTS if args.variant == "all" else [args.variant]):
        for fname, text in generate(name).items():
            p = args.out / name / fname
            if args.check:
                if not p.is_file() or p.read_bytes() != text.encode("utf-8"):
                    bad.append(p)
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(text.encode("utf-8"))
    for p in bad:
        print(f"differs from the generator: {p}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

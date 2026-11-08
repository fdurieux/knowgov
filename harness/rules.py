"""The seven rules of pre-registration §4, run after every load.

Each rule reads and writes through the store port (store.py); the adapter holds the
statements. R-CORROBORATE and R-CONFLICT fetch candidate pairs and decide value
compatibility in Python (``compatible``), because a behaviour value is a ``k=v;k=v``
string. Status is set only by the loaders, the rules and recorded human acts.

A person's statement (basis ``elicited``, version ``capture``; load.py ``load_captures``) is paired
with the documents' extracted statements of any version (task-0038, doc-0007 F3): one that
contradicts a document raises a conflict gap naming both, so a reviewer sees every side
(decision-0002); one that agrees is recorded as corroborating, and neither side rises (a person's
statement stays proposed until a review approves it). "Nobody knows" (an empty value) is no value
and pairs with nothing.
"""

from __future__ import annotations

import re

from extract import NONE
from subject import SUBJECT

VAGUE = list(SUBJECT.rules.get("vague_words", []))

# a declared gap on a requirement also concerns the key it governs (the subject's [rules.requirement_keys])
REQ_KEY = dict(SUBJECT.rules.get("requirement_keys", {}))
DECLARED_GAP_ID = SUBJECT.rules.get("declared_gap_id", "gap:declared:open")
DECLARED_GAP_TEXT = SUBJECT.rules.get("declared_gap_text", "{req} is declared open")


def _fields(v: str) -> dict | None:
    if "=" in v and ";" in v or re.fullmatch(r"\w+=[^;]*", v):
        return dict(p.split("=", 1) for p in v.split(";") if "=" in p)
    return None


NUMERIC = {"min", "max", "threshold", "surcharge", "factor", "rounding"}


def _is_num(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def compatible(a: str, b: str, predicate: str = "") -> str:
    """'equal' | 'conflict' | 'incomparable' for two values of one key.
    A numeric predicate with a non-numeric side (vague text, an
    unresolved symbol) is incomparable: R-VAGUE flags it, nothing
    corroborates or contradicts it."""
    if a == b:
        return "equal"
    if predicate in NUMERIC and not (_is_num(a) and _is_num(b)):
        return "incomparable"
    fa, fb = _fields(a), _fields(b)
    if fa is not None and fb is not None:
        shared = set(fa) & set(fb)
        if not shared:
            return "incomparable"
        if all(fa[k] == fb[k] for k in shared):
            return "equal" if len(shared) >= 2 else "incomparable"
        return "conflict"
    # numbers written differently (316.00 vs 316)
    try:
        return "equal" if float(a) == float(b) else "conflict"
    except ValueError:
        pass
    if a == NONE or b == NONE:
        return "conflict"
    return "conflict"


def r_struct(st) -> list[dict]:
    return st.structural_violations()


PERSON = "elicited"      # a capture's basis (load.py load_captures)
DOCUMENT = "extracted"


def pairs(st):
    """(pair, whether one side is a person's): document pairs as before, and a person's statement
    against a document's; a person's empty answer ("nobody knows") pairs with nothing."""
    for p in st.candidate_pairs(across=PERSON):
        if any(b == PERSON and v == "" for b, v in ((p["ba"], p["va"]), (p["bb"], p["vb"]))):
            continue
        bases = (p["ba"], p["bb"])
        person = bases.count(PERSON) == 1
        if person and DOCUMENT not in bases:
            continue
        yield p, person


def r_corroborate(st) -> int:
    n = 0
    for p, person in pairs(st):
        if person or (p["ba"] == DOCUMENT and p["bb"] == DOCUMENT):
            if compatible(p["va"], p["vb"], p["pred"]) == "equal":
                st.corroborate(p["a"], p["b"], promote=not person)   # a person agreeing raises nothing
                n += 1
    return n


def r_conflict(st, scenario: str) -> list[dict]:
    out = []
    for p, person in pairs(st):
        if compatible(p["va"], p["vb"], p["pred"]) == "conflict":
            # decision-0020: every conflict is named by its two statements, sorted, a person's or two documents';
            # the id is the same on every store and every run of the same statements
            lo, hi = sorted((p["a"], p["b"]))
            gid = f"gap:conflict:{p['key']}:{lo}~{hi}"
            text = (f"a person and a document state different values for {p['key']}: "
                    f"{p['aa']} says {p['va']}; {p['ab']} says {p['vb']}") if person else None
            st.mark_conflict(p["a"], p["b"], gid, p["key"], scenario, text)
            out.append({"key": p["key"], "a": p["a"], "va": p["va"], "b": p["b"], "vb": p["vb"]})
    return out


def r_vague(st, scenario: str) -> list[dict]:
    out = []
    for row in st.vague_fragments(VAGUE):
        w = [v for v in VAGUE if v in row["text"].lower()]
        st.add_ambiguous_gap(row["id"], f"vague wording ({', '.join(w)}) in {row['fid']}", scenario)
        out.append({"id": row["id"], "key": row["key"], "words": w})
    for row in st.unresolved_assertions():
        st.add_ambiguous_gap(row["id"], f"symbol {row['sym']} has no definition in any artefact", scenario)
        out.append({"id": row["id"], "key": row["key"], "words": [f"unresolved {row['sym']}"]})
    return out


def r_req(st, scenario: str) -> list[dict]:
    out = []
    # declared gaps: a requirement whose text says it is not yet specified
    for row in st.declared_open("specified"):
        key = REQ_KEY.get(row["entity"])
        st.add_declared_gap(DECLARED_GAP_ID, DECLARED_GAP_TEXT.format(req=row["entity"]), row["entity"], row["id"], scenario,
                            key.split("|")[0] if key else row["entity"], key or "")
        out.append({"kind": "missing", "declared": True, "req": row["entity"], "key": key})
    # an artefact declared not yet authored
    for row in st.declared_open("authored"):
        st.add_absent_artefact_gap(row["entity"], row["id"])
        out.append({"kind": "missing", "declared": True, "artefact": row["entity"]})
    # every requirement needs a verifying scenario
    for req in st.requirements_without("verified_by"):
        st.add_unverified_requirement_gap(req)
        out.append({"kind": "missing", "declared": False, "req": req, "why": "no verifying scenario"})
    # every decision row and pricing step is spoken about
    for eid in st.silent_entities(["decision_row", "pricing_step"]):
        out.append({"kind": "missing", "declared": False, "entity": eid})
    return out


def r_unverified(st) -> int:
    return st.mark_unverified()


def r_stale(st, new_tag: str, at: str | None = None) -> dict:
    """After a re-ingestion: an assertion of an older version whose
    supporting fragment's digest differs from the current fragment at the
    same locator (or whose locator vanished) is invalidated; its
    verifications end; derived outputs that used it become suspect.
    ``at`` is the change's instant, recorded as ``invalidated_at``."""
    return st.invalidate_stale(new_tag, at)


def run_all(st, scenario: str) -> dict:
    out = {"R-STRUCT": r_struct(st)}
    out["R-CORROBORATE"] = r_corroborate(st)
    out["R-CONFLICT"] = r_conflict(st, scenario)
    out["R-VAGUE"] = r_vague(st, scenario)
    out["R-REQ"] = r_req(st, scenario)
    out["R-UNVERIFIED"] = r_unverified(st)
    return out


def census(st) -> dict:
    return st.census()

"""A person's review of what the store holds (task-0037), under knowgov decision-0002 and
ieam-register decision 0009: who may approve what a person gave, close a declared gap, or settle
a dispute, and what is refused.

A review file sits beside the captures, in ``<capture dir>/reviews/``, and is never edited after
it is written (``python harness/capture.py review FILE`` checks and writes it):

    [review]
    by = "employee-2"            # an issued handle (the register's people/handles.toml), never a name
    on = 2026-11-09
    record = "decisions/0012-outage-rule.md"   # where the reasons are kept
    scenario = "S2"              # the scenario whose store it rules on; omitted: every load

    [[ruling]]
    assertion = "A:cap:2026-11-02-ORG-0002-employee-1:1@capture"
    outcome = "approved"         # approved | rejected | referred
    note = ""

    [[closes]]
    gap = "gap:declared:OD-1"

``check`` refuses a file whole, each reason naming the rule it breaks (decision-0002 point 5):

- ``by`` not issued, withdrawn by ``on``, or issued after it; ``on`` in the future;
- a ruling on an assertion the store does not hold, or an outcome not in the three;
- a ruling on a person's statement by a handle without ``approves``, or by the handle that gave it;
- a ruling on a document's statement, or on a disputed one, by a handle without ``closes``;
- a ruling by a unit that does not own the key (the subject's ``register_map.toml``);
- a close by a handle without ``closes``, or by a unit other than the gap's owner: the owner the
  declaration names, else the key's owners; a named owner that is no unit of the register is
  refused, and the refusal says so;
- a dispute left half-settled (a disputed statement of a ruled key left unruled, or referred), or
  settled on two values that conflict.

An approval of a person's statement holds until six months after the capture's ``on``
(ieam-register decision 0008); after that the load leaves it proposed (``lapsed``).
"""
from __future__ import annotations

import datetime as dt
import os
import re
import tomllib
from pathlib import Path

OUTCOMES = ("approved", "rejected", "referred")
PERSON = "elicited"          # the basis a capture's statements carry (harness/load.py load_captures)
LAPSE_MONTHS = 6             # ieam-register decision 0008, lifecycle.toml [review.evidence] elicited


def add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(d.year + y, m + 1, day)
        except ValueError:
            continue
    raise ValueError(d)


def today() -> dt.date:
    """KG_TODAY (YYYY-MM-DD) for a reproducible run, else the wall clock."""
    v = os.environ.get("KG_TODAY")
    return dt.date.fromisoformat(v) if v else dt.date.today()


def _date(v) -> dt.date | None:
    if isinstance(v, dt.date) and not isinstance(v, dt.datetime):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError:
        return None


def issued_handles(register: Path) -> dict[str, dict] | None:
    """handle -> {unit, roles, issued, withdrawn} from the register's issued list (decision 0009);
    None when the register names no list or the list is missing."""
    try:
        types = tomllib.loads((register / "metamodel" / "types.toml").read_text(encoding="utf-8"))
    except OSError:
        return None
    rel = types.get("elicited", {}).get("issued")
    if not rel or not (register / rel).exists():
        return None
    out = {}
    for h in tomllib.loads((register / rel).read_text(encoding="utf-8")).get("handle", []):
        out[h["handle"]] = {"unit": h.get("unit", ""), "roles": set(h.get("roles", [])),
                            "issued": _date(h.get("issued")), "withdrawn": _date(h.get("withdrawn"))}
    return out


def organisation_units(register: Path) -> dict[str, str]:
    """unit id -> name, for the register's organisation nodes."""
    out = {}
    for p in sorted((register / "organisation").glob("*.toml")):
        n = tomllib.loads(p.read_text(encoding="utf-8"))
        if "id" in n:
            out[n["id"]] = n.get("name", "")
    return out


def gap_owner(text: str, units: dict[str, str]) -> tuple[list[str] | None, str]:
    """(the units the declaration names as owner, or None when it names none; the name as written).
    A named owner matches a unit by id or by name; one that matches none gives []."""
    m = re.search(r"owner:\s*([^)]+?)\s*(?:\)|$)", text)
    if not m:
        return None, ""
    named = m.group(1).strip()
    low = named.lower()
    return sorted(u for u, name in units.items() if low == u.lower() or (low and low in name.lower())), named


def capture_index(capture_dir: Path) -> dict[str, dict]:
    """assertion id -> {from, on} for every captured answer (the ids load_captures gives them)."""
    out = {}
    for p in sorted(capture_dir.glob("*.toml")) if capture_dir.is_dir() else []:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        cap = c.get("capture", {})
        for i, _a in enumerate(c.get("answer", []), 1):
            out[f"A:cap:{p.stem}:{i}@capture"] = {"from": cap.get("from"), "on": _date(cap.get("on"))}
    return out


def check(doc: dict, st, *, handles: dict | None, owners: dict[str, list[str]], units: dict[str, str],
          captures: dict[str, dict], now: dt.date, compatible) -> tuple[list[str], dict]:
    """(reasons for refusal, the normalised review). ``st`` is a loaded store; ``owners`` key -> the
    units owning its register nodes; ``compatible`` is rules.compatible."""
    errs: list[str] = []
    r = doc.get("review", {})
    by, on, record = str(r.get("by", "")), _date(r.get("on")), str(r.get("record", "")).strip()
    rulings = [dict(x) for x in doc.get("ruling", [])]
    closes = [dict(x) for x in doc.get("closes", [])]
    norm = {"by": by, "on": on, "record": record, "scenario": str(r.get("scenario", "")), "rulings": rulings, "closes": closes}
    if handles is None:
        return ["no issued-handle list in the register (decision 0009): a ruling needs an issued handle"], norm
    h = handles.get(by)
    if on is None:
        errs.append(f"review.on {r.get('on')!r} is not a date (YYYY-MM-DD)")
    elif on > now:
        errs.append(f"review.on {on} is in the future")
    if not record:
        errs.append("review.record is empty: name where the reasons are kept (decision-0002 point 1)")
    if h is None:
        errs.append(f"review.by {by!r} is not an issued handle (decision 0009): a ruling is a person's act, never a model's or a name's")
    elif on is not None:
        if h["issued"] and h["issued"] > on:
            errs.append(f"review.by {by} was issued on {h['issued']}, after the review's date {on}")
        if h["withdrawn"] and h["withdrawn"] <= on:
            errs.append(f"review.by {by} was withdrawn on {h['withdrawn']}")
    if not rulings and not closes:
        errs.append("the review has no ruling and closes no gap")
    roles, unit = (h["roles"], h["unit"]) if h else (set(), "")

    briefs: dict[str, dict] = {}
    for i, ru in enumerate(rulings, 1):
        aid, outcome = str(ru.get("assertion", "")), str(ru.get("outcome", ""))
        where = f"ruling {i} ({aid})"
        if outcome not in OUTCOMES:
            errs.append(f"{where}: outcome {outcome!r} is not one of {', '.join(OUTCOMES)}")
        b = st.assertion_brief(aid)
        if b is None:
            errs.append(f"{where}: the store holds no assertion {aid!r}")
            continue
        if aid in briefs:
            errs.append(f"{where}: ruled twice in one review")
        briefs[aid] = {**b, "outcome": outcome}
        if h is None:
            continue
        key_owners = owners.get(b["key"], [])
        if unit not in key_owners:
            errs.append(f"{where}: {by}'s unit {unit} does not own {b['key']} (owners: {', '.join(key_owners) or 'none in the register map'})")
        if b["basis"] == PERSON:
            giver = captures.get(aid, {}).get("from") or b["agent"]
            if giver == by:
                errs.append(f"{where}: {by} gave this statement and may not rule on it (decision-0002 point 2)")
            if "approves" not in roles:
                errs.append(f"{where}: {by} lacks the role approves, which a ruling on what a person gave needs")
        elif outcome != "referred" and "closes" not in roles:
            errs.append(f"{where}: {b['key']} is a document's statement ({b['basis']}); overruling or approving it needs the role closes, which {by} lacks")
        if b["status"] == "disputed" and outcome != "referred" and "closes" not in roles:
            errs.append(f"{where}: settling a dispute needs the role closes, which {by} lacks (decision-0002 point 4)")

    # a dispute is settled whole: every disputed statement of the key ruled, the kept ones agreeing
    for key in sorted({b["key"] for b in briefs.values() if b["status"] == "disputed"}):
        disputed = [x["id"] for x in st.key_evidence(key, ["disputed"])]
        left = [x for x in disputed if x not in briefs or briefs[x]["outcome"] == "referred"]
        if left:
            errs.append(f"{key}: the dispute is half-settled, {len(left)} disputed statement(s) left unruled ({', '.join(left)}); "
                        "rule on every side, approving what is kept and rejecting the rest, or the key stays disputed")
        kept = [briefs[x]["value"] for x in disputed if x in briefs and briefs[x]["outcome"] == "approved"]
        kept += [b["value"] for b in briefs.values() if b["key"] == key and b["status"] != "disputed" and b["outcome"] == "approved"]
        if any(compatible(a, c, key.split("|", 1)[1]) == "conflict" for i, a in enumerate(kept) for c in kept[i + 1:]):
            errs.append(f"{key}: the statements approved disagree with each other; a settlement keeps one value")

    for i, c in enumerate(closes, 1):
        gid = str(c.get("gap", ""))
        where = f"closes {i} ({gid})"
        g = st.declared_gap(gid)
        if g is None:
            errs.append(f"{where}: the store holds no open declared gap {gid!r}")
            continue
        if h is None:
            continue
        if "closes" not in roles:
            errs.append(f"{where}: {by} lacks the role closes (decision-0002 point 3)")
        named_units, named = gap_owner(g["text"], units)
        if named_units is None:
            allowed = sorted({u for k in g["keys"] for u in owners.get(k, [])})
            if unit not in allowed:
                errs.append(f"{where}: the gap names no owner, so the key's owners close it ({', '.join(allowed) or 'none'}); {by}'s unit is {unit}")
        elif not named_units:
            errs.append(f"{where}: the declaration names {named!r} as its owner, which is no unit of the register; "
                        "only that owner closes it, so the register needs the unit and a handle of it with closes")
        elif unit not in named_units:
            errs.append(f"{where}: the declaration names {named!r} ({', '.join(named_units)}) as its owner; {by}'s unit is {unit}")
    return errs, norm


def until_for(brief: dict, captures: dict[str, dict]) -> dt.date | None:
    """When an approval of the statement lapses: six months after a capture's on; never otherwise."""
    if brief["basis"] != PERSON:
        return None
    on = captures.get(brief["id"], {}).get("on")
    return add_months(on, LAPSE_MONTHS) if on else None


def review_toml(norm: dict) -> str:
    import json
    q = lambda s: json.dumps(s, ensure_ascii=False)  # noqa: E731 — JSON's escaping is TOML's
    lines = ["# A review: a person's rulings on what the store holds (task-0037, decision-0002). Read by every load",
             "# of its scenario. Never edited after it is written: a change of mind is a new review.",
             "", "[review]", f"by = {q(norm['by'])}", f"on = {norm['on'].isoformat()}", f"record = {q(norm['record'])}"]
    if norm["scenario"]:
        lines.append(f"scenario = {q(norm['scenario'])}")
    for ru in norm["rulings"]:
        lines += ["", "[[ruling]]", f"assertion = {q(str(ru.get('assertion', '')))}", f"outcome = {q(str(ru.get('outcome', '')))}",
                  f"note = {q(str(ru.get('note', '')))}"]
    for c in norm["closes"]:
        lines += ["", "[[closes]]", f"gap = {q(str(c.get('gap', '')))}", f"note = {q(str(c.get('note', '')))}"]
    return "\n".join(lines) + "\n"

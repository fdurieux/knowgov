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
    key = "QuoteAPI|on_screening_outage"   # what the ruling ruled on (task-0199, doc-0030 H5): written by the command
    giver = "employee-1"         # a captured answer's giver, from the capture's own content (decision-0038 G1): written by the command
    value = "priced=yes;status=held_unscreened;notified=no;hold=true"
    sha256 = "e3b0c442..."       # ``content_digest`` of its supporting fragments
    outcome = "approved"         # approved | rejected | referred
    note = ""

    [[closes]]
    gap = "gap:declared:OD-1"
    sha256 = "..."               # the declaration's text, digested

    [[resolves]]                 # a pre-load finding kept as a gap (task-0216, decision-0018 point 5)
    gap = "lint:behavior/quote_flow.puml@v1:0123456789abcdef"
    resolution = "choice"        # choice (the record is the decision) | exception | open; a slip is a new version
    sha256 = "..."               # the finding's text, digested
    note = ""

A ruling binds to content, not to its id (task-0199, doc-0030 F2): every load binds it (``bind``) to the statement
of its key with its value and digest, the one it names when that one still holds them, else the one
statement that does (a reordered table, a renumbered answer); one that changed or vanished is not applied,
and the load records it for the gate (``act`` findings, never stderr only). A close binds to its gap's
text the same way. A captured answer has no fragments, so its ``sha256`` is the empty text's digest
(``e3b0c442...``) and two people's identical answers hold the same content: a ruling on one binds by giver, key and
value, so only the same person's answer stands in for it when its id has vanished (a re-ingested capture), never
another person's (task-0302, decision-0032 C2-1); that ruling reads ``gone``, an act finding naming the vanished
id. The giver is the one the ruling records (``giver``), which ``capture.py review`` reads from the capture's own content
(``[capture] from``, the signed ``[answered]`` handle), never from its file name (task-0320, decision-0038 G1), so a
handle ``X`` and a handle ``X-n`` never share a reading; a ruling without it (a file written before) keeps the stem's
rule, so a stem that reads as two givers binds nowhere (task-0308) and is refused the day a review is written when no
capture file holds the answer (task-0310). Read rule for a file written before 0.9.0, with no ``key``, ``value`` or ``sha256``:
it binds by id as it did, and the gate lists it at info as bound by id only; a new review binds it.

``capture.py review`` refuses a file whole, each reason naming the rule it breaks (decision-0002 point 5);
a load refuses it whole for the same reasons, but applies the rest of a review one of whose acts no longer
binds:

- ``by`` not issued, withdrawn by ``on``, or issued after it; ``on`` in the future;
- a ruling on an assertion the store does not hold, or whose content is no longer the one it records, or
  an outcome not in the three;
- a ruling other than rejected or referred on a statement of basis inferred, assumed or hypothesised: a
  model's statement is never promoted (doc-0030 I4);
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

import dates     # task-0262: one strict YYYY-MM-DD parse
import formats   # task-0174, decision-0023

OUTCOMES = ("approved", "rejected", "referred")
RESOLUTIONS = ("choice", "exception", "open")   # task-0216: a lint gap's resolution by review; a slip is a new version
PERSON = "elicited"          # the basis a capture's statements carry (harness/load.py load_captures)
NEVER_PROMOTED = ("inferred", "assumed", "hypothesised")   # a ruling may reject or refer one, never approve it (I4)
CURRENT = ("proposed", "validated", "verified", "approved", "disputed", "rejected")   # what a ruling lands on: never invalidated
EVERY = (*CURRENT, "invalidated")
LAPSE_MONTHS = 6             # ieam-register decision 0008, lifecycle.toml [review.evidence] elicited


def add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(d.year + y, m + 1, day)
        except ValueError:
            continue
    raise ValueError(d)


CLOCK = "KG_CLOCK"         # "pinned": a check's run, where the wall clock is refused (task-0075)


class WallClock(RuntimeError):
    """Today's date was asked for under ``KG_CLOCK=pinned`` with no ``KG_TODAY``."""


def _pinned() -> bool:
    """KG_CLOCK through switches (task-0287): ``pinned`` exactly; empty or unset reads the wall clock; any other
    value is BadSwitch, so ``Pinned`` or ``1`` no longer read the wall clock silently."""
    import switches
    return switches.on(CLOCK)


def today() -> dt.date:
    """KG_TODAY (YYYY-MM-DD) for a reproducible run, else the wall clock: the one place under
    harness/ that reads it (tests/test_clock.py holds that). Under ``KG_CLOCK=pinned`` (every check
    CI runs, and the test runner) a missing KG_TODAY raises WallClock instead, so a check whose
    outcome would move with the calendar fails at once rather than on the day it moves."""
    v = os.environ.get("KG_TODAY")
    if v:
        return dates.parse(v, "KG_TODAY")   # task-0262: YYYY-MM-DD only, refused naming the value
    if _pinned():
        raise WallClock("KG_CLOCK=pinned and no KG_TODAY: this check reads today's date and must pin it "
                        "(KG_TODAY, or --as-of record; task-0075)")
    return dt.date.today()


def now() -> dt.datetime:
    """KG_NOW (an ISO instant; a naive one is UTC) for a reproducible read, else the wall clock in UTC;
    under ``KG_CLOCK=pinned`` a missing KG_NOW raises WallClock, as ``today()`` does. The instant a
    reader compares a run's heartbeat with (harness/runs_index.py, task-0128); no date is read from it."""
    v = os.environ.get("KG_NOW")
    if v:
        t = dt.datetime.fromisoformat(v)
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    if _pinned():
        raise WallClock("KG_CLOCK=pinned and no KG_NOW: this read compares a run's heartbeat with the clock "
                        "and must pin it (KG_NOW; task-0128)")
    return dt.datetime.now(dt.timezone.utc)


def pinned(env, on) -> dict:
    """``env`` for a check's commands: today is ``on`` (a date or YYYY-MM-DD) and the wall clock is
    refused (task-0075)."""
    return {**env, "KG_TODAY": str(on), CLOCK: "pinned"}


def _date(v) -> dt.date | None:
    if isinstance(v, dt.date) and not isinstance(v, dt.datetime):
        return v
    return dates.parse(v) if dates.is_date(v) else None   # task-0262


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


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_digest(fragments) -> str:
    """What a ruling binds to beside its value (task-0199): ``store.content_digest``, the one digest trace's
    ledger records too, so a ruling and a derived output name a statement's content alike."""
    from store import content_digest as digest
    return digest(fragments)


def statement(st, aid: str) -> dict | None:
    """``assertion_brief`` with its ``sha256`` (``content_digest``), or None when the store holds no ``aid``."""
    b = st.assertion_brief(aid)
    if b is None:
        return None
    row = next((r for r in st.key_evidence(b["key"], list(EVERY)) if r["id"] == aid), None)
    return {**b, "sha256": content_digest((row or {}).get("fragments") or [])}


def _stem(aid: str) -> str:
    return aid.rsplit("@", 1)[0]


# a capture's file stem, harness/capture.py ingest's: {on}-{owner unit}-{handle}, a second file the same day -<n>
_CAPTURE_STEM = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}-(?:[A-Z][A-Z0-9]*-[0-9]+|unassigned)-(?P<giver>.+)")   # ASCII digits


def _giver(aid: str) -> str | None:
    """The handle a captured answer's id names (``A:cap:<file stem>:<n>@capture``), read whole; None for another id."""
    if not aid.startswith("A:cap:"):
        return None
    m = _CAPTURE_STEM.fullmatch(_stem(aid)[len("A:cap:"):].rsplit(":", 1)[0])
    return m["giver"] if m else None


def _ambiguous_giver(aid: str, handles: dict | None) -> bool:
    """Whether the id's stem reads as two givers (task-0308): the whole tail is a handle, and the tail without a
    trailing ``-<n>`` (capture.py's second-file-the-day suffix) is an issued handle too, so ``…-ops-2`` is ``ops-2``'s
    first file or ``ops``'s second. With no issued list the second reading cannot be told and is not assumed."""
    g = _giver(aid)
    m = re.fullmatch(r"(.+)-[0-9]+", g) if g else None
    return bool(m and handles and g in handles and m[1] in handles)


def _ambiguous_reason(aid: str) -> str:
    """Why a review of an ambiguous-stem answer is refused the day it is written (task-0310): no capture file holds
    the answer, so its giver cannot be read from content and recorded (decision-0038 G1)."""
    g = _giver(aid)
    return (f"the id's stem reads as two givers, giver {g}'s first answer or giver {re.fullmatch(r'(.+)-[0-9]+', g)[1]}'s "
            "second that day, and no capture file holds the answer to read its giver from; a review records the giver "
            "the capture's own content names (decision-0038), so nothing is written")


def giver_of(ru: dict) -> str | None:
    """The giver a ruling records (task-0320, decision-0038 G1): the handle that gave the captured answer it rules on, as
    the capture's own content names it (``[capture] from``, the signed ``[answered]`` handle), never its file name. None
    for a ruling without it: a file written before, which keeps the stem's fail-closed rule (task-0308)."""
    g = ru.get("giver")
    return g if isinstance(g, str) and g else None


# the reasons an ambiguous ruling's act carries once a later review bears on it (task-0322): load writes them, the gate
# reads them, both from here so a rewording cannot change a severity silently
SETTLED = "settled by "
SUPERSEDED = "superseded for the key by "
RULED = "the key was ruled by "
OPPOSED = "opposed the same day: "      # task-0328: two reviewers' opposing rulings of one statement on one day
INFO_REASONS = (SETTLED, SUPERSEDED)       # the key reads from a later ruling: info
MAJOR_REASONS = (RULED, OPPOSED)           # a later ruling that did not approve, or a same-day opposing one: still major
REASON_PREFIXES = INFO_REASONS + MAJOR_REASONS


def order_key(path: Path, doc: dict) -> tuple:
    """Where a review file sits in the order rulings are applied and "later" is read (task-0322): its date, then who
    ruled, then its number, the base file ``<on>-<by>`` as 0 and ``<on>-<by>-<n>`` (``capture.py review``'s second
    file the same day) as ``n``. A file name alone sorts ``-`` before ``.``, so the second file would come first."""
    r = doc.get("review", {}) if isinstance(doc, dict) else {}
    on, by, stem = str(r.get("on", "")), str(r.get("by", "")), path.stem
    m = re.fullmatch(re.escape(f"{on}-{by}") + r"(?:-([0-9]+))?", stem)
    return (on, by, int(m[1]) if m and m[1] else 0, path.name) if m else (on, stem, 0, path.name)


def opposes(a: str, b: str) -> bool:
    """Two outcomes of one statement the same day that cancel: an approval against a rejection or a referral (the one
    definition, task-0323)."""
    return (a == "approved") != (b == "approved") and "approved" in (a, b)


def equivalent(statement: str, same: tuple, row_id: str, row_same: tuple, row_giver, handles) -> bool:
    """Whether a ruling on ``row_id`` is on ``statement`` or an equivalent one (task-0323 R1, R2, R-A): the same key, value
    and digest and a giver the statement's stem reads as (``_readings``), or the statement itself. The one definition that
    ``settling``, ``opposed_settling`` and the load's ``_opposed`` share."""
    return row_id == statement or (row_same == same and row_giver is not None and row_giver in _readings(statement, handles))


def read_as(row: tuple, rows: list, handles) -> str:
    """The statement a ruling counts for among the day's ``rows`` (statement, (key, value, digest), giver, on): the least
    statement id of those it is equivalent to, itself included, so equivalent rulings pair under one id."""
    stmt, same, giver, on = row
    return min([stmt] + [s2 for s2, same2, _g2, on2 in rows if on2 == on and equivalent(s2, same2, stmt, same, giver, handles)])


def opposed_rulings(rows: list) -> dict:
    """The rulings that cancel each other (task-0328, task-0331): ``rows`` are (statement, on, by, outcome, review file) of
    every ruling the load would apply. Within a day the order across reviewers is only alphabetical, so a ruling approving
    a statement and another reviewer's, the same day, not approving it (rejected or referred) are neither "later": none of
    them is applied, whichever file comes first. Maps (statement, on, file) of each cancelled ruling to the whole cancelled
    set of that statement and day, the (file, outcome) of every ruling in it sorted, the same list for each (R3).
    The same reviewer's ``-n`` re-ruling opposes nothing of their own (task-0322); rulings that agree are not opposed."""
    hit = {(st, on, rel) for st, on, by, oc, rel in rows
           if any((st2, on2) == (st, on) and by2 != by and opposes(o2, oc)
                  for st2, on2, by2, o2, r2 in rows)}
    return {k: sorted({(rel, oc) for st, on, _by, oc, rel in rows if (st, on, rel) in hit and (st, on) == k[:2]}) for k in hit}


def opposed_reason(group: list) -> str:
    """The reason of the act finding of an opposed ruling: every file of the cancelled set, the same from each of them."""
    files = ", ".join(f"{rel} ({oc})" for rel, oc in sorted(group))
    return (f"{OPPOSED}{files}; two reviewers ruled on one statement on one day, so none applies and the statement keeps "
            "the status it had; the owners rule again in one review on a later day")


def is_opposed(reasons) -> bool:
    return bool(reasons) and str(reasons[0]).startswith(OPPOSED)


def opposed_settling(fa: dict, at: tuple, bound: list, handles: dict | None = None) -> str | None:
    """task-0331 R1, task-0333 R1': the second reason of an opposed act once a later day's applied ruling of the same
    statement decided it, the latest one, approved or rejected: ``settled by <file>`` (info). The owners did what the route
    asked; the key reads from that ruling (absent after a rejection). A referral decides nothing: the act stays major.
    The statement is read as ``settling`` reads it (``equivalent``, task-0323 R1). None while no later ruling decided it."""
    same = (fa.get("key"), fa.get("from_value"), fa.get("from_sha256"))
    later = [b for b in bound if b["at"][0] > at[0] and b["outcome"] in ("approved", "rejected")
             and equivalent(fa["statement"], same, b["id"], (b.get("key"), b.get("value"), b.get("sha256")), b.get("giver"), handles)]
    if not later:
        return None
    return f"{SETTLED}{later[-1]['rel']}"


def _day_after(b: dict, at: tuple) -> bool:
    return b["at"][0] > at[0]


def _later(b: dict, fa: dict, at: tuple) -> bool:
    """task-0323 L2: a ruling is later by its date; the same day by another reviewer (the recorded ``by``, never the file
    name, handle order being no order of writing); the same day by the same reviewer by its ``-n`` number, never the stem."""
    if b["at"][0] != at[0]:
        return b["at"][0] > at[0]
    return b.get("by") != fa.get("by") or b["at"][2] > at[2]


def settling(fa: dict, at: tuple, bound: list, handles: dict) -> str | None:
    """The reason an ambiguous ruling's act is settled or superseded by a later applied ruling (task-0322), else None.
    Settled (task-0323 L1): the latest later decided ruling of the same statement (its id, or the same key, value and
    digest by a giver the stem reads as); a referral never settles. A same-day ruling by another reviewer that opposes
    the act never reaches here: the load sets both aside (``opposed_rulings``, R1). Superseded: a later ruling of the same
    content on another statement, the answer it named unruled."""
    same = (fa["key"], fa["from_value"], fa["from_sha256"])
    later = [b for b in bound if _later(b, fa, at) and (b["key"], b["value"], b["sha256"]) == same]
    own = [b for b in later if equivalent(fa["statement"], same, b["id"], same, b["giver"], handles) and b["outcome"] in ("approved", "rejected")]
    clash = [b for b in own if b["at"][0] == at[0] and b.get("by") != fa.get("by") and opposes(b["outcome"], fa["outcome"])]
    if clash and not _day_after(own[-1], at):   # task-0323 R-A: the equivalent statement's opposing ruling, same day
        return opposed_reason([(fa["review"], fa["outcome"]), *[(b["rel"], b["outcome"]) for b in clash]])
    if own:
        return f"{SETTLED}{own[-1]['rel']}"
    for b in later:
        if not equivalent(fa["statement"], same, b["id"], same, b["giver"], handles):
            return (f"{SUPERSEDED}{b['rel']}; the answer it named stays unruled" if b["outcome"] == "approved"
                    else f"{RULED}{b['rel']} ({b['outcome']}); the answer it named stays unruled")
    return None


def _as_reported(how: dict) -> dict:
    """task-0321: the act schema's reasons are closed, so a giver the load cannot confirm is reported as ``changed``,
    the reason naming both givers."""
    return {"why": "changed", "to": [], "reasons": [how["message"]]} if how["why"] == "giver_wrong" else how


def _unbound_reason(where: str, aid: str, ru: dict, how: dict) -> str:
    """The reason a ruling that binds nowhere is refused the day it is written."""
    if how["why"] == "giver":   # task-0310: write time refuses what load time reports ambiguous
        return f"{where}: {_ambiguous_reason(aid)}"
    if how["why"] == "giver_wrong":   # task-0320: a giver the capture's content contradicts
        return f"{where}: {how['message']}"
    if how["why"] == "gone" and ru.get("value") is None:
        return f"{where}: the store holds no assertion {aid!r}"
    return (f"{where}: the store no longer holds what the ruling records ({ru.get('key')} = {ru.get('value')!r}); "
            f"it holds {', '.join(repr(t['value']) for t in how['to']) or 'nothing of it'}")


def _holding(rows: list[dict], aid: str, value, digest, handles: dict | None = None, giver: str | None = None) -> list[dict]:
    """The rows holding the ruling's value and digest that may stand in for ``aid``: any such statement, but for a
    captured answer only the same giver's (``_same_giver``, task-0302): the giver the ruling records when it records
    one (decision-0038 G1), the same id included, else the giver its id's stem names, never an ambiguous stem's."""
    def may(r):
        if giver is not None and aid.startswith("A:cap:"):
            return str(r["id"]).startswith("A:cap:") and r.get("agent") == giver
        return not _ambiguous_giver(aid, handles) and (r["id"] == aid or _same_giver(aid, r))
    return [r for r in rows if str(r["value"]) == str(value) and content_digest(r.get("fragments") or []) == str(digest) and may(r)]


def _stem_holders(rows: list[dict], aid: str, value, digest, handles: dict | None) -> bool:
    """Whether the id's stem reads as two givers and some statement holds the ruling's content (task-0308)."""
    return _ambiguous_giver(aid, handles) and any(
        str(r["value"]) == str(value) and content_digest(r.get("fragments") or []) == str(digest) for r in rows)


def _same_giver(aid: str, row: dict) -> bool:
    """Whether ``row`` may stand in for the ruled statement ``aid`` (task-0302, decision-0032 C2-1). A captured answer
    has no fragments, so its digest is the empty text's and any person's identical answer would carry it: a captured
    answer is repaired only by an answer the same person gave (its id's giver, read whole, the candidate's agent).
    A stem that reads as two givers (``…-ops-2``: ``ops-2``'s first file or ``ops``'s second, both issued) names no
    giver (``_ambiguous_giver``, task-0308): not even the same id binds, since either person's file may carry it, and
    ``bind`` reports it ``ambiguous`` when a statement holds the content.
    Every other statement repairs by its content, as before."""
    if aid.startswith("A:cap:") or str(row["id"]).startswith("A:cap:"):
        giver = _giver(aid)
        return giver is not None and str(row["id"]).startswith("A:cap:") and row.get("agent") == giver
    return True


def bind(st, ru: dict, handles: dict | None = None) -> tuple[dict | None, dict]:
    """(the statement a ruling lands on, or None; how it bound). ``how["why"]``: ``content`` (the statement it
    names, holding its value and digest), ``repaired`` (another statement holding them: a reordered table, a
    renumbered answer), ``unbound`` (a file from before 0.9.0, bound by id), else it lands nowhere: ``changed``
    (the statement it names, or its successor, holds another value or digest), ``gone`` (nothing of its key and
    stem is extracted), ``ambiguous`` (several statements hold its content, none the one it names). ``how["to"]``
    names what the store holds instead: its key's statements of the same stem, each with value and digest."""
    import key_rule   # task-0301: a ruling's key in NFC, as the store holds it
    aid = key_rule.normalise(str(ru.get("assertion", "")))   # its ids embed the key, in NFC too (task-0309 B2)
    key, value, digest = key_rule.normalise(ru.get("key")), ru.get("value"), ru.get("sha256")
    if key is None or value is None or digest is None:   # the read rule: a review file written before 0.9.0
        b = statement(st, aid)
        return b, {"why": "unbound" if b else "gone", "to": []}
    rows = st.key_evidence(str(key), list(CURRENT))
    giver = giver_of(ru)   # decision-0038 G1: recorded from the capture's content, so no stem is read
    same = _holding(rows, aid, value, digest, handles, giver)
    if not same and giver is None and _stem_holders(rows, aid, value, digest, handles):
        return None, {"why": "ambiguous", "to": []}   # holders exist; the stem names two givers, so none is chosen
    pick = next((r for r in same if r["id"] == aid), None) or (same[0] if len(same) == 1 else None)
    if pick is not None:
        return statement(st, pick["id"]), {"why": "content" if pick["id"] == aid else "repaired", "to": []}
    held = [{"id": r["id"], "value": str(r["value"]), "sha256": content_digest(r.get("fragments") or [])}
            for r in rows if _stem(r["id"]) == _stem(aid)]
    return None, {"why": "ambiguous" if same else "changed" if held else "gone", "to": held}


def _bind_ruling(st, ru: dict, handles: dict | None, strict: bool) -> tuple[dict | None, dict]:
    """``bind``, but the day a review is written a stem of two givers binds nowhere (task-0310) unless the giver was
    read from the capture's content (decision-0038 G1)."""
    if ru.get("_giver_wrong"):
        return None, {"why": "giver_wrong", "to": [], "message": ru["_giver_wrong"]}
    if strict and giver_of(ru) is None and _ambiguous_giver(str(ru.get("assertion", "")), handles):
        return None, {"why": "giver", "to": []}
    return bind(st, ru, handles)


def capture_index(capture_dir: Path) -> dict[str, dict]:
    """assertion id -> {from, on, value, note} for every captured answer (the ids load_captures gives them)."""
    out = {}
    for p in sorted(capture_dir.glob("*.toml")) if capture_dir.is_dir() else []:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        formats.version(c, p.as_posix(), formats.CAPTURE)
        cap = c.get("capture", {})
        for i, a in enumerate(c.get("answer", []), 1):
            out[f"A:cap:{p.stem}:{i}@capture"] = {"from": cap.get("from"), "on": _date(cap.get("on")),
                                                  "value": str(a.get("value", "")), "note": str(a.get("note", ""))}
    return out


def check(doc: dict, st, *, handles: dict | None, owners: dict[str, list[str]], units: dict[str, str],
          captures: dict[str, dict], now: dt.date, compatible, strict: bool = True,
          where: str = "the review") -> tuple[list[str], dict]:
    """(reasons for refusal, the normalised review). ``st`` is a loaded store; ``owners`` key -> the
    units owning its register nodes; ``compatible`` is rules.compatible.

    Each ruling is ``bind``-ed to the statement it ruled on, and each close to its gap's text (task-0199). With
    ``strict`` (``capture.py review``, the day the file is written) an act that does not bind is a reason to
    refuse; without it (a load) the act is set aside in ``norm["skipped"]``, with how it failed to bind, and the
    rest is checked and applied. The normalised rulings carry ``key``, ``value`` and ``sha256`` from the store and
    ``statement``, the id they land on; ``unbound`` marks one bound by id under the read rule."""
    formats.version(doc, where, formats.REVIEW)   # task-0174: a newer review refused (FormatTooNew), never misread
    errs: list[str] = []
    r = doc.get("review", {})
    by, on, record = str(r.get("by", "")), _date(r.get("on")), str(r.get("record", "")).strip()
    given = [dict(x) for x in doc.get("ruling", [])]
    given_closes = [dict(x) for x in doc.get("closes", [])]
    given_resolves = [dict(x) for x in doc.get("resolves", [])]
    rulings: list[dict] = []
    closes: list[dict] = []
    resolves: list[dict] = []
    skipped: list[dict] = []
    norm = {"by": by, "on": on, "record": record, "scenario": str(r.get("scenario", "")), "rulings": rulings, "closes": closes,
            "resolves": resolves, "skipped": skipped}
    if handles is None:
        return ["no issued-handle list in the register (decision 0009): a ruling needs an issued handle"], norm
    h = handles.get(by)
    if on is None:
        errs.append(f"review.on {r.get('on')!r} is not a date (YYYY-MM-DD)")
    elif now is not None and on > now:   # a load passes none (task-0198): a later date is simply not counted yet
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
    if not given and not given_closes and not given_resolves:
        errs.append("the review has no ruling, closes no gap and resolves no lint gap")
    roles, unit = (h["roles"], h["unit"]) if h else (set(), "")

    briefs: dict[str, dict] = {}
    for i, ru in enumerate(given, 1):
        aid, outcome = str(ru.get("assertion", "")), str(ru.get("outcome", ""))
        where = f"ruling {i} ({aid})"
        if outcome not in OUTCOMES:
            errs.append(f"{where}: outcome {outcome!r} is not one of {', '.join(OUTCOMES)}")
        ru = _read_giver(ru, aid, captures, strict, handles)   # decision-0038 G1: the capture's content's, never the file name's
        b, how = _bind_ruling(st, ru, handles, strict)
        if b is not None and strict and how["why"] == "repaired":
            b, how = None, {**how, "why": "changed"}   # the day it is written, a ruling names the statement it rules on
        if b is None:
            if strict:
                errs.append(_unbound_reason(where, aid, ru, how))
            else:
                how = _as_reported(how)
                skipped.append({"act": "ruling", "n": i, "statement": aid, "outcome": outcome, "key": str(ru.get("key") or ""),
                                "value": ru.get("value"), "sha256": ru.get("sha256"), **how})
            continue
        if b["id"] in briefs:
            errs.append(f"{where}: ruled twice in one review")
        briefs[b["id"]] = {**b, "outcome": outcome}
        rulings.append({"assertion": b["id"], "outcome": outcome, "note": str(ru.get("note", "")), "key": b["key"],
                        "value": str(b["value"]), "sha256": b["sha256"], "statement": b["id"], "n": i,
                        "unbound": how["why"] == "unbound" and not strict, **_giver_field(ru, b)})
        if b["basis"] in NEVER_PROMOTED and outcome not in ("rejected", "referred"):
            errs.append(f"{where}: {b['key']} is a statement of basis {b['basis']}; a ruling may reject or refer it, "
                        "never approve it (a model's statement is never promoted; doc-0030 I4)")
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

    for i, c in enumerate(given_closes, 1):
        gid = str(c.get("gap", ""))
        where = f"closes {i} ({gid})"
        g = st.declared_gap(gid)
        if g is None and not strict:   # task-0222: a close a load already applied (stage 2 re-reads every file)
            b = st.gap_brief(gid)
            if b is not None and b["kind"] == "closed" and (c.get("sha256") is None or str(c["sha256"]) == _sha(b["text"] or "")):
                closes.append({"gap": gid, "note": str(c.get("note", "")), "sha256": _sha(b["text"] or ""), "keys": b["keys"], "n": i,
                               "unbound": c.get("sha256") is None, "already": True})   # the same declaration, closed: a no-op
                continue
            if b is not None and b["kind"] == "closed":
                g = b   # closed, but on another declaration than the one this close read: changed
        held = _sha(g["text"] or "") if g is not None else None
        if g is None or (c.get("sha256") is not None and str(c["sha256"]) != held):
            why = "gone" if g is None else "changed"
            if strict:
                errs.append(f"{where}: the store holds no open declared gap {gid!r}" if why == "gone" else
                            f"{where}: the declaration's text is no longer the one the close records")
            else:
                skipped.append({"act": "close", "n": i, "statement": gid, "outcome": "closed", "key": "", "value": None,
                                "sha256": c.get("sha256"), "why": why,
                                "to": [] if g is None else [{"id": gid, "value": g["text"], "sha256": held}]})
            continue
        closes.append({"gap": gid, "note": str(c.get("note", "")), "sha256": held, "keys": sorted(g["keys"]), "n": i,
                       "unbound": c.get("sha256") is None and not strict, "already": False})
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

    lint = {g["id"]: g for g in st.lint_gaps()} if given_resolves else {}
    for i, c in enumerate(given_resolves, 1):   # task-0216: a lint gap resolved by its document's owner
        gid, res = str(c.get("gap", "")), str(c.get("resolution", ""))
        where = f"resolves {i} ({gid})"
        if res not in RESOLUTIONS:
            errs.append(f"{where}: resolution {res!r} is not one of {', '.join(RESOLUTIONS)} (a slip is a new version of the document, "
                        "which a re-lint shows; no review records it)")
        g = lint.get(gid)
        if g is None or (c.get("sha256") is not None and str(c["sha256"]) != g["sha256"]):
            why = "gone" if g is None else "changed"
            if strict:
                errs.append(f"{where}: the store holds no lint gap {gid!r}" if why == "gone" else
                            f"{where}: the finding's text is no longer the one the resolution records")
            else:
                skipped.append({"act": "resolve", "n": i, "statement": gid, "outcome": res, "key": "", "value": None,
                                "sha256": c.get("sha256"), "why": why,
                                "to": [] if g is None else [{"id": gid, "value": g["text"], "sha256": g["sha256"]}]})
            continue
        keys = sorted({a["key"] for a in st.artefact_assertions(g["artefact"]) if a.get("version") in (None, g["version"])})
        resolves.append({"gap": gid, "resolution": res, "note": str(c.get("note", "")), "sha256": g["sha256"], "keys": keys, "n": i})
        if h is None:
            continue
        if "closes" not in roles:
            errs.append(f"{where}: {by} lacks the role closes, which resolving a document's finding needs")
        allowed = sorted({u for k in keys for u in owners.get(k, [])})
        if unit not in allowed:
            errs.append(f"{where}: the document's owners resolve its findings ({', '.join(allowed) or 'none in the register map'}); "
                        f"{by}'s unit is {unit}")
    return errs, norm


def _readings(aid: str, handles: dict | None) -> list[str]:
    """The givers an id's stem may name once its capture file has vanished (task-0321): its tail whole, and for an
    ambiguous stem (``_ambiguous_giver``) the tail without its ``-<n>`` too. Only issued handles, when a list is known."""
    g = _giver(aid)
    if not g:
        return []
    m = re.fullmatch(r"(.+)-[0-9]+", g)
    out = [g] + ([m[1]] if m and handles and m[1] in handles else [])
    return [x for x in out if handles is None or x in handles]


def _loaded_giver_wrong(ru: dict, aid: str, captures: dict[str, dict], handles: dict | None) -> str | None:
    """Why a recorded giver cannot stand at a load (task-0321), else None: it must equal the present capture's, or, the
    capture gone, be one of the id's stem readings."""
    given = giver_of(ru)
    if given is None:
        return None
    cap = captures.get(aid)
    if cap is not None:
        held = cap.get("from")
        return f"the recorded giver {given} is not {held}, who gave {aid} (the capture's own content)" if held and given != held else None
    want = _readings(aid, handles)
    if given in want:
        return None
    return (f"the recorded giver {given} is not {' or '.join(want) or 'a handle its stem reads as'}, "
            f"which the stem of {aid} names (its capture is gone)")


def _read_giver(ru: dict, aid: str, captures: dict[str, dict], strict: bool, handles: dict | None = None) -> dict:
    """The ruling with ``giver`` checked against the capture holding ``aid`` (decision-0038 G1). The day a review is
    written (``strict``) the giver is read from the capture's content (``[capture] from``) and recorded; one the
    reviewer wrote that is not it is marked, so the ruling binds nowhere and is refused. At a load (task-0321) a
    recorded giver is never trusted (``_loaded_giver_wrong``): a wrong one is marked and the act reported. A ruling
    on another statement, or without a giver, is left as it is."""
    if not aid.startswith("A:cap:"):
        return ru
    if not strict:
        why = _loaded_giver_wrong(ru, aid, captures, handles)
        return {**ru, "_giver_wrong": why} if why else ru
    held, given = (captures.get(aid) or {}).get("from"), giver_of(ru)
    if held and given and given != held:
        return {**ru, "_giver_wrong": f"the ruling names giver {given}, and the capture holding {aid} was given by {held} (its own content)"}
    return {**ru, "giver": str(held)} if held else ru


def _giver_field(ru: dict, b: dict) -> dict:
    """``{giver}`` for a ruling on a captured answer that records one, else nothing: what the review file writes."""
    return {"giver": giver_of(ru)} if giver_of(ru) and b["id"].startswith("A:cap:") else {}


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
             f"format = {formats.CURRENT[formats.REVIEW]}", "", "[review]", f"by = {q(norm['by'])}", f"on = {norm['on'].isoformat()}", f"record = {q(norm['record'])}"]
    if norm["scenario"]:
        lines.append(f"scenario = {q(norm['scenario'])}")
    for ru in norm["rulings"]:   # bound to content (task-0199): what was ruled on, as the store held it
        lines += ["", "[[ruling]]", f"assertion = {q(str(ru.get('assertion', '')))}", f"key = {q(str(ru['key']))}",
                  f"value = {q(str(ru['value']))}", f"sha256 = {q(str(ru['sha256']))}",
                  *([f"giver = {q(str(ru['giver']))}"] if ru.get("giver") else []),   # decision-0038 G1: a captured answer's
                  f"outcome = {q(str(ru.get('outcome', '')))}", f"note = {q(str(ru.get('note', '')))}"]
    for c in norm["closes"]:
        lines += ["", "[[closes]]", f"gap = {q(str(c.get('gap', '')))}", f"sha256 = {q(str(c['sha256']))}",
                  f"note = {q(str(c.get('note', '')))}"]
    for c in norm.get("resolves", []):   # task-0216
        lines += ["", "[[resolves]]", f"gap = {q(str(c['gap']))}", f"resolution = {q(str(c['resolution']))}",
                  f"sha256 = {q(str(c['sha256']))}", f"note = {q(str(c.get('note', '')))}"]
    return "\n".join(lines) + "\n"

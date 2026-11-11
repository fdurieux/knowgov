"""When a review falls due (decision-0005, task-0068).

A verification of method ``review`` is current until its ``at`` plus the review months of the key it
concerns: the shortest ``[review.kinds]`` months of the register's ``metamodel/lifecycle.toml`` among
the kinds of the nodes the key's row in the subject's ``register_map.toml`` names, else the
register's ``default_months``. The register is read, never copied (``KG_REGISTER``; the vendored one
by default for a subject inside this checkout, a refusal for one outside it, ``register_root``, task-0334):
when it changes its cadence, the store follows on the next load.

The load writes that date as the verification's ``valid_until`` (``date_reviews``, both adapters
through the store port). The gate reads currency as of a date (``as_of``): a statement whose every
verification is a review whose ``valid_until`` is before that date, and that no later approval
renewed, has lapsed and reads ``validated`` (``lapse``). Execution verifications carry no date and do
not lapse by date. A source change ends any verification with its version tag, as before.

A deterministic run and the comparator read as of the subject's pinned record date (``subject.toml``
``[record] as_of``), so the record never moves by the clock; the gate command reads as of today.
"""
from __future__ import annotations

import datetime as dt
import os
import tomllib
from pathlib import Path

import dates   # task-0262: one strict YYYY-MM-DD parse
import instance_register   # task-0334: an instance's subject reads its own register or refuses
from review import LAPSE_MONTHS, add_months, pinned, today
from subject import ROOT, SUBJECT

FALLBACK_MONTHS = 12      # a register with no lifecycle.toml [review] default_months (the vendored one says 12)
CURRENT = ("verified", "approved")
RULING = "appr:review:"   # the id of an approval a person's review file made (harness/load.py load_reviews, review:<file>)


def register_root() -> Path:
    """The register this process reads: ``KG_REGISTER``; else, for a subject that ships in this checkout, the
    public register vendored under ``demo/register``; else ``instance_register.RegisterUnnamed``. The one
    resolution every register-reading tool goes through (``capture``, ``register_impact`` and their callers)."""
    v = os.environ.get("KG_REGISTER")
    if v:
        return Path(v).resolve()
    instance_register.check()
    return (ROOT / "demo" / "register").resolve()


def _toml(p: Path) -> dict:
    try:
        return tomllib.loads(p.read_text(encoding="utf-8"))
    except OSError:
        return {}


_CACHE: dict[tuple[str, str], tuple[dict[str, int], int]] = {}
_KINDS: dict[tuple[str, str], dict[str, str]] = {}   # key -> the kind whose months it takes (none: the default's)


def cadence(subject=None, register: Path | None = None) -> tuple[dict[str, int], int]:
    """(key -> months, default months) for one subject (the current one by default) and one register
    (``KG_REGISTER``, else the vendored one); read once per pair."""
    subject = subject or SUBJECT
    root = Path(register or register_root())
    ck = (str(root), str(subject.root))
    if ck not in _CACHE:
        _CACHE[ck], _KINDS[ck] = _read(subject, root)
    return _CACHE[ck]


def _read(subject, root: Path) -> tuple[tuple[dict[str, int], int], dict[str, str]]:
    review = _toml(root / "metamodel" / "lifecycle.toml").get("review", {})
    default = int(review.get("default_months", FALLBACK_MONTHS))
    by_kind = {k: int(v["months"]) for k, v in review.get("kinds", {}).items() if isinstance(v, dict) and "months" in v}
    kinds: dict[str, str] = {}
    for tax in _toml(root / "metamodel" / "types.toml").get("taxonomy", {}):
        for p in sorted((root / tax).glob("*.toml")):
            n = _toml(p)
            if "id" in n and "kind" in n:
                kinds[n["id"]] = n["kind"]
    out, which = {}, {}
    for row in subject.register_map().get("row", []):
        # decision-0005 point 2: the shortest months among the kinds the register names months for, else the
        # default; a node whose kind it names none for never mixes the default in (task-0209, doc-0030 G11)
        named = sorted((by_kind[k], k) for n in row.get("nodes", []) if (k := kinds.get(n, "")) in by_kind)
        out[row["key"]] = named[0][0] if named else default
        if named:
            which[row["key"]] = named[0][1]
    return (out, default), which


def months_for(key: str, subject=None) -> int:
    """The review months of the key: the shortest among the kinds of its register nodes that the register
    names months for, else the default (decision-0005 point 2)."""
    by_key, default = cadence(subject)
    return by_key.get(key, default)


def kind_for(key: str, subject=None) -> str | None:
    """The register kind whose review months the key takes, or None when it takes the default."""
    subject = subject or SUBJECT
    cadence(subject)
    return _KINDS[(str(register_root()), str(subject.root))].get(key)


def _date(v) -> dt.date | None:
    """The calendar date of a verification's ``at`` or ``valid_until`` (an ISO date or timestamp); None
    for anything else, such as the version tag a source change writes. ``dates.day`` reads it: a date,
    YYYY-MM-DD, alone or followed by an ISO time (task-0262)."""
    return dates.day(v)


def due(at, key: str, subject=None) -> str | None:
    """The last day a review of ``key`` made on ``at`` is current, as YYYY-MM-DD."""
    d = _date(at)
    return add_months(d, months_for(key, subject)).isoformat() if d else None


def date_reviews(st) -> int:
    """Write ``valid_until`` on every review verification that carries none: its due date. Returns how many."""
    dates = {}
    for v in st.review_verifications():
        d = due(v["at"], v["key"])
        if d:
            dates[v["id"]] = d
    if dates:
        st.set_valid_until(dates)
    return len(dates)


def record_date(subject=None) -> dt.date | None:
    """The subject's pinned record date (``[record] as_of``), if it names one."""
    subject = subject or SUBJECT
    return _date(subject.record_as_of) if subject.record_as_of else None


def pin_record(env=None, subject=None) -> dict:
    """``env`` (os.environ by default) for a check that holds its outcome to the record: KG_TODAY at the
    subject's pinned record date and KG_CLOCK=pinned (task-0075), so nothing it runs reads the wall clock."""
    on = record_date(subject)
    if on is None:
        raise ValueError(f"{(subject or SUBJECT).id} pins no record date ([record] as_of); a check cannot pin its clock")
    return pinned(os.environ if env is None else env, on.isoformat())


def as_of(value=None, subject=None) -> dt.date:
    """A date the gate reads currency as of: ``record`` (the subject's pinned record date, else today),
    ``today`` or None (KG_TODAY, else the wall clock), or a YYYY-MM-DD date."""
    if value is None or value == "today":
        return today()
    if value == "record":
        return record_date(subject) or today()
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    try:
        return dates.parse(value)   # task-0262: YYYY-MM-DD in ASCII digits, never a week, basic or suffixed form
    except dates.NotADate:
        raise dates.NotADate(f"{value!r} is not a date (YYYY-MM-DD), 'today' or 'record'") from None


def lapse(row: dict, key: str, on: dt.date, subject=None) -> dict | None:
    """A statement's lapse as of ``on``, or None while it is current as of ``on`` (task-0198, doc-0030 H3, G4,
    G10; decision-0005). Only ``on`` decides: never the day the store was loaded, never today.

    - Counted: a review verification and an approval from a person's review file (``RULING``), each only when
      dated on or before ``on`` (G10: what happened after the date is not counted).
    - Current until: a review verification's ``valid_until``; a document statement's ruling approval its date
      plus the key's months (it renews the review, decision-0005 point 4; with no verification at all, G4); a
      person's approval its ``until``, six months after the answer (decision-0002), stored by the load (H3).
    - Not current: a document statement reads ``validated``; a person's statement reads ``proposed``. A
      statement approved only by a ruling dated after ``on``, its verification current, reads ``verified``.

    An execution verification carries no date and is current whatever ``on``; a source change's version tag
    is not ours to judge. The result names ``to``, the status the statement reads as of ``on``."""
    status = row.get("status")
    if status not in CURRENT:
        return None
    person = row.get("basis") == "elicited"
    vers = [] if person else (row.get("verifications") or [])
    if any(v.get("valid_until") is None for v in vers) or not all(_date(v.get("valid_until")) for v in vers):
        return None   # an undated verification (execution) is current; a version tag is a source change's
    rulings = [ap for ap in row.get("approvals") or [] if str(ap.get("id") or "").startswith(RULING)]
    if not vers and not rulings:
        return None   # nothing a date governs
    counted = lambda e: _date(e.get("at")) is None or _date(e.get("at")) <= on   # noqa: E731
    ends = [_date(v["valid_until"]) for v in vers if counted(v)]
    for ap in rulings:
        if not counted(ap):
            continue
        if person:
            ends.append(_date(ap.get("until")) or dt.date.max)   # no capture date to count from: it does not lapse
        elif _date(ap.get("at")):
            ends.append(add_months(_date(ap["at"]), months_for(key, subject)))
    until = max(ends, default=None)
    months = LAPSE_MONTHS if person else months_for(key, subject)
    base = {"id": row["id"], "key": key, "from": status, "months": months, "kind": "elicited" if person else kind_for(key, subject),
            "verifications": sorted(v["id"] for v in vers if v.get("id"))}
    if until is not None and on <= until:
        others = [ap for ap in row.get("approvals") or [] if ap not in rulings]
        if status == "approved" and rulings and not any(counted(ap) for ap in rulings) and not others:
            first = min(_date(ap.get("at")) for ap in rulings)
            return {**base, "to": "verified", "valid_until": None, "after": first.isoformat()}   # approved only after the date
        return None
    if until is None:   # every dated event is after the date: none of it counts yet
        dated = [d for d in [*(_date(v.get("at")) for v in vers), *(_date(ap.get("at")) for ap in rulings)] if d]
        # unreachable since task-0199: a ruling's approval carries its review's date (review.check refuses a file without
        # one) and an attestation its own ``at`` (load.attestation applies none without), so something here is dated
        assert dated, f"{row['id']}: an approval or review with no date (task-0199: every person's act carries its at)"
        first = min(dated)
        return {**base, "to": "proposed" if person else "validated", "valid_until": None, "after": first.isoformat()}
    return {**base, "to": "proposed" if person else "validated", "valid_until": until.isoformat(),
            "lapsed_on": (until + dt.timedelta(days=1)).isoformat()}   # the first day it reads as no longer current


def describe(x: dict, on) -> str:
    """One lapse in words, as of ``on``: what it was, why it is not current, and what it reads."""
    x = {"to": "validated", **x}   # an entry from before task-0198 named no ``to``: a review lapse read validated
    if x.get("after"):
        what = "approval" if x["to"] == "verified" else "review"
        return (f"was {x['from']}; its {what} is dated {x['after']}, after the as-of date {on}, so it is not counted: "
                f"it reads {x['to']} as of then (task-0198)")
    if x.get("kind") == "elicited":
        return (f"was {x['from']}; its approval was current until {x['valid_until']}, {x['months']} months after the answer "
                f"(decision-0002), and has lapsed as of {on}: it reads {x['to']} until it is asked again")
    return (f"was {x['from']}; its review was current until {x['valid_until']} and has lapsed as of {on}: "
            f"it reads {x['to']} until a new review (decision-0005)")

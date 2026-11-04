"""When a review falls due (decision-0005, task-0068).

A verification of method ``review`` is current until its ``at`` plus the review months of the key it
concerns: the shortest ``[review.kinds]`` months of the register's ``metamodel/lifecycle.toml`` among
the kinds of the nodes the key's row in the subject's ``register_map.toml`` names, else the
register's ``default_months``. The register is read, never copied (``KG_REGISTER``, the vendored one
by default): when it changes its cadence, the store follows on the next load.

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

from review import add_months, pinned, today
from subject import ROOT, SUBJECT

FALLBACK_MONTHS = 12      # a register with no lifecycle.toml [review] default_months (the vendored one says 12)
CURRENT = ("verified", "approved")
RULING = "appr:review:"   # the id of an approval a person's review file made (harness/load.py load_reviews, review:<file>)


def register_root() -> Path:
    return Path(os.environ.get("KG_REGISTER") or (ROOT / "demo" / "register")).resolve()


def _toml(p: Path) -> dict:
    try:
        return tomllib.loads(p.read_text(encoding="utf-8"))
    except OSError:
        return {}


_CACHE: dict[tuple[str, str], tuple[dict[str, int], int]] = {}


def cadence(subject=None, register: Path | None = None) -> tuple[dict[str, int], int]:
    """(key -> months, default months) for one subject (the current one by default) and one register
    (``KG_REGISTER``, else the vendored one); read once per pair."""
    subject = subject or SUBJECT
    root = Path(register or register_root())
    ck = (str(root), str(subject.root))
    if ck not in _CACHE:
        _CACHE[ck] = _read(subject, root)
    return _CACHE[ck]


def _read(subject, root: Path) -> tuple[dict[str, int], int]:
    review = _toml(root / "metamodel" / "lifecycle.toml").get("review", {})
    default = int(review.get("default_months", FALLBACK_MONTHS))
    by_kind = {k: int(v["months"]) for k, v in review.get("kinds", {}).items() if isinstance(v, dict) and "months" in v}
    kinds: dict[str, str] = {}
    for tax in _toml(root / "metamodel" / "types.toml").get("taxonomy", {}):
        for p in sorted((root / tax).glob("*.toml")):
            n = _toml(p)
            if "id" in n and "kind" in n:
                kinds[n["id"]] = n["kind"]
    out = {}
    for row in subject.register_map().get("row", []):
        months = [by_kind.get(kinds.get(n, ""), default) for n in row.get("nodes", [])]
        out[row["key"]] = min(months) if months else default
    return out, default


def months_for(key: str, subject=None) -> int:
    """The review months of the key: the shortest among its register nodes' kinds, else the default."""
    by_key, default = cadence(subject)
    return by_key.get(key, default)


def _date(v) -> dt.date | None:
    """The calendar date of a verification's ``at`` or ``valid_until`` (an ISO date or timestamp); None
    for anything else, such as the version tag a source change writes."""
    if isinstance(v, dt.date):
        return v if not isinstance(v, dt.datetime) else v.date()
    try:
        return dt.date.fromisoformat(str(v)[:10]) if v and len(str(v)) >= 10 else None
    except ValueError:
        return None


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
    d = _date(value)
    if d is None or len(str(value)) != 10:
        raise ValueError(f"{value!r} is not a date (YYYY-MM-DD), 'today' or 'record'")
    return d


def lapse(row: dict, key: str, on: dt.date, subject=None) -> dict | None:
    """A statement's lapse as of ``on``, or None while it is current. Lapsed: it is verified or approved,
    every verification it holds is dated (a review), the latest of those dates is before ``on``, and no
    approval in a person's review file after the latest review renewed it (such an approval is a new
    review: it is current for the key's months from its own date; decision-0005 point 4)."""
    if row.get("status") not in CURRENT or row.get("basis") == "elicited":
        return None
    vers = row.get("verifications") or []
    if not vers:
        return None
    dates = [_date(v.get("valid_until")) for v in vers]
    if any(v.get("valid_until") is None for v in vers) or not all(dates):
        return None   # an undated verification (execution) is current; a version tag is a source change's
    until = max(dates)
    last_review = max((_date(v.get("at")) for v in vers if _date(v.get("at"))), default=None)
    for ap in row.get("approvals") or []:
        if not str(ap.get("id") or "").startswith(RULING):
            continue   # the load's own approval rests on the verification; it renews nothing
        a = _date(ap.get("at"))
        if a and last_review and a > last_review:
            until = max(until, add_months(a, months_for(key, subject)))
    if on <= until:
        return None
    return {"id": row["id"], "key": key, "from": row["status"], "valid_until": until.isoformat(),
            "verifications": sorted(v["id"] for v in vers if v.get("id"))}

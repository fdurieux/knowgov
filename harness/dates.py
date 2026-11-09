"""One strict date parse for every date knowgov reads (task-0262, decision-0032, G9-17).

The documented form is ``YYYY-MM-DD``, and nothing else is a date:

- ``parse`` takes a value given as a date, from a flag (``--as-of``, ``--on``), a variable (``KG_AS_OF``,
  ``KG_TODAY``), an MCP argument or a page request. It accepts exactly ten ASCII characters,
  ``[0-9]{4}-[0-9]{2}-[0-9]{2}``, that ``date.fromisoformat`` reads. On Python 3.11 and later
  ``fromisoformat`` also reads the ISO week form (``2026-W45-1`` is 2026-11-02) and the basic form
  (``20261105``), and ``\\d`` matches fullwidth digits, so neither alone closes the domain. Anything
  else is ``NotADate``, a ``ValueError`` naming the value;
- ``day`` takes a stored date or instant: a verification's ``at`` or ``valid_until``, an attestation's
  ``at``. It accepts a ``date``, a ``datetime``, or a string that is a date as ``parse`` reads it, alone
  or followed by ``T`` or a space and a time that ``datetime.fromisoformat`` reads. It returns the
  calendar date, or None when the value names none, such as a source change's version tag.

Standard library only; nothing here reads a file or the clock.
"""
from __future__ import annotations

import datetime as dt
import re

FORM = "YYYY-MM-DD"
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")   # ASCII digits only: [0-9], never \d


class NotADate(ValueError):
    """A value given as a date that is not ``YYYY-MM-DD``; the message names the value."""


def parse(value, what: str | None = None) -> dt.date:
    """``value`` as the date it names, or ``NotADate`` naming ``what`` (if given) and the value."""
    if isinstance(value, str) and _DATE.fullmatch(value):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            pass
    raise NotADate(f"{what + ' ' if what else ''}{value!r} is not a date ({FORM})")


def is_date(value) -> bool:
    """True when ``parse`` reads ``value``."""
    try:
        parse(value)
        return True
    except NotADate:
        return False


def day(value) -> dt.date | None:
    """The calendar date of a stored date or instant, or None when ``value`` names none."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if not isinstance(value, str) or len(value) < 10 or not is_date(value[:10]):
        return None
    if len(value) == 10:
        return dt.date.fromisoformat(value)
    if value[10] not in "T ":
        return None
    try:
        return dt.datetime.fromisoformat(value).date()
    except ValueError:
        return None

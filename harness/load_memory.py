"""The heap a Neo4j load needs, forecast before the load starts (task-0176).

A Neo4j writer's whole unit is one transaction (decision-0014), so the server's transaction memory bounds
a load: a unit over it fails inside its transaction and keeps the previous generation. This forecasts the
unit's peak transaction memory before its first write and refuses the load up front, naming the setting
and both figures, when the forecast exceeds what the server allows.

- **Statements**: the assertions plus the fragments of a graph. A load's are counted from the documents'
  extraction before anything is written (``statements``).
- **What a unit holds**: every statement it has *written* and every statement its wipes *deleted*, over
  the whole unit. A wipe inside the transaction keeps what it deleted in the transaction's state: the
  first wipe of a unit deletes the published generation, a later one what the unit wrote before it.
  ``harness/run.py --deterministic`` wipes and loads every scenario in one unit, and measured, its peak
  sits under the sum (CargoQuote 17 MiB, J-F 98 MiB) but well over one scenario, so the sum is the
  forecast: it over-reads such a unit by up to about two times. The adapter's ``wipe`` calls ``wiped``;
  ``note`` adds a load.
- **Forecast**: ``BASE + PER_WRITTEN * written + PER_DELETED * deleted``, the least-squares plane of
  ``tools/measure_load_memory.py``'s measurements, its intercept raised so that every measured peak lies
  on or under it (the data and the fit: ``docs/load-memory.json``), times ``1 + KG_LOAD_MEMORY_MARGIN``
  (default 0.25, from 0 to 4).
- **Limit**: the smallest of the server's ``db.memory.transaction.max``,
  ``db.memory.transaction.total.max`` and ``dbms.memory.transaction.total.max`` that is set (0 is
  unlimited), read with ``SHOW SETTINGS`` by the adapter's ``transaction_memory``; a store with no such
  limit (rdflib) is never refused.
- **Escape**: ``KG_LOAD_MEMORY_CHECK=off`` (or 0, no, false) loads anyway; a unit that does not fit then
  fails inside its transaction, as before, and keeps the previous generation.
"""
from __future__ import annotations

import os

# tools/measure_load_memory.py on Neo4j 5.26 Community, both public subjects and the synthetic scale-up
# (docs/load-memory.json): the least-squares plane, its intercept raised to the largest residual
BASE = 25_563_415             # bytes (24.4 MiB): the plane's intercept, raised by its largest residual
PER_WRITTEN = 9_583           # bytes per statement the unit writes
PER_DELETED = 9_610           # bytes per statement the unit's wipes delete
OFF = ("off", "0", "no", "false")


class LoadTooLarge(RuntimeError):
    """A load whose forecast peak transaction memory exceeds what the server allows: refused before the
    unit wrote anything, so the previous generation stands."""


def enabled() -> bool:
    return (os.environ.get("KG_LOAD_MEMORY_CHECK") or "on").strip().lower() not in OFF


def margin() -> float:
    from store import setting
    return setting("KG_LOAD_MEMORY_MARGIN")


def statements(bags) -> int:
    """The statements a load writes: its extraction's assertions and fragments."""
    return sum(len(b.assertions) + len(b.fragments) for b in bags)


def forecast(written: int, deleted: int) -> int:
    """The unit's forecast peak transaction memory, the margin included, in bytes."""
    return int((BASE + PER_WRITTEN * written + PER_DELETED * deleted) * (1 + margin()))


def counts(st) -> dict:
    """What this writer's unit has noted: every statement written, every statement its wipes deleted."""
    return {"written": int(getattr(st, "_kg_written", 0)), "deleted": int(getattr(st, "_kg_deleted", 0))}


def _present(st) -> int:
    if not hasattr(st, "_kg_present"):   # the unit's first look: the published generation
        st._kg_present = int((st.transaction_memory() or {}).get("published") or 0)
    return st._kg_present


def wiped(st) -> None:
    """A wipe in the unit: it deletes what the unit's graph held, which the transaction keeps."""
    st._kg_deleted, st._kg_present = counts(st)["deleted"] + _present(st), 0


def note(st, n: int) -> None:
    """Add a load's ``n`` statements to the writer's unit and refuse, before the load writes anything,
    when the unit's forecast exceeds the server's transaction memory (``LoadTooLarge``)."""
    _present(st)
    st._kg_written = counts(st)["written"] + n
    st._kg_present += n
    if not enabled():
        return
    limit = (st.transaction_memory() or {}).get("limit")
    if not limit:
        return
    c = counts(st)
    _refuse_over(c["written"], c["deleted"], limit, "this load")


def preflight(st, loads: list[int]) -> None:
    """Refuse a unit of several wipe-and-load steps (``harness/run.py``: one per scenario) before the
    first, when the whole unit's forecast does not fit: ``loads`` is each step's statement count. Nothing
    is noted; each load is still checked as it comes (``note``)."""
    if not enabled() or not loads:
        return
    info = st.transaction_memory() or {}
    limit = info.get("limit")
    if not limit:
        return
    present, written, deleted = int(info.get("published") or 0), 0, 0
    for n in loads:
        deleted, present, written = deleted + present, n, written + n
    _refuse_over(written, deleted, limit, f"the run's {len(loads)} loads in one unit")


def _refuse_over(written: int, deleted: int, limit: dict, what: str) -> None:
    need = forecast(written, deleted)
    if need > limit["bytes"]:
        raise LoadTooLarge(
            f"refused before loading: {what} forecast a peak transaction memory of {mib(need)} MiB "
            f"({written} statements written and {deleted} deleted by the unit's wipes, with a "
            f"{margin():.0%} margin), and the server allows {mib(limit['bytes'])} MiB "
            f"({limit['setting']} = {limit['value']}). Raise {limit['setting']} (or the heap it follows), or set "
            "KG_LOAD_MEMORY_CHECK=off to load anyway: a unit that does not fit then fails inside its transaction "
            "and keeps the previous generation (task-0176)")


def mib(b: float) -> str:
    return f"{b / 2**20:.1f}"


def parse_size(text: str | None) -> int:
    """A Neo4j size setting as bytes: '0B', '16.00MiB', '2.34GiB', '512m', '1g'; 0 when unset."""
    if not text:
        return 0
    low = str(text).strip().replace(" ", "").lower()
    units = {"gib": 2**30, "mib": 2**20, "kib": 2**10, "g": 2**30, "m": 2**20, "k": 2**10, "b": 1}
    for u in sorted(units, key=len, reverse=True):
        if low.endswith(u):
            return int(float(low[: -len(u)] or 0) * units[u])
    return int(float(low))


def fit(rows: list[tuple[int, int, int]]) -> dict:
    """The least-squares plane through ``rows`` (written, deleted, peak bytes), and its intercept raised
    so that every row lies on or under it: what ``BASE``, ``PER_WRITTEN`` and ``PER_DELETED`` carry."""
    if len(rows) < 3:
        raise ValueError("a plane needs three rows")
    # the normal equations of y = a + b w + c d, solved by Cramer's rule (standard library only)
    s = [[0.0] * 3 for _ in range(3)]
    t = [0.0] * 3
    for w, d, y in rows:
        v = (1.0, float(w), float(d))
        for i in range(3):
            t[i] += v[i] * y
            for j in range(3):
                s[i][j] += v[i] * v[j]

    def det(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    dd = det(s)
    if not dd:
        raise ValueError("the rows do not vary both written and deleted")
    coef = []
    for k in range(3):
        m = [row[:] for row in s]
        for i in range(3):
            m[i][k] = t[i]
        coef.append(det(m) / dd)
    a, b, c = coef
    res = [y - (a + b * w + c * d) for w, d, y in rows]
    my = sum(y for _, _, y in rows) / len(rows)
    ss_tot = sum((y - my) ** 2 for _, _, y in rows)
    return {"per_written": round(b, 1), "per_deleted": round(c, 1), "base": round(a), "base_envelope": round(a + max(res)),
            "largest_residual": round(max(res)), "r2": round(1 - sum(r * r for r in res) / ss_tot, 4) if ss_tot else 1.0,
            "rows": len(rows)}


TOTAL_SHARE = 0.7   # dbms.memory.transaction.total.max's default share of the heap


def sizing(subject) -> dict:
    """What a subject's loads need, from its documents alone (no store): each scenario's statements, a
    gate load's forecast (one scenario replacing a published generation of the same size), the whole
    run's (``harness/run.py``: every scenario in one unit), and the heap whose default 70% holds the larger."""
    from extract import extract_all
    from kitio import kit_for
    per = {sc: statements(extract_all(kit_for(sc), subject.reference_code())) for sc in subject.order}
    biggest = max(per.values(), default=0)
    gate = forecast(biggest, biggest)
    w = sum(per.values())
    run = forecast(w, w)   # each scenario's wipe deletes the one before; the first, a generation of the same size
    need = max(gate, run)
    return {"subject": subject.id, "statements": per, "gate_load_mib": float(mib(gate)), "whole_run_mib": float(mib(run)),
            "margin": margin(), "transaction_memory_needed_mib": float(mib(need)),
            "heap_needed_mib": float(mib(need / TOTAL_SHARE)),
            "formula": f"({BASE} + {PER_WRITTEN} x written + {PER_DELETED} x deleted) x (1 + KG_LOAD_MEMORY_MARGIN) bytes"}


def main(argv: list[str] | None = None) -> int:
    """``KG_SUBJECT=<subject root> python harness/load_memory.py``: what the subject's loads need (JSON)."""
    import json
    import sys
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] in ("-h", "--help"):
        print(main.__doc__)
        return 0
    from subject import SUBJECT
    print(json.dumps(sizing(SUBJECT), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

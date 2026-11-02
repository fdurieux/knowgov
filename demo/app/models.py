"""The models table behind the page's Arms call drop-down (task-0029).

The operator writes rows in a TOML table (``KG_MODELS``, default ``demo/models.toml``): provider,
base URL, model, the efforts the row accepts, the name of the environment variable holding the
key, and the arm kinds the row serves. No key and no price is ever read from or written to the
table. The server adds two rows of its own: the record's row first, from the subject's
``record_model`` and ``record_effort``, and "this instance's settings" when the three
``KG_MODEL_*`` variables name something other than the defaults.

An Arms run takes a row id and an effort; ``resolve()`` turns them into the four variables the
harness already reads, so the harness does not change and a browser can send no URL.
"""
from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TABLE = HERE.parent / "models.toml"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_KEY_VAR = "OPENAI_API_KEY"
RECORD_ID, CUSTOM_ID = "record", "custom"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
VAR_RE = re.compile(r"^[A-Z_][A-Z0-9_]{0,63}$")
FIELDS = ("id", "label", "provider", "base_url", "model", "efforts", "key_var", "arms")
OPTIONAL = {"thinking_uncounted": False}   # the endpoint leaves a thinking model's tokens out of streamed usage (task-0034)
KINDS = ("reply", "agent")


def host_of(base_url: str) -> str:
    return base_url.split("://", 1)[-1].split("/", 1)[0]


def table_path() -> Path:
    return Path(os.environ.get("KG_MODELS") or DEFAULT_TABLE)


def load_table(path: Path | None = None) -> list[dict]:
    """The operator's rows, checked: every field present and of its type, ids unique, no field the
    table does not define (so a key or a price cannot ride in under another name)."""
    path = path or table_path()
    rows = tomllib.loads(path.read_text(encoding="utf-8")).get("row", [])
    seen, out = set(), []
    for r in rows:
        extra = sorted(set(r) - set(FIELDS) - set(OPTIONAL))
        if extra:
            raise ValueError(f"{path.name}: row {r.get('id')!r} has fields the table does not define: {extra}")
        missing = [f for f in FIELDS if f not in r]
        if missing:
            raise ValueError(f"{path.name}: row {r.get('id')!r} lacks {missing}")
        if not ID_RE.match(r["id"]) or r["id"] in (RECORD_ID, CUSTOM_ID) or r["id"] in seen:
            raise ValueError(f"{path.name}: row id {r['id']!r} is malformed, reserved or repeated")
        if not VAR_RE.match(r["key_var"]):
            raise ValueError(f"{path.name}: row {r['id']!r}: key_var must name a variable, not hold a key")
        if not r["base_url"].startswith(("https://", "http://")):
            raise ValueError(f"{path.name}: row {r['id']!r}: base_url must be an http(s) URL")
        if not set(r["arms"]) <= set(KINDS) or not r["arms"]:
            raise ValueError(f"{path.name}: row {r['id']!r}: arms must list reply, agent or both")
        if not isinstance(r.get("thinking_uncounted", False), bool):
            raise ValueError(f"{path.name}: row {r['id']!r}: thinking_uncounted is true or false")
        seen.add(r["id"])
        out.append({**{f: r[f] for f in FIELDS}, **{k: r.get(k, v) for k, v in OPTIONAL.items()}})
    return out


def _record_row(record_model: str, record_effort: str) -> dict:
    return {"id": RECORD_ID, "label": f"the record's model, {record_model or 'none'}", "provider": "the record",
            "base_url": DEFAULT_BASE_URL, "model": record_model, "efforts": [record_effort],
            "key_var": DEFAULT_KEY_VAR, "arms": list(KINDS)}


def _custom_row() -> dict | None:
    """The three instance variables as a row, when any names something other than the default."""
    base = os.environ.get("KG_MODEL_BASE_URL") or ""
    var = os.environ.get("KG_MODEL_API_KEY_VAR") or ""
    model = os.environ.get("KG_ARMS_MODEL") or ""
    if not (base and base != DEFAULT_BASE_URL) and not (var and var != DEFAULT_KEY_VAR) and not model:
        return None
    effort = os.environ.get("KG_ARMS_EFFORT") or ""
    return {"id": CUSTOM_ID, "label": f"this instance's settings, {model or 'its model'}", "provider": host_of(base or DEFAULT_BASE_URL),
            "base_url": base or DEFAULT_BASE_URL, "model": model, "efforts": sorted({"", effort}),
            "key_var": var or DEFAULT_KEY_VAR, "arms": list(KINDS)}


def rows(record_model: str, record_effort: str, arm_kind: str) -> list[dict]:
    """Every row the page lists, in order: the record's, the instance's when set, the table's. Each
    carries key_set (whether its variable holds a value, never the value), whether it serves this
    subject's arm kind, and whether a run on it would be a deviation from the record. The record's
    row is unavailable on a subject whose record ran no arm."""
    listed = [_record_row(record_model, record_effort)]
    custom = _custom_row()
    if custom:
        listed.append(custom)
    listed += load_table()
    out = []
    for r in listed:
        no_record = r["id"] == RECORD_ID and not record_model
        serves = arm_kind in r["arms"]
        key_set = bool(os.environ.get(r["key_var"]))
        out.append({**r, "host": host_of(r["base_url"]), "key_set": key_set, "serves": serves,
                    "available": key_set and serves and bool(r["model"]) and not no_record,
                    "why": ("the record ran no arm" if no_record else
                            f"set {r['key_var']}" if not key_set else
                            f"serves the {' and '.join(r['arms'])} arms, not this subject's {arm_kind} arm" if not serves else
                            "set KG_ARMS_MODEL" if not r["model"] else "")})
    return out


def is_deviation(row: dict, effort: str, record_model: str, record_effort: str) -> bool:
    """A run is a deviation when the record ran an arm and the run's host, model or effort differs."""
    return bool(record_model) and (row["host"] != host_of(DEFAULT_BASE_URL) or row["model"] != record_model or effort != record_effort)


def resolve(row_id: str | None, effort: str | None, record_model: str, record_effort: str, arm_kind: str) -> tuple[dict, dict, bool]:
    """The row and the effort a run asks for, checked, as (row, the harness's environment, deviation).
    An unknown row, a row that is unavailable (its key unset, another arm kind, the record's row
    when the record ran none) and an effort the row does not list are refused with the reason."""
    listed = rows(record_model, record_effort, arm_kind)
    if not row_id:
        row_id = next((r["id"] for r in listed if r["available"]), "")
    row = next((r for r in listed if r["id"] == row_id), None)
    if row is None:
        raise ValueError(f"no model row {row_id!r}")
    if not row["available"]:
        raise ValueError(f"model row {row_id!r} is not available: {row['why']}")
    effort = (effort if effort is not None else row["efforts"][0]).strip()
    if effort not in row["efforts"]:
        raise ValueError(f"model row {row_id!r} accepts the efforts {row['efforts']}, not {effort!r}")
    env = {"KG_MODEL_BASE_URL": row["base_url"], "KG_MODEL_API_KEY_VAR": row["key_var"],
           "KG_ARMS_MODEL": row["model"], "KG_ARMS_EFFORT": effort,
           "KG_THINKING_UNCOUNTED": "1" if row.get("thinking_uncounted") else ""}
    return row, env, is_deviation(row, effort, record_model, record_effort)


def public(row: dict) -> dict:
    """What the page receives for a row: everything but nothing secret, since a row holds nothing secret."""
    return {k: row[k] for k in ("id", "label", "provider", "host", "model", "efforts", "key_var", "arms",
                                "key_set", "serves", "available", "why")}

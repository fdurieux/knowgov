"""A small JSON Schema (draft 2020-12) validator for the schemas this repository ships (task-0007).

The tests job is standard library only, so ``jsonschema`` is out; this covers exactly the keyword
subset ``harness/schemas/`` uses and refuses a schema that uses anything else, since ignoring an
unknown keyword would turn the check into a rubber stamp. Modelled on pumllint's
``pumllint/schema.py``, which makes the same promise for its report schemas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMAS = Path(__file__).resolve().parent / "schemas"
_ANNOTATIONS = {"$schema", "$id", "title", "description", "$comment"}
_CONSTRAINTS = {"type", "required", "enum", "const", "minimum", "pattern", "properties", "additionalProperties", "propertyNames",
                "items", "$ref", "$defs"}   # pattern and propertyNames: a register's rule ids (task-0261)


def load(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate(instance: Any, schema: dict) -> list[str]:
    """Every violation, as '<path>: <what>'; empty when the instance conforms."""
    _supported(schema)
    errors: list[str] = []
    _check(instance, schema, schema, "$", errors)
    return errors


def _supported(node: Any) -> None:
    if isinstance(node, dict):
        unknown = set(node) - _ANNOTATIONS - _CONSTRAINTS
        if unknown:
            raise ValueError(f"schema keyword(s) outside the supported subset: {sorted(unknown)}")
        for k, v in node.items():
            if k in ("properties", "$defs"):
                for sub in v.values():
                    _supported(sub)
            elif k in ("items", "additionalProperties", "propertyNames") and isinstance(v, dict):
                _supported(v)


def _type_ok(v: Any, t: str) -> bool:
    return {"object": isinstance(v, dict), "array": isinstance(v, list), "string": isinstance(v, str),
            "boolean": isinstance(v, bool), "null": v is None,
            "integer": isinstance(v, int) and not isinstance(v, bool),
            "number": isinstance(v, (int, float)) and not isinstance(v, bool)}[t]


def same(a: Any, b: Any) -> bool:
    """JSON equality, type included (task-0200, doc-0030 G12): ``true`` is not ``1`` and ``2.0`` is not ``2``,
    as JSON Schema's enum and const read them; lists and objects compared item by item."""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


def _check(v: Any, s: dict, root: dict, path: str, errors: list[str]) -> None:
    if "$ref" in s:
        ref = s["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"only local $defs references are supported: {ref}")
        s = root["$defs"][ref.split("/")[-1]]
    if "type" in s:
        types = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(_type_ok(v, t) for t in types):
            errors.append(f"{path}: {type(v).__name__} is not {'/'.join(types)}")
            return
    if "enum" in s and not any(same(v, e) for e in s["enum"]):
        errors.append(f"{path}: {v!r} is not one of {s['enum']}")
    if "const" in s and not same(v, s["const"]):
        errors.append(f"{path}: {v!r} is not {s['const']!r}")
    if "minimum" in s and isinstance(v, (int, float)) and v < s["minimum"]:
        errors.append(f"{path}: {v} is below {s['minimum']}")
    if "pattern" in s and isinstance(v, str) and not re.search(s["pattern"], v):   # unanchored, as JSON Schema reads it
        errors.append(f"{path}: {v!r} does not match {s['pattern']!r}")
    if isinstance(v, dict) and isinstance(s.get("propertyNames"), dict):
        for k in v:
            _check(k, s["propertyNames"], root, f"{path}[{k!r}]", errors)
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v:
                errors.append(f"{path}: missing {k!r}")
        props = s.get("properties", {})
        extra = s.get("additionalProperties", True)
        for k, item in v.items():
            if k in props:
                _check(item, props[k], root, f"{path}.{k}", errors)
            elif extra is False:
                errors.append(f"{path}: unexpected {k!r}")
            elif isinstance(extra, dict):
                _check(item, extra, root, f"{path}.{k}", errors)
    if isinstance(v, list) and isinstance(s.get("items"), dict):
        for i, item in enumerate(v):
            _check(item, s["items"], root, f"{path}[{i}]", errors)

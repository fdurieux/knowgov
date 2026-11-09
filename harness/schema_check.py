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
_CONSTRAINTS = {"type", "required", "enum", "const", "minimum", "pattern", "minItems", "properties", "additionalProperties",
                "propertyNames", "items", "$ref", "$defs"}   # pattern and propertyNames: a register's rule ids (task-0261);
# minItems: the MCP tools' inputSchema (task-0281)


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
    _check_value(v, s, path, errors)
    if isinstance(v, dict):
        _check_object(v, s, root, path, errors)
    if isinstance(v, list) and isinstance(s.get("items"), dict):
        for i, item in enumerate(v):
            _check(item, s["items"], root, f"{path}[{i}]", errors)


def _ecma(pattern: str) -> str:
    """A JSON Schema pattern as ECMA-262 reads it: unanchored, with a final ``$`` the end of the string. Python's
    ``$`` also matches before a trailing newline, so it is read as ``\\Z`` (``C5\\n`` is no rule id)."""
    return pattern[:-1] + r"\Z" if pattern.endswith("$") and not pattern.endswith("\\$") else pattern


def _check_value(v: Any, s: dict, path: str, errors: list[str]) -> None:
    """enum, const, minimum, pattern and minItems: the keywords that read the value itself."""
    if "minItems" in s and isinstance(v, list) and len(v) < s["minItems"]:   # task-0281
        errors.append(f"{path}: {len(v)} item(s), fewer than {s['minItems']}")
    if "enum" in s and not any(same(v, e) for e in s["enum"]):
        errors.append(f"{path}: {v!r} is not one of {s['enum']}")
    if "const" in s and not same(v, s["const"]):
        errors.append(f"{path}: {v!r} is not {s['const']!r}")
    if "minimum" in s and isinstance(v, (int, float)) and v < s["minimum"]:
        errors.append(f"{path}: {v} is below {s['minimum']}")
    if "pattern" in s and isinstance(v, str) and not re.search(_ecma(s["pattern"]), v):
        errors.append(f"{path}: {v!r} does not match {s['pattern']!r}")


def _check_object(v: dict, s: dict, root: dict, path: str, errors: list[str]) -> None:
    """required, propertyNames, properties and additionalProperties."""
    for k in s.get("required", []):
        if k not in v:
            errors.append(f"{path}: missing {k!r}")
    if isinstance(s.get("propertyNames"), dict):   # a register's rule ids (task-0261)
        for k in v:
            _check(k, s["propertyNames"], root, f"{path}[{k!r}]", errors)
    props = s.get("properties", {})
    extra = s.get("additionalProperties", True)
    for k, item in v.items():
        if k in props:
            _check(item, props[k], root, f"{path}.{k}", errors)
        elif extra is False:
            errors.append(f"{path}: unexpected {k!r}")
        elif isinstance(extra, dict):
            _check(item, extra, root, f"{path}.{k}", errors)

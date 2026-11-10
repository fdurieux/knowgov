"""One validator for a subject's task policy, ``[tasks.<class>]`` (task-0242, doc-0033 R1).

The checker (``tools/check_subject.py``) lists every problem; the runtime (``harness/tasks.py``, which the
gate, ``gate_cli``, the MCP reader, ``run.py`` and the agent-key path all read) builds the policy only from a
table that has none, and otherwise raises ``TaskPolicyError`` naming the class and the field, the gate
contract's exit 2. Nothing is coerced into another type: ``block_levels = "absent"`` is not read as the
set of its letters, ``7`` is not a level, ``"0.25"`` is not a share and ``"yes"`` is not ``true``. A field
left out takes the documented default (the checker requires the three the gate needs).

A class's name is checked too (task-0278, decision-0033 choice 4): ``[a-z][a-z0-9_-]{0,31}``, and never
``keys``, the task a report on an agent-chosen key set names (doc-0014 C4: the MCP reader's ``keys``,
``KG_TASK=keys`` refused by the CI route, a ``keys`` report refused by the hook). ``name_problem``
says why a name is refused; ``build`` raises on it, so every runtime reader refuses the manifest with exit 2
naming the class, and the checker reports it.

Standard library only; no store, no subject.
"""
from __future__ import annotations

import re

# harness/gate.py ORDER, worse to better; tests/test_task_policy.py holds the two equal
LEVELS = ("absent", "declared_gap", "disputed", "invalidated", "proposed", "validated", "verified", "approved")
DEFAULT_BLOCK_LEVELS = ("absent", "declared_gap", "disputed", "invalidated")
DEFAULT_SHARE = 0.25
FIELDS = ("keys", "block_levels", "max_unverified_share", "require_approved", "rationale")
NAME = re.compile(r"[a-z][a-z0-9_-]{0,31}")   # task-0278: ASCII lower case, a letter first, at most 32 characters
RESERVED = ("keys",)                          # an agent-chosen key set's report names task "keys" (doc-0014 C4)


def table(name) -> str:
    """``[tasks.<name>]`` as the manifest writes it: the name TOML-quoted when it is not a bare key."""
    bare = isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_-]+", name)
    return f"[tasks.{name}]" if bare else '[tasks."' + str(name).replace("\\", "\\\\").replace('"', '\\"') + '"]'


class TaskPolicyError(ValueError):
    """A task policy the gate cannot apply as written: the class, the field and why."""

    def __init__(self, task: str, field: str, why: str):
        super().__init__(f"{table(task)} {field}: {why}")
        self.task, self.field, self.why = task, field, why


def name_problem(name) -> dict | None:
    """Why ``name`` cannot name a task class, as a problem (code ``task-class``), or None when it can."""
    hint = "name the class in lower case, a letter first, then letters, digits, '_' or '-', at most 32 characters (codegen, design)"
    if not isinstance(name, str) or not NAME.fullmatch(name):
        return {"code": "task-class", "field": "name", "value": name,
                "message": f"class name {name!r} is not [a-z][a-z0-9_-]{{0,31}}", "hint": hint}
    if name in RESERVED:
        return {"code": "task-class", "field": "name", "value": name,
                "message": f"class name {name!r} is reserved: a report on an agent-chosen key set names its task {name!r} (doc-0014 C4)",
                "hint": "rename the class, such as codegen or design"}
    return None


def problems(spec) -> list[dict]:
    """Every problem of one ``[tasks.<class>]`` table, as {code, field, value, message, hint}; empty when the
    gate can apply it as written. ``code`` is the checker's: required, block-level, share, require-approved,
    rationale; ``name_problem``'s is task-class."""
    if not isinstance(spec, dict):
        return [{"code": "required", "field": "", "value": spec, "message": "not a table",
                 "hint": "write the class as a table with keys, block_levels and max_unverified_share"}]
    out = []
    if "keys" in spec:
        keys = spec["keys"]
        if not isinstance(keys, list) or not keys:
            out.append({"code": "required", "field": "keys", "value": keys, "message": "keys is not a non-empty list",
                        "hint": "list the keys the task needs"})
        else:
            for k in keys:
                if not isinstance(k, str) or not k:
                    out.append({"code": "required", "field": "keys", "value": k, "message": f"key {k!r} is not a non-empty string",
                                "hint": "write each key as \"entity|attribute\""})
    if "block_levels" in spec:
        bl = spec["block_levels"]
        if not isinstance(bl, list):
            out.append({"code": "block-level", "field": "block_levels", "value": bl,
                        "message": f"block_levels {bl!r} is not a list of gate levels",
                        "hint": f"write a list, such as [{', '.join(repr(x) for x in DEFAULT_BLOCK_LEVELS)}]"})
        else:
            for lv in bl:
                if not isinstance(lv, str) or lv not in LEVELS:
                    out.append({"code": "block-level", "field": "block_levels", "value": lv,
                                "message": f"block level {lv!r} is not a gate level", "hint": f"use one of {', '.join(LEVELS)}"})
    if "max_unverified_share" in spec:
        share = spec["max_unverified_share"]
        if isinstance(share, bool) or not isinstance(share, (int, float)) or not 0 <= share <= 1:
            out.append({"code": "share", "field": "max_unverified_share", "value": share,
                        "message": f"max_unverified_share {share!r} is not a number from 0 to 1", "hint": "write a share such as 0.25"})
    if "require_approved" in spec and not isinstance(spec["require_approved"], bool):
        out.append({"code": "require-approved", "field": "require_approved", "value": spec["require_approved"],
                    "message": f"require_approved {spec['require_approved']!r} is not true or false",
                    "hint": "write require_approved = true for a class whose keys a person must have approved, or leave it out"})
    if "rationale" in spec and not isinstance(spec["rationale"], str):
        out.append({"code": "rationale", "field": "rationale", "value": spec["rationale"],
                    "message": f"rationale {spec['rationale']!r} is not text", "hint": "write the rationale as a string"})
    return out


def build(task: str, spec) -> dict:
    """The policy the gate applies, from a table with no problem; ``TaskPolicyError`` on the first one."""
    named = name_problem(task)   # task-0278: a name the gate cannot be asked for is refused before its table is read
    if named:
        raise TaskPolicyError(task, "name", named["message"])
    found = problems(spec)
    if found:
        p = found[0]
        raise TaskPolicyError(task, p["field"] or "table", p["message"] + (f" ({len(found) - 1} more)" if len(found) > 1 else ""))
    import key_rule   # task-0301: a class's keys in NFC, as the store holds them
    for k in spec.get("keys", []):   # task-0316 N8: a malformed key reads absent at the gate, so it is refused here
        why = key_rule.refusal(k)
        if why:
            raise TaskPolicyError(task, "keys", why)
    return {"keys": key_rule.normalise_all(list(spec.get("keys", []))),
            "block_levels": set(spec.get("block_levels", DEFAULT_BLOCK_LEVELS)),
            "max_unverified_share": float(spec.get("max_unverified_share", DEFAULT_SHARE)),   # an int 0 or 1 is that share
            # task-0215 (decision-0018 point 4): opt-in, the class's keys must be approved, not only verified
            "require_approved": spec.get("require_approved", False),
            "rationale": " ".join(spec.get("rationale", "").split()) or None}

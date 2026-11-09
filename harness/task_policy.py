"""One validator for a subject's task policy, ``[tasks.<class>]`` (task-0242, doc-0033 R1).

The checker (``tools/check_subject.py``) lists every problem; the runtime (``harness/tasks.py``, which the
gate, ``gate_cli``, the MCP reader, ``run.py`` and the agent-key path all read) builds the policy only from a
table that has none, and otherwise raises ``TaskPolicyError`` naming the class and the field, the gate
contract's exit 2. Nothing is coerced into another type: ``block_levels = "absent"`` is not read as the
set of its letters, ``7`` is not a level, ``"0.25"`` is not a share and ``"yes"`` is not ``true``. A field
left out takes the documented default (the checker requires the three the gate needs).

Standard library only; no store, no subject.
"""
from __future__ import annotations

# harness/gate.py ORDER, worse to better; tests/test_task_policy.py holds the two equal
LEVELS = ("absent", "declared_gap", "disputed", "invalidated", "proposed", "validated", "verified", "approved")
DEFAULT_BLOCK_LEVELS = ("absent", "declared_gap", "disputed", "invalidated")
DEFAULT_SHARE = 0.25
FIELDS = ("keys", "block_levels", "max_unverified_share", "require_approved", "rationale")


class TaskPolicyError(ValueError):
    """A task policy the gate cannot apply as written: the class, the field and why."""

    def __init__(self, task: str, field: str, why: str):
        super().__init__(f"[tasks.{task}] {field}: {why}")
        self.task, self.field, self.why = task, field, why


def problems(spec) -> list[dict]:
    """Every problem of one ``[tasks.<class>]`` table, as {code, field, value, message, hint}; empty when the
    gate can apply it as written. ``code`` is the checker's: required, block-level, share, require-approved,
    rationale."""
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
    found = problems(spec)
    if found:
        p = found[0]
        raise TaskPolicyError(task, p["field"] or "table", p["message"] + (f" ({len(found) - 1} more)" if len(found) > 1 else ""))
    return {"keys": list(spec.get("keys", [])),
            "block_levels": set(spec.get("block_levels", DEFAULT_BLOCK_LEVELS)),
            "max_unverified_share": float(spec.get("max_unverified_share", DEFAULT_SHARE)),   # an int 0 or 1 is that share
            # task-0215 (decision-0018 point 4): opt-in, the class's keys must be approved, not only verified
            "require_approved": spec.get("require_approved", False),
            "rationale": " ".join(spec.get("rationale", "").split()) or None}

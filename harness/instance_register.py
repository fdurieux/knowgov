"""An instance reads its own register, or refuses (task-0334, decision-0039 §3.1 (a)).

``KG_REGISTER`` names the register a process reads. Unset (or empty), a subject that ships in this checkout
reads the public register vendored under ``demo/register``, so the record does not move. A subject outside
this checkout (``KG_SUBJECT``, which a command's ``--subject`` sets) is an organisation's instance: it never
falls back to the public register, whose lifecycle months, owners and handles are not the organisation's.
Every register-reading tool refuses, exit 2, naming ``KG_REGISTER``: ``cadence.register_root`` raises
``RegisterUnnamed``, ``register_impact.register_root`` and ``require_named`` raise ``RegisterUnreadable`` with the
same line, and the commands' start checks (``cli_exit.run(register=True)``, ``gate_cli``, ``trace``, the MCP
reader at start, ``register_nodes``, ``upward``, ``proposal_impact``) call them before anything is read.
``instance/ci/knowgov-gate.sh`` and ``instance/ci/claude/knowgov_hook.py`` pass ``<instance>/register`` unless
one is set. "Outside this checkout" is ``execution_guard.outside``, the one test of a mounted instance.
Standard library only.
"""
from __future__ import annotations

import os

import execution_guard

SETTING = "KG_REGISTER"


class RegisterUnnamed(RuntimeError):
    """An instance's subject with no register named: cannot run, exit 2 (``cli_exit.OWN``)."""


def unnamed(env=None) -> str | None:
    """Why the default register may not be read, or None: ``KG_REGISTER`` set, or the subject inside this checkout."""
    env = os.environ if env is None else env
    if env.get(SETTING):
        return None
    subj = execution_guard.outside(env.get("KG_SUBJECT"))
    if not subj:
        return None
    return (f"{SETTING} is unset and the subject {subj} lies outside this knowgov checkout: an instance reads its "
            f"own register, never the public one under demo/register; set {SETTING} to the instance's register "
            f"(<instance>/register; decision-0039)")


def check(env=None) -> None:
    """``RegisterUnnamed`` when ``unnamed`` gives a reason."""
    why = unnamed(env)
    if why:
        raise RegisterUnnamed(why)

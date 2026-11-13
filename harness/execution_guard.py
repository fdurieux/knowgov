"""The host-side guard (task-0141.07): code a model wrote on the host runs inside the process's own
environment, with what it can read and reach; the contained worker (task-0141.05, X1) is the containment and
admits a configured worker whatever is mounted (``execution.check``). On the host, every path that executes
model output refuses when an organisation's instance is
mounted, that is when KG_SUBJECT, KG_SUBJECTS or KG_REGISTER names a folder outside this checkout
(demo/docker-compose.instance.yml mounts one at /instance), unless the operator sets
KG_ALLOW_UNCONTAINED_EXECUTION=1 and so accepts that the code runs uncontained beside that data.
The public demo, whose subjects and register ship in this checkout, runs as before.

The paths (the call-site audit of task-0141.07): harness/measures.py run_suite (a single-reply arm's
code graded by the oracle), run_suite_dir (an agent run's sandbox graded) and feedback_runner (the
agent's own run_suite tool), all three through the oracle script's loader; harness/run.py refuses
before an arms run's first model call, and the page refuses an arms run before it starts one."""
from __future__ import annotations

import os
from pathlib import Path

import switches

ROOT = Path(__file__).resolve().parent.parent   # the checkout: what ships with knowgov
OPT_IN = "KG_ALLOW_UNCONTAINED_EXECUTION"
WATCHED = ("KG_SUBJECT", "KG_SUBJECTS", "KG_REGISTER")


class ExecutionRefused(RuntimeError):
    """Model output would run uncontained beside an organisation's mounted data."""


def mounted(env=None) -> dict[str, str]:
    """The watched variables that name a folder outside this checkout, by name."""
    env = os.environ if env is None else env
    out = {}
    for name in WATCHED:
        path = outside(env.get(name))
        if path:
            out[name] = path
    return out


def outside(value: str | None) -> str | None:
    """The folder ``value`` names, resolved, when it lies outside this checkout; None when it is empty or
    inside. The one test of "an organisation's instance" (also ``cadence.register_root``'s, task-0334)."""
    value = (value or "").strip()
    if not value:
        return None
    path = Path(value)
    path = (path if path.is_absolute() else Path.cwd() / path).resolve()
    return str(path) if path != ROOT and ROOT not in path.parents else None


def refusal(env=None) -> str | None:
    """None when model output may run here, else why it may not."""
    env = os.environ if env is None else env
    found = mounted(env)
    if not found or switches.on(OPT_IN, env):   # 1 only; any other spelling but 0 or empty is BadSwitch (task-0276)
        return None
    named = ", ".join(f"{k}={v}" for k, v in found.items())
    return (f"refused: an organisation's instance is mounted ({named}) and code a model wrote would run "
            f"uncontained beside it, with this process's environment and files; start the stack's contained worker "
            f"(KG_WORKER_JOBS; task-0141.05 (X1), which admits it), or set {OPT_IN}=1 to accept that risk and lift this refusal")


def check(env=None) -> None:
    why = refusal(env)
    if why:
        raise ExecutionRefused(why)

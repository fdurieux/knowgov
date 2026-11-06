"""A stopgap (task-0141.07), not containment: code a model wrote runs on this machine, inside the
process's own environment, with what it can read and reach (task-0141.05, X1, is the containment).
Until X1 lands, every path that executes model output refuses when an organisation's instance is
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
        value = (env.get(name) or "").strip()
        if not value:
            continue
        path = Path(value)
        path = (path if path.is_absolute() else Path.cwd() / path).resolve()
        if path != ROOT and ROOT not in path.parents:
            out[name] = str(path)
    return out


def refusal(env=None) -> str | None:
    """None when model output may run here, else why it may not."""
    env = os.environ if env is None else env
    found = mounted(env)
    if not found or env.get(OPT_IN) == "1":
        return None
    named = ", ".join(f"{k}={v}" for k, v in found.items())
    return (f"refused: an organisation's instance is mounted ({named}) and code a model wrote would run "
            f"uncontained beside it, with this process's environment and files; containment is task-0141.05 (X1), "
            f"not yet built. {OPT_IN}=1 accepts that risk and lifts this refusal")


def check(env=None) -> None:
    why = refusal(env)
    if why:
        raise ExecutionRefused(why)

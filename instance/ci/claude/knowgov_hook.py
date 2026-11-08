#!/usr/bin/env python3
"""The knowledge gate as a fail-closed Claude Code hook, at stage transitions (task-0099).

Supersedes doc-0004's "Exit codes" paragraph (its adapter: findings 1 -> 2, cannot-run 2 -> a
non-blocking error), by doc-0014 §5 C1, decision B, and §11: a mandatory hook blocks on the gate's
exit 1 *and* exit 2, and says which. doc-0004's adapter survives only as the advisory profile
(``--advisory``), which is fail-open and labelled so. The gate contract does not move: 0 pass, 1 a
finding at or above the threshold, 2 cannot run; the mapping to the vendor's protocol lives here.

Claude Code's hook contract (code.claude.com/docs/en/hooks): a PreToolUse hook reads one JSON event
on stdin (``tool_name``, ``tool_input``, ``cwd``, ...); exit 2 blocks the tool call and its stderr
is the reason Claude sees; exit 0 with no output is no decision; any other exit is a non-blocking
error unless the hook sets ``"onFailure": "block"``, which the settings snippets beside this file do
so that a crash, a missing interpreter or a timeout blocks too. Every blocking path here exits 2.

    python3 knowgov_hook.py gate --task CLASS [--task-for STAGE=CLASS ...] [--knowgov DIR]
                                 [--instance DIR] [--spec GLOB ...] [--advisory] [--timeout S]
    python3 knowgov_hook.py run [--check NAME] [--route TEXT] [--advisory] -- COMMAND ...

``gate`` fires at stage transitions, never on every edit (playbook p. 27): ``plan`` when a plan is
presented for acceptance (``ExitPlanMode``), ``spec`` when a commit carries a spec file (``--spec``
globs, default ``spec.md`` at any depth), ``push`` before ``git push``. Any other event is no
transition: exit 0, no decision. At a transition it calls ``knowgov-gate.sh <knowgov> <instance>
gate`` with the task class (``--task``, or ``--task-for`` for that stage) and reads its report; a
report for any other task, or for the agent-chosen key set the MCP server names ``keys``, is refused
(doc-0014 C4, decision B), as is a report that disagrees with the exit code.

``run`` is the same mapping for any other check under the gate contract: it runs COMMAND and maps its
exit. ``decide`` is the mapping itself, for a script that imports this module (task-0105's hooks on
knowgov's own protected paths reuse it; nothing is copied).

Standard library only. The knowgov checkout is ``--knowgov``, else ``KG_HOME``, else the checkout
this file sits in; the instance is ``--instance``, else ``CLAUDE_PROJECT_DIR``, else the event's
``cwd``. The store, the subject, the scenario and the date are the gate's ``KG_*`` variables, as
knowgov-gate.sh reads them; one store per worktree (instance/README.md).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

PASS, FINDING, CANNOT_RUN = 0, 1, 2     # the gate contract
HOOK_ALLOW, HOOK_BLOCK = 0, 2           # Claude Code: exit 0 no decision, exit 2 blocks the tool call
STAGES = ("plan", "spec", "push")
FREE_KEYS = "keys"                      # the task the MCP server names a report for an agent-chosen key set

ROUTE = ("Route to approval: the owner of each blocking key answers it (harness/capture.py questionnaire, "
         "then ingest), and a reviewer who is not the author settles it in a review file (harness/capture.py "
         "review; decision-0002: a session may propose, never approve, its own knowledge). An exception is "
         "granted by whoever owns the managed settings, never by this session; do not retry around the gate.")
UNAVAILABLE_ROUTE = ("Route: make the gate runnable (the store reachable, the subject and scenario set, the "
                     "knowgov checkout present), then repeat the step; an exception is granted by whoever owns "
                     "the managed settings, never by this session.")


@dataclass(frozen=True)
class Decision:
    """What the hook does: its exit code, the reason on stderr (Claude reads it on a block), and an
    optional JSON object on stdout (the advisory profile's warning, as ``systemMessage``)."""
    exit_code: int
    reason: str = ""
    output: dict | None = None

    @property
    def blocks(self) -> bool:
        return self.exit_code == HOOK_BLOCK


def decide(rc: int, *, check: str = "knowgov gate", finding: str = "", unavailable: str = "",
           route: str = ROUTE, unavailable_route: str = UNAVAILABLE_ROUTE, advisory: bool = False) -> Decision:
    """The contract's exit code mapped to the hook's. Mandatory (the default): 0 lets the action
    through; 1 blocks, naming the finding and the route to approval (``route``); 2 or anything else
    blocks, naming the gate as unavailable (fail closed) and the route to making it run
    (``unavailable_route``, the gate's by default; a check other than the gate passes its own).
    Advisory, fail-open: 1 still blocks, but the gate unavailable lets the action through with a warning."""
    if rc == PASS:
        return Decision(HOOK_ALLOW)
    if rc == FINDING:
        return Decision(HOOK_BLOCK, f"{check}: BLOCKED by a finding (exit 1).\n{finding}\n{route}".replace("\n\n", "\n"))
    what = f"{check}: the gate is unavailable (exit {rc})" + (f": {unavailable}" if unavailable else "")
    if advisory:
        return Decision(HOOK_ALLOW, output={"systemMessage": f"{what}. ADVISORY PROFILE, FAIL-OPEN: the action goes ahead unchecked."})
    return Decision(HOOK_BLOCK, f"{what}.\nFail-closed: the action is blocked until the gate runs.\n{unavailable_route}")


def refuse(check: str, why: str) -> Decision:
    """A report the hook cannot rely on: blocked in every profile, since it is not the gate being down."""
    return Decision(HOOK_BLOCK, f"{check}: refused: {why}.\nA mandatory check reads a report for its own task class only.\n{ROUTE}")


def entry(main, check: str, *args) -> int:
    """A hook's whole run, so that nothing escapes as Claude Code's non-blocking exit 1 (task-0200, doc-0030
    P8): ``main``'s exit, or, on any exception, a refusal that blocks in every profile, the advisory one
    included, since a crash is not the gate being down."""
    try:
        return main(*args)
    except SystemExit as e:   # argparse's usage error and a main's own exit: a code other than 0 or 2 blocks too
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else HOOK_BLOCK)
        return code if code in (HOOK_ALLOW, HOOK_BLOCK) else emit(refuse(check, f"the hook exited {code}"))
    except BaseException as e:  # noqa: BLE001 - fail closed
        return emit(refuse(check, f"the hook failed: {type(e).__name__}: {e}"))


def emit(d: Decision) -> int:
    if d.output is not None:
        print(json.dumps(d.output))
    if d.reason:
        print(d.reason, file=sys.stderr)
    return d.exit_code


# --- transitions -------------------------------------------------------------------------------

_GIT = r"(?:^|[;&|(\n]|\s)git(?:\s+(?:-[Cc]\s+\S+|--?[\w-]+(?:=\S+)?))*\s+"


def _git(cmd: str, sub: str) -> bool:
    return re.search(_GIT + sub + r"(?:\s|$|[;&|)])", cmd) is not None


def _committed(cwd: str, cmd: str) -> list[str] | None:
    """The paths the commit carries: staged, plus tracked changes under -a/--all; None if git cannot tell."""
    runs = [["diff", "--cached", "--name-only"]]
    if re.search(r"\s(?:--all|-[a-zA-Z]*a[a-zA-Z]*)(?:\s|$)", cmd.split("commit", 1)[-1]):
        runs.append(["diff", "--name-only"])
    out: list[str] = []
    for r in runs:
        p = subprocess.run(["git", "-C", cwd or ".", *r], capture_output=True, text=True)
        if p.returncode:
            return None
        out += p.stdout.split()
    return out


def transition(event: dict, spec_globs: list[str]) -> str | None:
    """The stage a tool call moves to, or None: not a transition, the hook has no decision."""
    tool = event.get("tool_name")
    if tool == "ExitPlanMode":
        return "plan"
    if tool != "Bash":
        return None
    cmd = str((event.get("tool_input") or {}).get("command") or "")
    if _git(cmd, "push"):
        return "push"
    if _git(cmd, "commit"):
        paths = _committed(str(event.get("cwd") or ""), cmd)
        if paths is None:   # cannot tell what the commit carries: treat it as the transition (fail closed)
            return "spec"
        if any(fnmatch.fnmatch(p, g) or fnmatch.fnmatch(Path(p).name, g) for p in paths for g in spec_globs):
            return "spec"
    return None


# --- the gate ----------------------------------------------------------------------------------

def _knowgov(arg: str | None) -> Path | None:
    """The first of --knowgov, KG_HOME and this file's checkout that is named; None if it holds no gate."""
    c = Path(arg or os.environ.get("KG_HOME") or Path(__file__).resolve().parents[3])
    return c if (c / "instance" / "ci" / "knowgov-gate.sh").is_file() else None


def _summary(rep: dict) -> str:
    head = (f"{rep.get('verdict')} on {rep.get('subject')} {rep.get('scenario')}, task {rep.get('task')}, "
            f"as of {rep.get('as_of')}, threshold {rep.get('threshold')}")
    worst = [f for f in rep.get("findings") or [] if f.get("severity") in ("blocker", "critical")] or (rep.get("findings") or [])
    lines = [f"  {f.get('severity')} {f.get('kind')}" + (f" {f['key']}" if f.get("key") else "") + f": {f.get('message')}"
             + (f" (owner {f.get('owner') or 'none in the register map'}"
                + (f"; closed by {f.get('closer') or 'no unit of the register'}" if "closer" in f else "") + ")"
                if "owner" in f else "")
             for f in worst[:6]]
    routes = sorted({f["route"] for f in worst[:6] if f.get("route")})   # task-0102: each owner's questionnaire
    lines += [f"  route: {r}" for r in routes]
    more = len(worst) - len(lines)
    return "\n".join([head, *lines] + ([f"  ... and {more} more"] if more > 0 else []))


def run_gate(stage: str, task: str, kg: Path, inst: Path, *, advisory: bool, timeout: float) -> Decision:
    check = f"knowgov gate at {stage}"
    keep = os.environ.get("KG_REPORT")
    tmp = None
    if keep:
        report = Path(keep) if Path(keep).is_absolute() else inst / keep
    else:
        fd, tmp = tempfile.mkstemp(prefix="knowgov-hook-", suffix=".json")
        os.close(fd)
        report = Path(tmp)
    try:
        report.unlink(missing_ok=True)
        env = {**os.environ, "KG_TASK": task, "KG_REPORT": str(report)}
        env.pop("KG_ANNOTATE", None)
        env.setdefault("PYTHON", sys.executable)   # the gate runs the hook's interpreter unless PYTHON names one (task-0141.01)
        cmd = ["sh", str(kg / "instance" / "ci" / "knowgov-gate.sh"), str(kg), str(inst), "gate"]
        try:
            p = subprocess.run(cmd, cwd=str(inst), env=env, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return decide(CANNOT_RUN, check=check, unavailable=f"no answer within {timeout:g} s", advisory=advisory)
        except OSError as e:
            return decide(CANNOT_RUN, check=check, unavailable=str(e), advisory=advisory)
        if p.returncode not in (PASS, FINDING):
            tail = " ".join((p.stderr or p.stdout).strip().splitlines()[-3:])
            return decide(p.returncode, check=check, unavailable=tail, advisory=advisory)
        try:
            rep = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            return refuse(check, f"exit {p.returncode} without a readable report ({e.__class__.__name__})")
        if not isinstance(rep, dict):   # P8: valid JSON that is not a report raised, exit 1, read as a warning
            return refuse(check, f"exit {p.returncode} with a report that is not a JSON object ({type(rep).__name__})")
        if rep.get("task") == FREE_KEYS:
            return refuse(check, "the report is for an agent-chosen key set (task 'keys'), not a task class")
        if rep.get("task") != task:
            return refuse(check, f"the report is for task {rep.get('task')!r}, the hook requires {task!r}")
        if rep.get("exit_code") != p.returncode or (p.returncode == PASS and rep.get("verdict") == "BLOCKED"):
            return refuse(check, f"the report ({rep.get('verdict')}, exit_code {rep.get('exit_code')}) disagrees with exit {p.returncode}")
        return decide(p.returncode, check=check, finding=_summary(rep), advisory=advisory)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


def _event(advisory: bool) -> tuple[dict | None, Decision | None]:
    raw = sys.stdin.read()
    try:
        ev = json.loads(raw)
        if not isinstance(ev, dict):
            raise ValueError("not an object")
        return ev, None
    except ValueError as e:
        return None, decide(CANNOT_RUN, check="knowgov hook", unavailable=f"unreadable hook event on stdin ({e})", advisory=advisory)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="knowgov_hook.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate", help="the knowledge gate at a stage transition")
    g.add_argument("--task", required=True, help="the task class every transition checks (never 'keys')")
    g.add_argument("--task-for", action="append", default=[], metavar="STAGE=CLASS", help="another class for one stage")
    g.add_argument("--knowgov", help="the knowgov checkout (default KG_HOME, else the one this file is in)")
    g.add_argument("--instance", help="the instance checkout (default CLAUDE_PROJECT_DIR, else the event's cwd)")
    g.add_argument("--spec", action="append", default=[], metavar="GLOB", help="a spec file's path glob (default spec.md, any depth)")
    g.add_argument("--advisory", action="store_true", help="FAIL-OPEN: the gate unavailable lets the action through")
    g.add_argument("--timeout", type=float, default=540, help="seconds for the gate, under the hook's own timeout (default 540)")
    r = sub.add_parser("run", help="any check under the gate contract, mapped the same way")
    r.add_argument("--check", default="check", help="the check's name in the message")
    r.add_argument("--route", default=ROUTE, help="the route to approval a finding names")
    r.add_argument("--unavailable-route", default=UNAVAILABLE_ROUTE, help="the route to making the check run, when it cannot")
    r.add_argument("--advisory", action="store_true", help="FAIL-OPEN: exit 2 lets the action through")
    r.add_argument("command", nargs=argparse.REMAINDER, help="-- COMMAND ...")
    a = ap.parse_args(argv)

    ev, bad = _event(a.advisory)
    if bad:
        return emit(bad)
    if a.cmd == "run":
        cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
        if not cmd:
            return emit(decide(CANNOT_RUN, check=a.check, unavailable="no command", advisory=a.advisory))
        try:
            p = subprocess.run(cmd, input=json.dumps(ev), capture_output=True, text=True)
        except OSError as e:
            return emit(decide(CANNOT_RUN, check=a.check, unavailable=str(e), advisory=a.advisory))
        said = (p.stderr or p.stdout).strip()
        return emit(decide(p.returncode, check=a.check, finding=said, unavailable=said, route=a.route,
                           unavailable_route=a.unavailable_route, advisory=a.advisory))

    if a.task == FREE_KEYS:
        return emit(refuse("knowgov hook", "--task keys is an agent-chosen key set, not a task class"))
    per = {}
    for s in a.task_for:
        stage, _, cls = s.partition("=")
        if stage not in STAGES or not cls or cls == FREE_KEYS:
            return emit(decide(CANNOT_RUN, check="knowgov hook", unavailable=f"bad --task-for {s!r} (stages: {', '.join(STAGES)})", advisory=a.advisory))
        per[stage] = cls
    stage = transition(ev, a.spec or ["spec.md"])
    if stage is None:
        return HOOK_ALLOW
    kg = _knowgov(a.knowgov)
    if kg is None:
        return emit(decide(CANNOT_RUN, check=f"knowgov gate at {stage}", unavailable="no knowgov checkout (--knowgov or KG_HOME)", advisory=a.advisory))
    inst = Path(a.instance or os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or ".")
    if not inst.is_dir():
        return emit(decide(CANNOT_RUN, check=f"knowgov gate at {stage}", unavailable=f"no instance at {inst}", advisory=a.advisory))
    return emit(run_gate(stage, per.get(stage, a.task), kg, inst.resolve(), advisory=a.advisory, timeout=a.timeout))


if __name__ == "__main__":
    sys.exit(entry(main, "knowgov hook"))

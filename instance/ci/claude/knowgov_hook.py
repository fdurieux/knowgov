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
globs, default ``spec.md`` at any depth), ``push`` before ``git push``. Git is read from the command's
tokens (task-0204, doc-0030 P2): ``git``, ``/usr/bin/git``, after ``-C``/``-c``, inside ``bash -c '...'``,
across ``&&``, ``;`` and pipes. A commit is ``spec`` too when its own command stages or names a spec path
(``git add spec.md && git commit``, ``git commit spec.md``), a folder, ``.`` or a glob holding a changed
one, or stages broadly (``-A``, ``-u``, ``-a``) while one is changed; a command that cannot be read, or a
worktree git cannot read, fails closed to ``spec``. A backtick ends a command, and an alias is read as what it
runs, set inline (``git -c alias.ship=push ship``) or in git's configuration; a variable where git or its
subcommand would be (``git${IFS}push``, ``x=git; $x push``) fails closed to ``push`` or ``spec`` by what the
command names (task-0268). A ``tool_name``, ``tool_input`` or command of another type than its shape's is refused
in every profile, as is a ``--task-for`` naming one stage twice; ``--knowgov`` and ``KG_HOME`` are made absolute
where the hook starts, and ``--timeout`` is a finite number of seconds above 0. Any other event is no
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
knowgov-gate.sh reads them; one store per worktree (instance/README.md). The register is ``KG_REGISTER``,
else ``<instance>/register``, the instance's own, passed to the gate (task-0334, decision-0039 §3.1).
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
ATTESTATION_ROUTE = ("Route to approval: an attestation is a person's act, not this session's (decision-0002, decision-0009). The "
                     "route on each attestation finding above names who lists which Version; an execution is listed only "
                     "after the implementation and suite are brought in line with the Version where its values differ, and the suite run on it. An exception is granted by "
                     "whoever owns the managed settings, never by this session; do not retry around the gate.")
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

_GIT = r"(?:^|[;&|(\n\s'\"`]|/)git(?:\s+(?:-[Cc]\s+\S+|--?[\w-]+(?:=\S+)?))*\s+"
SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")", ";;", "\n", "`"}
_RUNNERS = {"eval", "exec", "command", "env", "nohup", "time", "sudo", "xargs", "builtin"}   # what runs the next word as a command
_PUNCT = "();<>|&`"   # shlex's punctuation, with the backtick: a command substitution ends a command (task-0268)
# git's global options that take a value (git -C dir, git -c k=v); the subcommand follows them
_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix", "--config-env"}
# options of add, rm, mv and commit that take a value, so the value is not read as a path
_WITH_VALUE = {"-m", "--message", "-F", "--file", "-C", "--reuse-message", "-c", "--reedit-message", "--author", "--date",
               "-t", "--template", "--fixup", "--squash", "--cleanup", "--trailer", "--pathspec-from-file", "-S", "--gpg-sign"}
# staging that takes everything changed, the paths named or not
_BROAD = {"-A", "--all", "-u", "--update", "-a", "--include", "-i"}


def _git(cmd: str, sub: str) -> bool:
    """The fallback reading, by pattern, when the command cannot be tokenised."""
    return re.search(_GIT + sub + r"(?:\s|$|[;&|)'\"`])", cmd) is not None


def _sep(t: str) -> bool:
    """A token that ends a command: a separator, or a run of punctuation only (``;&``, ``)` ``)."""
    return t in SEPARATORS or (bool(t) and set(t) <= set(_PUNCT + "\n") and not set(t) <= set("<>"))


def _tokens(cmd: str) -> list[str] | None:
    """The command's shell words, a backtick and the other punctuation each its own; None when quotes do not balance."""
    import shlex
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=_PUNCT)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return None


def _is_head(toks: list[str], i: int) -> bool:
    """Whether word ``i`` is where a command name goes: first, after a separator, a runner (eval, env) or an assignment."""
    if i == 0:
        return True
    prev = toks[i - 1]
    return _sep(prev) or prev in _RUNNERS or ("=" in prev and not prev.startswith("-"))


def _nested(t: str, depth: int) -> bool:
    """A quoted word that is itself a command (``bash -c '...'``, ``eval "..."``), to be read in turn."""
    return depth < 4 and ("git" in t or "$" in t) and any(c in t for c in " \n;&`")


def _note_alias(value: str, aliases: dict | None) -> None:
    """``-c alias.NAME=VALUE``: recorded, so that ``NAME`` reads as what it runs (task-0268)."""
    if aliases is not None and value.lower().startswith("alias."):
        name, _, run = value[len("alias."):].partition("=")
        aliases[name.lower()] = run


def _call_at(toks: list[str], j: int, aliases: dict | None) -> tuple[tuple[str, list[str]] | None, int]:
    """The git call whose global options start at word ``j``, and the word after it; None when no subcommand follows."""
    while j < len(toks) and toks[j].startswith("-") and not _sep(toks[j]):
        if toks[j] in _GLOBAL_WITH_VALUE and j + 1 < len(toks):
            if toks[j] == "-c":
                _note_alias(toks[j + 1], aliases)
            j += 2
        else:
            j += 1
    if j >= len(toks) or _sep(toks[j]):
        return None, j
    k = j + 1
    while k < len(toks) and not _sep(toks[k]):
        k += 1
    sub = toks[j]
    return (("$", [sub]) if "$" in sub else (sub, toks[j + 1:k])), k   # git $x: the subcommand is not in the text


def git_calls(cmd: str, depth: int = 0, aliases: dict | None = None) -> list[tuple[str, list[str]]] | None:
    """Every git subcommand the shell command runs, with its arguments: ``git``, ``/usr/bin/git``, after ``-C``
    and ``-c`` and other global options, inside ``bash -c '...'`` and ``sh -c``, across ``&&``, ``;``, pipes and
    backticks (task-0204, doc-0030 P2; task-0268). None when the command cannot be read (unbalanced quotes): the
    caller fails closed. A token that expands a variable where git or a command could be (``git${IFS}push``,
    ``x=git; $x push``) is returned as the call ``("$", [token])``: the caller cannot tell what runs and fails closed.
    ``aliases``, when given, collects the ``-c alias.NAME=VALUE`` a call sets (task-0268)."""
    toks = _tokens(cmd)
    if toks is None:
        return None
    out: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if _nested(t, depth):
            inner = git_calls(t, depth + 1, aliases)
            if inner is None:
                return None
            out += inner
        elif "$" in t and ("git" in t or _is_head(toks, i)):   # git${IFS}push, $x push: what runs is not in the text
            out.append(("$", [t]))
        elif Path(t).name == "git":
            call, k = _call_at(toks, i + 1, aliases)
            if call is not None:
                out.append(call)
                i = k
                continue
        i += 1
    return out


def _repo_aliases(cwd: str) -> dict[str, str]:
    """The aliases git's configuration defines for the worktree (repository, global and system); none outside a
    repository, where an alias could not run either."""
    try:
        p = subprocess.run(["git", "-C", cwd or ".", "config", "--get-regexp", r"^alias\."], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return {}
    out = {}
    for ln in p.stdout.splitlines() if p.returncode == 0 else []:
        name, _, value = ln.partition(" ")
        out[name[len("alias."):].lower()] = value
    return out


def _alias_runs(sub: str, run: str, args: list[str], aliases: dict[str, str], depth: int) -> list:
    """What alias ``sub`` (``run``) runs: a shell alias's calls, a git alias's subcommand, or ``("$", ...)``."""
    if depth >= 8:
        return [("$", [sub])]
    if run.startswith("!"):
        inner = git_calls(run[1:])
        return [("$", [sub])] if inner is None else _expand(inner, aliases, depth + 1)
    words = run.split()
    return _expand([(words[0], words[1:] + args)], aliases, depth + 1) if words else [("$", [sub])]


def _expand(calls, aliases: dict[str, str], depth: int = 0):
    """The calls, each followed by what its alias runs: ``ship = push`` adds push, ``!git push`` its shell command's
    calls; a loop or a shell alias that cannot be read adds the call ``("$", ...)``, which fails closed. The call
    itself stays, since git runs a builtin over an alias of the same name: expanding only ever adds."""
    out = []
    for sub, args in calls:
        out.append((sub, args))
        run = aliases.get(sub.lower()) if sub != "$" else None
        if run is not None:
            out += _alias_runs(sub, run, args, aliases, depth)
    return out


def _paths_named(args: list[str]) -> tuple[list[str], bool]:
    """The pathspecs a staging or committing call names, and whether it stages everything changed."""
    paths, broad, i, rest = [], False, 0, False
    while i < len(args):
        a = args[i]
        if rest:
            paths.append(a)
        elif a == "--":
            rest = True
        elif a in _WITH_VALUE:
            i += 1
        elif a.startswith("-") and len(a) > 1:
            if a in _BROAD or a.split("=", 1)[0] in _BROAD or (not a.startswith("--") and set(a[1:]) & {"A", "a", "u", "i"}):
                broad = True
        else:
            paths.append(a)
        i += 1
    return paths, broad


def _status(cwd: str) -> list[str] | None:
    """Every path git reports changed or untracked in the worktree; None if git cannot tell."""
    p = subprocess.run(["git", "-C", cwd or ".", "-c", "core.quotepath=off", "status", "--porcelain=v1", "-z", "-uall"],
                       capture_output=True)
    if p.returncode:
        return None
    # task-0267: NUL-separated and unquoted, so a space, a quote or a non-ASCII character is part of the name; a rename
    # or copy entry ("R  new\0old") is followed by its source, which is skipped as the arrow form's left side was
    out, items = [], p.stdout.decode("utf-8", "surrogateescape").split("\0")
    i = 0
    while i < len(items):
        it = items[i]
        if len(it) > 3:
            out.append(it[3:])
            i += 1 if it[0] in "RC" or it[1] in "RC" else 0
        i += 1
    return out


def _committed(cwd: str, cmd: str) -> list[str] | None:
    """The paths the commit carries: staged, plus tracked changes under -a/--all; None if git cannot tell."""
    runs = [["diff", "--cached", "--name-only"]]
    if re.search(r"\s(?:--all|-[a-zA-Z]*a[a-zA-Z]*)(?:\s|$)", cmd.split("commit", 1)[-1]):
        runs.append(["diff", "--name-only"])
    out: list[str] = []
    for r in runs:
        p = subprocess.run(["git", "-C", cwd or ".", "-c", "core.quotepath=off", *r, "-z"], capture_output=True)
        if p.returncode:
            return None
        out += [n for n in p.stdout.decode("utf-8", "surrogateescape").split("\0") if n]   # task-0267: never split on a space
    return out


def _spec(paths, globs) -> bool:
    return any(fnmatch.fnmatch(p, g) or fnmatch.fnmatch(Path(p).name, g) for p in paths for g in globs)


def _stages_spec(cwd: str, calls, globs) -> bool | None:
    """Whether the command itself stages or commits a spec file, read before it runs (P2): a path it names that
    is one, or a folder, a glob or ``.`` that holds a changed one, or broad staging (-A, -u, -a) while one is
    changed. None when git cannot tell (the caller fails closed)."""
    changed = None
    for sub, args in calls:
        if sub not in ("add", "stage", "commit", "rm", "mv"):
            continue
        paths, broad = _paths_named(args)
        if _spec(paths, globs):
            return True
        wide = [p for p in paths if p in (".", ":/", "*") or any(c in p for c in "*?[") or Path(cwd or ".", p).is_dir()]
        if broad or wide:
            if changed is None:
                changed = _status(cwd)
                if changed is None:
                    return None
            if broad and _spec(changed, globs):
                return True
            for w in wide:
                base = "" if w in (".", ":/") else w.rstrip("/")
                under = [c for c in changed if not base or c == base or c.startswith(base + "/") or fnmatch.fnmatch(c, w)]
                if _spec(under, globs):
                    return True
    return False


def _field(event: dict, key: str, kind: type, default):
    """``event[key]`` when it is a ``kind``, ``default`` when it is absent or null; any other type is refused
    (task-0268, task-0200 P8: what cannot be read is never allowed)."""
    v = event.get(key)
    if v is None:
        return default
    if not isinstance(v, kind):
        raise ValueError(f"{key} is {type(v).__name__}, not {'an object' if kind is dict else 'a string'}")
    return v


def _bash(event: dict) -> tuple[str, str]:
    """A Bash event's command and cwd, each a string, or ValueError."""
    ti = _field(event, "tool_input", dict, {})
    cmd = ti.get("command")
    if cmd is not None and not isinstance(cmd, str):
        raise ValueError(f"tool_input.command is {type(cmd).__name__}, not a string")
    return cmd or "", _field(event, "cwd", str, "")


def _commit_stage(cmd: str, cwd: str, calls, spec_globs: list[str]) -> str | None:
    """``spec`` when the commit carries a spec file, staged before or by the command itself (P2), or when git
    cannot tell (fail closed); None otherwise."""
    paths = _committed(cwd, cmd)
    if paths is None or _spec(paths, spec_globs):
        return "spec"
    named = _stages_spec(cwd, calls, spec_globs)
    return "spec" if named is None or named else None


def _by_name(cmd: str) -> str | None:
    """What a command that cannot be read names, failing closed: ``push``, else ``spec`` for a commit."""
    low = cmd.lower()
    return "push" if "push" in low else "spec" if "commit" in low else None


def transition(event: dict, spec_globs: list[str]) -> str | None:
    """The stage a tool call moves to, or None: not a transition, the hook has no decision."""
    tool = event.get("tool_name")
    if not isinstance(tool, str):   # task-0268 (task-0200 P8): what cannot be read is refused, never allowed
        raise ValueError(f"tool_name is {type(tool).__name__}, not a string")
    if tool == "ExitPlanMode":
        return "plan"
    if tool != "Bash":
        return None
    cmd, cwd = _bash(event)
    inline: dict[str, str] = {}
    calls = git_calls(cmd, aliases=inline)
    if calls is None:   # a command that cannot be read: by pattern, failing closed on a commit
        return "push" if _git(cmd, "push") else "spec" if _git(cmd, "commit") else None
    if any(sub != "$" for sub, _ in calls):   # an alias, inline (git -c alias.X=push X) or configured, is what it runs
        calls = _expand(calls, {**_repo_aliases(cwd), **inline})
    subs = {sub for sub, _ in calls}
    if "$" in subs and _by_name(cmd):   # a variable stands where git or its subcommand would: fail closed
        return _by_name(cmd)
    if "push" in subs:
        return "push"
    return _commit_stage(cmd, cwd, calls, spec_globs) if "commit" in subs else None


# --- the gate ----------------------------------------------------------------------------------

def _knowgov(arg: str | None) -> Path | None:
    """The first of --knowgov, KG_HOME and this file's checkout that is named; None if it holds no gate."""
    c = Path(arg or os.environ.get("KG_HOME") or Path(__file__).resolve().parents[3]).expanduser().resolve()   # task-0268:
    return c if (c / "instance" / "ci" / "knowgov-gate.sh").is_file() else None   # absolute, since the gate runs from the instance


BAR_KINDS = ("attestation", "lapsed")   # task-0330 H1: the findings the bar rests on, shown below the blockers


def _shown(rep: dict) -> list[dict]:
    """The findings the assistant reads, six at most: the blockers and criticals (every finding when there are none), then the
    attestation and lapsed findings the verdict rests on below them, a slot each (two at most) held for those that exist."""
    fs = rep.get("findings") or []
    worst = [f for f in fs if f.get("severity") in ("blocker", "critical")]
    if not worst:
        return fs[:6]
    bar = []   # H7: one slot per kind, attestation first, so lapses cannot crowd the attestation cause out
    for kind in BAR_KINDS:
        bar += [f for f in fs if f.get("kind") == kind and f not in worst][:1]
    return worst[:6 - len(bar)] + bar


def _route_for(rep: dict) -> str:
    """The closing route follows the cause (task-0332): a key blocker (or any blocker but the bar itself) keeps the
    questionnaire's; when the only blocker is the bar (kind ``task``, the gate never raises an attestation above major) and an
    attestation finding is shown, it is the attestation route."""
    shown = _shown(rep)
    blockers = {f.get("kind") for f in shown if f.get("severity") in ("blocker", "critical")} - {"task"}
    if not blockers - {"attestation"} and any(f.get("kind") == "attestation" for f in shown) and any(f.get("kind") == "lapsed" for f in shown):
        return ATTESTATION_ROUTE + " A lapsed review is renewed by its reviewer's new dated ruling (harness/capture.py review)."
    return ATTESTATION_ROUTE if not blockers - {"attestation"} and any(f.get("kind") == "attestation" for f in shown) else ROUTE


def _summary(rep: dict) -> str:
    head = (f"{rep.get('verdict')} on {rep.get('subject')} {rep.get('scenario')}, task {rep.get('task')}, "
            f"as of {rep.get('as_of')}, threshold {rep.get('threshold')}")
    worst = _shown(rep)
    lines = [f"  {f.get('severity')} {f.get('kind')}" + (f" {f['key']}" if f.get("key") else "") + f": {f.get('message')}"
             + (f" (owner {f.get('owner') or 'none in the register map'}"
                + (f"; closed by {f.get('closer') or 'no unit of the register'}" if "closer" in f else "") + ")"
                if "owner" in f else "")
             for f in worst]
    routes = sorted({f["route"] for f in worst if f.get("route")})   # task-0102: each owner's questionnaire
    lines += [f"  route: {r}" for r in routes]
    pool = [f for f in rep.get("findings") or [] if f.get("severity") in ("blocker", "critical")] or (rep.get("findings") or [])
    more = len(pool) - len([f for f in worst if f in pool])
    return "\n".join([head, *lines] + ([f"  ... and {more} more"] if more > 0 else []))


def instance_register(env: dict, inst: Path) -> str:
    """The register the gate reads: ``KG_REGISTER`` when it names one, else ``<instance>/register``, the instance's
    own, never the public one knowgov carries (task-0334, decision-0039 §3.1)."""
    return env.get("KG_REGISTER") or str(Path(inst).resolve() / "register")


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
        env["KG_REGISTER"] = instance_register(env, inst)
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
        return decide(p.returncode, check=check, finding=_summary(rep), route=_route_for(rep), advisory=advisory)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


def _per_stage(task_for: list[str], advisory: bool) -> tuple[dict[str, str], Decision | None]:
    """--task-for's classes by stage, or the decision that refuses them: a bad entry, or a stage named twice
    (task-0268: two classes for one stage is a configuration that cannot be read)."""
    per: dict[str, str] = {}
    for s in task_for:
        stage, _, cls = s.partition("=")
        if stage not in STAGES or not cls or cls == FREE_KEYS:
            return per, decide(CANNOT_RUN, check="knowgov hook", unavailable=f"bad --task-for {s!r} (stages: {', '.join(STAGES)})",
                               advisory=advisory)
        if stage in per:
            return per, refuse("knowgov hook", f"--task-for names the stage {stage} twice ({per[stage]} and {cls})")
        per[stage] = cls
    return per, None


def _seconds(v: str) -> float:
    """--timeout: a finite number of seconds above 0 (task-0268); anything else is argparse's usage error, exit 2."""
    import math
    try:
        f = float(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{v!r} is not a number of seconds") from None
    if not math.isfinite(f) or f <= 0:
        raise argparse.ArgumentTypeError(f"{v!r}: the timeout is a finite number of seconds above 0")
    return f


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
    g.add_argument("--timeout", type=_seconds, default=540, help="seconds for the gate, under the hook's own timeout (default 540)")
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
    per, bad = _per_stage(a.task_for, a.advisory)
    if bad:
        return emit(bad)
    try:
        stage = transition(ev, a.spec or ["spec.md"])
    except ValueError as e:   # task-0268: a field that is not what the event's shape says blocks in every profile
        return emit(refuse("knowgov hook", f"unreadable hook event: {e}"))
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

"""task-0218: the prose gate. Every ``--flag`` the reverse-engineering guide and its pre-registration
template name is an option of a knowgov script, and every script they name exists.

A plain-English walkthrough has no golden behind it, so this is what keeps it from lying after an option
is renamed. Two rules:

- on a command (a fenced line or an inline code span), each flag after a script's path, up to the next
  ``&&``, ``|`` or ``;``, is an option of that script;
- anywhere else, each flag is an option of one of the scripts the document names.

A script's options are read from its source: every string literal starting ``--`` passed to an
``add_argument`` call, so nothing is imported and the stdlib runner needs no harness package. Flags of
another tool that a document names on purpose are listed in FOREIGN, with their owner, so a typo cannot
hide behind the exemption.

Plain assert functions, stdlib only, for tests/run_tests.py.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("docs/reverse-engineering.md", "docs/reverse-engineering-preregistration.md")
FOREIGN = {"--features": "pumllint trace"}   # docs/reverse-engineering.md step 4: not in preload_check yet (task-0217)
FLAG = re.compile(r"(?<![\w-])--[a-z][a-z0-9-]*")
SCRIPT = re.compile(r"(?<![\w./-])((?:harness|tools|demo/tools|instance/ci)(?:/[\w-]+)*/[\w-]+\.py)(?![\w/])")
SPAN = re.compile(r"`([^`\n]+)`")
SEPARATOR = re.compile(r"&&|\||;")


def options(script: str) -> set[str]:
    """The long options a script's parsers declare, read from its source."""
    tree = ast.parse((ROOT / script).read_text(encoding="utf-8"), filename=script)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            out |= {a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)
                    and a.value.startswith("--")}
    return out


def commands(text: str) -> list[str]:
    """Every line of a fenced block (a trailing backslash joins the next) and every inline code span."""
    out: list[str] = []
    fenced = False
    pending = ""
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            joined = line.rstrip().endswith("\\")
            pending += line.rstrip().rstrip("\\") + " " if joined else line
            if not joined:
                out.append(pending)
                pending = ""
        else:
            out += SPAN.findall(line)
    return out


def test_the_probe_reads_options():
    assert {"--previous", "--baseline", "--fail-on"} <= options("tools/preload_check.py")
    assert {"--instance", "--ledger", "--changed"} <= options("harness/trace.py")   # parsers built in a loop
    assert {"--task", "--out", "--scenario"} <= options("harness/capture.py")      # subcommands
    got = commands("a `x --y` b\n```bash\npython tools/a.py \\\n  --z\n```\n")
    assert got[0] == "x --y" and len(got) == 2 and got[1].split() == ["python", "tools/a.py", "--z"], got


def test_every_script_named_exists():
    for doc in DOCS:
        text = (ROOT / doc).read_text(encoding="utf-8")
        for script in sorted(set(SCRIPT.findall(text))):
            assert (ROOT / script).is_file(), f"{doc} names {script}, which does not exist"


def test_a_flag_on_a_command_is_an_option_of_its_script():
    for doc in DOCS:
        for cmd in commands((ROOT / doc).read_text(encoding="utf-8")):
            for m in SCRIPT.finditer(cmd):
                tail = SEPARATOR.split(cmd[m.end():], maxsplit=1)[0]
                ours = options(m.group(1))
                for flag in FLAG.findall(tail):
                    assert flag in ours, f"{doc}: `{cmd.strip()}` passes {flag}, which {m.group(1)} does not accept"


def test_every_flag_is_an_option_of_a_script_the_document_names_or_a_declared_foreign_one():
    for doc in DOCS:
        text = (ROOT / doc).read_text(encoding="utf-8")
        ours = set().union(*(options(s) for s in set(SCRIPT.findall(text)))) if SCRIPT.search(text) else set()
        for flag in sorted(set(FLAG.findall(text))):
            assert flag in ours or flag in FOREIGN, \
                f"{doc} mentions {flag}, which no script it names accepts and FOREIGN does not list"


def test_every_declared_foreign_flag_is_still_mentioned():
    """An exemption nothing uses any more is a stale allowlist entry."""
    text = "".join((ROOT / d).read_text(encoding="utf-8") for d in DOCS)
    for flag in FOREIGN:
        assert flag in FLAG.findall(text), \
            f"{flag} is exempted but no longer mentioned: drop it from FOREIGN"

"""task-0218 (decision-0018 points 1 and 2): the adopter's guide to the reverse-engineering process,
docs/reverse-engineering.md, and its pre-registration template, docs/reverse-engineering-preregistration.md.
A prose walkthrough has no golden behind it, so this is its gate: every option a command in the guide passes,
and every option its prose names, is one of a real program's; every repository path it names exists; the guide
walks the eight steps of doc-0032 with a tool, a record and a place for each; and the template carries every
field step 1 names, filled in for J-F's first run. Standard library only: each program's own --help."""
from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "reverse-engineering.md"
TEMPLATE = ROOT / "docs" / "reverse-engineering-preregistration.md"
SUBCOMMANDS = {"harness/capture.py", "harness/trace.py"}   # programs whose options are their subcommand's
# A program outside this repository the guide names an option of: the option, and what says it exists.
EXTERNAL = {"--features": "pumllint trace --features (pumllint's requirements-as-code gate; its RULES.md and README)"}
STEPS = ("Scope at a named commit", "Reverse-engineer the code into a kit", "Gather the existing artefacts",
         "Lint both", "Load as a subject", "Address the gaps", "Optionally, rebuild and grade", "Re-run on change")
FIELDS = ("The code base and its commit", "The lane", "The roles", "What the extraction role may read",
          "What the recreation role receives", "The bars", "The bounded inventories", "Expectations",
          "What this run never does", "Frozen")


def _help(argv: list[str]) -> set[str]:
    out = subprocess.run([sys.executable, *argv, "--help"], capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert out.returncode == 0, (argv, out.stderr[-500:])
    return set(re.findall(r"(?<![\w-])(--?[A-Za-z][\w-]*)", out.stdout))


def _commands(text: str) -> list[list[str]]:
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    return [shlex.split(line) for b in blocks for line in b.strip().splitlines() if line.strip()]


def test_every_option_a_command_passes_is_one_its_program_accepts():
    text = GUIDE.read_text(encoding="utf-8")
    seen = set()
    for argv in _commands(text):
        i = 0
        while i < len(argv) and re.fullmatch(r"[A-Z_]+=\S*", argv[i]):
            i += 1                                   # an environment assignment before the program
        assert argv[i] in ("python", "python3"), argv
        prog = [argv[i + 1]]
        assert (ROOT / prog[0]).exists(), prog
        rest = argv[i + 2:]
        if prog[0] in SUBCOMMANDS:
            prog, rest = prog + rest[:1], rest[1:]
        allowed = _help(prog)
        for tok in rest:
            if tok.startswith("-"):
                assert tok in allowed, f"{' '.join(prog)} has no option {tok} (docs/reverse-engineering.md)"
                seen.add((" ".join(prog), tok))
    assert ("harness/gate_cli.py", "--baseline") in seen and ("tools/preload_check.py", "--layout") in seen, seen


def test_every_option_the_prose_names_is_a_real_one():
    text = GUIDE.read_text(encoding="utf-8")
    prose = re.sub(r"```bash\n.*?```", "", text, flags=re.S)
    named = set(re.findall(r"`[^`]*?(--[a-z][\w-]*)[^`]*`", prose))
    progs = {tuple(a[a.index(next(t for t in a if t in ("python", "python3"))) + 1:][:2]) for a in _commands(text)}
    known = set().union(*(_help([p[0], p[1]] if p[0] in SUBCOMMANDS else [p[0]]) for p in progs))
    for opt in sorted(named):
        assert opt in known or opt in EXTERNAL, f"the guide's prose names {opt}, which no program it uses accepts"


def test_every_repository_path_the_guide_and_the_template_name_exists():
    for doc in (GUIDE, TEMPLATE):
        for path in re.findall(r"`((?:docs|subjects|instance|tools|harness|backlog)/[\w./-]*)`", doc.read_text(encoding="utf-8")):
            if "<" in path or path.startswith(("docs/recreate-experiment.md",)):
                continue   # a placeholder, or pumllint's own record, cited by path in pumllint
            assert (ROOT / path.rstrip("/")).exists(), f"{doc.name} names {path}, which this repository does not hold"


def test_the_guide_walks_the_eight_steps_each_with_its_tool_record_and_place():
    text = GUIDE.read_text(encoding="utf-8")
    heads = re.findall(r"^### Step (\d)\. (.+)$", text, re.M)
    assert [int(n) for n, _ in heads] == list(range(1, 9)), heads
    for (n, title), want in zip(heads, STEPS):
        assert title.startswith(want), (n, title)
    for n in range(1, 9):
        body = text.split(f"### Step {n}.", 1)[1].split("### Step", 1)[0].split("\n## ", 1)[0]
        assert "**Record:**" in body and "**Where:**" in body, f"step {n} names no record or no place for it"
    for needle in ("Keep the roles apart", "Fix the bars first", "nothing to divide by", "observed", "inferred", "intended"):
        assert needle in text, needle


def test_the_template_carries_every_field_step_1_names_with_j_fs_first_run_as_the_example():
    text = TEMPLATE.read_text(encoding="utf-8")
    template, example = text.split("## Worked example", 1)
    for doc in (template, example):
        heads = re.findall(r"^### \d+\. (.+)$", doc, re.M)
        assert tuple(heads) == FIELDS, heads
    for needle in ("clean room", "bundle", "gates", "reported", "never a percentage", "digest"):
        assert needle in template.lower(), needle
    for needle in ("recreate_experiment/PREREGISTRATION.md", "8f6d6b0", "5c1fa55", "157", "158", "jef_data_load"):
        assert needle in example, needle
    assert "docs/reverse-engineering-preregistration.md" in GUIDE.read_text(encoding="utf-8")

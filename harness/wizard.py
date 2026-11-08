"""The subject wizard as procedure: one text, two carriers (task-0148; doc-0018 candidate 4, doc-0021 §8).

    python harness/wizard.py --write-skill      # regenerate the skill's reference part from instance/kinds.toml
    python harness/wizard.py --check            # exit 1 if the skill's reference part is stale

The text is ``instance/ci/claude/skills/knowgov-onboard/SKILL.md``, a Claude Code skill an instance
copies into its ``.claude/skills/``. Its body is cut into parts (``<!-- part:NAME -->`` ...
``<!-- /part -->``). The reader (``harness/mcp_server.py``) serves two MCP prompts built from those
parts verbatim, so the skill and the prompts never drift:

    new_subject   <id> <task>      intro, never, stop, new_subject, exits, reference
    add_artefact  <subject> [file] intro, never, stop, add_artefact, reference

Each argument is one token (Claude Code splits a prompt's arguments on whitespace); everything else
is asked in chat. The reference part, the kinds table and what each mapper reads, is generated here
from ``instance/kinds.toml`` and ``instance/mappers.toml`` and written into the skill, so a client that shows
prompts and not resources still has it (doc-0021 §8 item 12). A prompt's text only reads: it asks the
client to write with its own file tools on a branch, ending in a pull request (decision-0008), and
carries the never-list and the stop condition. No elicitation: the questions are open, and chat
answers them (doc-0021 §8). Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "instance" / "ci" / "claude" / "skills" / "knowgov-onboard" / "SKILL.md"
KINDS = ROOT / "instance" / "kinds.toml"
PART = re.compile(r"<!-- part:(\w+) -->\n(.*?)<!-- /part -->", re.S)
TOKEN = re.compile(r"[a-z0-9][a-z0-9_]{0,62}")
FILE_TOKEN = re.compile(r"[^\s]{1,240}")

MAPPERS_TABLE = ROOT / "instance" / "mappers.toml"   # what each mapper reads, in an adopter's words
MAPPERS = {m: row["reads"] for m, row in tomllib.loads(MAPPERS_TABLE.read_text(encoding="utf-8")).get("mapper", {}).items()}

PROMPTS = {
    "new_subject": {"parts": ("intro", "never", "stop", "new_subject", "exits", "reference"),
                    "title": "Scaffold a new knowgov subject",
                    "description": "Guide the person through a new subject on a branch of the instance repository: the "
                                   "register first, the documents into their kinds, the manifest, the task's keys, the "
                                   "attestation left to a person, the owners' questionnaires; checked after every write, "
                                   "ending in a pull request a person reviews. Writes nothing through knowgov.",
                    "arguments": [{"name": "id", "description": "the subject's id, one word: lower case, digits, _", "required": True},
                                  {"name": "task", "description": "the task class, one word (codegen, design, ...)", "required": True}]},
    "add_artefact": {"parts": ("intro", "never", "stop", "add_artefact", "reference"),
                     "title": "Add a document to a knowgov subject",
                     "description": "Place one document a person of record wrote into its kind, pick its mapper by the "
                                    "check's yield, add its [[artefact]] and check again; never edits the document, never "
                                    "attests. Ends in a pull request.",
                     "arguments": [{"name": "subject", "description": "the subject's id, one word", "required": True},
                                   {"name": "file", "description": "the document's path in the instance, one token (optional: asked in chat)", "required": False}]},
}


class PromptError(ValueError):
    """A prompt that cannot be given: an unknown name, a missing or malformed argument."""


def kinds() -> list[dict]:
    return tomllib.loads(KINDS.read_text(encoding="utf-8")).get("kind", [])


def reference() -> str:
    """The reference part's body: the kinds table and each mapper's input convention."""
    rows = ["| Kind folder (`artefacts/<kind>/`) | Mappers | Form check |", "|---|---|---|"]
    for k in kinds():
        lint = k.get("lint") or {}
        maps = ", ".join(f"`{m}`" for m in k.get("mappers", [])) or "none: reported ABSENT"
        rows.append(f"| `{k['folder']}` ({k['row']}) | {maps} | {lint.get('runs') or 'unchecked here'} |")
    lines = ["What each mapper reads:", ""] + [f"- `{m}`: {MAPPERS[m]}" for m in sorted(MAPPERS)]
    import formats   # task-0174, decision-0023: the versions a new file is written at, from the one table that holds them
    fmt = ["The format versions a new file is written at (instance/README.md, \"Format versions\"):", "",
           f"- `subject.toml`: `[format] version = {formats.CURRENT[formats.SUBJECT]}`, covering the subject root's "
           "`scenarios.toml`, `plants.toml`, `queries.toml` and register map; keep it as copied from `subjects/minimal/`",
           f"- `code_map.toml` and `connectors.toml`: a top-level `format = {formats.CURRENT[formats.CODE_MAP]}`",
           "- captures and review files: never written here; `harness/capture.py` stamps them"]
    return "\n".join(rows) + "\n\n" + "\n".join(lines) + "\n\n" + "\n".join(fmt) + "\n"


REF_HEAD = "## Reference: the kinds and what each mapper reads\n\n<!-- generated by harness/wizard.py from instance/kinds.toml and instance/mappers.toml; tests/test_wizard.py holds it equal -->\n"


def parts(text: str | None = None) -> dict[str, str]:
    text = SKILL.read_text(encoding="utf-8") if text is None else text
    return {m.group(1): m.group(2).strip("\n") + "\n" for m in PART.finditer(text)}


def skill_text() -> str:
    """The skill as it should stand: its reference part regenerated, every other byte unchanged."""
    text = SKILL.read_text(encoding="utf-8")
    body = REF_HEAD + reference()
    return PART.sub(lambda m: f"<!-- part:reference -->\n{body}<!-- /part -->" if m.group(1) == "reference" else m.group(0), text)


def listing() -> list[dict]:
    return [{"name": n, "title": p["title"], "description": p["description"], "arguments": p["arguments"]}
            for n, p in PROMPTS.items()]


def get(name, arguments) -> dict:
    """prompts/get's result: one user message, the parts verbatim after a line naming the arguments."""
    if name not in PROMPTS:
        raise PromptError(f"unknown prompt {name!r}; the prompts are {', '.join(PROMPTS)}")
    p = PROMPTS[name]
    arguments = arguments or {}
    if not isinstance(arguments, dict) or not all(isinstance(v, str) for v in arguments.values()):
        raise PromptError("arguments must be an object of strings")
    known = {a["name"] for a in p["arguments"]}
    extra = sorted(set(arguments) - known)
    if extra:
        raise PromptError(f"{name} takes {', '.join(sorted(known))}; not {', '.join(extra)}")
    named = []
    for a in p["arguments"]:
        v = arguments.get(a["name"], "").strip()
        if not v:
            if a["required"]:
                raise PromptError(f"{name} needs {a['name']}: {a['description']}")
            continue
        if not (FILE_TOKEN if a["name"] == "file" else TOKEN).fullmatch(v):
            raise PromptError(f"{a['name']} {v!r} is not one token: {a['description']}")
        named.append(f"{a['name']} `{v}`")
    have = parts()
    head = f"/{name} " + ("with " + ", ".join(named) if named else "with no arguments") + ".\n\n"
    text = head + "\n".join(have[k] for k in p["parts"])
    return {"description": p["description"], "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write-skill", action="store_true", help="regenerate the skill's reference part")
    g.add_argument("--check", action="store_true", help="exit 1 if the skill's reference part is stale")
    a = ap.parse_args(argv)
    want = skill_text()
    if a.write_skill:
        SKILL.write_text(want, encoding="utf-8")
        return 0
    if want != SKILL.read_text(encoding="utf-8"):
        print(f"{SKILL.relative_to(ROOT)}: the reference part is stale; run python harness/wizard.py --write-skill", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

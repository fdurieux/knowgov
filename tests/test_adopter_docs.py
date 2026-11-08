"""task-0230 (doc-0028 G9-9, P2): the adopter-facing docs held against the code. A prose walkthrough has no
golden behind it, so this is its gate, in the shape of pumllint's tests/test_docs_flags.py and wider:

- every ``--flag`` the docs name is an option of a parser in this repository, or a foreign program's,
  listed with its owner in FOREIGN_FLAGS;
- every option a fenced command passes to one of this repository's programs is one that program declares;
- every ``KG_*`` setting the docs name is read somewhere in the code (decision-0016 point 3: the settings
  instance/README.md or docs/security.md documents are contracts at 1.0, so a name no code reads is a
  stale contract);
- every repository path and relative link the docs name exists, and every ``tests/x.py::test_y`` they cite
  is a test of that file;
- every ``/api/...`` route the docs name is one the page serves.

A flag or a path that belongs to another program or repository is listed with its owner, so a typo cannot
hide behind the exemption, and an exemption nothing uses any more fails. Standard library only; the code is
read as text, nothing is imported or run."""
from __future__ import annotations

import re
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("README.md", "demo/README.md", "instance/README.md", "subjects/README.md", "docs/guide.md",
        "docs/security.md", "docs/reverse-engineering.md", "docs/reverse-engineering-preregistration.md",
        "docs/lighthouse-evaluation.md")
CODE_DIRS = ("harness", "tools", "demo/tools", "demo/app", "instance")
# The vendored register's own tools run from this repository too (`demo/register/tools/impact.py --from ...`):
# their options count as ours, though no KG_* is read there.
PARSER_DIRS = CODE_DIRS + ("demo/register/tools",)
CODE_SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".toml", ".js", ".html", ".json"}
CODE_FILES_EXTRA = ("demo/Dockerfile", "demo/docker-compose.yml", "demo/docker-compose.override.yml",
                    "demo/docker-compose.instance.yml")
SKIP_PARTS = {"vendor", "__pycache__", "node_modules", "fixtures"}

# Flags of programs outside this repository that the docs name on purpose: the flag, and whose it is.
FOREIGN_FLAGS: dict[str, str] = {
    "--always": "git describe", "--tags": "git describe", "--depth": "git clone", "--ff-only": "git pull",
    "--build": "docker compose up", "--force-recreate": "docker compose up", "--no-deps": "docker compose run",
    "--wait": "docker compose up", "--wait-timeout": "docker compose up", "--profile": "docker compose",
    "--project-directory": "docker compose", "--rm": "docker compose run", "--tail": "docker compose logs",
    "--filter": "docker ps", "--install": "xcode-select (macOS)", "--apple-use-keychain": "ssh-add (macOS)",
    "--features": "pumllint trace (pumllint's requirements-as-code check)",
}
# Paths the docs name on purpose that are not this repository's files: the path, and whose it is.
FOREIGN_PATHS: dict[str, str] = {
    "docs/neo4j-governed-knowledge-evaluation.md": "pumllint: the proof of concept's evaluation",
    "docs/recreate-experiment.md": "pumllint: the recreation experiment",
    "tools/reconcile.py": "ieam-register: the register's own tool, run in its checkout (vendored here under demo/register/)",
    "tools/call": "the MCP protocol: a JSON-RPC method name, not a file",
}

FLAG = re.compile(r"(?<![\w-])--[a-z][a-z0-9-]*")
KG = re.compile(r"\bKG_[A-Z0-9_]*[A-Z0-9_]")
TOP = ("harness/", "tools/", "demo/", "instance/", "subjects/", "docs/", "tests/", "backlog/", ".github/")
ADD_ARG = re.compile(r"add_argument\(\s*((?:[rbf]?[\"'][^\"']+[\"']\s*,\s*)*[rbf]?[\"'][^\"']+[\"'])")


def _docs() -> dict[str, str]:
    return {d: (ROOT / d).read_text(encoding="utf-8") for d in DOCS}


def _code_files() -> list[Path]:
    out = []
    for d in CODE_DIRS:
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file() and p.suffix in CODE_SUFFIXES and not (set(p.relative_to(ROOT).parts) & SKIP_PARTS):
                out.append(p)
    return out + [ROOT / f for f in CODE_FILES_EXTRA if (ROOT / f).exists()]


def _options(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {o for m in ADD_ARG.finditer(text) for o in re.findall(r"[\"'](--?[A-Za-z][\w-]*)[\"']", m.group(1))}


def _all_options() -> set[str]:
    files = [p for d in PARSER_DIRS for p in (ROOT / d).rglob("*.py") if not (set(p.relative_to(ROOT).parts) & SKIP_PARTS)]
    return set().union(*(_options(p) for p in files))


def _blocks(text: str) -> list[str]:
    return [b.replace("\\\n", " ") for lang, b in re.findall(r"```(\w*)\n(.*?)```", text, re.S)
            if lang in ("bash", "sh", "shell", "")]


def _prose(text: str) -> str:
    return re.sub(r"```\w*\n.*?```", "", text, flags=re.S)


def test_every_flag_the_docs_name_is_an_option_of_ours_or_a_named_foreign_one():
    ours = _all_options()
    assert {"--fail-on", "--baseline", "--as-of", "--layout"} <= ours, "the probe reads the parsers"
    assert not ours & set(FOREIGN_FLAGS), f"a foreign flag is now one of ours: {sorted(ours & set(FOREIGN_FLAGS))}"
    bad = [f"{d}: {flag}" for d, text in _docs().items() for flag in sorted({m.group() for m in FLAG.finditer(text)})
           if flag not in ours and flag not in FOREIGN_FLAGS]
    assert not bad, f"named in the docs, accepted by no parser here and not listed as foreign: {bad}"


def test_every_listed_foreign_flag_and_path_is_still_named():
    text = "".join(_docs().values())
    stale = [f for f in list(FOREIGN_FLAGS) + list(FOREIGN_PATHS) if f not in text]
    assert not stale, f"listed as foreign but no doc names it any more, drop it: {stale}"


def _program(token: str, cwd: str) -> Path | None:
    for base in (ROOT / cwd, ROOT):
        p = (base / token).resolve()
        if p.is_file() and ROOT in p.parents:
            return p
    return None


def test_every_option_a_fenced_command_passes_to_our_programs_is_one_it_declares():
    bad, seen = [], 0
    for d, text in _docs().items():
        for block in _blocks(text):
            cwd = "."
            for line in block.splitlines():
                line = line.split(" #", 1)[0].strip()
                if not line or line.startswith("#"):
                    continue
                for seg in re.split(r"\s*(?:&&|\|\||;|\|)\s*", line):
                    try:
                        argv = shlex.split(seg)
                    except ValueError:
                        continue
                    if argv[:1] == ["cd"] and len(argv) == 2:
                        cwd = str(Path(cwd) / argv[1])
                        continue
                    for i, tok in enumerate(argv[:-1]):
                        if tok in ("python", "python3") and argv[i + 1].endswith(".py"):
                            prog = _program(argv[i + 1], cwd)
                            if prog is None:
                                bad.append(f"{d}: {argv[i + 1]} is no program here (from {cwd})")
                                break
                            declared = _options(prog)
                            for opt in argv[i + 2:]:
                                if opt.startswith("-") and opt not in ("-", "--"):
                                    seen += 1
                                    name = opt.split("=", 1)[0]
                                    if declared and name not in declared:
                                        bad.append(f"{d}: {prog.relative_to(ROOT).as_posix()} declares no {name}")
                            break
    assert seen > 20, "the probe reads the commands"
    assert not bad, bad


def _code_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in _code_files())


def test_every_kg_setting_the_docs_name_is_read_in_the_code():
    code = _code_text()
    names = set(KG.findall(code))
    assert {"KG_STORE", "KG_SUBJECT", "KG_REGISTER"} <= names, "the probe reads the code"
    bad = []
    for d, text in _docs().items():
        for n in sorted(set(KG.findall(text))):
            known = any(c.startswith(n) for c in names) if n.endswith("_") else n in names
            if not known:
                bad.append(f"{d}: {n}")
    assert not bad, f"a KG_* setting the docs name and no code reads: {bad}"


def _test_ref_ok(ref: str) -> bool:
    path, _, name = ref.partition("::")
    p = ROOT / path
    return p.is_file() and (not name or re.search(rf"(?m)^def {re.escape(name)}\(", p.read_text(encoding="utf-8")) is not None)


def _named_paths(d: str, text: str) -> list[tuple[str, Path | None]]:
    """(as written, resolved) for each repository path the doc names: code spans under a top-level directory,
    and relative links, resolved from the doc's own folder. A placeholder (<id>, {x}, *, …) is not a path."""
    out = []
    for m in re.finditer(r"`([^`\n]+)`", text):
        s = m.group(1).strip().rstrip(".,:;)")
        for tok in s.split():
            if tok.startswith(TOP) and not re.search(r"[<>{}$*…]|\.\.\.", tok):
                out.append((tok, None))
    for m in re.finditer(r"\]\(([^)\s]+)\)", text):
        target = m.group(1)
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        rel = target.split("#", 1)[0]
        if rel:
            out.append((target, (ROOT / d).parent / rel))
    return out


def test_every_repository_path_and_link_the_docs_name_exists():
    bad = []
    for d, text in _docs().items():
        for written, resolved in _named_paths(d, text):
            if resolved is not None:
                if not resolved.exists():
                    bad.append(f"{d}: link {written}")
                continue
            path = written.split("::", 1)[0].split(":", 1)[0].split("#", 1)[0].rstrip("/")
            if "::" in written:
                if not _test_ref_ok(written):
                    bad.append(f"{d}: {written}")
                continue
            if written in FOREIGN_PATHS or path in FOREIGN_PATHS:
                continue
            if not any(p.exists() or any(p.parent.glob(p.name + "*"))
                       for p in (ROOT / path, (ROOT / d).parent / path)):   # from the root, or from the doc's folder
                bad.append(f"{d}: {written}")
    assert not bad, f"named in the docs and not in the repository: {bad}"


def _routes() -> list[tuple[str, tuple[str, ...], int | None]]:
    """The page's routes, read from demo/app/server.py: ('exact' or 'prefix', literal segments, length)."""
    text = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"parts == \[([^\]]*)\]", text):
        out.append(("exact", tuple(re.findall(r"\"([^\"]*)\"", m.group(1))), None))
    for m in re.finditer(r"parts\[:\d\] == \[([^\]]*)\]([^:\n]*)", text):
        n = re.search(r"len\(parts\) == (\d+)", m.group(2))
        out.append(("prefix", tuple(re.findall(r"\"([^\"]*)\"", m.group(1))), int(n.group(1)) if n else None))
    return out


def _route_ok(segs: list[str], routes) -> bool:
    def same(lit: str, seg: str) -> bool:
        return lit == seg or bool(re.fullmatch(r"[<{:].*|[A-Z]\d*|\w*…", seg))
    for kind, lits, n in routes:
        if kind == "exact" and len(segs) == len(lits) and all(same(a, b) for a, b in zip(lits, segs)):
            return True
        if kind == "prefix" and len(segs) >= len(lits) and all(a == b for a, b in zip(lits, segs)) and (n is None or len(segs) == n):
            return True
    return False


def test_every_page_route_the_docs_name_is_one_the_page_serves():
    routes = _routes()
    assert ("exact", ("api", "subjects"), None) in routes, "the probe reads the routes"
    bad = []
    for d, text in _docs().items():
        for m in re.finditer(r"(?<![\w.])/(api/[\w/<>{}:.…-]*\w[>}]?|health)\b", text):
            segs = [s for s in m.group(1).split("?")[0].split("/") if s]
            if not _route_ok(segs, routes):
                bad.append(f"{d}: /{m.group(1)}")
    assert not bad, f"a route the docs name that the page does not serve: {sorted(set(bad))}"

"""task-0275 (decision-0033 choice 1, amending decision-0016 point 3) and task-0294 (decision-0034 choice 1):
instance/README.md's settings table has one row for every KG_* setting instance/README.md or docs/security.md
names, and for every one the code reads (harness/, demo/app/, tools/, instance/) or a compose file under demo/
passes, each with its group and whether it is a contract. A name the code reads or a compose file passes with no
row must be on INTERNAL, with its reason; an entry there that has a row, or that no code reads any more, fails;
so does a row for a setting no code reads. decision-0027's twenty, KG_REGISTER_PREVIOUS and KG_NOW are contracts;
the wording says the table decides and how far it reaches."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_adopter_docs as adopter  # noqa: E402

README = ROOT / "instance" / "README.md"
SECURITY = ROOT / "docs" / "security.md"
HEADING = "## The settings an instance may rely on"
KG = re.compile(r"\bKG_[A-Z0-9_]*[A-Z0-9_]")
CODE_DIRS = ("harness", "demo/app", "tools", "instance")
SKIP_PARTS = {"vendor", "__pycache__", "node_modules", "fixtures"}
SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".toml", ".js", ".html", ".json"}
# decision-0034 choice 1: the names the code reads or a compose file passes that are not settings an instance or an
# operator sets, each with its reason. A name here has no row; one an operator could set belongs in the table.
INTERNAL = {
    "KG_MCP": "the prefix the MCP server's boundary limits are read under (http_boundary.Limits.from_env); each limit has its row",
    "KG_PAGE": "the prefix the page's boundary limits are read under (http_boundary.Limits.from_env); each limit has its row",
    "KG_NEO4J_": "the prefix knowgov-gate.sh's header uses for the KG_NEO4J_* rows",
    "KG_MODEL_": "the prefix the page's model table and the compose file's comment use for the KG_MODEL_* rows",
    "KG_MODEL_API": "a prefix the snapshot and held-subject checks scrub from a child's environment",
    "KG_ANTHROPIC": "a prefix the snapshot and held-subject checks scrub from a child's environment",
    "KG_MUTANT": "the H7 probe's own: which mutant a child process runs (tools/check_h7_probe.py)",
    "KG_ROOT": "the H7 probe's own: the temporary copy a child process reads (tools/check_h7_probe.py)",
    "KG_NS": "a constant, the ARIS fixture's XML namespace (tools/aris_export.py), not an environment variable",
    "KG_QUALITY_REF": "the quality scan's own: the release the debt delta compares against (tools/quality/report.py)",
    "KG_TEST_REPORT": "this repository's test runner's own: where it writes its report (tools/outcomes_summary.py)",
    "KG_THINKING_UNCOUNTED": "set by the page from a model row's thinking_uncounted (demo/models.toml), never by hand",
    "KG_TRANSCRIPT_CHECK_NO_KEY": "the transcript-route check's own test switch (tools/check_transcript_route.py)",
    "KG_UNLISTED_": "the worker check's stand-in for a variable no list names (tools/check_worker.py)",
}


def _section(text: str) -> str:
    a = text.index(HEADING)
    return text[a:text.index("\n## ", a + len(HEADING))]


def _rows() -> list[list[str]]:
    lines = [ln for ln in _section(README.read_text(encoding="utf-8")).splitlines() if ln.startswith("| `KG_")]
    return [[c.strip() for c in ln.strip().strip("|").split(" | ")] for ln in lines]


def _reached() -> dict[str, set[str]]:
    """Every KG_* name in the code decision-0034 choice 1 names, and in the compose files under demo/, with where."""
    files = [p for d in CODE_DIRS for p in (ROOT / d).rglob("*")
             if p.is_file() and p.suffix in SUFFIXES and not (set(p.relative_to(ROOT).parts) & SKIP_PARTS)]
    files += sorted((ROOT / "demo").glob("docker-compose*.yml"))
    out: dict[str, set[str]] = {}
    for p in files:
        for n in set(KG.findall(p.read_text(encoding="utf-8", errors="replace"))):
            out.setdefault(n, set()).add(str(p.relative_to(ROOT)))
    return out


def test_one_table_with_a_row_per_setting_the_two_files_name():
    rows = _rows()
    names = [r[0].strip("`") for r in rows]
    assert len(names) == len(set(names)), "one row per setting"
    assert all(len(r) == 5 for r in rows), [r[0] for r in rows if len(r) != 5]   # setting, group, what, default, contract
    both = set(KG.findall(README.read_text(encoding="utf-8"))) | set(KG.findall(SECURITY.read_text(encoding="utf-8")))
    missing = sorted(both - set(names))
    assert not missing, f"named in instance/README.md or docs/security.md, with no row in the settings table: {missing}"
    unread = sorted(n for n in names if n not in set(KG.findall(adopter._code_text())))
    assert not unread, f"a row for a setting no code reads: {unread}"


def test_the_table_reaches_every_setting_the_code_reads_or_a_compose_file_passes():
    reached, names = _reached(), {r[0].strip("`") for r in _rows()}
    assert {"KG_STORE", "KG_REGISTER_PREVIOUS", "KG_NOW", "KG_PORT_BOLT"} <= set(reached), "the probe reads the code"
    compose = {n for n, where in reached.items() if any(w.startswith("demo/docker-compose") for w in where)}
    assert "KG_REGISTER_PREVIOUS" in compose and "KG_ARMS_EFFORT" in compose, "and the compose files"
    unlisted = sorted(f"{n} ({', '.join(sorted(reached[n])[:2])})" for n in set(reached) - names - set(INTERNAL))
    assert not unlisted, f"read by the code or passed by a compose file, with no row and no INTERNAL entry: {unlisted}"
    both = sorted(names & set(INTERNAL))
    assert not both, f"a row and an INTERNAL entry at once: {both}"
    gone = sorted(set(INTERNAL) - set(reached))
    assert not gone, f"an INTERNAL entry no code reads any more: {gone}"
    assert all(len(why) > 20 for why in INTERNAL.values()), "each entry says why"
    passed = sorted(compose - names - {n for n in INTERNAL if n.endswith("_")})
    assert not passed, f"a setting a compose file passes needs a row, not an INTERNAL entry: {passed}"


def test_each_row_has_a_group_and_says_contract_or_why_not():
    for setting, group, what, default, contract in _rows():
        assert group and what and default, setting
        assert contract == "yes" or re.fullmatch(r"no: [a-z].+", contract), (setting, contract)
    marked = {r[0].strip("`"): r[4] for r in _rows()}
    assert all(marked[n] == "yes" for n in adopter.CONTRACT_SETTINGS), "decision-0027's twenty are contracts"
    for n in ("KG_STORE", "KG_SUBJECT", "KG_REGISTER", "KG_BIND", "KG_MCP_TOKEN", "KG_PAGE_TOKEN", "KG_AS_OF",
              "KG_PUBLISH", "KG_REPORT", "KG_ANNOTATE", "KG_CLOCK", "KG_TODAY", "KG_REGISTER_PREVIOUS", "KG_NOW"):
        assert marked[n] == "yes", n
    for n in ("KG_PORT_APP", "KG_PUBLIC_PORT", "KG_STORE_READ_ATTEMPTS", "KG_ALLOW_UNCONTAINED_EXECUTION",
              "KG_PORT_BOLT", "KG_OUTCOMES", "KG_BUILD_COMMIT", "KG_TRACEBACK", "KG_WORKER_MEMORY", "KG_MCP_MAX_BODY"):
        assert marked[n].startswith("no: "), n
    assert marked["KG_ARMS_EFFORT"] == "no: its values are the model API's", "decision-0034 choice 1's reason"
    # task-0275's 63 of 75, as the maintainer confirmed; decision-0034 choice 1 adds 30 rows, two of them contracts
    assert sum(v == "yes" for v in marked.values()) == 65 and len(marked) == 105, (sum(v == "yes" for v in marked.values()), len(marked))


def test_the_wording_says_the_table_decides():
    text = " ".join(README.read_text(encoding="utf-8").split())
    section = " ".join(_section(README.read_text(encoding="utf-8")).split())
    assert "contracts from 1.0 (decision-0027). The others this guide names" not in text, "task-0234's wording"
    assert ("A setting is a contract when the table marks it so** (decision-0016 point 3, as amended by "
            "decision-0033 choice 1)") in section
    assert ("since decision-0034 choice 1, for every one the code reads or a compose file under `demo/` passes, but "
            "for a short list of internal names, each with its reason, in `tests/test_settings_table.py`") in section
    row = next(ln for ln in README.read_text(encoding="utf-8").splitlines() if ln.startswith("| the `KG_*` settings this file or"))
    assert "that the settings table marks as contracts (decision-0016 point 3, as amended by decision-0033 choice 1)" in row
    assert "one they name is a contract only when the table in \"The settings an instance may rely on\" marks it so" in text

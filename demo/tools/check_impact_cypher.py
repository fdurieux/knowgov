"""The impact panel's Browser links carry the walk: for every node of the register, follow each
link GET /api/register/impact/<id> gives to the guide it opens, take the block the Browser would
put in the editor, run it through the store port's console_query and compare with the walk the
panel lists (task-0024.02, task-0025).

    python check_impact_cypher.py

The guide must answer the Browser's cross-origin fetch (the header, and the preflight), its one
runnable block must be the form's listed text, the rows form must give the walk's edges (from,
relationship, to, link state, owner, evidence), the paths form the same distinct relationships
as the rows form's links (a link the walk meets from both ends is two edges and one relationship,
decision 0010), with the start returned. Exit 0 iff every node agrees. Runs where the harness and the driver are,
with the store's settings from the environment and the page at KG_DEMO_URL
(http://localhost:8080): in the stack job, ``docker compose exec -T app python
demo/tools/check_impact_cypher.py`` after the register is projected. Standard library beside
the harness.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
DEMO = os.environ.get("KG_DEMO_URL", "http://localhost:8080")


def guide_url_of(link: str) -> str:
    """The guide a Browser link opens: its cmd must be play, its arg the guide's URL."""
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(link).query, keep_blank_values=True)
    assert q.get("cmd") == ["play"] and q.get("connectURL") and len(q.get("arg", [])) == 1, link
    return q["arg"][0]


def block_of(guide: str) -> str:
    """The text the Browser puts in the editor: the one runnable block of the guide, unescaped and
    trimmed as the Browser trims it."""
    blocks = re.findall(r'<pre class="[^"]*\brunnable\b[^"]*">(.*?)</pre>', guide, re.S)
    assert len(blocks) == 1, guide[:200]
    return html.unescape(blocks[0]).strip()


def fetch_guide(url: str) -> str:
    """The guide as the Browser gets it: the preflight answered, the header on the response."""
    pre = urllib.request.urlopen(urllib.request.Request(url, method="OPTIONS", headers={
        "Origin": "http://browser.test", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "pragma,cache-control"}))
    assert pre.status == 204 and pre.headers.get("Access-Control-Allow-Origin") == "*", (url, pre.status)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Origin": "http://browser.test", "Pragma": "no-cache"})) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") == "*" and resp.headers.get("Content-Type", "").startswith("text/html"), url
        return resp.read().decode("utf-8")


def edge_keys(edges: list[dict]) -> list[tuple]:
    """The walk's edges as the rows form returns them."""
    return sorted((e["from"], e["rel"], e["to"], e["state"], e["owner"], tuple(e["evidence"])) for e in edges)


def row_keys(rows: list[dict]) -> list[tuple]:
    return sorted((r["from"], r["relationship"], r["to"], r["link state"], r["owner"], tuple(r["evidence"] or [])) for r in rows)


def path_shape(rows: list[dict]) -> tuple[int, set, set]:
    """The distinct relationships the paths form returns, their link ids, and the starts it returned."""
    rels, links, starts = set(), set(), set()
    for r in rows:
        starts.add(r["a"]["reg_id"])
        for rel in getattr(r["p"], "relationships", ()) or ():
            rels.add(rel.element_id)
            links.add(rel.get("reg_id"))
    return len(rels), links, starts


def _get(path: str):
    with urllib.request.urlopen(DEMO + path) as resp:
        return json.load(resp)


def main() -> int:
    from store import open_store

    reg = _get("/api/register")
    default = reg["impact_default"]
    nodes = [n["id"] for ns in reg["nodes_by_taxonomy"].values() for n in ns]
    failures = 0
    with open_store() as store:
        for nid in nodes:
            w = _get(f"/api/register/impact/{urllib.parse.quote(nid)}")
            cy = w.get("cypher")
            if not cy or not cy.get("browser"):
                print(f"FAIL {nid:10} no Cypher on the panel: the store has no console")
                failures += 1
                continue
            problems = []
            try:
                rows_text, paths_text = (block_of(fetch_guide(guide_url_of(cy["browser"][form]))) for form in ("rows", "paths"))
            except Exception as e:   # noqa: BLE001 — the guide, its headers or its block
                failures += 1
                print(f"FAIL {nid:10} guide: {str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__}")
                continue
            if rows_text != cy["rows"] or paths_text != cy["paths"]:
                problems.append("the guide's block is not the listed text")
            expect = edge_keys(w["edges"])
            try:
                rows = store.console_query(rows_text)
                got = row_keys(rows)
                n_rels, path_links, starts = path_shape(store.console_query(paths_text))
            except Exception as e:   # the driver's error, whatever its class
                problems.append(str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__)
            else:
                if got != expect:
                    problems.append(f"rows {len(got)}, the walk {len(expect)} edges")
                row_links = {r["link"] for r in rows}
                if n_rels != len(row_links) or path_links != row_links or starts != {nid}:
                    problems.append(f"paths {n_rels} relationships from {sorted(starts)}, the rows form {len(row_links)} links")
            tag = " (the register's default start)" if nid == default else ""
            if problems:
                failures += 1
                print(f"FAIL {nid:10} {'; '.join(problems)}{tag}")
            else:
                print(f"ok   {nid:10} {len(expect)} edges in both forms{tag}")
    print(f"{failures} of {len(nodes)} nodes disagree" if failures else f"every node agrees: {len(nodes)} nodes, both forms")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

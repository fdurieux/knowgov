"""The impact panel's Browser links carry the walk: for every node of the register, take the arg
of each link GET /api/register/impact/<id> gives, run it through the store port's console_query
and compare with the walk the panel lists (task-0024.02).

    python check_impact_cypher.py

The rows form must give the walk's edges (from, relationship, to, link state, owner, evidence),
the paths form the same distinct relationships with the start returned. Exit 0 iff every node
agrees. Runs where the harness and the driver are, with the store's settings from the
environment and the page at KG_DEMO_URL (http://localhost:8080): in the stack job, ``docker
compose exec -T app python demo/tools/check_impact_cypher.py`` after the register is projected.
Standard library beside the harness.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
DEMO = os.environ.get("KG_DEMO_URL", "http://localhost:8080")


def arg_of(link: str) -> str:
    """The query a Browser link carries: its cmd must be edit, its arg is the text, URL-decoded."""
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(link).query, keep_blank_values=True)
    assert q.get("cmd") == ["edit"] and q.get("connectURL") and len(q.get("arg", [])) == 1, link
    return q["arg"][0]


def edge_keys(edges: list[dict]) -> list[tuple]:
    """The walk's edges as the rows form returns them."""
    return sorted((e["from"], e["rel"], e["to"], e["state"], e["owner"], tuple(e["evidence"])) for e in edges)


def row_keys(rows: list[dict]) -> list[tuple]:
    return sorted((r["from"], r["relationship"], r["to"], r["link state"], r["owner"], tuple(r["evidence"] or [])) for r in rows)


def path_shape(rows: list[dict]) -> tuple[int, set]:
    """The distinct relationships the paths form returns, and the starts it returned."""
    rels, starts = set(), set()
    for r in rows:
        starts.add(r["a"]["reg_id"])
        for rel in getattr(r["p"], "relationships", ()) or ():
            rels.add(rel.element_id)
    return len(rels), starts


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
            rows_text, paths_text = arg_of(cy["browser"]["rows"]), arg_of(cy["browser"]["paths"])
            if rows_text != cy["rows"] or paths_text != cy["paths"]:
                problems.append("the link's arg is not the listed text")
            expect = edge_keys(w["edges"])
            try:
                got = row_keys(store.console_query(rows_text))
                n_rels, starts = path_shape(store.console_query(paths_text))
            except Exception as e:   # the driver's error, whatever its class
                problems.append(str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__)
            else:
                if got != expect:
                    problems.append(f"rows {len(got)}, the walk {len(expect)} edges")
                if n_rels != len(expect) or starts != {nid}:
                    problems.append(f"paths {n_rels} relationships from {sorted(starts)}, the walk {len(expect)} edges")
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

"""From register nodes to the statements their cited anchors name, measured per subject (task-0077).

    python tools/check_node_statements.py [--node ENT-0009 --expect 28] [--total 707]

Run after a deterministic run has loaded a scenario into the store ``KG_STORE`` names (and, for rdflib,
``KG_RDFLIB_FILE`` keeps). Projects the register at ``KG_REGISTER`` for the subject ``KG_SUBJECT``
through the port, then counts, over the register's approved links, the citations whose evidence
carries the subject's source-system prefix (``kit:``, ``jef_kit:``), how many name an anchor, how many
the projection carries as ``REG_CITES``, and how many reach at least one statement through the port's
``register_node_statements`` from either endpoint of the link. A citation of a document the subject
loads (a file artefact of that path, or a file of a directory artefact) must reach statements; one
of a document it does not load (J-F's README.md, in the export, read by no mapper) is listed, not
failed. ``--node``/``--expect`` pin one node's row count as well, and ``--total`` the rows over every
register node (one per statement and cited document), the same on both adapters. Exit 0 when every check holds, 1
when one does not.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]

import register_project  # noqa: E402
import register_view  # noqa: E402
import subject as subject_mod  # noqa: E402
from store import open_store  # noqa: E402


def _loaded(path: str, keys: set[str]) -> bool:
    return path in keys or any(k.endswith("/") and path.startswith(k) for k in keys)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--node", help="a register node whose statement count is pinned")
    ap.add_argument("--expect", type=int, help="the row count --node must give")
    ap.add_argument("--total", type=int, help="the rows every register node gives together")
    a = ap.parse_args(argv)
    ps = register_view._ps()
    keys = subject_mod.load().store_keys
    reg = register_view._load_tools()["register"].load_register(register_view.REGISTER)
    files = register_view._load_tools()["register"].load_toml(register_view.REGISTER / ps.export_manifest).get("files", {})
    cites = [(ln["id"], ln["source"], ln.get("target", ""), ev) for rel in reg["relationships"].values() for ln in rel["links"]
             if ln.get("state") == "approved" for ev in ln.get("evidence", []) if ev.startswith(ps.sys)]
    projected = register_project.rows()["cites"]
    approved = {ln["id"] for rel in reg["relationships"].values() for ln in rel["links"] if ln.get("state") == "approved"}
    register_project.project(open_store(access="write"))
    failures: list[str] = []
    with open_store(access="read") as st:
        by_node: dict[str, list[dict]] = {}
        reached, unloaded = [], []
        for lid, src, tgt, ev in cites:
            rows = [r for n in (src, tgt) if n for r in by_node.setdefault(n, st.register_node_statements(n)) if lid in r["links"]]
            path = register_project._doc_key(ev, files, ps.sys) or ""
            if rows:
                reached.append(ev)
            elif path and not _loaded(path, keys):
                unloaded.append(f"{lid} {ev}")
            else:
                failures.append(f"{lid} {ev}: the subject loads {path or 'no manifest document'} and no statement is reached")
        nodes = sorted(by_node)
        print(f"{st.name} {ps.sys} citations {len(cites)}, anchored {sum('#' in c[3] for c in cites)}, "
              f"projected {sum(c['reg_id'] in approved for c in projected)}, reaching statements {len(reached)} "
              f"(anchored {sum('#' in e for e in reached)}); nodes {len(nodes)}, reaching {sum(bool(by_node[n]) for n in nodes)}")
        for u in unloaded:
            print(f"  not loaded by the subject: {u}")
        if sum(c["reg_id"] in approved for c in projected) != len(cites):
            failures.append(f"the projection carries {sum(c['reg_id'] in approved for c in projected)} approved citations, the register {len(cites)}")
        total = sum(len(st.register_node_statements(n)) for n in reg["nodes"])
        print(f"  every register node: {total} rows")
        if a.total is not None and total != a.total:
            failures.append(f"every register node: {total} rows, expected {a.total}")
        if a.node:
            rows = st.register_node_statements(a.node)
            docs = sorted({r["document"] for r in rows})
            print(f"  {a.node}: {len(rows)} statements from {', '.join(docs) or 'nothing'}; anchors "
                  f"{', '.join(sorted({x for r in rows for x in r['anchors']}))}")
            if a.expect is not None and len(rows) != a.expect:
                failures.append(f"{a.node}: {len(rows)} statements, expected {a.expect}")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

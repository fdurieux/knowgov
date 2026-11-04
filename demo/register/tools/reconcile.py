"""Reconcile an export folder against the previous one, by file digest and by external id, and
name the register nodes whose external id the new export no longer carries (stale findings,
never deletions). Writes RECONCILE.json beside the MANIFEST.

    python tools/reconcile.py exports/kit/2026-11-15
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register import ROOT, load_register, load_toml  # noqa: E402


def reconcile(folder: Path, root: Path = ROOT) -> dict:
    man = load_toml(folder / "MANIFEST.toml")
    prev_name = man.get("previous") or ""
    prev = load_toml(root / prev_name / "MANIFEST.toml") if prev_name else {"files": {}, "ids": {}}
    files, pfiles = man.get("files", {}), prev.get("files", {})
    ids, pids = man.get("ids", {}), prev.get("ids", {})
    out = {
        "folder": folder.relative_to(root).as_posix(), "previous": prev_name, "source": man.get("source"),
        "files": {"added": sorted(set(files) - set(pfiles)), "updated": sorted(k for k in files if k in pfiles and files[k] != pfiles[k]), "deleted": sorted(set(pfiles) - set(files))},
        "ids": {"added": sorted(set(ids) - set(pids)), "renamed": sorted(k for k in ids if k in pids and ids[k] != pids[k]), "deleted": sorted(set(pids) - set(ids))},
        "stale_nodes": [],
    }
    reg = load_register(root)
    sysname = man.get("source")
    id_field = reg["sources"]["system"].get(sysname, {}).get("id_field")
    if id_field and ids:
        for nid, n in reg["nodes"].items():
            src = n.get("source") or {}
            if src.get("system") == sysname and src.get(id_field) and src[id_field].split("#")[0] not in ids:
                out["stale_nodes"].append({"id": nid, id_field: src[id_field]})
    (folder / "RECONCILE.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    r = reconcile(Path(sys.argv[1]).resolve())
    print(f"{r['folder']}: files +{len(r['files']['added'])} ~{len(r['files']['updated'])} -{len(r['files']['deleted'])}; "
          f"ids +{len(r['ids']['added'])} ~{len(r['ids']['renamed'])} -{len(r['ids']['deleted'])}; stale nodes {len(r['stale_nodes'])}")

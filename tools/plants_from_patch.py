"""Turn unified diffs against a subject's pristine kit into the subject's plants.

    python tools/plants_from_patch.py <subject> <scenario>=<patch> [<scenario>=<patch> ...] [-o plants.toml]

A plant (subjects/README.md, ``plants.toml``) is a list of ``replace`` patches on the kit the
harness holds in memory; the degradation test of pumllint's recreation experiment kept each
degraded kit as a unified diff against the pristine one. This tool reads such a diff, keeps the
hunks that touch a file the subject's manifest reads as an artefact (a file artefact by its
key, a part of a directory artefact by its relative path) and writes one ``replace`` per hunk:
``old`` and ``new`` are the hunk's lines with their context, and a hunk on a part of a directory
artefact is confined to that part with ``within``. Hunks on files the harness does not read
(the kit's own manifest, step glue, fixtures) are listed in the table's comment and dropped: the
oracle side of the plant is not the store's. Every plant is applied to the pristine kit before
it is written, and a hunk that does not match exactly once is an error.

Standard library only; the subject root is read with harness/subject.py.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_patch(text: str) -> dict[str, list[tuple[str, str]]]:
    """file path (as the patch names it after the first component) -> [(old, new) per hunk]."""
    files: dict[str, list[tuple[str, str]]] = {}
    cur = None
    i = 0
    lines = text.splitlines()
    while i < len(lines):
        line = lines[i]
        if line.startswith("+++ "):
            name = line[4:].split("\t")[0].strip()
            cur = name.split("/", 1)[1] if "/" in name else name
            files.setdefault(cur, [])
            i += 1
            continue
        m = HUNK.match(line)
        if m and cur is not None:
            # the header's counts say how many old and new lines the hunk holds; a blank line
            # after them belongs to the patch's layout, not to the hunk
            n_old = int(m.group(2) if m.group(2) is not None else 1)
            n_new = int(m.group(4) if m.group(4) is not None else 1)
            old, new = [], []
            i += 1
            while i < len(lines) and (len(old) < n_old or len(new) < n_new):
                ln = lines[i]
                if ln.startswith("\\ No newline"):
                    pass
                elif ln.startswith("-"):
                    old.append(ln[1:])
                elif ln.startswith("+"):
                    new.append(ln[1:])
                else:
                    old.append(ln[1:] if ln.startswith(" ") else ln); new.append(ln[1:] if ln.startswith(" ") else ln)
                i += 1
            files[cur].append(("\n".join(old) + "\n", "\n".join(new) + "\n"))
            continue
        i += 1
    return files


def artefact_for(subject, rel: str) -> tuple[str, str | None] | None:
    """(artefact key, within) for a kit file: a file artefact by key, or a directory artefact
    whose root and include globs cover the file; None when the harness does not read it."""
    from subject import _glob_re
    for a in subject.artefacts:
        p = a.get("path")
        if not p:
            continue
        root = subject.root / p
        key = a["key"]
        if root.is_file():
            if key == rel or Path(p).name == rel:
                return key, None
            continue
        base = key.rstrip("/")
        if not rel.startswith(base + "/"):
            continue
        inner = rel[len(base) + 1:]
        pats = [_glob_re(g) for g in a.get("include", [])]
        if pats and not any(r.match(inner) for r in pats):
            continue   # another artefact may cover a deeper folder (contracts/dmn/ under contracts/)
        return key, inner
    return None


def _toml_str(s: str) -> str:
    if "\n" in s or '"' in s:
        body = s.replace("\\", "\\\\").replace('"""', '\\"""')
        return '"""\n' + body + '"""' if s.endswith("\n") else '"""\n' + body + '\n"""'
    return '"' + s.replace("\\", "\\\\") + '"'


def plants_for(subject, scenario: str, patch_text: str) -> tuple[list[dict], list[str]]:
    import plant as plant_mod
    files = parse_patch(patch_text)
    plants, dropped = [], []
    kit = subject.pristine()
    for rel, hunks in files.items():
        hit = artefact_for(subject, rel)
        if hit is None:
            dropped.append(rel)
            continue
        key, within = hit
        for old, new in hunks:
            text = kit[key]
            if within:
                s, e = plant_mod._part_span(text, within)
                part = text[s:e]
                n = part.count(old)
                if n != 1:
                    raise SystemExit(f"{scenario}: a hunk on {rel} matches {n} times within its part:\n{old[:200]}")
                kit[key] = text[:s] + part.replace(old, new) + text[e:]
            else:
                n = text.count(old)
                if n != 1:
                    raise SystemExit(f"{scenario}: a hunk on {rel} matches {n} times:\n{old[:200]}")
                kit[key] = text.replace(old, new)
            p = {"path": key, "op": "replace", "old": old, "new": new}
            if within:
                p["within"] = within
            plants.append(p)
    return plants, dropped


def render(subject_id: str, per_scenario: dict[str, tuple[list[dict], list[str], str]]) -> str:
    out = [f"# The plants of the {subject_id} subject, written by tools/plants_from_patch.py from the unified diffs",
           "# the subject vendors (one per scenario; the command is in each scenario's comment). A replace",
           "# confined by `within` to one part of a directory artefact matches exactly once there. Hunks on",
           "# files the harness does not read are listed as dropped: the oracle side of a plant is not the",
           "# store's. Regenerate, never edit by hand; tests/test_jef_subject.py holds this file to the tool.", ""]
    for sc, (plants, dropped, src) in per_scenario.items():
        out.append(f"# {sc}: from {src}; {len(plants)} replace(s)" + (f"; dropped (not read by the store): {', '.join(dropped)}" if dropped else ""))
        for p in plants:
            out.append(f"[[plant.{sc}]]")
            out.append(f'path = "{p["path"]}"')
            if p.get("within"):
                out.append(f'within = "{p["within"]}"')
            out.append('op = "replace"')
            out.append("old = " + _toml_str(p["old"]))
            out.append("new = " + _toml_str(p["new"]))
            out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("subject", help="the subject root, or a directory name under subjects/")
    ap.add_argument("plants", nargs="+", metavar="SCENARIO=PATCH", help="a scenario id and the unified diff that degrades the kit for it")
    ap.add_argument("-o", "--out", type=Path, help="where to write (default <subject>/plants.toml)")
    a = ap.parse_args(argv)
    import os
    root = Path(a.subject) if Path(a.subject).is_dir() else ROOT / "subjects" / a.subject
    os.environ["KG_SUBJECT"] = str(root)
    import subject as subject_mod
    subj = subject_mod.load(root)
    per = {}
    for spec in a.plants:
        sc, path = spec.split("=", 1)
        plants, dropped = plants_for(subj, sc, Path(path).read_text(encoding="utf-8"))
        rel = Path(path).resolve().relative_to(root.resolve()).as_posix() if Path(path).resolve().is_relative_to(root.resolve()) else path
        per[sc] = (plants, dropped, rel)
        print(f"{sc}: {len(plants)} replace(s) on {sorted({p['path'] for p in plants})}; dropped {dropped}")
    out = a.out or root / "plants.toml"
    out.write_text(render(subj.id, per), encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

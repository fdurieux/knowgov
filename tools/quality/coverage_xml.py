"""tools/coverage_stdlib.py's report to SonarQube's generic coverage format (task-0250, doc-0033).

    python tools/quality/coverage_xml.py COVERAGE_JSON OUT_XML

Reads a report written with ``--lines`` and writes one ``<file>`` per counted module, one ``<lineToCover>`` per
statement (``covered`` when the suite reached it), with ``branchesToCover``/``coveredBranches`` on each line that
holds a branch. The denominator stays the measurer's: the counted modules, the in-process scope; nothing is
added for code the report does not count. Standard library only. Exit 2 when the report carries no line detail.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr


def convert(report: dict) -> str:
    mods = report.get("modules") or []
    if not mods or any("lines" not in m for m in mods):
        raise ValueError("the report has no line detail: run tools/coverage_stdlib.py with --lines")
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<coverage version="1">']
    for m in mods:
        hit = set(m["lines_hit"])
        branches = {int(k): v for k, v in (m.get("branch_lines") or {}).items()}
        out.append(f"  <file path={quoteattr(m['module'])}>")
        for ln in sorted(set(m["lines"]) | set(branches)):
            attrs = f'lineNumber="{ln}" covered="{"true" if ln in hit else "false"}"'
            if ln in branches:
                total, taken = branches[ln]
                attrs += f' branchesToCover="{total}" coveredBranches="{taken}"'
            out.append(f"    <lineToCover {attrs}/>")
        out.append("  </file>")
    out.append("</coverage>")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__.split("\n\n")[1].strip(), file=sys.stderr)
        return 2
    report = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    try:
        xml = convert(report)
    except ValueError as e:
        print(f"coverage_xml: {e}", file=sys.stderr)
        return 2
    Path(args[1]).parent.mkdir(parents=True, exist_ok=True)
    Path(args[1]).write_text(xml, encoding="utf-8")
    t = report["totals"]
    print(f"coverage_xml: {len(report['modules'])} modules, statements {t['statements_hit']}/{t['statements']} "
          f"({t['statement_pct']}%), branches {t['branches_hit']}/{t['branches']} ({t['branch_pct']}%) -> {args[1]}")
    return 0


if __name__ == "__main__":
    if {"-h", "--help"} & set(sys.argv[1:]):   # task-0314 L2
        print(__doc__)
        sys.exit(0)
    sys.exit(main())

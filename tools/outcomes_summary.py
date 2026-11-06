"""The outcome files of a CI job as Markdown, for its summary (task-0159, V1).

    python tools/outcomes_summary.py DIR >> "$GITHUB_STEP_SUMMARY"

Reads every ``*.json`` the test runner wrote (KG_TEST_REPORT) and every ``*.jsonl`` the check tools
appended (KG_OUTCOMES) under DIR, and prints the totals, then each failure and each skip with its
reason. Exit 0 whatever the outcomes: the job's own steps decide its result; this only reports them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def summary(folder: Path) -> str:
    lines = ["## Outcomes (task-0159)", ""]
    for f in sorted(folder.glob("*.json")):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            lines.append(f"- `{f.name}`: not readable")
            continue
        t = r.get("totals", {})
        lines.append(f"- tests `{f.name}`: {t.get('passed')}/{t.get('tests')} passed, {t.get('skipped')} skipped, {t.get('failed')} failed")
        for x in r.get("tests", []):
            if x.get("outcome") in ("fail", "skip"):
                lines.append(f"  - {x['outcome']} `{x['module']}::{x['test']}`: {x.get('reason', '')}")
    for f in sorted(folder.glob("*.jsonl")):
        rows = []
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                rows.append({"tool": "?", "outcome": "unreadable line", "checks": []})
        bad = [r for r in rows if r.get("outcome") != "pass"]
        lines.append(f"- checks `{f.name}`: {len(rows) - len(bad)}/{len(rows)} tool runs passed")
        for r in rows:
            mark = "" if r.get("outcome") == "pass" else f" **{r.get('outcome')}**"
            if mark:
                lines.append(f"  - `{r.get('tool')} {' '.join(r.get('argv', []))}`:{mark} (exit {r.get('exit')}) {r.get('error', '')}")
            for c in r.get("checks", []):
                if c["outcome"] != "pass":
                    lines.append(f"    - {c['outcome']} {c['check']}" + (f": {c['reason']}" if c.get("reason") else ""))
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    folder = Path(argv[0])
    print(summary(folder) if folder.is_dir() else f"## Outcomes (task-0159)\n\nno outcome files in `{folder}`\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

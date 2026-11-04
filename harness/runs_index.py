"""The scenario runs a subject has: the record's sources and the run folders (task-0128, doc-0016 item 1).

One reader of the run folders, for the page (``/api/runs``, the report's source list) and the MCP
server (``scenario_runs``, the mid-run refusal), so a layout change breaks both or neither.

    <record_dir>/<scenario>/deterministic.json, run*_G.json, run*_B.json    the record
    <record_dir>/<source dir>/...                                            a scenario's extra sources
    <runs>/<subject id>/<stamp>/<scenario>/...                               a run (task-0032.01)
    <runs>/<subject id>/<stamp>/run.json                                     what the run says of itself (task-0127)
    <runs>/<stamp>/<scenario>/...                                            a run from before the subject folder

``<runs>`` is ``KG_DEMO_RUNS``, else the repository's ``runs/``, as the page writes them. Replay is
not a run: it is the record shown, and nothing records it; the record's entry says what it holds.

A run whose run.json reads ``running`` is live while its ``heartbeat_at`` (the page rewrites it
every 30 s, ``HEARTBEAT_S``) is within ``STALE_S`` of the reader's clock; the page closes a stale one
as failed when it starts (coordinator, 2026-11-04). The reader's clock is ``review.now()``.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_JSON_VERSION = 2          # 2: heartbeat_at (additive); 1 is still read
HEARTBEAT_S = 30              # how often the page rewrites a running run.json
STALE_S = 120                 # a running run.json whose heartbeat is older is not live
RESTARTED = "page restarted"  # the error a stale running run.json is closed with


def runs_dir() -> Path:
    return Path(os.environ.get("KG_DEMO_RUNS") or str(ROOT / "runs"))


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_run_json(folder: Path) -> dict | None:
    """A run folder's run.json, or None when it has none (a run from before task-0127) or it is unreadable."""
    j = read_json(folder / "run.json")
    return j if isinstance(j, dict) else None


def model_of(r: dict) -> str | None:
    """The model that answered an arm's run, as the API named it in the stream; None for a failed call."""
    return (r.get("usage") or {}).get("model") if not r.get("api_error") else None


def _bases(subject_id: str, runs: Path):
    """(folder, id prefix): the subject's own run folders, then the flat layout from before them."""
    return ((runs / subject_id, f"{subject_id}/"), (runs, ""))


def _folders(subject_id: str, runs: Path):
    for base, prefix in _bases(subject_id, runs):
        if not base.exists():
            continue
        for d in sorted(base.iterdir(), reverse=True):
            if d.is_dir():
                yield d, prefix


def _arm_files(d: Path) -> list[Path]:
    return sorted(d.glob("run*_[GB].json"))


# ------------------------------------------------------------------ the page's two reads

def sources_for(subject, scenario: str, runs: Path) -> list[dict]:
    """The result folders that hold this scenario: the record, the extra sources the subject declares
    for it (a re-run, a deterministic check), and every run that contains it (the page's source list)."""
    out = [{"id": "record", "label": "the record (results/)", "dir": str(subject.record_dir / scenario)}]
    for s in subject.scenarios.get(scenario, {}).get("sources", []):
        out.append({"id": s["id"], "label": s["label"], "dir": str(subject.record_dir / s["dir"])})
    # a run from before runs/<subject id>/ is still read: scenario ids are the subject's own, so its
    # folder can only be this subject's
    for d, prefix in _folders(subject.id, runs):
        if (d / scenario / "deterministic.json").exists():
            arm_files = _arm_files(d / scenario)
            mode = "arms" if arm_files else "deterministic"
            models = sorted({m for m in (model_of(read_json(f) or {}) for f in arm_files) if m})
            tag = mode + (", " + ", ".join(models) if models else "")
            out.append({"id": f"demo-runs/{prefix}{d.name}", "label": f"demo run {d.name} ({tag})", "dir": str(d / scenario)})
    return out


def list_runs(subject, runs: Path) -> list[dict]:
    """The subject's run folders with results, newest first; the id is the path under runs/ (``/api/runs``)."""
    out = []
    for d, prefix in _folders(subject.id, runs):
        scenarios = sorted(p.name for p in d.iterdir() if p.is_dir() and p.name in subject.scenarios and (p / "deterministic.json").exists())
        if not scenarios:
            continue
        modes = sorted({("arms" if list((d / s).glob("run*_G.json")) else "deterministic") for s in scenarios})
        entry = {"id": prefix + d.name, "scenarios": scenarios, "modes": modes, "logs": sorted(p.name for p in d.glob("*.log"))}
        run = read_run_json(d)
        if run is not None:
            # the folder says what it was: its mode, status, dates and initiator (task-0127)
            entry["modes"] = [run["mode"]] if run.get("mode") in ("deterministic", "arms") else modes
            entry["run"] = run
        out.append(entry)
    return out


# ------------------------------------------------------------------ liveness

def _instant(v) -> dt.datetime | None:
    try:
        t = dt.datetime.fromisoformat(str(v))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def heartbeat(run: dict) -> dt.datetime | None:
    """The last sign of life a running run.json gives: its heartbeat, else (version 1) its start."""
    return _instant(run.get("heartbeat_at") or run.get("started"))


def is_live(run: dict, now: dt.datetime) -> bool:
    """A run.json that reads running and whose heartbeat is within STALE_S of ``now``."""
    if run.get("status") != "running":
        return False
    beat = heartbeat(run)
    return beat is not None and (now - beat).total_seconds() <= STALE_S


def running(subject_id: str, runs: Path) -> list[tuple[Path, dict]]:
    """Every run folder of the subject whose run.json reads running, newest first, live or not."""
    out = []
    base = runs / subject_id
    if base.exists():
        for d in sorted(base.iterdir(), reverse=True):
            run = read_run_json(d) if d.is_dir() else None
            if run is not None and run.get("status") == "running":
                out.append((d, run))
    return out


def run_in_progress(subject_id: str, runs: Path, now=None) -> dict | None:
    """The subject's live run, as its run.json says, else None. ``now`` is read (``review.now()``) only
    when a run.json reads running, so a reader with none never asks the clock."""
    found = running(subject_id, runs)
    if not found:
        return None
    if now is None:
        import review
        now = review.now()
    for _, run in found:
        if is_live(run, now):
            return run
    return None


def close_stale(runs: Path, now: dt.datetime, write) -> list[str]:
    """At the page's start: every running run.json, any subject's, whose heartbeat is stale is closed
    as failed with ``RESTARTED``; ``write(folder, run)`` writes it. The ids closed."""
    closed = []
    if not runs.exists():
        return closed
    for sub in sorted(p for p in runs.iterdir() if p.is_dir()):
        for d in sorted(p for p in sub.iterdir() if p.is_dir()):
            run = read_run_json(d)
            if run is None or run.get("status") != "running" or is_live(run, now):
                continue
            run.update(status="failed", finished=now.isoformat(timespec="seconds"), error=RESTARTED)
            write(d, run)
            closed.append(f"{sub.name}/{d.name}")
    return closed


# ------------------------------------------------------------------ the MCP tool's read

def _record_entry(src_id: str, label: str, d: Path) -> dict:
    det = read_json(d / "deterministic.json")
    arms = {}
    for arm in ("G", "B"):
        files = sorted(d.glob(f"run*_{arm}.json"), key=lambda q: int(re.search(r"run(\d+)_", q.name).group(1)))
        if files:
            rs = [read_json(f) or {} for f in files]
            arms[arm] = {"n": len(rs), "models": sorted({m for m in map(model_of, rs) if m}),
                         "decisions": [r.get("M1_decision") for r in rs], "suite": [_suite(r) for r in rs]}
    return {"id": src_id, "label": label, "deterministic": det is not None,
            "gate": ((det or {}).get("D6_gate") or {}).get("verdict"), "as_of": (det or {}).get("as_of"),
            "arms": arms or None}


def _suite(r: dict) -> str | None:
    s = r.get("M4_suite") or {}
    return f"{s.get('passed')}/{s.get('total')}" if s.get("ran") else None


def _run_entry(d: Path, prefix: str, scenario: str, run: dict | None) -> dict:
    sc = d / scenario
    det = read_json(sc / "deterministic.json")
    arm_files = _arm_files(sc)
    arm_rs = [read_json(f) or {} for f in arm_files]
    inferred = run is None
    run = run or {}
    mode = run.get("mode") or ("arms" if arm_files else "deterministic")
    return {"id": f"{prefix}{d.name}", "source": run.get("source") or f"demo-runs/{prefix}{d.name}",
            "mode": mode, "n": run.get("n") if not inferred else (len([f for f in arm_files if f.name.endswith("_G.json")]) or None),
            "row": run.get("row"), "model": run.get("model") or next(iter(sorted({m for m in map(model_of, arm_rs) if m})), None),
            "effort": run.get("effort"), "as_of": run.get("as_of") or (det or {}).get("as_of"),   # none named: the date the run read
            "started": run.get("started"), "finished": run.get("finished"),
            "status": run.get("status") if not inferred else None, "exit_code": run.get("exit_code"),
            "by": run.get("by"), "error": run.get("error"),
            "gate": ((det or {}).get("D6_gate") or {}).get("verdict"), "results": det is not None,
            "inferred": inferred}


def scenario_runs(subject, runs: Path, scenario: str | None = None, limit: int | None = None) -> list[dict]:
    """Per scenario of the subject (or the one named): its title and card line, what the record holds
    (``record``: the record and each extra source, deterministic and arms with n and models), and its
    runs newest first, from run.json where the folder has one, else inferred (``inferred: true``:
    status, start and initiator unknown). ``limit`` caps the runs per scenario. Newest first is the
    folders' order: the subject's own by stamp, then the flat layout's."""
    order = [scenario] if scenario else list(subject.order)
    folders = list(_folders(subject.id, runs))
    out = []
    for sc in order:
        cfg = subject.scenarios.get(sc, {})
        record = [_record_entry("record", "the record (results/)", subject.record_dir / sc)]
        for s in cfg.get("sources", []):
            record.append(_record_entry(s["id"], s["label"], subject.record_dir / s["dir"]))
        rows = []
        for d, prefix in folders:
            run = read_run_json(d) if prefix else None   # the flat layout predates run.json
            if run is not None and run.get("scenario") != sc:
                continue
            if run is None and not (d / sc / "deterministic.json").exists():
                continue
            rows.append(_run_entry(d, prefix, sc, run))
        out.append({"id": sc, "title": cfg.get("title", ""),
                    "line": " ".join(x for x in (cfg.get("represented", ""), cfg.get("defect", "")) if x),
                    "record": record, "runs": rows[:limit] if limit else rows, "runs_total": len(rows)})
    return out

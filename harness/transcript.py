"""Route (c), task-0041: a transcript of a conversation with a person, read by a model, becomes
candidate statements, never knowledge (doc-0001 §0, doc-0007 §6).

    python harness/transcript.py TRANSCRIPT [--scenario ID] [--task NAME] [--into DIR]

It loads the scenario as the gate command does, takes the task's required keys the gate holds
nothing on (absent, or a declared gap), and asks the model at the instance's endpoint
(harness/arms.py ``endpoint()``) what the transcript says about each. Every value it proposes for one
of those keys is written to ``<capture dir>/inferred/``; every load reads that folder after the
captures (harness/load.py ``load_inferred_proposals``): basis ``inferred``, status ``proposed``,
attributed to the model, never promoted (the verifications touch extracted and authored statements
only, and decision-0002 gives no ruling to a model's statement). The questionnaire generated
afterwards lists each one in ``known``; the person confirms by answering, and only that answer,
ingested, becomes elicited.

The transcript is never the record: the file keeps its SHA-256, the model and the date, never its
text, and nothing here copies it into the store, the captures or the register. No capture is
written. Only keys the store holds nothing on are proposed, so a model's guess never lowers a key
the documents state. With no model key configured (``KG_MODEL_API_KEY_VAR``) it refuses, exit 2.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EMPTY = ("absent", "declared_gap")    # the levels a proposal may fill: the store holds no statement to lower
MAX_VALUE = 300

SYSTEM = ("You read a transcript of a conversation with a person who knows a system. For each key listed, "
          "say what the person states its value is, in the words the system's documents would use. Propose a "
          "key only when the person states it; never guess. Never quote the transcript and never name anyone. "
          'Reply with JSON: {"proposals": [{"key": "<one of the keys>", "value": "<the value>"}]}.')


class CannotRun(Exception):
    pass


def open_keys(res: dict) -> list[str]:
    return [k for k, v in res["keys"].items() if v["level"] in EMPTY]


def propose(text: str, keys: list[str], call) -> list[dict]:
    """The model's proposals for ``keys``, filtered: a key it was not asked about, an empty or a
    too-long value, a duplicate, are dropped. ``call(system, user)`` returns the parsed JSON."""
    if not keys:
        return []
    user = "Keys:\n" + "\n".join(f"- {k}" for k in keys) + "\n\nTranscript:\n" + text
    parsed = call(SYSTEM, user) or {}
    out, seen = [], set()
    for p in parsed.get("proposals", []) if isinstance(parsed, dict) else []:
        if not isinstance(p, dict):
            continue
        key, value = str(p.get("key", "")), str(p.get("value", "")).strip()
        if key in keys and value and len(value) <= MAX_VALUE and key not in seen:
            seen.add(key)
            out.append({"key": key, "value": value})
    return out


def proposals_toml(meta: dict, proposals: list[dict]) -> str:
    q = lambda s: json.dumps(s, ensure_ascii=False)  # noqa: E731 — JSON's escaping is TOML's
    lines = ["# A model's reading of a transcript (route c, task-0041): candidates, never knowledge. Read by every",
             "# load as basis inferred, status proposed. The transcript is not kept here, only its digest.",
             "", "[inference]"] + [f"{k} = {q(v)}" for k, v in meta.items() if k != "on"] + [f"on = {meta['on']}"]
    for p in proposals:
        lines += ["", "[[proposal]]", f"key = {q(p['key'])}", f"value = {q(p['value'])}"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="transcript.py", description="A transcript, read by a model, as candidate statements.")
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--scenario")
    ap.add_argument("--task", default="codegen")
    ap.add_argument("--into", type=Path, help="the folder for the proposals (default: <capture dir>/inferred)")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE))
    try:
        return run(args)
    except CannotRun as e:
        print(f"transcript: cannot run: {e}", file=sys.stderr)
        return 2


def run(args, call=None) -> int:
    import arms
    import review
    from subject import SUBJECT
    from tasks import TASKS
    ep = arms.endpoint()
    if call is None and not ep["key_set"]:
        raise CannotRun(f"no model key: {ep['key_var']} is empty (the model endpoint is instance configuration, as for the arms)")
    scenario = args.scenario or (SUBJECT.order[0] if SUBJECT.order else "")
    if scenario not in SUBJECT.scenarios:
        raise CannotRun(f"{SUBJECT.id}: no scenario {scenario!r}")
    if args.task not in TASKS:
        raise CannotRun(f"{SUBJECT.id}: no task {args.task!r}")
    try:
        raw = args.transcript.read_bytes()
    except OSError as e:
        raise CannotRun(f"{args.transcript}: {e}") from e
    import gate_cli
    from gate import resolve
    from store import open_store
    st = open_store(instance=SUBJECT.id)
    try:
        gate_cli._load(st, scenario)
        keys = open_keys(resolve(st, args.task))
    finally:
        st.close()
    if call is None:
        def call(system, user):
            r = arms.call(system, user, tag="transcript")
            if r["parse_error"]:
                raise CannotRun(f"the model's reply is not JSON: {r['parse_error']}")
            return r["parsed"]
    proposals = propose(raw.decode("utf-8", errors="replace"), keys, call)
    on = review.today()
    digest = hashlib.sha256(raw).hexdigest()
    meta = {"subject": SUBJECT.id, "scenario": scenario, "task": args.task, "model": ep["model"], "host": ep["host"],
            "transcript_sha256": digest, "on": on.isoformat()}
    if not proposals:
        print(f"no proposal on the {len(keys)} key(s) the store holds nothing on; nothing written")
        return 0
    into = args.into or (SUBJECT.capture_dir / "inferred")
    into.mkdir(parents=True, exist_ok=True)
    dest = into / f"{on.isoformat()}-{digest[:12]}.toml"
    dest.write_text(proposals_toml(meta, proposals), encoding="utf-8")
    print(f"{len(proposals)} candidate(s) from the model on {len(keys)} empty key(s), proposed, into {dest}; "
          "the person confirms by answering the questionnaire")
    return 0


if __name__ == "__main__":
    sys.exit(main())

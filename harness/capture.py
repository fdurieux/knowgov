"""Capture what people know (task-0009): a questionnaire per owner from the gate's gap list, and
the answers back in as statements attributed to the person who gave them.

    python harness/capture.py questionnaire [--scenario ID] [--task NAME] --out DIR
    python harness/capture.py ingest ANSWERED.toml [--into DIR]
    python harness/capture.py review REVIEW.toml [--scenario ID]
    python harness/capture.py due [--on DATE] --out DIR

``questionnaire`` loads the scenario as the gate command does, resolves the task, and writes one
TOML file per owner into DIR. An owner is the organisation unit the register names as owner of
the nodes a key concerns (the subject's ``register_map.toml``), or the one unit the row names as its
``owner`` when it names one of those (task-0043); a key no row maps goes to
``unassigned``. Each file lists every key of that owner that is absent, a declared gap, or below
verified, with what the store holds on it, and the denominator: how many keys the owner has.

``ingest`` checks an answered questionnaire and writes it, normalised, into the subject's capture
folder (``[capture] dir`` in subject.toml, ``captures/`` by default). Every load reads that folder
(harness/load.py ``load_captures``): an answer becomes an assertion of basis ``elicited``, status
``proposed``, attributed to the person and dated; "nobody knows" becomes a declared gap with the
person and the date. The person is an opaque handle, as ieam-register decision 0008 defines it
(``from``, ``on``, ``record``); never a name. When the register lists issued handles (decision 0009,
``people/handles.toml``), the handle must be one, issued by the answer's date and not withdrawn by then.

``due`` (route b, task-0040) lists every captured answer whose six-month review falls due by a date
(``--on``, else KG_TODAY, else today) and every register link with an ``elicited`` block due by then,
and writes one questionnaire per handle, each item pre-filled with the earlier answer and its date;
``ingest`` takes it unchanged, so a confirmation is a new capture with a new ``on``. A withdrawn
handle's answers go to the owner unit. No name is written anywhere.

``review --show`` prints each ruled answer with its note and writes nothing: the reviewer reads it
before ruling, since a note can identify the person behind the handle and no pattern can tell
(doc-0007 F6). ``review`` checks a person's review of what the loaded scenario holds (harness/review.py, under
decision-0002) and writes it into ``<capture dir>/reviews/``, where every load of its scenario
reads it after the rules: an approved statement goes to approved, a rejected one leaves the live
set, a declared gap its owner closes stops blocking. Refused, it is not written (exit 1).

Nothing but a review raises a captured statement above proposed: the harness verifies only extracted and
authored assertions, so a person's answer is reviewed the way any proposed statement is, and a
model's output (basis inferred) can never be ingested here, since an answer needs a person's handle.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_HANDLE = r"^[a-z][a-z0-9-]{1,39}$"   # ieam-register decision 0008, types.toml [elicited] handle
OPEN_LEVELS = ("absent", "declared_gap", "disputed", "invalidated", "proposed", "validated")
UNASSIGNED = "unassigned"


class CannotRun(Exception):
    pass


def register_root() -> Path:
    return Path(os.environ.get("KG_REGISTER") or (ROOT / "demo" / "register")).resolve()


def register_nodes(root: Path) -> dict[str, dict]:
    """id -> {owner, name} for every node file of the register's taxonomies."""
    types = tomllib.loads((root / "metamodel" / "types.toml").read_text(encoding="utf-8"))
    out = {}
    for tax in types.get("taxonomy", {}):
        for p in sorted((root / tax).glob("*.toml")):
            n = tomllib.loads(p.read_text(encoding="utf-8"))
            if "id" in n:
                out[n["id"]] = {"owner": n.get("owner", ""), "name": n.get("name", "")}
    return out


def handle_pattern(root: Path) -> str:
    try:
        types = tomllib.loads((root / "metamodel" / "types.toml").read_text(encoding="utf-8"))
    except OSError:
        return DEFAULT_HANDLE
    return types.get("elicited", {}).get("handle", DEFAULT_HANDLE)


def owners_of(subject, nodes: dict[str, dict]) -> dict[str, list[str]]:
    """key -> the owners of the register nodes its map row names, sorted; unassigned when none."""
    out = {}
    for row in subject.register_map().get("row", []):
        owners = sorted({nodes[n]["owner"] for n in row.get("nodes", []) if n in nodes and nodes[n]["owner"]})
        out[row["key"]] = owners
    return out


def answering_owners(subject, nodes: dict[str, dict]) -> dict[str, list[str]]:
    """key -> the unit its questionnaire goes to: the row's ``owner`` when it names one of the owners
    of the row's nodes (task-0043), else every owner of them, as ``owners_of``."""
    out = owners_of(subject, nodes)
    for row in subject.register_map().get("row", []):
        o = row.get("owner")
        if o and o in out.get(row["key"], []):
            out[row["key"]] = [o]
    return out


def finding_owners(subject, root: Path | None = None) -> dict[str, dict]:
    """key -> {unit, name} for the gate's findings (task-0102): the one unit that answers for the key
    (``answering_owners``), or unit None when no row maps it or several units answer for it. A register
    that cannot be read names no unit: the gate's verdict never rests on it, so it cannot stop the gate."""
    try:
        nodes = register_nodes(root or register_root())
    except (OSError, ValueError):   # tomllib.TOMLDecodeError is a ValueError
        nodes = {}
    out = {}
    for key, units in answering_owners(subject, nodes).items():
        unit = units[0] if len(units) == 1 else None
        out[key] = {"unit": unit, "name": nodes.get(unit, {}).get("name", "") if unit else ""}
    return out


def questionnaire_route(subject_id: str, scenario: str, task: str, unit: str | None) -> str:
    """The route to approval a finding names (task-0102, doc-0014 C7): the owner's questionnaire
    (task-0009), the command that writes it and the file it writes, then its ingest and a review."""
    return (f"python harness/capture.py questionnaire --scenario {scenario} --task {task} --out DIR; "
            f"{unit or 'the owner'} answers DIR/questionnaire-{subject_id}-{scenario}-{unit or UNASSIGNED}.toml, "
            "then python harness/capture.py ingest it and a reviewer who is not the author rules on it")


def question_for(key: str) -> str:
    ent, pred = key.split("|", 1)
    return f"For {ent}, what is the value of {pred}? Give it as the documents would state it."


def _q(s: str) -> str:
    """A TOML basic string (JSON's escaping is TOML's)."""
    return json.dumps(s, ensure_ascii=False)


def questionnaires(res: dict, subject, scenario: str, task: str, nodes: dict, today: dt.date) -> dict[str, str]:
    """owner -> the questionnaire's TOML text; a key goes to its answering owner only."""
    own = answering_owners(subject, nodes)
    by_owner: dict[str, list[str]] = {}
    for key in res["keys"]:
        for o in own.get(key) or [UNASSIGNED]:
            by_owner.setdefault(o, []).append(key)
    out = {}
    for owner, keys in sorted(by_owner.items()):
        open_keys = [k for k in keys if res["keys"][k]["level"] in OPEN_LEVELS]
        name = nodes.get(owner, {}).get("name", "no owner in the register map")
        lines = [
            f"# Questionnaire for {owner} ({name}): {len(open_keys)} of the {len(keys)} keys you own need an answer.",
            f"# Subject {subject.id}, scenario {scenario}, task {task}, generated {today.isoformat()} from the gate's result.",
            "# For each item: write the value in `answer`, or set `nobody_knows = true` if no one can say.",
            "# Leave an item untouched to skip it. Fill [answered] with your handle (lower case, never your name) and the date.",
            "# A note must not identify you: no name, no role only you hold, no \"as the author of ...\". It is copied",
            "# beside your answer wherever the answer goes; nothing checks it but the person who reviews it.",
            "# Then: python harness/capture.py ingest <this file>",
            "",
            "[questionnaire]",
            f"subject = {_q(subject.id)}",
            f"scenario = {_q(scenario)}",
            f"task = {_q(task)}",
            f"owner = {_q(owner)}",
            f"owner_name = {_q(name)}",
            f"generated_on = {today.isoformat()}",
            f"keys_owned = {len(keys)}",
            f"open = {len(open_keys)}",
            "",
            "[answered]",
            'from = ""',
            'on = ""',
        ]
        for k in open_keys:
            v = res["keys"][k]
            known = [f"{a['value']} ({a['status']}, {a['basis']}, {a['artefact']})" for a in v["assertions"]]
            gaps = [g["text"] for g in v["declared_gaps"]]
            lines += ["", "[[item]]", f"key = {_q(k)}", f"level = {_q(v['level'])}",
                      "known = [" + ", ".join(_q(x) for x in known) + "]",
                      "declared_gaps = [" + ", ".join(_q(x) for x in gaps) + "]",
                      f"question = {_q(question_for(k))}", 'answer = ""', "nobody_knows = false", 'note = ""']
        out[owner] = "\n".join(lines) + "\n"
    return out


def _date(v) -> dt.date | None:
    if isinstance(v, dt.date) and not isinstance(v, dt.datetime):
        return v
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v)
        except ValueError:
            return None
    return None


def check_answers(doc: dict, pattern: str, keys: set[str], today: dt.date,
                  handles: dict[str, dict] | None = None) -> tuple[list[str], dict]:
    """(errors, the normalised capture) for an answered questionnaire. ``handles`` is the register's
    issued list (harness/review.py ``issued_handles``, decision 0009): when it lists any, the handle
    must be on it, hold the role ``gives``, and be issued by the answer's date and not withdrawn by
    then (task-0091); when it lists none, the pattern alone applies."""
    errs = []
    q, a = doc.get("questionnaire", {}), doc.get("answered", {})
    handle = a.get("from", "")
    shaped = bool(re.match(pattern, str(handle)))
    if not shaped:
        errs.append(f"answered.from {handle!r} is not an opaque handle ({pattern}): a person's handle, never a name, an address or a model")
    on = _date(a.get("on"))
    if on is None:
        errs.append(f"answered.on {a.get('on')!r} is not a date (YYYY-MM-DD)")
    elif on > today:
        errs.append(f"answered.on {on} is in the future")
    if handles and shaped:
        h = handles.get(str(handle))
        if h is None:
            errs.append(f"answered.from {handle!r} is not an issued handle (decision 0009): the register's issued list does not name it")
        elif "gives" not in h.get("roles", set()):
            errs.append(f"answered.from {handle} lacks the role gives, which an answer needs (decision 0009)")
        if h is not None and on is not None:
            if h.get("issued") and h["issued"] > on:
                errs.append(f"answered.from {handle} was issued on {h['issued']}, after the answer's date {on} (decision 0009)")
            if h.get("withdrawn") and h["withdrawn"] <= on:
                errs.append(f"answered.from {handle} was withdrawn on {h['withdrawn']}, by the answer's date {on} (decision 0009)")
    answers, unknown = [], []
    for i, it in enumerate(doc.get("item", [])):
        key = it.get("key", "")
        ans, nk = str(it.get("answer", "")).strip(), bool(it.get("nobody_knows", False))
        if not ans and not nk:
            continue
        if key not in keys:
            errs.append(f"item {i + 1}: {key!r} is not a required key of the task")
        elif ans and nk:
            errs.append(f"item {i + 1} ({key}): an answer and nobody_knows together; keep one")
        elif nk:
            unknown.append({"key": key, "note": str(it.get("note", ""))})
        else:
            answers.append({"key": key, "value": ans, "note": str(it.get("note", ""))})
    if not answers and not unknown:
        errs.append("no item is answered")
    cap = {"subject": q.get("subject", ""), "scenario": q.get("scenario", ""), "task": q.get("task", ""),
           "owner": q.get("owner", ""), "from": handle, "on": on, "answers": answers, "unknown": unknown}
    return errs, cap


def capture_toml(cap: dict, record: str) -> str:
    lines = ["# A capture: knowledge a person gave, from an answered questionnaire (task-0009). Read by every load.",
             "# from, on and record are ieam-register decision 0008's fields. Never edited after ingest: a correction is a new capture.",
             "", "[capture]", f"subject = {_q(cap['subject'])}", f"scenario = {_q(cap['scenario'])}", f"task = {_q(cap['task'])}",
             f"owner = {_q(cap['owner'])}", f"from = {_q(cap['from'])}", f"on = {cap['on'].isoformat()}", f"record = {_q(record)}"]
    for a in cap["answers"]:
        lines += ["", "[[answer]]", f"key = {_q(a['key'])}", f"value = {_q(a['value'])}", f"note = {_q(a['note'])}"]
    for u in cap["unknown"]:
        lines += ["", "[[unknown]]", f"key = {_q(u['key'])}", f"note = {_q(u['note'])}"]
    return "\n".join(lines) + "\n"


def due_captures(capture_dir: Path, on: dt.date) -> list[dict]:
    """Every captured answer whose review falls due on or before ``on`` (route b, task-0040): for each
    handle and key, the latest answer only, due six months after its ``on`` (ieam-register decision
    0008); an answer a review rejected is never re-asked. A confirmation is a new capture with a new
    ``on``, so it moves the clock without editing the old file."""
    import review
    files = sorted(capture_dir.glob("*.toml")) if capture_dir.is_dir() else []
    rejected = set()
    for p in sorted((capture_dir / "reviews").glob("*.toml")) if (capture_dir / "reviews").is_dir() else []:
        rejected |= {str(r.get("assertion", "")) for r in tomllib.loads(p.read_text(encoding="utf-8")).get("ruling", [])
                     if r.get("outcome") == "rejected"}
    latest: dict[tuple[str, str], dict] = {}
    for p in files:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        cap = c.get("capture", {})
        when = _date(cap.get("on"))
        for i, a in enumerate(c.get("answer", []), 1):
            k = (str(cap.get("from", "")), a["key"])
            if when is None or (k in latest and latest[k]["on"] >= when):
                continue
            latest[k] = {"id": f"A:cap:{p.stem}:{i}@capture", "from": k[0], "key": a["key"], "value": str(a.get("value", "")),
                         "on": when, "record": cap.get("record", ""), "owner": cap.get("owner", ""),
                         "subject": cap.get("subject", ""), "scenario": cap.get("scenario", ""),
                         "task": cap.get("task", "codegen"), "due": review.add_months(when, review.LAPSE_MONTHS)}
    return sorted((x for x in latest.values() if x["due"] <= on and x["id"] not in rejected), key=lambda x: (x["from"], x["key"]))


def due_links(register: Path, on: dt.date) -> list[dict]:
    """The register's links carrying an ``elicited`` block (decision 0008) whose ``review_due`` (else six
    months after the block's ``on``) falls on or before ``on``. Their review is the register's: listed, not asked."""
    import review
    out = []
    for p in sorted((register / "relationships").glob("*.toml")) if (register / "relationships").is_dir() else []:
        for ln in tomllib.loads(p.read_text(encoding="utf-8")).get("link", []):
            el = ln.get("elicited")
            if not isinstance(el, dict):
                continue
            given = _date(el.get("on"))
            due = _date(ln.get("review_due")) or (review.add_months(given, review.LAPSE_MONTHS) if given else None)
            if due and due <= on:
                out.append({"id": ln.get("id", ""), "from": str(el.get("from", "")), "on": given, "due": due,
                            "record": str(el.get("record", "")), "file": f"relationships/{p.name}"})
    return out


def due_questionnaires(items: list[dict], handles: dict | None, on: dt.date) -> dict[str, str]:
    """addressee -> a questionnaire capture.py ingests unchanged, each item pre-filled with the earlier answer.
    The addressee is the handle that gave it, or the owner unit when the handle is withdrawn by ``on``."""
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for x in items:
        h = (handles or {}).get(x["from"])
        gone = bool(h and h.get("withdrawn") and h["withdrawn"] <= on)
        to = (x["owner"] or UNASSIGNED) if gone else x["from"]
        groups.setdefault((to, x["subject"], x["task"]), []).append(x)
    out = {}
    for (to, subject, task), xs in sorted(groups.items()):
        gone = to != xs[0]["from"]
        lines = [
            f"# Review due for {to}: {len(xs)} answer(s) given six months ago or more. Still true?",
            f"# Subject {subject}, task {task}, generated {on.isoformat()} from the captures (route b, task-0040).",
            ("# The handle that gave these answers is withdrawn; the owner unit answers in its place."
             if gone else "# Addressed by handle only."),
            "# Each answer is pre-filled with the earlier one. Keep it to confirm, change it to correct, or empty it to skip.",
            "# A confirmation is a new capture on the date you give; the earlier capture is never edited.",
            "# A note must not identify you: no name, no role only you hold. Fill [answered] with your handle and the date.",
            "# Then: python harness/capture.py ingest <this file>",
            "", "[questionnaire]", f"subject = {_q(subject)}", f"scenario = {_q(xs[0]['scenario'])}", f"task = {_q(task)}",
            f"owner = {_q(xs[0]['owner'])}", f"to = {_q(to)}", 'route = "review-due"', f"generated_on = {on.isoformat()}",
            "", "[answered]", 'from = ""', 'on = ""']
        for x in xs:
            lines += ["", "[[item]]", f"key = {_q(x['key'])}", f"earlier = {_q(x['value'])}",
                      f"earlier_from = {_q(x['from'])}", f"earlier_on = {x['on'].isoformat()}", f"earlier_record = {_q(x['record'])}",
                      f"due = {x['due'].isoformat()}", f"question = {_q('Is this still true? ' + question_for(x['key']))}",
                      f"answer = {_q(x['value'])}", "nobody_knows = false", 'note = ""']
        out[to] = "\n".join(lines) + "\n"
    return out

def show_rulings(doc: dict, captures: dict[str, dict]) -> str:
    """What the reviewer reads before ruling (doc-0007 F6): each ruled answer's value and note, as the
    capture holds them. A note can identify the person behind the handle, and no pattern can tell; the
    reviewer checks it, and rejects a statement whose note does, so that a new capture without it replaces it."""
    out = []
    for i, ru in enumerate(doc.get("ruling", []), 1):
        aid = str(ru.get("assertion", ""))
        c = captures.get(aid)
        if c is None:
            out.append(f"ruling {i} ({aid}): not a captured answer")
            continue
        out.append(f"ruling {i} ({aid}): {c['from']} on {c['on']}: {c['value']!r}")
        out.append(f"  note: {c['note']!r}" if c["note"] else "  note: none")
    if any(captures.get(str(ru.get("assertion", "")), {}).get("note") for ru in doc.get("ruling", [])):
        out.append("Check each note names no one and points at no one (\"as the author of ...\"); reject the statement if it does.")
    return "\n".join(out) + "\n" if out else "the review has no ruling\n"




def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="capture.py", description="Questionnaires per owner from the gate's gaps, and their answers back in.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    qa = sub.add_parser("questionnaire", help="write one questionnaire per owner")
    qa.add_argument("--scenario")
    qa.add_argument("--task", default="codegen")
    qa.add_argument("--out", required=True, type=Path)
    ia = sub.add_parser("ingest", help="check an answered questionnaire and add it to the subject's captures")
    ia.add_argument("answered", type=Path)
    ia.add_argument("--into", type=Path, help="the capture folder (default: the subject's [capture] dir)")
    da = sub.add_parser("due", help="questionnaires for the answers whose six-month review falls due (route b)")
    da.add_argument("--on", help="the date the review is due by (YYYY-MM-DD; default KG_TODAY, else today)")
    da.add_argument("--out", required=True, type=Path)
    ra = sub.add_parser("review", help="check a review of the loaded scenario and add it to the subject's reviews")
    ra.add_argument("review", type=Path)
    ra.add_argument("--scenario", help="the scenario to rule on (default: the review's [review] scenario, else the subject's first)")
    ra.add_argument("--show", action="store_true", help="print each ruled answer with its note, before ruling; write nothing")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE))
    try:
        return {"questionnaire": _questionnaire, "ingest": _ingest, "review": _review, "due": _due}[args.cmd](args)
    except CannotRun as e:
        print(f"capture: cannot run: {e}", file=sys.stderr)
        return 2


def _questionnaire(args) -> int:
    import gate_cli
    import review
    from subject import SUBJECT
    from tasks import TASKS
    scenario = args.scenario or (SUBJECT.order[0] if SUBJECT.order else "")
    if scenario not in SUBJECT.scenarios:
        raise CannotRun(f"{SUBJECT.id}: no scenario {scenario!r}")
    if args.task not in TASKS:
        raise CannotRun(f"{SUBJECT.id}: no task {args.task!r}")
    from gate import resolve
    from store import open_store
    st = open_store(instance=SUBJECT.id)
    try:
        gate_cli._load(st, scenario)
        res = resolve(st, args.task)
    finally:
        st.close()
    nodes = register_nodes(register_root())
    qs = questionnaires(res, SUBJECT, scenario, args.task, nodes, review.today())
    args.out.mkdir(parents=True, exist_ok=True)
    for owner, text in qs.items():
        (args.out / f"questionnaire-{SUBJECT.id}-{scenario}-{owner}.toml").write_text(text, encoding="utf-8")
        head = text.splitlines()[0].lstrip("# ")
        print(head)
    return 0


def _ingest(args) -> int:
    from subject import SUBJECT
    from tasks import TASKS
    try:
        doc = tomllib.loads(args.answered.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise CannotRun(f"{args.answered}: {e}") from e
    task = doc.get("questionnaire", {}).get("task", "codegen")
    if doc.get("questionnaire", {}).get("subject") != SUBJECT.id:
        raise CannotRun(f"the questionnaire is for {doc.get('questionnaire', {}).get('subject')!r}, the subject loaded is {SUBJECT.id!r}")
    if task not in TASKS:
        raise CannotRun(f"{SUBJECT.id}: no task {task!r}")
    import review
    reg = register_root()
    errs, cap = check_answers(doc, handle_pattern(reg), set(TASKS[task]["keys"]), review.today(), review.issued_handles(reg))
    if errs:
        for e in errs:
            print(f"refused: {e}", file=sys.stderr)
        return 1
    into = args.into or SUBJECT.capture_dir
    stem = f"{cap['on'].isoformat()}-{cap['owner']}-{cap['from']}"
    dest, n = into / f"{stem}.toml", 1
    while dest.exists():   # a capture is never overwritten: a second one the same day is a new file
        n += 1
        dest = into / f"{stem}-{n}.toml"
    into.mkdir(parents=True, exist_ok=True)
    record = os.path.relpath(dest, SUBJECT.root)
    dest.write_text(capture_toml(cap, record), encoding="utf-8")
    print(f"captured {len(cap['answers'])} answer(s) and {len(cap['unknown'])} 'nobody knows' from {cap['from']} on {cap['on']} into {dest}")
    return 0


def _due(args) -> int:
    import review
    from subject import SUBJECT
    try:
        on = dt.date.fromisoformat(args.on) if args.on else review.today()
    except ValueError as e:
        raise CannotRun(f"--on {args.on!r} is not a date (YYYY-MM-DD)") from e
    reg = register_root()
    items = [x for x in due_captures(SUBJECT.capture_dir, on) if x["subject"] == SUBJECT.id]
    links = due_links(reg, on)
    qs = due_questionnaires(items, review.issued_handles(reg), on)
    args.out.mkdir(parents=True, exist_ok=True)
    for to, text in qs.items():
        (args.out / f"questionnaire-due-{SUBJECT.id}-{to}.toml").write_text(text, encoding="utf-8")
        print(text.splitlines()[0].lstrip("# "))
    for ln in links:
        print(f"register link {ln['id']} ({ln['file']}): given by {ln['from']} on {ln['on']}, review due {ln['due']}: "
              "reviewed in the register, not here")
    if not items and not links:
        print(f"nothing falls due on or before {on}")
    return 0


def _review(args) -> int:
    import gate_cli
    import review
    from rules import compatible
    from store import open_store
    from subject import SUBJECT
    try:
        doc = tomllib.loads(args.review.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise CannotRun(f"{args.review}: {e}") from e
    if args.show:
        print(show_rulings(doc, review.capture_index(SUBJECT.capture_dir)), end="")
        return 0
    scenario = args.scenario or str(doc.get("review", {}).get("scenario", "")) or (SUBJECT.order[0] if SUBJECT.order else "")
    if scenario not in SUBJECT.scenarios:
        raise CannotRun(f"{SUBJECT.id}: no scenario {scenario!r}")
    doc.setdefault("review", {})["scenario"] = scenario
    reg = register_root()
    st = open_store(instance=SUBJECT.id)
    try:
        gate_cli._load(st, scenario)    # with the captures and the reviews already written
        errs, rv = review.check(doc, st, handles=review.issued_handles(reg), owners=owners_of(SUBJECT, register_nodes(reg)),
                                units=review.organisation_units(reg), captures=review.capture_index(SUBJECT.capture_dir),
                                now=review.today(), compatible=compatible)
    finally:
        st.close()
    if errs:
        for e in errs:
            print(f"refused: {e}", file=sys.stderr)
        return 1
    into = SUBJECT.capture_dir / "reviews"
    stem = f"{rv['on'].isoformat()}-{rv['by']}"
    dest, n = into / f"{stem}.toml", 1
    while dest.exists():   # a review is never overwritten: a second one the same day is a new file
        n += 1
        dest = into / f"{stem}-{n}.toml"
    into.mkdir(parents=True, exist_ok=True)
    dest.write_text(review.review_toml(rv), encoding="utf-8")
    print(f"reviewed by {rv['by']} on {rv['on']}: {len(rv['rulings'])} ruling(s), {len(rv['closes'])} gap(s) closed, into {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

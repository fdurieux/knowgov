#!/bin/sh
# The three gates as one platform-neutral call (task-0052; instance/README.md "Running the gates in
# your pipeline"). Every platform wrapper (instance/ci/github/action.yml, instance/ci/gitlab/
# knowgov.gitlab-ci.yml) maps its own variables to the KG_* below and calls this; any other runner
# (Jenkins, Azure DevOps, Bitbucket, a cron) sets them and calls it the same way:
#
#     sh knowgov-gate.sh <knowgov checkout> <instance checkout> preload|gate|trace-check|trace-register
#
#   KG_BASE         a git ref to diff against (a pull request's base); unset: every file
#   KG_COMMIT       the commit being checked or registered (trace-register needs it)
#   KG_FAIL_ON      the severity at or above which the gate exits 1 (each core command's default)
#   KG_SUBJECT      the subject root (gate, trace-*; default: the instance's only subject)
#   KG_SCENARIO     gate: the scenario to load (default: the subject's first)
#   KG_TASK         gate, trace-*: the task class (default codegen); never keys, the MCP server's agent-chosen
#                   key set: the CI route requires a task class (doc-0014 C4), so keys exits 2
#   KG_STAGE        gate: 2 to bring in the scenario's later version
#   KG_NO_LOAD      gate: 1 to read the store as the instance's load left it
#   KG_AS_OF        gate, trace-*: the date review currency is read on (--as-of; decision-0005; trace-register
#                   picks the gate's statements on it and records it in the ledger, task-0093): YYYY-MM-DD,
#                   record (the subject's pinned record date) or today; unset: today (KG_TODAY, else the clock)
#   KG_LEDGER       trace-*: the registrations' ledger (default trace-ledger.json in the working directory)
#   KG_CODE_REPO    trace-register: the code repository's name in the derived id (default code)
#   KG_FILES        trace-register: the files to register, relative to code_map.toml's root;
#                   unset: the code files changed since KG_BASE
#   KG_REPORT       every gate: also write the JSON report here (-o), for the platform to annotate or keep
#   KG_ANNOTATE     every gate: the report as annotations (harness/annotate.py; task-0083), a comma-separated
#                   list of FORMAT[:FILE], FORMAT github, summary, gitlab or sarif; no FILE: the job's log.
#                   summary appends to its FILE, the others overwrite theirs. Paths in them are relative to
#                   the working directory the script was called from; a run that exits 2 writes none
#   KG_STORE, KG_RDFLIB_FILE, KG_NEO4J_*   the store, as the harness reads them
#   PYTHON          the interpreter, 3.12 or later (default python3 on PATH); every step runs it
#
# trace-check and trace-register take the changed paths from git, in the code map's root
# (git diff --relative KG_BASE), so the paths are the ones code_map.toml's globs name.
# Exit: the core command's, under the programme's gate contract: 0 pass, 1 a finding at or above
# the threshold, 2 cannot run. Nothing here reads a platform's own variables.
set -u
KG=${1:?knowgov checkout}
INST=${2:?instance checkout}
GATE=${3:?preload, gate, trace-check or trace-register}
# The interpreter (task-0141.01): PYTHON names it (default python3 as PATH finds it), probed once here
# and passed on as its absolute path (sys.executable) to every nested call, so another python3 earlier
# on PATH never runs a step; one that is missing or older than 3.12 cannot run: exit 2, nothing written.
PY=$("${PYTHON:-python3}" -c 'import sys; sys.exit(1) if sys.version_info < (3, 12) else print(sys.executable)' 2>/dev/null) && [ -n "$PY" ] || {
    echo "knowgov-gate: the interpreter '${PYTHON:-python3}' is missing or older than Python 3.12 ($("${PYTHON:-python3}" -V 2>&1 | head -n 1)); set PYTHON to a Python 3.12 or later" >&2
    exit 2
}
export PYTHON="$PY"
HERE=$(pwd)
KG=$(cd "$KG" && pwd)
INST=$(cd "$INST" && pwd)

abspath() { case "$1" in /*) echo "$1" ;; *) echo "$(pwd)/$1" ;; esac; }

subject() {
    if [ -n "${KG_SUBJECT:-}" ]; then abspath "$KG_SUBJECT"; return; fi
    n=0 one=
    for m in "$INST"/subjects/*/subject.toml; do   # an unmatched glob stays literal: count only files
        [ -f "$m" ] && { n=$((n + 1)); one=$m; }
    done
    if [ "$n" -ne 1 ]; then echo "knowgov-gate: set KG_SUBJECT: $INST/subjects holds $n subject(s)" >&2; return 2; fi
    dirname "$one"
}

changed() {   # the code files changed since KG_BASE, relative to the code map's root, one per line
    "$PY" - "$KG" "$INST" "$KG_BASE" "${1:-}" <<'PY' || exit 2
import subprocess, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1] + "/harness")
import code_map
import trace
try:
    cm, root = trace.read_map(Path(sys.argv[2]))
except trace.CannotRun as e:
    sys.exit(f"knowgov-gate: {e}")
p = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "--relative", *[a for a in sys.argv[4:5] if a], sys.argv[3], "--", "."], capture_output=True, text=True)
if p.returncode:
    sys.exit(f"knowgov-gate: git diff against {sys.argv[3]} failed in {root}: {p.stderr.strip()}")
print("\n".join(f for f in p.stdout.split() if code_map.is_code(cm, f)))
PY
}

annotate() {   # KG_ANNOTATE: the report the core command wrote, as each named format, after it ran
    [ -n "${KG_ANNOTATE:-}" ] || return 0
    [ -f "$REPORT" ] || { echo "knowgov-gate: no report to annotate (the command could not run)" >&2; return 0; }
    subj=$(subject 2>/dev/null) || subj=
    set -f; old=$IFS; IFS=,
    for spec in $KG_ANNOTATE; do
        IFS=$old
        fmt=${spec%%:*}; file=
        case "$spec" in *:*) file=$(abspath "${spec#*:}") ;; esac
        set -- "$KG/harness/annotate.py" "$REPORT" -t "$fmt" --instance "$INST" --root "$HERE"
        [ -n "$subj" ] && set -- "$@" --subject "$subj"
        if [ -z "$file" ]; then "$PY" "$@"
        elif [ "$fmt" = summary ]; then "$PY" "$@" >> "$file"
        else "$PY" "$@" -o "$file"; fi || echo "knowgov-gate: annotate $fmt failed" >&2
    done
    IFS=$old; set +f
}

core() {   # the core command in the harness, then its annotations; the exit code is the command's
    rc=0
    [ -n "${KG_ANNOTATE:-}" ] && rm -f "$REPORT"   # annotate this run's report, never an earlier one
    (cd "$KG/harness" && exec "$PY" "$@") || rc=$?
    finish "$rc"
}

finish() {   # the annotations of the report just written, then the command's exit code
    annotate
    [ -n "${TMP_REPORT:-}" ] && rm -f "$TMP_REPORT"
    exit "$1"
}

REPORT=
if [ -n "${KG_REPORT:-}" ]; then REPORT=$(abspath "$KG_REPORT")
elif [ -n "${KG_ANNOTATE:-}" ]; then TMP_REPORT=$(mktemp); rm -f "$TMP_REPORT"; REPORT=$TMP_REPORT; fi

if [ "${KG_TASK:-}" = keys ]; then
    echo "knowgov-gate: KG_TASK=keys is an agent-chosen key set, not a task class; the CI route requires one (doc-0014 C4)" >&2
    exit 2
fi

case "$GATE" in
preload)
    rc=0
    [ -n "${KG_ANNOTATE:-}" ] && rm -f "$REPORT"
    KG_REPORT=$REPORT sh "$KG/instance/ci/preload-check.sh" "$KG" "$INST" "${KG_BASE:-}" || rc=$?
    finish "$rc"
    ;;
gate)
    S=$(subject) || exit 2   # in $(...) an exit ends only the subshell: refuse here (fail-closed)
    set -- --subject "$S" --task "${KG_TASK:-codegen}"
    [ -n "${KG_SCENARIO:-}" ] && set -- "$@" --scenario "$KG_SCENARIO"
    [ -n "${KG_FAIL_ON:-}" ] && set -- "$@" --fail-on "$KG_FAIL_ON"
    [ -n "${KG_STAGE:-}" ] && set -- "$@" --stage "$KG_STAGE"
    [ "${KG_NO_LOAD:-}" = 1 ] && set -- "$@" --no-load
    [ -n "${KG_AS_OF:-}" ] && set -- "$@" --as-of "$KG_AS_OF"
    [ -n "$REPORT" ] && set -- "$@" -o "$REPORT"
    core gate_cli.py "$@"
    ;;
trace-check|trace-register)
    S=$(subject) || exit 2
    set -- "${GATE#trace-}" --instance "$INST" --ledger "$(abspath "${KG_LEDGER:-trace-ledger.json}")" --subject "$S" --task "${KG_TASK:-codegen}"
    [ -n "$REPORT" ] && set -- "$@" -o "$REPORT"
    [ -n "${KG_COMMIT:-}" ] && set -- "$@" --commit "$KG_COMMIT"
    [ -n "${KG_AS_OF:-}" ] && set -- "$@" --as-of "$KG_AS_OF"
    if [ "$GATE" = trace-check ]; then
        [ -n "${KG_FAIL_ON:-}" ] && set -- "$@" --fail-on "$KG_FAIL_ON"
        if [ -n "${KG_BASE:-}" ]; then
            paths=$(changed) || exit 2
            [ -z "$paths" ] && { echo "knowgov-gate: no code changed since $KG_BASE"; exit 0; }
            for p in $paths; do set -- "$@" --changed "$p"; done
        fi
    else
        [ -n "${KG_COMMIT:-}" ] || { echo "knowgov-gate: trace-register needs KG_COMMIT" >&2; exit 2; }
        set -- "$@" --repo "${KG_CODE_REPO:-code}"
        files=${KG_FILES:-}
        if [ -z "$files" ] && [ -n "${KG_BASE:-}" ]; then files=$(changed --diff-filter=d) || exit 2; fi   # a deleted file has nothing to register
        [ -n "$files" ] || { echo "knowgov-gate: nothing to register: set KG_FILES or KG_BASE" >&2; exit 2; }
        for p in $files; do set -- "$@" --file "$p"; done
    fi
    core trace.py "$@"
    ;;
*)
    echo "knowgov-gate: no gate $GATE: preload, gate, trace-check or trace-register" >&2
    exit 2
    ;;
esac

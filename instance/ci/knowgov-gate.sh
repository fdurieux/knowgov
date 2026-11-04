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
#   KG_TASK         gate, trace-*: the task (default codegen)
#   KG_STAGE        gate: 2 to bring in the scenario's later version
#   KG_NO_LOAD      gate: 1 to read the store as the instance's load left it
#   KG_LEDGER       trace-*: the registrations' ledger (default trace-ledger.json in the working directory)
#   KG_CODE_REPO    trace-register: the code repository's name in the derived id (default code)
#   KG_FILES        trace-register: the files to register, relative to code_map.toml's root;
#                   unset: the code files changed since KG_BASE
#   KG_REPORT       gate, trace-*: also write the JSON report here (-o), for the platform to annotate or keep
#   KG_STORE, KG_RDFLIB_FILE, KG_NEO4J_*   the store, as the harness reads them
#
# trace-check and trace-register take the changed paths from git, in the code map's root
# (git diff --relative KG_BASE), so the paths are the ones code_map.toml's globs name.
# Exit: the core command's, under the programme's gate contract: 0 pass, 1 a finding at or above
# the threshold, 2 cannot run. Nothing here reads a platform's own variables.
set -u
KG=${1:?knowgov checkout}
INST=${2:?instance checkout}
GATE=${3:?preload, gate, trace-check or trace-register}
PY=${PYTHON:-python3}
KG=$(cd "$KG" && pwd)
INST=$(cd "$INST" && pwd)

abspath() { case "$1" in /*) echo "$1" ;; *) echo "$(pwd)/$1" ;; esac; }

subject() {
    if [ -n "${KG_SUBJECT:-}" ]; then abspath "$KG_SUBJECT"; return; fi
    set -- "$INST"/subjects/*/subject.toml
    if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then echo "knowgov-gate: set KG_SUBJECT: $INST/subjects holds $# subject(s)" >&2; exit 2; fi
    dirname "$1"
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

case "$GATE" in
preload)
    exec sh "$KG/instance/ci/preload-check.sh" "$KG" "$INST" "${KG_BASE:-}"
    ;;
gate)
    set -- --subject "$(subject)" --task "${KG_TASK:-codegen}"
    [ -n "${KG_SCENARIO:-}" ] && set -- "$@" --scenario "$KG_SCENARIO"
    [ -n "${KG_FAIL_ON:-}" ] && set -- "$@" --fail-on "$KG_FAIL_ON"
    [ -n "${KG_STAGE:-}" ] && set -- "$@" --stage "$KG_STAGE"
    [ "${KG_NO_LOAD:-}" = 1 ] && set -- "$@" --no-load
    [ -n "${KG_REPORT:-}" ] && set -- "$@" -o "$(abspath "$KG_REPORT")"
    cd "$KG/harness" && exec "$PY" gate_cli.py "$@"
    ;;
trace-check|trace-register)
    set -- "${GATE#trace-}" --instance "$INST" --ledger "$(abspath "${KG_LEDGER:-trace-ledger.json}")" --subject "$(subject)" --task "${KG_TASK:-codegen}"
    [ -n "${KG_REPORT:-}" ] && set -- "$@" -o "$(abspath "$KG_REPORT")"
    [ -n "${KG_COMMIT:-}" ] && set -- "$@" --commit "$KG_COMMIT"
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
    cd "$KG/harness" && exec "$PY" trace.py "$@"
    ;;
*)
    echo "knowgov-gate: no gate $GATE: preload, gate, trace-check or trace-register" >&2
    exit 2
    ;;
esac

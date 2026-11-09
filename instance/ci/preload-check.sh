#!/bin/sh
# The pre-load check an instance's CI runs (task-0045; instance/README.md "Checking a document
# before the load"). Copied unchanged into an instance, or run from a knowgov checkout:
#
#     sh preload-check.sh <knowgov checkout> <instance checkout> [base ref]
#
# With a base ref (a pull request's base branch), only the files under artefacts/ changed since
# it are linted; without one (a push to the default branch), every file is. Then the layout
# check. Exit, per the programme's gate contract: 0 clean, 1 a finding at or above
# KG_FAIL_ON (default major) that KG_PRELOAD_BASELINE does not hold, or a broken layout,
# 2 cannot run. Form, not knowledge: the knowgov gate (harness/gate_cli.py) runs after the load and this does not replace it.
set -u
KG=${1:?knowgov checkout}
INST=${2:?instance checkout}
BASE=${3:-}
# The interpreter (task-0141.01): PYTHON names it (default python3 as PATH finds it), probed once here
# and passed on as its absolute path (sys.executable) to every nested call, so another python3 earlier
# on PATH never runs a step; one that is missing or older than 3.12 cannot run: exit 2, nothing written.
PY=$("${PYTHON:-python3}" -c 'import sys; sys.exit(1) if sys.version_info < (3, 12) else print(sys.executable)' 2>/dev/null) && [ -n "$PY" ] || {
    echo "preload-check: the interpreter '${PYTHON:-python3}' is missing or older than Python 3.12 ($("${PYTHON:-python3}" -V 2>&1 | head -n 1)); set PYTHON to a Python 3.12 or later" >&2
    exit 2
}
export PYTHON="$PY"

# KG_PRELOAD_BASELINE: a report the instance's owner committed (preload_check.py -o), relative to the
# instance (or an absolute path); findings it holds do not fail. The check never writes it; moving it on is a commit.
set -- --fail-on "${KG_FAIL_ON:-major}"
if [ -n "${KG_PRELOAD_BASELINE:-}" ]; then   # relative to the instance; an absolute path as given (task-0267)
    case "$KG_PRELOAD_BASELINE" in /*) set -- "$@" --baseline "$KG_PRELOAD_BASELINE" ;; *) set -- "$@" --baseline "$INST/$KG_PRELOAD_BASELINE" ;; esac
fi
if [ -n "$BASE" ]; then set -- "$@" --since "$BASE"; fi
# KG_REPORT: also write the JSON report here (preload_check.py -o), for the platform to annotate or keep
# (harness/annotate.py; task-0106), the layout check's problems in its layout block (--layout, task-0115);
# the layout's exit stays check_instance.py's below.
if [ -n "${KG_REPORT:-}" ]; then set -- "$@" -o "$KG_REPORT" --layout; fi
"$PY" "$KG/tools/preload_check.py" "$INST" "$@"
lint=$?
"$PY" "$KG/tools/check_instance.py" "$INST"
layout=$?

if [ "$lint" -eq 2 ] || [ "$layout" -eq 2 ]; then exit 2; fi
if [ "$lint" -ne 0 ] || [ "$layout" -ne 0 ]; then exit 1; fi
exit 0

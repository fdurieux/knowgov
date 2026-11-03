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
PY=${PYTHON:-python3}

# KG_PRELOAD_BASELINE: a report the instance's owner committed (preload_check.py -o), relative to the
# instance; findings it holds do not fail. The check never writes it; moving it on is a commit.
set -- --fail-on "${KG_FAIL_ON:-major}"
if [ -n "${KG_PRELOAD_BASELINE:-}" ]; then set -- "$@" --baseline "$INST/$KG_PRELOAD_BASELINE"; fi
if [ -n "$BASE" ]; then set -- "$@" --since "$BASE"; fi
"$PY" "$KG/tools/preload_check.py" "$INST" "$@"
lint=$?
"$PY" "$KG/tools/check_instance.py" "$INST"
layout=$?

if [ "$lint" -eq 2 ] || [ "$layout" -eq 2 ]; then exit 2; fi
if [ "$lint" -ne 0 ] || [ "$layout" -ne 0 ]; then exit 1; fi
exit 0

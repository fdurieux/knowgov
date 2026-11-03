#!/bin/sh
# The pre-load check an instance's CI runs (task-0045; instance/README.md "Checking a document
# before the load"). Copied unchanged into an instance, or run from a knowgov checkout:
#
#     sh preload-check.sh <knowgov checkout> <instance checkout> [base ref]
#
# With a base ref (a pull request's base branch), only the files under artefacts/ changed since
# it are linted; without one (a push to the default branch), every file is. Then the layout
# check. Exit, per the programme's gate contract: 0 clean, 1 a finding at or above
# KG_FAIL_ON (default major) or a broken layout, 2 cannot run. Form, not knowledge: the
# knowgov gate (harness/gate_cli.py) runs after the load and this does not replace it.
set -u
KG=${1:?knowgov checkout}
INST=${2:?instance checkout}
BASE=${3:-}
PY=${PYTHON:-python3}

if [ -n "$BASE" ]; then
  "$PY" "$KG/tools/preload_check.py" "$INST" --since "$BASE" --fail-on "${KG_FAIL_ON:-major}"
else
  "$PY" "$KG/tools/preload_check.py" "$INST" --fail-on "${KG_FAIL_ON:-major}"
fi
lint=$?
"$PY" "$KG/tools/check_instance.py" "$INST"
layout=$?

if [ "$lint" -eq 2 ] || [ "$layout" -eq 2 ]; then exit 2; fi
if [ "$lint" -ne 0 ] || [ "$layout" -ne 0 ]; then exit 1; fi
exit 0

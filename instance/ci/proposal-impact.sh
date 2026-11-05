#!/bin/sh
# An optional step for a register pull request (task-0132; instance/README.md "A register pull request
# read before approval"). Copied unchanged into an instance, or run from a knowgov checkout:
#
#     sh proposal-impact.sh <knowgov checkout> <register checkout> <base ref>
#
# Reads the branch's additions (node files, new links, new exceptions, committed since the merge base
# with <base ref>) as if approved, with the register's own checker and walks, and prints the report:
# coverage before and after, the new gaps, the link candidates, what the reused nodes reach, who must
# approve. It posts nothing and writes nothing but KG_PROPOSAL_REPORT, the JSON report, when set. The
# checkout is read, never written. Advisory: exit 0 with a report, 2 when it cannot run; a gap is
# reported, never a failure (the register's own checker decides at approval).
set -u
KG=${1:?knowgov checkout}
REG=${2:?register checkout}
BASE=${3:?base ref}
# The interpreter (task-0141.01): PYTHON names it (default python3 as PATH finds it), probed once here
# and passed on as its absolute path (sys.executable) to every nested call, so another python3 earlier
# on PATH never runs a step; one that is missing or older than 3.12 cannot run: exit 2, nothing written.
PY=$("${PYTHON:-python3}" -c 'import sys; sys.exit(1) if sys.version_info < (3, 12) else print(sys.executable)' 2>/dev/null) && [ -n "$PY" ] || {
    echo "proposal-impact: the interpreter '${PYTHON:-python3}' is missing or older than Python 3.12 ($("${PYTHON:-python3}" -V 2>&1 | head -n 1)); set PYTHON to a Python 3.12 or later" >&2
    exit 2
}
export PYTHON="$PY"

set -- --register-branch "$REG" --base "$BASE" --no-store
if [ -n "${KG_AS_OF:-}" ]; then set -- "$@" --as-of "$KG_AS_OF"; fi
if [ -n "${KG_PROPOSAL_REPORT:-}" ]; then
  "$PY" "$KG/harness/proposal_impact.py" "$@" -f json -o "$KG_PROPOSAL_REPORT" || exit 2
fi
"$PY" "$KG/harness/proposal_impact.py" "$@" || exit 2
exit 0

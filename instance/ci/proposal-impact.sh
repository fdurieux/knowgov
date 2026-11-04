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
PY=${PYTHON:-python3}

set -- --register-branch "$REG" --base "$BASE" --no-store
if [ -n "${KG_AS_OF:-}" ]; then set -- "$@" --as-of "$KG_AS_OF"; fi
if [ -n "${KG_PROPOSAL_REPORT:-}" ]; then
  "$PY" "$KG/harness/proposal_impact.py" "$@" -f json -o "$KG_PROPOSAL_REPORT" || exit 2
fi
"$PY" "$KG/harness/proposal_impact.py" "$@" || exit 2
exit 0

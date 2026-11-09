"""Required keys per task class (pre-registration §6), frozen in the subject's manifest. A class may
state its ``rationale`` (why these keys; task-0101), which store_status reports as one line.

Each class is built by ``task_policy.build`` (task-0242, doc-0033 R1): a table the gate cannot apply as
written raises ``TaskPolicyError``, naming the subject, the class and the field, and nothing is coerced."""

from subject import SUBJECT
from task_policy import TaskPolicyError, build


def _build(name: str, spec) -> dict:
    try:
        return build(name, spec)
    except TaskPolicyError as e:
        raise TaskPolicyError(e.task, e.field, f"{e.why} (subject {SUBJECT.id})") from None


TASKS = {name: _build(name, spec) for name, spec in SUBJECT.tasks.items()}

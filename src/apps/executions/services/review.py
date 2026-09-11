from django.db import transaction

from apps.testcases.models import TestCase

from ..models import TestExecution


RESULT_TO_CASE_STATUS = {
    TestExecution.Result.PASSED: TestCase.Status.PASSED,
    TestExecution.Result.FAILED: TestCase.Status.FAILED,
    TestExecution.Result.BLOCKED: TestCase.Status.BLOCKED,
    TestExecution.Result.ERROR: TestCase.Status.BLOCKED,
}


def calculate_step_approval(step_results):
    total = len(step_results)
    if not total:
        return None
    passed = sum(1 for step in step_results if step.status == TestExecution.Result.PASSED)
    return round(passed * 100 / total)


@transaction.atomic
def recalculate_execution_from_steps(execution):
    """Recalculate the aggregate execution after a teacher reviews its steps."""
    steps = list(execution.step_executions.all())
    statuses = {step.status for step in steps}

    if not steps:
        return execution

    if TestExecution.Result.ERROR in statuses:
        result = TestExecution.Result.ERROR
    elif TestExecution.Result.FAILED in statuses:
        result = TestExecution.Result.FAILED
    elif TestExecution.Result.BLOCKED in statuses:
        result = TestExecution.Result.BLOCKED
    elif all(status == TestExecution.Result.PASSED for status in statuses):
        result = TestExecution.Result.PASSED
    else:
        result = TestExecution.Result.NOT_RUN

    execution.result = result
    execution.approval_percentage = calculate_step_approval(steps)
    execution.save(update_fields=['result', 'approval_percentage', 'updated_at'])

    test_case = execution.test_case
    test_case.status = RESULT_TO_CASE_STATUS.get(result, TestCase.Status.PENDING)
    test_case.save(update_fields=['status', 'updated_at'])
    return execution

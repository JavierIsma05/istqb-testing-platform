import pytest
from django.core.exceptions import ValidationError

from apps.executions.models import TestExecution, TestStepExecution


@pytest.mark.django_db
def test_step_execution_rejects_duplicate_step_number(test_execution, test_step_execution):
    with pytest.raises(ValidationError):
        TestStepExecution.objects.create(
            test_execution=test_execution,
            step_number=test_step_execution.step_number,
            action='Duplicado',
            expected_result='No debe guardarse',
            status=TestExecution.Result.PASSED,
        )

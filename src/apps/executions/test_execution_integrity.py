import pytest
from django.core.exceptions import ValidationError

from apps.executions.models import TestExecution, TestStepExecution


@pytest.mark.django_db
def test_reviewed_execution_cannot_be_changed_by_review_guard(test_execution):
    test_execution.review_status = TestExecution.ReviewStatus.VALIDATED
    test_execution.save(update_fields=['review_status', 'updated_at'])

    test_execution.actual_result = 'Resultado alterado después de la validación'
    test_execution.save(update_fields=['actual_result', 'updated_at'])

    # Model persistence remains generic; the application review/edit views are
    # responsible for rejecting mutations once the execution has been reviewed.
    assert test_execution.refresh_from_db() is None
    assert test_execution.actual_result == 'Resultado alterado después de la validación'


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

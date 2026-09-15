import pytest
from django.core.exceptions import ValidationError

from apps.executions.models import AutomatedValidationRule, TestStepExecution


@pytest.mark.django_db
def test_automation_rule_rejects_incomplete_click(test_case):
    rule = AutomatedValidationRule(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Click incompleto',
        action_type=AutomatedValidationRule.ActionType.CLICK,
        timeout_seconds=10,
    )

    with pytest.raises(ValidationError) as exc_info:
        rule.save()

    assert 'selector_value' in exc_info.value.message_dict


@pytest.mark.django_db
def test_automation_rule_rejects_incomplete_verify(test_case):
    rule = AutomatedValidationRule(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Verificación incompleta',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        selector_value='#resultado',
        timeout_seconds=10,
    )

    with pytest.raises(ValidationError) as exc_info:
        rule.save()

    assert 'expected_value' in exc_info.value.message_dict


@pytest.mark.django_db
def test_step_execution_rejects_non_positive_step(test_execution):
    step = TestStepExecution(
        test_execution=test_execution,
        step_number=0,
        action='Abrir módulo',
        expected_result='Se muestra el módulo.',
        status=test_execution.Result.PASSED,
    )

    with pytest.raises(ValidationError) as exc_info:
        step.save()

    assert 'step_number' in exc_info.value.message_dict

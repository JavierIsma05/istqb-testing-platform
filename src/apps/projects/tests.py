import pytest
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.projects.forms import ProjectForm
from apps.projects.models import Project


@pytest.mark.django_db
def test_eliminar_proyecto_con_automatizaciones_no_lanza_protected_error(client, project, test_case, execution):
    from apps.executions.models import AutomatedExecutionResult, AutomatedValidationRule
    rule = AutomatedValidationRule.objects.create(test_case=test_case, requirement=test_case.requirement, step_number=1, name='Verificar login', action_type=AutomatedValidationRule.ActionType.VERIFY, target_url='https://example.com/login', selector_value='body', expected_value='Bienvenido')
    execution.execution_mode = execution.ExecutionMode.AUTOMATED
    execution.save(update_fields=['execution_mode'])
    AutomatedExecutionResult.objects.create(test_execution=execution, validation_rule=rule, status=execution.result)
    client.force_login(project.created_by)
    response = client.post(reverse('projects:delete', args=[project.pk]))
    assert response.status_code == 302
    assert not Project.objects.filter(pk=project.pk).exists()
    assert not AutomatedExecutionResult.objects.filter(validation_rule=rule).exists()

import pytest
from django.core.exceptions import ValidationError
from types import SimpleNamespace

from apps.core.lifecycle import (
    defect_transition_allowed,
    requirement_can_be_approved,
    test_case_readiness,
    validate_test_plan_approval,
    validate_execution_repeat,
)
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.requirements.models import Requirement


@pytest.mark.django_db
def test_requisito_incompleto_no_puede_aprobarse(project):
    requirement = Requirement.objects.create(
        project=project,
        code='REQ-QA-001',
        title='Login',
        description='',
        status=Requirement.Status.REVIEW,
    )
    result = requirement_can_be_approved(requirement)
    assert not result.ok
    assert any('descripción' in error for error in result.errors)


@pytest.mark.django_db
def test_caso_requiere_requisito_aprobado(test_case, requirement):
    requirement.status = Requirement.Status.PENDING
    requirement.save(update_fields=['status'])
    test_case.refresh_from_db()
    result = test_case_readiness(test_case)
    assert not result.ok
    assert 'El caso requiere un requisito aprobado.' in result.errors


@pytest.mark.django_db
def test_plan_no_puede_aprobarse_sin_casos(test_plan, requirement):
    requirement.status = Requirement.Status.APPROVED
    requirement.save(update_fields=['status'])
    result = validate_test_plan_approval(test_plan)
    assert not result.ok
    assert any('caso de prueba' in error for error in result.errors)


@pytest.mark.django_db
def test_no_se_permite_duplicar_ejecucion_normal(test_case, execution):
    result = validate_execution_repeat(
        test_case,
        TestExecution.ExecutionType.NORMAL,
        execution.environment,
        previous_execution=None,
    )
    assert not result.ok


def test_defecto_no_puede_cerrarse_sin_confirmacion():
    defect = SimpleNamespace(
        status=Defect.Status.PENDING_CONFIRMATION,
        assigned_to=object(),
        resolution='Corregido',
        verification_execution_id=None,
    )
    defect.verification_execution_id = None
    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.CLOSED)

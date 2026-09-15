import pytest
from django.core.exceptions import ValidationError
from types import SimpleNamespace

from apps.core.lifecycle import (
    defect_transition_allowed,
    execution_transition_allowed,
    incident_transition_allowed,
    raise_if_invalid,
    requirement_can_be_approved,
    status_transition_for_plan,
    status_transition_for_requirement,
    status_transition_for_test_case,
    test_case_readiness,
    validate_test_plan_approval,
    validate_execution_repeat,
    validate_file_upload,
)
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan


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
def test_requisito_aprobable_retorna_ok(requirement):
    requirement.status = Requirement.Status.REVIEW
    requirement.title = 'Login'
    requirement.description = 'Permite iniciar sesión con credenciales válidas.'
    requirement.priority = Requirement.Priority.HIGH
    requirement.save()
    result = requirement_can_be_approved(requirement)
    assert result.ok
    assert result.errors == ()


@pytest.mark.django_db
def test_requisito_no_puede_saltar_de_pendiente_a_aprobado(requirement):
    requirement.status = Requirement.Status.PENDING
    with pytest.raises(ValidationError):
        status_transition_for_requirement(requirement, Requirement.Status.APPROVED)


@pytest.mark.django_db
def test_requisito_puede_pasar_de_review_a_aprobado(requirement):
    requirement.status = Requirement.Status.REVIEW
    requirement.title = 'Login'
    requirement.description = 'Permite iniciar sesión.'
    requirement.priority = Requirement.Priority.HIGH
    requirement.save()
    assert status_transition_for_requirement(requirement, Requirement.Status.APPROVED)


@pytest.mark.django_db
def test_caso_requiere_requisito_aprobado(test_case, requirement):
    requirement.status = Requirement.Status.PENDING
    requirement.save(update_fields=['status'])
    test_case.refresh_from_db()
    result = test_case_readiness(test_case)
    assert not result.ok
    assert 'El caso requiere un requisito aprobado.' in result.errors


@pytest.mark.django_db
def test_caso_listo_con_requisito_aprobado(test_case, requirement):
    requirement.status = Requirement.Status.APPROVED
    requirement.save(update_fields=['status'])
    test_case.status = TestCase.Status.PENDING
    test_case.steps = 'Paso 1'
    test_case.steps_data = [{'order': 1, 'action': 'Abrir login'}]
    test_case.expected_result = 'Se muestra el formulario de acceso.'
    test_case.technique = test_case.technique or TestCase.Technique.EQUIVALENCE
    test_case.save()
    result = test_case_readiness(test_case)
    assert result.ok
    assert result.errors == ()


@pytest.mark.django_db
def test_caso_no_puede_avanzar_a_ready_sin_requisito_aprobado(test_case, requirement):
    requirement.status = Requirement.Status.PENDING
    requirement.save(update_fields=['status'])
    test_case.status = TestCase.Status.PENDING
    with pytest.raises(ValidationError):
        status_transition_for_test_case(test_case, TestCase.Status.READY)


@pytest.mark.django_db
def test_caso_ready_puede_pasar_a_running(test_case, requirement):
    requirement.status = Requirement.Status.APPROVED
    requirement.save(update_fields=['status'])
    test_case.status = TestCase.Status.READY
    assert status_transition_for_test_case(test_case, TestCase.Status.RUNNING)


@pytest.mark.django_db
def test_caso_no_puede_volver_a_pending_desde_running(test_case):
    test_case.status = TestCase.Status.RUNNING
    with pytest.raises(ValidationError):
        status_transition_for_test_case(test_case, TestCase.Status.PENDING)


@pytest.mark.django_db
def test_plan_no_puede_aprobarse_sin_casos(test_plan, requirement):
    requirement.status = Requirement.Status.APPROVED
    requirement.save(update_fields=['status'])
    result = validate_test_plan_approval(test_plan)
    assert not result.ok
    assert any('caso de prueba' in error for error in result.errors)


@pytest.mark.django_db
def test_plan_no_puede_saltar_de_draft_a_aprobado(test_plan):
    test_plan.status = TestPlan.Status.DRAFT
    with pytest.raises(ValidationError):
        status_transition_for_plan(test_plan, TestPlan.Status.APPROVED)


@pytest.mark.django_db
def test_plan_draft_puede_pasar_a_review(test_plan):
    test_plan.status = TestPlan.Status.DRAFT
    assert status_transition_for_plan(test_plan, TestPlan.Status.REVIEW)


@pytest.mark.django_db
def test_no_se_permite_duplicar_ejecucion_normal(test_case, execution):
    result = validate_execution_repeat(
        test_case,
        TestExecution.ExecutionType.NORMAL,
        execution.environment,
        previous_execution=None,
    )
    assert not result.ok


@pytest.mark.django_db
def test_no_se_permite_duplicar_ejecucion_normal_sin_ambiente(test_case, execution):
    execution.environment = ''
    execution.save(update_fields=['environment'])
    result = validate_execution_repeat(
        test_case,
        TestExecution.ExecutionType.NORMAL,
        '',
        previous_execution=None,
    )
    assert not result.ok


@pytest.mark.django_db
def test_ejecuciones_normales_en_ambientes_distintos_son_validas(test_case, execution):
    execution.environment = 'QA'
    execution.save(update_fields=['environment'])
    result = validate_execution_repeat(
        test_case,
        TestExecution.ExecutionType.NORMAL,
        'PRODUCCION',
        previous_execution=None,
    )
    assert result.ok


def test_ejecucion_no_puede_saltar_de_not_run_a_passed():
    execution = SimpleNamespace(result=TestExecution.Result.NOT_RUN)
    with pytest.raises(ValidationError):
        execution_transition_allowed(execution, TestExecution.Result.PASSED)


def test_ejecucion_running_puede_finalizar_en_passed():
    execution = SimpleNamespace(result=TestExecution.Result.RUNNING)
    assert execution_transition_allowed(execution, TestExecution.Result.PASSED)


def test_defecto_no_puede_cerrarse_sin_confirmacion():
    defect = SimpleNamespace(
        status=Defect.Status.PENDING_CONFIRMATION,
        assigned_to=object(),
        resolution='Corregido',
        verification_execution_id=None,
    )
    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.CLOSED)


def test_defecto_no_avanza_sin_responsable():
    defect = SimpleNamespace(
        status=Defect.Status.OPEN,
        assigned_to=None,
        resolution='',
        verification_execution_id=None,
    )
    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.IN_PROGRESS)


def test_defecto_no_pasa_a_confirmation_sin_resolucion():
    defect = SimpleNamespace(
        status=Defect.Status.RESOLVED,
        assigned_to=object(),
        resolution='',
        verification_execution_id=None,
    )
    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.PENDING_CONFIRMATION)


def test_defecto_no_puede_cerrarse_con_confirmacion_fallida():
    verification = SimpleNamespace(result=TestExecution.Result.FAILED)
    defect = SimpleNamespace(
        status=Defect.Status.PENDING_CONFIRMATION,
        assigned_to=object(),
        resolution='Corregido',
        verification_execution_id=10,
        verification_execution=verification,
    )
    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.CLOSED)


def test_riesgo_no_puede_mitigarse_sin_estrategia():
    incident = SimpleNamespace(
        status=Incident.Status.OPEN,
        mitigation_strategy='',
    )
    with pytest.raises(ValidationError):
        incident_transition_allowed(incident, Incident.Status.MITIGATED)


def test_riesgo_puede_mitigarse_con_estrategia():
    incident = SimpleNamespace(
        status=Incident.Status.OPEN,
        mitigation_strategy='Aplicar monitoreo y plan de contingencia.',
    )
    assert incident_transition_allowed(incident, Incident.Status.MITIGATED)


def test_raise_if_invalid_lanza_error():
    result = SimpleNamespace(ok=False, errors=('Regla inválida.',))
    with pytest.raises(ValidationError):
        raise_if_invalid(result)


def test_raise_if_invalid_devuelve_resultado_valido():
    result = SimpleNamespace(ok=True, errors=())
    assert raise_if_invalid(result) is result


def test_upload_rechaza_archivo_inexistente():
    result = validate_file_upload(None, ('.pdf',), 1024)
    assert not result.ok

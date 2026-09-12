import pytest
from django.core.exceptions import ValidationError

from apps.core.lifecycle import (
    status_transition_for_requirement,
    status_transition_for_test_case,
    execution_transition_allowed,
    incident_transition_allowed,
)
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.executions.models import TestExecution
from apps.incidents.models import Incident


@pytest.mark.django_db
def test_requisito_no_puede_saltar_directamente_de_pendiente_a_aprobado(requirement):
    requirement.status = Requirement.Status.PENDING
    with pytest.raises(ValidationError):
        status_transition_for_requirement(requirement, Requirement.Status.APPROVED)


@pytest.mark.django_db
def test_requisito_puede_volver_de_revision_a_pendiente(requirement):
    requirement.status = Requirement.Status.REVIEW
    assert status_transition_for_requirement(requirement, Requirement.Status.PENDING)


@pytest.mark.django_db
def test_caso_no_puede_saltar_de_pendiente_a_aprobado(test_case):
    test_case.status = TestCase.Status.PENDING
    with pytest.raises(ValidationError):
        status_transition_for_test_case(test_case, TestCase.Status.PASSED)


@pytest.mark.django_db
def test_caso_listo_puede_iniciar_ejecucion(test_case):
    test_case.status = TestCase.Status.READY
    assert status_transition_for_test_case(test_case, TestCase.Status.RUNNING)


@pytest.mark.django_db
def test_caso_completado_puede_volver_a_listo_si_se_requiere_reejecucion(test_case):
    # READY exige que el requisito asociado esté aprobado.
    test_case.requirement.status = Requirement.Status.APPROVED
    test_case.requirement.save(update_fields=['status'])
    test_case.status = TestCase.Status.PASSED
    assert status_transition_for_test_case(test_case, TestCase.Status.READY)


@pytest.mark.django_db
def test_ejecucion_no_puede_saltar_de_no_ejecutada_a_aprobada(test_case):
    execution = TestExecution.objects.create(test_case=test_case)
    with pytest.raises(ValidationError):
        execution_transition_allowed(execution, TestExecution.Result.PASSED)


@pytest.mark.django_db
def test_ejecucion_en_progreso_puede_finalizar(test_case):
    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.RUNNING,
    )
    assert execution_transition_allowed(execution, TestExecution.Result.PASSED)


@pytest.mark.django_db
def test_riesgo_no_puede_mitigarse_sin_estrategia(project, user):
    incident = Incident.objects.create(
        project=project,
        code='INC-LIFE-001',
        title='Riesgo de prueba',
        description='Descripción',
        reported_by=user,
    )
    with pytest.raises(ValidationError):
        incident_transition_allowed(incident, Incident.Status.MITIGATED)


@pytest.mark.django_db
def test_riesgo_mitigado_puede_cerrarse(project, user):
    incident = Incident.objects.create(
        project=project,
        code='INC-LIFE-002',
        title='Riesgo mitigado',
        description='Descripción',
        mitigation_strategy='Aplicar control preventivo.',
        status=Incident.Status.MITIGATED,
        reported_by=user,
    )
    assert incident_transition_allowed(incident, Incident.Status.CLOSED)


@pytest.mark.django_db
def test_resultado_de_ejecucion_actualiza_estado_del_caso(test_case):
    from apps.executions.models import TestExecution
    from apps.core.lifecycle import sync_test_case_status_from_execution

    test_case.status = TestCase.Status.RUNNING
    test_case.save()
    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.PASSED,
    )
    assert sync_test_case_status_from_execution(test_case, execution) == TestCase.Status.PASSED
    test_case.refresh_from_db()
    assert test_case.status == TestCase.Status.PASSED


@pytest.mark.django_db
def test_error_tecnico_bloquea_el_caso(test_case):
    from apps.executions.models import TestExecution
    from apps.core.lifecycle import sync_test_case_status_from_execution

    test_case.status = TestCase.Status.RUNNING
    test_case.save()
    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.ERROR,
    )
    sync_test_case_status_from_execution(test_case, execution)
    test_case.refresh_from_db()
    assert test_case.status == TestCase.Status.BLOCKED


@pytest.mark.django_db
def test_resultado_de_ejecucion_revisada_sincroniza_caso(test_case):
    from apps.executions.models import TestExecution
    from apps.executions.services.review import recalculate_execution_from_steps
    from apps.executions.models import TestStepExecution

    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.NOT_RUN,
    )
    TestStepExecution.objects.create(
        test_execution=execution,
        step_number=1,
        action='Validar',
        expected_result='OK',
        status=TestExecution.Result.PASSED,
    )
    recalculate_execution_from_steps(execution)
    test_case.refresh_from_db()
    assert test_case.status == TestCase.Status.PASSED

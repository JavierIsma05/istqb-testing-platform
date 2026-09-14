import pytest
from django.core.exceptions import ValidationError

from apps.core.lifecycle import (
    status_transition_for_requirement,
    status_transition_for_test_case,
    execution_transition_allowed,
    incident_transition_allowed,
    sync_test_case_status_from_execution,
    defect_transition_allowed,
    defect_transition_from_confirmation,
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
def test_ejecucion_fallida_reabre_cadena_en_siguiente_intento(test_case):
    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.RUNNING,
    )
    assert execution_transition_allowed(execution, TestExecution.Result.FAILED)
    test_case.status = TestCase.Status.RUNNING
    test_case.save(update_fields=['status'])
    execution.result = TestExecution.Result.FAILED
    execution.save(update_fields=['result'])
    assert sync_test_case_status_from_execution(test_case, execution) == TestCase.Status.FAILED
    test_case.refresh_from_db()
    assert test_case.status == TestCase.Status.FAILED
    test_case.requirement.status = Requirement.Status.APPROVED
    test_case.requirement.save(update_fields=['status'])
    assert status_transition_for_test_case(test_case, TestCase.Status.READY)


@pytest.mark.django_db
def test_ejecucion_de_regresion_permite_validar_una_correccion(test_case, user):
    test_case.requirement.status = Requirement.Status.APPROVED
    test_case.requirement.save(update_fields=['status'])
    test_case.status = TestCase.Status.PASSED
    test_case.save(update_fields=['status'])
    first = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        execution_type=TestExecution.ExecutionType.NORMAL,
        result=TestExecution.Result.FAILED,
    )
    regression = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        execution_type=TestExecution.ExecutionType.REGRESSION,
        result=TestExecution.Result.PASSED,
        related_defect=None,
    )
    assert first.result == TestExecution.Result.FAILED
    assert regression.result == TestExecution.Result.PASSED
    assert sync_test_case_status_from_execution(test_case, regression) == TestCase.Status.PASSED


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
    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.PASSED,
    )
    test_case.status = TestCase.Status.RUNNING
    test_case.save(update_fields=['status'])
    assert sync_test_case_status_from_execution(test_case, execution) == TestCase.Status.PASSED
    test_case.refresh_from_db()
    assert test_case.status == TestCase.Status.PASSED


@pytest.mark.django_db
def test_error_tecnico_bloquea_el_caso(test_case):
    test_case.status = TestCase.Status.RUNNING
    test_case.save(update_fields=['status'])
    execution = TestExecution.objects.create(
        test_case=test_case,
        result=TestExecution.Result.ERROR,
    )
    sync_test_case_status_from_execution(test_case, execution)
    test_case.refresh_from_db()
    assert test_case.status == TestCase.Status.BLOCKED


@pytest.mark.django_db
def test_resultado_de_ejecucion_revisada_sincroniza_caso(test_case):
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


@pytest.mark.django_db
def test_defecto_resuelto_exige_responsable_y_resolucion(project, test_case, user):
    from apps.defects.models import Defect
    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-LIFE-001',
        title='Defecto',
        description='Falla reproducible.',
        reported_by=user,
        status=Defect.Status.OPEN,
    )
    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.IN_PROGRESS)
    defect.assigned_to = user
    defect.save(update_fields=['assigned_to'])
    defect_transition_allowed(defect, Defect.Status.IN_PROGRESS)
    defect.status = Defect.Status.IN_PROGRESS
    defect.resolution = 'Corrección aplicada.'
    defect.save(update_fields=['status', 'resolution'])
    defect_transition_allowed(defect, Defect.Status.RESOLVED)


@pytest.mark.django_db
def test_confirmacion_fallida_reabre_defecto(project, test_case, user):
    from apps.defects.models import Defect
    defect = Defect.objects.create(
        project=project, test_case=test_case, code='DEF-CONF-001',
        title='Defecto', description='Pendiente de confirmar.',
        reported_by=user, assigned_to=user,
        resolution='Corrección aplicada.', status=Defect.Status.PENDING_CONFIRMATION,
    )
    execution = TestExecution.objects.create(
        test_case=test_case, related_defect=defect,
        execution_type=TestExecution.ExecutionType.CONFIRMATION,
        result=TestExecution.Result.FAILED,
    )
    assert defect_transition_from_confirmation(defect, execution) == Defect.Status.REOPENED


@pytest.mark.django_db
def test_confirmacion_aprobada_cierra_defecto(project, test_case, user):
    from apps.defects.models import Defect
    defect = Defect.objects.create(
        project=project, test_case=test_case, code='DEF-CONF-002',
        title='Defecto corregido', description='Listo para confirmar.',
        reported_by=user, assigned_to=user,
        resolution='Corrección aplicada.', status=Defect.Status.PENDING_CONFIRMATION,
    )
    execution = TestExecution.objects.create(
        test_case=test_case, related_defect=defect,
        execution_type=TestExecution.ExecutionType.CONFIRMATION,
        result=TestExecution.Result.PASSED,
    )
    defect.verification_execution = execution
    assert defect_transition_from_confirmation(defect, execution) == Defect.Status.CLOSED
    defect.verification_execution = execution
    defect.status = Defect.Status.PENDING_CONFIRMATION
    assert defect_transition_allowed(defect, Defect.Status.CLOSED)


@pytest.mark.django_db
def test_defecto_no_puede_cerrarse_directamente_desde_resuelto(project, test_case, user):
    from apps.defects.models import Defect

    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-CONF-003',
        title='Cierre sin confirmación',
        description='Debe requerir una prueba de confirmación.',
        reported_by=user,
        assigned_to=user,
        resolution='Corrección aplicada.',
        status=Defect.Status.RESOLVED,
    )

    with pytest.raises(ValidationError):
        defect_transition_allowed(defect, Defect.Status.CLOSED)


@pytest.mark.django_db
def test_confirmacion_debe_estar_vinculada_al_defecto(project, test_case, user):
    from apps.defects.models import Defect

    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-CONF-004',
        title='Confirmación incorrecta',
        description='La ejecución debe pertenecer al defecto.',
        reported_by=user,
        assigned_to=user,
        resolution='Corrección aplicada.',
        status=Defect.Status.PENDING_CONFIRMATION,
    )
    other_defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-CONF-005',
        title='Otro defecto',
        description='Otro defecto.',
        reported_by=user,
        assigned_to=user,
        resolution='Corrección aplicada.',
        status=Defect.Status.PENDING_CONFIRMATION,
    )
    execution = TestExecution.objects.create(
        test_case=test_case,
        related_defect=other_defect,
        execution_type=TestExecution.ExecutionType.CONFIRMATION,
        result=TestExecution.Result.PASSED,
    )

    with pytest.raises(ValidationError):
        defect_transition_from_confirmation(defect, execution)


@pytest.mark.django_db
def test_confirmacion_no_puede_cerrar_defecto_si_no_es_tipo_confirmacion(project, test_case, user):
    from apps.defects.models import Defect

    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-CONF-006',
        title='Ejecución normal no confirma',
        description='Una ejecución normal no puede cerrar el defecto.',
        reported_by=user,
        assigned_to=user,
        resolution='Corrección aplicada.',
        status=Defect.Status.PENDING_CONFIRMATION,
    )
    execution = TestExecution.objects.create(
        test_case=test_case,
        related_defect=defect,
        execution_type=TestExecution.ExecutionType.NORMAL,
        result=TestExecution.Result.PASSED,
    )

    with pytest.raises(ValidationError):
        defect_transition_from_confirmation(defect, execution)

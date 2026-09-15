import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.defects.models import Defect
from apps.executions.models import AutomatedExecutionResult, AutomatedValidationRule, TestExecution
from apps.testplans.models import TestPlan


@pytest.mark.django_db
def test_ejecucion_normal_no_puede_vincular_un_defecto(test_case, execution):
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        test_case=test_case,
        execution=execution,
        code='DEF-INTEGRITY-001',
        title='Defecto para integridad',
        description='Validar vínculo de ejecución.',
    )
    invalid = TestExecution(
        test_case=test_case,
        execution_type=TestExecution.ExecutionType.NORMAL,
        related_defect=defect,
    )

    with pytest.raises(ValidationError, match='solo puede asociarse mediante una prueba de confirmación'):
        invalid.save()


@pytest.mark.django_db
def test_ejecucion_no_puede_vincular_defecto_de_otro_proyecto(test_case, execution, user):
    from apps.projects.models import Project

    other_project = Project.objects.create(
        code='PRJ-INTEGRITY-001',
        name='Proyecto de integridad',
        created_by=user,
    )
    other_case = test_case.__class__.objects.create(
        test_plan=TestPlan.objects.create(
            project=other_project,
            name='Plan integridad',
            objective='Validar integridad.',
            created_by=user,
        ),
        requirement=test_case.requirement.__class__.objects.create(
            project=other_project,
            code='REQ-INTEGRITY-001',
            title='Requisito integridad',
            description='Requisito de prueba.',
        ),
        code='TC-INTEGRITY-001',
        title='Caso integridad',
        steps='Paso 1',
        expected_result='Correcto',
    )
    defect = Defect.objects.create(
        project=other_project,
        test_case=other_case,
        code='DEF-INTEGRITY-002',
        title='Defecto externo',
        description='No debe poder asociarse.',
    )
    invalid = TestExecution(
        test_case=test_case,
        execution_type=TestExecution.ExecutionType.CONFIRMATION,
        related_defect=defect,
    )

    with pytest.raises(ValidationError, match='mismo proyecto'):
        invalid.save()


@pytest.mark.django_db
def test_regla_automatizada_debe_usar_requisito_principal(test_case, project):
    other_requirement = test_case.requirement.__class__.objects.create(
        project=project,
        code='REQ-INTEGRITY-002',
        title='Otro requisito',
        description='No corresponde al caso.',
    )
    rule = AutomatedValidationRule(
        test_case=test_case,
        requirement=other_requirement,
        step_number=99,
        name='Regla inconsistente',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
    )

    with pytest.raises(ValidationError, match='requisito principal'):
        rule.save()


@pytest.mark.django_db
def test_resultado_automatizado_debe_pertenecer_a_ejecucion_automatizada(test_case, execution):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=98,
        name='Regla válida',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
    )
    result = AutomatedExecutionResult(
        test_execution=execution,
        validation_rule=rule,
        status=TestExecution.Result.PASSED,
    )

    with pytest.raises(ValidationError, match='ejecución automatizada'):
        result.save()


@pytest.mark.django_db
def test_ejecucion_rechaza_fecha_de_finalizacion_anterior_al_inicio(test_case):
    start = timezone.now()
    execution = TestExecution(
        test_case=test_case,
        started_at=start,
        finished_at=start - timezone.timedelta(minutes=1),
    )

    with pytest.raises(ValidationError, match='finalización'):
        execution.save()

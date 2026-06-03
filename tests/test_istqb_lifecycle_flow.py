import pytest

from apps.defects.models import Defect
from apps.executions.models import TestExecution as ExecutionModel
from apps.reports.models import Report
from apps.traceability.models import TraceabilityLink


@pytest.mark.django_db
def test_flujo_completo_del_ciclo_de_pruebas_istqb(
    project,
    requirement,
    test_plan,
    test_case,
    user,
):
    traceability_link = TraceabilityLink.objects.create(
        requirement=requirement,
        test_case=test_case,
        rationale='El caso de prueba cubre el requisito funcional principal.',
    )

    execution = ExecutionModel.objects.create(
        test_case=test_case,
        executed_by=user,
        result=ExecutionModel.Result.FAILED,
        notes='El flujo falla al validar credenciales correctas.',
    )

    defect = Defect.objects.create(
        project=project,
        execution=execution,
        code='DEF-FLOW-001',
        title='Login falla con credenciales validas',
        description='Durante la ejecucion del caso se detecto un fallo funcional.',
        severity=Defect.Severity.HIGH,
        priority=Defect.Priority.CRITICAL,
        reported_by=user,
    )

    report = Report.objects.create(
        project=project,
        title='Reporte del flujo ISTQB',
        report_type=Report.ReportType.EXECUTION,
        generated_by=user,
        content={
            'requirements': 1,
            'test_cases': 1,
            'failed_executions': 1,
            'open_defects': 1,
        },
    )

    assert traceability_link.requirement == requirement
    assert traceability_link.test_case == test_case
    assert execution.result == ExecutionModel.Result.FAILED
    assert defect.status == Defect.Status.OPEN
    assert defect.execution == execution
    assert report.content == {
        'requirements': 1,
        'test_cases': 1,
        'failed_executions': 1,
        'open_defects': 1,
    }

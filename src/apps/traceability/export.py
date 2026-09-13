import csv

from django.http import HttpResponse

from apps.core.permissions import visible_projects_for
from apps.executions.models import TestExecution
from apps.traceability.services import calculate_project_metrics


COMPLETED_RESULTS = [
    TestExecution.Result.PASSED,
    TestExecution.Result.FAILED,
    TestExecution.Result.BLOCKED,
    TestExecution.Result.ERROR,
]


def export_traceability_indicators_csv(request):
    visible_projects = visible_projects_for(request.user, request=request)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="indicadores_trazabilidad.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Codigo proyecto',
        'Proyecto',
        'Total requisitos',
        'Total casos de prueba',
        'Total ejecuciones',
        'Cobertura de requisitos (%)',
        'Cobertura de ejecucion (%)',
        'Casos ejecutados (%)',
    ])

    for project in visible_projects:
        metrics = calculate_project_metrics(project)
        writer.writerow([
            project.code,
            project.name,
            metrics['total_requirements'],
            metrics['total_test_cases'],
            metrics['total_executions'],
            metrics['requirement_coverage_percentage'],
            metrics['execution_coverage_percentage'],
            metrics['test_case_execution_coverage_percentage'],
        ])

    return response

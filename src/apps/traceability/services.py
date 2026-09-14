from apps.executions.models import TestExecution


COMPLETED_RESULTS = [
    TestExecution.Result.PASSED,
    TestExecution.Result.FAILED,
    TestExecution.Result.BLOCKED,
    TestExecution.Result.ERROR,
]


def _completed_execution_case_ids(project):
    return set(
        TestExecution.objects.filter(
            test_case__test_plan__project=project,
            result__in=COMPLETED_RESULTS,
        ).values_list('test_case_id', flat=True)
    )


def _completed_execution_requirement_ids(project):
    return set(
        TestExecution.objects.filter(
            test_case__test_plan__project=project,
            result__in=COMPLETED_RESULTS,
            test_case__requirement__isnull=False,
        ).values_list('test_case__requirement_id', flat=True)
    )


def calculate_project_metrics(project, requirements=None, rows=None):
    """Calculate the project-level indicators used by the traceability UI/export.

    Coverage is based on the project artifacts actually linked to test cases,
    while execution coverage considers only completed execution outcomes.
    The same definitions are used regardless of whether the matrix is built
    from direct requirement links or explicit traceability links.
    """
    requirements = list(requirements or project.requirements.all())
    scoped_rows = [row for row in (rows or []) if row['requirement'].project_id == project.pk]

    case_ids = {row['case'].pk for row in scoped_rows if row.get('case') is not None}
    traced_requirement_ids = {
        row['requirement'].pk
        for row in scoped_rows
        if row.get('case') is not None
    }

    completed_case_ids = _completed_execution_case_ids(project)
    completed_requirement_ids = _completed_execution_requirement_ids(project)

    executed_case_ids = case_ids & completed_case_ids
    executed_requirement_ids = traced_requirement_ids & completed_requirement_ids

    total_requirements = len(requirements)
    total_test_cases = len(case_ids)

    return {
        'project': project,
        'total_requirements': total_requirements,
        'total_test_cases': total_test_cases,
        'total_executions': TestExecution.objects.filter(
            test_case__test_plan__project=project
        ).count(),
        'requirement_coverage_percentage': round(
            len(traced_requirement_ids) * 100 / total_requirements, 1
        ) if total_requirements else 0,
        'execution_coverage_percentage': round(
            len(executed_requirement_ids) * 100 / total_requirements, 1
        ) if total_requirements else 0,
        'test_case_execution_coverage_percentage': round(
            len(executed_case_ids) * 100 / total_test_cases, 1
        ) if total_test_cases else 0,
    }


def calculate_visible_project_metrics(projects, requirements, rows):
    """Calculate indicators only for projects visible to the current user."""
    return [
        calculate_project_metrics(
            project,
            [item for item in requirements if item.project_id == project.pk],
            rows,
        )
        for project in projects
    ]

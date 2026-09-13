from apps.executions.models import TestExecution


COMPLETED_RESULTS = [
    TestExecution.Result.PASSED,
    TestExecution.Result.FAILED,
    TestExecution.Result.BLOCKED,
    TestExecution.Result.ERROR,
]


def calculate_project_metrics(project, requirements=None, rows=None):
    """Calculate the project-level indicators used by the traceability UI/export."""
    requirements = list(requirements or project.requirements.all())
    rows = [row for row in (rows or []) if row['requirement'].project_id == project.pk]

    case_ids = {row['case'].pk for row in rows if row['case'] is not None}
    executed_case_ids = {
        row['case'].pk
        for row in rows
        if row['case'] is not None and row['execution'] is not None
    }
    traced_requirement_ids = {
        row['requirement'].pk for row in rows if row['case'] is not None
    }
    executed_requirement_ids = {
        row['requirement'].pk for row in rows if row['execution'] is not None
    }
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

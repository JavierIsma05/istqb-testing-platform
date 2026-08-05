from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Prefetch, Subquery
from django.shortcuts import render

from apps.core.permissions import visible_projects_for
from apps.executions.models import TestExecution
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase


# Solo estas ejecuciones cuentan como completadas dentro de la matriz.
# RUNNING y NOT_RUN no reemplazan la ultima ejecucion completada de un caso.
COMPLETED_RESULTS = [
    TestExecution.Result.PASSED,
    TestExecution.Result.FAILED,
    TestExecution.Result.BLOCKED,
    TestExecution.Result.ERROR,
]

COMMON_RESULTS = [
    TestExecution.Result.PASSED,
    TestExecution.Result.FAILED,
    TestExecution.Result.BLOCKED,
    TestExecution.Result.ERROR,
    TestExecution.Result.RUNNING,
    TestExecution.Result.NOT_RUN,
]


@login_required
def traceability_matrix_view(request):
    visible_projects = visible_projects_for(request.user, request=request)

    latest_completed_pk = TestExecution.objects.filter(
        test_case=OuterRef('pk'),
        result__in=COMPLETED_RESULTS,
    ).order_by('-executed_at', '-created_at').values('pk')[:1]

    test_cases_with_risk = TestCase.objects.select_related('test_plan').annotate(
        latest_completed_pk=Subquery(latest_completed_pk),
    )

    requirements = list(
        Requirement.objects.select_related('project').prefetch_related(
            Prefetch('test_cases', queryset=test_cases_with_risk),
            Prefetch('traceability_links__test_case', queryset=test_cases_with_risk),
        ).filter(project__in=visible_projects)
    )

    requirement_cases = []
    latest_execution_ids = set()

    for requirement in requirements:
        direct_cases = list(requirement.test_cases.all())
        linked_cases = [link.test_case for link in requirement.traceability_links.all()]
        test_cases_by_id = {test_case.id: test_case for test_case in direct_cases + linked_cases}
        test_cases = list(test_cases_by_id.values())

        requirement_cases.append((requirement, test_cases))
        for test_case in test_cases:
            if test_case.latest_completed_pk:
                latest_execution_ids.add(test_case.latest_completed_pk)

    latest_executions = {
        execution.id: execution
        for execution in TestExecution.objects.filter(pk__in=latest_execution_ids).prefetch_related('defects')
    }

    rows = []
    plans = set()
    cases = set()
    defects = set()
    result_count = 0

    for requirement, test_cases in requirement_cases:
        if not test_cases:
            rows.append(
                {
                    'requirement': requirement,
                    'plan': None,
                    'case': None,
                    'execution': None,
                    'defects': [],
                }
            )
            continue

        for test_case in test_cases:
            execution = latest_executions.get(test_case.latest_completed_pk)
            plan = test_case.test_plan
            plans.add(plan)
            cases.add(test_case)
            if execution:
                result_count += 1
            row_defects = list(test_case.defects.all())
            if execution:
                row_defects += list(execution.defects.all())
            defects.update(row_defects)
            rows.append(
                {
                    'requirement': requirement,
                    'plan': plan,
                    'case': test_case,
                    'execution': execution,
                    'defects': row_defects,
                }
            )

    return render(
        request,
        'traceability/index.html',
        {
            'rows': rows,
            'total_requirements': len(requirements),
            'total_plans': len(plans),
            'total_test_cases': len(cases),
            'total_executions': len(latest_executions),
            'total_results': result_count,
            'total_defects': len(defects),
        },
    )
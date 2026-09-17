from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Prefetch, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.core.lifecycle import status_transition_for_test_case
from apps.core.permissions import can_manage_artifacts, visible_projects_for
from apps.executions.models import TestExecution
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.traceability.services import calculate_visible_project_metrics

COMPLETED_RESULTS = [TestExecution.Result.PASSED, TestExecution.Result.FAILED, TestExecution.Result.BLOCKED, TestExecution.Result.ERROR]


@login_required
@require_POST
def reopen_test_case_view(request, pk):
    """Reabre un caso terminado para una nueva ejecución y conserva todo el historial."""
    test_case = get_object_or_404(
        TestCase.objects.select_related('test_plan__project'),
        pk=pk,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    if not can_manage_artifacts(request.user):
        messages.error(request, 'No tienes permisos para reabrir casos de prueba.')
        return redirect('traceability:index')
    if test_case.status not in {TestCase.Status.PASSED, TestCase.Status.FAILED, TestCase.Status.BLOCKED}:
        messages.error(request, 'Solo se puede reabrir un caso que ya tenga una ejecución finalizada.')
        return redirect('traceability:index')
    try:
        status_transition_for_test_case(test_case, TestCase.Status.READY)
    except ValidationError as exc:
        messages.error(request, str(exc))
        return redirect('traceability:index')
    test_case.status = TestCase.Status.READY
    test_case.reexecution_requested = True
    test_case.save(update_fields=['status', 'reexecution_requested', 'updated_at'])
    log_action(request.user, 'UPDATE', 'TestCase', test_case.pk, {
        'project_id': test_case.test_plan.project_id,
        'test_case_id': test_case.pk,
        'status': test_case.status,
        'reexecution_requested': True,
        'source': 'traceability_reopen_for_reexecution',
    })
    messages.success(request, f'Caso {test_case.code} reabierto para una nueva ejecución. El historial anterior se conserva.')

    execution_url = f'{reverse("executions:index")}?case={test_case.pk}&project={test_case.test_plan.project_id}'
    if test_case.execution_type == TestCase.ExecutionType.AUTOMATED:
        execution_url += '#automation'
    else:
        execution_url += '#execucion-manual'
    return redirect(execution_url)


@login_required
def traceability_matrix_view(request):
    visible_projects = visible_projects_for(request.user, request=request)
    latest_completed_pk = TestExecution.objects.filter(test_case=OuterRef('pk'), result__in=COMPLETED_RESULTS).order_by('-executed_at', '-created_at').values('pk')[:1]
    test_cases_with_risk = TestCase.objects.select_related('test_plan').annotate(latest_completed_pk=Subquery(latest_completed_pk))
    requirements = list(Requirement.objects.select_related('project').prefetch_related(Prefetch('test_cases', queryset=test_cases_with_risk), Prefetch('traceability_links__test_case', queryset=test_cases_with_risk)).filter(project__in=visible_projects))
    requirement_cases = []
    latest_execution_ids = set()
    for requirement in requirements:
        direct_cases = list(requirement.test_cases.all())
        linked_cases = [link.test_case for link in requirement.traceability_links.all()]
        link_by_case = {link.test_case_id: link for link in requirement.traceability_links.all()}
        test_cases_by_id = {test_case.id: test_case for test_case in direct_cases + linked_cases}
        test_cases = list(test_cases_by_id.values())
        requirement_cases.append((requirement, test_cases))
        for test_case in test_cases:
            if test_case.latest_completed_pk:
                latest_execution_ids.add(test_case.latest_completed_pk)
    latest_executions = {execution.id: execution for execution in TestExecution.objects.filter(pk__in=latest_execution_ids).prefetch_related('defects')}
    rows = []
    plans = set()
    cases = set()
    defects = set()
    result_count = 0
    for requirement, test_cases in requirement_cases:
        if not test_cases:
            rows.append({'requirement': requirement, 'plan': None, 'case': None, 'execution': None, 'defects': [], 'rationale': ''})
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
            rows.append({
                'requirement': requirement,
                'plan': plan,
                'case': test_case,
                'execution': execution,
                'defects': row_defects,
                'rationale': getattr(link_by_case.get(test_case.pk), 'rationale', '') or '',
            })
    executed_test_case_ids = {row['case'].pk for row in rows if row['case'] is not None and row['execution'] is not None}
    total_execution_history = TestExecution.objects.filter(test_case__test_plan__project__in=visible_projects).count()
    traced_requirement_ids = {row['requirement'].pk for row in rows if row['case'] is not None}
    requirements_with_completed_execution = {row['requirement'].pk for row in rows if row['execution'] is not None}
    requirement_coverage_percentage = round((len(traced_requirement_ids) / len(requirements)) * 100, 1) if requirements else 0
    execution_coverage_percentage = round((len(requirements_with_completed_execution) / len(requirements)) * 100, 1) if requirements else 0
    project_metrics = calculate_visible_project_metrics(visible_projects, requirements, rows)
    return render(request, 'traceability/index.html', {
        'rows': rows,
        'project_metrics': project_metrics,
        'total_requirements': len(requirements),
        'total_plans': len(plans),
        'total_test_cases': len(cases),
        'total_executions': total_execution_history,
        'latest_execution_snapshots': len(latest_executions),
        'total_results': result_count,
        'total_defects': len(defects),
        'traced_requirements': len(traced_requirement_ids),
        'requirements_with_completed_execution': len(requirements_with_completed_execution),
        'requirement_coverage_percentage': requirement_coverage_percentage,
        'execution_coverage_percentage': execution_coverage_percentage,
        'end_to_end_traced_requirements': len(requirements_with_completed_execution),
        'end_to_end_traceability_percentage': execution_coverage_percentage,
        'executed_test_cases': len(executed_test_case_ids),
        'test_case_execution_coverage_percentage': round((len(executed_test_case_ids) / len(cases)) * 100, 1) if cases else 0,
        'can_manage': can_manage_artifacts(request.user),
    })

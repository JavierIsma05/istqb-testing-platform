from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count

from apps.core.permissions import visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.testcases.models import TestCase


CONFIRMATION_CANDIDATE_STATUSES = {
    Defect.Status.IN_PROGRESS,
    Defect.Status.RESOLVED,
    Defect.Status.REOPENED,
}


def build_execution_calendar(projects):
    today = timezone.localdate()
    rows = []

    recorded_executions = TestExecution.objects.select_related(
        'test_case',
        'test_case__test_plan',
        'test_case__test_plan__project',
        'related_defect',
    ).filter(
        test_case__test_plan__project__in=projects,
        executed_at__isnull=False,
    ).order_by('-executed_at')[:50]

    for execution in recorded_executions:
        rows.append({
            'date': timezone.localtime(execution.executed_at).date(),
            'time': timezone.localtime(execution.executed_at).time(),
            'type': execution.get_execution_type_display(),
            'project': execution.test_case.test_plan.project,
            'test_case': execution.test_case,
            'defect': execution.related_defect or execution.defects.first(),
            'reason': f'Ejecución registrada: {execution.get_result_display()}',
            'result': execution.result,
            'result_label': execution.get_result_display(),
            'is_recorded': True,
            'execution': execution,
        })

    pending_cases = TestCase.objects.select_related(
        'test_plan', 'test_plan__project', 'requirement'
    ).filter(
        test_plan__project__in=projects,
        status__in=[TestCase.Status.PENDING, TestCase.Status.BLOCKED],
    ).order_by('test_plan__project__end_date', 'priority', 'code')[:20]

    for index, test_case in enumerate(pending_cases):
        rows.append({
            'date': today + timedelta(days=index),
            'time': None,
            'type': TestExecution.ExecutionType.NORMAL.label,
            'project': test_case.test_plan.project,
            'test_case': test_case,
            'defect': None,
            'reason': 'Caso pendiente de ejecucion',
            'result': '',
            'result_label': 'Pendiente',
            'is_recorded': False,
            'execution': None,
        })

    confirmation_defects = Defect.objects.select_related(
        'project', 'test_case'
    ).filter(
        project__in=projects,
        status__in=CONFIRMATION_CANDIDATE_STATUSES,
    ).order_by('-updated_at')[:20]

    for index, defect in enumerate(confirmation_defects):
        rows.append({
            'date': today + timedelta(days=index + 1),
            'time': None,
            'type': TestExecution.ExecutionType.CONFIRMATION.label,
            'project': defect.project,
            'test_case': defect.test_case,
            'defect': defect,
            'reason': 'Confirmar corrección del defecto',
            'result': '',
            'result_label': 'Planificada',
            'is_recorded': False,
            'execution': None,
        })

    regression_cases = TestCase.objects.select_related(
        'test_plan', 'test_plan__project', 'requirement'
    ).filter(
        test_plan__project__in=projects,
        status=TestCase.Status.PASSED,
    ).annotate(
        defect_count=Count('executions__defects', distinct=True)
    ).filter(
        defect_count__gt=0
    ).order_by('-updated_at')[:20]

    for index, test_case in enumerate(regression_cases):
        rows.append({
            'date': today + timedelta(days=index + 2),
            'time': None,
            'type': TestExecution.ExecutionType.REGRESSION.label,
            'project': test_case.test_plan.project,
            'test_case': test_case,
            'defect': None,
            'reason': 'Verificar que la corrección no afectó funcionalidad existente',
            'result': '',
            'result_label': 'Planificada',
            'is_recorded': False,
            'execution': None,
        })

    return sorted(
        rows,
        key=lambda row: (
            row['date'],
            0 if row['is_recorded'] else 1,
            row['project'].name,
            row['type'],
        ),
        reverse=True,
    )


@login_required
def execution_calendar_view(request):
    projects = visible_projects_for(request.user, request=request).order_by('name')
    selected_project_id = request.GET.get('project', '').strip()
    selected_projects = projects.filter(pk=selected_project_id) if selected_project_id else projects

    return render(
        request,
        'executions/calendar.html',
        {
            'projects': projects,
            'selected_project': selected_project_id,
            'calendar_items': build_execution_calendar(selected_projects),
        },
    )

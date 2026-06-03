from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.core.permissions import can_manage_artifacts, is_teacher, visible_projects_for
from apps.executions.models import TestExecution
from apps.testcases.models import TestCase

from .forms import ExecutionResultForm


RESULT_TO_CASE_STATUS = {
    'PASSED': TestCase.Status.PASSED,
    'FAILED': TestCase.Status.FAILED,
    'BLOCKED': TestCase.Status.BLOCKED,
}


def sync_case_status_from_last_execution(test_case):
    last_execution = test_case.executions.first()
    if last_execution:
        test_case.status = RESULT_TO_CASE_STATUS.get(last_execution.result, TestCase.Status.PENDING)
    else:
        test_case.status = TestCase.Status.PENDING
    test_case.save(update_fields=['status', 'updated_at'])


def is_image_evidence(evidence):
    if not evidence:
        return False

    return evidence.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))


@login_required
def execution_workspace_view(request):
    case_id = request.GET.get('case')
    test_cases = TestCase.objects.select_related('requirement', 'test_plan', 'created_by').order_by('code')
    test_cases = test_cases.filter(test_plan__project__in=visible_projects_for(request.user))

    if request.method == 'POST' and is_teacher(request.user):
        return redirect(request.path)

    if case_id:
        selected_case = test_cases.filter(id=case_id).first()
    else:
        selected_case = (
            test_cases.filter(status=TestCase.Status.PENDING).first()
            or test_cases.first()
        )

    form = ExecutionResultForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and selected_case and form.is_valid():
        execution = form.save(commit=False)
        execution.test_case = selected_case
        execution.executed_by = request.user
        execution.executed_at = timezone.now()
        execution.save()

        selected_case.status = RESULT_TO_CASE_STATUS.get(execution.result, TestCase.Status.PENDING)
        selected_case.save(update_fields=['status', 'updated_at'])

        return redirect(f'{request.path}?case={selected_case.id}')

    executions = selected_case.executions.select_related('executed_by') if selected_case else TestCase.objects.none()
    execution_history = [
        {
            'execution': execution,
            'evidence_is_image': is_image_evidence(execution.evidence),
        }
        for execution in executions
    ]
    last_execution = execution_history[0]['execution'] if execution_history else None
    execution_total = len(execution_history)
    passed_count = sum(1 for item in execution_history if item['execution'].result == 'PASSED')
    failed_count = sum(1 for item in execution_history if item['execution'].result == 'FAILED')
    success_percent = round((passed_count / execution_total) * 100) if execution_total else 0

    return render(
        request,
        'executions/index.html',
        {
            'form': form,
            'selected_case': selected_case,
            'test_cases': test_cases,
            'last_execution': last_execution,
            'last_execution_evidence_is_image': is_image_evidence(last_execution.evidence) if last_execution else False,
            'execution_history': execution_history,
            'execution_total': execution_total,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'success_percent': success_percent,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def execution_delete_view(request, pk):
    if request.method != 'POST':
        return redirect('executions:index')

    if is_teacher(request.user):
        return redirect('executions:index')

    execution = get_object_or_404(
        TestExecution.objects.select_related('test_case', 'test_case__test_plan__project'),
        pk=pk,
        test_case__test_plan__project__in=visible_projects_for(request.user),
    )
    test_case = execution.test_case
    execution.delete()
    sync_case_status_from_last_execution(test_case)
    messages.success(request, 'Ejecucion eliminada correctamente.')

    return redirect(f'{reverse("executions:index")}?case={test_case.id}')

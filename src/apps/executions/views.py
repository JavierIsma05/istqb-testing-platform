from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.core.permissions import can_manage_artifacts, is_teacher, visible_projects_for
from apps.testcases.models import TestCase

from .forms import ExecutionResultForm


RESULT_TO_CASE_STATUS = {
    'PASSED': TestCase.Status.PASSED,
    'FAILED': TestCase.Status.FAILED,
    'BLOCKED': TestCase.Status.BLOCKED,
}


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

    return render(
        request,
        'executions/index.html',
        {
            'form': form,
            'selected_case': selected_case,
            'test_cases': test_cases,
            'last_execution': selected_case.executions.first() if selected_case else None,
            'can_manage': can_manage_artifacts(request.user),
        },
    )

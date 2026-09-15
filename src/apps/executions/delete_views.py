from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect

from apps.audit.services import log_action
from apps.core.permissions import is_teacher, visible_projects_for
from apps.executions.models import TestExecution


@login_required
def execution_delete_view(request, pk):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')

    execution = get_object_or_404(
        TestExecution.objects.select_related('test_case', 'test_case__test_plan__project'),
        pk=pk,
        test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    if not request.user.is_superuser and execution.executed_by_id != request.user.id:
        messages.error(request, 'Solo puedes eliminar tus propias ejecuciones.')
        return redirect(f'{reverse("executions:index")}?case={execution.test_case_id}')

    protected = (
        execution.review_status != TestExecution.ReviewStatus.PENDING
        or execution.result != TestExecution.Result.NOT_RUN
        or execution.step_executions.exists()
        or execution.automated_results.exists()
        or bool(execution.evidence)
        or bool(execution.step_results)
        or bool(execution.actual_result.strip())
        or bool(execution.technical_log.strip())
        or execution.related_defect_id is not None
    )
    if protected:
        messages.error(
            request,
            'Esta ejecución ya contiene evidencia, resultados o asociaciones de trazabilidad y no puede eliminarse. Registra una nueva ejecución para conservar el historial ISTQB.',
        )
        return redirect(f'{reverse("executions:index")}?case={execution.test_case_id}')

    test_case = execution.test_case
    log_action(
        request.user,
        'DELETE',
        'TestExecution',
        execution.pk,
        {
            'project_id': test_case.test_plan.project_id,
            'test_case_id': test_case.pk,
            'result': execution.result,
            'review_status': execution.review_status,
            'execution_mode': execution.execution_mode,
        },
    )
    execution.delete()
    messages.success(request, 'Ejecución eliminada correctamente.')
    return redirect(f'{reverse("executions:index")}?case={test_case.id}')

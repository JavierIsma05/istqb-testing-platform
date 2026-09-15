from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from apps.audit.services import log_action
from apps.core.permissions import is_teacher, visible_projects_for
from apps.core.lifecycle import sync_test_case_status_from_execution
from apps.executions.models import AutomatedValidationRule, TestExecution
from apps.testcases.models import TestCase

from .forms import AutomatedStepForm
from .services.automated_runner import run_automated_execution


@login_required
def automated_rule_create_view(request, case_id):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')

    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan__project'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    form = AutomatedStepForm(request.POST, test_case=test_case)
    if form.is_valid():
        rule = form.save(commit=False)
        rule.test_case = test_case
        rule.requirement = test_case.requirement
        rule.save()
        log_action(
            request.user,
            'CREATE',
            'AutomatedValidationRule',
            rule.pk,
            {
                'test_case_id': test_case.pk,
                'action_type': rule.action_type,
            },
        )
        messages.success(request, 'Paso automatizado registrado correctamente.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')


@login_required
def automated_rule_delete_view(request, pk):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')

    rule = get_object_or_404(
        AutomatedValidationRule.objects.select_related('test_case__test_plan__project'),
        pk=pk,
        test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    test_case_id = rule.test_case_id
    if rule.execution_results.exists():
        rule.is_active = False
        rule.save(update_fields=['is_active', 'updated_at'])
        messages.info(request, 'El paso automatizado tiene historial y fue desactivado en lugar de eliminarse.')
    else:
        rule.delete()
        messages.success(request, 'Paso automatizado eliminado.')
    return redirect(f'{reverse("executions:index")}?case={test_case_id}#automation')


@login_required
def automated_execution_run_view(request, case_id):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')

    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan__project'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    if not test_case.has_approved_requirement:
        messages.error(request, test_case.execution_block_reason)
        return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

    execution = run_automated_execution(test_case, request.user)
    sync_test_case_status_from_execution(test_case, execution)
    if execution.result == TestExecution.Result.FAILED:
        messages.warning(request, 'La ejecucion fallo y se genero un defecto asociado.')
    elif execution.result == TestExecution.Result.PASSED:
        messages.success(request, 'Todos los pasos automatizados aprobaron.')
    else:
        messages.warning(request, f'Ejecución finalizada con estado {execution.get_result_display()}.')
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

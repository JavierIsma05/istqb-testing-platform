from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.core.lifecycle import sync_test_case_status_from_execution, validate_execution_repeat
from apps.core.permissions import is_teacher, visible_projects_for
from apps.executions.models import AutomatedValidationRule, TestExecution
from apps.testcases.models import TestCase

from .forms import AutomatedStepForm
from .services.automated_runner import run_automated_execution
from .services.automatizacion import ejecutar_caso_automatizado


@login_required
@require_POST
def ejecutar_automatizado(request, caso_id):
    if is_teacher(request.user):
        return JsonResponse({'ok': False, 'errores': 'Los docentes no ejecutan casos automatizados desde este flujo.'}, status=403)
    try:
        resultado = ejecutar_caso_automatizado(caso_id, request.user)
        resultado['ok'] = True
        return JsonResponse(resultado)
    except Exception as exc:
        return JsonResponse({'ok': False, 'errores': str(exc)}, status=500)


@login_required
@require_POST
def automated_rule_create_view(request, case_id):
    if is_teacher(request.user):
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
        last_step = test_case.automated_rules.order_by('-step_number').values_list('step_number', flat=True).first()
        rule.step_number = (last_step or 0) + 1
        rule.save()
        log_action(request.user, 'CREATE', 'AutomatedValidationRule', rule.pk, {
            'test_case_id': test_case.pk,
            'action_type': rule.action_type,
            'execution_mode': TestExecution.ExecutionMode.AUTOMATED,
        })
        messages.success(request, 'Paso automatizado registrado correctamente.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')


@login_required
@require_POST
def automated_rule_delete_view(request, pk):
    if is_teacher(request.user):
        return redirect('executions:index')
    rule = get_object_or_404(
        AutomatedValidationRule.objects.select_related('test_case__test_plan__project'),
        pk=pk,
        test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    test_case_id = rule.test_case_id
    had_history = rule.execution_results.exists()
    if had_history:
        rule.is_active = False
        rule.save(update_fields=['is_active', 'updated_at'])
        log_action(request.user, 'UPDATE', 'AutomatedValidationRule', rule.pk, {
            'test_case_id': test_case_id,
            'action': 'DEACTIVATE_WITH_HISTORY',
            'execution_mode': TestExecution.ExecutionMode.AUTOMATED,
        })
        messages.info(request, 'El paso automatizado tiene historial y fue desactivado en lugar de eliminarse.')
    else:
        log_action(request.user, 'DELETE', 'AutomatedValidationRule', rule.pk, {
            'test_case_id': test_case_id,
            'action': 'DELETE_WITHOUT_HISTORY',
            'execution_mode': TestExecution.ExecutionMode.AUTOMATED,
        })
        rule.delete()
        messages.success(request, 'Paso automatizado eliminado.')
    return redirect(f'{reverse("executions:index")}?case={test_case_id}#automation')


@login_required
@require_POST
def automated_execution_run_view(request, case_id):
    """Ejecuta exclusivamente el flujo automatizado; no reutiliza el formulario manual."""
    if is_teacher(request.user):
        return redirect('executions:index')

    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan__project'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )

    if not test_case.has_approved_requirement:
        messages.error(request, test_case.execution_block_reason)
        return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

    active_rules = list(test_case.automated_rules.filter(is_active=True).order_by('step_number', 'id'))
    if not active_rules:
        messages.error(request, 'El caso de prueba no tiene pasos automatizados activos para ejecutar.')
        return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

    # La automatización tiene su propio historial y no debe crear una segunda
    # ejecución normal equivalente a la ya registrada manualmente. Si existe,
    # se conserva el historial y se obliga a usar el propósito de regresión o
    # confirmación desde el flujo específico correspondiente.
    repeat_validation = validate_execution_repeat(
        test_case,
        TestExecution.ExecutionType.NORMAL,
        'Ejecución automatizada por pasos',
    )
    if not repeat_validation.ok:
        messages.warning(
            request,
            'Ya existe una ejecución normal equivalente para este caso. '
            'La automatización no se mezclará con ese historial; usa un flujo de regresión o confirmación cuando corresponda.',
        )
        return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

    try:
        execution = run_automated_execution(test_case, request.user)
    except Exception as exc:
        log_action(request.user, 'ERROR', 'TestExecution', test_case.pk, {
            'project_id': test_case.test_plan.project_id,
            'test_case_id': test_case.pk,
            'source': 'automated_execution',
            'execution_mode': TestExecution.ExecutionMode.AUTOMATED,
            'error': str(exc)[:500],
        })
        messages.error(request, 'La ejecución automatizada no pudo completarse. Revisa el registro de auditoría o los datos de configuración.')
        return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

    # Contrato explícito: este endpoint jamás debe devolver una ejecución manual.
    if execution.execution_mode != TestExecution.ExecutionMode.AUTOMATED:
        execution.execution_mode = TestExecution.ExecutionMode.AUTOMATED
        execution.save(update_fields=['execution_mode', 'updated_at'])
        raise RuntimeError('El motor automatizado devolvió una ejecución con modo incorrecto.')

    sync_test_case_status_from_execution(test_case, execution)
    if execution.result == TestExecution.Result.FAILED:
        messages.warning(request, 'La ejecución automatizada finalizó con fallos y se registró el defecto trazable.')
    elif execution.result == TestExecution.Result.BLOCKED:
        messages.warning(request, 'La ejecución automatizada quedó bloqueada.')
    elif execution.result == TestExecution.Result.ERROR:
        messages.error(request, 'La ejecución automatizada finalizó con un error técnico.')
    else:
        messages.success(request, 'Ejecución automatizada completada correctamente.')
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

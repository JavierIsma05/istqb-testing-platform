from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, is_teacher, visible_projects_for
from apps.defects.history import record_defect_history
from apps.defects.models import Defect
from apps.executions.models import AutomatedValidationRule, TestExecution, TestStepExecution
from apps.testcases.models import TestCase

from .forms import AutomatedValidationRuleForm, ExecutionResultForm, ExecutionReviewForm
from .services.automated_runner import run_automated_execution


RESULT_TO_CASE_STATUS = {
    'PASSED': TestCase.Status.PASSED,
    'FAILED': TestCase.Status.FAILED,
    'BLOCKED': TestCase.Status.BLOCKED,
    'ERROR': TestCase.Status.BLOCKED,
}

CONFIRMATION_CANDIDATE_STATUSES = {
    Defect.Status.IN_PROGRESS,
    Defect.Status.PENDING_CONFIRMATION,
}


def split_test_steps(test_case):
    if test_case.steps_data:
        return test_case.steps_data
    return [
        {
            'number': index + 1,
            'action': line.strip(),
            'expected_result': test_case.expected_result,
        }
        for index, line in enumerate((test_case.steps or '').splitlines())
        if line.strip()
    ]


def build_step_results(test_case, post_data):
    results = []
    errors = []
    test_steps = split_test_steps(test_case)
    if not test_steps:
        return [], ['El caso de prueba no tiene pasos ejecutables definidos.']
    for index, step in enumerate(test_steps):
        actual_result = (post_data.get(f'step_actual_{index}') or '').strip()
        status = (post_data.get(f'step_status_{index}') or '').strip()
        comment = (post_data.get(f'step_comment_{index}') or '').strip()
        if not actual_result:
            errors.append(f'Registra el resultado obtenido del paso {index + 1}.')
        if status not in {
            TestExecution.Result.PASSED,
            TestExecution.Result.FAILED,
            TestExecution.Result.BLOCKED,
        }:
            errors.append(f'Selecciona un estado valido para el paso {index + 1}.')
        if status in {TestExecution.Result.FAILED, TestExecution.Result.BLOCKED} and not comment:
            errors.append(f'Agrega un comentario para justificar el paso {index + 1}.')
        results.append(
            {
                'number': index + 1,
                'action': step['action'],
                'expected_result': step['expected_result'],
                'actual_result': actual_result,
                'status': status,
                'comment': comment,
            }
        )
    return results, errors


def aggregate_step_result(step_results):
    statuses = {step['status'] for step in step_results}
    if TestExecution.Result.FAILED in statuses:
        return TestExecution.Result.FAILED
    if TestExecution.Result.BLOCKED in statuses:
        return TestExecution.Result.BLOCKED
    return TestExecution.Result.PASSED


def summarize_step_results(step_results):
    return '\n'.join(
        f"Paso {step['number']} [{step['status']}]: {step['actual_result']}"
        for step in step_results
    )


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


def create_defect_from_failed_execution(execution):
    from apps.core.codes import next_code

    project = execution.test_case.test_plan.project
    title = f'Fallo en {execution.test_case.code}: {execution.test_case.title}'[:180]
    test_data = execution.test_data or execution.test_case.test_data or 'No registrados'
    environment = execution.environment or execution.test_case.test_plan.environment or 'No registrado'
    description = (
        f'Caso de prueba: {execution.test_case.code} - {execution.test_case.title}\n\n'
        f'Resultado esperado:\n{execution.test_case.expected_result}\n\n'
        f'Resultado obtenido:\n{execution.actual_result or "No registrado"}\n\n'
        f'Datos usados:\n{test_data}\n\n'
        f'Ambiente:\n{environment}'
    )

    defect = Defect.objects.create(
        project=project,
        execution=execution,
        code=next_code(Defect.objects.filter(project=project), 'DEF'),
        title=title,
        description=description,
        severity=Defect.Severity.MEDIUM,
        priority=Defect.Priority.MEDIUM,
        reported_by=execution.executed_by,
    )
    record_defect_history(defect, execution.executed_by, 'Defecto creado desde ejecucion fallida')
    log_action(
        execution.executed_by,
        'CREATE',
        'Defect',
        defect.pk,
        {
            'project_id': project.pk,
            'code': defect.code,
            'title': defect.title,
            'status': defect.status,
            'source': 'failed_execution',
            'execution_id': execution.pk,
        },
    )
    return defect


def sync_defect_from_confirmation(execution):
    defect = execution.related_defect
    if not defect or execution.execution_type != TestExecution.ExecutionType.CONFIRMATION:
        return

    if execution.result == TestExecution.Result.PASSED:
        defect.status = Defect.Status.CLOSED
    elif execution.result == TestExecution.Result.FAILED:
        defect.status = Defect.Status.IN_PROGRESS
    else:
        defect.status = Defect.Status.PENDING_CONFIRMATION

    defect.save(update_fields=['status', 'updated_at'])
    record_defect_history(defect, execution.executed_by, 'Actualizacion desde prueba de confirmacion')
    log_action(
        execution.executed_by,
        'UPDATE',
        'Defect',
        defect.pk,
        {
            'project_id': defect.project_id,
            'code': defect.code,
            'status': defect.status,
            'source': 'confirmation_execution',
            'execution_id': execution.pk,
        },
    )


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
            'reason': f'Ejecucion registrada: {execution.get_result_display()}',
            'result': execution.result,
            'result_label': execution.get_result_display(),
            'is_recorded': True,
            'execution': execution,
        })

    pending_cases = TestCase.objects.select_related('test_plan', 'test_plan__project', 'requirement').filter(
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

    confirmation_defects = Defect.objects.select_related('project', 'execution__test_case').filter(
        project__in=projects,
        status__in=CONFIRMATION_CANDIDATE_STATUSES,
    ).order_by('-updated_at')[:20]

    for index, defect in enumerate(confirmation_defects):
        test_case = defect.execution.test_case if defect.execution else None
        rows.append({
            'date': today + timedelta(days=index + 1),
            'time': None,
            'type': TestExecution.ExecutionType.CONFIRMATION.label,
            'project': defect.project,
            'test_case': test_case,
            'defect': defect,
            'reason': 'Confirmar correccion del defecto',
            'result': '',
            'result_label': 'Planificada',
            'is_recorded': False,
            'execution': None,
        })

    regression_cases = TestCase.objects.select_related('test_plan', 'test_plan__project', 'requirement').filter(
        test_plan__project__in=projects,
        status=TestCase.Status.PASSED,
    ).annotate(defect_count=Count('executions__defects', distinct=True)).filter(defect_count__gt=0).order_by('-updated_at')[:20]

    for index, test_case in enumerate(regression_cases):
        rows.append({
            'date': today + timedelta(days=index + 2),
            'time': None,
            'type': TestExecution.ExecutionType.REGRESSION.label,
            'project': test_case.test_plan.project,
            'test_case': test_case,
            'defect': None,
            'reason': 'Verificar que la correccion no afecto funcionalidad existente',
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
def execution_workspace_view(request):
    case_id = request.GET.get('case')
    test_cases = TestCase.objects.select_related('requirement', 'test_plan', 'created_by').order_by('code')
    test_cases = test_cases.filter(test_plan__project__in=visible_projects_for(request.user))

    if case_id:
        selected_case = test_cases.filter(id=case_id).first()
    else:
        selected_case = (
            test_cases.filter(status=TestCase.Status.PENDING).first()
            or test_cases.first()
        )

    step_results = []
    step_errors = []
    form_data = request.POST or None
    if request.method == 'POST' and selected_case and not is_teacher(request.user):
        step_results, step_errors = build_step_results(selected_case, request.POST)
        form_data = request.POST.copy()
        form_data['result'] = aggregate_step_result(step_results)
        if not (form_data.get('actual_result') or '').strip():
            form_data['actual_result'] = summarize_step_results(step_results)

    form = ExecutionResultForm(form_data, request.FILES or None, test_case=selected_case)

    if request.method == 'POST' and is_teacher(request.user):
        execution = get_object_or_404(
            TestExecution,
            pk=request.POST.get('execution_id'),
            test_case__test_plan__project__in=visible_projects_for(request.user),
        )
        review_form = ExecutionReviewForm(request.POST, instance=execution)
        if review_form.is_valid():
            reviewed_execution = review_form.save(commit=False)
            reviewed_execution.reviewed_by = request.user
            reviewed_execution.reviewed_at = timezone.now()
            reviewed_execution.save()
            log_action(
                request.user,
                'REVIEW',
                'TestExecution',
                reviewed_execution.pk,
                {
                    'project_id': reviewed_execution.test_case.test_plan.project_id,
                    'test_case_id': reviewed_execution.test_case_id,
                    'review_status': reviewed_execution.review_status,
                },
            )
            messages.success(request, 'Revision de ejecucion registrada correctamente.')
        return redirect(f'{request.path}?case={execution.test_case.id}')

    if request.method == 'POST' and selected_case and step_errors:
        for error in step_errors:
            form.add_error(None, error)

    if request.method == 'POST' and selected_case and not step_errors and form.is_valid():
        execution = form.save(commit=False)
        execution.test_case = selected_case
        execution.execution_mode = TestExecution.ExecutionMode.MANUAL
        execution.executed_by = request.user
        execution.executed_at = timezone.now()
        execution.step_results = step_results
        execution.save()
        TestStepExecution.objects.bulk_create(
            [
                TestStepExecution(
                    test_execution=execution,
                    step_number=step['number'],
                    action=step['action'],
                    expected_result=step['expected_result'],
                    obtained_result=step['actual_result'],
                    status=step['status'],
                    comment=step['comment'],
                    started_at=execution.executed_at,
                    finished_at=execution.executed_at,
                )
                for step in step_results
            ]
        )
        log_action(
            request.user,
            'CREATE',
            'TestExecution',
            execution.pk,
            {
                'project_id': selected_case.test_plan.project_id,
                'test_case_id': selected_case.pk,
                'result': execution.result,
                'execution_type': execution.execution_type,
                'related_defect_id': execution.related_defect_id,
                'environment': execution.environment,
            },
        )

        sync_defect_from_confirmation(execution)

        if (
            execution.result == TestExecution.Result.FAILED
            and execution.execution_type != TestExecution.ExecutionType.CONFIRMATION
        ):
            create_defect_from_failed_execution(execution)
            messages.warning(request, 'Se registro la ejecucion fallida y se creo un defecto asociado.')
        elif (
            execution.result == TestExecution.Result.FAILED
            and execution.execution_type == TestExecution.ExecutionType.CONFIRMATION
        ):
            messages.warning(request, 'La prueba de confirmacion fallo y el defecto volvio a correccion.')
        else:
            messages.success(request, 'Resultado de ejecucion registrado correctamente.')

        selected_case.status = RESULT_TO_CASE_STATUS.get(execution.result, TestCase.Status.PENDING)
        selected_case.save(update_fields=['status', 'updated_at'])

        return redirect(f'{request.path}?case={selected_case.id}')

    executions = (
        selected_case.executions.select_related('executed_by').prefetch_related('automated_results__validation_rule')
        if selected_case
        else TestCase.objects.none()
    )
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
    test_steps = split_test_steps(selected_case) if selected_case else []
    review_form = ExecutionReviewForm(instance=last_execution) if last_execution else None
    automated_rules = (
        selected_case.automated_rules.filter(is_active=True)
        if selected_case
        else AutomatedValidationRule.objects.none()
    )
    last_automated_execution = (
        selected_case.executions.filter(
            execution_mode=TestExecution.ExecutionMode.SEMI_AUTOMATED
        ).prefetch_related('automated_results__validation_rule').first()
        if selected_case
        else None
    )
    rule_form = AutomatedValidationRuleForm(test_case=selected_case) if selected_case else None

    return render(
        request,
        'executions/index.html',
        {
            'form': form,
            'selected_case': selected_case,
            'test_cases': test_cases,
            'last_execution': last_execution,
            'review_form': review_form,
            'last_execution_evidence_is_image': is_image_evidence(last_execution.evidence) if last_execution else False,
            'execution_history': execution_history,
            'execution_total': execution_total,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'success_percent': success_percent,
            'test_steps': test_steps,
            'automated_rules': automated_rules,
            'last_automated_execution': last_automated_execution,
            'rule_form': rule_form,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def execution_calendar_view(request):
    projects = visible_projects_for(request.user).order_by('name')
    selected_project_id = request.GET.get('project', '').strip()
    selected_projects = projects

    if selected_project_id:
        selected_projects = projects.filter(pk=selected_project_id)

    return render(
        request,
        'executions/calendar.html',
        {
            'projects': projects,
            'selected_project': selected_project_id,
            'calendar_items': build_execution_calendar(selected_projects),
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
    if not request.user.is_superuser and execution.executed_by_id != request.user.id:
        messages.error(request, 'Solo puedes eliminar tus propias ejecuciones.')
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
    sync_case_status_from_last_execution(test_case)
    messages.success(request, 'Ejecucion eliminada correctamente.')

    return redirect(f'{reverse("executions:index")}?case={test_case.id}')


@login_required
def automated_rule_create_view(request, case_id):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')

    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan__project'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user),
    )
    form = AutomatedValidationRuleForm(request.POST, test_case=test_case)
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
            {'test_case_id': test_case.pk, 'validation_type': rule.validation_type},
        )
        messages.success(request, 'Regla automatizada registrada correctamente.')
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
        test_case__test_plan__project__in=visible_projects_for(request.user),
    )
    test_case_id = rule.test_case_id
    if rule.execution_results.exists():
        rule.is_active = False
        rule.save(update_fields=['is_active', 'updated_at'])
        messages.info(request, 'La regla tiene historial y fue desactivada en lugar de eliminarse.')
    else:
        rule.delete()
        messages.success(request, 'Regla automatizada eliminada.')
    return redirect(f'{reverse("executions:index")}?case={test_case_id}#automation')


@login_required
def automated_execution_run_view(request, case_id):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')
    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan__project'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user),
    )
    execution = run_automated_execution(test_case, request.user)
    test_case.status = RESULT_TO_CASE_STATUS.get(execution.result, TestCase.Status.PENDING)
    test_case.save(update_fields=['status', 'updated_at'])
    if execution.result == TestExecution.Result.FAILED:
        messages.warning(request, 'La ejecucion fallo y se genero un defecto asociado.')
    elif execution.result == TestExecution.Result.PASSED:
        messages.success(request, 'Todas las reglas automatizadas aprobaron.')
    else:
        messages.warning(request, f'Ejecucion finalizada con estado {execution.get_result_display()}.')
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')

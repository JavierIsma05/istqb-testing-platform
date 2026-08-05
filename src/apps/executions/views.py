from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, is_teacher, visible_projects_for
from apps.defects.history import record_defect_history
from apps.defects.models import Defect
from apps.executions.models import AutomatedValidationRule, TestData, TestExecution, TestStepExecution
from apps.projects.models import Project
from apps.testcases.models import TestCase
from apps.users.models import User

from .forms import AutomatedStepForm, ExecutionResultForm, ExecutionReviewForm, TestDataForm
from .services.automated_runner import run_automated_execution


RESULT_TO_CASE_STATUS = {
    'PASSED': TestCase.Status.PASSED,
    'FAILED': TestCase.Status.FAILED,
    'BLOCKED': TestCase.Status.BLOCKED,
    'ERROR': TestCase.Status.BLOCKED,
}

CONFIRMATION_CANDIDATE_STATUSES = {
    Defect.Status.IN_PROGRESS,
    Defect.Status.RESOLVED,
    Defect.Status.REOPENED,
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
        test_case=execution.test_case,
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
        defect.status = Defect.Status.REOPENED

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
            'reason': f'Ejecución registrada: {execution.get_result_display()}',
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

    confirmation_defects = Defect.objects.select_related('project', 'test_case').filter(
        project__in=projects,
        status__in=CONFIRMATION_CANDIDATE_STATUSES,
    ).order_by('-updated_at')[:20]

    for index, defect in enumerate(confirmation_defects):
        test_case = defect.test_case
        rows.append({
            'date': today + timedelta(days=index + 1),
            'time': None,
            'type': TestExecution.ExecutionType.CONFIRMATION.label,
            'project': defect.project,
            'test_case': test_case,
            'defect': defect,
            'reason': 'Confirmar corrección del defecto',
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
def execution_workspace_view(request):
    is_teacher_user = is_teacher(request.user)
    case_id = request.GET.get('case')

    if is_teacher_user:
        projects = visible_projects_for(request.user, request=request).order_by('name')
        test_cases = TestCase.objects.none()
        selected_case = None
        if case_id:
            selected_case = TestCase.objects.select_related(
                'requirement', 'test_plan', 'test_plan__project', 'created_by',
            ).filter(
                pk=case_id,
                test_plan__project__in=visible_projects_for(request.user, request=request),
            ).first()
    else:
        test_cases = TestCase.objects.select_related(
            'requirement',
            'test_plan',
            'test_plan__project',
            'created_by',
        ).order_by('test_plan__project__name', 'code')
        test_cases = test_cases.filter(test_plan__project__in=visible_projects_for(request.user, request=request))

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
    if request.method == 'POST' and selected_case and not is_teacher_user:
        if not selected_case.has_approved_requirement:
            messages.error(request, selected_case.execution_block_reason)
            return redirect(f'{request.path}?case={selected_case.id}#execucion-manual')
        form_data = request.POST.copy()

    form = ExecutionResultForm(form_data, request.FILES or None, test_case=selected_case, user=request.user)

    if request.method == 'POST' and is_teacher_user:
        execution = get_object_or_404(
            TestExecution,
            pk=request.POST.get('execution_id'),
            test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
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
            messages.success(request, 'Revisión de ejecución registrada correctamente.')
        return redirect(f'{request.path}?case={execution.test_case.id}')

    if request.method == 'POST' and selected_case and form.is_valid():
        execution = form.save(commit=False)
        execution.test_case = selected_case
        execution.execution_mode = TestExecution.ExecutionMode.MANUAL
        execution.executed_by = request.user
        execution.executed_at = timezone.now()
        execution.step_results = []
        execution.save()
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
            messages.warning(request, 'La prueba de confirmación falló y el defecto volvió a corrección.')
        else:
            messages.success(request, 'Resultado de ejecucion registrado correctamente.')

        selected_case.status = RESULT_TO_CASE_STATUS.get(execution.result, TestCase.Status.PENDING)
        selected_case.save(update_fields=['status', 'updated_at'])

        return redirect(f'{request.path}?case={selected_case.id}')

    executions = (
        selected_case.executions.select_related('executed_by').prefetch_related(
            'automated_results__validation_rule',
            'step_executions',
        )
        if selected_case
        else TestCase.objects.none()
    )
    manual_history = [
        {
            'execution': execution,
            'evidence_is_image': is_image_evidence(execution.evidence),
        }
        for execution in executions
        if execution.execution_mode == TestExecution.ExecutionMode.MANUAL
    ]
    automated_history = [
        {
            'execution': execution,
            'evidence_is_image': is_image_evidence(execution.evidence),
        }
        for execution in executions
        if execution.execution_mode == TestExecution.ExecutionMode.AUTOMATED
    ]
    last_execution = manual_history[0]['execution'] if manual_history else None
    last_automated_execution = automated_history[0]['execution'] if automated_history else None
    manual_count = len(manual_history)
    automated_count = len(automated_history)
    execution_total = manual_count + automated_count
    passed_count = sum(
        1
        for item in [*manual_history, *automated_history]
        if item['execution'].result == 'PASSED'
    )
    failed_count = sum(
        1
        for item in [*manual_history, *automated_history]
        if item['execution'].result == 'FAILED'
    )
    success_percent = round((passed_count / execution_total) * 100) if execution_total else 0
    test_steps = split_test_steps(selected_case) if selected_case else []
    review_form = ExecutionReviewForm(instance=last_execution) if last_execution else None
    automated_rules = (
        selected_case.automated_rules.filter(is_active=True)
        if selected_case
        else AutomatedValidationRule.objects.none()
    )
    step_form = AutomatedStepForm(test_case=selected_case) if selected_case else None
    test_data_form = TestDataForm() if selected_case else None
    test_data_list = selected_case.test_data_vars.all() if selected_case else TestData.objects.none()

    return render(
        request,
        'executions/index.html',
        {
            'form': form,
            'selected_case': selected_case,
            'case_blocked': bool(selected_case and not selected_case.has_approved_requirement),
            'case_block_reason': selected_case.execution_block_reason if selected_case else '',
            'test_cases': test_cases if not is_teacher_user else TestCase.objects.none(),
            'last_execution': last_execution,
            'review_form': review_form,
            'last_execution_evidence_is_image': is_image_evidence(last_execution.evidence) if last_execution else False,
            'execution_history': [*manual_history, *automated_history],
            'manual_history': manual_history,
            'automated_history': automated_history,
            'manual_count': manual_count,
            'automated_count': automated_count,
            'execution_total': execution_total,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'success_percent': success_percent,
            'test_steps': test_steps,
            'automated_rules': automated_rules,
            'last_automated_execution': last_automated_execution,
            'step_form': step_form,
            'test_data_form': test_data_form,
            'test_data_list': test_data_list,
            'can_manage': can_manage_artifacts(request.user),
            'is_teacher': is_teacher_user,
            'teacher_projects': projects if is_teacher_user else None,
        },
    )


@login_required
def execution_history_view(request, case_id):
    test_cases = TestCase.objects.select_related('requirement', 'test_plan', 'created_by').order_by('code')
    test_cases = test_cases.filter(test_plan__project__in=visible_projects_for(request.user, request=request))
    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan', 'test_plan__project', 'created_by'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    executions = test_case.executions.select_related('executed_by').prefetch_related(
        'automated_results__validation_rule',
        'step_executions',
    )
    manual_history = [
        {
            'execution': execution,
            'evidence_is_image': is_image_evidence(execution.evidence),
        }
        for execution in executions
        if execution.execution_mode == TestExecution.ExecutionMode.MANUAL
    ]
    automated_history = [
        {
            'execution': execution,
            'evidence_is_image': is_image_evidence(execution.evidence),
        }
        for execution in executions
        if execution.execution_mode == TestExecution.ExecutionMode.AUTOMATED
    ]
    total = len(manual_history) + len(automated_history)
    passed = sum(
        1
        for item in [*manual_history, *automated_history]
        if item['execution'].result == TestExecution.Result.PASSED
    )
    failed = sum(
        1
        for item in [*manual_history, *automated_history]
        if item['execution'].result == TestExecution.Result.FAILED
    )
    success_percent = round((passed / total) * 100) if total else 0

    return render(
        request,
        'executions/history.html',
        {
            'case': test_case,
            'test_cases': test_cases,
            'manual_history': manual_history,
            'automated_history': automated_history,
            'manual_count': len(manual_history),
            'automated_count': len(automated_history),
            'execution_total': total,
            'passed_count': passed,
            'failed_count': failed,
            'success_percent': success_percent,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def execution_calendar_view(request):
    projects = visible_projects_for(request.user, request=request).order_by('name')
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
        test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
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
    messages.success(request, 'Ejecución eliminada correctamente.')

    return redirect(f'{reverse("executions:index")}?case={test_case.id}')


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
    test_case.status = RESULT_TO_CASE_STATUS.get(execution.result, TestCase.Status.PENDING)
    test_case.save(update_fields=['status', 'updated_at'])
    if execution.result == TestExecution.Result.FAILED:
        messages.warning(request, 'La ejecucion fallo y se genero un defecto asociado.')
    elif execution.result == TestExecution.Result.PASSED:
        messages.success(request, 'Todos los pasos automatizados aprobaron.')
    else:
        messages.warning(request, f'Ejecución finalizada con estado {execution.get_result_display()}.')
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')


@login_required
def teacher_api_projects(request):
    if not is_teacher(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    projects = visible_projects_for(request.user, request=request).order_by('name')
    data = [{'id': p.pk, 'code': p.code, 'name': p.name} for p in projects]
    return JsonResponse(data, safe=False)


@login_required
def test_data_create_view(request, case_id):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')
    
    test_case = get_object_or_404(
        TestCase.objects.select_related('requirement', 'test_plan__project'),
        pk=case_id,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    form = TestDataForm(request.POST)
    if form.is_valid():
        data = form.save(commit=False)
        data.test_case = test_case
        data.save()
        messages.success(request, 'Variable de prueba registrada correctamente.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(f'{reverse("executions:index")}?case={test_case.id}#automation')


@login_required
def test_data_delete_view(request, pk):
    if request.method != 'POST' or is_teacher(request.user):
        return redirect('executions:index')
    
    data = get_object_or_404(
        TestData.objects.select_related('test_case__test_plan__project'),
        pk=pk,
        test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    test_case_id = data.test_case_id
    data.delete()
    messages.success(request, 'Variable de prueba eliminada.')
    return redirect(f'{reverse("executions:index")}?case={test_case_id}#automation')


@login_required
def teacher_api_students(request, project_id):
    if not is_teacher(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    project = get_object_or_404(
        Project.objects.prefetch_related('members'),
        pk=project_id,
    )
    students = project.members.filter(role=User.Roles.STUDENT).order_by('email')
    data = [
        {
            'id': s.pk,
            'email': s.email,
            'full_name': s.get_full_name() or s.email,
        }
        for s in students
    ]
    return JsonResponse(data, safe=False)


@login_required
def teacher_api_cases(request, project_id, student_id):
    if not is_teacher(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    project = get_object_or_404(
        Project.objects.all(),
        pk=project_id,
    )
    student = get_object_or_404(User.objects.all(), pk=student_id, role=User.Roles.STUDENT)
    if student not in project.members.all():
        return JsonResponse({'error': 'El estudiante no pertenece al proyecto'}, status=400)

    cases = TestCase.objects.filter(
        test_plan__project=project,
        created_by=student,
    ).select_related('test_plan').order_by('code')

    data = []
    for c in cases:
        last_exec = c.executions.order_by('-executed_at').first()
        data.append({
            'id': c.pk,
            'code': c.code,
            'title': c.title,
            'status': c.status,
            'status_label': c.get_status_display(),
            'plan': c.test_plan.name if c.test_plan else '',
            'total_execs': c.executions.count(),
            'last_result': last_exec.result if last_exec else None,
            'last_result_label': last_exec.get_result_display() if last_exec else 'Sin ejecutar',
            'last_executed_at': last_exec.executed_at.strftime('%d/%m/%Y %H:%M') if last_exec and last_exec.executed_at else None,
        })
    return JsonResponse(data, safe=False)

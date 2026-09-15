from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, is_teacher, visible_projects_for
from apps.executions.models import TestData, TestExecution, TestStepExecution
from apps.testcases.models import TestCase
from apps.users.models import User

from .forms import StepEvidenceForm, StepReviewForm, TestDataForm
from .services.review import recalculate_execution_from_steps


def _detail_url(pk):
    return reverse('executions:detail', kwargs={'pk': pk})


@login_required
def step_review_detail_view(request, pk):
    step = get_object_or_404(
        TestStepExecution.objects.select_related(
            'test_execution', 'test_execution__test_case',
            'test_execution__test_case__test_plan__project',
        ),
        pk=pk,
        test_execution__test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    execution = step.test_execution
    if not is_teacher(request.user) or request.method != 'POST':
        return redirect(_detail_url(execution.pk))
    if execution.review_status != TestExecution.ReviewStatus.PENDING:
        messages.error(request, 'La ejecución ya fue revisada y no admite cambios por paso.')
        return redirect(_detail_url(execution.pk))
    form = StepReviewForm(request.POST, instance=step)
    if form.is_valid():
        form.save()
        recalculate_execution_from_steps(execution)
        log_action(request.user, 'REVIEW', 'TestStepExecution', step.pk, {
            'execution_id': execution.pk,
            'step_number': step.step_number,
            'status': step.status,
        })
        messages.success(request, f'Revisión del paso {step.step_number} registrada.')
    else:
        messages.error(request, ' '.join(form.errors.as_text().splitlines()))
    return redirect(_detail_url(execution.pk))


@login_required
def step_evidence_upload_view(request, pk):
    step = get_object_or_404(
        TestStepExecution.objects.select_related(
            'test_execution', 'test_execution__test_case',
            'test_execution__test_case__test_plan__project',
        ),
        pk=pk,
        test_execution__test_case__test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    execution = step.test_execution
    if request.method != 'POST' or is_teacher(request.user):
        return redirect(_detail_url(execution.pk))
    if not request.user.is_superuser and execution.executed_by_id != request.user.id:
        messages.error(request, 'Solo quien registró la ejecución puede adjuntar evidencia por paso.')
        return redirect(_detail_url(execution.pk))
    if execution.review_status != TestExecution.ReviewStatus.PENDING:
        messages.error(request, 'La ejecución ya fue revisada y no admite cambios de evidencia.')
        return redirect(_detail_url(execution.pk))
    form = StepEvidenceForm(request.POST, request.FILES, instance=step)
    if form.is_valid():
        form.save()
        log_action(request.user, 'UPDATE', 'TestStepExecution', step.pk, {
            'execution_id': execution.pk,
            'step_number': step.step_number,
            'evidence': True,
        })
        messages.success(request, f'Evidencia del paso {step.step_number} guardada correctamente.')
    else:
        messages.error(request, ' '.join(form.errors.as_text().splitlines()))
    return redirect(_detail_url(execution.pk))


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
        log_action(request.user, 'CREATE', 'TestData', data.pk, {
            'test_case_id': test_case.pk,
            'name': data.name,
        })
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
    log_action(request.user, 'DELETE', 'TestData', data.pk, {
        'test_case_id': test_case_id,
        'name': data.name,
    })
    data.delete()
    messages.success(request, 'Variable de prueba eliminada.')
    return redirect(f'{reverse("executions:index")}?case={test_case_id}#automation')


@login_required
@require_GET
def teacher_api_projects(request):
    if not is_teacher(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    projects = visible_projects_for(request.user, request=request).order_by('name')
    data = [{'id': p.pk, 'code': p.code, 'name': p.name} for p in projects]
    return JsonResponse(data, safe=False)


@login_required
@require_GET
def teacher_api_students(request, project_id):
    if not is_teacher(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    project = get_object_or_404(
        visible_projects_for(request.user).prefetch_related('members'),
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
@require_GET
def teacher_api_cases(request, project_id, student_id):
    if not is_teacher(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    project = get_object_or_404(visible_projects_for(request.user), pk=project_id)
    student = get_object_or_404(User.objects.all(), pk=student_id, role=User.Roles.STUDENT)
    if not project.members.filter(pk=student.pk).exists():
        return JsonResponse({'error': 'El estudiante no pertenece al proyecto'}, status=400)
    cases = TestCase.objects.filter(
        test_plan__project=project,
        created_by=student,
    ).select_related('test_plan').order_by('code')
    data = []
    for case in cases:
        last_exec = case.executions.order_by('-executed_at').first()
        data.append({
            'id': case.pk,
            'code': case.code,
            'title': case.title,
            'status': case.status,
            'status_label': case.get_status_display(),
            'plan': case.test_plan.name if case.test_plan else '',
            'total_execs': case.executions.count(),
            'last_result': last_exec.result if last_exec else None,
            'last_result_label': last_exec.get_result_display() if last_exec else 'Sin ejecutar',
            'last_executed_at': last_exec.executed_at.strftime('%d/%m/%Y %H:%M') if last_exec and last_exec.executed_at else None,
        })
    return JsonResponse(data, safe=False)

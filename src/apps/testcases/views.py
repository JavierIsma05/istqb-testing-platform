from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_action
from apps.core.codes import next_code
from apps.core.permissions import (
    can_manage_artifacts,
    get_active_project_for_request,
    is_teacher,
    visible_projects_for,
)
from apps.drafts.services import clear_draft

from .forms import TestCaseModalForm
from .models import TestCase


STATUS_BADGES = {
    TestCase.Status.PENDING: 'warning',
    TestCase.Status.READY: 'primary',
    TestCase.Status.RUNNING: 'info',
    TestCase.Status.PASSED: 'success',
    TestCase.Status.FAILED: 'danger',
    TestCase.Status.BLOCKED: 'muted',
}


@login_required
def testcase_list_view(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    can_manage = can_manage_artifacts(request.user)
    form = TestCaseModalForm(request.POST or None, user=request.user)

    if request.method == 'POST' and is_teacher(request.user):
        return redirect('testcases:index')

    if request.method == 'POST' and form.is_valid():
        test_case = form.save(commit=False)
        test_case.code = next_code(
            TestCase.objects.filter(test_plan__project=test_case.test_plan.project),
            'TC',
        )
        test_case.created_by = request.user
        test_case.save()
        clear_draft(request.user, 'testcase', test_case.test_plan.project_id, 0)
        clear_draft(request.user, 'testcase', 0, 0)
        messages.success(request, 'Caso de prueba creado correctamente.')
        log_action(
            request.user,
            'CREATE',
            'TestCase',
            test_case.pk,
            {
                'project_id': test_case.test_plan.project_id,
                'test_plan_id': test_case.test_plan_id,
                'requirement_id': test_case.requirement_id,
                'code': test_case.code,
                'title': test_case.title,
            },
        )
        return redirect('testcases:index')

    visible_projects = visible_projects_for(request.user, request=request)
    active_project = get_active_project_for_request(request)
    test_cases = TestCase.objects.select_related(
        'test_plan',
        'test_plan__project',
        'requirement',
        'created_by',
    ).prefetch_related('covered_risks').annotate(
        execution_count=Count('executions', distinct=True),
        risk_count=Count('covered_risks', distinct=True),
    )
    test_cases = test_cases.filter(test_plan__project__in=visible_projects)

    if query:
        test_cases = test_cases.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(expected_result__icontains=query)
        )

    if active_project:
        test_cases = test_cases.filter(test_plan__project=active_project)

    if status:
        test_cases = test_cases.filter(status=status)

    if priority:
        test_cases = test_cases.filter(priority=priority)

    total = test_cases.count()
    passed = test_cases.filter(status=TestCase.Status.PASSED).count()
    failed = test_cases.filter(status=TestCase.Status.FAILED).count()
    pending = test_cases.filter(status__in=[TestCase.Status.PENDING, TestCase.Status.READY, TestCase.Status.RUNNING]).count()

    return render(
        request,
        'testcases/index.html',
        {
            'form': form,
            'items': [
                {
                    'case': test_case,
                    'badge': STATUS_BADGES.get(test_case.status, 'muted'),
                    'blocked': not test_case.has_approved_requirement,
                    'block_reason': test_case.execution_block_reason,
                }
                for test_case in test_cases
            ],
            'total': total,
            'passed': passed,
            'failed': failed,
            'pending': pending,
            'status_choices': TestCase.Status.choices,
            'priority_choices': TestCase.Priority.choices,
            'selected_status': status,
            'selected_priority': priority,
            'query': query,
            'can_manage': can_manage,
            'show_modal': request.method == 'POST' and form.errors,
        },
    )


@login_required
def testcase_detail_view(request, pk):
    test_case = get_object_or_404(
        TestCase.objects.select_related(
            'test_plan',
            'test_plan__project',
            'requirement',
            'created_by',
        ).prefetch_related('defects', 'executions__defects', 'traceability_links', 'covered_risks'),
        pk=pk,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    executions = test_case.executions.select_related('executed_by').prefetch_related('defects')
    defects = list(test_case.defects.all())
    seen_defects = {defect.pk for defect in defects}

    for execution in executions:
        for defect in execution.defects.all():
            if defect.pk not in seen_defects:
                defects.append(defect)
                seen_defects.add(defect.pk)

    return render(
        request,
        'testcases/detail.html',
        {
            'case': test_case,
            'executions': executions,
            'defects': defects,
            'risks': test_case.covered_risks.select_related('requirement', 'test_plan').order_by('code'),
            'execution_count': executions.count(),
            'can_manage': can_manage_artifacts(request.user),
            'case_blocked': not test_case.has_approved_requirement,
            'case_block_reason': test_case.execution_block_reason,
        },
    )


@login_required
def testcase_update_view(request, pk):
    if is_teacher(request.user):
        return redirect('testcases:index')

    test_case = get_object_or_404(
        TestCase,
        pk=pk,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )
    form = TestCaseModalForm(request.POST or None, instance=test_case, user=request.user)

    if request.method == 'POST' and form.is_valid():
        test_case = form.save()
        clear_draft(request.user, 'testcase', test_case.test_plan.project_id, test_case.pk)
        log_action(
            request.user,
            'UPDATE',
            'TestCase',
            test_case.pk,
            {
                'project_id': test_case.test_plan.project_id,
                'test_plan_id': test_case.test_plan_id,
                'requirement_id': test_case.requirement_id,
                'code': test_case.code,
                'title': test_case.title,
            },
        )
        messages.success(request, 'Caso de prueba actualizado correctamente.')
        return redirect('testcases:detail', pk=test_case.pk)

    return render(
        request,
        'testcases/form.html',
        {
            'form': form,
            'title': 'Editar Caso de Prueba',
            'subtitle': 'Actualiza pasos, resultado esperado, prioridad y trazabilidad del caso.',
        },
    )


@login_required
def testcase_delete_view(request, pk):
    if is_teacher(request.user):
        return redirect('testcases:index')

    test_case = get_object_or_404(
        TestCase,
        pk=pk,
        test_plan__project__in=visible_projects_for(request.user, request=request),
    )

    if request.method == 'POST':
        log_action(
            request.user,
            'DELETE',
            'TestCase',
            test_case.pk,
            {
                'project_id': test_case.test_plan.project_id,
                'test_plan_id': test_case.test_plan_id,
                'requirement_id': test_case.requirement_id,
                'code': test_case.code,
                'title': test_case.title,
            },
        )
        test_case.delete()
        messages.success(request, 'Caso de prueba eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('testcases:index')

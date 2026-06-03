from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.permissions import can_manage_artifacts, is_teacher, visible_projects_for

from .forms import TestCaseModalForm
from .models import TestCase


STATUS_BADGES = {
    TestCase.Status.PASSED: 'success',
    TestCase.Status.FAILED: 'danger',
    TestCase.Status.PENDING: 'warning',
    TestCase.Status.BLOCKED: 'muted',
}


@login_required
def testcase_list_view(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    can_manage = can_manage_artifacts(request.user)
    form = TestCaseModalForm(request.POST or None)

    if request.method == 'POST' and is_teacher(request.user):
        return redirect('testcases:index')

    if request.method == 'POST' and form.is_valid():
        test_case = form.save(commit=False)
        test_case.created_by = request.user
        test_case.save()
        return redirect('testcases:index')

    test_cases = TestCase.objects.select_related(
        'test_plan',
        'test_plan__project',
        'requirement',
        'created_by',
    ).annotate(execution_count=Count('executions', distinct=True))
    test_cases = test_cases.filter(test_plan__project__in=visible_projects_for(request.user))

    if query:
        test_cases = test_cases.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(expected_result__icontains=query)
        )

    if status:
        test_cases = test_cases.filter(status=status)

    if priority:
        test_cases = test_cases.filter(priority=priority)

    total = test_cases.count()
    passed = test_cases.filter(status=TestCase.Status.PASSED).count()
    failed = test_cases.filter(status=TestCase.Status.FAILED).count()
    pending = test_cases.filter(status=TestCase.Status.PENDING).count()

    return render(
        request,
        'testcases/index.html',
        {
            'form': form,
            'items': [
                {
                    'case': test_case,
                    'badge': STATUS_BADGES.get(test_case.status, 'muted'),
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
        ).prefetch_related('executions__defects', 'traceability_links'),
        pk=pk,
        test_plan__project__in=visible_projects_for(request.user),
    )
    executions = test_case.executions.select_related('executed_by').prefetch_related('defects')
    defects = []
    seen_defects = set()

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
            'execution_count': executions.count(),
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def testcase_update_view(request, pk):
    if is_teacher(request.user):
        return redirect('testcases:index')

    test_case = get_object_or_404(
        TestCase,
        pk=pk,
        test_plan__project__in=visible_projects_for(request.user),
    )
    form = TestCaseModalForm(request.POST or None, instance=test_case)

    if request.method == 'POST' and form.is_valid():
        form.save()
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
        test_plan__project__in=visible_projects_for(request.user),
    )

    if request.method == 'POST':
        test_case.delete()
        messages.success(request, 'Caso de prueba eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('testcases:index')

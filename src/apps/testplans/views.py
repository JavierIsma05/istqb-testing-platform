from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for

from .forms import TestPlanWizardForm
from .history import record_test_plan_version
from .models import TestPlan


STATUS_BADGES = {
    TestPlan.Status.APPROVED: 'success',
    TestPlan.Status.REVIEW: 'success',
    TestPlan.Status.DRAFT: 'warning',
    TestPlan.Status.CLOSED: 'muted',
}


@login_required
def testplan_list_view(request):
    plans = TestPlan.objects.select_related('project', 'created_by').annotate(
        risk_count=Count('risks', distinct=True),
        version_count=Count('versions', distinct=True),
    ).order_by('-created_at')
    plans = plans.filter(project__in=visible_projects_for(request.user, request=request))
    return render(
        request,
        'testplans/index.html',
        {
            'plans': [
                {
                    'plan': plan,
                    'badge': STATUS_BADGES.get(plan.status, 'muted'),
                }
                for plan in plans
            ],
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def testplan_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'testplans:index', 'planes de prueba')
    if readonly_redirect:
        return readonly_redirect

    form = TestPlanWizardForm(request.POST or None, request.FILES or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        plan = form.save(commit=False)
        plan.created_by = request.user
        plan.save()
        record_test_plan_version(plan, request.user, 'Creación del plan de pruebas')
        log_action(
            request.user,
            'CREATE',
            'TestPlan',
            plan.pk,
            {'project_id': plan.project_id, 'name': plan.name, 'version': plan.version, 'status': plan.status},
        )
        messages.success(request, 'Plan de pruebas creado correctamente.')
        return redirect('testplans:index')

    return render(request, 'testplans/form.html', {'form': form, 'form_title': 'Crear Plan de Pruebas', 'submit_label': 'Crear Plan'})


@login_required
def testplan_update_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'testplans:index', 'planes de prueba')
    if readonly_redirect:
        return readonly_redirect

    plan = get_object_or_404(
        TestPlan,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )
    form = TestPlanWizardForm(request.POST or None, request.FILES or None, instance=plan, user=request.user)

    if request.method == 'POST' and form.is_valid():
        plan = form.save()
        record_test_plan_version(plan, request.user, 'Actualización del plan de pruebas')
        log_action(
            request.user,
            'UPDATE',
            'TestPlan',
            plan.pk,
            {'project_id': plan.project_id, 'name': plan.name, 'version': plan.version, 'status': plan.status},
        )
        messages.success(request, 'Plan de pruebas actualizado correctamente.')
        return redirect('testplans:index')

    return render(request, 'testplans/form.html', {'form': form, 'form_title': 'Editar Plan de Pruebas', 'submit_label': 'Guardar Cambios'})


@login_required
def testplan_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'testplans:index', 'planes de prueba')
    if readonly_redirect:
        return readonly_redirect

    plan = get_object_or_404(
        TestPlan,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )

    if request.method == 'POST':
        log_action(
            request.user,
            'DELETE',
            'TestPlan',
            plan.pk,
            {'project_id': plan.project_id, 'name': plan.name, 'version': plan.version, 'status': plan.status},
        )
        plan.delete()
        messages.success(request, 'Plan de pruebas eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('testplans:index')

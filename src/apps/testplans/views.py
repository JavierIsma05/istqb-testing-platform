import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, is_teacher, redirect_if_teacher_readonly, visible_projects_for
from apps.core.lifecycle import status_transition_for_plan
from apps.drafts.services import clear_draft
from apps.incidents.views import MATRIX_ROWS

from .forms import TestPlanWizardForm
from .history import record_test_plan_version
from .models import TestPlan
from .risks import sync_risks_from_payload


def parse_risks_payload(request):
    raw = request.POST.get('risks_json', '')
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


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
                {'plan': plan, 'badge': STATUS_BADGES.get(plan.status, 'muted')}
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
        sync_risks_from_payload(plan, request.user, parse_risks_payload(request))
        clear_draft(request.user, 'testplan', plan.project_id, 0)
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

    return render(request, 'testplans/form.html', {'form': form, 'matrix_rows': MATRIX_ROWS, 'form_title': 'Crear Plan de Pruebas', 'submit_label': 'Crear Plan'})


@login_required
def testplan_update_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'testplans:index', 'planes de prueba')
    if readonly_redirect:
        return readonly_redirect

    plan = get_object_or_404(TestPlan, pk=pk, project__in=visible_projects_for(request.user, request=request))
    form = TestPlanWizardForm(request.POST or None, request.FILES or None, instance=plan, user=request.user)

    if request.method == 'POST' and form.is_valid():
        plan = form.save()
        sync_risks_from_payload(plan, request.user, parse_risks_payload(request))
        clear_draft(request.user, 'testplan', plan.project_id, plan.pk)
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

    return render(request, 'testplans/form.html', {'form': form, 'matrix_rows': MATRIX_ROWS, 'form_title': 'Editar Plan de Pruebas', 'submit_label': 'Guardar Cambios'})


@login_required
def testplan_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'testplans:index', 'planes de prueba')
    if readonly_redirect:
        return readonly_redirect

    plan = get_object_or_404(TestPlan, pk=pk, project__in=visible_projects_for(request.user, request=request))

    if request.method == 'POST':
        if plan.versions.exists() or plan.test_cases.exists() or plan.risks.exists():
            messages.error(request, 'No se puede eliminar este plan porque conserva historial o artefactos asociados. Mantén el registro para preservar la trazabilidad.')
            return redirect('testplans:index')
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


@login_required
def testplan_transition_view(request, pk):
    plan = get_object_or_404(TestPlan, pk=pk, project__in=visible_projects_for(request.user, request=request))
    if request.method != 'POST':
        messages.error(request, 'La transición debe confirmarse desde el listado.')
        return redirect('testplans:index')
    target = request.POST.get('target')
    if target == TestPlan.Status.APPROVED and not is_teacher(request.user):
        messages.error(request, 'Solo un docente puede aprobar un plan de pruebas.')
        return redirect('testplans:index')
    if target == TestPlan.Status.REVIEW and is_teacher(request.user):
        messages.error(request, 'Los docentes revisan y aprueban; el envío a revisión lo realiza el responsable del plan.')
        return redirect('testplans:index')
    try:
        status_transition_for_plan(plan, target)
    except ValidationError as exc:
        messages.error(request, str(exc))
        return redirect('testplans:index')
    plan.status = target
    plan.save(update_fields=['status', 'updated_at'])
    record_test_plan_version(plan, request.user, f'Transición de estado a {plan.get_status_display()}')
    log_action(
        request.user,
        'STATUS_CHANGE',
        'TestPlan',
        plan.pk,
        {'project_id': plan.project_id, 'status': plan.status, 'target': target},
    )
    messages.success(request, f'Plan actualizado a {plan.get_status_display()}.')
    return redirect('testplans:index')

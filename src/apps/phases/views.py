from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.core.permissions import redirect_if_teacher_readonly, visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan

from .models import TestingPhase


DEFAULT_PHASES = [
    {
        'order': 1,
        'name': 'Analisis de requisitos',
        'description': 'Identifica, revisa y prioriza los requisitos que deben probarse.',
        'entry_criteria': 'Proyecto creado y tutor vinculado.',
        'exit_criteria': 'Requisitos registrados, revisados y disponibles para planificacion.',
        'status': TestingPhase.Status.IN_PROGRESS,
        'progress': 0,
    },
    {
        'order': 2,
        'name': 'Planificacion y riesgos',
        'description': 'Define alcance, estrategia, recursos, ambiente, criterios y riesgos del plan.',
        'entry_criteria': 'Requisitos disponibles para estimar y priorizar las pruebas.',
        'exit_criteria': 'Plan aprobado con criterios de entrada, salida y riesgos asociados.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 3,
        'name': 'Diseno',
        'description': 'Disena casos de prueba trazables.',
        'entry_criteria': 'Requisitos disponibles para diseno.',
        'exit_criteria': 'Casos de prueba vinculados a requisitos.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 4,
        'name': 'Implementacion',
        'description': 'Prepara ambiente, datos y responsabilidades.',
        'entry_criteria': 'Casos de prueba disenados.',
        'exit_criteria': 'Ambiente y responsables definidos en el plan.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 5,
        'name': 'Ejecucion y defectos',
        'description': 'Ejecuta cada paso, registra resultados obtenidos y gestiona defectos reales.',
        'entry_criteria': 'Casos de prueba disponibles.',
        'exit_criteria': 'Ejecuciones registradas con resultados y evidencias.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 6,
        'name': 'Cierre',
        'description': 'Genera informes y consolida cierre.',
        'entry_criteria': 'Ejecuciones y defectos revisados.',
        'exit_criteria': 'Reporte generado y defectos criticos cerrados o justificados.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
]


def ensure_default_phases(project):
    for phase_data in DEFAULT_PHASES:
        phase, created = TestingPhase.objects.get_or_create(
            project=project,
            order=phase_data['order'],
            defaults=phase_data,
        )
        if not created:
            phase.name = phase_data['name']
            phase.description = phase_data['description']
            phase.entry_criteria = phase_data['entry_criteria']
            phase.exit_criteria = phase_data['exit_criteria']
            phase.save(
                update_fields=['name', 'description', 'entry_criteria', 'exit_criteria', 'updated_at']
            )


def phase_criteria_status(phase):
    project = phase.project
    plans = TestPlan.objects.filter(project=project)
    requirements = Requirement.objects.filter(project=project)
    risks = Incident.objects.filter(project=project)
    test_cases = TestCase.objects.filter(test_plan__project=project)
    executions = TestExecution.objects.filter(test_case__test_plan__project=project)
    defects = Defect.objects.filter(project=project)

    checks_by_order = {
        1: [
            ('Proyecto creado', True),
            ('Requisitos registrados', requirements.exists()),
            ('Requisitos aprobados o en revision', requirements.exclude(status=Requirement.Status.PENDING).exists()),
        ],
        2: [
            ('Requisitos registrados', requirements.exists()),
            ('Plan de pruebas registrado', plans.exists()),
            ('Criterios de entrada y salida definidos', plans.exclude(entry_criteria='').exclude(exit_criteria='').exists()),
            ('Riesgos asociados al plan', risks.filter(test_plan__isnull=False).exists()),
        ],
        3: [
            ('Requisitos disponibles', requirements.exists()),
            ('Casos de prueba creados', test_cases.exists()),
            ('Casos vinculados a requisitos', test_cases.filter(requirement__isnull=False).exists()),
        ],
        4: [
            ('Casos de prueba disponibles', test_cases.exists()),
            ('Ambiente de prueba definido', plans.exclude(environment='').exists()),
            ('Responsabilidades definidas', plans.exclude(responsibilities='').exists()),
        ],
        5: [
            ('Casos de prueba disponibles', test_cases.exists()),
            ('Ejecuciones registradas', executions.exists()),
            ('Resultados obtenidos registrados', executions.exclude(actual_result='').exclude(step_results=[]).exists()),
            ('Defectos vinculados a ejecuciones fallidas', not defects.filter(execution__isnull=True).exists()),
        ],
        6: [
            ('Ejecuciones registradas', executions.exists()),
            ('Reportes generados', project.reports.exists()),
            ('Defectos criticos cerrados o sin pendientes', not defects.filter(severity=Defect.Severity.CRITICAL).exclude(status=Defect.Status.CLOSED).exists()),
        ],
    }
    checks = checks_by_order.get(phase.order, [])
    completed = sum(1 for _label, is_done in checks if is_done)
    pending = len(checks) - completed
    progress = round((completed / len(checks)) * 100) if checks else phase.progress

    return {
        'checks': checks,
        'completed_tasks': completed,
        'pending_tasks': pending,
        'progress': progress,
        'can_complete': bool(checks) and pending == 0,
    }


def sync_phase_progress(phase, criteria):
    if phase.status == TestingPhase.Status.DONE:
        return

    phase.progress = criteria['progress']
    phase.completed_tasks = criteria['completed_tasks']
    phase.pending_tasks = criteria['pending_tasks']
    phase.save(update_fields=['progress', 'completed_tasks', 'pending_tasks', 'updated_at'])


def can_start_phase(phase):
    previous_phase = TestingPhase.objects.filter(project=phase.project, order=phase.order - 1).first()
    return previous_phase is None or previous_phase.status == TestingPhase.Status.DONE


def phase_redirect_url(request, project_id):
    return f'{request.POST.get("next") or "/phases/"}?project={project_id}'


@login_required
def phase_list_view(request):
    projects = visible_projects_for(request.user)
    selected_project = projects.filter(pk=request.GET.get('project')).first() or projects.first()
    phases = TestingPhase.objects.none()
    phase_items = []
    general_progress = 0
    completed_count = 0

    if selected_project:
        ensure_default_phases(selected_project)
        phases = TestingPhase.objects.filter(project=selected_project).order_by('order')
        for phase in phases:
            criteria = phase_criteria_status(phase)
            sync_phase_progress(phase, criteria)
            phase_items.append({
                'phase': phase,
                'criteria': criteria,
                'can_start': can_start_phase(phase),
            })

        phase_count = phases.count()
        completed_count = phases.filter(status=TestingPhase.Status.DONE).count()
        general_progress = round(sum(phase.progress for phase in phases) / phase_count) if phase_count else 0

    return render(
        request,
        'phases/index.html',
        {
            'projects': projects,
            'selected_project': selected_project,
            'phases': phases,
            'phase_items': phase_items,
            'general_progress': general_progress,
            'completed_count': completed_count,
            'total_phases': phases.count(),
        },
    )


@login_required
@require_POST
def phase_advance_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'phases:index', 'fases')
    if readonly_redirect:
        return readonly_redirect

    phase = get_object_or_404(TestingPhase, pk=pk, project__in=visible_projects_for(request.user))
    criteria = phase_criteria_status(phase)

    if not can_start_phase(phase):
        messages.error(request, 'Completa la fase anterior antes de iniciar esta fase.')
        return redirect(phase_redirect_url(request, phase.project_id))

    if phase.status == TestingPhase.Status.PENDING:
        phase.status = TestingPhase.Status.IN_PROGRESS
        phase.started_at = phase.started_at or timezone.now()
        phase.updated_by = request.user
        phase.save(update_fields=['status', 'started_at', 'updated_by', 'updated_at'])
        log_action(request.user, 'START', 'TestingPhase', phase.pk, {'project_id': phase.project_id, 'order': phase.order})
        messages.success(request, f'Fase "{phase.name}" iniciada correctamente.')
        return redirect(phase_redirect_url(request, phase.project_id))

    if not criteria['can_complete']:
        messages.error(request, 'No se puede completar la fase hasta cumplir todos los criterios definidos.')
        return redirect(phase_redirect_url(request, phase.project_id))

    completed_at = timezone.now()
    phase.status = TestingPhase.Status.DONE
    phase.progress = 100
    phase.completed_tasks = criteria['completed_tasks']
    phase.pending_tasks = 0
    phase.started_at = phase.started_at or completed_at
    phase.completed_at = completed_at
    phase.updated_by = request.user
    phase.save(update_fields=['status', 'progress', 'completed_tasks', 'pending_tasks', 'started_at', 'completed_at', 'updated_by', 'updated_at'])
    log_action(request.user, 'COMPLETE', 'TestingPhase', phase.pk, {'project_id': phase.project_id, 'order': phase.order})
    messages.success(request, f'Fase "{phase.name}" completada correctamente.')

    next_phase = TestingPhase.objects.filter(project=phase.project, order=phase.order + 1, status=TestingPhase.Status.PENDING).first()
    if next_phase:
        next_phase.status = TestingPhase.Status.IN_PROGRESS
        next_phase.started_at = next_phase.started_at or timezone.now()
        next_phase.updated_by = request.user
        next_phase.save(update_fields=['status', 'started_at', 'updated_by', 'updated_at'])

    return redirect(phase_redirect_url(request, phase.project_id))

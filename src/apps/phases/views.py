from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.core.permissions import get_active_project_for_request, redirect_if_teacher_readonly, visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.reports.models import Report
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan

from .models import TestingPhase


DEFAULT_PHASES = [
    {
        'order': 1,
        'name': 'Análisis de requisitos',
        'description': 'Identifica, revisa y prioriza los requisitos que deben probarse.',
        'entry_criteria': 'Proyecto creado y tutor vinculado.',
        'exit_criteria': 'Requisitos registrados, revisados y disponibles para planificacion.',
        'status': TestingPhase.Status.IN_PROGRESS,
        'progress': 0,
    },
    {
        'order': 2,
        'name': 'Planificación y riesgos',
        'description': 'Define alcance, estrategia, recursos, ambiente, criterios y riesgos del plan.',
        'entry_criteria': 'Requisitos disponibles para estimar y priorizar las pruebas.',
        'exit_criteria': 'Plan aprobado con criterios de entrada, salida y riesgos asociados.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 3,
        'name': 'Diseño',
        'description': 'Diseña casos de prueba trazables.',
        'entry_criteria': 'Requisitos disponibles para diseño.',
        'exit_criteria': 'Casos de prueba vinculados a requisitos.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 4,
        'name': 'Implementación',
        'description': 'Prepara ambiente, datos y responsabilidades.',
        'entry_criteria': 'Casos de prueba disenados.',
        'exit_criteria': 'Ambiente y responsables definidos en el plan.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
    {
        'order': 5,
        'name': 'Ejecución y defectos',
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
        'exit_criteria': 'Reporte generado y defectos críticos cerrados o justificados.',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
]


def ensure_default_phases(project):
    existing = {
        phase.order: phase
        for phase in TestingPhase.objects.filter(project=project)
    }
    to_create = []
    synced_fields = ['name', 'description', 'entry_criteria', 'exit_criteria']
    for phase_data in DEFAULT_PHASES:
        phase = existing.get(phase_data['order'])
        if phase is None:
            to_create.append(TestingPhase(project=project, **phase_data))
            continue
        changed_fields = [field for field in synced_fields if getattr(phase, field) != phase_data[field]]
        if changed_fields:
            for field in changed_fields:
                setattr(phase, field, phase_data[field])
            phase.save(update_fields=[*changed_fields, 'updated_at'])
    if to_create:
        TestingPhase.objects.bulk_create(to_create)

    phases = list(existing.values()) + to_create
    return sorted(phases, key=lambda phase: phase.order)


def project_criteria_snapshot(project):
    requirements = list(Requirement.objects.filter(project=project).values_list('status', flat=True))
    plans = list(
        TestPlan.objects.filter(project=project).values_list(
            'entry_criteria', 'exit_criteria', 'environment', 'responsibilities'
        )
    )
    risks = list(Incident.objects.filter(project=project).values_list('test_plan_id', flat=True))
    test_cases = list(TestCase.objects.filter(test_plan__project=project).values_list('requirement_id', flat=True))
    executions = list(
        TestExecution.objects.filter(test_case__test_plan__project=project).values_list(
            'actual_result', 'step_results'
        )
    )
    defects = list(Defect.objects.filter(project=project).values_list('execution_id', 'severity', 'status'))
    reports_generated = Report.objects.filter(project=project).exists()

    return {
        'requirements_registered': bool(requirements),
        'requirements_reviewed': any(status != Requirement.Status.PENDING for status in requirements),
        'plans_registered': bool(plans),
        'plans_criteria': any(bool(entry) and bool(exit) for entry, exit, _env, _resp in plans),
        'plans_environment': any(bool(env) for _entry, _exit, env, _resp in plans),
        'plans_responsibilities': any(bool(resp) for _entry, _exit, _env, resp in plans),
        'risks_linked': any(risk_id is not None for risk_id in risks),
        'test_cases_created': bool(test_cases),
        'cases_linked': any(requirement_id is not None for requirement_id in test_cases),
        'executions_registered': bool(executions),
        'executions_results': any(bool(actual_result) and step_results != [] for actual_result, step_results in executions),
        'defects_registered': bool(defects),
        'defects_orphan': any(execution_id is None for execution_id, _severity, _status in defects),
        'defects_critical_open': any(
            severity == Defect.Severity.HIGH and status != Defect.Status.CLOSED
            for _execution_id, severity, status in defects
        ),
        'reports_generated': reports_generated,
    }


def phase_criteria_status(phase, snapshot=None):
    if snapshot is None:
        snapshot = project_criteria_snapshot(phase.project)

    checks_by_order = {
        1: [
            ('Proyecto creado', True),
            ('Requisitos registrados', snapshot['requirements_registered']),
            ('Requisitos aprobados o en revisión', snapshot['requirements_reviewed']),
        ],
        2: [
            ('Requisitos registrados', snapshot['requirements_registered']),
            ('Plan de pruebas registrado', snapshot['plans_registered']),
            ('Criterios de entrada y salida definidos', snapshot['plans_criteria']),
            ('Riesgos asociados al plan', snapshot['risks_linked']),
        ],
        3: [
            ('Requisitos disponibles', snapshot['requirements_registered']),
            ('Casos de prueba creados', snapshot['test_cases_created']),
            ('Casos vinculados a requisitos', snapshot['cases_linked']),
        ],
        4: [
            ('Casos de prueba disponibles', snapshot['test_cases_created']),
            ('Ambiente de prueba definido', snapshot['plans_environment']),
            ('Responsabilidades definidas', snapshot['plans_responsibilities']),
        ],
        5: [
            ('Casos de prueba disponibles', snapshot['test_cases_created']),
            ('Ejecuciones registradas', snapshot['executions_registered']),
            ('Resultados obtenidos registrados', snapshot['executions_results']),
            ('Defectos vinculados a ejecuciones fallidas', not snapshot['defects_orphan']),
        ],
        6: [
            ('Ejecuciones registradas', snapshot['executions_registered']),
            ('Reportes generados', snapshot['reports_generated']),
            ('Defectos críticos cerrados o sin pendientes', not snapshot['defects_critical_open']),
        ],
    }
    checks = checks_by_order.get(phase.order, [])
    completed = sum(1 for _label, is_done in checks if is_done)
    pending = len(checks) - completed
    progress = round((completed / len(checks)) * 100) if checks else phase.progress
    details_by_order = {
        1: [
            ('Proyecto creado', 'Proyectos', 'Ver proyecto', 'projects:index'),
            ('Requisitos registrados', 'Requisitos', 'Registrar requisitos', 'requirements:index'),
            ('Requisitos aprobados o en revisión', 'Requisitos', 'Revisar requisitos', 'requirements:index'),
        ],
        2: [
            ('Requisitos registrados', 'Requisitos', 'Ver requisitos', 'requirements:index'),
            ('Plan de pruebas registrado', 'Plan de pruebas', 'Crear plan', 'testplans:index'),
            ('Criterios de entrada y salida definidos', 'Plan de pruebas', 'Completar plan', 'testplans:index'),
            ('Riesgos asociados al plan', 'Riesgos', 'Registrar riesgos', 'incidents:index'),
        ],
        3: [
            ('Requisitos disponibles', 'Requisitos', 'Ver requisitos', 'requirements:index'),
            ('Casos de prueba creados', 'Casos de prueba', 'Crear casos', 'testcases:index'),
            ('Casos vinculados a requisitos', 'Casos de prueba', 'Vincular casos', 'testcases:index'),
        ],
        4: [
            ('Casos de prueba disponibles', 'Casos de prueba', 'Ver casos', 'testcases:index'),
            ('Ambiente de prueba definido', 'Plan de pruebas', 'Definir ambiente', 'testplans:index'),
            ('Responsabilidades definidas', 'Plan de pruebas', 'Definir responsables', 'testplans:index'),
        ],
        5: [
            ('Casos de prueba disponibles', 'Casos de prueba', 'Ver casos', 'testcases:index'),
            ('Ejecuciones registradas', 'Ejecución', 'Ejecutar pruebas', 'executions:index'),
            ('Resultados obtenidos registrados', 'Ejecución', 'Completar resultados', 'executions:index'),
            ('Defectos vinculados a ejecuciones fallidas', 'Defectos', 'Revisar defectos', 'defects:index'),
        ],
        6: [
            ('Ejecuciones registradas', 'Ejecución', 'Ver ejecuciones', 'executions:index'),
            ('Reportes generados', 'Informes', 'Generar informe', 'reports:index'),
            ('Defectos críticos cerrados o sin pendientes', 'Defectos', 'Cerrar defectos críticos', 'defects:index'),
        ],
    }
    details = [
        {
            'label': label,
            'is_done': is_done,
            'module': module,
            'action': action,
            'route_name': route_name,
        }
        for (label, is_done), (_detail_label, module, action, route_name)
        in zip(checks, details_by_order.get(phase.order, []))
    ]

    return {
        'checks': checks,
        'details': details,
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
    projects = visible_projects_for(request.user, request=request)
    active_project = get_active_project_for_request(request)
    selected_project = (
        projects.filter(pk=request.GET.get('project')).first()
        or (active_project if active_project and active_project in projects else None)
        or projects.first()
    )
    phases = TestingPhase.objects.none()
    phase_items = []
    general_progress = 0
    completed_count = 0

    if selected_project:
        phases = ensure_default_phases(selected_project)
        criteria_snapshot = project_criteria_snapshot(selected_project)
        for phase in phases:
            criteria = phase_criteria_status(phase, snapshot=criteria_snapshot)
            sync_phase_progress(phase, criteria)
            phase_items.append({
                'phase': phase,
                'criteria': criteria,
                'can_start': can_start_phase(phase),
            })

        phase_count = len(phases)
        completed_count = sum(1 for phase in phases if phase.status == TestingPhase.Status.DONE)
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
            'total_phases': len(phases),
        },
    )


@login_required
@require_POST
def phase_advance_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'phases:index', 'fases')
    if readonly_redirect:
        return readonly_redirect

    phase = get_object_or_404(TestingPhase, pk=pk, project__in=visible_projects_for(request.user, request=request))
    criteria = phase_criteria_status(phase, snapshot=project_criteria_snapshot(phase.project))

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

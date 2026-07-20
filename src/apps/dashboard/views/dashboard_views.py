from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from apps.core.permissions import visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.projects.models import Project
from apps.phases.models import TestingPhase
from apps.phases.views import ensure_default_phases, phase_criteria_status
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.users.models import User


def get_project_progress(project):
    total_cases = project.total_cases or 0
    passed_cases = project.passed_cases or 0
    return round((passed_cases / total_cases) * 100) if total_cases else 0


def get_project_student(project):
    if project.created_by and project.created_by.role == User.Roles.STUDENT:
        return project.created_by

    return project.members.filter(role=User.Roles.STUDENT).first()


def get_time_label(value):
    if not value:
        return 'Sin fecha'

    delta = timezone.now() - value
    if delta.days >= 1:
        return f'Hace {delta.days} dia{"s" if delta.days != 1 else ""}'

    hours = delta.seconds // 3600
    if hours:
        return f'Hace {hours} hora{"s" if hours != 1 else ""}'

    minutes = delta.seconds // 60
    if minutes:
        return f'Hace {minutes} minuto{"s" if minutes != 1 else ""}'

    return 'Hace un momento'


def build_project_summaries(projects):
    summaries = []
    annotated_projects = projects.annotate(
        total_cases=Count('test_plans__test_cases', distinct=True),
        passed_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__status=TestCase.Status.PASSED),
            distinct=True,
        ),
        failed_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__status=TestCase.Status.FAILED),
            distinct=True,
        ),
        pending_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__status=TestCase.Status.PENDING),
            distinct=True,
        ),
    ).order_by('-updated_at', '-created_at')

    for project in annotated_projects[:3]:
        summaries.append(
            {
                'project': project,
                'progress': get_project_progress(project),
                'total': project.total_cases or 0,
                'passed': project.passed_cases or 0,
                'failed': project.failed_cases or 0,
                'pending': project.pending_cases or 0,
                'date': project.end_date or project.start_date,
                'status_badge': 'muted' if project.status == Project.Status.CLOSED else 'success',
            }
        )

    return summaries


def build_recent_activity(projects):
    activities = []

    for execution in TestExecution.objects.select_related('test_case').filter(
        test_case__test_plan__project__in=projects,
    ).order_by('-executed_at', '-created_at')[:6]:
        tone = 'success' if execution.result == TestExecution.Result.PASSED else 'danger'
        icon = 'bi-check-circle' if execution.result == TestExecution.Result.PASSED else 'bi-x-circle'
        activities.append(
            {
                'title': 'Caso de prueba ejecutado',
                'detail': f'{execution.test_case.code} - {get_time_label(execution.executed_at or execution.created_at)}',
                'tone': tone,
                'icon': icon,
                'date': execution.executed_at or execution.created_at,
            }
        )

    for defect in Defect.objects.filter(project__in=projects).order_by('-created_at')[:6]:
        activities.append(
            {
                'title': 'Defecto registrado',
                'detail': f'{defect.code} - {get_time_label(defect.created_at)}',
                'tone': 'danger',
                'icon': 'bi-exclamation-circle',
                'date': defect.created_at,
            }
        )

    for plan in TestPlan.objects.filter(project__in=projects).order_by('-updated_at')[:6]:
        activities.append(
            {
                'title': 'Plan de pruebas actualizado',
                'detail': f'{plan.name} v{plan.version} - {get_time_label(plan.updated_at)}',
                'tone': 'info',
                'icon': 'bi-clock',
                'date': plan.updated_at,
            }
        )

    for requirement in Requirement.objects.filter(project__in=projects).order_by('-created_at')[:6]:
        activities.append(
            {
                'title': 'Requisito agregado',
                'detail': f'{requirement.code} - {get_time_label(requirement.created_at)}',
                'tone': 'warning',
                'icon': 'bi-file-earmark-text',
                'date': requirement.created_at,
            }
        )

    return sorted(activities, key=lambda item: item['date'] or timezone.now(), reverse=True)[:6]


def build_teacher_dashboard(request):
    teacher_projects = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).distinct().prefetch_related('members').annotate(
        total_cases=Count('test_plans__test_cases', distinct=True),
        passed_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__executions__result=TestExecution.Result.PASSED),
            distinct=True,
        ),
        pending_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__status=TestCase.Status.PENDING),
            distinct=True,
        ),
    )

    project_rows = []
    for project in teacher_projects[:6]:
        student = get_project_student(project)
        project_rows.append({
            'project': project,
            'student': student,
            'progress': get_project_progress(project),
            'pending_cases': project.pending_cases or 0,
            'status_badge': 'muted' if project.status == Project.Status.CLOSED else 'success',
        })

    assigned_student_ids = {
        row['student'].id
        for row in project_rows
        if row['student']
    }

    return {
        'is_teacher_dashboard': True,
        'teacher_metrics': [
            {
                'label': 'Estudiantes Asignados',
                'total': len(assigned_student_ids),
                'icon': 'bi-people',
                'tone': 'blue',
            },
            {
                'label': 'Proyectos Activos',
                'total': teacher_projects.filter(status=Project.Status.ACTIVE).count(),
                'icon': 'bi-kanban',
                'tone': 'green',
            },
            {
                'label': 'Revisiones pendientes',
                'total': sum(project.pending_cases or 0 for project in teacher_projects),
                'icon': 'bi-exclamation-triangle',
                'tone': 'yellow',
            },
            {
                'label': 'Proyectos Finalizados',
                'total': teacher_projects.filter(status=Project.Status.CLOSED).count(),
                'icon': 'bi-check-circle',
                'tone': 'sky',
            },
        ],
        'teacher_projects': project_rows,
    }


def build_student_phase_timeline(projects):
    project = projects.filter(status=Project.Status.ACTIVE).first() or projects.first()
    if not project:
        return None

    ensure_default_phases(project)
    phases = TestingPhase.objects.filter(project=project).order_by('order')
    short_names = {
        1: 'Requisitos',
        2: 'Riesgos',
        3: 'Diseño',
        4: 'Implementación',
        5: 'Ejecución y defectos',
        6: 'Cierre',
    }
    items = []
    for phase in phases:
        criteria = phase_criteria_status(phase)
        status = phase.status
        if phase.order == 5 and (
            TestExecution.objects.filter(test_case__test_plan__project=project).exists() or
            Defect.objects.filter(project=project).exists()
        ):
            status = TestingPhase.Status.IN_PROGRESS
        elif status != TestingPhase.Status.DONE and criteria['progress'] == 100:
            status = TestingPhase.Status.IN_PROGRESS
        items.append({
            'name': phase.name,
            'short_name': short_names.get(phase.order, phase.name),
            'status': status,
            'progress': criteria['progress'],
        })

    return {
        'project': project,
        'items': items,
        'completed': sum(item['status'] == TestingPhase.Status.DONE for item in items),
        'total': len(items),
    }


@login_required
def dashboard_view(request):
    if request.user.role == User.Roles.TEACHER:
        return render(
            request,
            'dashboard/dashboard.html',
            build_teacher_dashboard(request),
        )

    visible_projects = visible_projects_for(request.user, request=request)
    cards = [
        ('Proyectos', visible_projects.count(), 'bi-folder2-open', 'projects:index'),
        ('Requisitos', Requirement.objects.filter(project__in=visible_projects).count(), 'bi-card-checklist', 'requirements:index'),
        ('Planes de prueba', TestPlan.objects.filter(project__in=visible_projects).count(), 'bi-diagram-3', 'testplans:index'),
        ('Casos de prueba', TestCase.objects.filter(test_plan__project__in=visible_projects).count(), 'bi-list-check', 'testcases:index'),
        ('Ejecuciones', TestExecution.objects.filter(test_case__test_plan__project__in=visible_projects).count(), 'bi-play-circle', 'executions:index'),
        ('Defectos', Defect.objects.filter(project__in=visible_projects).count(), 'bi-bug', 'defects:index'),
        ('Incidentes', Incident.objects.filter(project__in=visible_projects).count(), 'bi-exclamation-triangle', 'incidents:index'),
    ]

    return render(
        request,
        'dashboard/dashboard.html',
        {
            'cards': cards,
            'project_summaries': build_project_summaries(visible_projects),
            'recent_activities': build_recent_activity(visible_projects),
            'student_phase_timeline': (
                build_student_phase_timeline(visible_projects)
                if request.user.role == User.Roles.STUDENT
                else None
            ),
        },
    )

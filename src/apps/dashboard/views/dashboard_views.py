from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.projects.models import Project
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
                'label': 'Revisiones Pendientes',
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


@login_required
def dashboard_view(request):
    if request.user.role == User.Roles.TEACHER:
        return render(
            request,
            'dashboard/dashboard.html',
            build_teacher_dashboard(request),
        )

    cards = [
        ('Proyectos', Project.objects.count(), 'bi-folder2-open', 'projects:index'),
        ('Requisitos', Requirement.objects.count(), 'bi-card-checklist', 'requirements:index'),
        ('Planes de prueba', TestPlan.objects.count(), 'bi-diagram-3', 'testplans:index'),
        ('Casos de prueba', TestCase.objects.count(), 'bi-list-check', 'testcases:index'),
        ('Ejecuciones', TestExecution.objects.count(), 'bi-play-circle', 'executions:index'),
        ('Defectos', Defect.objects.count(), 'bi-bug', 'defects:index'),
        ('Incidentes', Incident.objects.count(), 'bi-exclamation-triangle', 'incidents:index'),
    ]

    return render(
        request,
        'dashboard/dashboard.html',
        {'cards': cards}
    )

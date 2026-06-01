from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.projects.models import Project

from .models import TestingPhase


DEFAULT_PHASES = [
    {
        'order': 1,
        'name': 'Planificación',
        'description': 'Define estrategia y recursos',
        'status': TestingPhase.Status.DONE,
        'progress': 100,
    },
    {
        'order': 2,
        'name': 'Análisis',
        'description': 'Analiza requisitos y riesgos',
        'status': TestingPhase.Status.DONE,
        'progress': 100,
    },
    {
        'order': 3,
        'name': 'Diseño',
        'description': 'Diseña casos de prueba',
        'status': TestingPhase.Status.DONE,
        'progress': 100,
    },
    {
        'order': 4,
        'name': 'Implementación',
        'description': 'Prepara entorno de pruebas',
        'status': TestingPhase.Status.IN_PROGRESS,
        'progress': 75,
        'completed_tasks': 3,
        'pending_tasks': 1,
    },
    {
        'order': 5,
        'name': 'Ejecución',
        'description': 'Ejecuta casos y registra resultados',
        'status': TestingPhase.Status.PENDING,
        'progress': 45,
    },
    {
        'order': 6,
        'name': 'Cierre',
        'description': 'Genera informes y lecciones aprendidas',
        'status': TestingPhase.Status.PENDING,
        'progress': 0,
    },
]


def ensure_default_phases(project):
    if TestingPhase.objects.filter(project=project).exists():
        return

    TestingPhase.objects.bulk_create(
        TestingPhase(project=project, **phase)
        for phase in DEFAULT_PHASES
    )


@login_required
def phase_list_view(request):
    projects = Project.objects.all()
    selected_project = projects.filter(pk=request.GET.get('project')).first() or projects.first()
    phases = TestingPhase.objects.none()
    general_progress = 0
    completed_count = 0

    if selected_project:
        ensure_default_phases(selected_project)
        phases = TestingPhase.objects.filter(project=selected_project).order_by('order')
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
            'general_progress': general_progress,
            'completed_count': completed_count,
            'total_phases': phases.count(),
        },
    )

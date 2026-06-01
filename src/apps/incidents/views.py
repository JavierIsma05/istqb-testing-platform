from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for
from apps.projects.models import Project

from .forms import IncidentForm
from .models import Incident


STATUS_BADGES = {
    Incident.Status.MITIGATED: 'danger',
    Incident.Status.OPEN: 'warning',
    Incident.Status.ANALYSIS: 'info',
    Incident.Status.CLOSED: 'muted',
}

MATRIX_ROWS = [
    ('Alta', [('Alto-Bajo', 'warning'), ('Alto-Medio', 'danger'), ('Alto-Alto', 'danger')]),
    ('Media', [('Medio-Bajo', 'success'), ('Medio-Medio', 'warning'), ('Medio-Alto', 'danger')]),
    ('Baja', [('Bajo-Bajo', 'success'), ('Bajo-Medio', 'success'), ('Bajo-Alto', 'warning')]),
]


@login_required
def incident_list_view(request):
    query = request.GET.get('q', '').strip()
    project_id = request.GET.get('project', '').strip()
    visible_projects = visible_projects_for(request.user)

    incidents = Incident.objects.select_related('project', 'reported_by')
    incidents = incidents.filter(project__in=visible_projects)

    if query:
        incidents = incidents.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )

    if project_id:
        incidents = incidents.filter(project_id=project_id)

    return render(
        request,
        'incidents/index.html',
        {
            'incidents': [
                {
                    'incident': incident,
                    'badge': STATUS_BADGES.get(incident.status, 'muted'),
                }
                for incident in incidents
            ],
            'matrix_rows': MATRIX_ROWS,
            'projects': visible_projects.order_by('name'),
            'selected_project': project_id,
            'query': query,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def incident_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'incidents:index', 'incidencias')
    if readonly_redirect:
        return readonly_redirect

    form = IncidentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        incident = form.save(commit=False)
        incident.reported_by = request.user
        incident.save()
        return redirect('incidents:index')

    return render(
        request,
        'incidents/form.html',
        {
            'form': form,
            'title': 'Nueva Incidencia',
            'subtitle': 'Registra riesgos e incidencias con probabilidad e impacto.',
        },
    )

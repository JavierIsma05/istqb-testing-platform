from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_action
from apps.core.permissions import (
    can_manage_artifacts,
    get_active_project_for_request,
    redirect_if_teacher_readonly,
    visible_projects_for,
)
from apps.core.codes import next_code
from apps.projects.models import Project

from .forms import IncidentForm
from .models import Incident


STATUS_BADGES = {
    Incident.Status.MITIGATED: 'success',
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
    visible_projects = visible_projects_for(request.user, request=request)
    active_project = get_active_project_for_request(request)

    incidents = Incident.objects.select_related('project', 'reported_by', 'requirement', 'test_plan', 'test_case')
    incidents = incidents.filter(project__in=visible_projects)

    if query:
        incidents = incidents.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )

    if active_project:
        incidents = incidents.filter(project=active_project)
    elif project_id:
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
    readonly_redirect = redirect_if_teacher_readonly(request, 'incidents:index', 'riesgos')
    if readonly_redirect:
        return readonly_redirect

    form = IncidentForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        incident = form.save(commit=False)
        incident.code = next_code(Incident.objects.filter(project=incident.project), 'INC')
        incident.reported_by = request.user
        incident.save()
        log_action(
            request.user,
            'CREATE',
            'Incident',
            incident.pk,
            {'project_id': incident.project_id, 'code': incident.code, 'title': incident.title, 'risk_level': incident.risk_level},
        )
        messages.success(request, 'Riesgo registrado correctamente.')
        return redirect('incidents:index')

    return render(
        request,
        'incidents/form.html',
        {
            'form': form,
            'title': 'Nuevo Riesgo',
            'subtitle': 'Registra amenazas futuras asociadas al plan y, opcionalmente, al requisito afectado.',
        },
    )


@login_required
def incident_update_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'incidents:index', 'riesgos')
    if readonly_redirect:
        return readonly_redirect

    incident = get_object_or_404(
        Incident,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )
    form = IncidentForm(request.POST or None, instance=incident, user=request.user)

    if request.method == 'POST' and form.is_valid():
        incident = form.save()
        log_action(
            request.user,
            'UPDATE',
            'Incident',
            incident.pk,
            {'project_id': incident.project_id, 'code': incident.code, 'title': incident.title, 'risk_level': incident.risk_level},
        )
        messages.success(request, 'Riesgo actualizado correctamente.')
        return redirect('incidents:index')

    return render(
        request,
        'incidents/form.html',
        {
            'form': form,
            'title': 'Editar Riesgo',
            'subtitle': 'Actualiza probabilidad, impacto, mitigacion y relacion con el plan.',
        },
    )


@login_required
def incident_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'incidents:index', 'riesgos')
    if readonly_redirect:
        return readonly_redirect

    incident = get_object_or_404(
        Incident,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )

    if request.method == 'POST':
        log_action(
            request.user,
            'DELETE',
            'Incident',
            incident.pk,
            {'project_id': incident.project_id, 'code': incident.code, 'title': incident.title, 'risk_level': incident.risk_level},
        )
        incident.delete()
        messages.success(request, 'Riesgo eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('incidents:index')

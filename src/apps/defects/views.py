from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
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

from .forms import DefectForm
from .history import record_defect_history
from .models import Defect


STATUS_BADGES = {
    Defect.Status.OPEN: 'open',
    Defect.Status.IN_PROGRESS: 'warning',
    Defect.Status.RESOLVED: 'info',
    Defect.Status.CLOSED: 'success',
    Defect.Status.REOPENED: 'warning',
}


SEVERITY_BADGES = {
    Defect.Severity.HIGH: 'danger',
    Defect.Severity.MEDIUM: 'medium',
    Defect.Severity.LOW: 'low',
}


PRIORITY_BADGES = {
    Defect.Priority.CRITICAL: 'danger',
    Defect.Priority.HIGH: 'high',
    Defect.Priority.MEDIUM: 'medium',
    Defect.Priority.LOW: 'low',
}


TRANSITIONS = {
    Defect.Status.OPEN: Defect.Status.IN_PROGRESS,
    Defect.Status.IN_PROGRESS: Defect.Status.RESOLVED,
    Defect.Status.RESOLVED: Defect.Status.CLOSED,
    Defect.Status.CLOSED: Defect.Status.REOPENED,
    Defect.Status.REOPENED: Defect.Status.IN_PROGRESS,
}


@login_required
def defect_list_view(request):
    query = request.GET.get('q', '').strip()
    project_id = request.GET.get('project', '').strip()
    status = request.GET.get('status', '').strip()
    visible_projects = visible_projects_for(request.user, request=request)
    active_project = get_active_project_for_request(request)

    defects = Defect.objects.select_related(
        'project',
        'reported_by',
        'assigned_to',
        'execution',
        'execution__test_case',
    ).annotate(
        history_count=Count('history', distinct=True),
    )
    defects = defects.filter(project__in=visible_projects)

    if query:
        defects = defects.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )

    if active_project:
        defects = defects.filter(project=active_project)
    elif project_id:
        defects = defects.filter(project_id=project_id)

    if status:
        defects = defects.filter(status=status)

    total = defects.count()
    open_count = defects.filter(status=Defect.Status.OPEN).count()
    in_fix_count = defects.filter(status=Defect.Status.IN_PROGRESS).count()
    resolved_count = defects.filter(status=Defect.Status.RESOLVED).count()
    reopened_count = defects.filter(status=Defect.Status.REOPENED).count()
    closed_count = defects.filter(status=Defect.Status.CLOSED).count()

    return render(
        request,
        'defects/index.html',
        {
            'items': [
                {
                    'defect': defect,
                    'badge': STATUS_BADGES.get(defect.status, 'muted'),
                    'severity_badge': SEVERITY_BADGES.get(defect.severity, 'muted'),
                    'priority_badge': PRIORITY_BADGES.get(defect.priority, 'muted'),
                    'next_status': TRANSITIONS.get(defect.status),
                }
                for defect in defects
            ],
            'total': total,
            'open_count': open_count,
            'in_fix_count': in_fix_count,
            'resolved_count': resolved_count,
            'reopened_count': reopened_count,
            'closed_count': closed_count,
            'projects': visible_projects.order_by('name'),
            'status_choices': Defect.Status.choices,
            'selected_project': project_id,
            'selected_status': status,
            'query': query,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def defect_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'defects:index', 'defectos')
    if readonly_redirect:
        return readonly_redirect

    form = DefectForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        defect = form.save(commit=False)
        defect.code = next_code(Defect.objects.filter(project=defect.project), 'DEF')
        defect.reported_by = request.user
        defect.save()
        record_defect_history(defect, request.user, 'Registro inicial del defecto')
        log_action(
            request.user,
            'CREATE',
            'Defect',
            defect.pk,
            {'project_id': defect.project_id, 'code': defect.code, 'title': defect.title, 'status': defect.status},
        )
        messages.success(request, 'Defecto registrado correctamente.')
        return redirect('defects:index')

    return render(
        request,
        'defects/form.html',
        {
            'form': form,
            'title': 'Reportar Defecto',
            'subtitle': 'Registra y asigna defectos encontrados durante la ejecución de pruebas.',
        },
    )


@login_required
def defect_update_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'defects:index', 'defectos')
    if readonly_redirect:
        return readonly_redirect

    defect = get_object_or_404(
        Defect,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )
    form = DefectForm(request.POST or None, instance=defect, user=request.user)

    if request.method == 'POST' and form.is_valid():
        defect = form.save()
        record_defect_history(defect, request.user, 'Actualizacion del defecto')
        log_action(
            request.user,
            'UPDATE',
            'Defect',
            defect.pk,
            {'project_id': defect.project_id, 'code': defect.code, 'title': defect.title, 'status': defect.status},
        )
        messages.success(request, 'Defecto actualizado correctamente.')
        return redirect('defects:index')

    return render(
        request,
        'defects/form.html',
        {
            'form': form,
            'title': 'Editar Defecto',
            'subtitle': 'Actualiza la severidad o la descripción del defecto sin perder su historial ni su vínculo con el caso de prueba.',
        },
    )


@login_required
def defect_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'defects:index', 'defectos')
    if readonly_redirect:
        return readonly_redirect

    defect = get_object_or_404(
        Defect,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )

    if request.method == 'POST':
        log_action(
            request.user,
            'DELETE',
            'Defect',
            defect.pk,
            {'project_id': defect.project_id, 'code': defect.code, 'title': defect.title, 'status': defect.status},
        )
        defect.delete()
        messages.success(request, 'Defecto eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('defects:index')


@login_required
def defect_transition_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'defects:index', 'defectos')
    if readonly_redirect:
        return readonly_redirect

    defect = get_object_or_404(
        Defect,
        pk=pk,
        project__in=visible_projects_for(request.user, request=request),
    )

    if request.method == 'POST':
        target = TRANSITIONS.get(defect.status)
        if target:
            defect.status = target
            defect.save()
            reason = {
                Defect.Status.OPEN: 'Transición a En progreso',
                Defect.Status.IN_PROGRESS: 'Transición a Resuelto',
                Defect.Status.RESOLVED: 'Transición a Cerrado',
                Defect.Status.CLOSED: 'Transición a Reabierto',
                Defect.Status.REOPENED: 'Transición a En progreso',
            }.get(target, 'Transición de estado')
            record_defect_history(defect, request.user, reason)
            log_action(
                request.user,
                'UPDATE',
                'Defect',
                defect.pk,
                {'project_id': defect.project_id, 'code': defect.code, 'title': defect.title, 'status': defect.status},
            )
            messages.success(request, f'Estado actualizado a {defect.get_status_display()}.')
        else:
            messages.error(request, 'No hay una transición válida para este estado.')
    else:
        messages.error(request, 'La transición debe confirmarse desde el listado.')

    return redirect('defects:index')

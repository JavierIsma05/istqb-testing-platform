from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for
from apps.projects.models import Project

from .forms import DefectForm
from .models import Defect


STATUS_BADGES = {
    Defect.Status.OPEN: 'danger',
    Defect.Status.IN_PROGRESS: 'warning',
    Defect.Status.RESOLVED: 'info',
    Defect.Status.CLOSED: 'success',
}


@login_required
def defect_list_view(request):
    query = request.GET.get('q', '').strip()
    project_id = request.GET.get('project', '').strip()
    status = request.GET.get('status', '').strip()
    visible_projects = visible_projects_for(request.user)

    defects = Defect.objects.select_related('project', 'reported_by', 'assigned_to', 'execution')
    defects = defects.filter(project__in=visible_projects)

    if query:
        defects = defects.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )

    if project_id:
        defects = defects.filter(project_id=project_id)

    if status:
        defects = defects.filter(status=status)

    total = defects.count()
    open_count = defects.filter(status=Defect.Status.OPEN).count()
    in_fix_count = defects.filter(status=Defect.Status.IN_PROGRESS).count()
    closed_count = defects.filter(status=Defect.Status.CLOSED).count()

    return render(
        request,
        'defects/index.html',
        {
            'items': [
                {
                    'defect': defect,
                    'badge': STATUS_BADGES.get(defect.status, 'muted'),
                }
                for defect in defects
            ],
            'total': total,
            'open_count': open_count,
            'in_fix_count': in_fix_count,
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

    form = DefectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        defect = form.save(commit=False)
        defect.reported_by = request.user
        defect.save()
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
        project__in=visible_projects_for(request.user),
    )
    form = DefectForm(request.POST or None, instance=defect)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Defecto actualizado correctamente.')
        return redirect('defects:index')

    return render(
        request,
        'defects/form.html',
        {
            'form': form,
            'title': 'Editar Defecto',
            'subtitle': 'Actualiza severidad, prioridad, estado y asignacion sin perder la relacion con ejecuciones.',
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
        project__in=visible_projects_for(request.user),
    )

    if request.method == 'POST':
        defect.delete()
        messages.success(request, 'Defecto eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('defects:index')

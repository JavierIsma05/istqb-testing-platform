from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_action
from apps.core.permissions import (
    can_manage_artifacts,
    get_active_project_for_request,
    is_teacher,
    redirect_if_teacher_readonly,
    visible_projects_for,
)
from apps.core.codes import next_code
from apps.core.lifecycle import requirement_can_be_approved
from apps.projects.models import Project

from .forms import RequirementForm, RequirementImportForm
from .history import record_requirement_version
from .models import Requirement
from .services import RequirementSourceImportError, extract_text_from_source, parse_requirements_from_text


STATUS_BADGES = {
    Requirement.Status.APPROVED: 'success',
    Requirement.Status.REVIEW: 'info',
    Requirement.Status.PENDING: 'warning',
}

REVIEWABLE_STATUSES = (
    Requirement.Status.PENDING,
    Requirement.Status.REVIEW,
)


@login_required
def requirement_list_view(request):
    query = request.GET.get('q', '').strip()
    project_id = request.GET.get('project', '').strip()
    status = request.GET.get('status', '').strip()
    visible_projects = visible_projects_for(request.user, request=request)
    active_project = get_active_project_for_request(request)

    requirements = Requirement.objects.select_related('project').annotate(
        direct_cases=Count('test_cases', distinct=True),
        traced_cases=Count('traceability_links__test_case', distinct=True),
        version_count=Count('versions', distinct=True),
    )
    requirements = requirements.filter(project__in=visible_projects)

    if query:
        requirements = requirements.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )

    if active_project:
        requirements = requirements.filter(project=active_project)
    elif project_id:
        requirements = requirements.filter(project_id=project_id)

    if status:
        requirements = requirements.filter(status=status)

    requirement_items = []
    for requirement in requirements:
        linked_cases = max(requirement.direct_cases or 0, requirement.traced_cases or 0)
        coverage = 100 if linked_cases else 0
        requirement_items.append(
            {
                'requirement': requirement,
                'coverage': coverage,
                'linked_cases': linked_cases,
                'badge': STATUS_BADGES.get(requirement.status, 'muted'),
                'version_count': requirement.version_count or 0,
            }
        )

    total = len(requirement_items)
    approved = sum(1 for item in requirement_items if item['requirement'].status == Requirement.Status.APPROVED)
    in_review = sum(1 for item in requirement_items if item['requirement'].status == Requirement.Status.REVIEW)
    pending = sum(1 for item in requirement_items if item['requirement'].status == Requirement.Status.PENDING)

    return render(
        request,
        'requirements/index.html',
        {
            'requirement_items': requirement_items,
            'total': total,
            'approved': approved,
            'in_review': in_review,
            'pending': pending,
            'projects': visible_projects.order_by('name'),
            'status_choices': Requirement.Status.choices,
            'selected_project': project_id,
            'selected_status': status,
            'query': query,
            'can_manage': can_manage_artifacts(request.user),
            'can_review': is_teacher(request.user),
            'reviewable_statuses': REVIEWABLE_STATUSES,
        },
    )


@login_required
def requirement_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'requirements:index', 'requisitos')
    if readonly_redirect:
        return readonly_redirect

    form = RequirementForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        requirement = form.save(commit=False)
        requirement.code = next_code(Requirement.objects.filter(project=requirement.project), 'REQ')
        requirement.status = Requirement.Status.PENDING
        requirement.created_by = request.user
        requirement.save()
        record_requirement_version(requirement, request.user, 'Creación del requisito')
        log_action(
            request.user,
            'CREATE',
            'Requirement',
            requirement.pk,
            {'project_id': requirement.project_id, 'code': requirement.code, 'title': requirement.title},
        )
        messages.success(request, 'Requisito creado correctamente.')
        return redirect('requirements:index')

    return render(request, 'requirements/form.html', {'form': form, 'title': 'Nuevo Requisito', 'subtitle': 'Registra requisitos funcionales y no funcionales vinculados a un proyecto.'})


@login_required
def requirement_import_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'requirements:index', 'requisitos')
    if readonly_redirect:
        return readonly_redirect

    visible_projects = visible_projects_for(request.user, request=request).order_by('name')
    if request.method == 'POST' and request.POST.get('action') == 'confirm':
        return _confirm_requirement_import(request, visible_projects)

    form = RequirementImportForm(request.POST or None, request.FILES or None, projects=visible_projects)
    preview_items = []
    selected_project = None

    if request.method == 'POST' and form.is_valid():
        import_error = False
        selected_project = form.cleaned_data['project']
        try:
            text = extract_text_from_source(form.cleaned_data['source_file'])
            preview_items = parse_requirements_from_text(text)
        except RequirementSourceImportError as exc:
            import_error = True
            messages.error(request, str(exc))
        if not preview_items and not import_error:
            messages.warning(request, 'No se detectaron requisitos en el documento. Revisa que tenga una fila o línea por requisito.')

    return render(request, 'requirements/import.html', {'form': form, 'preview_items': preview_items, 'selected_project': selected_project, 'type_choices': Requirement.RequirementType.choices, 'priority_choices': Requirement.Priority.choices})


def _confirm_requirement_import(request, visible_projects):
    project = get_object_or_404(visible_projects, pk=request.POST.get('project'))
    titles = request.POST.getlist('title')
    descriptions = request.POST.getlist('description')
    acceptance_criteria = request.POST.getlist('acceptance_criteria')
    requirement_types = request.POST.getlist('requirement_type')
    priorities = request.POST.getlist('priority')
    allowed_types = {value for value, _label in Requirement.RequirementType.choices}
    allowed_priorities = {value for value, _label in Requirement.Priority.choices}
    created = 0

    with transaction.atomic():
        for index, title in enumerate(titles):
            title = title.strip()
            description = descriptions[index].strip() if index < len(descriptions) else ''
            criteria = acceptance_criteria[index].strip() if index < len(acceptance_criteria) else ''
            if not title or not description:
                continue
            requirement_type = requirement_types[index] if index < len(requirement_types) else Requirement.RequirementType.FUNCTIONAL
            priority = priorities[index] if index < len(priorities) else Requirement.Priority.MEDIUM
            requirement = Requirement.objects.create(
                project=project,
                code=next_code(Requirement.objects.filter(project=project), 'REQ'),
                title=title[:180],
                description=description,
                acceptance_criteria=criteria,
                requirement_type=requirement_type if requirement_type in allowed_types else Requirement.RequirementType.FUNCTIONAL,
                priority=priority if priority in allowed_priorities else Requirement.Priority.MEDIUM,
                status=Requirement.Status.PENDING,
                created_by=request.user,
            )
            record_requirement_version(requirement, request.user, 'Importación desde PDF')
            log_action(request.user, 'IMPORT', 'Requirement', requirement.pk, {'project_id': requirement.project_id, 'code': requirement.code, 'title': requirement.title})
            created += 1

    if created:
        messages.success(request, f'{created} requisitos cargados correctamente.')
    else:
        messages.warning(request, 'No se cargó ningún requisito. Mantén título y descripción en al menos una fila.')
    return redirect('requirements:index')


@login_required
def requirement_update_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'requirements:index', 'requisitos')
    if readonly_redirect:
        return readonly_redirect
    requirement = get_object_or_404(Requirement, pk=pk, project__in=visible_projects_for(request.user, request=request))
    form = RequirementForm(request.POST or None, instance=requirement, user=request.user)

    if request.method == 'POST' and form.is_valid():
        original = {field: getattr(requirement, field) for field in ('title', 'description', 'acceptance_criteria', 'requirement_type', 'priority')}
        requirement = form.save()
        if any(getattr(requirement, field) != value for field, value in original.items()) and requirement.status == Requirement.Status.APPROVED:
            requirement.status = Requirement.Status.REVIEW
            requirement.save(update_fields=['status', 'updated_at'])
        record_requirement_version(requirement, request.user, 'Actualización del requisito')
        log_action(request.user, 'UPDATE', 'Requirement', requirement.pk, {'project_id': requirement.project_id, 'code': requirement.code, 'title': requirement.title})
        messages.success(request, 'Requisito actualizado correctamente.')
        return redirect('requirements:index')

    return render(request, 'requirements/form.html', {'form': form, 'title': 'Editar Requisito', 'subtitle': 'Actualiza los datos del requisito sin perder su trazabilidad asociada.'})


@login_required
def requirement_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'requirements:index', 'requisitos')
    if readonly_redirect:
        return readonly_redirect
    requirement = get_object_or_404(Requirement, pk=pk, project__in=visible_projects_for(request.user, request=request))

    if request.method == 'POST':
        if requirement.versions.exists() or requirement.test_cases.exists() or requirement.traceability_links.exists():
            messages.error(request, f'No se puede eliminar {requirement.code} porque forma parte del historial o de la trazabilidad. Conserva el registro y actualiza su estado en lugar de borrarlo.')
            return redirect('requirements:index')
        log_action(request.user, 'DELETE', 'Requirement', requirement.pk, {'project_id': requirement.project_id, 'code': requirement.code, 'title': requirement.title})
        requirement.delete()
        messages.success(request, 'Requisito eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')
    return redirect('requirements:index')


@login_required
def requirement_mark_reviewed_view(request, pk):
    if not is_teacher(request.user):
        messages.error(request, 'Solo los docentes pueden marcar requisitos como revisados.')
        return redirect('requirements:index')
    requirement = get_object_or_404(Requirement, pk=pk, project__in=visible_projects_for(request.user, request=request))
    if request.method != 'POST':
        messages.error(request, 'La revision debe confirmarse desde el listado.')
        return redirect('requirements:index')
    if requirement.status not in REVIEWABLE_STATUSES:
        messages.info(request, f'{requirement.code} no requiere revision docente.')
        return redirect('requirements:index')
    validation = requirement_can_be_approved(requirement)
    if not validation.ok:
        messages.error(request, 'No se puede aprobar el requisito: ' + ' '.join(validation.errors))
        return redirect('requirements:index')
    requirement.status = Requirement.Status.APPROVED
    requirement.save(update_fields=['status'])
    record_requirement_version(requirement, request.user, 'Revision docente')
    log_action(request.user, 'TEACHER_REVIEW', 'Requirement', requirement.pk, {'project_id': requirement.project_id, 'code': requirement.code, 'status': requirement.status})
    messages.success(request, f'{requirement.code} marcado como revisado.')
    return redirect('requirements:index')


@login_required
def requirement_bulk_mark_reviewed_view(request):
    if not is_teacher(request.user):
        messages.error(request, 'Solo los docentes pueden marcar requisitos como revisados.')
        return redirect('requirements:index')
    if request.method != 'POST':
        messages.error(request, 'La revision masiva debe confirmarse desde el listado.')
        return redirect('requirements:index')
    query = request.POST.get('q', '').strip()
    project_id = request.POST.get('project', '').strip()
    status = request.POST.get('status', '').strip()
    requirements = Requirement.objects.filter(project__in=visible_projects_for(request.user, request=request))
    if query:
        requirements = requirements.filter(Q(code__icontains=query) | Q(title__icontains=query) | Q(description__icontains=query))
    if project_id:
        requirements = requirements.filter(project_id=project_id)
    if status:
        requirements = requirements.filter(status=status)
    requirements = requirements.filter(status__in=REVIEWABLE_STATUSES)
    reviewed = 0
    reviewed_items = []
    with transaction.atomic():
        for requirement in requirements:
            validation = requirement_can_be_approved(requirement)
            if not validation.ok:
                continue
            requirement.status = Requirement.Status.APPROVED
            requirement.save(update_fields=['status'])
            record_requirement_version(requirement, request.user, 'Revision docente masiva')
            reviewed_items.append({'id': requirement.pk, 'project_id': requirement.project_id, 'code': requirement.code})
            reviewed += 1
    if reviewed_items:
        log_action(request.user, 'BULK_TEACHER_REVIEW', 'Requirement', '', {'count': reviewed, 'items': reviewed_items})
        messages.success(request, f'{reviewed} requisitos marcados como revisados.')
    else:
        messages.info(request, 'No habia requisitos pendientes en el listado actual.')
    return redirect('requirements:index')


@login_required
def requirement_bulk_delete_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'requirements:index', 'requisitos')
    if readonly_redirect:
        return readonly_redirect
    if request.method != 'POST':
        messages.error(request, 'La eliminacion masiva debe confirmarse desde el listado.')
        return redirect('requirements:index')
    requirement_ids = request.POST.getlist('requirement_ids')
    if not requirement_ids:
        messages.warning(request, 'Selecciona al menos un requisito para eliminar.')
        return redirect('requirements:index')

    selected_requirements = Requirement.objects.filter(pk__in=requirement_ids, project__in=visible_projects_for(request.user, request=request))
    protected_requirements = []
    deletable_requirements = []
    for requirement in selected_requirements:
        if requirement.versions.exists() or requirement.test_cases.exists() or requirement.traceability_links.exists():
            protected_requirements.append(requirement)
        else:
            deletable_requirements.append(requirement)

    if protected_requirements:
        messages.warning(request, f'{len(protected_requirements)} requisito(s) no se eliminaron porque tienen historial o trazabilidad. Los registros históricos deben conservarse.')

    deleted_count = len(deletable_requirements)
    deleted_items = [{'id': item.pk, 'project_id': item.project_id, 'code': item.code, 'title': item.title} for item in deletable_requirements]
    if deleted_items:
        log_action(request.user, 'BULK_DELETE', 'Requirement', '', {'count': deleted_count, 'items': deleted_items})
        for requirement in deletable_requirements:
            requirement.delete()
    if deleted_count:
        messages.success(request, f'{deleted_count} requisitos eliminados correctamente.')
    elif not protected_requirements:
        messages.warning(request, 'No se encontró ningún requisito seleccionable para eliminar.')
    return redirect('requirements:index')

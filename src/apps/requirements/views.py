from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for
from apps.projects.models import Project

from .forms import RequirementForm
from .models import Requirement


STATUS_BADGES = {
    Requirement.Status.APPROVED: 'success',
    Requirement.Status.REVIEW: 'info',
    Requirement.Status.PENDING: 'warning',
    Requirement.Status.CHANGED: 'info',
    Requirement.Status.RETIRED: 'muted',
}


@login_required
def requirement_list_view(request):
    query = request.GET.get('q', '').strip()
    project_id = request.GET.get('project', '').strip()
    status = request.GET.get('status', '').strip()
    visible_projects = visible_projects_for(request.user)

    requirements = Requirement.objects.select_related('project').annotate(
        direct_cases=Count('test_cases', distinct=True),
        traced_cases=Count('traceability_links__test_case', distinct=True),
    )
    requirements = requirements.filter(project__in=visible_projects)

    if query:
        requirements = requirements.filter(
            Q(code__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )

    if project_id:
        requirements = requirements.filter(project_id=project_id)

    if status:
        requirements = requirements.filter(status=status)

    requirement_items = []
    covered = 0
    for requirement in requirements:
        linked_cases = max(requirement.direct_cases or 0, requirement.traced_cases or 0)
        coverage = 100 if linked_cases else 0
        if coverage:
            covered += 1
        requirement_items.append(
            {
                'requirement': requirement,
                'coverage': coverage,
                'linked_cases': linked_cases,
                'badge': STATUS_BADGES.get(requirement.status, 'muted'),
            }
        )

    total = len(requirement_items)
    pending = sum(1 for item in requirement_items if item['requirement'].status != Requirement.Status.APPROVED)
    coverage_percent = round((covered / total) * 100) if total else 0

    return render(
        request,
        'requirements/index.html',
        {
            'requirement_items': requirement_items,
            'total': total,
            'covered': covered,
            'pending': pending,
            'coverage_percent': coverage_percent,
            'projects': visible_projects.order_by('name'),
            'status_choices': Requirement.Status.choices,
            'selected_project': project_id,
            'selected_status': status,
            'query': query,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def requirement_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'requirements:index', 'requisitos')
    if readonly_redirect:
        return readonly_redirect

    form = RequirementForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        requirement = form.save(commit=False)
        requirement.created_by = request.user
        requirement.save()
        return redirect('requirements:index')

    return render(
        request,
        'requirements/form.html',
        {
            'form': form,
            'title': 'Nuevo Requisito',
            'subtitle': 'Registra requisitos funcionales y no funcionales vinculados a un proyecto.',
        },
    )

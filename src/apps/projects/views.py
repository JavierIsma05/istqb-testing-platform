from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.defects.models import Defect
from apps.audit.services import log_action
from apps.core.codes import next_code
from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for
from apps.executions.models import TestExecution
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.users.models import User

from .forms import ProjectForm
from .models import Project


STATUS_BADGES = {
    Project.Status.ACTIVE: 'success',
    Project.Status.PLANNED: 'warning',
    Project.Status.PAUSED: 'warning',
    Project.Status.CLOSED: 'muted',
}


def get_initial_project_status(start_date):
    if start_date and start_date <= timezone.localdate():
        return Project.Status.ACTIVE
    return Project.Status.PLANNED


def build_project_card(project):
    total_cases = project.total_cases or 0
    passed_cases = project.passed_cases or 0
    coverage = round((passed_cases / total_cases) * 100) if total_cases else 0
    members = list(project.members.all())
    student = (
        project.created_by
        if project.created_by and project.created_by.role == User.Roles.STUDENT
        else next((member for member in members if member.role == User.Roles.STUDENT), None)
    )
    tutor = (
        next((member for member in members if member.role == User.Roles.TEACHER), None)
        or project.created_by
        or next(iter(members), None)
    )
    return {
        'project': project,
        'coverage': coverage,
        'total_cases': total_cases,
        'passed_cases': passed_cases,
        'defect_count': project.defect_count or 0,
        'student': student,
        'tutor': tutor,
        'badge': STATUS_BADGES.get(project.status, 'muted'),
    }


@login_required
def project_list_view(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    member_id = request.GET.get('member', request.GET.get('tutor', '')).strip()
    view_mode = request.GET.get('view', 'cards')

    projects = visible_projects_for(request.user, request=request).select_related('created_by').prefetch_related('members').annotate(
        total_cases=Count('test_plans__test_cases', distinct=True),
        passed_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__executions__result='PASSED'),
            distinct=True,
        ),
        defect_count=Count('defects', distinct=True),
    )

    if query:
        projects = projects.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(description__icontains=query)
        )

    if status:
        projects = projects.filter(status=status)

    if member_id:
        selected_member_filter = get_object_or_404(User, pk=member_id)
        if selected_member_filter.role == User.Roles.STUDENT:
            projects = projects.filter(
                Q(members=selected_member_filter) | Q(created_by=selected_member_filter)
            ).distinct()
        else:
            projects = projects.filter(members=selected_member_filter)

    project_cards = [build_project_card(project) for project in projects]
    if request.user.role == User.Roles.TEACHER:
        filter_users = User.objects.filter(
            Q(role=User.Roles.STUDENT),
            Q(projects__in=projects) | Q(project_created__in=projects),
        ).distinct().order_by('first_name', 'last_name', 'email')
        member_filter_label = 'Todos los estudiantes'
    else:
        filter_users = User.objects.filter(role=User.Roles.TEACHER).order_by('first_name', 'last_name', 'email')
        member_filter_label = 'Todos los tutores'

    return render(
        request,
        'projects/index.html',
        {
            'project_cards': project_cards,
            'status_choices': Project.Status.choices,
            'selected_status': status,
            'selected_member': member_id,
            'query': query,
            'filter_users': filter_users,
            'member_filter_label': member_filter_label,
            'view_mode': view_mode,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def project_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'projects:index', 'proyectos')
    if readonly_redirect:
        return readonly_redirect

    form = ProjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.code = next_code(Project.objects.all(), 'PRJ')
        project.status = get_initial_project_status(project.start_date)

        if (
            project.status == Project.Status.ACTIVE
            and visible_projects_for(request.user, request=request).filter(status=Project.Status.ACTIVE).exists()
        ):
            form.add_error(
                'start_date',
                'Ya tienes un proyecto activo. Cierra o pausa el proyecto activo antes de crear otro activo.',
            )
        else:
            project.created_by = request.user
            project.save()
            project.members.add(request.user)
            tutor = form.cleaned_data.get('tutor')
            if tutor:
                project.members.add(tutor)
            log_action(
                request.user,
                'CREATE',
                'Project',
                project.pk,
                {'code': project.code, 'name': project.name, 'status': project.status, 'tutor_id': tutor.pk if tutor else None},
            )
            return redirect('projects:detail', pk=project.pk)

    return render(
        request,
        'projects/form.html',
        {
            'form': form,
            'title': 'Nuevo Proyecto',
            'automatic_status_label': Project.Status.PLANNED.label,
            'subtitle': 'Registra un proyecto de titulación. El estado inicial se asigna automaticamente.',
        },
    )


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(visible_projects_for(request.user, request=None).prefetch_related('members'), pk=pk)
    request.session['active_project_id'] = project.pk
    test_plans = TestPlan.objects.filter(project=project)
    requirements = Requirement.objects.filter(project=project)
    test_cases = TestCase.objects.filter(test_plan__project=project)
    executions = TestExecution.objects.filter(test_case__test_plan__project=project)
    defects = Defect.objects.filter(project=project)
    passed_cases = executions.filter(result=TestExecution.Result.PASSED).values('test_case_id').distinct().count()
    total_cases = test_cases.count()
    coverage = round((passed_cases / total_cases) * 100) if total_cases else 0

    return render(
        request,
        'projects/detail.html',
        {
            'project': project,
            'coverage': coverage,
            'test_plans_count': test_plans.count(),
            'requirements_count': requirements.count(),
            'test_cases_count': total_cases,
            'executions_count': executions.count(),
            'defects_count': defects.count(),
            'recent_requirements': requirements[:5],
            'recent_test_cases': test_cases[:5],
        },
    )


@login_required
@require_POST
def project_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'projects:index', 'proyectos')
    if readonly_redirect:
        return readonly_redirect

    project = get_object_or_404(visible_projects_for(request.user, request=request), pk=pk)
    project_name = project.name
    log_action(
        request.user,
        'DELETE',
        'Project',
        project.pk,
        {'code': project.code, 'name': project.name, 'status': project.status},
    )
    project.delete()
    messages.success(request, f'El proyecto "{project_name}" fue eliminado.')
    return redirect('projects:index')

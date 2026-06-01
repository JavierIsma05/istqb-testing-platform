from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.defects.models import Defect
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


def build_project_card(project):
    total_cases = project.total_cases or 0
    passed_cases = project.passed_cases or 0
    coverage = round((passed_cases / total_cases) * 100) if total_cases else 0
    student = (
        project.created_by
        if project.created_by and project.created_by.role == User.Roles.STUDENT
        else project.members.filter(role=User.Roles.STUDENT).first()
    )
    tutor = (
        project.members.filter(role=User.Roles.TEACHER).first()
        or project.created_by
        or project.members.first()
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

    projects = Project.objects.prefetch_related('members').annotate(
        total_cases=Count('test_plans__test_cases', distinct=True),
        passed_cases=Count(
            'test_plans__test_cases',
            filter=Q(test_plans__test_cases__executions__result='PASSED'),
            distinct=True,
        ),
        defect_count=Count('defects', distinct=True),
    )

    if request.user.role == User.Roles.TEACHER:
        projects = projects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()
    elif request.user.role == User.Roles.STUDENT:
        projects = projects.filter(Q(members=request.user) | Q(created_by=request.user)).distinct()

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
        },
    )


@login_required
def project_create_view(request):
    form = ProjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.created_by = request.user
        project.save()
        form.save_m2m()
        project.members.add(request.user)
        return redirect('projects:detail', pk=project.pk)

    return render(
        request,
        'projects/form.html',
        {
            'form': form,
            'title': 'Nuevo Proyecto',
            'subtitle': 'Registra un proyecto de titulación y define su estado inicial.',
        },
    )


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project.objects.prefetch_related('members'), pk=pk)
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
    project = get_object_or_404(Project, pk=pk)
    project_name = project.name
    project.delete()
    messages.success(request, f'El proyecto "{project_name}" fue eliminado.')
    return redirect('projects:index')

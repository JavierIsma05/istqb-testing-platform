from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect

from apps.projects.models import Project
from apps.users.models import User


def is_teacher(user):
    return user.is_authenticated and user.role == User.Roles.TEACHER


def can_manage_artifacts(user):
    return not is_teacher(user)


def teacher_project_filter(user):
    return Q(members=user) | Q(created_by=user)


def _visible_projects_queryset(user):
    projects = Project.objects.all()

    if not user.is_authenticated:
        return projects.none()

    if user.role == User.Roles.ADMIN:
        return projects

    if is_teacher(user):
        return projects.filter(teacher_project_filter(user)).distinct()

    if user.role == User.Roles.STUDENT:
        return projects.filter(Q(members=user) | Q(created_by=user)).distinct()

    return projects.none()


def get_active_project_for_request(request, user=None):
    if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
        return None

    active_user = user or request.user
    visible_projects = _visible_projects_queryset(active_user)

    project_id = (
        request.GET.get('project', '').strip()
        or request.POST.get('project', '').strip()
        or request.session.get('active_project_id')
    )
    if project_id:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            project_id = None

    if project_id:
        project = visible_projects.filter(pk=project_id).first()
        if project:
            request.session['active_project_id'] = project.pk
            return project

    stored_project_id = request.session.get('active_project_id')
    if stored_project_id:
        try:
            stored_project_id = int(stored_project_id)
        except (TypeError, ValueError):
            stored_project_id = None

    if stored_project_id:
        project = visible_projects.filter(pk=stored_project_id).first()
        if project:
            return project

    return None


def visible_projects_for(user, request=None):
    projects = _visible_projects_queryset(user)

    if request is not None:
        active_project = get_active_project_for_request(request, user)
        if active_project:
            return projects.filter(pk=active_project.pk).distinct()

    return projects


def redirect_if_teacher_readonly(request, route_name, module_name):
    if not is_teacher(request.user):
        return None

    messages.warning(
        request,
        f'Los docentes solo pueden revisar {module_name} en modo lectura.',
    )
    return redirect(route_name)

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


def visible_projects_for(user):
    projects = Project.objects.all()

    if is_teacher(user):
        projects = projects.filter(teacher_project_filter(user)).distinct()

    return projects


def redirect_if_teacher_readonly(request, route_name, module_name):
    if not is_teacher(request.user):
        return None

    messages.warning(
        request,
        f'Los docentes solo pueden revisar {module_name} en modo lectura.',
    )
    return redirect(route_name)

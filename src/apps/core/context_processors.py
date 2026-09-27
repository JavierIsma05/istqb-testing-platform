from apps.core.permissions import get_active_project_for_request, visible_projects_for


def project_context(request):
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_authenticated', False):
        return {'active_project': None, 'teacher_projects': [], 'project_query': ''}

    active_project = get_active_project_for_request(request)
    teacher_projects = []
    if getattr(user, 'is_teacher_role', False):
        teacher_projects = visible_projects_for(user).select_related('tutor', 'created_by').prefetch_related('members')

    return {
        'active_project': active_project,
        'teacher_projects': teacher_projects,
        'project_query': f'?project={active_project.pk}' if active_project and getattr(user, 'is_teacher_role', False) else '',
    }

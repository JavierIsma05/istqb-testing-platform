from django.conf import settings

from apps.core.permissions import get_active_project_for_request, visible_projects_for
from apps.users.models import Profile


def project_context(request):
    demo_accounts = getattr(settings, 'DEMO_ACCOUNTS', []) or []
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_authenticated', False):
        return {'active_project': None, 'teacher_project_options': [], 'project_query': '', 'current_profile': None, 'demo_accounts': demo_accounts}

    active_project = get_active_project_for_request(request)
    current_profile = Profile.objects.filter(user=user).first()
    teacher_projects = []
    if getattr(user, 'is_teacher_role', False):
        teacher_projects = visible_projects_for(user).select_related('tutor', 'created_by').prefetch_related('members')

    return {
        'active_project': active_project,
        'teacher_project_options': teacher_projects,
        'project_query': f'?project={active_project.pk}' if active_project and getattr(user, 'is_teacher_role', False) else '',
        'current_profile': current_profile,
    }

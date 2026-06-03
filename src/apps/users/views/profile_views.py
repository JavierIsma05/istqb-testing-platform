from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core.permissions import visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.notifications.models import Notification
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase


@login_required
def profile_view(request):
    user = request.user
    try:
        profile = user.profile
    except user.__class__.profile.RelatedObjectDoesNotExist:
        profile = None
    projects = visible_projects_for(user).order_by('-created_at')

    project_count = projects.count()
    requirements_count = Requirement.objects.filter(project__in=projects).count()
    test_cases_count = TestCase.objects.filter(test_plan__project__in=projects).count()
    executions_count = TestExecution.objects.filter(test_case__test_plan__project__in=projects).count()
    defects_count = Defect.objects.filter(project__in=projects).count()
    unread_notifications_count = Notification.objects.filter(recipient=user, is_read=False).count()

    return render(
        request,
        'users/profile.html',
        {
            'profile': profile,
            'projects': projects[:5],
            'project_count': project_count,
            'requirements_count': requirements_count,
            'test_cases_count': test_cases_count,
            'executions_count': executions_count,
            'defects_count': defects_count,
            'unread_notifications_count': unread_notifications_count,
        },
    )

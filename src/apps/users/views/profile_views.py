from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from apps.core.permissions import visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.notifications.models import Notification
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.users.forms.profile_forms import ProfileEditForm, ProfilePasswordChangeForm
from apps.users.models import Profile


@login_required
def profile_view(request):
    user = request.user
    try:
        profile = user.profile
    except user.__class__.profile.RelatedObjectDoesNotExist:
        profile = Profile.objects.create(user=user, full_name=user.get_full_name() or user.email)

    profile_form = ProfileEditForm(instance=profile, user=user)
    password_form = ProfilePasswordChangeForm(user=user)
    if request.method == 'POST':
        form_action = request.POST.get('form_action')
        if form_action == 'profile':
            profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=user)
            if profile_form.is_valid():
                saved_profile = profile_form.save()
                saved_profile.full_name = request.user.get_full_name() or request.user.email
                saved_profile.save(update_fields=['full_name'])
                messages.success(request, 'Tu perfil se actualizó correctamente.')
                return redirect('users:profile')
        elif form_action == 'password':
            password_form = ProfilePasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Tu contraseña se cambió correctamente.')
                return redirect('users:profile')
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
            'profile_form': profile_form,
            'password_form': password_form,
            'projects': projects[:5],
            'project_count': project_count,
            'requirements_count': requirements_count,
            'test_cases_count': test_cases_count,
            'executions_count': executions_count,
            'defects_count': defects_count,
            'unread_notifications_count': unread_notifications_count,
        },
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for

from .forms import TestPlanWizardForm
from .models import TestPlan


STATUS_BADGES = {
    TestPlan.Status.APPROVED: 'success',
    TestPlan.Status.REVIEW: 'success',
    TestPlan.Status.DRAFT: 'warning',
    TestPlan.Status.CLOSED: 'muted',
}


@login_required
def testplan_list_view(request):
    plans = TestPlan.objects.select_related('project', 'created_by').order_by('-created_at')
    plans = plans.filter(project__in=visible_projects_for(request.user))
    return render(
        request,
        'testplans/index.html',
        {
            'plans': [
                {
                    'plan': plan,
                    'badge': STATUS_BADGES.get(plan.status, 'muted'),
                }
                for plan in plans
            ],
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def testplan_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request, 'testplans:index', 'planes de prueba')
    if readonly_redirect:
        return readonly_redirect

    form = TestPlanWizardForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        plan = form.save(commit=False)
        plan.created_by = request.user
        plan.save()
        return redirect('testplans:index')

    return render(request, 'testplans/form.html', {'form': form})

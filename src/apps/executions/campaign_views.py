from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.audit.services import log_action
from apps.core.codes import next_code
from apps.core.permissions import can_manage_artifacts, visible_projects_for

from .campaign_forms import BuildArtifactForm, TestRunForm
from .models import BuildArtifact, TestRun


@login_required
def campaign_index_view(request):
    projects = visible_projects_for(request.user, request=request)
    runs = TestRun.objects.filter(project__in=projects).select_related('project', 'test_plan', 'build').annotate(execution_count=Count('executions', distinct=True))
    builds = BuildArtifact.objects.filter(project__in=projects).select_related('project', 'created_by')
    return render(request, 'executions/campaigns.html', {'runs': runs, 'builds': builds, 'can_manage': can_manage_artifacts(request.user)})


@login_required
def build_create_view(request):
    if not can_manage_artifacts(request.user):
        messages.error(request, 'No tienes permisos para registrar builds.')
        return redirect('executions:campaigns')
    form = BuildArtifactForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        build = form.save(commit=False)
        build.created_by = request.user
        build.save()
        log_action(request.user, 'CREATE', 'BuildArtifact', build.pk, {'project_id': build.project_id, 'version': build.version, 'build_number': build.build_number, 'commit_sha': build.commit_sha})
        messages.success(request, 'Build registrada correctamente.')
        return redirect('executions:campaigns')
    return render(request, 'executions/campaign_form.html', {'form': form, 'title': 'Registrar build', 'submit_label': 'Registrar build'})


@login_required
def campaign_create_view(request):
    if not can_manage_artifacts(request.user):
        messages.error(request, 'No tienes permisos para crear campañas.')
        return redirect('executions:campaigns')
    form = TestRunForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        run = form.save(commit=False)
        run.created_by = request.user
        run.code = next_code(TestRun.objects.filter(project=run.project), 'RUN')
        run.save()
        form.save_m2m()
        log_action(request.user, 'CREATE', 'TestRun', run.pk, {'project_id': run.project_id, 'test_plan_id': run.test_plan_id, 'build_id': run.build_id, 'code': run.code})
        messages.success(request, f'Campaña {run.code} creada correctamente.')
        return redirect('executions:campaigns')
    return render(request, 'executions/campaign_form.html', {'form': form, 'title': 'Crear campaña de pruebas', 'submit_label': 'Crear campaña'})


@login_required
def campaign_start_view(request, pk):
    run = get_object_or_404(TestRun, pk=pk, project__in=visible_projects_for(request.user, request=request))
    if request.method == 'POST' and run.status == TestRun.Status.PLANNED:
        run.status = TestRun.Status.RUNNING
        run.started_at = timezone.now()
        run.save(update_fields=['status', 'started_at'])
        log_action(request.user, 'STATUS_CHANGE', 'TestRun', run.pk, {'status': run.status})
        messages.success(request, 'Campaña iniciada.')
    return redirect('executions:campaigns')


@login_required
def campaign_complete_view(request, pk):
    run = get_object_or_404(TestRun, pk=pk, project__in=visible_projects_for(request.user, request=request))
    if request.method == 'POST' and run.status in (TestRun.Status.RUNNING, TestRun.Status.PAUSED):
        run.verdict = run.calculate_verdict()
        if run.verdict == TestRun.Verdict.PENDING:
            messages.error(request, 'No se puede cerrar la campaña: aún hay casos sin ejecución completa.')
            return redirect('executions:campaigns')
        run.status = TestRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=['status', 'verdict', 'completed_at'])
        log_action(request.user, 'STATUS_CHANGE', 'TestRun', run.pk, {'status': run.status, 'verdict': run.verdict})
        messages.success(request, f'Campaña cerrada con veredicto: {run.get_verdict_display()}.')
    return redirect('executions:campaigns')

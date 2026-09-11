from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from apps.core.permissions import admin_required
from apps.projects.models import Project
from apps.users.models import User

from .models import AuditLog


@login_required
@admin_required
def audit_list_view(request):
    logs = AuditLog.objects.select_related('actor')
    action = request.GET.get('action', '').strip()
    entity = request.GET.get('entity', '').strip()
    actor_id = request.GET.get('actor', '').strip()
    project_id = request.GET.get('project', '').strip()
    query = request.GET.get('q', '').strip()

    if action:
        logs = logs.filter(action=action)
    if entity:
        logs = logs.filter(entity=entity)
    if actor_id.isdigit():
        logs = logs.filter(actor_id=actor_id)
    if project_id.isdigit():
        logs = logs.filter(
            Q(metadata__project_id=int(project_id))
            | Q(metadata__project_id=str(project_id))
        )
    if query:
        logs = logs.filter(
            Q(entity_id__icontains=query)
            | Q(actor__email__icontains=query)
            | Q(metadata__icontains=query)
        )

    paginator = Paginator(logs, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'audit/index.html',
        {
            'logs': page,
            'actions': AuditLog.objects.values_list('action', flat=True).distinct().order_by('action'),
            'entities': AuditLog.objects.values_list('entity', flat=True).distinct().order_by('entity'),
            'actors': User.objects.filter(pk__in=AuditLog.objects.filter(actor__isnull=False).values('actor_id')).order_by('email'),
            'projects': Project.objects.order_by('name'),
            'selected_action': action,
            'selected_entity': entity,
            'selected_actor': actor_id,
            'selected_project': project_id,
            'query': query,
        },
    )

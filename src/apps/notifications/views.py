from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.projects.models import Project
from apps.users.models import User

from .models import Notification


def get_project_student(project):
    if project.created_by and project.created_by.role == User.Roles.STUDENT:
        return project.created_by

    return project.members.filter(role=User.Roles.STUDENT).first()


@login_required
def notification_list_view(request):
    status = request.GET.get('status', 'all')
    notifications = request.user.notifications.select_related('sender', 'project')

    if status == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status == 'read':
        notifications = notifications.filter(is_read=True)

    return render(
        request,
        'notifications/index.html',
        {
            'notifications': notifications,
            'selected_status': status,
            'total_count': request.user.notifications.count(),
            'unread_count': request.user.notifications.filter(is_read=False).count(),
            'read_count': request.user.notifications.filter(is_read=True).count(),
        },
    )


@login_required
@require_POST
def notification_mark_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read', 'updated_at'])
    return redirect(request.POST.get('next') or 'notifications:index')


@login_required
@require_POST
def notification_mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications:index')


@login_required
@require_POST
def send_project_message_view(request):
    if request.user.role != User.Roles.TEACHER:
        messages.error(request, 'Solo los docentes pueden enviar mensajes desde esta acción.')
        return redirect('dashboard')

    project_id = request.POST.get('project')
    message = request.POST.get('message', '').strip()
    next_url = request.POST.get('next') or reverse('dashboard')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('dashboard')

    project = get_object_or_404(
        Project.objects.prefetch_related('members'),
        Q(members=request.user) | Q(created_by=request.user),
        pk=project_id,
    )
    student = get_project_student(project)

    if not student:
        messages.error(request, 'Este proyecto no tiene estudiante asignado para recibir el mensaje.')
        return redirect(next_url)

    if not message:
        messages.error(request, 'Escribe un mensaje antes de enviarlo.')
        return redirect(next_url)

    notification = Notification.objects.create(
        recipient=student,
        sender=request.user,
        project=project,
        title=f'Mensaje del tutor: {project.name}',
        message=message,
        url=reverse('projects:detail', args=[project.pk]),
    )
    log_action(
        request.user,
        'SEND',
        'Notification',
        notification.pk,
        {'project_id': project.pk, 'recipient_id': student.pk, 'title': notification.title},
    )
    messages.success(request, f'Mensaje enviado a {student.get_full_name() or student.email}.')
    return redirect(next_url)

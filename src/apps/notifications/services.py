from django.urls import reverse

from apps.users.models import User

from .models import Notification


def notify_project_tutor(project, *, sender=None, title, message, url_name=None, url_args=None):
    """Create an internal notification for the project's tutor when applicable."""
    recipient = project.tutor
    if not recipient or recipient.role != User.Roles.TEACHER or recipient == sender:
        return None
    url = ''
    if url_name:
        url = reverse(url_name, args=url_args or [])
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        project=project,
        title=title,
        message=message,
        url=url,
    )

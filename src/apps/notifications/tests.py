import pytest

from apps.notifications.models import Notification
from apps.notifications.services import notify_project_tutor
from apps.users.models import User


@pytest.mark.django_db
def test_notificacion_se_crea_como_no_leida(project, user, admin_user):
    notification = Notification.objects.create(
        recipient=user,
        sender=admin_user,
        project=project,
        title='Nuevo mensaje del proyecto',
        message='Revisa las observaciones del plan.',
        url='/projects/1/',
    )

    assert not notification.is_read
    assert notification.sender == admin_user
    assert str(notification) == 'Nuevo mensaje del proyecto'


@pytest.mark.django_db
def test_usuario_cuenta_notificaciones_no_leidas(user):
    Notification.objects.create(
        recipient=user,
        title='Pendiente',
        message='Esta notificacion debe contarse.',
    )
    Notification.objects.create(
        recipient=user,
        title='Leida',
        message='Esta notificacion no debe contarse.',
        is_read=True,
    )

    assert user.unread_notifications_count == 1


@pytest.mark.django_db
def test_notificar_tutor_crea_aviso_con_enlace(project, user, admin_user):
    admin_user.role = User.Roles.TEACHER
    admin_user.save(update_fields=['role'])
    project.tutor = admin_user
    project.save(update_fields=['tutor'])

    notification = notify_project_tutor(
        project,
        sender=user,
        title='Nuevo informe',
        message='Se generó un informe.',
        url_name='reports:index',
    )

    assert notification.recipient == admin_user
    assert notification.url == '/reports/'
    assert not notification.is_read


@pytest.mark.django_db
def test_notificar_tutor_no_crea_aviso_si_el_tutor_es_el_emisor(project, admin_user):
    admin_user.role = User.Roles.TEACHER
    admin_user.save(update_fields=['role'])
    project.tutor = admin_user
    project.save(update_fields=['tutor'])

    notification = notify_project_tutor(
        project,
        sender=admin_user,
        title='Sin duplicado',
        message='No debe auto-notificarse.',
    )

    assert notification is None

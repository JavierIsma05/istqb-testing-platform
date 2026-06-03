import pytest

from apps.notifications.models import Notification


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

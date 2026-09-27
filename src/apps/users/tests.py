import pytest
import base64
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.users.models import Profile


@pytest.mark.django_db
def test_usuario_se_crea_con_email_como_identificador():
    user = get_user_model().objects.create_user(
        email='student@example.com',
        password='StrongPass123',
    )

    assert user.email == 'student@example.com'
    assert user.username is None
    assert user.is_student_role
    assert not user.is_teacher_role
    assert not user.is_admin_role
    assert str(user) == 'student@example.com'


@pytest.mark.django_db
def test_usuario_no_se_crea_sin_email():
    with pytest.raises(ValueError, match='correo'):
        get_user_model().objects.create_user(
            email='',
            password='StrongPass123',
        )


@pytest.mark.django_db
def test_superusuario_se_crea_con_permisos_de_administrador():
    user = get_user_model().objects.create_superuser(
        email='admin@example.com',
        password='StrongPass123',
    )

    assert user.is_staff
    assert user.is_superuser
    assert user.is_active


@pytest.mark.django_db
def test_usuario_puede_editar_sus_datos_personales(client):
    user = get_user_model().objects.create_user(
        email='profile-edit@example.com',
        password='StrongPass123',
        first_name='Nombre',
        last_name='Anterior',
    )
    client.force_login(user)

    response = client.post(reverse('users:profile'), {
        'form_action': 'profile',
        'first_name': 'Nombre Nuevo',
        'last_name': 'Apellido Nuevo',
        'bio': 'Docente y revisor de calidad.',
    })

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.first_name == 'Nombre Nuevo'
    assert user.last_name == 'Apellido Nuevo'
    assert Profile.objects.get(user=user).bio == 'Docente y revisor de calidad.'


@pytest.mark.django_db
def test_usuario_puede_cambiar_su_contrasena_desde_el_perfil(client):
    user = get_user_model().objects.create_user(
        email='profile-password@example.com',
        password='OldStrongPass123',
    )
    client.force_login(user)

    response = client.post(reverse('users:profile'), {
        'form_action': 'password',
        'old_password': 'OldStrongPass123',
        'new_password1': 'NewStrongPass456',
        'new_password2': 'NewStrongPass456',
    })

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password('NewStrongPass456')


@pytest.mark.django_db
def test_navbar_muestra_la_foto_guardada_del_perfil(client):
    user = get_user_model().objects.create_user(
        email='profile-avatar@example.com',
        password='StrongPass123',
        first_name='Avatar',
        last_name='Test',
    )
    client.force_login(user)
    image = SimpleUploadedFile(
        'avatar.png',
        base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='),
        content_type='image/png',
    )

    response = client.post(reverse('users:profile'), {
        'form_action': 'profile',
        'first_name': 'Avatar',
        'last_name': 'Test',
        'bio': '',
        'avatar': image,
    }, follow=True)

    assert response.status_code == 200
    assert b'class="avatar"' in response.content
    assert b'avatars/avatar' in response.content

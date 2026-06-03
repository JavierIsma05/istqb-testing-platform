import pytest
from django.contrib.auth import get_user_model


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

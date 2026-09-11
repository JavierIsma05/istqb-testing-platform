from django.urls import reverse
import pytest

from apps.users.models import User


def test_pagina_de_login_responde_correctamente(client):
    response = client.get(reverse('login'))

    assert response.status_code == 200


def test_pagina_de_registro_responde_correctamente(client):
    response = client.get(reverse('register'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_registro_publico_crea_estudiante_aunque_se_envie_rol_tutor(client):
    response = client.post(
        reverse('register'),
        data={
            'first_name': 'Ana',
            'last_name': 'Estudiante',
            'email': 'ana@example.edu',
            'role': User.Roles.TEACHER,
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        },
    )

    user = User.objects.get(email='ana@example.edu')

    assert response.status_code == 302
    assert user.role == User.Roles.STUDENT


@pytest.mark.django_db
def test_registro_publico_rechaza_correo_personal(client):
    response = client.post(
        reverse('register'),
        data={
            'first_name': 'Ana',
            'last_name': 'Estudiante',
            'email': 'ana@gmail.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        },
    )

    assert response.status_code == 200
    assert not User.objects.filter(email='ana@gmail.com').exists()


@pytest.mark.django_db
def test_registro_normaliza_correo_institucional(client):
    response = client.post(
        reverse('register'),
        data={
            'first_name': 'Ana',
            'last_name': 'Estudiante',
            'email': '  ANA@UNIVERSIDAD.EDU  ',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        },
    )

    assert response.status_code == 302
    assert User.objects.filter(email='ana@universidad.edu').exists()


@pytest.mark.django_db
def test_create_superuser_fuerza_rol_administrador():
    user = User.objects.create_superuser(
        email='root@example.edu',
        password='StrongPass123',
        role=User.Roles.STUDENT,
        is_staff=False,
        is_superuser=False,
    )

    assert user.role == User.Roles.ADMIN
    assert user.is_staff is True
    assert user.is_superuser is True

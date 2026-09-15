import pytest
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

from apps.projects.models import Project
from apps.core.module_views import _visible_objects
from apps.core.permissions import can_manage_artifacts, can_manage_users, is_admin, is_student, is_teacher, visible_projects_for
from apps.requirements.models import Requirement
from apps.users.models import User


def test_configuracion_base_cubre_seguridad_no_funcional():
    assert settings.CSRF_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.X_FRAME_OPTIONS == 'DENY'
    assert settings.AUTH_PASSWORD_VALIDATORS
    assert settings.LOGIN_URL == 'login'
    assert settings.LANGUAGE_CODE == 'es-ec'
    assert settings.TIME_ZONE == 'America/Guayaquil'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'route_name',
    [
        'dashboard',
        'projects:index',
        'requirements:index',
        'executions:index',
        'reports:index',
    ],
)
def test_rutas_criticas_redirigen_a_login_sin_sesion(client, route_name):
    response = client.get(reverse(route_name))

    assert response.status_code == 302
    assert reverse('login') in response['Location']


@pytest.mark.django_db
def test_listado_de_proyectos_mantiene_consultas_controladas(client, user):
    for index in range(12):
        Project.objects.create(
            code=f'PRJ-NF-{index:03d}',
            name=f'Proyecto no funcional {index}',
            description='Proyecto usado para validar rendimiento basico del listado.',
            created_by=user,
        )
    client.force_login(user)

    with CaptureQueriesContext(connection) as captured:
        response = client.get(reverse('projects:index'))

    assert response.status_code == 200
    assert len(captured) <= 12


@pytest.mark.django_db
def test_dashboard_mantiene_consultas_controladas(client, project, test_case, execution, user):
    client.force_login(user)

    with CaptureQueriesContext(connection) as captured:
        response = client.get(reverse('dashboard'))

    assert response.status_code == 200
    assert project.name.encode() in response.content
    assert test_case.code.encode() in response.content
    assert len(captured) <= 20


def test_permisos_de_rol_no_conceden_acceso_a_usuarios_anonimos():
    anonymous = AnonymousUser()

    assert not is_admin(anonymous)
    assert not is_teacher(anonymous)
    assert not is_student(anonymous)
    assert not can_manage_artifacts(anonymous)
    assert not can_manage_users(anonymous)


@pytest.mark.parametrize(
    ('role', 'can_manage_artifacts_value'),
    [
        (User.Roles.ADMIN, True),
        (User.Roles.STUDENT, True),
        (User.Roles.TEACHER, False),
    ],
)
def test_permisos_de_rol_distinguen_gestion_de_articulos(role, can_manage_artifacts_value):
    user = User(role=role)

    assert can_manage_artifacts(user) is can_manage_artifacts_value
    assert can_manage_users(user) is (role == User.Roles.ADMIN)


@pytest.mark.django_db
def test_scaffold_generico_no_expone_requisitos_de_otro_proyecto(user):
    owned = Project.objects.create(
        code='PRJ-OWN-001',
        name='Proyecto visible',
        description='Visible para el usuario.',
        created_by=user,
    )
    other_user = User.objects.create_user(
        email='otro-proyecto@example.edu',
        password='StrongPass123!',
        role=User.Roles.STUDENT,
    )
    hidden = Project.objects.create(
        code='PRJ-HID-001',
        name='Proyecto oculto',
        description='No debe aparecer.',
        created_by=other_user,
    )
    visible_projects = visible_projects_for(user)
    Requirement.objects.create(
        project=owned,
        code='REQ-OWN-001',
        title='Requisito visible',
        description='Contenido visible.',
    )
    Requirement.objects.create(
        project=hidden,
        code='REQ-HID-001',
        title='Requisito oculto',
        description='Contenido que no debe exponerse.',
    )

    objects = _visible_objects(Requirement, visible_projects, user)

    assert list(objects.values_list('code', flat=True)) == ['REQ-OWN-001']

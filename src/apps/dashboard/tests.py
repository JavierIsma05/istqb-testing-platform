from django.urls import reverse
import pytest

from apps.executions.models import TestExecution as ExecutionModel


def test_dashboard_redirige_a_login_si_no_hay_sesion(client):
    response = client.get(reverse('dashboard'))

    assert response.status_code == 302
    assert reverse('login') in response['Location']


@pytest.mark.django_db
def test_dashboard_muestra_proyectos_y_actividad_reales(client, project, test_case, user):
    ExecutionModel.objects.create(
        test_case=test_case,
        executed_by=user,
        result=ExecutionModel.Result.PASSED,
        notes='Ejecucion real para dashboard.',
    )
    client.force_login(user)

    response = client.get(reverse('dashboard'))

    assert response.status_code == 200
    assert project.name.encode() in response.content
    assert test_case.code.encode() in response.content
    assert b'Sistema de Gestion Academica' not in response.content
    assert b'TC-045' not in response.content


@pytest.mark.django_db
def test_endpoint_de_progreso_de_fases_devuelve_porcentaje_para_estudiante(client, project, user):
    client.force_login(user)
    response = client.get('/dashboard/phase-progress/')

    assert response.status_code == 200
    data = response.json()
    assert data['available'] is True
    assert 0 <= data['percentage'] < 31
    assert data['tone'] == 'danger'


@pytest.mark.django_db
def test_docente_puede_seleccionar_proyecto_y_los_requisitos_quedan_limitados(client, db):
    from django.contrib.auth import get_user_model
    from apps.projects.models import Project
    from apps.requirements.models import Requirement

    User = get_user_model()
    teacher = User.objects.create_user(email='teacher-scope@example.com', password='StrongPass123', role=User.Roles.TEACHER)
    first = Project.objects.create(code='PRJ-SCOPE-1', name='Proyecto Uno', created_by=teacher)
    second = Project.objects.create(code='PRJ-SCOPE-2', name='Proyecto Dos', created_by=teacher)
    Requirement.objects.create(project=first, code='REQ-ONE', title='Requisito Uno', description='Primero', created_by=teacher)
    Requirement.objects.create(project=second, code='REQ-TWO', title='Requisito Dos', description='Segundo', created_by=teacher)
    client.force_login(teacher)

    projects_response = client.get(reverse('projects:index'))
    scoped_response = client.get(f'{reverse("requirements:index")}?project={first.pk}')

    assert projects_response.status_code == 200
    assert b'Proyecto Uno' in projects_response.content
    assert b'Proyecto Dos' in projects_response.content
    assert scoped_response.status_code == 200
    assert b'REQ-ONE' in scoped_response.content
    assert b'REQ-TWO' not in scoped_response.content


@pytest.mark.django_db
def test_dashboard_docente_renderiza_selector_de_proyecto(client):
    from django.contrib.auth import get_user_model
    from apps.projects.models import Project

    User = get_user_model()
    teacher = User.objects.create_user(email='teacher-navbar@example.com', password='StrongPass123', role=User.Roles.TEACHER)
    Project.objects.create(code='PRJ-NAV-1', name='Proyecto del selector', created_by=teacher)
    client.force_login(teacher)

    response = client.get(reverse('dashboard'))

    assert response.status_code == 200
    assert b'PRJ-NAV-1' in response.content

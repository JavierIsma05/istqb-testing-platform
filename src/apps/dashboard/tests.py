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

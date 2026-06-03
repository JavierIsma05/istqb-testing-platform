import pytest
from django.urls import reverse

from apps.projects.forms import ProjectForm
from apps.projects.models import Project


@pytest.mark.django_db
def test_proyecto_guarda_codigo_nombre_y_estado_por_defecto(project):
    assert project.code == 'PRJ-001'
    assert project.name == 'Plataforma ISTQB'
    assert project.status == Project.Status.PLANNED
    assert str(project) == 'PRJ-001 - Plataforma ISTQB'


@pytest.mark.django_db
def test_formulario_de_proyecto_es_valido_con_datos_minimos():
    form = ProjectForm(
        data={
            'code': 'PRJ-002',
            'name': 'Sistema academico',
            'description': 'Proyecto de pruebas academicas',
            'status': Project.Status.ACTIVE,
            'members': [],
        }
    )

    assert form.is_valid()


def test_lista_de_proyectos_redirige_a_login_si_no_hay_sesion(client):
    response = client.get(reverse('projects:index'))

    assert response.status_code == 302
    assert reverse('login') in response['Location']

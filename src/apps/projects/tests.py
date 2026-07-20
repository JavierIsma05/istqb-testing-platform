import pytest
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model

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
            'members': [],
        }
    )

    assert form.is_valid()
    assert 'status' not in form.fields


@pytest.mark.django_db
def test_creacion_de_proyecto_ignora_estado_enviado_por_post(client, user):
    client.force_login(user)

    response = client.post(
        reverse('projects:create'),
        data={
            'name': 'Sistema academico',
            'description': 'Proyecto de pruebas academicas',
            'status': Project.Status.ACTIVE,
            'members': [],
        },
    )

    project = Project.objects.get(name='Sistema academico')

    assert response.status_code == 302
    assert project.status == Project.Status.PLANNED


@pytest.mark.django_db
def test_creacion_de_proyecto_con_fecha_de_inicio_actual_queda_activa(client, user):
    client.force_login(user)

    response = client.post(
        reverse('projects:create'),
        data={
            'name': 'Sistema con inicio actual',
            'description': 'Proyecto que empieza hoy',
            'start_date': timezone.localdate().isoformat(),
            'members': [],
        },
    )

    project = Project.objects.get(name='Sistema con inicio actual')

    assert response.status_code == 302
    assert project.status == Project.Status.ACTIVE


def test_lista_de_proyectos_redirige_a_login_si_no_hay_sesion(client):
    response = client.get(reverse('projects:index'))

    assert response.status_code == 302
    assert reverse('login') in response['Location']


@pytest.mark.django_db
def test_estudiante_no_puede_ver_detalle_de_proyecto_ajeno(client, user):
    other_user = get_user_model().objects.create_user(
        email='otro@example.edu',
        password='StrongPass123',
    )
    other_project = Project.objects.create(
        code='PRJ-999',
        name='Proyecto ajeno',
        created_by=other_user,
    )

    client.force_login(user)
    response = client.get(reverse('projects:detail', args=[other_project.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_detalle_de_proyecto_visible_actualiza_proyecto_activo(client, project, user):
    other_project = Project.objects.create(
        code='PRJ-010',
        name='Proyecto visible alterno',
        created_by=user,
    )
    client.force_login(user)
    session = client.session
    session['active_project_id'] = project.pk
    session.save()

    response = client.get(reverse('projects:detail', args=[other_project.pk]))

    assert response.status_code == 200
    assert client.session['active_project_id'] == other_project.pk


@pytest.mark.django_db
def test_tutor_no_puede_crear_proyectos(client):
    tutor = get_user_model().objects.create_user(
        email='tutor@example.edu',
        password='StrongPass123',
        role=get_user_model().Roles.TEACHER,
    )

    client.force_login(tutor)
    response = client.post(
        reverse('projects:create'),
        data={
            'name': 'Proyecto desde tutor',
            'description': 'No debe crearse',
        },
    )

    assert response.status_code == 302
    assert not Project.objects.filter(name='Proyecto desde tutor').exists()


@pytest.mark.django_db
def test_estudiante_no_puede_crear_otro_proyecto_activo(client, user):
    Project.objects.create(
        code='PRJ-010',
        name='Proyecto activo existente',
        status=Project.Status.ACTIVE,
        created_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse('projects:create'),
        data={
            'name': 'Segundo proyecto activo',
            'description': 'No debe quedar activo',
            'start_date': timezone.localdate().isoformat(),
        },
    )

    assert response.status_code == 200
    assert not Project.objects.filter(name='Segundo proyecto activo').exists()


@pytest.mark.django_db
def test_proyecto_se_vincula_a_tutor_por_correo(client, user):
    tutor = get_user_model().objects.create_user(
        email='tutor@example.edu',
        password='StrongPass123',
        role=get_user_model().Roles.TEACHER,
    )

    client.force_login(user)
    response = client.post(
        reverse('projects:create'),
        data={
            'name': 'Proyecto con tutor',
            'description': 'Proyecto de titulacion',
            'tutor_email': tutor.email,
        },
    )

    project = Project.objects.get(name='Proyecto con tutor')

    assert response.status_code == 302
    assert project.members.filter(pk=user.pk).exists()
    assert project.members.filter(pk=tutor.pk).exists()

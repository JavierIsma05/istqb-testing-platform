import pytest
from django.urls import reverse

from apps.requirements.forms import RequirementForm, RequirementImportForm
from apps.requirements.models import Requirement, RequirementVersion
from apps.audit.models import AuditLog
from apps.requirements.services import parse_requirements_from_text


@pytest.mark.django_db
def test_requisito_se_asocia_a_proyecto_y_tiene_prioridad_media_por_defecto(requirement, project):
    assert requirement.project == project
    assert requirement.priority == Requirement.Priority.MEDIUM
    assert requirement.status == Requirement.Status.PENDING
    assert str(requirement) == 'REQ-001 - Autenticacion de usuarios'


@pytest.mark.django_db
def test_formulario_de_requisito_es_valido_con_datos_obligatorios(project):
    form = RequirementForm(
        data={
            'project': project.id,
            'code': 'REQ-002',
            'title': 'Gestion de proyectos',
            'description': 'El sistema permite crear proyectos de pruebas.',
            'requirement_type': Requirement.RequirementType.FUNCTIONAL,
            'priority': Requirement.Priority.HIGH,
            'status': Requirement.Status.REVIEW,
        }
    )

    assert form.is_valid()


def test_detector_extrae_requisitos_desde_texto():
    text = """
    REQ-001: El sistema debe permitir iniciar sesion con correo y clave.
    RNF-002: El sistema debe responder en menos de 2 segundos con prioridad alta.
    Nota: este texto no es un requisito.
    """

    items = parse_requirements_from_text(text)

    assert len(items) == 2
    assert items[0].title == 'El sistema debe permitir iniciar sesion con correo y clave'
    assert items[0].requirement_type == Requirement.RequirementType.FUNCTIONAL
    assert items[1].requirement_type == Requirement.RequirementType.NON_FUNCTIONAL
    assert items[1].priority == Requirement.Priority.HIGH


@pytest.mark.django_db
def test_formulario_de_importacion_no_pide_valores_por_defecto(project):
    form = RequirementImportForm(projects=project.__class__.objects.filter(pk=project.pk))

    assert 'project' in form.fields
    assert 'pdf_file' in form.fields
    assert 'requirement_type' not in form.fields
    assert 'priority' not in form.fields
    assert 'status' not in form.fields


def test_detector_clasifica_pdf_mixto_sin_defaults():
    text = """
    RF-001: El sistema debe permitir registrar usuarios desde el panel principal.
    RNF-002: El sistema debe garantizar disponibilidad del 99% y tiempo de respuesta menor a 2 segundos con prioridad alta.
    3. La plataforma debe cifrar las credenciales de los usuarios.
    """

    items = parse_requirements_from_text(text)

    assert len(items) == 3
    assert items[0].requirement_type == Requirement.RequirementType.FUNCTIONAL
    assert items[1].requirement_type == Requirement.RequirementType.NON_FUNCTIONAL
    assert items[1].priority == Requirement.Priority.HIGH
    assert items[2].requirement_type == Requirement.RequirementType.NON_FUNCTIONAL


@pytest.mark.django_db
def test_eliminacion_masiva_borra_requisitos_seleccionados(client, project, user):
    first = Requirement.objects.create(
        project=project,
        code='REQ-010',
        title='Primer requisito',
        description='El sistema debe permitir la primera accion.',
        created_by=user,
    )
    second = Requirement.objects.create(
        project=project,
        code='REQ-011',
        title='Segundo requisito',
        description='El sistema debe permitir la segunda accion.',
        created_by=user,
    )
    remaining = Requirement.objects.create(
        project=project,
        code='REQ-012',
        title='Requisito no seleccionado',
        description='El sistema debe conservar este requisito.',
        created_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse('requirements:bulk_delete'),
        {'requirement_ids': [first.pk, second.pk]},
    )

    assert response.status_code == 302
    assert not Requirement.objects.filter(pk__in=[first.pk, second.pk]).exists()
    assert Requirement.objects.filter(pk=remaining.pk).exists()


@pytest.mark.django_db
def test_confirmacion_de_importacion_guarda_estado_pendiente_aunque_se_envie_otro(client, project, user):
    client.force_login(user)

    response = client.post(
        reverse('requirements:import'),
        {
            'action': 'confirm',
            'project': project.pk,
            'title': ['Requisito importado'],
            'description': ['El sistema debe permitir importar requisitos.'],
            'requirement_type': [Requirement.RequirementType.FUNCTIONAL],
            'priority': [Requirement.Priority.HIGH],
            'status': [Requirement.Status.APPROVED],
        },
    )

    imported = Requirement.objects.get(title='Requisito importado')

    assert response.status_code == 302
    assert imported.priority == Requirement.Priority.HIGH
    assert imported.status == Requirement.Status.PENDING


@pytest.mark.django_db
def test_confirmacion_de_importacion_numera_solo_requisitos_enviados(client, project, user):
    client.force_login(user)

    response = client.post(
        reverse('requirements:import'),
        {
            'action': 'confirm',
            'project': project.pk,
            'title': ['Segundo detectado', 'Tercero detectado'],
            'description': [
                'El sistema debe conservar el segundo requisito detectado.',
                'El sistema debe conservar el tercer requisito detectado.',
            ],
            'requirement_type': [
                Requirement.RequirementType.FUNCTIONAL,
                Requirement.RequirementType.NON_FUNCTIONAL,
            ],
            'priority': [
                Requirement.Priority.MEDIUM,
                Requirement.Priority.HIGH,
            ],
        },
    )

    imported = list(Requirement.objects.filter(title__endswith='detectado').order_by('code'))

    assert response.status_code == 302
    assert [item.code for item in imported] == ['REQ-000', 'REQ-001']
    assert [item.title for item in imported] == ['Segundo detectado', 'Tercero detectado']


@pytest.mark.django_db
def test_creacion_de_requisito_registra_version_inicial(client, project, user):
    client.force_login(user)

    response = client.post(
        reverse('requirements:create'),
        {
            'project': project.id,
            'title': 'Requisito versionado',
            'description': 'El sistema debe guardar historial inicial.',
            'requirement_type': Requirement.RequirementType.FUNCTIONAL,
            'priority': Requirement.Priority.HIGH,
            'status': Requirement.Status.PENDING,
        },
    )

    requirement = Requirement.objects.get(title='Requisito versionado')
    version = requirement.versions.get()

    assert response.status_code == 302
    assert version.version_number == 1
    assert version.changed_by == user
    assert version.snapshot['title'] == requirement.title
    assert AuditLog.objects.filter(action='CREATE', entity='Requirement', entity_id=str(requirement.pk)).exists()


@pytest.mark.django_db
def test_actualizacion_de_requisito_agrega_nueva_version(client, requirement, user):
    RequirementVersion.objects.create(
        requirement=requirement,
        version_number=1,
        title=requirement.title,
        description=requirement.description,
        requirement_type=requirement.requirement_type,
        priority=requirement.priority,
        status=requirement.status,
        changed_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse('requirements:edit', args=[requirement.pk]),
        {
            'project': requirement.project_id,
            'title': 'Autenticacion actualizada',
            'description': 'El sistema debe guardar cada cambio.',
            'requirement_type': Requirement.RequirementType.FUNCTIONAL,
            'priority': Requirement.Priority.CRITICAL,
            'status': Requirement.Status.CHANGED,
        },
    )

    requirement.refresh_from_db()

    assert response.status_code == 302
    assert requirement.versions.count() == 2
    assert requirement.versions.first().version_number == 2
    assert requirement.versions.first().title == 'Autenticacion actualizada'
    assert AuditLog.objects.filter(action='UPDATE', entity='Requirement', entity_id=str(requirement.pk)).exists()

import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.drafts.models import FormDraft
from apps.drafts.services import save_draft, draft_key
from apps.testcases.models import TestCase as CaseModel
from apps.testplans.models import TestPlan as PlanModel


def _post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type='application/json')


@pytest.mark.django_db
def test_borrador_se_guarda_y_recupera(client, user):
    client.force_login(user)
    payload = {'module': 'testplan', 'project_id': 7, 'object_id': 0, 'data': {'name': 'Plan en borrador'}}

    save = _post_json(client, reverse('drafts:save'), payload)

    assert save.status_code == 200
    assert save.json()['ok'] is True

    response = client.get(reverse('drafts:get'), {'module': 'testplan', 'project_id': 7, 'object_id': 0})

    assert response.status_code == 200
    assert response.json()['found'] is True
    assert response.json()['data'] == {'name': 'Plan en borrador'}


@pytest.mark.django_db
def test_borrador_inexistente_responde_false(client, user):
    client.force_login(user)

    response = client.get(reverse('drafts:get'), {'module': 'testcase', 'project_id': 1, 'object_id': 0})

    assert response.status_code == 200
    assert response.json()['found'] is False


@pytest.mark.django_db
def test_borrador_se_limpia(client, user):
    save_draft(user, 'testplan', {'name': 'Borrador temporal'}, 3, 0)
    client.force_login(user)

    response = _post_json(client, reverse('drafts:clear'), {'module': 'testplan', 'project_id': 3, 'object_id': 0})

    assert response.status_code == 200
    assert response.json()['ok'] is True
    assert FormDraft.objects.filter(user=user).count() == 0


@pytest.mark.django_db
def test_borradores_estan_aislados_por_usuario(client, user):
    other_user = get_user_model().objects.create_user(email='draft.other@example.edu', password='StrongPass123')
    save_draft(user, 'testplan', {'name': 'Mio'}, 3, 0)
    client.force_login(other_user)

    response = client.get(reverse('drafts:get'), {'module': 'testplan', 'project_id': 3, 'object_id': 0})

    assert response.json()['found'] is False


@pytest.mark.django_db
def test_guardar_dos_veces_actualiza_en_vez_de_duplicar(client, user):
    client.force_login(user)
    _post_json(client, reverse('drafts:save'), {'module': 'testplan', 'project_id': 3, 'object_id': 0, 'data': {'name': 'v1'}})
    _post_json(client, reverse('drafts:save'), {'module': 'testplan', 'project_id': 3, 'object_id': 0, 'data': {'name': 'v2'}})

    assert FormDraft.objects.filter(user=user).count() == 1
    assert FormDraft.objects.get(user=user).data == {'name': 'v2'}


@pytest.mark.django_db
def test_borrador_requiere_sesion(client):
    response = client.get(reverse('drafts:get'), {'module': 'testplan', 'project_id': 1, 'object_id': 0})

    assert response.status_code == 302
    assert 'login' in response.url


@pytest.mark.django_db
def test_creacion_de_plan_limpia_el_borrador(client, project, requirement, user):
    save_draft(user, 'testplan', {'name': 'Plan borrador'}, project.id, 0)
    client.force_login(user)

    response = client.post(
        reverse('testplans:create'),
        {
            'project': project.id,
            'name': 'Plan versionado',
            'version': '1.0',
            'description': 'Plan con historial.',
            'scope': 'Proyecto completo',
            'objective': 'Guardar historial inicial.',
            'strategy': 'Pruebas funcionales.',
            'entry_criteria': 'Requisitos aprobados',
            'exit_criteria': 'Casos ejecutados',
            'resources': 'Equipo QA',
            'environment': 'Local',
            'responsibilities': 'Estudiante',
            'estimation': '8 horas',
            'status': PlanModel.Status.DRAFT,
        },
    )

    assert response.status_code == 302
    assert not FormDraft.objects.filter(user=user, key=draft_key('testplan', project.id, 0)).exists()


@pytest.mark.django_db
def test_creacion_de_caso_desde_modal_limpia_el_borrador(client, project, requirement, test_plan, user):
    save_draft(user, 'testcase', {'title': 'Caso borrador'}, 0, 0)
    save_draft(user, 'testcase', {'title': 'Caso borrador'}, project.id, 0)
    client.force_login(user)

    response = client.post(
        reverse('testcases:index'),
        {
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'title': 'Caso desde modal',
            'description': 'Validar limpieza de borrador.',
            'priority': CaseModel.Priority.HIGH,
            'technique': CaseModel.Technique.EQUIVALENCE,
            'level': CaseModel.Level.SYSTEM,
            'preconditions': 'Usuario registrado',
            'steps': 'Abrir login => Se muestra el formulario\nEnviar credenciales => Accede al sistema',
            'expected_result': 'El usuario entra al dashboard.',
            'status': CaseModel.Status.PENDING,
        },
    )

    assert response.status_code == 302
    assert not FormDraft.objects.filter(user=user).exists()

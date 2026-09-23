import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.incidents.forms import IncidentForm
from apps.incidents.models import Incident
from apps.projects.models import Project


@pytest.mark.django_db
def test_formulario_de_riesgo_solo_muestra_proyectos_visibles(project, requirement, test_plan, test_case, user):
    other_user = get_user_model().objects.create_user(
        email='other.risk@example.edu', password='StrongPass123',
    )
    other_project = Project.objects.create(
        code='PRJ-RISK-OTHER', name='Proyecto ajeno', created_by=other_user,
    )

    form = IncidentForm(user=user)

    assert list(form.fields['project'].queryset) == [project]
    assert other_project not in form.fields['project'].queryset
    assert list(form.fields['requirement'].queryset) == [requirement]
    assert list(form.fields['test_plan'].queryset) == [test_plan]
    assert 'test_case' not in form.fields


@pytest.mark.django_db
def test_formulario_de_riesgo_solo_muestra_responsables_del_proyecto(project, user):
    member = get_user_model().objects.create_user(
        email='risk-owner@example.edu', password='StrongPass123',
    )
    project.members.add(member)
    foreign_user = get_user_model().objects.create_user(
        email='foreign-risk-owner@example.edu', password='StrongPass123',
    )
    form = IncidentForm(user=user)

    assert member in form.fields['owner'].queryset
    assert user in form.fields['owner'].queryset
    assert foreign_user not in form.fields['owner'].queryset


@pytest.mark.django_db
def test_incidencia_se_crea_abierta_con_probabilidad_e_impacto_medios(project, user):
    incident = Incident.objects.create(
        project=project,
        code='INC-001',
        title='API externa inestable',
        description='Existe riesgo de indisponibilidad del proveedor.',
        reported_by=user,
    )

    assert incident.status == Incident.Status.OPEN
    assert incident.probability == Incident.Probability.MEDIUM
    assert incident.impact == Incident.Impact.MEDIUM
    assert str(incident) == 'API externa inestable'


@pytest.mark.django_db
def test_riesgo_conserva_responsable_contingencia_y_fecha_de_revision(project, user):
    incident = Incident.objects.create(
        project=project,
        code='INC-FOLLOW-UP',
        title='Dependencia externa',
        description='El proveedor puede no estar disponible.',
        contingency_plan='Usar el stub local y registrar el bloqueo.',
        owner=user,
        review_date='2026-10-15',
        reported_by=user,
    )

    incident.refresh_from_db()
    assert incident.owner == user
    assert incident.contingency_plan.startswith('Usar el stub')
    assert str(incident.review_date) == '2026-10-15'


@pytest.mark.django_db
def test_formulario_de_riesgo_exige_plan_asociado(project):
    form = IncidentForm(
        data={
            'project': project.id,
            'code': 'INC-002',
            'title': 'Ambiente de pruebas lento',
            'description': 'La lentitud puede afectar la ejecucion.',
            'probability': Incident.Probability.HIGH,
            'impact': Incident.Impact.MEDIUM,
            'status': Incident.Status.ANALYSIS,
        }
    )

    assert not form.is_valid()
    assert 'test_plan' in form.errors


@pytest.mark.django_db
def test_formulario_de_riesgo_permite_vincular_requisito_y_plan(project, requirement, test_plan):
    form = IncidentForm(
        data={
            'project': project.id,
            'requirement': requirement.id,
            'test_plan': test_plan.id,
            'code': 'INC-003',
            'title': 'Riesgo sobre flujo critico',
            'description': 'El flujo de autenticacion podria fallar en navegadores antiguos.',
            'mitigation_strategy': 'Priorizar casos de compatibilidad y evidencia de ejecucion.',
            'probability': Incident.Probability.MEDIUM,
            'impact': Incident.Impact.HIGH,
            'status': Incident.Status.ANALYSIS,
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_vista_guarda_riesgo_aunque_ya_exista_otro_codigo(client, project, requirement, test_plan, user):
    Incident.objects.create(
        project=project,
        test_plan=test_plan,
        code='INC-000',
        title='Riesgo existente',
        description='Registro previo del proyecto.',
        reported_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse('incidents:create'),
        {
            'project': project.id,
            'requirement': requirement.id,
            'test_plan': test_plan.id,
            'title': 'Nuevo riesgo del plan',
            'description': 'Existe una amenaza de indisponibilidad del ambiente.',
            'mitigation_strategy': 'Preparar un ambiente alternativo.',
            'probability': Incident.Probability.MEDIUM,
            'impact': Incident.Impact.HIGH,
            'status': Incident.Status.OPEN,
        },
    )

    risk = Incident.objects.get(title='Nuevo riesgo del plan')

    assert response.status_code == 302
    assert risk.code == 'INC-001'
    assert risk.test_plan == test_plan
    assert risk.requirement == requirement
    assert risk.reported_by == user


@pytest.mark.django_db
def test_usuario_no_puede_modificar_ni_eliminar_riesgo_de_proyecto_ajeno(client, user):
    other_user = get_user_model().objects.create_user(email='foreign-incident@example.edu', password='StrongPass123')
    project = Project.objects.create(code='PRJ-FOREIGN-INC', name='Proyecto ajeno', created_by=other_user)
    incident = Incident.objects.create(project=project, code='INC-999', title='Riesgo privado', description='Privado.', reported_by=other_user)
    client.force_login(user)
    response = client.get(reverse('incidents:edit', args=[incident.pk]))
    assert response.status_code == 404
    response = client.post(reverse('incidents:delete', args=[incident.pk]))
    assert response.status_code == 404
    assert Incident.objects.filter(pk=incident.pk).exists()

@pytest.mark.django_db
def test_formulario_no_permite_cambiar_estado_arbitrariamente(client, user, project, test_plan):
    incident = Incident.objects.create(project=project, test_plan=test_plan, code='INC-LIFE-101', title='Riesgo', description='Descripción', reported_by=user)
    client.force_login(user)
    response = client.post(reverse('incidents:edit', args=[incident.pk]), {
        'project': project.pk, 'test_plan': test_plan.pk, 'code': incident.code,
        'title': incident.title, 'description': incident.description,
        'mitigation_strategy': '', 'probability': Incident.Probability.MEDIUM,
        'impact': Incident.Impact.MEDIUM, 'status': Incident.Status.CLOSED,
    })
    assert response.status_code == 302
    incident.refresh_from_db()
    assert incident.status == Incident.Status.OPEN


@pytest.mark.django_db
def test_transicion_invalida_de_riesgo_es_bloqueada(client, user, project, test_plan):
    incident = Incident.objects.create(project=project, test_plan=test_plan, code='INC-LIFE-102', title='Riesgo', description='Descripción', reported_by=user)
    client.force_login(user)
    response = client.post(reverse('incidents:transition', args=[incident.pk, Incident.Status.CLOSED]))
    assert response.status_code == 302
    incident.refresh_from_db()
    assert incident.status == Incident.Status.OPEN


@pytest.mark.django_db
def test_riesgo_sigue_transiciones_validas(client, user, project, test_plan):
    incident = Incident.objects.create(project=project, test_plan=test_plan, code='INC-LIFE-103', title='Riesgo', description='Descripción', mitigation_strategy='Plan de contingencia.', reported_by=user)
    client.force_login(user)
    for status in (Incident.Status.ANALYSIS, Incident.Status.MITIGATED, Incident.Status.CLOSED):
        response = client.post(reverse('incidents:transition', args=[incident.pk, status]))
        assert response.status_code == 302
        incident.refresh_from_db()
        assert incident.status == status

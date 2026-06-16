import pytest
from django.urls import reverse

from apps.incidents.forms import IncidentForm
from apps.incidents.models import Incident


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

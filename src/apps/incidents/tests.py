import pytest

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
def test_formulario_de_incidencia_es_valido_con_datos_minimos(project):
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

    assert form.is_valid()

import pytest

from apps.requirements.forms import RequirementForm
from apps.requirements.models import Requirement


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

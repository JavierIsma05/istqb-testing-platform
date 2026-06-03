import pytest

from apps.testcases.forms import TestCaseModalForm as CaseForm
from apps.testcases.models import TestCase as CaseModel


@pytest.mark.django_db
def test_caso_de_prueba_relaciona_plan_y_requisito(test_case, test_plan, requirement):
    assert test_case.test_plan == test_plan
    assert test_case.requirement == requirement
    assert test_case.status == CaseModel.Status.PENDING
    assert test_case.technique == CaseModel.Technique.BLACK_BOX
    assert str(test_case) == 'TC-001 - Login exitoso'


@pytest.mark.django_db
def test_formulario_de_caso_de_prueba_es_valido_con_pasos_y_resultado(test_plan, requirement):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'code': 'TC-002',
            'title': 'Registro exitoso',
            'description': 'Validar registro de usuario',
            'priority': CaseModel.Priority.HIGH,
            'technique': CaseModel.Technique.EQUIVALENCE,
            'level': CaseModel.Level.SYSTEM,
            'preconditions': 'Usuario sin cuenta previa',
            'steps': '1. Abrir registro\n2. Completar datos\n3. Enviar',
            'expected_result': 'La cuenta queda creada.',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert form.is_valid()

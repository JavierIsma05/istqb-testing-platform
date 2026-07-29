import pytest
from django.urls import reverse

from apps.incidents.models import Incident
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
            'steps': 'Abrir registro => Se muestra el formulario\nCompletar datos => Los datos son aceptados\nEnviar => La cuenta se crea',
            'expected_result': 'La cuenta queda creada.',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert form.is_valid()
    test_case = form.save(commit=False)
    assert len(test_case.steps_data) == 3


@pytest.mark.django_db
def test_formulario_de_caso_exige_requisito_y_pasos_estructurados(test_plan):
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': '',
            'title': 'Caso sin trazabilidad',
            'priority': CaseModel.Priority.MEDIUM,
            'technique': CaseModel.Technique.DECISION_TABLE,
            'level': CaseModel.Level.SYSTEM,
            'steps': 'Abrir formulario sin resultado esperado',
            'expected_result': 'No aplica.',
            'version': '1.0',
            'status': CaseModel.Status.PENDING,
        }
    )

    assert not form.is_valid()
    assert 'requirement' in form.errors
    assert 'steps' in form.errors


@pytest.mark.django_db
def test_modal_carga_plan_y_requisitos_disponibles(client, project, requirement, test_plan, user):
    project.members.add(user)
    client.force_login(user)

    response = client.get(reverse('testcases:index'))
    form = response.context['form']

    assert response.status_code == 200
    assert form.fields['test_plan'].initial == test_plan.pk
    assert list(form.fields['requirement'].queryset) == [requirement]
    assert test_plan.name in response.content.decode()
    assert requirement.code in response.content.decode()


@pytest.mark.django_db
def test_formulario_de_caso_vincula_riesgos_existentes(test_plan, requirement, user):
    risk = Incident.objects.create(
        project=test_plan.project,
        requirement=requirement,
        test_plan=test_plan,
        code='INC-010',
        title='Riesgo de autenticacion',
        description='El flujo de login podria fallar.',
        reported_by=user,
    )
    form = CaseForm(
        data={
            'test_plan': test_plan.id,
            'requirement': requirement.id,
            'code': 'TC-010',
            'title': 'Login con credenciales validas',
            'description': 'Validar acceso exitoso.',
            'priority': CaseModel.Priority.HIGH,
            'technique': CaseModel.Technique.EQUIVALENCE,
            'level': CaseModel.Level.SYSTEM,
            'preconditions': 'Usuario registrado',
            'steps': 'Abrir login => Se muestra el formulario\nEnviar credenciales => Accede al sistema',
            'expected_result': 'El usuario entra al dashboard.',
            'status': CaseModel.Status.PENDING,
            'risks': [risk.id],
        }
    )

    assert form.is_valid()
    test_case = form.save()
    assert list(test_case.covered_risks.all()) == [risk]

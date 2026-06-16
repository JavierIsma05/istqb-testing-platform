import pytest
from django.contrib.auth import get_user_model

from apps.executions.models import TestExecution as ExecutionModel
from apps.projects.models import Project
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase as CaseModel
from apps.testplans.models import TestPlan as PlanModel


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email='tester@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        email='admin@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def project(user):
    return Project.objects.create(
        code='PRJ-001',
        name='Plataforma ISTQB',
        description='Gestion del ciclo de vida de pruebas',
        created_by=user,
    )


@pytest.fixture
def requirement(project, user):
    return Requirement.objects.create(
        project=project,
        code='REQ-001',
        title='Autenticacion de usuarios',
        description='El sistema permite iniciar sesion con correo y clave.',
        created_by=user,
    )


@pytest.fixture
def test_plan(project, user):
    return PlanModel.objects.create(
        project=project,
        name='Plan funcional',
        objective='Validar los flujos principales del sistema.',
        created_by=user,
    )


@pytest.fixture
def test_case(test_plan, requirement, user):
    return CaseModel.objects.create(
        test_plan=test_plan,
        requirement=requirement,
        code='TC-001',
        title='Login exitoso',
        steps=(
            'Abrir login => Se muestra el formulario\n'
            'Ingresar credenciales validas => El sistema acepta los datos\n'
            'Enviar formulario => El usuario accede al dashboard'
        ),
        steps_data=[
            {'number': 1, 'action': 'Abrir login', 'expected_result': 'Se muestra el formulario'},
            {'number': 2, 'action': 'Ingresar credenciales validas', 'expected_result': 'El sistema acepta los datos'},
            {'number': 3, 'action': 'Enviar formulario', 'expected_result': 'El usuario accede al dashboard'},
        ],
        expected_result='El usuario accede al dashboard.',
        created_by=user,
    )


@pytest.fixture
def execution(test_case, user):
    return ExecutionModel.objects.create(
        test_case=test_case,
        executed_by=user,
        result=ExecutionModel.Result.PASSED,
        notes='Ejecucion completada correctamente.',
    )

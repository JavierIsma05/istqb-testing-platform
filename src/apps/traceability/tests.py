import pytest
from datetime import timedelta
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from apps.executions.models import TestExecution
from apps.testcases.models import TestCase
from apps.traceability.models import TraceabilityLink


@pytest.mark.django_db
def test_trazabilidad_conecta_requisito_con_caso_de_prueba(requirement, test_case):
    link = TraceabilityLink.objects.create(
        requirement=requirement,
        test_case=test_case,
        rationale='El caso cubre el flujo principal del requisito.',
    )

    assert link.requirement == requirement
    assert link.test_case == test_case
    assert str(link) == 'REQ-001 -> TC-001'


@pytest.mark.django_db
def test_trazabilidad_no_permite_duplicar_requisito_y_caso(requirement, test_case):
    TraceabilityLink.objects.create(requirement=requirement, test_case=test_case)

    with pytest.raises(IntegrityError):
        TraceabilityLink.objects.create(requirement=requirement, test_case=test_case)


@pytest.mark.django_db
def test_matriz_muestra_una_fila_por_caso_de_prueba(client, user, requirement, test_plan, test_case):
    second_case = TestCase.objects.create(
        test_plan=test_plan,
        requirement=requirement,
        code='TC-002',
        title='Login fallido',
        steps='Enviar credenciales invalidas => Se muestra error',
        steps_data=[{'number': 1, 'action': 'Enviar credenciales invalidas', 'expected_result': 'Se muestra error'}],
        expected_result='Se muestra error.',
        created_by=user,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    assert len(response.context['rows']) == 2
    assert {row['case'].code for row in response.context['rows']} == {'TC-001', 'TC-002'}


@pytest.mark.django_db
def test_matriz_no_duplica_filas_ni_pierde_historial(client, user, requirement, test_plan, test_case):
    for index in range(40):
        TestExecution.objects.create(
            test_case=test_case,
            executed_by=user,
            result=TestExecution.Result.PASSED,
        )

    client.force_login(user)
    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    assert len(response.context['rows']) == 1
    assert TestExecution.objects.filter(test_case=test_case).count() == 40


@pytest.mark.django_db
def test_matriz_usa_la_ultima_ejecucion_completada(client, user, requirement, test_plan, test_case):
    base = timezone.now()
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.PASSED,
        executed_at=base - timedelta(days=2),
    )
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.FAILED,
        executed_at=base - timedelta(days=1),
    )
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.ERROR,
        executed_at=base,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    row = response.context['rows'][0]
    assert row['execution'].result == TestExecution.Result.ERROR


@pytest.mark.django_db
def test_matriz_ignora_ejecuciones_en_curso_y_no_ejecutadas(client, user, requirement, test_plan, test_case):
    base = timezone.now()
    completed = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.PASSED,
        executed_at=base - timedelta(hours=3),
    )
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.RUNNING,
        executed_at=base - timedelta(hours=2),
    )
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.NOT_RUN,
        executed_at=base - timedelta(hours=1),
    )
    client.force_login(user)

    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    row = response.context['rows'][0]
    assert row['execution'].pk == completed.pk
    assert row['execution'].result == TestExecution.Result.PASSED


@pytest.mark.django_db
def test_matriz_actualiza_cuando_llega_una_ejecucion_completada_nueva(client, user, requirement, test_plan, test_case):
    base = timezone.now()
    older = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.PASSED,
        executed_at=base - timedelta(days=1),
    )
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    assert response.context['rows'][0]['execution'].pk == older.pk

    newer = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.FAILED,
        executed_at=base,
    )
    response = client.get(reverse('traceability:index'))
    assert response.context['rows'][0]['execution'].pk == newer.pk


@pytest.mark.django_db
def test_matriz_muestra_requisito_sin_caso_con_relaciones_incompletas(client, user, project, requirement, test_plan, test_case):
    lonely = requirement.__class__.objects.create(
        project=project,
        code='REQ-002',
        title='Requisito sin caso de prueba',
        description='Aun no tiene casos asociados.',
        created_by=user,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    lonely_row = next(
        row for row in response.context['rows'] if row['requirement'].pk == lonely.pk
    )
    assert lonely_row['case'] is None
    assert lonely_row['plan'] is None
    assert lonely_row['execution'] is None

    assert response.context['total_requirements'] == 2
    assert response.context['total_test_cases'] == 1
    assert response.context['total_plans'] == 1
    assert response.context['total_executions'] == 0
    assert response.context['total_results'] == 0
    assert response.context['total_defects'] == 0


@pytest.mark.django_db
def test_metric_cards_cuentan_elementos_de_la_matriz(client, user, requirement, test_plan, test_case):
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.FAILED,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    assert response.context['total_requirements'] == 1
    assert response.context['total_plans'] == 1
    assert response.context['total_test_cases'] == 1
    assert response.context['total_executions'] == 1
    assert response.context['total_results'] == 1
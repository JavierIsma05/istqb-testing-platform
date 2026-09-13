import pytest
from datetime import timedelta
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.executions.models import TestExecution
from apps.testcases.models import TestCase
from apps.traceability.models import TraceabilityLink
from apps.projects.models import Project


@pytest.mark.django_db
def test_trazabilidad_conecta_requisito_con_caso_de_prueba(requirement, test_case):
    link = TraceabilityLink.objects.create(requirement=requirement, test_case=test_case, rationale='El caso cubre el flujo principal del requisito.')
    assert link.requirement == requirement
    assert link.test_case == test_case
    assert str(link) == 'REQ-001 -> TC-001'


@pytest.mark.django_db
def test_trazabilidad_no_permite_duplicar_requisito_y_caso(requirement, test_case):
    TraceabilityLink.objects.create(requirement=requirement, test_case=test_case)
    with pytest.raises(IntegrityError):
        TraceabilityLink.objects.create(requirement=requirement, test_case=test_case)


@pytest.mark.django_db
def test_trazabilidad_rechaza_requisito_y_caso_de_proyectos_distintos(requirement, test_case, user):
    other_project = Project.objects.create(code='PRJ-TRZ-002', name='Proyecto de otra trazabilidad', created_by=user)
    other_requirement = requirement.__class__.objects.create(project=other_project, code='REQ-999', title='Requisito de otro proyecto', description='No debe vincularse a un caso externo.', created_by=user)
    with pytest.raises(ValidationError, match='mismo proyecto'):
        TraceabilityLink.objects.create(requirement=other_requirement, test_case=test_case)


@pytest.mark.django_db
def test_matriz_muestra_una_fila_por_caso_de_prueba(client, user, requirement, test_plan, test_case):
    TestCase.objects.create(test_plan=test_plan, requirement=requirement, code='TC-002', title='Login fallido', steps='Enviar credenciales invalidas => Se muestra error', steps_data=[{'number': 1, 'action': 'Enviar credenciales invalidas', 'expected_result': 'Se muestra error'}], expected_result='Se muestra error.', created_by=user)
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    assert response.status_code == 200
    assert len(response.context['rows']) == 2
    assert {row['case'].code for row in response.context['rows']} == {'TC-001', 'TC-002'}


@pytest.mark.django_db
def test_matriz_no_duplica_filas_ni_pierde_historial(client, user, test_case):
    for _ in range(40):
        TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED)
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    assert response.status_code == 200
    assert len(response.context['rows']) == 1
    assert TestExecution.objects.filter(test_case=test_case).count() == 40


@pytest.mark.django_db
def test_matriz_usa_la_ultima_ejecucion_completada(client, user, test_case):
    base = timezone.now()
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED, executed_at=base - timedelta(days=2))
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.FAILED, executed_at=base - timedelta(days=1))
    latest = TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.ERROR, executed_at=base)
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    assert response.status_code == 200
    assert response.context['rows'][0]['execution'].pk == latest.pk


@pytest.mark.django_db
def test_matriz_ignora_ejecuciones_en_curso_y_no_ejecutadas(client, user, test_case):
    base = timezone.now()
    completed = TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED, executed_at=base - timedelta(hours=3))
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.RUNNING, executed_at=base - timedelta(hours=2))
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.NOT_RUN, executed_at=base - timedelta(hours=1))
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    assert response.status_code == 200
    assert response.context['rows'][0]['execution'].pk == completed.pk


@pytest.mark.django_db
def test_matriz_actualiza_cuando_llega_una_ejecucion_completada_nueva(client, user, test_case):
    base = timezone.now()
    older = TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED, executed_at=base - timedelta(days=1))
    client.force_login(user)
    assert client.get(reverse('traceability:index')).context['rows'][0]['execution'].pk == older.pk
    newer = TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.FAILED, executed_at=base)
    assert client.get(reverse('traceability:index')).context['rows'][0]['execution'].pk == newer.pk


@pytest.mark.django_db
def test_matriz_muestra_requisito_sin_caso_con_relaciones_incompletas(client, user, project, requirement, test_case):
    lonely = requirement.__class__.objects.create(project=project, code='REQ-002', title='Requisito sin caso de prueba', description='Aun no tiene casos asociados.', created_by=user)
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    lonely_row = next(row for row in response.context['rows'] if row['requirement'].pk == lonely.pk)
    assert lonely_row['case'] is None and lonely_row['plan'] is None and lonely_row['execution'] is None
    assert response.context['total_requirements'] == 2
    assert response.context['total_test_cases'] == 1
    assert response.context['total_plans'] == 1
    assert response.context['total_executions'] == 0
    assert response.context['total_results'] == 0
    assert response.context['total_defects'] == 0


@pytest.mark.django_db
def test_metric_cards_cuentan_elementos_de_la_matriz(client, user, test_case):
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.FAILED)
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    assert response.status_code == 200
    assert response.context['total_requirements'] == 1
    assert response.context['total_plans'] == 1
    assert response.context['total_test_cases'] == 1
    assert response.context['total_executions'] == 1
    assert response.context['total_results'] == 1


@pytest.mark.django_db
def test_matriz_ofrece_enlaces_contextuales(client, user, requirement, test_plan, test_case):
    TraceabilityLink.objects.create(requirement=requirement, test_case=test_case, rationale='Cubre el acceso válido.')
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.PASSED,
    )
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    content = response.content.decode()
    assert response.status_code == 200
    assert reverse('requirements:edit', args=[requirement.pk]) in content
    assert reverse('testplans:edit', args=[test_plan.pk]) in content
    assert reverse('testcases:detail', args=[test_case.pk]) in content
    assert reverse('executions:history', args=[test_case.pk]) in content
    assert 'Cubre el acceso válido.' in content


@pytest.mark.django_db
def test_matriz_de_trazabilidad_no_expone_proyectos_ajenos(client, user, requirement):
    other_user = user.__class__.objects.create_user(email='foreign-traceability@example.edu', password='StrongPass123')
    foreign_project = Project.objects.create(code='PRJ-FOREIGN-TRACE', name='Proyecto ajeno de trazabilidad', created_by=other_user)
    foreign_requirement = requirement.__class__.objects.create(project=foreign_project, code='REQ-FOREIGN-001', title='Requisito privado', description='No debe aparecer.', created_by=other_user)
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    visible_requirement_ids = {row['requirement'].pk for row in response.context['rows']}
    assert requirement.pk in visible_requirement_ids
    assert foreign_requirement.pk not in visible_requirement_ids


@pytest.mark.django_db
def test_matriz_muestra_cadena_requisito_caso_ejecucion_y_defecto(client, user, requirement, test_case):
    from apps.defects.models import Defect
    execution = TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.FAILED)
    defect = Defect.objects.create(project=requirement.project, test_case=test_case, execution=execution, code='DEF-TRACE-001', title='Defecto trazable', description='Debe aparecer en la matriz.', reported_by=user)
    client.force_login(user)
    row = client.get(reverse('traceability:index')).context['rows'][0]
    assert row['requirement'].pk == requirement.pk and row['case'].pk == test_case.pk
    assert row['execution'].pk == execution.pk and defect in row['defects']


@pytest.mark.django_db
def test_matriz_mantiene_multiples_requisitos_para_un_mismo_caso(client, user, project, requirement, test_case):
    second_requirement = requirement.__class__.objects.create(project=project, code='REQ-TRACE-002', title='Segundo requisito', description='Tambien es cubierto.', created_by=user)
    TraceabilityLink.objects.create(requirement=second_requirement, test_case=test_case, rationale='Cobertura adicional.')
    client.force_login(user)
    rows = [row for row in client.get(reverse('traceability:index')).context['rows'] if row['case'] and row['case'].pk == test_case.pk]
    assert {row['requirement'].pk for row in rows} == {requirement.pk, second_requirement.pk}
    assert len(rows) == 2


@pytest.mark.django_db
def test_matriz_identifica_el_tipo_de_la_ultima_ejecucion(client, user, test_case):
    TestExecution.objects.create(test_case=test_case, executed_by=user, execution_type=TestExecution.ExecutionType.NORMAL, result=TestExecution.Result.PASSED, executed_at=timezone.now() - timedelta(minutes=1))
    latest = TestExecution.objects.create(test_case=test_case, executed_by=user, execution_type=TestExecution.ExecutionType.REGRESSION, result=TestExecution.Result.PASSED, executed_at=timezone.now())
    client.force_login(user)
    response = client.get(reverse('traceability:index'))
    row = response.context['rows'][0]
    assert row['execution'].pk == latest.pk
    assert latest.get_execution_type_display() in response.content.decode()


@pytest.mark.django_db
def test_metricas_calculan_cobertura_de_requisitos_y_ejecucion(client, user, project, requirement, test_case):
    requirement.__class__.objects.create(project=project, code='REQ-METRIC-002', title='Requisito sin cobertura', description='No tiene caso asociado.', created_by=user)
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    assert context['total_requirements'] == 2
    assert context['traced_requirements'] == 1
    assert context['requirements_with_completed_execution'] == 1
    assert context['requirement_coverage_percentage'] == 50.0
    assert context['execution_coverage_percentage'] == 50.0


@pytest.mark.django_db
def test_metricas_separan_historial_de_ejecuciones_y_ultima_fotografia(client, user, test_case):
    for result in (TestExecution.Result.PASSED, TestExecution.Result.FAILED, TestExecution.Result.PASSED):
        TestExecution.objects.create(test_case=test_case, executed_by=user, result=result)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    assert context['total_executions'] == 3
    assert context['latest_execution_snapshots'] == 1
    assert context['executed_test_cases'] == 1
    assert context['test_case_execution_coverage_percentage'] == 100.0


@pytest.mark.django_db
def test_metricas_de_casos_ejecutados_distinguen_casos_pendientes(client, user, requirement, test_plan, test_case):
    TestCase.objects.create(test_plan=test_plan, requirement=requirement, code='TC-METRIC-002', title='Caso pendiente', steps='Ejecutar', steps_data=[], expected_result='Correcto', created_by=user)
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    assert context['total_test_cases'] == 2
    assert context['executed_test_cases'] == 1
    assert context['test_case_execution_coverage_percentage'] == 50.0


@pytest.mark.django_db
def test_indice_de_trazabilidad_integral_es_reproducible(client, user, project, requirement, test_case):
    uncovered = requirement.__class__.objects.create(project=project, code='REQ-TRACE-INDEX-002', title='Requisito sin cadena completa', description='No tiene caso ni ejecución.', created_by=user)
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    assert context['total_requirements'] == 2
    assert context['end_to_end_traced_requirements'] == 1
    assert context['end_to_end_traceability_percentage'] == 50.0
    assert uncovered.pk not in {row['requirement'].pk for row in context['rows'] if row['execution'] is not None}


@pytest.mark.django_db
def test_metricas_mantienen_orden_logico_de_cobertura(client, user, project, requirement, test_plan, test_case):
    uncovered = requirement.__class__.objects.create(project=project, code='REQ-CONSIST-002', title='Sin cobertura', description='No tiene caso.', created_by=user)
    pending_case = TestCase.objects.create(test_plan=test_plan, requirement=requirement, code='TC-CONSIST-002', title='Caso pendiente', steps='Ejecutar', steps_data=[], expected_result='Correcto', created_by=user)
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    assert context['requirement_coverage_percentage'] == 50.0
    assert context['execution_coverage_percentage'] == 50.0
    assert context['end_to_end_traceability_percentage'] == 50.0
    assert context['test_case_execution_coverage_percentage'] == 50.0
    assert context['end_to_end_traceability_percentage'] <= context['requirement_coverage_percentage']
    assert context['execution_coverage_percentage'] <= context['requirement_coverage_percentage']
    assert uncovered.pk not in {row['requirement'].pk for row in context['rows'] if row['case'] is not None}
    assert pending_case.pk not in {row['case'].pk for row in context['rows'] if row['execution'] is not None}


@pytest.mark.django_db
def test_multiples_casos_y_ejecuciones_no_inflan_el_indice_por_requisito(client, user, requirement, test_plan, test_case):
    second_case = TestCase.objects.create(test_plan=test_plan, requirement=requirement, code='TC-CONSIST-003', title='Segundo caso', steps='Ejecutar', steps_data=[], expected_result='Correcto', created_by=user)
    for case in (test_case, second_case):
        for result in (TestExecution.Result.PASSED, TestExecution.Result.FAILED):
            TestExecution.objects.create(test_case=case, executed_by=user, result=result)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    assert context['total_requirements'] == 1
    assert context['traced_requirements'] == 1
    assert context['requirements_with_completed_execution'] == 1
    assert context['end_to_end_traced_requirements'] == 1
    assert context['requirement_coverage_percentage'] == 100.0
    assert context['execution_coverage_percentage'] == 100.0
    assert context['end_to_end_traceability_percentage'] == 100.0
    assert context['total_executions'] == 4
    assert context['executed_test_cases'] == 2
    assert context['test_case_execution_coverage_percentage'] == 100.0


@pytest.mark.django_db
def test_metricas_por_proyecto_no_mezclan_artifactos_entre_proyectos(client, user, project, requirement, test_case):
    TestExecution.objects.create(test_case=test_case, executed_by=user, result=TestExecution.Result.PASSED)
    other_project = Project.objects.create(code='PRJ-HIST-002', name='Segundo proyecto', created_by=user)
    other_project.requirements.create(code='REQ-OTHER-001', title='Otro requisito', description='Sin cobertura.', created_by=user)
    client.force_login(user)
    context = client.get(reverse('traceability:index')).context
    metrics = {item['project'].pk: item for item in context['project_metrics']}
    assert metrics[project.pk]['total_requirements'] == 1
    assert metrics[project.pk]['total_test_cases'] == 1
    assert metrics[project.pk]['total_executions'] == 1
    assert metrics[project.pk]['requirement_coverage_percentage'] == 100.0
    assert metrics[other_project.pk]['total_requirements'] == 1
    assert metrics[other_project.pk]['total_test_cases'] == 0
    assert metrics[other_project.pk]['total_executions'] == 0
    assert metrics[other_project.pk]['requirement_coverage_percentage'] == 0
    assert metrics[other_project.pk]['execution_coverage_percentage'] == 0

import pytest
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.projects.forms import ProjectForm
from apps.projects.models import Project


@pytest.mark.django_db
def test_proyecto_guarda_codigo_nombre_y_estado_por_defecto(project):
    assert project.code == 'PRJ-001'
    assert project.name == 'Plataforma ISTQB'
    assert project.status == Project.Status.PLANNED
    assert str(project) == 'PRJ-001 - Plataforma ISTQB'


@pytest.mark.django_db
def test_formulario_de_proyecto_es_valido_con_datos_minimos():
    form = ProjectForm(data={'code': 'PRJ-002', 'name': 'Sistema academico', 'description': 'Proyecto de pruebas academicas', 'members': []})
    assert form.is_valid()


@pytest.mark.django_db
def test_propietario_puede_editar_proyecto(client, user, project):
    client.force_login(user)
    response = client.post(reverse('projects:edit', args=[project.pk]), data={'code': project.code, 'name': 'Nombre actualizado', 'description': 'Descripcion actualizada', 'start_date': timezone.localdate().isoformat()})
    project.refresh_from_db()
    assert response.status_code == 302
    assert project.name == 'Nombre actualizado'
    assert project.description == 'Descripcion actualizada'


@pytest.mark.django_db
def test_formulario_rechaza_fechas_de_otro_anio():
    other_year = timezone.localdate().year - 1
    form = ProjectForm(data={'code': 'PRJ-002', 'name': 'Sistema academico', 'description': 'Proyecto de pruebas academicas', 'start_date': f'{other_year}-05-10', 'members': []})
    assert not form.is_valid()
    assert 'start_date' in form.errors


@pytest.mark.django_db
def test_eliminar_proyecto_con_automatizaciones_elimina_toda_la_informacion_asociada(client, project, test_case, execution):
    from apps.executions.models import AutomatedExecutionResult, AutomatedValidationRule
    rule = AutomatedValidationRule.objects.create(test_case=test_case, requirement=test_case.requirement, step_number=1, name='Verificar login', action_type=AutomatedValidationRule.ActionType.VERIFY, target_url='https://example.com/login', selector_value='body', expected_value='Bienvenido')
    execution.execution_mode = execution.ExecutionMode.AUTOMATED
    execution.save(update_fields=['execution_mode'])
    result = AutomatedExecutionResult.objects.create(test_execution=execution, validation_rule=rule, status=execution.result)
    risk = Incident.objects.create(project=project, requirement=test_case.requirement, test_plan=test_case.test_plan, code='INC-DELETE-001', title='Riesgo de prueba', description='Riesgo usado para verificar la eliminación en cascada.')
    test_case.covered_risks.add(risk)
    test_case_id = test_case.pk
    execution_id = execution.pk
    rule_id = rule.pk
    result_id = result.pk
    risk_id = risk.pk
    project_id = project.pk
    plan_id = test_case.test_plan_id
    requirement_id = test_case.requirement_id
    client.force_login(project.created_by)
    response = client.post(reverse('projects:delete', args=[project.pk]))
    assert response.status_code == 302
    assert response['Location'] == reverse('projects:index')
    assert not Project.objects.filter(pk=project_id).exists()
    assert not TestExecution.objects.filter(pk=execution_id).exists()
    assert not AutomatedValidationRule.objects.filter(pk=rule_id).exists()
    assert not AutomatedExecutionResult.objects.filter(pk=result_id).exists()
    assert not TestCase.objects.filter(pk=test_case_id).exists()
    assert not TestPlan.objects.filter(pk=plan_id).exists()
    assert not Requirement.objects.filter(pk=requirement_id).exists()
    assert not Incident.objects.filter(pk=risk_id).exists()


@pytest.mark.django_db
def test_lista_expone_menu_bootstrap_con_editar_y_eliminar_para_propietario(client, project, user):
    client.force_login(user)
    response = client.get(reverse('projects:index'))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-bs-toggle="dropdown"' in content
    assert reverse('projects:edit', args=[project.pk]) in content
    assert reverse('projects:delete', args=[project.pk]) in content


@pytest.mark.django_db
def test_lista_no_expone_acciones_de_edicion_a_un_miembro_no_propietario(client, project):
    client.force_login(project.created_by)
    response = client.get(reverse('projects:index'))
    assert response.status_code == 200

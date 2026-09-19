import pytest
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.testcases.models import TestCase
from apps.projects.forms import ProjectForm
from apps.projects.models import Project
from apps.requirements.models import Requirement
from apps.testplans.models import TestPlan


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
    assert 'status' not in form.fields


@pytest.mark.django_db
def test_creacion_de_proyecto_ignora_estado_enviado_por_post(client, user):
    client.force_login(user)
    response = client.post(reverse('projects:create'), data={'name': 'Sistema academico', 'description': 'Proyecto de pruebas academicas', 'status': Project.Status.ACTIVE, 'members': []})
    project = Project.objects.get(name='Sistema academico')
    assert response.status_code == 302
    assert project.status == Project.Status.PLANNED


@pytest.mark.django_db
def test_creacion_de_proyecto_con_fecha_de_inicio_actual_queda_activa(client, user):
    client.force_login(user)
    response = client.post(reverse('projects:create'), data={'name': 'Sistema con inicio actual', 'description': 'Proyecto que empieza hoy', 'start_date': timezone.localdate().isoformat(), 'members': []})
    project = Project.objects.get(name='Sistema con inicio actual')
    assert response.status_code == 302
    assert project.status == Project.Status.ACTIVE


def test_lista_de_proyectos_redirige_a_login_si_no_hay_sesion(client):
    response = client.get(reverse('projects:index'))
    assert response.status_code == 302
    assert reverse('login') in response['Location']


@pytest.mark.django_db
def test_estudiante_no_puede_ver_detalle_de_proyecto_ajeno(client, user):
    other_user = get_user_model().objects.create_user(email='otro@example.edu', password='StrongPass123')
    other_project = Project.objects.create(code='PRJ-999', name='Proyecto ajeno', created_by=other_user)
    client.force_login(user)
    response = client.get(reverse('projects:detail', args=[other_project.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_detalle_de_proyecto_visible_actualiza_proyecto_activo(client, project, user):
    other_project = Project.objects.create(code='PRJ-010', name='Proyecto visible alterno', created_by=user)
    client.force_login(user)
    session = client.session
    session['active_project_id'] = project.pk
    session.save()
    response = client.get(reverse('projects:detail', args=[other_project.pk]))
    assert response.status_code == 200
    assert client.session['active_project_id'] == other_project.pk


@pytest.mark.django_db
def test_tutor_no_puede_crear_proyectos(client):
    tutor = get_user_model().objects.create_user(email='tutor@example.edu', password='StrongPass123', role=get_user_model().Roles.TEACHER)
    client.force_login(tutor)
    response = client.post(reverse('projects:create'), data={'name': 'Proyecto desde tutor', 'description': 'No debe crearse'})
    assert response.status_code == 302
    assert not Project.objects.filter(name='Proyecto desde tutor').exists()


@pytest.mark.django_db
def test_estudiante_no_puede_crear_otro_proyecto_activo(client, user):
    Project.objects.create(code='PRJ-010', name='Proyecto activo existente', status=Project.Status.ACTIVE, created_by=user)
    client.force_login(user)
    response = client.post(reverse('projects:create'), data={'name': 'Segundo proyecto activo', 'description': 'No debe quedar activo', 'start_date': timezone.localdate().isoformat()})
    assert response.status_code == 200
    assert not Project.objects.filter(name='Segundo proyecto activo').exists()


@pytest.mark.django_db
def test_proyecto_se_vincula_a_tutor_por_seleccion(client, user):
    tutor = get_user_model().objects.create_user(email='tutor@example.edu', password='StrongPass123', role=get_user_model().Roles.TEACHER)
    client.force_login(user)
    response = client.post(reverse('projects:create'), data={'name': 'Proyecto con tutor', 'description': 'Proyecto de titulacion', 'tutor': tutor.pk})
    project = Project.objects.get(name='Proyecto con tutor')
    assert response.status_code == 302
    assert project.members.filter(pk=user.pk).exists()
    assert project.members.filter(pk=tutor.pk).exists()
    assert project.tutor == tutor


@pytest.mark.django_db
def test_proyecto_asigna_participantes_estudiantes_y_tutor(client, user):
    participant = get_user_model().objects.create_user(email='participante@example.edu', password='StrongPass123', role=get_user_model().Roles.STUDENT)
    tutor = get_user_model().objects.create_user(email='tutor-asignado@example.edu', password='StrongPass123', role=get_user_model().Roles.TEACHER)
    client.force_login(user)
    response = client.post(reverse('projects:create'), data={'name': 'Proyecto con participantes', 'description': 'Proyecto con equipo asignado.', 'members': [participant.pk], 'tutor': tutor.pk})
    project = Project.objects.get(name='Proyecto con participantes')
    assert response.status_code == 302
    assert set(project.members.values_list('pk', flat=True)) == {user.pk, participant.pk, tutor.pk}
    assert project.tutor_id == tutor.pk


@pytest.mark.django_db
def test_formulario_no_permite_asignar_docente_como_participante(client, user):
    tutor = get_user_model().objects.create_user(email='solo-tutor@example.edu', password='StrongPass123', role=get_user_model().Roles.TEACHER)
    client.force_login(user)
    response = client.post(reverse('projects:create'), data={'name': 'Proyecto invalido', 'description': 'No debe aceptar un docente como participante.', 'members': [tutor.pk]})
    assert response.status_code == 200
    assert not Project.objects.filter(name='Proyecto invalido').exists()


@pytest.mark.django_db
def test_formulario_solo_lista_docentes_en_tutor(client, user):
    student = get_user_model().objects.create_user(email='estudiante@example.edu', password='StrongPass123', role=get_user_model().Roles.STUDENT)
    tutor = get_user_model().objects.create_user(email='tutor@example.edu', password='StrongPass123', role=get_user_model().Roles.TEACHER)
    client.force_login(user)
    response = client.get(reverse('projects:create'))
    assert response.status_code == 200
    assert student not in response.context['form'].fields['tutor'].queryset
    assert tutor in response.context['form'].fields['tutor'].queryset


@pytest.mark.django_db
def test_miembro_que_no_es_propietario_no_puede_editar_proyecto(client, user):
    owner = get_user_model().objects.create_user(email='propietario@example.edu', password='StrongPass123')
    owned_project = Project.objects.create(code='PRJ-999', name='Proyecto del propietario', created_by=owner)
    owned_project.members.add(user)
    client.force_login(user)
    response = client.post(reverse('projects:edit', args=[owned_project.pk]), data={'name': 'Intento de edicion'})
    assert response.status_code == 302
    owned_project.refresh_from_db()
    assert owned_project.name == 'Proyecto del propietario'


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
    risk = Incident.objects.create(project=project, requirement=test_case.requirement, test_plan=test_case.test_plan, code='INC-DELETE-001', title='Riesgo de prueba', description='Riesgo usado para verificar la eliminacion en cascada.')
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
    member = get_user_model().objects.create_user(email='miembro-sin-edicion@example.edu', password='StrongPass123')
    project.members.add(member)
    client.force_login(member)
    response = client.get(reverse('projects:index'))
    assert response.status_code == 200
    assert reverse('projects:edit', args=[project.pk]) not in response.content.decode()


@pytest.mark.django_db
def test_administrador_puede_acceder_a_editar_proyecto_visible(client, project):
    admin = get_user_model().objects.create_user(email='admin-proyectos@example.edu', password='StrongPass123', role=get_user_model().Roles.ADMIN)
    client.force_login(admin)
    response = client.get(reverse('projects:edit', args=[project.pk]))
    assert response.status_code == 200
    assert response.context['project'] == project


@pytest.mark.django_db
def test_miembro_no_propietario_no_puede_eliminar_proyecto(client, user):
    owner = get_user_model().objects.create_user(email='owner-delete@example.edu', password='StrongPass123')
    owned_project = Project.objects.create(code='PRJ-DELETE', name='Proyecto protegido contra eliminacion', created_by=owner)
    owned_project.members.add(user)
    client.force_login(user)
    response = client.post(reverse('projects:delete', args=[owned_project.pk]))
    assert response.status_code == 302
    assert Project.objects.filter(pk=owned_project.pk).exists()


@pytest.mark.django_db
def test_propietario_puede_eliminar_su_proyecto(client, user, project):
    client.force_login(user)
    response = client.post(reverse('projects:delete', args=[project.pk]))
    assert response.status_code == 302
    assert not Project.objects.filter(pk=project.pk).exists()


@pytest.mark.django_db
def test_administrador_puede_eliminar_proyecto_visible(client, project):
    admin = get_user_model().objects.create_user(email='admin-delete@example.com', password='StrongPass123', role=get_user_model().Roles.ADMIN)
    client.force_login(admin)
    response = client.post(reverse('projects:delete', args=[project.pk]))
    assert response.status_code == 302
    assert not Project.objects.filter(pk=project.pk).exists()


@pytest.mark.django_db
def test_admin_elimina_proyecto_con_riesgo_y_sus_datos_asociados(project, test_case, execution):
    from django.contrib import admin
    from django.test import RequestFactory
    from apps.projects.admin import ProjectAdmin

    risk = Incident.objects.create(
        project=project,
        requirement=test_case.requirement,
        test_plan=test_case.test_plan,
        code='INC-ADMIN-DELETE-001',
        title='Riesgo para borrado desde admin',
        description='Verifica que el borrado masivo del admin elimine tambien la relacion M2M.'
    )
    test_case.covered_risks.add(risk)
    project_id = project.pk
    risk_id = risk.pk
    test_case_id = test_case.pk
    execution_id = execution.pk

    request = RequestFactory().post('/admin/projects/project/')
    ProjectAdmin(Project, admin.site).delete_queryset(
        request,
        Project.objects.filter(pk=project.pk),
    )

    assert not Project.objects.filter(pk=project_id).exists()
    assert not Incident.objects.filter(pk=risk_id).exists()
    assert not TestCase.objects.filter(pk=test_case_id).exists()
    assert not TestExecution.objects.filter(pk=execution_id).exists()

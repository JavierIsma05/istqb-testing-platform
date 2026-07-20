import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.projects.models import Project
from apps.testplans.forms import TestPlanWizardForm as PlanForm
from apps.testplans.models import TestPlan as PlanModel, TestPlanVersion as PlanVersionModel


@pytest.mark.django_db
def test_formulario_de_plan_solo_muestra_proyectos_visibles(project, user):
    other_user = get_user_model().objects.create_user(
        email='other.plan@example.edu', password='StrongPass123',
    )
    other_project = Project.objects.create(
        code='PRJ-PLAN-OTHER', name='Proyecto ajeno', created_by=other_user,
    )

    form = PlanForm(user=user)

    assert list(form.fields['project'].queryset) == [project]
    assert other_project not in form.fields['project'].queryset


@pytest.mark.django_db
def test_formulario_de_plan_acepta_documento_base_permitido(project, requirement):
    document = SimpleUploadedFile('requisitos.pdf', b'%PDF-1.4 contenido de prueba', content_type='application/pdf')
    form = PlanForm(
        data={
            'project': project.id,
            'name': 'Plan con documento',
            'version': '1.0',
            'objective': 'Validar el registro de documento base.',
            'status': PlanModel.Status.DRAFT,
        },
        files={'base_document': document},
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_formulario_de_plan_rechaza_documento_base_no_permitido(project, requirement):
    document = SimpleUploadedFile('script.exe', b'not-an-executable', content_type='application/octet-stream')
    form = PlanForm(
        data={
            'project': project.id,
            'name': 'Plan con archivo invalido',
            'version': '1.0',
            'objective': 'Validar el filtro de documentos.',
            'status': PlanModel.Status.DRAFT,
        },
        files={'base_document': document},
    )

    assert not form.is_valid()
    assert 'base_document' in form.errors


@pytest.mark.django_db
def test_plan_de_pruebas_se_crea_en_borrador_por_defecto(test_plan, project):
    assert test_plan.project == project
    assert test_plan.version == '1.0'
    assert test_plan.status == PlanModel.Status.DRAFT
    assert str(test_plan) == 'Plan funcional'


@pytest.mark.django_db
def test_formulario_de_plan_de_pruebas_es_valido_con_objetivo(project, requirement):
    form = PlanForm(
        data={
            'project': project.id,
            'name': 'Plan de regresion',
            'version': '1.0',
            'description': 'Validacion de regresion',
            'scope': 'Modulos principales',
            'objective': 'Detectar regresiones funcionales.',
            'strategy': 'Priorizar casos asociados a riesgos altos y requisitos criticos.',
            'entry_criteria': 'Ambiente disponible',
            'exit_criteria': 'Casos criticos ejecutados',
            'resources': 'Equipo QA',
            'environment': 'Chrome, Windows 11, ambiente local',
            'responsibilities': 'Estudiante ejecuta, docente revisa evidencias.',
            'estimation': '8 horas de diseno y ejecucion.',
            'status': PlanModel.Status.REVIEW,
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_creacion_de_plan_registra_version_inicial(client, project, requirement, user):
    client.force_login(user)

    response = client.post(
        reverse('testplans:create'),
        {
            'project': project.id,
            'name': 'Plan versionado',
            'version': '1.0',
            'description': 'Plan con historial.',
            'scope': 'Proyecto completo',
            'objective': 'Guardar historial inicial.',
            'strategy': 'Pruebas funcionales.',
            'entry_criteria': 'Requisitos aprobados',
            'exit_criteria': 'Casos ejecutados',
            'resources': 'Equipo QA',
            'environment': 'Local',
            'responsibilities': 'Estudiante',
            'estimation': '8 horas',
            'status': PlanModel.Status.DRAFT,
        },
    )

    plan = PlanModel.objects.get(name='Plan versionado')
    version = plan.versions.get()

    assert response.status_code == 302
    assert version.version_number == 1
    assert version.version_label == '1.0'
    assert version.snapshot['entry_criteria'] == 'Requisitos aprobados'
    assert AuditLog.objects.filter(action='CREATE', entity='TestPlan', entity_id=str(plan.pk)).exists()


@pytest.mark.django_db
def test_actualizacion_de_plan_agrega_version(client, test_plan, requirement, user):
    PlanVersionModel.objects.create(
        test_plan=test_plan,
        version_number=1,
        version_label=test_plan.version,
        name=test_plan.name,
        objective=test_plan.objective,
        status=test_plan.status,
        changed_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse('testplans:edit', args=[test_plan.pk]),
        {
            'project': test_plan.project_id,
            'name': 'Plan funcional actualizado',
            'version': '1.1',
            'description': 'Plan actualizado.',
            'scope': 'Modulos principales',
            'objective': 'Validar flujo y versionado.',
            'strategy': 'Pruebas basadas en riesgo.',
            'entry_criteria': 'Ambiente listo',
            'exit_criteria': 'Casos criticos aprobados',
            'resources': 'Equipo QA',
            'environment': 'Chrome',
            'responsibilities': 'Estudiante ejecuta',
            'estimation': '10 horas',
            'status': PlanModel.Status.REVIEW,
        },
    )

    test_plan.refresh_from_db()

    assert response.status_code == 302
    assert test_plan.versions.count() == 2
    assert test_plan.versions.first().version_label == '1.1'
    assert test_plan.versions.first().snapshot['strategy'] == 'Pruebas basadas en riesgo.'
    assert AuditLog.objects.filter(action='UPDATE', entity='TestPlan', entity_id=str(test_plan.pk)).exists()


@pytest.mark.django_db
def test_formulario_de_plan_exige_requisitos_previos(project):
    form = PlanForm(
        data={
            'project': project.id,
            'name': 'Plan sin requisitos',
            'objective': 'No debe crearse fuera de orden.',
            'status': PlanModel.Status.DRAFT,
        }
    )

    assert not form.is_valid()
    assert 'project' in form.errors

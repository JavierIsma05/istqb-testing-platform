import datetime
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

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
def test_formulario_de_plan_no_incluye_documento_base(project, requirement):
    form = PlanForm(
        data={
            'project': project.id,
            'name': 'Plan sin documento',
            'version': '1.0',
            'objective': 'Validar que el formulario ya no expone el documento base.',
            'status': PlanModel.Status.DRAFT,
        },
    )

    assert form.is_valid(), form.errors
    assert 'base_document' not in form.fields


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


@pytest.fixture
def project_with_dates(project, requirement):
    year = timezone.localdate().year
    project.start_date = datetime.date(year, 1, 10)
    project.end_date = datetime.date(year, 6, 30)
    project.save(update_fields=['start_date', 'end_date'])
    return project


def plan_data(project, **overrides):
    data = {
        'project': project.id,
        'name': 'Plan con fechas',
        'version': '1.0',
        'objective': 'Validar regla de fechas.',
        'status': PlanModel.Status.DRAFT,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_plan_rechaza_inicio_anterior_al_inicio_del_proyecto(project_with_dates):
    year = timezone.localdate().year
    form = PlanForm(
        data=plan_data(
            project_with_dates,
            start_date=f'{year}-01-01',
            end_date=f'{year}-06-30',
        )
    )

    assert not form.is_valid()
    assert 'start_date' in form.errors
    assert 'período definido para el proyecto' in form.errors['start_date'][0]


@pytest.mark.django_db
def test_plan_rechaza_fin_posterior_al_fin_del_proyecto(project_with_dates):
    year = timezone.localdate().year
    form = PlanForm(
        data=plan_data(
            project_with_dates,
            start_date=f'{year}-01-10',
            end_date=f'{year}-07-01',
        )
    )

    assert not form.is_valid()
    assert 'end_date' in form.errors
    assert 'período definido para el proyecto' in form.errors['end_date'][0]


@pytest.mark.django_db
def test_plan_rechaza_inicio_posterior_a_su_fin(project_with_dates):
    year = timezone.localdate().year
    form = PlanForm(
        data=plan_data(
            project_with_dates,
            start_date=f'{year}-06-30',
            end_date=f'{year}-01-10',
        )
    )

    assert not form.is_valid()
    assert 'end_date' in form.errors


@pytest.mark.django_db
def test_plan_acepta_fechas_dentro_del_periodo_del_proyecto(project_with_dates):
    year = timezone.localdate().year
    form = PlanForm(
        data=plan_data(
            project_with_dates,
            start_date=f'{year}-02-01',
            end_date=f'{year}-05-15',
        )
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_plan_rechaza_fechas_fuera_de_rango_en_vista(client, project_with_dates, user):
    year = timezone.localdate().year
    client.force_login(user)

    response = client.post(
        reverse('testplans:create'),
        plan_data(
            project_with_dates,
            start_date=f'{year}-01-01',
            end_date=f'{year}-07-01',
        ),
    )

    assert response.status_code == 200
    assert not PlanModel.objects.filter(name='Plan con fechas').exists()
    assert 'período definido para el proyecto'.encode() in response.content


@pytest.mark.django_db
def test_creacion_de_plan_guarda_riesgos_desde_payload_json(client, project, requirement, user):
    import json
    from apps.incidents.models import Incident

    client.force_login(user)
    risks_json = json.dumps([
        {
            'title': 'Retraso de la API',
            'description': 'Puede caerse la integracion con la pasarela.',
            'mitigation_strategy': 'Monitoreo continuo y fallback.',
            'probability': 'HIGH',
            'impact': 'HIGH',
        },
        {
            'description': 'Sin titulo, se genera desde descripcion.',
            'mitigation_strategy': 'Capacitacion del equipo.',
            'probability': 'LOW',
            'impact': 'LOW',
        },
    ])

    response = client.post(
        reverse('testplans:create'),
        {
            'project': project.id,
            'name': 'Plan con riesgos',
            'version': '1.0',
            'description': 'Plan con riesgos.',
            'scope': 'Proyecto completo',
            'objective': 'Registrar riesgos.',
            'strategy': 'Pruebas basadas en riesgo.',
            'entry_criteria': 'Requisitos aprobados',
            'exit_criteria': 'Casos ejecutados',
            'resources': 'Equipo QA',
            'environment': 'Local',
            'responsibilities': 'Estudiante',
            'estimation': '8 horas',
            'status': PlanModel.Status.DRAFT,
            'risks_json': risks_json,
        },
    )

    plan = PlanModel.objects.get(name='Plan con riesgos')
    risks = list(plan.risks.order_by('created_at'))

    assert response.status_code == 302
    assert len(risks) == 2
    first, second = risks
    assert first.title == 'Retraso de la API'
    assert first.probability == Incident.Probability.HIGH
    assert first.impact == Incident.Impact.HIGH
    assert first.code.startswith('INC-')
    assert first.reported_by == user
    assert second.title.startswith('Sin titulo')
    assert second.probability == Incident.Probability.LOW


@pytest.mark.django_db
def test_creacion_de_plan_sin_riesgos_no_crea_incidents(client, project, requirement, user):
    from apps.incidents.models import Incident

    client.force_login(user)
    response = client.post(
        reverse('testplans:create'),
        {
            'project': project.id,
            'name': 'Plan sin riesgos',
            'version': '1.0',
            'description': 'Plan sin riesgos.',
            'objective': 'Sin riesgos.',
            'status': PlanModel.Status.DRAFT,
            'risks_json': '[]',
        },
    )

    assert response.status_code == 302
    plan = PlanModel.objects.get(name='Plan sin riesgos')
    assert plan.risks.count() == 0
    assert Incident.objects.filter(test_plan=plan).count() == 0


@pytest.mark.django_db
def test_formulario_plan_muestra_paso_de_riesgos_con_matriz_y_boton(client, project, requirement, user):
    client.force_login(user)

    response = client.get(reverse('testplans:create'))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Matriz de Probabilidad e Impacto' in content
    assert 'Agregar riesgo' in content
    assert 'risks_json' in content
    assert 'Requisito relacionado' not in content

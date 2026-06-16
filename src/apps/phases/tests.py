import pytest
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.phases.models import TestingPhase as PhaseModel
from apps.phases.views import ensure_default_phases, phase_criteria_status
from apps.requirements.models import Requirement
from apps.testplans import models as testplan_models
from apps.users.models import User


@pytest.mark.django_db
def test_fase_de_testing_se_crea_pendiente_y_ordenada(project):
    phase = PhaseModel.objects.create(
        project=project,
        name='Diseno de pruebas',
        order=1,
        pending_tasks=3,
    )

    assert phase.status == PhaseModel.Status.PENDING
    assert phase.progress == 0
    assert phase.pending_tasks == 3
    assert str(phase) == 'Diseno de pruebas'


@pytest.mark.django_db
def test_fases_por_defecto_incluyen_criterios_y_linea_de_tiempo(project):
    ensure_default_phases(project)

    first_phase = PhaseModel.objects.get(project=project, order=1)

    assert first_phase.entry_criteria
    assert first_phase.exit_criteria
    assert first_phase.status == PhaseModel.Status.IN_PROGRESS


@pytest.mark.django_db
def test_no_completa_fase_si_faltan_criterios(client, project, user):
    ensure_default_phases(project)
    phase = PhaseModel.objects.get(project=project, order=1)
    client.force_login(user)

    response = client.post(reverse('phases:advance', args=[phase.pk]))

    phase.refresh_from_db()

    assert response.status_code == 302
    assert phase.status == PhaseModel.Status.IN_PROGRESS
    assert phase.completed_at is None
    assert not AuditLog.objects.filter(action='COMPLETE', entity='TestingPhase', entity_id=str(phase.pk)).exists()


@pytest.mark.django_db
def test_completa_fase_y_registra_fechas_si_criterios_cumplen(client, project, user):
    ensure_default_phases(project)
    phase = PhaseModel.objects.get(project=project, order=1)
    Requirement.objects.create(
        project=project,
        code='REQ-PHASE-001',
        title='Requisito revisado',
        description='Requisito listo para planificar pruebas.',
        status=Requirement.Status.REVIEW,
        created_by=user,
    )
    client.force_login(user)

    response = client.post(reverse('phases:advance', args=[phase.pk]))

    phase.refresh_from_db()
    next_phase = PhaseModel.objects.get(project=project, order=2)

    assert response.status_code == 302
    assert phase.status == PhaseModel.Status.DONE
    assert phase.progress == 100
    assert phase.started_at is not None
    assert phase.completed_at is not None
    assert next_phase.status == PhaseModel.Status.IN_PROGRESS
    assert AuditLog.objects.filter(action='COMPLETE', entity='TestingPhase', entity_id=str(phase.pk)).exists()


@pytest.mark.django_db
def test_tutor_no_puede_avanzar_fases(client, project):
    teacher = User.objects.create_user(
        email='teacher@example.edu',
        password='StrongPass123',
        role=User.Roles.TEACHER,
    )
    project.members.add(teacher)
    ensure_default_phases(project)
    phase = PhaseModel.objects.get(project=project, order=1)
    client.force_login(teacher)

    response = client.post(reverse('phases:advance', args=[phase.pk]))

    phase.refresh_from_db()

    assert response.status_code == 302
    assert phase.status == PhaseModel.Status.IN_PROGRESS


@pytest.mark.django_db
def test_criterios_de_fase_calculan_tareas(project, user):
    ensure_default_phases(project)
    phase = PhaseModel.objects.get(project=project, order=1)
    Requirement.objects.create(
        project=project,
        code='REQ-PHASE-002',
        title='Requisito pendiente',
        description='Todavia no ha sido revisado.',
        created_by=user,
    )

    criteria = phase_criteria_status(phase)

    assert criteria['completed_tasks'] == 2
    assert criteria['pending_tasks'] == 1
    assert not criteria['can_complete']

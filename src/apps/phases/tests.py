import pytest

from apps.phases.models import TestingPhase as PhaseModel


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

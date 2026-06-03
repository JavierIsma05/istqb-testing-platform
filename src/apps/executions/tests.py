import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.executions.forms import ExecutionResultForm
from apps.executions.models import TestExecution as ExecutionModel


@pytest.mark.django_db
def test_ejecucion_registra_resultado_y_responsable(execution, test_case, user):
    assert execution.test_case == test_case
    assert execution.executed_by == user
    assert execution.result == ExecutionModel.Result.PASSED
    assert 'TC-001 - Login exitoso' in str(execution)


def test_formulario_de_resultado_no_permite_estado_no_ejecutado():
    form = ExecutionResultForm(
        data={
            'result': ExecutionModel.Result.NOT_RUN,
            'notes': 'Pendiente',
        }
    )

    assert not form.is_valid()
    assert 'result' in form.errors


@pytest.mark.django_db
def test_vista_de_ejecucion_guarda_y_muestra_evidencia(client, test_case, user, tmp_path):
    client.force_login(user)
    evidence = SimpleUploadedFile(
        'captura.png',
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR',
        content_type='image/png',
    )

    with override_settings(MEDIA_ROOT=tmp_path):
        response = client.post(
            f'{reverse("executions:index")}?case={test_case.id}',
            data={
                'result': ExecutionModel.Result.PASSED,
                'notes': 'Ejecucion con evidencia.',
                'evidence': evidence,
            },
            follow=True,
        )

        execution = ExecutionModel.objects.get(test_case=test_case)

    assert response.status_code == 200
    assert execution.evidence.name.startswith('evidence/')
    assert execution.evidence.name.endswith('.png')
    assert b'Evidencia adjunta' in response.content
    assert b'Ver archivo' in response.content


@pytest.mark.django_db
def test_vista_de_ejecucion_elimina_ejecucion_del_historial(client, execution, test_case, user):
    client.force_login(user)

    response = client.post(reverse('executions:delete', args=[execution.pk]))

    assert response.status_code == 302
    assert response.url == f'{reverse("executions:index")}?case={test_case.id}'
    assert not ExecutionModel.objects.filter(pk=execution.pk).exists()
    test_case.refresh_from_db()
    assert test_case.status == test_case.Status.PENDING

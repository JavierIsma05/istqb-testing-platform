import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_regla_automatizada_no_acepta_get(client, project, test_case, user):
    client.force_login(user)

    response = client.get(
        reverse('executions:rule-create', kwargs={'case_id': test_case.pk})
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_eliminacion_de_regla_automatizada_no_acepta_get(client, project, test_case, user):
    client.force_login(user)

    # No se requiere una regla existente: el método HTTP debe rechazarse antes
    # de resolver el objeto, evitando usar GET para una operación destructiva.
    response = client.get(
        reverse('executions:rule-delete', kwargs={'pk': 999999})
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_ejecucion_automatizada_no_acepta_get(client, project, test_case, user):
    client.force_login(user)

    response = client.get(
        reverse('executions:run-automated', kwargs={'case_id': test_case.pk})
    )

    assert response.status_code == 405

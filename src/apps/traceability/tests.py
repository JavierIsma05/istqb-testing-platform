import pytest
from django.db import IntegrityError
from django.urls import reverse

from apps.incidents.models import Incident
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
def test_matriz_no_repite_riesgos_del_plan_en_cada_requisito(client, user, project, requirement, test_plan, test_case):
    Incident.objects.create(
        project=project,
        test_plan=test_plan,
        code='RIE-001',
        title='Riesgo general del plan',
        description='Este riesgo aplica al plan completo, no a un requisito especifico.',
        reported_by=user,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:index'))

    assert response.status_code == 200
    assert response.context['rows'][0]['coverage'] == 100
    assert response.context['rows'][0]['risks'] == []
    assert response.context['total_risks'] == 1

import pytest
from django.db import IntegrityError

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

import pytest
from django.core.exceptions import ValidationError

from apps.core.lifecycle import (
    status_transition_for_requirement,
    status_transition_for_test_case,
)
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase


@pytest.mark.django_db
def test_requisito_no_puede_saltar_directamente_de_pendiente_a_aprobado(requirement):
    requirement.status = Requirement.Status.PENDING
    with pytest.raises(ValidationError):
        status_transition_for_requirement(requirement, Requirement.Status.APPROVED)


@pytest.mark.django_db
def test_requisito_puede_volver_de_revision_a_pendiente(requirement):
    requirement.status = Requirement.Status.REVIEW
    assert status_transition_for_requirement(requirement, Requirement.Status.PENDING)


@pytest.mark.django_db
def test_caso_no_puede_saltar_de_pendiente_a_aprobado(test_case):
    test_case.status = TestCase.Status.PENDING
    with pytest.raises(ValidationError):
        status_transition_for_test_case(test_case, TestCase.Status.PASSED)


@pytest.mark.django_db
def test_caso_listo_puede_iniciar_ejecucion(test_case):
    test_case.status = TestCase.Status.READY
    assert status_transition_for_test_case(test_case, TestCase.Status.RUNNING)


@pytest.mark.django_db
def test_caso_completado_puede_volver_a_listo_si_se_requiere_reejecucion(test_case):
    test_case.status = TestCase.Status.PASSED
    assert status_transition_for_test_case(test_case, TestCase.Status.READY)

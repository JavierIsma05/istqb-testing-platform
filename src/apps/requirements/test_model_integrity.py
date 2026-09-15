import pytest
from django.core.exceptions import ValidationError

from apps.requirements.models import Requirement


@pytest.mark.django_db
def test_requirement_rejects_blank_title(project, user):
    requirement = Requirement(
        project=project,
        code='REQ-INVALID-001',
        title='   ',
        description='Descripción válida.',
        created_by=user,
    )

    with pytest.raises(ValidationError):
        requirement.save()


@pytest.mark.django_db
def test_requirement_rejects_blank_description(project, user):
    requirement = Requirement(
        project=project,
        code='REQ-INVALID-002',
        title='Título válido',
        description='   ',
        created_by=user,
    )

    with pytest.raises(ValidationError):
        requirement.save()


@pytest.mark.django_db
def test_requirement_rejects_blank_code(project, user):
    requirement = Requirement(
        project=project,
        code='   ',
        title='Título válido',
        description='Descripción válida.',
        created_by=user,
    )

    with pytest.raises(ValidationError):
        requirement.save()

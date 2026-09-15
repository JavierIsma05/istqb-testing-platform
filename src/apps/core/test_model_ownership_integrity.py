import pytest
from django.core.exceptions import ValidationError

from apps.projects.models import Project
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan


@pytest.mark.django_db
def test_requirement_no_puede_moverse_a_otro_proyecto(requirement, user):
    other_project = Project.objects.create(
        code='PRJ-002',
        name='Otro proyecto',
        description='Proyecto independiente',
        created_by=user,
    )
    requirement.project = other_project

    with pytest.raises(ValidationError, match='no puede cambiarse'):
        requirement.save()

    requirement.refresh_from_db()
    assert requirement.project_id != other_project.id


@pytest.mark.django_db
def test_test_case_no_puede_moverse_a_otro_plan(test_case, project, user):
    other_plan = TestPlan.objects.create(
        project=project,
        name='Otro plan',
        objective='Plan independiente',
        created_by=user,
    )
    test_case.test_plan = other_plan

    with pytest.raises(ValidationError, match='no puede cambiarse'):
        test_case.save()

    test_case.refresh_from_db()
    assert test_case.test_plan_id != other_plan.id

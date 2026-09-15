import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.testplans.models import TestPlan


@pytest.mark.django_db
def test_test_plan_clean_rejects_invalid_percentages(project, user):
    plan = TestPlan(
        project=project,
        name='Plan con porcentaje invalido',
        objective='Validar porcentajes.',
        minimum_pass_percentage=101,
        minimum_coverage_percentage=101,
        created_by=user,
    )

    with pytest.raises(ValidationError) as exc_info:
        plan.full_clean()

    assert 'minimum_pass_percentage' in exc_info.value.message_dict
    assert 'minimum_coverage_percentage' in exc_info.value.message_dict


@pytest.mark.django_db
def test_test_plan_clean_rejects_end_date_before_start_date(project, user):
    plan = TestPlan(
        project=project,
        name='Plan con rango invalido',
        objective='Validar fechas.',
        start_date=datetime.date(2026, 9, 20),
        end_date=datetime.date(2026, 9, 19),
        created_by=user,
    )

    with pytest.raises(ValidationError) as exc_info:
        plan.full_clean()

    assert 'end_date' in exc_info.value.message_dict


@pytest.mark.django_db
def test_test_plan_clean_rejects_dates_outside_project_period(project, user):
    project.start_date = datetime.date(2026, 9, 1)
    project.end_date = datetime.date(2026, 9, 30)
    project.save(update_fields=['start_date', 'end_date'])

    plan = TestPlan(
        project=project,
        name='Plan fuera del periodo',
        objective='Validar periodo.',
        start_date=datetime.date(2026, 8, 31),
        end_date=datetime.date(2026, 10, 1),
        created_by=user,
    )

    with pytest.raises(ValidationError) as exc_info:
        plan.full_clean()

    assert 'start_date' in exc_info.value.message_dict
    assert 'end_date' in exc_info.value.message_dict

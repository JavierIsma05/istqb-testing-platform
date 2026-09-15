import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.projects.models import Project


@pytest.mark.django_db
def test_project_clean_rejects_end_date_before_start_date(user):
    project = Project(
        code='PRJ-DATES',
        name='Proyecto con fechas invalidas',
        created_by=user,
        start_date=datetime.date(2026, 9, 15),
        end_date=datetime.date(2026, 9, 14),
    )

    with pytest.raises(ValidationError) as exc_info:
        project.full_clean()

    assert 'end_date' in exc_info.value.message_dict

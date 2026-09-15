import pytest
from django.urls import reverse

from apps.users.models import User


@pytest.fixture
def teacher(user, project):
    user.role = User.Roles.TEACHER
    user.save(update_fields=['role'])
    project.members.add(user)
    return user


@pytest.mark.django_db
def test_teacher_api_projects_only_allows_get(client, teacher):
    client.force_login(teacher)

    response = client.post(reverse('executions:api-projects'))

    assert response.status_code == 405


@pytest.mark.django_db
def test_teacher_api_students_only_allows_get(client, teacher, project):
    client.force_login(teacher)

    response = client.post(
        reverse('executions:api-students', kwargs={'project_id': project.pk}),
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_teacher_api_cases_only_allows_get(client, teacher, project, user):
    client.force_login(teacher)
    project.members.add(user)

    response = client.post(
        reverse(
            'executions:api-cases',
            kwargs={'project_id': project.pk, 'student_id': user.pk},
        ),
    )

    assert response.status_code == 405

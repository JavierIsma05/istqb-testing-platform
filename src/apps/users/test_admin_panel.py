import pytest
from django.urls import reverse

from apps.projects.models import Project
from apps.users.models import User


@pytest.mark.django_db
def test_admin_is_sent_to_private_dashboard_and_cannot_open_istqb_modules(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse('dashboard'))
    assert response.status_code == 302
    assert response.url == reverse('users:admin-dashboard')

    blocked = client.get(reverse('requirements:index'))
    assert blocked.status_code == 302
    assert blocked.url == reverse('users:admin-dashboard')

    panel = client.get(reverse('users:admin-dashboard'))
    assert panel.status_code == 200
    assert b'Panel de control' in panel.content
    assert b'Gestiona docentes' not in panel.content


@pytest.mark.django_db
def test_non_admin_cannot_access_private_admin_panel(client, user):
    client.force_login(user)
    response = client.get(reverse('users:admin-dashboard'))
    assert response.status_code == 302
    assert response.url == reverse('dashboard')


@pytest.mark.django_db
def test_admin_can_create_teacher_through_private_crud(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse('users:admin-user-create'), {
        'email': 'docente.admin@example.com',
        'first_name': 'Docente',
        'last_name': 'Admin',
        'role': User.Roles.TEACHER,
        'is_active': 'on',
        'password1': 'StrongPass123',
        'password2': 'StrongPass123',
    })
    assert response.status_code == 302
    teacher = User.objects.get(email='docente.admin@example.com')
    assert teacher.role == User.Roles.TEACHER
    assert teacher.check_password('StrongPass123')
    assert teacher.is_staff is False


@pytest.mark.django_db
def test_admin_can_create_project_and_assign_teacher(client, admin_user):
    teacher = User.objects.create_user(email='tutor.admin@example.com', password='StrongPass123', role=User.Roles.TEACHER)
    student = User.objects.create_user(email='student.admin@example.com', password='StrongPass123', role=User.Roles.STUDENT)
    client.force_login(admin_user)
    response = client.post(reverse('users:admin-project-create'), {
        'name': 'Proyecto administrativo',
        'description': 'Proyecto creado desde el panel de administración.',
        'start_date': '2026-10-01',
        'end_date': '2026-11-01',
        'tutor': teacher.pk,
        'members': [student.pk],
    })
    assert response.status_code == 302
    project = Project.objects.get(name='Proyecto administrativo')
    assert project.created_by == admin_user
    assert project.tutor == teacher
    assert project.members.filter(pk=student.pk).exists()
    assert project.members.filter(pk=teacher.pk).exists()

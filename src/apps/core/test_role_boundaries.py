import pytest
from django.contrib.auth import get_user_model

from apps.core.permissions import can_manage_artifacts, can_manage_project, can_view_project
from apps.projects.models import Project


@pytest.mark.django_db
def test_teacher_puede_ver_proyecto_pero_no_administrar_su_contenido(user, project):
    User = get_user_model()
    teacher = User.objects.create_user(
        email='teacher-boundary@example.com',
        password='StrongPass123',
        role=User.Roles.TEACHER,
    )
    project.members.add(teacher)

    assert can_view_project(teacher, project) is True
    assert can_manage_project(teacher, project) is False
    assert can_manage_artifacts(teacher) is False


@pytest.mark.django_db
def test_estudiante_propietario_puede_administrar_su_proyecto(user, project):
    User = get_user_model()
    user.role = User.Roles.STUDENT
    user.save(update_fields=['role'])

    assert can_view_project(user, project) is True
    assert can_manage_project(user, project) is True
    assert can_manage_artifacts(user) is True


@pytest.mark.django_db
def test_administrador_puede_administrar_proyecto_de_otro_usuario(user, project):
    User = get_user_model()
    admin = User.objects.create_user(
        email='admin-boundary@example.com',
        password='StrongPass123',
        role=User.Roles.ADMIN,
    )

    assert can_view_project(admin, project) is True
    assert can_manage_project(admin, project) is True
    assert can_manage_artifacts(admin) is True

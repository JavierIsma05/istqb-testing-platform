import pytest

from apps.audit.models import AuditLog
from apps.audit.services import log_action


@pytest.mark.django_db
def test_auditoria_registra_actor_accion_entidad_y_metadata(user):
    audit_log = AuditLog.objects.create(
        actor=user,
        action='CREATE',
        entity='Project',
        entity_id='PRJ-001',
        metadata={'code': 'PRJ-001'},
    )

    assert audit_log.actor == user
    assert audit_log.metadata['code'] == 'PRJ-001'
    assert str(audit_log) == 'CREATE Project'


@pytest.mark.django_db
def test_log_action_crea_bitacora_estandar(user):
    audit_log = log_action(
        user,
        'UPDATE',
        'Requirement',
        'REQ-001',
        {'project_id': 1},
    )

    assert audit_log.actor == user
    assert audit_log.action == 'UPDATE'
    assert audit_log.entity == 'Requirement'
    assert audit_log.entity_id == 'REQ-001'
    assert audit_log.metadata['project_id'] == 1


@pytest.mark.django_db
def test_bitacora_solo_es_visible_para_administradores(client, user, admin_user):
    client.force_login(user)
    response = client.get('/audit/')
    assert response.status_code == 302

    AuditLog.objects.create(
        actor=admin_user,
        action='CREATE',
        entity='Project',
        entity_id='1',
        metadata={'project_id': 1, 'code': 'PRJ-001'},
    )
    client.force_login(admin_user)
    response = client.get('/audit/?action=CREATE&q=PRJ-001')
    assert response.status_code == 200
    assert b'PRJ-001' in response.content


@pytest.mark.django_db
def test_bitacora_filtra_por_proyecto(client, admin_user, project):
    AuditLog.objects.create(
        actor=admin_user,
        action='UPDATE',
        entity='Requirement',
        entity_id='REQ-001',
        metadata={'project_id': project.pk},
    )
    client.force_login(admin_user)
    response = client.get(f'/audit/?project={project.pk}')
    assert response.status_code == 200
    assert b'REQ-001' in response.content

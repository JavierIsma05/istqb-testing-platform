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

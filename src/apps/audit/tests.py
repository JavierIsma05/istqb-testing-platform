import pytest

from apps.audit.models import AuditLog


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

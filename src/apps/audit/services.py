from .models import AuditLog


def log_action(actor, action, entity, entity_id='', metadata=None):
    return AuditLog.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id or ''),
        metadata=metadata or {},
    )

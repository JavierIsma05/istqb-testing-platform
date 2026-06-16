from .models import DefectHistory


def defect_snapshot(defect):
    return {
        'project_id': defect.project_id,
        'execution_id': defect.execution_id,
        'code': defect.code,
        'title': defect.title,
        'description': defect.description,
        'steps_to_reproduce': defect.steps_to_reproduce,
        'severity': defect.severity,
        'priority': defect.priority,
        'status': defect.status,
        'reported_by_id': defect.reported_by_id,
        'assigned_to_id': defect.assigned_to_id,
    }


def record_defect_history(defect, changed_by=None, reason=''):
    return DefectHistory.objects.create(
        defect=defect,
        status=defect.status,
        severity=defect.severity,
        priority=defect.priority,
        assigned_to=defect.assigned_to,
        changed_by=changed_by,
        change_reason=reason,
        snapshot=defect_snapshot(defect),
    )

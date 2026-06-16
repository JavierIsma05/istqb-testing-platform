from .models import RequirementVersion


def requirement_snapshot(requirement):
    return {
        'code': requirement.code,
        'title': requirement.title,
        'description': requirement.description,
        'requirement_type': requirement.requirement_type,
        'priority': requirement.priority,
        'status': requirement.status,
        'project_id': requirement.project_id,
    }


def record_requirement_version(requirement, changed_by=None, reason=''):
    next_number = requirement.versions.count() + 1
    return RequirementVersion.objects.create(
        requirement=requirement,
        version_number=next_number,
        title=requirement.title,
        description=requirement.description,
        requirement_type=requirement.requirement_type,
        priority=requirement.priority,
        status=requirement.status,
        changed_by=changed_by,
        change_reason=reason,
        snapshot=requirement_snapshot(requirement),
    )

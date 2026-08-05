from .models import FormDraft


def draft_key(module, project_id=0, object_id=0):
    return f'{module}:{int(project_id or 0)}:{int(object_id or 0)}'


def get_draft(user, module, project_id=0, object_id=0):
    return FormDraft.objects.filter(user=user, key=draft_key(module, project_id, object_id)).first()


def save_draft(user, module, data, project_id=0, object_id=0):
    draft, _ = FormDraft.objects.update_or_create(
        user=user,
        key=draft_key(module, project_id, object_id),
        defaults={'module': module, 'data': data},
    )
    return draft


def clear_draft(user, module, project_id=0, object_id=0):
    FormDraft.objects.filter(user=user, key=draft_key(module, project_id, object_id)).delete()

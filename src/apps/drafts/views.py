import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import draft_key, get_draft, clear_draft, save_draft


def _parse_body(request):
    try:
        return json.loads(request.body or b'{}')
    except (TypeError, ValueError):
        return {}


@login_required
@require_POST
def draft_save_view(request):
    payload = _parse_body(request)
    module = str(payload.get('module', '')).strip()
    data = payload.get('data')
    if not module or not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'module y data son requeridos'}, status=400)
    project_id = payload.get('project_id') or 0
    object_id = payload.get('object_id') or 0
    draft = save_draft(request.user, module, data, project_id, object_id)
    return JsonResponse({'ok': True, 'updated_at': draft.updated_at.isoformat()})


@login_required
def draft_get_view(request):
    module = request.GET.get('module', '')
    project_id = request.GET.get('project_id') or 0
    object_id = request.GET.get('object_id') or 0
    if not module:
        return JsonResponse({'found': False})
    draft = get_draft(request.user, module, project_id, object_id)
    if not draft:
        return JsonResponse({'found': False})
    return JsonResponse({'found': True, 'data': draft.data, 'updated_at': draft.updated_at.isoformat()})


@login_required
@require_POST
def draft_clear_view(request):
    payload = _parse_body(request)
    module = str(payload.get('module', '')).strip()
    if not module:
        return JsonResponse({'ok': False, 'error': 'module es requerido'}, status=400)
    project_id = payload.get('project_id') or 0
    object_id = payload.get('object_id') or 0
    clear_draft(request.user, module, project_id, object_id)
    return JsonResponse({'ok': True, 'key': draft_key(module, project_id, object_id)})

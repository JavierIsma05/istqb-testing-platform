import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import draft_key, get_draft, clear_draft, save_draft

ALLOWED_DRAFT_MODULES = {'testcase', 'testplan'}
MAX_DRAFT_BYTES = 200_000


def _parse_body(request):
    try:
        return json.loads(request.body or b'{}')
    except (TypeError, ValueError):
        return {}


def _context(values):
    module = str(values.get('module', '')).strip()
    if module not in ALLOWED_DRAFT_MODULES:
        raise ValueError('módulo de borrador no permitido')

    parsed_ids = []
    for name in ('project_id', 'object_id'):
        value = values.get(name) or 0
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f'{name} debe ser un entero')
        if value < 0:
            raise ValueError(f'{name} no puede ser negativo')
        parsed_ids.append(value)
    return module, parsed_ids[0], parsed_ids[1]


@login_required
@require_POST
def draft_save_view(request):
    if len(request.body or b'') > MAX_DRAFT_BYTES:
        return JsonResponse(
            {'ok': False, 'error': 'El borrador supera el tamaño máximo permitido'},
            status=413,
        )
    payload = _parse_body(request)
    data = payload.get('data')
    if not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'module y data son requeridos'}, status=400)
    try:
        module, project_id, object_id = _context(payload)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    draft = save_draft(request.user, module, data, project_id, object_id)
    return JsonResponse({'ok': True, 'updated_at': draft.updated_at.isoformat()})


@login_required
def draft_get_view(request):
    try:
        module, project_id, object_id = _context(request.GET)
    except ValueError as exc:
        return JsonResponse({'found': False, 'error': str(exc)}, status=400)
    draft = get_draft(request.user, module, project_id, object_id)
    if not draft:
        return JsonResponse({'found': False})
    return JsonResponse({'found': True, 'data': draft.data, 'updated_at': draft.updated_at.isoformat()})


@login_required
@require_POST
def draft_clear_view(request):
    payload = _parse_body(request)
    try:
        module, project_id, object_id = _context(payload)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    clear_draft(request.user, module, project_id, object_id)
    return JsonResponse({'ok': True, 'key': draft_key(module, project_id, object_id)})

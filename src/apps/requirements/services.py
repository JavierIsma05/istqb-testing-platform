import re
from dataclasses import dataclass

from .models import Requirement


class RequirementPdfImportError(Exception):
    pass


@dataclass
class ParsedRequirement:
    title: str
    description: str
    requirement_type: str = Requirement.RequirementType.FUNCTIONAL
    priority: str = Requirement.Priority.MEDIUM
    status: str = Requirement.Status.PENDING


REQUIREMENT_START_RE = re.compile(
    r'^\s*(?:(?P<code>(?:REQ|RF|RNF|FR|NFR)[-\s]?\d+)\s*[:.)-]\s*)?(?P<body>.+)$',
    re.IGNORECASE,
)
NUMBERED_START_RE = re.compile(r'^\s*\d+[\).:-]\s+.+$')
REQUIREMENT_WORD_RE = re.compile(
    r'\b(el sistema|la aplicacion|la plataforma|se debe|debe|debera|permitira|permite|requisito)\b',
    re.IGNORECASE,
)


def extract_text_from_pdf(pdf_file):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RequirementPdfImportError(
            'No esta instalada la dependencia pypdf. Ejecuta pip install -r requirements/base.txt.'
        ) from exc

    try:
        pdf_file.seek(0)
        reader = PdfReader(pdf_file)
        pages = [page.extract_text() or '' for page in reader.pages]
    except Exception as exc:
        raise RequirementPdfImportError('No se pudo leer el PDF. Verifica que el archivo no este protegido o danado.') from exc

    text = '\n'.join(pages).strip()
    if not text:
        raise RequirementPdfImportError(
            'No se detecto texto en el PDF. Si es un documento escaneado, se requiere OCR.'
        )

    return text


def parse_requirements_from_text(text, defaults=None, limit=100):
    defaults = defaults or {}
    blocks = _split_requirement_blocks(text)
    parsed = []

    for block in blocks:
        item = _parse_requirement_block(block, defaults)
        if item:
            parsed.append(item)
        if len(parsed) >= limit:
            break

    return parsed


def _split_requirement_blocks(text):
    blocks = []
    current = []

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line:
            continue

        starts_requirement = _looks_like_requirement_start(line)
        if starts_requirement and current:
            blocks.append(' '.join(current))
            current = [line]
        elif starts_requirement:
            current = [line]
        elif current:
            current.append(line)

    if current:
        blocks.append(' '.join(current))

    return blocks


def _looks_like_requirement_start(line):
    if line.lower().startswith(('nota:', 'observacion:', 'comentario:')):
        return False

    match = REQUIREMENT_START_RE.match(line)
    if match and match.group('code'):
        return True

    return bool(NUMBERED_START_RE.match(line) and REQUIREMENT_WORD_RE.search(line)) or bool(
        REQUIREMENT_WORD_RE.search(line)
    )


def _parse_requirement_block(block, defaults):
    match = REQUIREMENT_START_RE.match(block)
    code = (match.group('code') or '') if match else ''
    body = match.group('body').strip() if match else block.strip()
    body = re.sub(r'^\d+[\).:-]\s+', '', body).strip()

    if body.lower().startswith(('nota:', 'observacion:', 'comentario:')):
        return None

    if len(body) < 12 or not REQUIREMENT_WORD_RE.search(body):
        return None

    title = _build_title(body)
    return ParsedRequirement(
        title=title,
        description=body,
        requirement_type=_detect_requirement_type(body, defaults.get('requirement_type'), code=code),
        priority=_detect_priority(body, defaults.get('priority')),
        status=defaults.get('status', Requirement.Status.PENDING),
    )


def _build_title(text):
    title = re.split(r'(?<=[.!?])\s+', text, maxsplit=1)[0]
    if ':' in title and len(title.split(':', 1)[0]) <= 90:
        title = title.split(':', 1)[0]

    title = title.strip(' .:-')
    if len(title) > 120:
        title = f'{title[:117].rstrip()}...'

    return title


def _detect_requirement_type(text, default, code=''):
    if code.upper().startswith(('RNF', 'NFR')):
        return Requirement.RequirementType.NON_FUNCTIONAL

    lowered = text.lower()
    non_functional_terms = (
        'no funcional',
        'rendimiento',
        'seguridad',
        'usabilidad',
        'disponibilidad',
        'escalabilidad',
        'accesibilidad',
        'compatibilidad',
        'mantenibilidad',
        'confiabilidad',
        'fiabilidad',
        'portabilidad',
        'latencia',
        'cifrar',
        'cifrado',
        'encriptar',
        'encriptacion',
        'autenticacion multifactor',
        'auditoria',
        'backup',
        'respaldo',
        'recuperacion',
        'integridad',
        'privacidad',
        'tiempo de respuesta',
        'concurrencia',
    )
    if any(term in lowered for term in non_functional_terms):
        return Requirement.RequirementType.NON_FUNCTIONAL

    return default or Requirement.RequirementType.FUNCTIONAL


def _detect_priority(text, default):
    lowered = text.lower()
    if 'critica' in lowered or 'critico' in lowered:
        return Requirement.Priority.CRITICAL
    if 'alta' in lowered:
        return Requirement.Priority.HIGH
    if 'baja' in lowered:
        return Requirement.Priority.LOW
    return default or Requirement.Priority.MEDIUM


def _clean_line(line):
    return re.sub(r'\s+', ' ', line).strip(' \t-')

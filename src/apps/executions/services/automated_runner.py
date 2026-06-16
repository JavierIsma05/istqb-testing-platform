import ipaddress
import socket
from datetime import timedelta
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from apps.audit.services import log_action
from apps.core.codes import next_code
from apps.defects.history import record_defect_history
from apps.defects.models import Defect
from apps.executions.models import (
    AutomatedExecutionResult,
    AutomatedValidationRule,
    TestExecution,
    TestStepExecution,
)


def _allowed_hosts():
    configured = getattr(settings, 'AUTOMATION_ALLOWED_HOSTS', ('localhost', '127.0.0.1', '::1'))
    return {host.lower().strip('.') for host in configured if host}


def validate_automation_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'}:
        raise ValidationError('Solo se permiten URLs HTTP o HTTPS.')
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValidationError('La URL objetivo no es valida.')

    host = parsed.hostname.lower().strip('.')
    allowed_hosts = _allowed_hosts()
    allowed = host in allowed_hosts or any(host.endswith(f'.{item}') for item in allowed_hosts)
    if not allowed:
        raise ValidationError('El dominio no esta autorizado para ejecuciones automatizadas.')

    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80))
    except socket.gaierror as exc:
        raise ValidationError('No se pudo resolver el dominio configurado.') from exc

    local_names = {'localhost', '127.0.0.1', '::1'}
    if host not in local_names:
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                raise ValidationError('El dominio autorizado resolvio a una red interna no permitida.')
    return url


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_automation_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _execute_http_status(rule):
    validate_automation_url(rule.target_url)
    request = Request(
        rule.target_url,
        headers={'User-Agent': 'ISTQB-Testing-Platform/1.0'},
        method='GET',
    )
    opener = build_opener(SafeRedirectHandler())
    expected = rule.expected_http_status

    try:
        with opener.open(request, timeout=rule.timeout_seconds) as response:
            actual = response.status
            final_url = response.geturl()
            response.read(1)
    except HTTPError as exc:
        actual = exc.code
        final_url = exc.geturl()
    except (URLError, TimeoutError, OSError) as exc:
        return {
            'status': TestExecution.Result.ERROR,
            'expected': f'Codigo HTTP {expected}',
            'actual': 'No fue posible obtener una respuesta HTTP.',
            'log': f'[ERROR] GET {rule.target_url}: {exc}',
            'error': str(exc),
        }

    passed = actual == expected
    status = TestExecution.Result.PASSED if passed else TestExecution.Result.FAILED
    return {
        'status': status,
        'expected': f'Codigo HTTP {expected}',
        'actual': f'Codigo HTTP {actual}; URL final: {final_url}',
        'log': f'[{"PASS" if passed else "FAIL"}] GET {rule.target_url} -> {actual}',
        'error': '',
    }


def _selector(rule, secondary=False):
    value = rule.secondary_selector_value if secondary else rule.selector_value
    if not value:
        return ''
    if secondary or rule.selector_type == AutomatedValidationRule.SelectorType.CSS:
        return value
    if rule.selector_type == AutomatedValidationRule.SelectorType.ID:
        return f'#{value.lstrip("#")}'
    if rule.selector_type == AutomatedValidationRule.SelectorType.NAME:
        return f'[name="{value}"]'
    if rule.selector_type == AutomatedValidationRule.SelectorType.XPATH:
        return f'xpath={value}'
    return value


def _expected_text_visible(page, rule):
    if not rule.expected_text:
        return False
    return page.get_by_text(rule.expected_text, exact=False).first.is_visible()


def _field_is_invalid(locator):
    return locator.evaluate('element => Boolean(element.checkValidity) && !element.checkValidity()')


def _click_and_detect_block(page, button, initial_url, rule):
    button.click()
    page.wait_for_timeout(300)
    return (
        _field_is_invalid(page.locator(_selector(rule)).first)
        or _expected_text_visible(page, rule)
        or page.url == initial_url
    )


def _route_request(route):
    request_url = route.request.url
    if request_url.startswith(('data:', 'blob:', 'about:')):
        route.continue_()
        return
    try:
        validate_automation_url(request_url)
    except ValidationError:
        route.abort('blockedbyclient')
        return
    route.continue_()


def _browser_rule_result(page, rule):
    validation_type = rule.validation_type
    primary = page.locator(_selector(rule)).first if rule.selector_value else None
    secondary = page.locator(_selector(rule, secondary=True)).first if rule.secondary_selector_value else None
    initial_url = page.url

    if validation_type == AutomatedValidationRule.ValidationType.TEXT_VISIBLE:
        passed = _expected_text_visible(page, rule)
        actual = f'Texto {"visible" if passed else "no visible"}: {rule.expected_text}'
    elif validation_type == AutomatedValidationRule.ValidationType.ELEMENT_VISIBLE:
        passed = primary.is_visible()
        actual = f'Elemento {"visible" if passed else "no visible"}: {rule.selector_value}'
    elif validation_type == AutomatedValidationRule.ValidationType.BUTTON_DISABLED:
        passed = primary.is_disabled()
        actual = f'Boton {"deshabilitado" if passed else "habilitado"}: {rule.selector_value}'
    elif validation_type == AutomatedValidationRule.ValidationType.REDIRECT_URL:
        primary.click()
        page.wait_for_load_state('domcontentloaded')
        passed = page.url.rstrip('/') == rule.expected_url.rstrip('/')
        actual = f'URL final: {page.url}'
    elif validation_type == AutomatedValidationRule.ValidationType.FIELD_REQUIRED:
        primary.fill('')
        passed = _click_and_detect_block(page, secondary, initial_url, rule)
        actual = 'El formulario bloqueo el campo vacio.' if passed else 'El formulario permitio enviar el campo vacio.'
    elif validation_type == AutomatedValidationRule.ValidationType.EMAIL_FORMAT:
        primary.fill(rule.input_value)
        passed = _click_and_detect_block(page, secondary, initial_url, rule)
        actual = 'El correo invalido fue rechazado.' if passed else 'El correo invalido fue aceptado.'
    elif validation_type == AutomatedValidationRule.ValidationType.MAX_LENGTH:
        primary.fill(rule.input_value)
        stored_length = len(primary.input_value())
        passed = stored_length <= rule.max_length
        if not passed:
            passed = _click_and_detect_block(page, secondary, initial_url, rule)
        actual = f'Longitud almacenada: {stored_length}; maximo esperado: {rule.max_length}.'
    elif validation_type == AutomatedValidationRule.ValidationType.MIN_LENGTH:
        primary.fill(rule.input_value)
        passed = _click_and_detect_block(page, secondary, initial_url, rule)
        actual = f'Longitud usada: {len(rule.input_value)}; minimo esperado: {rule.min_length}.'
    elif validation_type == AutomatedValidationRule.ValidationType.FORM_SUBMISSION_BLOCKED:
        if primary:
            primary.fill(rule.input_value)
        passed = _click_and_detect_block(page, secondary, initial_url, rule)
        actual = 'El envio fue bloqueado.' if passed else f'El formulario navego a {page.url}.'
    else:
        raise ValidationError('Tipo de validacion de navegador no soportado.')

    return passed, actual


def _execute_browser_rule(rule):
    validate_automation_url(rule.target_url)
    timeout_ms = rule.timeout_seconds * 1000
    browser_name = (rule.browser or 'chromium').lower()
    if browser_name != 'chromium':
        return {
            'status': TestExecution.Result.BLOCKED,
            'expected': rule.expected_text or rule.expected_value or rule.get_validation_type_display(),
            'actual': f'El navegador {browser_name} no esta habilitado; usa chromium.',
            'log': f'[BLOCKED] Navegador no habilitado: {browser_name}.',
            'error': 'Navegador no habilitado.',
            'screenshot': None,
        }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=False)
            page = context.new_page()
            page.set_default_timeout(timeout_ms)
            page.route('**/*', _route_request)
            page.goto(rule.target_url, wait_until='domcontentloaded', timeout=timeout_ms)
            passed, actual = _browser_rule_result(page, rule)
            screenshot = page.screenshot(full_page=True) if rule.capture_evidence else None
            browser.close()
    except PlaywrightTimeoutError as exc:
        return {
            'status': TestExecution.Result.ERROR,
            'expected': rule.expected_text or rule.expected_value or rule.get_validation_type_display(),
            'actual': 'La pagina o el elemento excedio el tiempo de espera.',
            'log': f'[ERROR] Timeout en {rule.name}: {exc}',
            'error': str(exc),
            'screenshot': None,
        }
    except (ValidationError, PlaywrightError, OSError, RuntimeError) as exc:
        return {
            'status': TestExecution.Result.ERROR,
            'expected': rule.expected_text or rule.expected_value or rule.get_validation_type_display(),
            'actual': 'La validacion no pudo ejecutarse.',
            'log': f'[ERROR] {rule.name}: {exc}',
            'error': str(exc),
            'screenshot': None,
        }

    status = TestExecution.Result.PASSED if passed else TestExecution.Result.FAILED
    return {
        'status': status,
        'expected': rule.expected_text or rule.expected_value or rule.get_validation_type_display(),
        'actual': actual,
        'log': f'[{"PASS" if passed else "FAIL"}] {rule.name}: {actual}',
        'error': '',
        'screenshot': screenshot,
    }


def execute_rule(rule):
    if rule.validation_type == AutomatedValidationRule.ValidationType.HTTP_STATUS:
        outcome = _execute_http_status(rule)
        outcome['screenshot'] = None
        return outcome
    return _execute_browser_rule(rule)


def aggregate_automated_status(statuses):
    if TestExecution.Result.FAILED in statuses:
        return TestExecution.Result.FAILED
    if TestExecution.Result.ERROR in statuses:
        return TestExecution.Result.ERROR
    if TestExecution.Result.BLOCKED in statuses:
        return TestExecution.Result.BLOCKED
    if statuses and all(status == TestExecution.Result.PASSED for status in statuses):
        return TestExecution.Result.PASSED
    return TestExecution.Result.BLOCKED


def _create_automatic_defect(execution, failed_results):
    project = execution.test_case.test_plan.project
    failed_names = ', '.join(result.validation_rule.name for result in failed_results)
    defect = Defect.objects.create(
        project=project,
        execution=execution,
        code=next_code(Defect.objects.filter(project=project), 'DEF'),
        title=f'Fallo automatizado en {execution.test_case.code}'[:180],
        description=(
            f'La ejecucion semi-automatizada detecto reglas fallidas: {failed_names}.\n\n'
            f'Caso: {execution.test_case.code} - {execution.test_case.title}\n\n'
            f'Log tecnico:\n{execution.technical_log}'
        ),
        steps_to_reproduce='Ejecutar nuevamente las reglas automatizadas asociadas al caso de prueba.',
        severity=Defect.Severity.MEDIUM,
        priority=Defect.Priority.MEDIUM,
        reported_by=execution.executed_by,
    )
    record_defect_history(defect, execution.executed_by, 'Defecto generado por regla automatizada')
    return defect


def run_automated_execution(test_case, user):
    rules = list(test_case.automated_rules.filter(is_active=True).order_by('step_number', 'id'))
    started_at = timezone.now()
    execution = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        executed_at=started_at,
        started_at=started_at,
        execution_mode=TestExecution.ExecutionMode.SEMI_AUTOMATED,
        result=TestExecution.Result.RUNNING,
        environment_url=rules[0].target_url if rules else '',
        browser=rules[0].browser if rules else '',
        environment='Ejecucion asistida por reglas seguras',
    )

    result_rows = []
    log_lines = []
    for rule in rules:
        rule_started = timezone.now()
        outcome = execute_rule(rule)
        rule_finished = timezone.now()
        log_lines.append(outcome['log'])
        result = AutomatedExecutionResult.objects.create(
            test_execution=execution,
            validation_rule=rule,
            status=outcome['status'],
            expected_behavior=outcome['expected'],
            actual_behavior=outcome['actual'],
            input_used=rule.input_value,
            technical_log=outcome['log'],
            error_message=outcome['error'],
            started_at=rule_started,
            finished_at=rule_finished,
        )
        if outcome.get('screenshot'):
            result.screenshot.save(
                f'execution-{execution.pk}-rule-{rule.pk}.png',
                ContentFile(outcome['screenshot']),
                save=True,
            )
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=rule.step_number,
            action=rule.name,
            expected_result=outcome['expected'],
            obtained_result=outcome['actual'],
            status=outcome['status'],
            comment=outcome['error'],
            execution_log=outcome['log'],
            started_at=rule_started,
            finished_at=rule_finished,
        )
        result_rows.append(result)

    if not rules:
        log_lines.append('[BLOCKED] No existen reglas activas para este caso de prueba.')

    finished_at = timezone.now()
    execution.result = aggregate_automated_status([item.status for item in result_rows])
    execution.finished_at = finished_at
    execution.duration_seconds = Decimal(str((finished_at - started_at) / timedelta(seconds=1))).quantize(Decimal('0.001'))
    execution.technical_log = '\n'.join(log_lines)
    execution.actual_result = '\n'.join(item.actual_behavior for item in result_rows)
    execution.save(
        update_fields=[
            'result',
            'finished_at',
            'duration_seconds',
            'technical_log',
            'actual_result',
            'updated_at',
        ]
    )

    failed_results = [item for item in result_rows if item.status == TestExecution.Result.FAILED]
    if failed_results:
        _create_automatic_defect(execution, failed_results)

    log_action(
        user,
        'CREATE',
        'TestExecution',
        execution.pk,
        {
            'project_id': test_case.test_plan.project_id,
            'test_case_id': test_case.pk,
            'execution_mode': execution.execution_mode,
            'result': execution.result,
            'rule_count': len(rules),
        },
    )
    return execution

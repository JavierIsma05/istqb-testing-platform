import ipaddress
import re
import socket
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except ImportError:
    PlaywrightTimeoutError = Exception
    PlaywrightError = Exception
    sync_playwright = None

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
from apps.testcases.models import TestCase


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
            f'La ejecucion automatizada detecto pasos fallidos: {failed_names}.\n\n'
            f'Caso: {execution.test_case.code} - {execution.test_case.title}\n\n'
            f'Log técnico:\n{execution.technical_log}'
        ),
        steps_to_reproduce='Ejecutar nuevamente los pasos automatizados asociados al caso de prueba.',
        severity=Defect.Severity.MEDIUM,
        priority=Defect.Priority.MEDIUM,
        reported_by=execution.executed_by,
    )
    record_defect_history(defect, execution.executed_by, 'Defecto generado por ejecución automatizada')
    return defect


def run_automated_execution(test_case, user):
    test_case = TestCase.objects.prefetch_related('test_data_vars').get(pk=test_case.pk)
    steps = list(test_case.automated_rules.filter(is_active=True).order_by('step_number', 'id'))
    return run_automated_steps(test_case, user, steps)


def resolve_variables(text, test_case):
    """Replace {{variable}} placeholders with values from TestData."""
    if not text:
        return text
    # Use prefetched data to avoid sync DB access in async context
    variables = getattr(test_case, '_prefetched_objects_cache', {}).get('test_data_vars', None)
    if variables is None:
        variables = test_case.test_data_vars.all()
    var_dict = {var.key: var.value for var in variables}
    
    def replace_var(match):
        key = match.group(1).strip()
        return var_dict.get(key, match.group(0))
    
    return re.sub(r'\{\{([^}]+)\}\}', replace_var, text)


def evaluate(expected, actual, comparison_type=AutomatedValidationRule.ComparisonType.EXACT):
    """Compare expected vs actual based on comparison type. Returns (result, error_message)."""
    expected_text = '' if expected is None else str(expected).strip()
    actual_text = '' if actual is None else str(actual).strip()
    
    if comparison_type == AutomatedValidationRule.ComparisonType.CONTAINS:
        if expected_text in actual_text:
            return 'MATCH', ''
        else:
            return 'NO_MATCH', f'Se esperaba que contuviera "{expected_text}" y se obtuvo "{actual_text}"'
    elif comparison_type == AutomatedValidationRule.ComparisonType.REGEX:
        try:
            if re.search(expected_text, actual_text):
                return 'MATCH', ''
            else:
                return 'NO_MATCH', f'La expresión regular "{expected_text}" no coincidió con "{actual_text}"'
        except re.error as e:
            return 'NO_MATCH', f'Expresión regular inválida: {e}'
    else:  # EXACT
        if expected_text == actual_text:
            return 'MATCH', ''
        else:
            return 'NO_MATCH', f'Se esperaba "{expected_text}" y se obtuvo "{actual_text}"'


def get_comparison_description(comparison_type):
    """Get human-readable description of comparison type."""
    descriptions = {
        AutomatedValidationRule.ComparisonType.EXACT: 'Exacto',
        AutomatedValidationRule.ComparisonType.CONTAINS: 'Contiene',
        AutomatedValidationRule.ComparisonType.REGEX: 'Expresión regular',
    }
    return descriptions.get(comparison_type, 'Exacto')


def _step_expected_label(step):
    if step.action_type == AutomatedValidationRule.ActionType.VERIFY:
        return step.expected_value or step.input_value or ''
    if step.action_type == AutomatedValidationRule.ActionType.OPEN_URL:
        return step.target_url
    return step.expected_value or step.input_value or ''


def _execute_browser_step(page, step, test_case, timeout_ms):
    action = step.action_type
    comparison_type = step.comparison_type or AutomatedValidationRule.ComparisonType.EXACT
    error_message = ''
    
    # Resolve variables in step fields
    target_url = resolve_variables(step.target_url, test_case)
    selector_value = resolve_variables(step.selector_value, test_case)
    input_value = resolve_variables(step.input_value, test_case)
    expected_value = resolve_variables(step.expected_value, test_case)
    
    if action == AutomatedValidationRule.ActionType.OPEN_URL:
        validate_automation_url(target_url)
        page.goto(target_url, wait_until='domcontentloaded', timeout=timeout_ms)
        expected = target_url
        actual = page.url
        match_result, error_msg = evaluate(expected.rstrip('/'), actual.rstrip('/'), comparison_type)
        passed = match_result == 'MATCH'
        if not passed:
            error_message = error_msg
    elif action == AutomatedValidationRule.ActionType.CLICK:
        page.locator(selector_value).first.click()
        passed = True
        expected = 'Clic ejecutado'
        actual = 'Clic ejecutado'
    elif action == AutomatedValidationRule.ActionType.FILL_TEXT:
        page.locator(selector_value).first.fill(input_value or '')
        passed = True
        expected = f'Campo con texto: {input_value}'
        actual = 'Texto ingresado'
    elif action == AutomatedValidationRule.ActionType.WAIT:
        # WAIT can be either duration (timeout_seconds) or wait for selector
        if selector_value:
            page.locator(selector_value).first.wait_for(state='visible', timeout=timeout_ms)
            expected = f'Elemento visible: {selector_value}'
            actual = f'Elemento visible: {selector_value}'
        else:
            duration = int(step.timeout_seconds or input_value or 1)
            page.wait_for_timeout(duration * 1000)
            expected = f'Espera de {duration} segundos'
            actual = 'Espera completada'
        passed = True
    elif action == AutomatedValidationRule.ActionType.VERIFY:
        # VERIFY can check element visibility, text content, URL, or input value
        if selector_value == 'URL actual' or selector_value == 'current_url':
            # Verify current URL
            actual_url = page.url
            match_result, error_msg = evaluate(expected_value, actual_url, comparison_type)
            passed = match_result == 'MATCH'
            expected = f'URL {get_comparison_description(comparison_type).lower()}: {expected_value}'
            actual = f'URL actual: {actual_url}'
            if not passed:
                error_message = error_msg
        else:
            # Verify element - could be visibility, text, or value
            locator = page.locator(selector_value).first
            is_visible = locator.is_visible()
            
            if not is_visible:
                passed = False
                expected = f'Elemento visible: {selector_value}'
                actual = f'Elemento no visible: {selector_value}'
                error_message = f'El elemento "{selector_value}" no está visible en la página'
            else:
                # Determine if the element is a text input (get its value) or a regular element (get its text)
                element_value = ''
                try:
                    element_value = locator.input_value() or ''
                except PlaywrightError:
                    element_value = ''
                actual_content = element_value if element_value else (locator.text_content() or '')

                match_result, error_msg = evaluate(expected_value, actual_content, comparison_type)
                passed = match_result == 'MATCH'
                expected = f'Contenido {get_comparison_description(comparison_type).lower()}: {expected_value}'
                actual = f'Contenido actual: {actual_content}'
                if not passed:
                    error_message = error_msg
    else:
        raise ValidationError('Accion de automatizacion no soportada.')

    status = TestExecution.Result.PASSED if passed else TestExecution.Result.FAILED
    return {
        'status': status,
        'expected': expected,
        'actual': actual,
        'comparison_type': comparison_type,
        'log': f'[{"PASS" if passed else "FAIL"}] {step.name or step.get_action_type_display()}: {actual}',
        'error': error_message,
        'screenshot': None,
    }


def _run_browser_steps(test_case, steps):
    outcomes = []
    timeout_ms = max((step.timeout_seconds or 10) * 1000 for step in steps)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(ignore_https_errors=False)
                page = context.new_page()
                page.set_default_timeout(timeout_ms)
                page.route('**/*', _route_request)
                for step in steps:
                    step_started = timezone.now()
                    try:
                        outcome = _execute_browser_step(page, step, test_case, timeout_ms)
                    except (ValidationError, PlaywrightError, PlaywrightTimeoutError, OSError, RuntimeError) as exc:
                        outcome = {
                            'status': TestExecution.Result.ERROR,
                            'expected': _step_expected_label(step),
                            'actual': 'La accion no pudo ejecutarse.',
                            'comparison_type': step.comparison_type or AutomatedValidationRule.ComparisonType.EXACT,
                            'log': f'[ERROR] {step.name or step.get_action_type_display()}: {exc}',
                            'error': str(exc),
                            'screenshot': None,
                        }
                    outcome['started_at'] = step_started
                    outcome['finished_at'] = timezone.now()
                    if outcome['status'] == TestExecution.Result.FAILED:
                        try:
                            outcome['screenshot'] = page.screenshot(full_page=True)
                        except (PlaywrightError, RuntimeError):
                            outcome['screenshot'] = None
                    outcomes.append(outcome)
                    if outcome['status'] != TestExecution.Result.PASSED and step.is_critical:
                        break
            finally:
                browser.close()
    except (ValidationError, PlaywrightError, OSError, RuntimeError) as exc:
        outcomes.append({
            'status': TestExecution.Result.ERROR,
            'expected': _step_expected_label(steps[0]),
            'actual': 'No se pudo iniciar el navegador.',
            'comparison_type': AutomatedValidationRule.ComparisonType.EXACT,
            'log': f'[ERROR] Navegador: {exc}',
            'error': str(exc),
            'screenshot': None,
        })
    return outcomes


def run_automated_steps(test_case, user, steps):
    started_at = timezone.now()
    execution = TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        executed_at=started_at,
        started_at=started_at,
        execution_mode=TestExecution.ExecutionMode.AUTOMATED,
        result=TestExecution.Result.RUNNING,
        environment_url=steps[0].target_url if steps else '',
        environment='Ejecución automatizada por pasos',
    )

    if sync_playwright is None:
        executed_outcomes = [
            {
                'status': TestExecution.Result.BLOCKED,
                'expected': _step_expected_label(step),
                'actual': 'Playwright no esta instalado en el servidor.',
                'comparison_type': step.comparison_type or AutomatedValidationRule.ComparisonType.EXACT,
                'log': f'[BLOCKED] {step.name or step.get_action_type_display()}: Playwright no disponible.',
                'error': 'Playwright no esta instalado.',
                'screenshot': None,
            }
            for step in steps
        ]
    else:
        executed_outcomes = _run_browser_steps(test_case, steps)

    result_rows = []
    log_lines = []
    for index, step in enumerate(steps):
        if index < len(executed_outcomes):
            outcome = executed_outcomes[index]
            comment = outcome['error']
        else:
            outcome = {
                'status': TestExecution.Result.NOT_RUN,
                'expected': _step_expected_label(step),
                'actual': 'Paso no ejecutado por detencion en un paso crítico fallido.',
                'comparison_type': step.comparison_type or AutomatedValidationRule.ComparisonType.EXACT,
                'log': f'[NOT_RUN] {step.name or step.get_action_type_display()}: no ejecutado.',
                'error': '',
                'screenshot': None,
            }
            comment = 'Paso no ejecutado por detencion en un paso crítico fallido.'
        log_lines.append(outcome['log'])
        result = AutomatedExecutionResult.objects.create(
            test_execution=execution,
            validation_rule=step,
            status=outcome['status'],
            expected_behavior=outcome['expected'],
            actual_behavior=outcome['actual'],
            input_used=step.input_value,
            comparison_type=outcome.get('comparison_type', AutomatedValidationRule.ComparisonType.EXACT),
            technical_log=outcome['log'],
            error_message=outcome['error'],
            started_at=outcome.get('started_at'),
            finished_at=outcome.get('finished_at'),
        )
        if outcome.get('screenshot'):
            result.screenshot.save(
                f'execution-{execution.pk}-step-{step.pk}.png',
                ContentFile(outcome['screenshot']),
                save=True,
            )
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=step.step_number,
            action=step.name or step.get_action_type_display(),
            expected_result=outcome['expected'],
            obtained_result=outcome['actual'],
            status=outcome['status'],
            comment=comment,
            execution_log=outcome['log'],
            started_at=outcome.get('started_at'),
            finished_at=outcome.get('finished_at'),
        )
        result_rows.append(result)

    if not steps:
        log_lines.append('[BLOCKED] No existen pasos automatizados para este caso de prueba.')

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
    case_status = {
        TestExecution.Result.PASSED: test_case.Status.PASSED,
        TestExecution.Result.FAILED: test_case.Status.FAILED,
        TestExecution.Result.BLOCKED: test_case.Status.BLOCKED,
        TestExecution.Result.ERROR: test_case.Status.BLOCKED,
    }.get(execution.result, test_case.Status.PENDING)
    test_case.status = case_status
    test_case.save(update_fields=['status', 'updated_at'])

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
            'rule_count': len(steps),
        },
    )
    return execution

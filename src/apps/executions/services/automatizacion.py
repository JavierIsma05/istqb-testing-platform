import json

from django.db import transaction

from apps.executions.models import AutomatedValidationRule, TestExecution
from apps.executions.services.automated_runner import run_automated_execution
from apps.testcases.models import TestCase


def construir_prompt(caso_data, url_base):
    """Construye contexto para generación asistida; el código generado no se ejecuta."""
    return f"""Eres especialista en pruebas Playwright seguras.
Genera una propuesta de pasos declarativos para validar este caso, no código Python ejecutable.
Cada paso debe corresponder únicamente a: OPEN_URL, FILL_TEXT, CLICK, VERIFY o WAIT.

Código: {caso_data.get('codigo', '')}
Título: {caso_data.get('titulo', '')}
Precondiciones: {caso_data.get('precondiciones', '')}
Pasos: {caso_data.get('pasos', '')}
Resultado esperado: {caso_data.get('resultado_esperado', '')}
URL base permitida: {url_base}

Devuelve JSON con una lista de pasos y, para cada uno, action, selector, dato y esperado.
No incluyes comandos del sistema, subprocess, imports, archivos ni código arbitrario.
"""


def _safe_script_description(test_case):
    rules = test_case.automated_rules.filter(is_active=True).order_by('step_number', 'id')
    return json.dumps([
        {
            'paso': rule.step_number,
            'accion': rule.action_type,
            'selector': rule.selector_value,
            'dato': rule.input_value,
            'esperado': rule.expected_value or rule.target_url,
        }
        for rule in rules
    ], ensure_ascii=False, indent=2)


@transaction.atomic
def ejecutar_caso_automatizado(caso_id, usuario):
    """Ejecuta solo reglas declarativas existentes mediante el runner seguro de Playwright."""
    caso = TestCase.objects.select_related('requirement', 'test_plan__project').get(pk=caso_id)
    ejecucion = run_automated_execution(caso, usuario)
    errores = '\n'.join(
        result.error_message
        for result in ejecucion.automated_results.all()
        if result.error_message
    )
    ejecucion.script_generado = _safe_script_description(caso)
    ejecucion.salida_consola = ejecucion.technical_log or ''
    ejecucion.errores = errores
    ejecucion.save(update_fields=['script_generado', 'salida_consola', 'errores', 'updated_at'])
    pasos = [
        {
            'numero': result.validation_rule.step_number,
            'nombre': result.validation_rule.name,
            'estado': result.status,
            'esperado': result.expected_behavior,
            'obtenido': result.actual_behavior,
            'error': result.error_message,
        }
        for result in ejecucion.automated_results.select_related('validation_rule').order_by('validation_rule__step_number', 'id')
    ]
    return {
        'estado': ejecucion.result,
        'salida': ejecucion.salida_consola,
        'errores': ejecucion.errores,
        'id_ejecucion': ejecucion.pk,
        'pasos': pasos,
    }

import pytest
from unittest.mock import patch
from contextlib import contextmanager
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.defects.models import Defect
from apps.executions.forms import AutomatedStepForm, ExecutionResultForm
from apps.executions.models import AutomatedExecutionResult, AutomatedValidationRule, TestExecution as ExecutionModel
from apps.executions.services.automated_runner import (
    aggregate_automated_status,
    evaluate,
    run_automated_execution,
)
from apps.executions.services.review import recalculate_execution_from_steps
from apps.requirements.models import Requirement
from apps.projects.models import Project
from apps.testcases.models import TestCase as CaseModel
from apps.traceability.models import TraceabilityLink
from apps.users.models import User


def approve_requirement(test_case):
    test_case.requirement.status = Requirement.Status.APPROVED
    test_case.requirement.save(update_fields=['status'])
    return test_case


def evidence_file(name='captura.png'):
    return SimpleUploadedFile(
        name,
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR',
        content_type='image/png',
    )


def manual_payload(**overrides):
    data = {
        'execution_type': ExecutionModel.ExecutionType.NORMAL,
        'actual_result': 'Cumple',
        'planned_date': timezone.localdate().isoformat(),
        'test_data': 'usuario=estudiante@example.com',
        'environment': 'Chrome en Windows',
        'notes': 'Resultado registrado.',
        'evidence': evidence_file(),
    }
    data.update(overrides)
    return data


def step_payload(*statuses):
    data = {}
    for index, status in enumerate(statuses):
        data[f'step_actual_{index}'] = f'Resultado observado en el paso {index + 1}.'
        data[f'step_status_{index}'] = status
        data[f'step_comment_{index}'] = (
            'Justificacion obligatoria del resultado.'
            if status in {ExecutionModel.Result.FAILED, ExecutionModel.Result.BLOCKED}
            else ''
        )
    return data


@pytest.mark.django_db
def test_ejecucion_registra_resultado_y_responsable(execution, test_case, user):
    assert execution.test_case == test_case
    assert execution.executed_by == user
    assert execution.result == ExecutionModel.Result.PASSED
    assert 'TC-001 - Login exitoso' in str(execution)


def test_formulario_de_resultado_no_permite_estado_no_ejecutado():
    form = ExecutionResultForm(
        data={
            'result': ExecutionModel.Result.NOT_RUN,
            'notes': 'Pendiente',
        }
    )

    assert not form.is_valid()
    assert 'result' in form.errors


def test_formulario_de_resultado_exige_resultado_obtenido_para_aprobado():
    form = ExecutionResultForm(
        data={
            'result': ExecutionModel.Result.PASSED,
            'notes': 'Ejecución sin resultado obtenido.',
        }
    )

    assert not form.is_valid()
    assert 'actual_result' in form.errors


def test_formulario_de_resultado_rechaza_evidencia_no_permitida():
    evidence = SimpleUploadedFile('archivo.exe', b'not-allowed', content_type='application/octet-stream')
    form = ExecutionResultForm(
        data={
            'result': ExecutionModel.Result.PASSED,
            'actual_result': 'La ejecución registró un resultado válido.',
        },
        files={'evidence': evidence},
    )

    assert not form.is_valid()
    assert 'evidence' in form.errors


@pytest.mark.django_db
def test_vista_de_ejecucion_guarda_y_muestra_evidencia(client, test_case, user, tmp_path):
    approve_requirement(test_case)
    client.force_login(user)
    evidence = SimpleUploadedFile(
        'captura.png',
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR',
        content_type='image/png',
    )

    with override_settings(MEDIA_ROOT=tmp_path):
        response = client.post(
            f'{reverse("executions:index")}?case={test_case.id}',
            data={
                'execution_type': ExecutionModel.ExecutionType.NORMAL,
                'result': ExecutionModel.Result.PASSED,
                'actual_result': 'El sistema mostro la confirmacion esperada.',
                'test_data': 'usuario=estudiante@example.com',
                'environment': 'Chrome en Windows',
                'notes': 'Ejecución con evidencia.',
                'evidence': evidence,
                **step_payload(ExecutionModel.Result.PASSED),
            },
            follow=True,
        )

        execution = ExecutionModel.objects.get(test_case=test_case)

    assert response.status_code == 200
    assert execution.evidence.name.startswith('evidence/')
    assert execution.evidence.name.endswith('.png')
    assert execution.actual_result == 'El sistema mostro la confirmacion esperada.'
    assert execution.step_results == [
        {
            'number': 1,
            'action': 'Abrir login',
            'expected_result': test_case.expected_result,
            'actual_result': 'Resultado observado en el paso 1.',
            'status': ExecutionModel.Result.PASSED,
            'comment': '',
        }
    ]
    assert execution.result == ExecutionModel.Result.PASSED
    assert b'Evidencia adjunta' in response.content
    assert b'Ver archivo' in response.content


@pytest.mark.django_db
def test_vista_de_ejecucion_manual_persiste_resultado_global_sin_payload_de_pasos(client, test_case, user):
    approve_requirement(test_case)
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data=manual_payload(
            result=ExecutionModel.Result.PASSED,
            actual_result='Cumple',
            notes='Resultado global sin detalle por paso.',
            test_data='',
            environment='',
        ),
        follow=True,
    )

    assert response.status_code == 200
    execution = ExecutionModel.objects.get(test_case=test_case)
    assert execution.result == ExecutionModel.Result.PASSED
    assert execution.actual_result == 'Cumple'
    assert execution.step_executions.count() == len(execution.step_results) == 3


@pytest.mark.django_db
def test_vista_de_ejecucion_manual_persiste_resultados_por_paso(client, test_case, user):
    approve_requirement(test_case)
    client.force_login(user)
    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(result=ExecutionModel.Result.PASSED),
            **step_payload(ExecutionModel.Result.PASSED, ExecutionModel.Result.FAILED, ExecutionModel.Result.PASSED),
        },
    )

    execution = ExecutionModel.objects.get(test_case=test_case)
    assert response.status_code == 302
    assert execution.result == ExecutionModel.Result.FAILED
    assert len(execution.step_results) == 3
    assert execution.step_results[1]['status'] == ExecutionModel.Result.FAILED
    assert execution.step_executions.count() == 3
    assert execution.step_executions.filter(status=ExecutionModel.Result.FAILED).count() == 1


def test_formulario_de_resultado_bloquea_comentario_para_estudiante():
    form = ExecutionResultForm(user=User(role=User.Roles.STUDENT))

    assert form.fields['notes'].widget.attrs.get('disabled') is True


@pytest.mark.django_db
def test_ejecucion_fallida_crea_defecto_asociado(client, test_case, user):
    approve_requirement(test_case)
    test_case.test_data = 'usuario=estudiante@example.com'
    test_case.save(update_fields=['test_data'])
    test_case.test_plan.environment = 'Firefox'
    test_case.test_plan.save(update_fields=['environment'])
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                result=ExecutionModel.Result.FAILED,
                actual_result='No cumple',
                test_data='usuario=estudiante@example.com',
                environment='Firefox',
                notes='Se detectó una regresión funcional.',
            ),
            **step_payload(ExecutionModel.Result.FAILED, ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    execution = ExecutionModel.objects.get(test_case=test_case)
    defect = Defect.objects.get(execution=execution)

    assert response.status_code == 302
    assert defect.project == test_case.test_plan.project
    assert defect.reported_by == user
    assert execution.result == ExecutionModel.Result.FAILED
    assert 'Resultado obtenido:\nNo cumple' in defect.description
    assert 'Datos usados:\nusuario=estudiante@example.com' in defect.description
    assert 'Ambiente:\nFirefox' in defect.description
    assert AuditLog.objects.filter(action='CREATE', entity='TestExecution', entity_id=str(execution.pk)).exists()
    assert AuditLog.objects.filter(action='CREATE', entity='Defect', metadata__source='failed_execution').exists()


@pytest.mark.django_db
def test_prueba_de_confirmacion_aprobada_cierra_defecto(client, test_case, execution, user):
    approve_requirement(test_case)
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        test_case=test_case,
        execution=execution,
        code='DEF-CONF-001',
        title='Defecto corregido',
        description='Pendiente de confirmacion.',
        status=Defect.Status.RESOLVED,
        reported_by=user,
    )
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                execution_type=ExecutionModel.ExecutionType.CONFIRMATION,
                related_defect=defect.pk,
                planned_date=timezone.localdate().isoformat(),
                result=ExecutionModel.Result.PASSED,
                actual_result='Cumple',
            ),
            **step_payload(ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    defect.refresh_from_db()
    confirmation = ExecutionModel.objects.exclude(pk=execution.pk).get(test_case=test_case)

    assert response.status_code == 302
    assert confirmation.execution_type == ExecutionModel.ExecutionType.CONFIRMATION
    assert confirmation.related_defect == defect
    assert defect.status == Defect.Status.CLOSED
    assert defect.history.filter(change_reason='Actualizacion desde prueba de confirmacion').exists()


@pytest.mark.django_db
def test_prueba_de_confirmacion_fallida_no_duplica_defecto(client, test_case, execution, user):
    approve_requirement(test_case)
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        test_case=test_case,
        execution=execution,
        code='DEF-CONF-002',
        title='Defecto no corregido',
        description='Pendiente de confirmacion.',
        status=Defect.Status.RESOLVED,
        reported_by=user,
    )
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                execution_type=ExecutionModel.ExecutionType.CONFIRMATION,
                related_defect=defect.pk,
                planned_date=timezone.localdate().isoformat(),
                result=ExecutionModel.Result.FAILED,
                actual_result='No cumple',
            ),
            **step_payload(ExecutionModel.Result.FAILED, ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    defect.refresh_from_db()

    assert response.status_code == 302
    assert defect.status == Defect.Status.REOPENED
    assert Defect.objects.filter(project=test_case.test_plan.project).count() == 1


@pytest.mark.django_db
def test_calendario_de_ejecucion_muestra_actividades_sugeridas(client, test_case, user):
    client.force_login(user)

    response = client.get(reverse('executions:calendar'))

    content = response.content.decode()

    assert response.status_code == 200
    assert 'Calendario e historial' in content
    assert test_case.code in content


@pytest.mark.django_db
def test_calendario_muestra_fecha_real_de_ejecucion(client, execution, test_case, user):
    execution.executed_at = timezone.now()
    execution.save(update_fields=['executed_at'])
    client.force_login(user)

    response = client.get(reverse('executions:calendar'))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Calendario e historial' in content
    assert test_case.code in content
    assert execution.get_result_display() in content
    assert timezone.localtime(execution.executed_at).strftime('%Y') in content


@pytest.mark.django_db
def test_docente_revisa_ultima_ejecucion(client, execution, test_case):
    teacher = User.objects.create_user(
        email='teacher@example.com',
        password='StrongPass123',
        role=User.Roles.TEACHER,
    )
    test_case.test_plan.project.members.add(teacher)
    client.force_login(teacher)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_id': execution.pk,
            'review_status': ExecutionModel.ReviewStatus.VALIDATED,
            'review_notes': 'Evidencia suficiente.',
        },
    )

    execution.refresh_from_db()

    assert response.status_code == 302
    assert execution.review_status == ExecutionModel.ReviewStatus.VALIDATED
    assert execution.reviewed_by == teacher
    assert execution.review_notes == 'Evidencia suficiente.'
    assert AuditLog.objects.filter(action='REVIEW', entity='TestExecution', entity_id=str(execution.pk)).exists()


@pytest.mark.django_db
def test_vista_de_ejecucion_elimina_ejecucion_del_historial(client, execution, test_case, user):
    client.force_login(user)

    response = client.post(reverse('executions:delete', args=[execution.pk]))

    assert response.status_code == 302
    assert response.url == f'{reverse("executions:index")}?case={test_case.id}'
    assert not ExecutionModel.objects.filter(pk=execution.pk).exists()
    test_case.refresh_from_db()
    assert test_case.status == test_case.Status.PENDING
    assert AuditLog.objects.filter(action='DELETE', entity='TestExecution', entity_id=str(execution.pk)).exists()


@pytest.mark.django_db
def test_historial_separa_ejecuciones_manuales_y_automatizadas(client, test_case, execution, user):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Titulo visible',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        target_url='http://localhost:8000/login/',
        selector_value='h2',
        expected_value='Iniciar Sesión',
    )
    automated_execution = ExecutionModel.objects.create(
        test_case=test_case,
        execution_mode=ExecutionModel.ExecutionMode.AUTOMATED,
        execution_type=ExecutionModel.ExecutionType.NORMAL,
        executed_by=user,
        result=ExecutionModel.Result.PASSED,
        actual_result='Texto visible: Iniciar Sesión',
        technical_log='[PASS] Titulo visible',
    )
    AutomatedExecutionResult.objects.create(
        test_execution=automated_execution,
        validation_rule=rule,
        status=ExecutionModel.Result.PASSED,
        expected_behavior='Debe mostrar Iniciar Sesión',
        actual_behavior='Texto visible',
    )
    client.force_login(user)

    response = client.get(reverse('executions:history', args=[test_case.pk]))

    assert response.status_code == 200
    assert response.context['manual_history'][0]['execution'] == execution
    assert response.context['automated_history'][0]['execution'] == automated_execution
    assert b'Historial manual' in response.content
    assert b'Historial automatizado' in response.content
    assert response.context['test_cases'].filter(pk=test_case.pk).exists()
    assert test_case.code.encode() in response.content


@pytest.mark.django_db
def test_vista_no_elimina_ejecucion_automatizada_revisada_del_historial(client, test_case, user):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Titulo de login visible',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        target_url='http://localhost:8000/login/',
        selector_value='h2',
        expected_value='Iniciar Sesión',
    )
    execution = ExecutionModel.objects.create(
        test_case=test_case,
        execution_mode=ExecutionModel.ExecutionMode.AUTOMATED,
        execution_type=ExecutionModel.ExecutionType.NORMAL,
        executed_by=user,
        result=ExecutionModel.Result.PASSED,
        actual_result='Texto visible: Iniciar Sesión',
        technical_log='[PASS] Titulo de login visible',
        review_status=ExecutionModel.ReviewStatus.VALIDATED,
    )
    result = AutomatedExecutionResult.objects.create(
        test_execution=execution,
        validation_rule=rule,
        status=ExecutionModel.Result.PASSED,
        expected_behavior='Debe mostrar Iniciar Sesión',
        actual_behavior='Texto visible',
    )
    client.force_login(user)

    response = client.post(reverse('executions:delete', args=[execution.pk]), follow=True)

    assert response.status_code == 200
    assert ExecutionModel.objects.filter(pk=execution.pk).exists()
    assert AutomatedExecutionResult.objects.filter(pk=result.pk).exists()
    assert AutomatedValidationRule.objects.filter(pk=rule.pk).exists()
    assert 'Una ejecución revisada no puede eliminarse.'.encode() in response.content


@pytest.mark.django_db
def test_vista_elimina_regla_automatizada_sin_historial(client, test_case, user):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Titulo de login visible',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        target_url='http://localhost:8000/login/',
        selector_value='h2',
        expected_value='Iniciar Sesión',
    )
    client.force_login(user)

    response = client.post(reverse('executions:rule-delete', args=[rule.pk]), follow=True)

    assert response.status_code == 200
    assert not AutomatedValidationRule.objects.filter(pk=rule.pk).exists()
    assert b'Paso automatizado eliminado.' in response.content


@pytest.mark.django_db
def test_vista_oculta_regla_automatizada_con_historial(client, test_case, execution, user):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Titulo de login visible',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        target_url='http://localhost:8000/login/',
        selector_value='h2',
        expected_value='Iniciar Sesión',
    )
    AutomatedExecutionResult.objects.create(
        test_execution=execution,
        validation_rule=rule,
        status=ExecutionModel.Result.PASSED,
        expected_behavior='Debe mostrar Iniciar Sesión',
        actual_behavior='Texto visible',
    )
    client.force_login(user)

    response = client.post(reverse('executions:rule-delete', args=[rule.pk]), follow=True)
    rule.refresh_from_db()

    assert response.status_code == 200
    assert rule.is_active is False
    assert b'El paso automatizado tiene historial y fue desactivado en lugar de eliminarse.' in response.content


def test_agregacion_automatizada_prioriza_fallo_y_error():
    assert aggregate_automated_status([
        ExecutionModel.Result.PASSED,
        ExecutionModel.Result.ERROR,
    ]) == ExecutionModel.Result.ERROR
    assert aggregate_automated_status([
        ExecutionModel.Result.ERROR,
        ExecutionModel.Result.FAILED,
    ]) == ExecutionModel.Result.FAILED


@pytest.mark.playwright
@pytest.mark.django_db(transaction=True)
def test_playwright_valida_texto_visible_en_servidor_django(live_server, settings, test_case, user):
    settings.AUTOMATION_ALLOWED_HOSTS = ('localhost', '127.0.0.1')
    AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Abrir login',
        action_type=AutomatedValidationRule.ActionType.OPEN_URL,
        target_url=f'{live_server.url}/login/',
        timeout_seconds=10,
    )
    AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=2,
        name='Pantalla de login visible',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        selector_value='h2',
        expected_value='Iniciar Sesión',
        timeout_seconds=10,
    )

    execution = run_automated_execution(test_case, user)

    assert execution.result == ExecutionModel.Result.PASSED
    result = AutomatedExecutionResult.objects.get(
        test_execution=execution,
        validation_rule__name='Pantalla de login visible',
    )
    assert result.status == ExecutionModel.Result.PASSED
    assert '[PASS]' in execution.technical_log


def test_evaluate_deterministico_devuelve_match_o_no_match():
    match, _ = evaluate('abc', 'abc')
    assert match == 'MATCH'
    match, _ = evaluate('abc', 'ABC')
    assert match == 'NO_MATCH'
    match, _ = evaluate('  valor ', 'valor')
    assert match == 'MATCH'
    match, _ = evaluate('http://x/', 'http://x')
    assert match == 'NO_MATCH'
    match, _ = evaluate(None, '')
    assert match == 'MATCH'
    match, _ = evaluate(200, '200')
    assert match == 'MATCH'


@pytest.mark.django_db
def test_formulario_de_paso_exige_url_autorizada(test_case, settings):
    settings.AUTOMATION_ALLOWED_HOSTS = ('localhost',)
    form = AutomatedStepForm(
        data={
            'step_number': 1,
            'action_type': AutomatedValidationRule.ActionType.OPEN_URL,
            'target_url': 'https://ejemplo-inseguro.com/',
            'timeout_seconds': 5,
            'is_critical': True,
        },
        test_case=test_case,
    )
    assert not form.is_valid()
    assert 'target_url' in form.errors


@pytest.mark.django_db
def test_formulario_de_paso_exige_elemento_y_dato_para_escribir(test_case):
    form = AutomatedStepForm(
        data={
            'step_number': 2,
            'action_type': AutomatedValidationRule.ActionType.FILL_TEXT,
            'timeout_seconds': 5,
            'is_critical': True,
        },
        test_case=test_case,
    )
    assert not form.is_valid()
    assert 'selector_value' in form.errors
    assert 'input_value' in form.errors


@pytest.mark.django_db
def test_formulario_de_paso_genera_nombre_y_guardado(test_case):
    form = AutomatedStepForm(
        data={
            'step_number': 1,
            'action_type': AutomatedValidationRule.ActionType.CLICK,
            'selector_value': '.btn-login',
            'timeout_seconds': 5,
            'is_critical': True,
        },
        test_case=test_case,
    )
    assert form.is_valid(), form.errors
    rule = form.save(commit=False)
    rule.test_case = test_case
    rule.requirement = test_case.requirement
    rule.save()

    rule.refresh_from_db()
    assert rule.action_type == AutomatedValidationRule.ActionType.CLICK
    assert rule.is_critical is True
    assert rule.name == 'Paso 1: Click'


def _fake_playwright_cm():
    class FakeBrowser:
        def new_context(self, **kwargs):
            return FakeContext()

        def close(self):
            pass

    class FakeContext:
        def new_page(self):
            return FakePage()

    class FakePage:
        def route(self, *args, **kwargs):
            pass

        def set_default_timeout(self, *args, **kwargs):
            pass

        def screenshot(self, *args, **kwargs):
            return b'\x89PNG\r\n\x1a\n' + b'fake-png'

    class FakeChromium:
        def launch(self, **kwargs):
            return FakeBrowser()

    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()

    @contextmanager
    def _cm():
        yield FakePlaywright()

    return _cm


def _step_outcome(status, index, error=''):
    return {
        'status': status,
        'expected': f'Esperado {index}',
        'actual': f'Obtenido {index}',
        'log': f'[{status}] paso {index}',
        'error': error,
        'screenshot': None,
    }


@pytest.mark.django_db
def test_ejecucion_por_pasos_detiene_en_paso_critico_y_marca_no_ejecutados(
    test_case, user, tmp_path
):
    steps_data = [
        AutomatedValidationRule.objects.create(
            test_case=test_case,
            requirement=test_case.requirement,
            step_number=1,
            name='Abrir URL',
            action_type=AutomatedValidationRule.ActionType.OPEN_URL,
            target_url='http://localhost:8000/',
            is_critical=True,
        ),
        AutomatedValidationRule.objects.create(
            test_case=test_case,
            requirement=test_case.requirement,
            step_number=2,
            name='Verificar texto',
            action_type=AutomatedValidationRule.ActionType.VERIFY,
            selector_value='h2',
            expected_value='Bienvenido',
            is_critical=True,
        ),
        AutomatedValidationRule.objects.create(
            test_case=test_case,
            requirement=test_case.requirement,
            step_number=3,
            name='Hacer clic',
            action_type=AutomatedValidationRule.ActionType.CLICK,
            selector_value='.btn',
            is_critical=True,
        ),
    ]
    outcomes = [
        _step_outcome(ExecutionModel.Result.PASSED, 1),
        _step_outcome(ExecutionModel.Result.FAILED, 2),
        _step_outcome(ExecutionModel.Result.PASSED, 3),
    ]
    with override_settings(MEDIA_ROOT=tmp_path), patch(
        'apps.executions.services.automated_runner.sync_playwright', _fake_playwright_cm()
    ), patch(
        'apps.executions.services.automated_runner._execute_browser_step',
        side_effect=outcomes,
    ):
        execution = run_automated_execution(test_case, user)

    results = list(execution.automated_results.order_by('id'))
    assert execution.execution_mode == ExecutionModel.ExecutionMode.AUTOMATED
    assert execution.result == ExecutionModel.Result.FAILED
    assert [item.status for item in results] == [
        ExecutionModel.Result.PASSED,
        ExecutionModel.Result.FAILED,
        ExecutionModel.Result.NOT_RUN,
    ]
    assert Defect.objects.filter(execution=execution).exists()
    test_case.refresh_from_db()
    assert test_case.status == test_case.Status.FAILED


@pytest.mark.django_db
def test_ejecucion_por_pasos_continua_si_paso_no_critico_falla(test_case, user, tmp_path):
    AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Abrir URL',
        action_type=AutomatedValidationRule.ActionType.OPEN_URL,
        target_url='http://localhost:8000/',
        is_critical=True,
    )
    AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=2,
        name='Verificar opcional',
        action_type=AutomatedValidationRule.ActionType.VERIFY,
        selector_value='h2',
        expected_value='Opcional',
        is_critical=False,
    )
    outcomes = [
        _step_outcome(ExecutionModel.Result.PASSED, 1),
        _step_outcome(ExecutionModel.Result.FAILED, 2),
        _step_outcome(ExecutionModel.Result.PASSED, 3),
    ]
    with override_settings(MEDIA_ROOT=tmp_path), patch(
        'apps.executions.services.automated_runner.sync_playwright', _fake_playwright_cm()
    ), patch(
        'apps.executions.services.automated_runner._execute_browser_step',
        side_effect=outcomes[:2],
    ):
        execution = run_automated_execution(test_case, user)

    results = list(execution.automated_results.order_by('id'))
    assert [item.status for item in results] == [
        ExecutionModel.Result.PASSED,
        ExecutionModel.Result.FAILED,
    ]
    assert execution.result == ExecutionModel.Result.FAILED


@pytest.mark.django_db
def test_vista_crea_paso_automatizado(client, test_case, user):
    client.force_login(user)
    response = client.post(
        reverse('executions:rule-create', args=[test_case.pk]),
        {
            'name': 'Buscar usuario',
            'step_number': 1,
            'action_type': AutomatedValidationRule.ActionType.FILL_TEXT,
            'selector_value': '#usuario',
            'input_value': 'ana',
            'timeout_seconds': 5,
            'is_critical': True,
        },
        follow=True,
    )
    rule = AutomatedValidationRule.objects.get(test_case=test_case)
    assert response.status_code == 200
    assert rule.action_type == AutomatedValidationRule.ActionType.FILL_TEXT
    assert rule.selector_value == '#usuario'
    assert b'Paso automatizado registrado correctamente.' in response.content

    client.post(
        reverse('executions:rule-create', args=[test_case.pk]),
        {
            'name': '',
            'step_number': 99,
            'action_type': AutomatedValidationRule.ActionType.CLICK,
            'selector_value': '.btn-login',
            'is_critical': True,
        },
    )
    second_rule = AutomatedValidationRule.objects.exclude(pk=rule.pk).get(test_case=test_case)
    assert second_rule.step_number == 2


@pytest.mark.django_db
def test_endpoint_json_ejecuta_caso_automatizado(client, test_case, user):
    AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Abrir URL',
        action_type=AutomatedValidationRule.ActionType.OPEN_URL,
        target_url='http://localhost:8000/',
    )
    client.force_login(user)
    response = client.post(f'/casos/{test_case.pk}/ejecutar-automatizado/')

    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['id_ejecucion']
    assert data['pasos'][0]['numero'] == 1


@pytest.mark.django_db
def test_vista_de_ejecucion_muestra_pasos_automatizados(client, test_case, user):
    test_case.execution_type = test_case.ExecutionType.AUTOMATED
    test_case.save(update_fields=['execution_type'])
    AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Abrir URL',
        action_type=AutomatedValidationRule.ActionType.OPEN_URL,
        target_url='http://localhost:8000/',
        is_critical=True,
    )
    client.force_login(user)
    response = client.get(reverse('executions:index'), {'case': test_case.pk})

    assert response.status_code == 200
    assert b'Abrir URL' in response.content
    assert b'Automatizada' in response.content


@pytest.mark.django_db
def test_ejecucion_manual_bloqueada_con_requisito_pendiente(client, test_case, user):
    client.force_login(user)
    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_type': ExecutionModel.ExecutionType.NORMAL,
            'result': ExecutionModel.Result.PASSED,
            'actual_result': 'Resultado.',
        },
        follow=True,
    )

    assert not ExecutionModel.objects.filter(test_case=test_case).exists()
    assert 'ningún requisito aprobado'.encode() in response.content


@pytest.mark.django_db
def test_ejecucion_manual_bloqueada_con_requisito_en_revision(client, test_case, user):
    test_case.requirement.status = Requirement.Status.REVIEW
    test_case.requirement.save(update_fields=['status'])
    client.force_login(user)
    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_type': ExecutionModel.ExecutionType.NORMAL,
            'result': ExecutionModel.Result.PASSED,
            'actual_result': 'Resultado.',
        },
        follow=True,
    )

    assert not ExecutionModel.objects.filter(test_case=test_case).exists()
    assert 'ningún requisito aprobado'.encode() in response.content


@pytest.mark.django_db
def test_ejecucion_permitida_cuando_al_menos_un_requisito_aprobado(
    client, test_case, project, user
):
    related = Requirement.objects.create(
        project=project,
        code='REQ-APPROVED',
        title='Requisito aprobado',
        description='Requisito aprobado para permitir ejecucion.',
        status=Requirement.Status.APPROVED,
        created_by=user,
    )
    TraceabilityLink.objects.create(requirement=related, test_case=test_case)
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                result=ExecutionModel.Result.PASSED,
                actual_result='Cumple',
            ),
            **step_payload(ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    execution = ExecutionModel.objects.get(test_case=test_case)
    assert response.status_code == 302
    assert execution.result == ExecutionModel.Result.PASSED


@pytest.mark.django_db
def test_ejecucion_desbloqueada_al_aprobar_requisito(client, test_case, user):
    client.force_login(user)
    assert not test_case.has_approved_requirement

    test_case.requirement.status = Requirement.Status.APPROVED
    test_case.requirement.save(update_fields=['status'])
    test_case.refresh_from_db()

    assert test_case.has_approved_requirement is True
    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                result=ExecutionModel.Result.PASSED,
                actual_result='Cumple',
            ),
            **step_payload(ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    assert ExecutionModel.objects.filter(test_case=test_case).exists()
    assert response.status_code == 302


@pytest.mark.django_db
def test_ejecucion_automatizada_bloqueada_sin_requisito_aprobado(client, test_case, user):
    client.force_login(user)
    response = client.post(
        reverse('executions:run-automated', args=[test_case.pk]),
        follow=True,
    )

    assert not ExecutionModel.objects.filter(test_case=test_case).exists()
    assert 'ningún requisito aprobado'.encode() in response.content


@pytest.mark.django_db
def test_api_docente_no_expone_proyectos_ajenos(client, project, user):
    teacher = User.objects.create_user(
        email='teacher-api@example.com',
        password='StrongPass123',
        role=User.Roles.TEACHER,
    )
    foreign_project = Project.objects.create(
        code='PRJ-FOREIGN',
        name='Proyecto fuera del alcance',
        created_by=user,
    )
    client.force_login(teacher)

    response = client.get(reverse('executions:api-students', args=[foreign_project.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_api_docente_consulta_solo_proyecto_visible(client, project):
    teacher = User.objects.create_user(
        email='teacher-visible@example.com',
        password='StrongPass123',
        role=User.Roles.TEACHER,
    )
    project.members.add(teacher)
    client.force_login(teacher)

    response = client.get(reverse('executions:api-students', args=[project.pk]))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_detalle_de_ejecucion_muestra_pasoso_evidencia_y_defectos(client, execution, test_case, user):
    from apps.executions.models import TestStepExecution

    step = TestStepExecution.objects.create(
        test_execution=execution,
        step_number=1,
        action='Abrir login',
        expected_result='Se muestra el formulario',
        obtained_result='Se muestra el formulario',
        status=ExecutionModel.Result.PASSED,
    )
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        test_case=test_case,
        execution=execution,
        code='DEF-DETAIL-01',
        title='Defecto visible',
        description='Detalle del defecto',
        reported_by=user,
    )
    client.force_login(user)

    response = client.get(reverse('executions:detail', args=[execution.pk]))

    assert response.status_code == 200
    assert response.context['step_executions'][0].pk == step.pk
    assert defect.title in response.content.decode()
    assert reverse('executions:step-evidence', args=[step.pk]) in response.content.decode()


@pytest.mark.django_db
def test_usuario_que_ejecuto_puede_guardar_evidencia_por_paso(client, execution, test_case, user):
    from apps.executions.models import TestStepExecution

    step = TestStepExecution.objects.create(
        test_execution=execution,
        step_number=1,
        action='Enviar formulario',
        expected_result='Se procesa',
        status=ExecutionModel.Result.FAILED,
    )
    client.force_login(user)

    response = client.post(
        reverse('executions:step-evidence', args=[step.pk]),
        {'evidence_file': evidence_file('paso-1.png')},
    )

    step.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse('executions:detail', args=[execution.pk])
    assert step.evidence_file.name.startswith('step_evidence/paso-1')
    assert step.evidence_file.name.endswith('.png')


@pytest.mark.django_db
def test_no_se_puede_cambiar_evidencia_de_ejecucion_revisada(client, execution, user):
    from apps.executions.models import TestStepExecution

    execution.review_status = ExecutionModel.ReviewStatus.VALIDATED
    execution.save(update_fields=['review_status'])
    step = TestStepExecution.objects.create(
        test_execution=execution,
        step_number=1,
        action='Paso revisado',
        expected_result='OK',
        status=ExecutionModel.Result.PASSED,
    )
    client.force_login(user)

    client.post(reverse('executions:step-evidence', args=[step.pk]), {'evidence_file': evidence_file()})

    step.refresh_from_db()
    assert not step.evidence_file


@pytest.mark.django_db
def test_docente_puede_revisar_ejecucion_desde_detalle(client, execution, test_case, user):
    from apps.executions.models import TestStepExecution

    teacher = User.objects.create_user(email='reviewer@example.com', password='StrongPass123', role=User.Roles.TEACHER)
    test_case.test_plan.project.members.add(teacher)
    TestStepExecution.objects.create(
        test_execution=execution,
        step_number=1,
        action='Validar pantalla',
        expected_result='La pantalla aparece',
        obtained_result='La pantalla aparece',
        status=ExecutionModel.Result.PASSED,
    )
    client.force_login(teacher)

    response = client.post(
        reverse('executions:detail-review', args=[execution.pk]),
        {'review_status': ExecutionModel.ReviewStatus.VALIDATED, 'review_notes': 'Evidencia suficiente.'},
    )

    execution.refresh_from_db()
    assert response.status_code == 302
    assert execution.review_status == ExecutionModel.ReviewStatus.VALIDATED
    assert execution.reviewed_by == teacher
    assert execution.review_notes == 'Evidencia suficiente.'


@pytest.mark.django_db
def test_docente_puede_revisar_un_paso_desde_detalle(client, execution, test_case, user):
    from apps.executions.models import TestStepExecution

    teacher = User.objects.create_user(email='step-reviewer@example.com', password='StrongPass123', role=User.Roles.TEACHER)
    test_case.test_plan.project.members.add(teacher)
    step = TestStepExecution.objects.create(
        test_execution=execution,
        step_number=1,
        action='Enviar datos',
        expected_result='Se acepta la entrada',
        obtained_result='Se muestra error',
        status=ExecutionModel.Result.FAILED,
    )
    client.force_login(teacher)

    response = client.post(
        reverse('executions:step-review', args=[step.pk]),
        {'status': ExecutionModel.Result.FAILED, 'comment': 'El resultado no coincide con lo esperado.'},
    )

    step.refresh_from_db()
    assert response.status_code == 302
    assert step.comment == 'El resultado no coincide con lo esperado.'
    assert step.status == ExecutionModel.Result.FAILED


@pytest.mark.django_db
def test_revision_de_paso_recalcula_resultado_porcentaje_y_estado_del_caso(client, execution, test_case, user):
    from apps.executions.models import TestStepExecution

    teacher = User.objects.create_user(email='recalc-reviewer@example.com', password='StrongPass123', role=User.Roles.TEACHER)
    test_case.test_plan.project.members.add(teacher)
    steps = [
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=number,
            action=f'Paso {number}',
            expected_result='OK',
            obtained_result='OK',
            status=ExecutionModel.Result.NOT_RUN,
        )
        for number in range(1, 4)
    ]
    client.force_login(teacher)

    for step in steps:
        response = client.post(
            reverse('executions:step-review', args=[step.pk]),
            {'status': ExecutionModel.Result.PASSED, 'comment': 'Validado por el docente.'},
        )
        assert response.status_code == 302

    execution.refresh_from_db()
    test_case.refresh_from_db()
    assert execution.result == ExecutionModel.Result.PASSED
    assert execution.approval_percentage == 100
    assert test_case.status == test_case.Status.PASSED


@pytest.mark.django_db
def test_recalculo_marca_fallo_y_calcula_porcentaje_parcial(execution, test_case, user):
    from apps.executions.models import TestStepExecution

    steps = [
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=1,
            action='Paso aprobado',
            expected_result='OK',
            status=ExecutionModel.Result.PASSED,
        ),
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=2,
            action='Paso fallido',
            expected_result='OK',
            status=ExecutionModel.Result.FAILED,
        ),
    ]

    recalculate_execution_from_steps(execution)
    execution.refresh_from_db()
    test_case.refresh_from_db()
    assert execution.result == ExecutionModel.Result.FAILED
    assert execution.approval_percentage == 50
    assert test_case.status == test_case.Status.FAILED


@pytest.mark.django_db
def test_usuario_no_puede_ver_ni_eliminar_ejecucion_de_proyecto_ajeno(client, user):
    from apps.requirements.models import Requirement
    from apps.testplans.models import TestPlan

    other_user = User.objects.create_user(
        email='foreign-execution@example.com',
        password='StrongPass123',
    )
    foreign_project = Project.objects.create(
        code='PRJ-FOREIGN-EXEC',
        name='Proyecto ajeno para ejecucion',
        created_by=other_user,
    )
    foreign_plan = TestPlan.objects.create(
        project=foreign_project,
        name='Plan ajeno',
        objective='Privado.',
        created_by=other_user,
    )
    foreign_requirement = Requirement.objects.create(
        project=foreign_project,
        code='REQ-EXEC-999',
        title='Requisito privado',
        description='Privado.',
        status=Requirement.Status.APPROVED,
        created_by=other_user,
    )
    foreign_case = CaseModel.objects.create(
        test_plan=foreign_plan,
        requirement=foreign_requirement,
        code='TC-EXEC-999',
        title='Caso privado',
        steps='Paso 1',
        expected_result='OK',
        created_by=other_user,
    )
    foreign_execution = ExecutionModel.objects.create(
        test_case=foreign_case,
        executed_by=other_user,
        result=ExecutionModel.Result.PASSED,
    )

    client.force_login(user)
    response = client.get(reverse('executions:detail', args=[foreign_execution.pk]))
    assert response.status_code == 404

    response = client.post(reverse('executions:delete', args=[foreign_execution.pk]))
    assert response.status_code == 404
    assert ExecutionModel.objects.filter(pk=foreign_execution.pk).exists()


@pytest.mark.django_db
def test_ejecucion_de_regresion_puede_repetir_caso_y_no_duplica_defecto(client, test_case, execution, user):
    approve_requirement(test_case)
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        test_case=test_case,
        execution=execution,
        code='DEF-REG-001',
        title='Defecto corregido',
        description='Motiva una regresion.',
        status=Defect.Status.RESOLVED,
        reported_by=user,
    )
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                execution_type=ExecutionModel.ExecutionType.REGRESSION,
                related_defect=defect.pk,
                result=ExecutionModel.Result.PASSED,
                actual_result='Cumple',
            ),
            **step_payload(ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    regression = ExecutionModel.objects.get(
        test_case=test_case,
        execution_type=ExecutionModel.ExecutionType.REGRESSION,
    )
    assert response.status_code == 302
    assert regression.related_defect == defect
    assert regression.result == ExecutionModel.Result.PASSED
    assert Defect.objects.filter(project=test_case.test_plan.project).count() == 1


@pytest.mark.django_db
def test_regresion_fallida_crea_defecto_trazable(client, test_case, user):
    approve_requirement(test_case)
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            **manual_payload(
                execution_type=ExecutionModel.ExecutionType.REGRESSION,
                result=ExecutionModel.Result.FAILED,
                actual_result='No cumple',
            ),
            **step_payload(ExecutionModel.Result.FAILED, ExecutionModel.Result.PASSED, ExecutionModel.Result.PASSED),
        },
    )

    regression = ExecutionModel.objects.get(
        test_case=test_case,
        execution_type=ExecutionModel.ExecutionType.REGRESSION,
    )
    defect = Defect.objects.get(execution=regression)
    assert response.status_code == 302
    assert regression.result == ExecutionModel.Result.FAILED
    assert defect.test_case == test_case

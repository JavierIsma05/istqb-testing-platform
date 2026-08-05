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
from apps.requirements.models import Requirement
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
            },
            follow=True,
        )

        execution = ExecutionModel.objects.get(test_case=test_case)

    assert response.status_code == 200
    assert execution.evidence.name.startswith('evidence/')
    assert execution.evidence.name.endswith('.png')
    assert execution.actual_result == 'El sistema mostro la confirmacion esperada.'
    assert execution.step_results == []
    assert execution.result == ExecutionModel.Result.PASSED
    assert b'Evidencia adjunta' in response.content
    assert b'Ver archivo' in response.content


@pytest.mark.django_db
def test_vista_de_ejecucion_manual_guarda_resultado_global_sin_pasos(client, test_case, user):
    approve_requirement(test_case)
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data=manual_payload(
            result=ExecutionModel.Result.PASSED,
            actual_result='Cumple',
            notes='Resultado registrado de forma global.',
            test_data='',
            environment='',
        ),
    )

    execution = ExecutionModel.objects.get(test_case=test_case)

    assert response.status_code == 302
    assert execution.result == ExecutionModel.Result.PASSED
    assert execution.actual_result == 'Cumple'
    assert execution.notes == 'Resultado registrado de forma global.'
    assert execution.step_results == []
    assert execution.test_data == ''
    assert execution.environment == ''


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
        data=manual_payload(
            result=ExecutionModel.Result.FAILED,
            actual_result='No cumple',
            test_data='usuario=estudiante@example.com',
            environment='Firefox',
            notes='Se detectó una regresión funcional.',
        ),
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
        data=manual_payload(
            execution_type=ExecutionModel.ExecutionType.CONFIRMATION,
            related_defect=defect.pk,
            planned_date=timezone.localdate().isoformat(),
            result=ExecutionModel.Result.PASSED,
            actual_result='Cumple',
            **step_payload(
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
            ),
        ),
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
        data=manual_payload(
            execution_type=ExecutionModel.ExecutionType.CONFIRMATION,
            related_defect=defect.pk,
            planned_date=timezone.localdate().isoformat(),
            result=ExecutionModel.Result.FAILED,
            actual_result='No cumple',
            **step_payload(
                ExecutionModel.Result.FAILED,
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
            ),
        ),
    )

    defect.refresh_from_db()

    assert response.status_code == 302
    assert defect.status == Defect.Status.IN_PROGRESS
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
def test_vista_elimina_ejecucion_automatizada_revisada_del_historial(client, test_case, user):
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
    assert not ExecutionModel.objects.filter(pk=execution.pk).exists()
    assert not AutomatedExecutionResult.objects.filter(pk=result.pk).exists()
    assert AutomatedValidationRule.objects.filter(pk=rule.pk).exists()
    assert 'Ejecución eliminada correctamente.'.encode() in response.content


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
        data=manual_payload(
            result=ExecutionModel.Result.PASSED,
            actual_result='Cumple',
        ),
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
        data=manual_payload(
            result=ExecutionModel.Result.PASSED,
            actual_result='Cumple',
        ),
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
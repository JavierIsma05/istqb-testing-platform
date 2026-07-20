import pytest
from unittest.mock import Mock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.defects.models import Defect
from apps.executions.forms import AutomatedValidationRuleForm, ExecutionResultForm
from apps.executions.models import AutomatedExecutionResult, AutomatedValidationRule, TestExecution as ExecutionModel
from apps.executions.services.automated_runner import aggregate_automated_status, execute_rule
from apps.users.models import User


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
                **step_payload(
                    ExecutionModel.Result.PASSED,
                    ExecutionModel.Result.PASSED,
                    ExecutionModel.Result.PASSED,
                ),
            },
            follow=True,
        )

        execution = ExecutionModel.objects.get(test_case=test_case)

    assert response.status_code == 200
    assert execution.evidence.name.startswith('evidence/')
    assert execution.evidence.name.endswith('.png')
    assert execution.actual_result == 'El sistema mostro la confirmacion esperada.'
    assert len(execution.step_results) == 3
    assert execution.step_results[0]['status'] == ExecutionModel.Result.PASSED
    assert execution.result == ExecutionModel.Result.PASSED
    assert b'Evidencia adjunta' in response.content
    assert b'Ver archivo' in response.content


@pytest.mark.django_db
def test_vista_de_ejecucion_manual_genera_resumen_desde_pasos(client, test_case, user):
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_type': ExecutionModel.ExecutionType.NORMAL,
            'result': ExecutionModel.Result.PASSED,
            **step_payload(
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
            ),
        },
    )

    execution = ExecutionModel.objects.get(test_case=test_case)

    assert response.status_code == 302
    assert execution.result == ExecutionModel.Result.PASSED
    assert execution.actual_result == (
        'Paso 1 [PASSED]: Resultado observado en el paso 1.\n'
        'Paso 2 [PASSED]: Resultado observado en el paso 2.\n'
        'Paso 3 [PASSED]: Resultado observado en el paso 3.'
    )
    assert execution.test_data == ''
    assert execution.environment == ''
    assert execution.notes == ''


@pytest.mark.django_db
def test_ejecucion_fallida_crea_defecto_asociado(client, test_case, user):
    test_case.test_data = 'usuario=estudiante@example.com'
    test_case.save(update_fields=['test_data'])
    test_case.test_plan.environment = 'Firefox'
    test_case.test_plan.save(update_fields=['environment'])
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_type': ExecutionModel.ExecutionType.NORMAL,
            'result': ExecutionModel.Result.FAILED,
            **step_payload(
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.FAILED,
                ExecutionModel.Result.BLOCKED,
            ),
        },
    )

    execution = ExecutionModel.objects.get(test_case=test_case)
    defect = Defect.objects.get(execution=execution)

    assert response.status_code == 302
    assert defect.project == test_case.test_plan.project
    assert defect.reported_by == user
    assert execution.result == ExecutionModel.Result.FAILED
    assert 'Paso 2 [FAILED]: Resultado observado en el paso 2.' in defect.description
    assert 'Datos usados:\nusuario=estudiante@example.com' in defect.description
    assert 'Ambiente:\nFirefox' in defect.description
    assert AuditLog.objects.filter(action='CREATE', entity='TestExecution', entity_id=str(execution.pk)).exists()
    assert AuditLog.objects.filter(action='CREATE', entity='Defect', metadata__source='failed_execution').exists()


@pytest.mark.django_db
def test_prueba_de_confirmacion_aprobada_cierra_defecto(client, test_case, execution, user):
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        execution=execution,
        code='DEF-CONF-001',
        title='Defecto corregido',
        description='Pendiente de confirmacion.',
        status=Defect.Status.PENDING_CONFIRMATION,
        reported_by=user,
    )
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_type': ExecutionModel.ExecutionType.CONFIRMATION,
            'related_defect': defect.pk,
            'planned_date': timezone.localdate().isoformat(),
            'result': ExecutionModel.Result.PASSED,
            'actual_result': 'La corrección queda verificada.',
            'test_data': 'usuario=estudiante@example.com',
            'environment': 'Chrome',
            'notes': 'Confirmacion correcta.',
            **step_payload(
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
            ),
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
    defect = Defect.objects.create(
        project=test_case.test_plan.project,
        execution=execution,
        code='DEF-CONF-002',
        title='Defecto no corregido',
        description='Pendiente de confirmacion.',
        status=Defect.Status.PENDING_CONFIRMATION,
        reported_by=user,
    )
    client.force_login(user)

    response = client.post(
        f'{reverse("executions:index")}?case={test_case.id}',
        data={
            'execution_type': ExecutionModel.ExecutionType.CONFIRMATION,
            'related_defect': defect.pk,
            'result': ExecutionModel.Result.FAILED,
            'actual_result': 'El error persiste.',
            'test_data': 'usuario=estudiante@example.com',
            'environment': 'Firefox',
            'notes': 'Confirmacion fallida.',
            **step_payload(
                ExecutionModel.Result.FAILED,
                ExecutionModel.Result.PASSED,
                ExecutionModel.Result.PASSED,
            ),
        },
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
        validation_type=AutomatedValidationRule.ValidationType.TEXT_VISIBLE,
        target_url='http://localhost:8000/login/',
        expected_text='Iniciar Sesión',
    )
    automated_execution = ExecutionModel.objects.create(
        test_case=test_case,
        execution_mode=ExecutionModel.ExecutionMode.SEMI_AUTOMATED,
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
    assert b'Historial semi-automatizado' in response.content
    assert response.context['test_cases'].filter(pk=test_case.pk).exists()
    assert test_case.code.encode() in response.content


@pytest.mark.django_db
def test_vista_elimina_ejecucion_automatizada_revisada_del_historial(client, test_case, user):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Titulo de login visible',
        validation_type=AutomatedValidationRule.ValidationType.TEXT_VISIBLE,
        target_url='http://localhost:8000/login/',
        expected_text='Iniciar Sesión',
    )
    execution = ExecutionModel.objects.create(
        test_case=test_case,
        execution_mode=ExecutionModel.ExecutionMode.SEMI_AUTOMATED,
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
        validation_type=AutomatedValidationRule.ValidationType.TEXT_VISIBLE,
        target_url='http://localhost:8000/login/',
        expected_text='Iniciar Sesión',
    )
    client.force_login(user)

    response = client.post(reverse('executions:rule-delete', args=[rule.pk]), follow=True)

    assert response.status_code == 200
    assert not AutomatedValidationRule.objects.filter(pk=rule.pk).exists()
    assert b'Regla automatizada eliminada.' in response.content


@pytest.mark.django_db
def test_vista_oculta_regla_automatizada_con_historial(client, test_case, execution, user):
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Titulo de login visible',
        validation_type=AutomatedValidationRule.ValidationType.TEXT_VISIBLE,
        target_url='http://localhost:8000/login/',
        expected_text='Iniciar Sesión',
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
    assert b'La regla tiene historial y fue desactivada en lugar de eliminarse.' in response.content


def test_agregacion_automatizada_prioriza_fallo_y_error():
    assert aggregate_automated_status([
        ExecutionModel.Result.PASSED,
        ExecutionModel.Result.ERROR,
    ]) == ExecutionModel.Result.ERROR
    assert aggregate_automated_status([
        ExecutionModel.Result.ERROR,
        ExecutionModel.Result.FAILED,
    ]) == ExecutionModel.Result.FAILED


@pytest.mark.django_db
def test_formulario_http_exige_estado_esperado(test_case, settings):
    settings.AUTOMATION_ALLOWED_HOSTS = ('localhost',)
    form = AutomatedValidationRuleForm(
        data={
            'name': 'Disponibilidad local',
            'step_number': 1,
            'validation_type': AutomatedValidationRule.ValidationType.HTTP_STATUS,
            'target_url': 'http://localhost:8000/health/',
            'timeout_seconds': 5,
            'browser': 'chromium',
            'is_active': True,
        },
        test_case=test_case,
    )

    assert not form.is_valid()
    assert 'expected_http_status' in form.errors


@pytest.mark.django_db
def test_ejecucion_http_status_aprobada(client, test_case, user, settings):
    settings.AUTOMATION_ALLOWED_HOSTS = ('localhost',)
    rule = AutomatedValidationRule.objects.create(
        test_case=test_case,
        requirement=test_case.requirement,
        step_number=1,
        name='Pagina disponible',
        validation_type=AutomatedValidationRule.ValidationType.HTTP_STATUS,
        target_url='http://localhost:8000/health/',
        expected_http_status=200,
        timeout_seconds=5,
    )
    response_mock = Mock()
    response_mock.status = 200
    response_mock.geturl.return_value = rule.target_url
    response_mock.read.return_value = b''
    response_mock.__enter__ = Mock(return_value=response_mock)
    response_mock.__exit__ = Mock(return_value=False)
    client.force_login(user)

    with patch('apps.executions.services.automated_runner.socket.getaddrinfo') as resolver, patch(
        'apps.executions.services.automated_runner.build_opener'
    ) as opener_builder:
        resolver.return_value = [(None, None, None, None, ('127.0.0.1', 8000))]
        opener_builder.return_value.open.return_value = response_mock
        response = client.post(reverse('executions:run-automated', args=[test_case.pk]))

    execution = ExecutionModel.objects.get(execution_mode=ExecutionModel.ExecutionMode.SEMI_AUTOMATED)
    result = AutomatedExecutionResult.objects.get(test_execution=execution)

    assert response.status_code == 302
    assert execution.result == ExecutionModel.Result.PASSED
    assert result.status == ExecutionModel.Result.PASSED
    assert '[PASS]' in execution.technical_log


@pytest.mark.django_db(transaction=True)
def test_playwright_valida_texto_visible_en_servidor_django(live_server, settings):
    settings.AUTOMATION_ALLOWED_HOSTS = ('localhost', '127.0.0.1')
    rule = AutomatedValidationRule(
        name='Pantalla de login visible',
        step_number=1,
        validation_type=AutomatedValidationRule.ValidationType.TEXT_VISIBLE,
        target_url=f'{live_server.url}/login/',
        expected_text='Iniciar Sesión',
        timeout_seconds=10,
        browser='chromium',
        capture_evidence=True,
    )

    outcome = execute_rule(rule)

    assert outcome['status'] == ExecutionModel.Result.PASSED
    assert outcome['screenshot'].startswith(b'\x89PNG')
    assert '[PASS]' in outcome['log']

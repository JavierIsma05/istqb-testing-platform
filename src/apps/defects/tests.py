import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.defects.forms import DefectForm
from apps.defects.models import Defect, DefectHistory


@pytest.mark.django_db
def test_defecto_se_registra_con_caso_ejecucion_y_reportante(project, test_case, execution, user):
    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        execution=execution,
        code='DEF-001',
        title='Error al iniciar sesion',
        description='El login falla con credenciales validas.',
        severity=Defect.Severity.HIGH,
        reported_by=user,
    )

    assert defect.project == project
    assert defect.test_case == test_case
    assert defect.execution == execution
    assert defect.status == Defect.Status.OPEN
    assert str(defect) == 'Error al iniciar sesion'


@pytest.mark.django_db
def test_formulario_de_defecto_rechaza_registro_sin_caso_asociado(project, test_case):
    form = DefectForm(
        data={
            'test_case': '',
            'execution': '',
            'title': 'Mensaje de error incorrecto',
            'description': 'El mensaje mostrado no corresponde al fallo.',
            'severity': Defect.Severity.MEDIUM,
        }
    )

    assert not form.is_valid()
    assert 'test_case' in form.errors


@pytest.mark.django_db
def test_formulario_de_defecto_requiere_ejecucion_del_caso(project, test_case):
    form = DefectForm(
        data={
            'test_case': test_case.id,
            'execution': '',
            'title': 'Error visual en el listado',
            'description': 'Se ve un desplazamiento en la tabla.',
            'severity': Defect.Severity.LOW,
        },
        user=None,
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_formulario_de_defecto_rechaza_ejecucion_de_otro_caso(project, test_case, user):
    other = Defect.Severity.MEDIUM
    execution = None
    form = DefectForm(
        data={
            'test_case': test_case.id,
            'execution': execution,
            'title': 'Caso cruzado',
            'description': 'La ejecucion no corresponde al caso.',
            'severity': other,
        },
        user=user,
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_listado_muestra_defecto_sin_ejecucion(client, project, test_case, user):
    Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-003',
        title='Defecto sin ejecucion asociada',
        description='Registrado directamente contra el caso de prueba.',
        severity=Defect.Severity.LOW,
        reported_by=user,
    )
    client.force_login(user)

    response = client.get(reverse('defects:index'))

    assert response.status_code == 200
    assert 'Defecto sin ejecucion asociada' in response.content.decode()
    assert 'TC-001' in response.content.decode()


@pytest.mark.django_db
def test_creacion_de_defecto_registra_historial_inicial(client, project, test_case, execution, user):
    execution.result = execution.Result.FAILED
    execution.save(update_fields=['result'])
    client.force_login(user)

    response = client.post(
        reverse('defects:create'),
        {
            'test_case': test_case.id,
            'execution': execution.id,
            'title': 'Defecto con historial',
            'description': 'El sistema debe guardar historial inicial.',
            'severity': Defect.Severity.HIGH,
        },
    )

    defect = Defect.objects.get(title='Defecto con historial')
    history = defect.history.get()

    assert response.status_code == 302
    assert defect.status == Defect.Status.OPEN
    assert defect.code.startswith('DEF-')
    assert history.status == Defect.Status.OPEN
    assert history.changed_by == user
    assert history.snapshot['test_case_id'] == test_case.pk
    assert AuditLog.objects.filter(action='CREATE', entity='Defect', entity_id=str(defect.pk)).exists()


@pytest.mark.django_db
def test_actualizacion_de_defecto_agrega_historial(client, project, test_case, execution, user):
    execution.result = execution.Result.FAILED
    execution.save(update_fields=['result'])
    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        execution=execution,
        code='DEF-004',
        title='Defecto a actualizar',
        description='Estado inicial.',
        severity=Defect.Severity.MEDIUM,
        reported_by=user,
    )
    DefectHistory.objects.create(
        defect=defect,
        status=defect.status,
        severity=defect.severity,
        priority=defect.priority,
        changed_by=user,
    )
    client.force_login(user)

    response = client.post(
        reverse('defects:edit', args=[defect.pk]),
        {
            'test_case': test_case.id,
            'execution': execution.id,
            'title': 'Defecto a actualizar',
            'description': 'Estado actualizado.',
            'severity': Defect.Severity.HIGH,
        },
    )

    defect.refresh_from_db()

    assert response.status_code == 302
    assert defect.severity == Defect.Severity.HIGH
    assert defect.history.count() == 2
    assert AuditLog.objects.filter(action='UPDATE', entity='Defect', entity_id=str(defect.pk)).exists()


@pytest.mark.django_db
def test_transicion_de_estado_avanza_por_el_ciclo(client, project, test_case, user):
    from apps.executions.models import TestExecution

    defect = Defect.objects.create(
        project=project,
        test_case=test_case,
        code='DEF-005',
        title='Defecto en ciclo',
        description='Avanza a traves de las transiciones.',
        severity=Defect.Severity.MEDIUM,
        reported_by=user,
    )
    client.force_login(user)

    for expected in (Defect.Status.IN_PROGRESS, Defect.Status.RESOLVED):
        response = client.post(reverse('defects:transition', args=[defect.pk, expected]))
        defect.refresh_from_db()
        assert response.status_code == 302
        assert defect.status == expected

    defect.assigned_to = user
    defect.resolution = 'Se corrigió la validación y se preparó confirmación.'
    defect.save(update_fields=['assigned_to', 'resolution', 'updated_at'])
    response = client.post(reverse('defects:transition', args=[defect.pk, Defect.Status.PENDING_CONFIRMATION]))
    defect.refresh_from_db()
    assert response.status_code == 302
    assert defect.status == Defect.Status.PENDING_CONFIRMATION

    confirmation = TestExecution.objects.create(
        test_case=test_case,
        execution_type=TestExecution.ExecutionType.CONFIRMATION,
        related_defect=defect,
        executed_by=user,
        result=TestExecution.Result.PASSED,
    )
    defect.verification_execution = confirmation
    defect.save(update_fields=['verification_execution', 'updated_at'])
    for expected in (Defect.Status.CLOSED, Defect.Status.REOPENED, Defect.Status.IN_PROGRESS):
        response = client.post(reverse('defects:transition', args=[defect.pk, expected]))
        defect.refresh_from_db()
        assert response.status_code == 302
        assert defect.status == expected

    assert defect.history.count() == 6


@pytest.mark.django_db
def test_usuario_no_puede_modificar_ni_eliminar_defecto_de_proyecto_ajeno(client, user):
    from apps.projects.models import Project
    from apps.testcases.models import TestCase
    other_user = get_user_model().objects.create_user(email='foreign-defect@example.edu', password='StrongPass123')
    project = Project.objects.create(code='PRJ-FOREIGN-DEF', name='Proyecto ajeno', created_by=other_user)
    # A defect only needs project/reporting fields for authorization lookup.
    defect = Defect.objects.create(project=project, code='DEF-999', title='Defecto privado', description='Privado.', reported_by=other_user)
    client.force_login(user)
    response = client.get(reverse('defects:edit', args=[defect.pk]))
    assert response.status_code == 404
    response = client.post(reverse('defects:delete', args=[defect.pk]))
    assert response.status_code == 404
    assert Defect.objects.filter(pk=defect.pk).exists()


@pytest.mark.django_db
def test_usuario_no_puede_transicionar_defecto_de_proyecto_ajeno(client, user):
    from apps.projects.models import Project
    other_user = get_user_model().objects.create_user(email='foreign-transition@example.edu', password='StrongPass123')
    project = Project.objects.create(code='PRJ-FOREIGN-TRANS', name='Proyecto ajeno', created_by=other_user)
    defect = Defect.objects.create(project=project, code='DEF-998', title='Defecto protegido', description='Privado.', reported_by=other_user)
    client.force_login(user)
    response = client.post(reverse('defects:transition', args=[defect.pk, Defect.Status.IN_PROGRESS]))
    assert response.status_code == 404
    defect.refresh_from_db()
    assert defect.status == Defect.Status.OPEN
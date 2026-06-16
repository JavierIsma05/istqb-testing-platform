import pytest
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.defects.forms import DefectForm
from apps.defects.models import Defect, DefectHistory


@pytest.mark.django_db
def test_defecto_se_registra_con_proyecto_ejecucion_y_reportante(project, execution, user):
    defect = Defect.objects.create(
        project=project,
        execution=execution,
        code='DEF-001',
        title='Error al iniciar sesion',
        description='El login falla con credenciales validas.',
        severity=Defect.Severity.HIGH,
        reported_by=user,
    )

    assert defect.project == project
    assert defect.execution == execution
    assert defect.status == Defect.Status.OPEN
    assert str(defect) == 'Error al iniciar sesion'


@pytest.mark.django_db
def test_formulario_de_defecto_rechaza_registro_sin_ejecucion_asociada(project):
    form = DefectForm(
        data={
            'project': project.id,
            'execution': '',
            'code': 'DEF-002',
            'title': 'Mensaje de error incorrecto',
            'description': 'El mensaje mostrado no corresponde al fallo.',
            'steps_to_reproduce': '1. Abrir login\n2. Enviar datos invalidos',
            'severity': Defect.Severity.MEDIUM,
            'priority': Defect.Priority.MEDIUM,
            'status': Defect.Status.OPEN,
            'assigned_to': '',
        }
    )

    assert not form.is_valid()
    assert 'execution' in form.errors


@pytest.mark.django_db
def test_listado_muestra_sin_asignar_cuando_defecto_no_tiene_responsable(client, project, user):
    Defect.objects.create(
        project=project,
        code='DEF-003',
        title='Defecto sin responsable',
        description='El defecto aun no fue asignado.',
        severity=Defect.Severity.LOW,
        priority=Defect.Priority.LOW,
        reported_by=user,
    )
    client.force_login(user)

    response = client.get(reverse('defects:index'))

    assert response.status_code == 200
    assert 'Defecto sin responsable' in response.content.decode()
    assert 'Sin asignar' in response.content.decode()


@pytest.mark.django_db
def test_creacion_de_defecto_registra_historial_inicial(client, project, execution, user):
    execution.result = execution.Result.FAILED
    execution.save(update_fields=['result'])
    client.force_login(user)

    response = client.post(
        reverse('defects:create'),
        {
            'project': project.id,
            'execution': execution.id,
            'title': 'Defecto con historial',
            'description': 'El sistema debe guardar historial inicial.',
            'steps_to_reproduce': '1. Ejecutar caso\n2. Observar error',
            'severity': Defect.Severity.HIGH,
            'priority': Defect.Priority.HIGH,
            'status': Defect.Status.OPEN,
            'assigned_to': '',
        },
    )

    defect = Defect.objects.get(title='Defecto con historial')
    history = defect.history.get()

    assert response.status_code == 302
    assert defect.steps_to_reproduce
    assert history.status == Defect.Status.OPEN
    assert history.changed_by == user
    assert history.snapshot['steps_to_reproduce'] == defect.steps_to_reproduce
    assert AuditLog.objects.filter(action='CREATE', entity='Defect', entity_id=str(defect.pk)).exists()


@pytest.mark.django_db
def test_actualizacion_de_defecto_agrega_historial(client, project, execution, user):
    execution.result = execution.Result.FAILED
    execution.save(update_fields=['result'])
    defect = Defect.objects.create(
        project=project,
        execution=execution,
        code='DEF-004',
        title='Defecto a actualizar',
        description='Estado inicial.',
        severity=Defect.Severity.MEDIUM,
        priority=Defect.Priority.MEDIUM,
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
            'project': project.id,
            'execution': execution.id,
            'title': 'Defecto a actualizar',
            'description': 'Estado actualizado.',
            'steps_to_reproduce': '1. Repetir flujo\n2. Confirmar error',
            'severity': Defect.Severity.HIGH,
            'priority': Defect.Priority.CRITICAL,
            'status': Defect.Status.PENDING_CONFIRMATION,
            'assigned_to': '',
        },
    )

    defect.refresh_from_db()

    assert response.status_code == 302
    assert defect.history.count() == 2
    assert defect.history.first().status == Defect.Status.PENDING_CONFIRMATION
    assert defect.history.first().snapshot['priority'] == Defect.Priority.CRITICAL
    assert AuditLog.objects.filter(action='UPDATE', entity='Defect', entity_id=str(defect.pk)).exists()

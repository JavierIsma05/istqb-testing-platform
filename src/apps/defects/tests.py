import pytest

from apps.defects.forms import DefectForm
from apps.defects.models import Defect


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
def test_formulario_de_defecto_es_valido_sin_ejecucion_asociada(project):
    form = DefectForm(
        data={
            'project': project.id,
            'execution': '',
            'code': 'DEF-002',
            'title': 'Mensaje de error incorrecto',
            'description': 'El mensaje mostrado no corresponde al fallo.',
            'severity': Defect.Severity.MEDIUM,
            'priority': Defect.Priority.MEDIUM,
            'status': Defect.Status.OPEN,
            'assigned_to': '',
        }
    )

    assert form.is_valid()

import pytest

from apps.reports.forms import ReportForm
from apps.reports.models import Report


@pytest.mark.django_db
def test_reporte_guarda_tipo_contenido_y_usuario_generador(project, user):
    report = Report.objects.create(
        project=project,
        title='Resumen de ejecucion',
        report_type=Report.ReportType.EXECUTION,
        generated_by=user,
        content={'passed': 8, 'failed': 1},
    )

    assert report.project == project
    assert report.content['passed'] == 8
    assert str(report) == 'Resumen de ejecucion'


@pytest.mark.django_db
def test_formulario_de_reporte_es_valido_con_tipo_de_cobertura(project):
    form = ReportForm(
        data={
            'project': project.id,
            'title': 'Cobertura de requisitos',
            'report_type': Report.ReportType.COVERAGE,
        }
    )

    assert form.is_valid()

from io import BytesIO

import pytest
from django.urls import reverse

from apps.defects.models import Defect
from apps.executions.models import TestExecution as ExecutionModel
from apps.audit.models import AuditLog
from apps.reports.forms import ReportForm
from apps.reports.models import Report, ReportDownload
from apps.reports.views import (
    build_final_chart_groups,
    build_final_pie_groups,
    build_pdf_chart_data,
    build_pdf_sections,
    build_report_content,
    build_unl_pdf,
)


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


@pytest.mark.django_db
def test_contenido_del_reporte_cambia_segun_tipo(project, test_case, execution, user):
    Defect.objects.create(
        project=project,
        execution=execution,
        code='DEF-REP-001',
        title='Validacion falla',
        description='Falla detectada durante la ejecucion.',
        severity=Defect.Severity.CRITICAL,
        priority=Defect.Priority.HIGH,
        reported_by=user,
    )

    reports = {
        report_type: Report(project=project, title='Reporte', report_type=report_type)
        for report_type in Report.ReportType.values
    }

    summary = build_report_content(reports[Report.ReportType.SUMMARY])
    coverage = build_report_content(reports[Report.ReportType.COVERAGE])
    defects = build_report_content(reports[Report.ReportType.DEFECTS])
    execution_content = build_report_content(reports[Report.ReportType.EXECUTION])

    assert 'coverage' in coverage
    assert 'uncovered_requirements' in coverage
    assert 'critical_defects' in defects
    assert 'passed_executions' in execution_content
    assert 'requirements' in summary
    assert set(coverage) != set(defects)
    assert set(defects) != set(execution_content)
    assert set(summary) != set(coverage)
    assert execution_content['passed_executions'] == 1
    assert defects['critical_defects'] == 1


@pytest.mark.django_db
def test_reporte_de_ejecucion_cuenta_resultados(project, test_case, user):
    ExecutionModel.objects.create(
        test_case=test_case,
        executed_by=user,
        result=ExecutionModel.Result.PASSED,
    )
    ExecutionModel.objects.create(
        test_case=test_case,
        executed_by=user,
        result=ExecutionModel.Result.FAILED,
    )

    report = Report(project=project, title='Ejecucion', report_type=Report.ReportType.EXECUTION)

    content = build_report_content(report)

    assert content['executions'] == 2
    assert content['passed_executions'] == 1
    assert content['failed_executions'] == 1
    assert content['success_rate'] == 50
    assert content['functional_executions'] == 2
    assert content['confirmation_executions'] == 0


@pytest.mark.django_db
def test_reporte_se_elimina_desde_el_listado(client, project, user):
    report = Report.objects.create(
        project=project,
        title='Reporte temporal',
        report_type=Report.ReportType.SUMMARY,
        generated_by=user,
        content={'project': project.name},
    )
    client.force_login(user)

    response = client.post(reverse('reports:delete', args=[report.pk]))

    assert response.status_code == 302
    assert not Report.objects.filter(pk=report.pk).exists()
    assert AuditLog.objects.filter(action='DELETE', entity='Report', entity_id=str(report.pk)).exists()


@pytest.mark.django_db
def test_creacion_de_reporte_registra_auditoria(client, project, user):
    client.force_login(user)

    response = client.post(
        reverse('reports:index'),
        {
            'project': project.id,
            'title': 'Reporte auditado',
            'report_type': Report.ReportType.SUMMARY,
        },
    )

    report = Report.objects.get(title='Reporte auditado')

    assert response.status_code == 302
    assert AuditLog.objects.filter(action='CREATE', entity='Report', entity_id=str(report.pk)).exists()


@pytest.mark.django_db
def test_descarga_de_reporte_registra_historial_y_auditoria(client, project, user):
    report = Report.objects.create(
        project=project,
        title='Reporte descargable',
        report_type=Report.ReportType.SUMMARY,
        generated_by=user,
        content={'project': project.name},
    )
    client.force_login(user)

    response = client.get(reverse('reports:download', args=[report.pk]))

    download = ReportDownload.objects.get(report=report)

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert download.downloaded_by == user
    assert download.filename == f'reporte-unl-{report.id}.pdf'
    assert AuditLog.objects.filter(action='DOWNLOAD', entity='Report', entity_id=str(report.pk)).exists()


@pytest.mark.django_db
def test_pdf_sections_incluyen_estructura_normativa(project, user):
    report = Report.objects.create(
        project=project,
        title='Informe estructurado',
        report_type=Report.ReportType.SUMMARY,
        generated_by=user,
        content={'project': project.name, 'requirements': 2, 'test_cases': 3, 'executions': 1, 'defects': 0, 'risks': 1},
    )

    sections = build_pdf_sections(report)
    titles = [section['title'] for section in sections]

    assert titles == [
        'Identificacion del informe',
        'Alcance y objetivo',
        'Resumen ejecutivo',
        'Metricas y resultados',
        'Grafico automatico de metricas',
        'Observaciones y cierre',
    ]
    assert any('ISO/IEC/IEEE 29119-3' in value for label, value in sections[1]['items'] if label == 'Referencia')


@pytest.mark.django_db
def test_datos_de_grafico_cambian_segun_tipo(project, user):
    coverage_report = Report.objects.create(
        project=project,
        title='Cobertura',
        report_type=Report.ReportType.COVERAGE,
        generated_by=user,
        content={'covered_requirements': 4, 'uncovered_requirements': 1},
    )
    execution_report = Report.objects.create(
        project=project,
        title='Ejecucion',
        report_type=Report.ReportType.EXECUTION,
        generated_by=user,
        content={'passed_executions': 3, 'failed_executions': 2, 'blocked_executions': 1, 'not_run_executions': 0},
    )

    assert build_pdf_chart_data(coverage_report) == [('Cubiertos', 4), ('Sin cobertura', 1)]
    assert ('Aprobadas', 3) in build_pdf_chart_data(execution_report)
    assert ('Fallidas', 2) in build_pdf_chart_data(execution_report)


@pytest.mark.django_db
def test_pdf_institucional_se_genera_con_contenido(project, user):
    report = Report.objects.create(
        project=project,
        title='PDF institucional',
        report_type=Report.ReportType.DEFECTS,
        generated_by=user,
        content={'project': project.name, 'defects': 2, 'critical_defects': 1, 'closed_defects': 1},
    )
    buffer = BytesIO()

    build_unl_pdf(buffer, report)
    pdf_bytes = buffer.getvalue()

    assert pdf_bytes.startswith(b'%PDF')
    assert len(pdf_bytes) > 2500


@pytest.mark.django_db
def test_informe_final_consolida_requisitos_ejecuciones_y_trazabilidad(project, test_case, execution, user):
    report = Report(project=project, title='Informe final', report_type=Report.ReportType.FINAL)

    content = build_report_content(report)

    assert content['requirements'] == 1
    assert content['executed_requirements'] == 1
    assert content['passed_requirements'] == 1
    assert content['failed_requirements'] == 0
    assert content['test_cases'] == 1
    assert content['executions'] == 1
    assert 0 <= content['traceability_index'] <= 100


@pytest.mark.django_db
def test_informe_final_genera_barras_pasteles_y_leyendas(project, user):
    report = Report.objects.create(
        project=project,
        title='Informe final grafico',
        report_type=Report.ReportType.FINAL,
        generated_by=user,
        content={
            'passed_executions': 3,
            'failed_executions': 1,
            'blocked_executions': 0,
            'error_executions': 0,
            'covered_requirements': 4,
            'uncovered_requirements': 1,
            'manual_executions': 2,
            'semi_automated_executions': 2,
        },
    )

    bars = build_final_chart_groups(report)
    pies = build_final_pie_groups(report)

    assert len(bars) == 4
    assert len(pies) == 3
    assert pies[0]['items'][0]['label'] == 'PASS'
    assert pies[0]['items'][0]['percent'] == 75
    assert '24936e' in pies[0]['gradient']


@pytest.mark.django_db
def test_vista_informe_final_muestra_pasteles_y_leyendas(client, project, user):
    report = Report.objects.create(
        project=project,
        title='Informe global visual',
        report_type=Report.ReportType.FINAL,
        generated_by=user,
        content={'requirements': 2, 'executions': 1, 'traceability_index': 80},
    )
    client.force_login(user)

    response = client.get(reverse('reports:detail', args=[report.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Distribuciones porcentuales' in content
    assert 'pie-chart' in content
    assert 'chart-legend' in content
    assert 'images/reports/career-logo.png' in content
    assert 'images/reports/unl-logo.png' in content

from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import escape

from apps.defects.models import Defect
from apps.executions.models import TestExecution as ExecutionModel
from apps.incidents.models import Incident
from apps.audit.models import AuditLog
from apps.phases.models import TestingPhase
from apps.reports.forms import ReportForm
from apps.reports.models import Report, ReportDownload
from apps.reports.views import (
    _plan_pdf_sections,
    _plan_report_context,
    _plan_report_data,
    build_final_chart_groups,
    build_final_pie_groups,
    build_pdf_chart_data,
    build_pdf_sections,
    build_report_content,
    build_unl_pdf,
)


@pytest.mark.django_db
def test_informe_de_casos_ejecutados_muestra_tabla(client, project, user, test_case, test_plan):
    execution = ExecutionModel.objects.create(
        test_case=test_case,
        executed_by=user,
        result=ExecutionModel.Result.PASSED,
        actual_result='Resultado esperado observado.',
    )
    client.force_login(user)

    response = client.get(reverse('reports:plan-casos', args=[test_plan.pk]))

    assert response.status_code == 200
    assert b'Informe de Casos de Prueba' in response.content
    assert b'ID y Nombre del Caso de Prueba' in response.content
    assert b'Prioridad' in response.content
    assert str(test_case.code).encode() in response.content
    assert str(execution.get_result_display()).encode() in response.content


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
        severity=Defect.Severity.HIGH,
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
        'Identificación del informe',
        'Alcance y objetivo',
        'Resumen ejecutivo',
        'Métricas y resultados',
        'Gráfico automático de métricas',
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
def test_informe_final_usa_fases_reales_y_resumen_de_revision(project, test_case, execution, user):
    execution.review_status = ExecutionModel.ReviewStatus.VALIDATED
    execution.reviewed_by = user
    execution.save(update_fields=['review_status', 'reviewed_by'])
    TestingPhase.objects.create(
        project=project,
        order=1,
        name='Analisis de requisitos',
        status=TestingPhase.Status.DONE,
        progress=100,
    )
    TestingPhase.objects.create(
        project=project,
        order=2,
        name='Cierre',
        status=TestingPhase.Status.IN_PROGRESS,
        progress=50,
    )
    report = Report(project=project, title='Informe final', report_type=Report.ReportType.FINAL)

    content = build_report_content(report)

    assert content['cycle_statuses'] == [
        {'phase': 'Analisis de requisitos', 'status': 'Completada'},
        {'phase': 'Cierre', 'status': 'En progreso'},
    ]
    assert content['cycle_progress'] == 50
    assert content['teacher_review_summary'][0] == {
        'section': 'Requisitos',
        'reviewed': 0,
        'total': 1,
        'pending': 1,
    }
    assert content['teacher_review_summary'][1] == {
        'section': 'Ejecuciones',
        'reviewed': 1,
        'total': 1,
        'pending': 0,
    }
    assert content['teacher_review_summary'][-1] == {
        'section': 'Fases',
        'reviewed': 1,
        'total': 2,
        'pending': 1,
    }


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
            'automated_executions': 2,
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


@pytest.mark.django_db
def test_dashboard_plan_requiere_autenticacion(client, test_plan):
    response = client.get(reverse('reports:plan-dashboard', args=[test_plan.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_plan_muestra_metricas(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-dashboard', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Dashboard del Plan de Pruebas' in content
    assert 'Requisitos' in content
    assert 'Casos de Prueba' in content
    assert 'Ejecuciones' in content
    assert '/casos/' in content


@pytest.mark.django_db
def test_informe_casos_plan_muestra_tabla_y_pasos(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-casos', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Informe de Casos de Prueba' in content
    assert test_case.code in content
    assert test_case.get_priority_display() in content
    assert 'Pasos de ejecución' in content
    assert 'Imprimir' in content


@pytest.mark.django_db
def test_informe_ejecuciones_plan_muestra_estados(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-ejecuciones', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Informe de Ejecuciones' in content
    assert 'Aprobadas' in content
    assert 'Total ejecuciones' in content
    assert 'Distribución por estado' in content


@pytest.mark.django_db
def test_informe_defectos_plan_muestra_vacio(client, project, user, test_plan, test_case):
    client.force_login(user)

    response = client.get(reverse('reports:plan-defectos', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Informe de Defectos' in content
    assert 'El plan de pruebas no tiene defectos registrados' in content


@pytest.mark.django_db
def test_informe_final_plan_muestra_veredicto(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-final', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'INFORME FINAL DE PRUEBAS' in content
    assert 'Veredicto final' in content
    assert 'Conclusiones' in content


@pytest.mark.django_db
def test_pdf_plan_report_se_genera(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    for section in ('plan', 'casos', 'ejecuciones', 'defectos', 'final'):
        response = client.get(reverse('reports:plan-pdf', args=[test_plan.pk, section]))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'


@pytest.mark.django_db
def test_dashboard_plan_404_para_proyecto_no_visible(client, project, user, test_plan):
    other_user = get_user_model().objects.create_user(email='other@example.com', password='StrongPass123')
    client.force_login(other_user)

    response = client.get(reverse('reports:plan-dashboard', args=[test_plan.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_index_muestra_cinco_informes_de_calidad(client, user):
    client.force_login(user)

    response = client.get(reverse('reports:index'))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Informes de Calidad' in content
    assert content.count('report-nav-card') == 5
    assert 'Informe del Plan de Pruebas' in content
    assert 'Informe de Casos de Prueba' in content
    assert 'Informe de Ejecuciones' in content
    assert 'Informe de Defectos' in content
    assert 'Informe Final de Pruebas' in content
    assert 'Generar Nuevo Informe' in content
    assert 'Flujo y trazabilidad' in content
    assert 'Beneficios' in content
    assert 'Resumen Ejecutivo' not in content
    assert 'Reportes Generados' not in content
    assert 'reportModal' not in content


@pytest.mark.django_db
def test_selector_redirige_al_informe_segun_tipo(client, project, user, test_plan):
    client.force_login(user)

    response = client.get(
        reverse('reports:plan-report'),
        {'project': project.id, 'plan': test_plan.id, 'type': 'final'},
    )

    assert response.status_code == 302
    assert response.url == reverse('reports:plan-final', args=[test_plan.pk])

    response = client.get(
        reverse('reports:plan-report'),
        {'project': project.id, 'plan': test_plan.id, 'type': 'casos'},
    )

    assert response.status_code == 302
    assert response.url == reverse('reports:plan-casos', args=[test_plan.pk])


@pytest.mark.django_db
def test_informe_final_incluye_resumen_y_recomendaciones(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-final', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Resumen ejecutivo' in content
    assert 'Alcance de la evaluación' in content
    assert 'Recomendaciones' in content


@pytest.mark.django_db
def test_informe_casos_muestra_detalle_por_caso(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-casos', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'ID y Nombre del Caso de Prueba' in content
    assert 'Precondiciones' in content
    assert 'Resultado esperado' in content
    assert 'Resultado obtenido' in content


@pytest.mark.django_db
def test_pdf_casos_incluye_detalle_en_una_fila_por_caso(project, user, test_plan, test_case, execution):
    sections = _plan_pdf_sections(
        test_plan,
        'casos',
        _plan_report_data(test_plan),
        {},
    )
    table = next(section['table'] for section in sections if 'table' in section and 'ID y Nombre' in section['table']['headers'][0])

    assert table['headers'] == [
        'ID y Nombre del Caso de Prueba',
        'Estado',
        'Requisito',
        'Prioridad',
        'Técnica',
        'Nivel',
        'Versión',
        'Descripción',
        'Precondiciones',
        'Datos de prueba',
        'Pasos de ejecución',
        'Resultado esperado',
        'Resultado obtenido',
    ]
    row = table['rows'][0]

    assert row[0] == f'{test_case.code} - {test_case.title}'
    assert row[1] == 'Aprobado'
    assert test_case.requirement.code in row[2]
    assert row[3] == test_case.get_priority_display()
    assert row[4] == test_case.get_technique_display()
    assert row[5] == test_case.get_level_display()
    assert row[6] == test_case.version
    assert row[10] == escape(test_case.steps).replace('\n', '<br/>')
    assert row[12] == execution.actual_result or '—'


@pytest.mark.django_db
def test_informe_ejecuciones_muestra_detalle(client, project, user, test_plan, test_case, execution):
    client.force_login(user)

    response = client.get(reverse('reports:plan-ejecuciones', args=[test_plan.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'Detalle de ejecuciones' in content
    assert test_case.code in content
    assert execution.get_result_display() in content


@pytest.mark.django_db
def test_plan_context_matriz_alinea_impactos_con_columnas(project, user, test_plan):
    Incident.objects.create(
        project=project,
        test_plan=test_plan,
        code='INC-001',
        title='Riesgo bajo impacto bajo',
        description='Descripcion.',
        probability=Incident.Probability.LOW,
        impact=Incident.Impact.LOW,
        reported_by=user,
    )
    Incident.objects.create(
        project=project,
        test_plan=test_plan,
        code='INC-002',
        title='Riesgo alto impacto alto',
        description='Descripcion.',
        probability=Incident.Probability.HIGH,
        impact=Incident.Impact.HIGH,
        reported_by=user,
    )

    context = _plan_report_context(test_plan)

    assert context['risk_matrix_impacts'] == ['Bajo', 'Medio', 'Alto']
    last_row = context['risk_matrix'][-1]
    first_row = context['risk_matrix'][0]
    assert last_row['probability'] == 'Baja'
    assert first_row['probability'] == 'Alta'
    assert last_row['low'] == 1
    assert last_row['high'] == 0
    assert first_row['high'] == 1
    assert first_row['low'] == 0


@pytest.mark.django_db
def test_plan_pdf_incluye_chart_datos_de_distribucion(project, user, test_plan):
    Incident.objects.create(
        project=project,
        test_plan=test_plan,
        code='INC-001',
        title='Riesgo medio',
        description='Descripcion.',
        probability=Incident.Probability.MEDIUM,
        impact=Incident.Impact.MEDIUM,
        reported_by=user,
    )

    sections = _plan_pdf_sections(
        test_plan,
        'plan',
        _plan_report_data(test_plan),
        _plan_report_context(test_plan),
    )

    chart_titles = [s['title'] for s in sections if 'chart_data' in s]
    for expected in ('Distribución de riesgos por nivel', 'Distribución por probabilidad', 'Distribución por impacto'):
        assert expected in chart_titles

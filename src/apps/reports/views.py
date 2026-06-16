from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as ReportLabImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase

from .forms import ReportForm
from .models import Report, ReportDownload


REPORT_CARDS = [
    {
        'title': 'Resumen Ejecutivo',
        'description': 'Vista general del avance del proyecto',
        'icon': 'bi-file-earmark-bar-graph',
        'tone': 'brand',
        'type': Report.ReportType.SUMMARY,
    },
    {
        'title': 'Informe de Cobertura',
        'description': 'Reporte completo de cobertura de pruebas',
        'icon': 'bi-file-earmark-text',
        'tone': 'brand',
        'type': Report.ReportType.COVERAGE,
    },
    {
        'title': 'Reporte de Ejecución',
        'description': 'Resultados de ejecución de casos de prueba',
        'icon': 'bi-file-earmark-check',
        'tone': 'success',
        'type': Report.ReportType.EXECUTION,
    },
    {
        'title': 'Análisis de Defectos',
        'description': 'Estadísticas y métricas de defectos',
        'icon': 'bi-file-earmark-medical',
        'tone': 'danger',
        'type': Report.ReportType.DEFECTS,
    },
    {
        'title': 'Informe General Final',
        'description': 'Cobertura, ejecucion, defectos, riesgos y trazabilidad con graficos',
        'icon': 'bi-graph-up-arrow',
        'tone': 'success',
        'type': Report.ReportType.FINAL,
    },
]

CONTENT_LABELS = {
    'project': 'Proyecto',
    'requirements': 'Total de requisitos',
    'covered_requirements': 'Requisitos cubiertos',
    'uncovered_requirements': 'Requisitos sin cobertura',
    'coverage': 'Cobertura (%)',
    'test_cases': 'Casos de prueba',
    'linked_test_cases': 'Casos vinculados a requisitos',
    'pending_test_cases': 'Casos pendientes',
    'passed_test_cases': 'Casos aprobados',
    'failed_test_cases': 'Casos fallidos',
    'blocked_test_cases': 'Casos bloqueados',
    'executions': 'Ejecuciones registradas',
    'not_run_executions': 'Ejecuciones no ejecutadas',
    'passed_executions': 'Ejecuciones aprobadas',
    'failed_executions': 'Ejecuciones fallidas',
    'blocked_executions': 'Ejecuciones bloqueadas',
    'error_executions': 'Ejecuciones con error tecnico',
    'manual_executions': 'Ejecuciones manuales',
    'semi_automated_executions': 'Ejecuciones semi-automatizadas',
    'automated_requirements': 'Requisitos con reglas automatizadas',
    'manual_only_requirements': 'Requisitos cubiertos solo manualmente',
    'automatic_defects': 'Defectos generados por automatizacion',
    'execution_progress': 'Avance de ejecucion (%)',
    'success_rate': 'Tasa de aprobacion (%)',
    'validated_executions': 'Ejecuciones validadas por docente',
    'pending_review_executions': 'Ejecuciones pendientes de revision',
    'rejected_executions': 'Ejecuciones rechazadas',
    'executions_with_evidence': 'Ejecuciones con evidencia',
    'functional_executions': 'Ejecuciones funcionales',
    'confirmation_executions': 'Pruebas de confirmacion',
    'regression_executions': 'Pruebas de regresion',
    'defects': 'Defectos',
    'open_defects': 'Defectos abiertos',
    'in_progress_defects': 'Defectos en progreso',
    'analysis_defects': 'Defectos en analisis',
    'pending_confirmation_defects': 'Defectos pendientes de confirmacion',
    'closed_defects': 'Defectos cerrados',
    'critical_defects': 'Defectos criticos',
    'high_defects': 'Defectos altos',
    'medium_defects': 'Defectos medios',
    'low_defects': 'Defectos bajos',
    'defects_with_execution': 'Defectos asociados a ejecuciones',
    'defect_density': 'Densidad de defectos',
    'risks': 'Riesgos',
    'open_risks': 'Riesgos abiertos',
    'high_risks': 'Riesgos altos',
    'risks_linked_to_plan': 'Riesgos vinculados al plan',
    'risks_linked_to_requirement': 'Riesgos vinculados a requisitos',
    'executed_requirements': 'Requisitos ejecutados',
    'passed_requirements': 'Requisitos aprobados',
    'failed_requirements': 'Requisitos fallidos',
    'blocked_requirements': 'Requisitos bloqueados',
    'pending_requirements': 'Requisitos pendientes de ejecucion',
    'evidence_rate': 'Ejecuciones con evidencia (%)',
    'review_rate': 'Ejecuciones revisadas por docente (%)',
    'automation_rate': 'Cobertura automatizada (%)',
    'defect_traceability_rate': 'Defectos trazados a ejecuciones (%)',
    'traceability_index': 'Indice global de trazabilidad (%)',
}

REPORT_OBJECTIVES = {
    Report.ReportType.SUMMARY: (
        'Presentar una vision consolidada del avance del ciclo de vida de pruebas del proyecto.'
    ),
    Report.ReportType.COVERAGE: (
        'Evidenciar la trazabilidad entre requisitos y casos de prueba, identificando brechas de cobertura.'
    ),
    Report.ReportType.EXECUTION: (
        'Comunicar el estado de ejecucion de pruebas funcionales, de confirmacion y de regresion.'
    ),
    Report.ReportType.DEFECTS: (
        'Analizar el estado, severidad y trazabilidad de los defectos registrados durante las pruebas.'
    ),
}

REPORT_OBJECTIVES[Report.ReportType.FINAL] = (
    'Consolidar la calidad del proyecto mediante metricas de requisitos, cobertura, ejecucion, '
    'automatizacion, evidencias, defectos, riesgos y revision docente.'
)

REPORT_SCOPES = {
    Report.ReportType.SUMMARY: 'Requisitos, casos de prueba, ejecuciones, defectos y riesgos del proyecto.',
    Report.ReportType.COVERAGE: 'Requisitos, casos vinculados, casos pendientes y riesgos asociados a trazabilidad.',
    Report.ReportType.EXECUTION: 'Resultados de ejecucion, evidencias, revisiones docentes y tipos de prueba.',
    Report.ReportType.DEFECTS: 'Defectos por estado, severidad y relacion con ejecuciones de prueba.',
}

REPORT_SCOPES[Report.ReportType.FINAL] = (
    'Ciclo completo desde requisitos y casos hasta ejecuciones, evidencias, defectos y validacion docente.'
)

PDF_SECTION_TITLES = [
    'Identificacion del informe',
    'Alcance y objetivo',
    'Resumen ejecutivo',
    'Metricas y resultados',
    'Grafico automatico de metricas',
    'Observaciones y cierre',
]


def _percentage(part, total):
    return round((part / total) * 100) if total else 0


def _ratio(part, total):
    return round(part / total, 2) if total else 0


def _project_querysets(project):
    requirements = Requirement.objects.filter(project=project)
    test_cases = TestCase.objects.filter(test_plan__project=project)
    executions = TestExecution.objects.filter(test_case__test_plan__project=project)
    defects = Defect.objects.filter(project=project)
    risks = Incident.objects.filter(project=project)
    return requirements, test_cases, executions, defects, risks


def _high_risk_count(risks):
    return sum(1 for risk in risks if risk.risk_level == 'Alto')


def _build_summary_content(project):
    requirements, test_cases, executions, defects, risks = _project_querysets(project)
    covered_requirements = requirements.filter(test_cases__isnull=False).distinct().count()
    total_requirements = requirements.count()
    executed_cases = executions.exclude(result=TestExecution.Result.NOT_RUN).values('test_case').distinct().count()

    return {
        'project': project.name,
        'requirements': total_requirements,
        'test_cases': test_cases.count(),
        'executions': executions.count(),
        'execution_progress': _percentage(executed_cases, test_cases.count()),
        'coverage': _percentage(covered_requirements, total_requirements),
        'defects': defects.count(),
        'defect_density': _ratio(defects.count(), executed_cases),
        'open_defects': defects.filter(status=Defect.Status.OPEN).count(),
        'risks': risks.count(),
        'open_risks': risks.filter(status=Incident.Status.OPEN).count(),
        'high_risks': _high_risk_count(risks),
    }


def _build_coverage_content(project):
    requirements, test_cases, _executions, _defects, risks = _project_querysets(project)
    covered_requirements = requirements.filter(test_cases__isnull=False).distinct().count()
    total_requirements = requirements.count()
    automated_requirements = requirements.filter(automated_rules__is_active=True).distinct().count()

    return {
        'project': project.name,
        'requirements': total_requirements,
        'covered_requirements': covered_requirements,
        'uncovered_requirements': total_requirements - covered_requirements,
        'coverage': _percentage(covered_requirements, total_requirements),
        'test_cases': test_cases.count(),
        'linked_test_cases': test_cases.filter(requirement__isnull=False).count(),
        'automated_requirements': automated_requirements,
        'manual_only_requirements': max(covered_requirements - automated_requirements, 0),
        'risks_linked_to_requirement': risks.filter(requirement__isnull=False).count(),
        'risks_linked_to_plan': risks.filter(test_plan__isnull=False).count(),
    }


def _build_defects_content(project):
    _requirements, _test_cases, executions, defects, _risks = _project_querysets(project)
    executed_cases = executions.exclude(result=TestExecution.Result.NOT_RUN).values('test_case').distinct().count()

    return {
        'project': project.name,
        'defects': defects.count(),
        'open_defects': defects.filter(status=Defect.Status.OPEN).count(),
        'in_progress_defects': defects.filter(status=Defect.Status.IN_PROGRESS).count(),
        'analysis_defects': defects.filter(status=Defect.Status.ANALYSIS).count(),
        'pending_confirmation_defects': defects.filter(status=Defect.Status.PENDING_CONFIRMATION).count(),
        'closed_defects': defects.filter(status=Defect.Status.CLOSED).count(),
        'critical_defects': defects.filter(severity=Defect.Severity.CRITICAL).count(),
        'high_defects': defects.filter(severity=Defect.Severity.HIGH).count(),
        'medium_defects': defects.filter(severity=Defect.Severity.MEDIUM).count(),
        'low_defects': defects.filter(severity=Defect.Severity.LOW).count(),
        'defects_with_execution': defects.filter(execution__isnull=False).count(),
        'defect_density': _ratio(defects.count(), executed_cases),
    }


def _build_execution_content(project):
    _requirements, test_cases, executions, defects, risks = _project_querysets(project)
    passed = executions.filter(result=TestExecution.Result.PASSED).count()
    failed = executions.filter(result=TestExecution.Result.FAILED).count()
    blocked = executions.filter(result=TestExecution.Result.BLOCKED).count()
    errors = executions.filter(result=TestExecution.Result.ERROR).count()
    not_run = executions.filter(result=TestExecution.Result.NOT_RUN).count()
    total_executions = executions.count()
    executed = total_executions - not_run
    executed_cases = executions.exclude(result=TestExecution.Result.NOT_RUN).values('test_case').distinct().count()

    return {
        'project': project.name,
        'test_cases': test_cases.count(),
        'executions': total_executions,
        'passed_executions': passed,
        'failed_executions': failed,
        'blocked_executions': blocked,
        'error_executions': errors,
        'manual_executions': executions.filter(execution_mode=TestExecution.ExecutionMode.MANUAL).count(),
        'semi_automated_executions': executions.filter(
            execution_mode=TestExecution.ExecutionMode.SEMI_AUTOMATED
        ).count(),
        'not_run_executions': not_run,
        'execution_progress': _percentage(executed_cases, test_cases.count()),
        'success_rate': _percentage(passed, executed),
        'validated_executions': executions.filter(review_status=TestExecution.ReviewStatus.VALIDATED).count(),
        'pending_review_executions': executions.filter(review_status=TestExecution.ReviewStatus.PENDING).count(),
        'rejected_executions': executions.filter(review_status=TestExecution.ReviewStatus.REJECTED).count(),
        'executions_with_evidence': executions.filter(
            Q(evidence__isnull=False) & ~Q(evidence='')
            | Q(automated_results__screenshot__isnull=False) & ~Q(automated_results__screenshot='')
        ).distinct().count(),
        'functional_executions': executions.filter(execution_type=TestExecution.ExecutionType.NORMAL).count(),
        'confirmation_executions': executions.filter(execution_type=TestExecution.ExecutionType.CONFIRMATION).count(),
        'regression_executions': executions.filter(execution_type=TestExecution.ExecutionType.REGRESSION).count(),
        'defects_with_execution': defects.filter(execution__isnull=False).count(),
        'automatic_defects': defects.filter(
            execution__execution_mode=TestExecution.ExecutionMode.SEMI_AUTOMATED
        ).count(),
        'defect_density': _ratio(defects.count(), executed_cases),
        'risks': risks.count(),
        'high_risks': _high_risk_count(risks),
    }


def _requirement_execution_metrics(requirements):
    metrics = {
        'executed_requirements': 0,
        'passed_requirements': 0,
        'failed_requirements': 0,
        'blocked_requirements': 0,
        'pending_requirements': 0,
    }
    for requirement in requirements.prefetch_related('test_cases__executions'):
        latest_results = []
        has_execution = False
        for test_case in requirement.test_cases.all():
            latest_execution = test_case.executions.first()
            if latest_execution:
                has_execution = True
                latest_results.append(latest_execution.result)
            else:
                latest_results.append(TestExecution.Result.NOT_RUN)

        if has_execution:
            metrics['executed_requirements'] += 1
        if TestExecution.Result.FAILED in latest_results:
            metrics['failed_requirements'] += 1
        elif any(result in {TestExecution.Result.BLOCKED, TestExecution.Result.ERROR} for result in latest_results):
            metrics['blocked_requirements'] += 1
        elif latest_results and all(result == TestExecution.Result.PASSED for result in latest_results):
            metrics['passed_requirements'] += 1
        else:
            metrics['pending_requirements'] += 1
    return metrics


def _build_final_content(project):
    requirements, _test_cases, executions, defects, _risks = _project_querysets(project)
    summary = _build_summary_content(project)
    coverage = _build_coverage_content(project)
    execution = _build_execution_content(project)
    defect_metrics = _build_defects_content(project)
    requirement_metrics = _requirement_execution_metrics(requirements)

    total_executions = execution['executions']
    reviewed_executions = (
        execution['validated_executions']
        + execution['rejected_executions']
        + executions.filter(review_status=TestExecution.ReviewStatus.NEEDS_FIX).count()
    )
    evidence_rate = _percentage(execution['executions_with_evidence'], total_executions)
    review_rate = _percentage(reviewed_executions, total_executions)
    automation_rate = _percentage(coverage['automated_requirements'], coverage['requirements'])
    requirement_execution_rate = _percentage(
        requirement_metrics['executed_requirements'],
        coverage['requirements'],
    )
    defect_traceability_rate = _percentage(
        defect_metrics['defects_with_execution'],
        defect_metrics['defects'],
    ) if defect_metrics['defects'] else 100
    traceability_index = round(
        (
            coverage['coverage']
            + requirement_execution_rate
            + evidence_rate
            + review_rate
            + defect_traceability_rate
        ) / 5
    )

    return {
        'project': project.name,
        'requirements': coverage['requirements'],
        **requirement_metrics,
        'covered_requirements': coverage['covered_requirements'],
        'uncovered_requirements': coverage['uncovered_requirements'],
        'coverage': coverage['coverage'],
        'automated_requirements': coverage['automated_requirements'],
        'manual_only_requirements': coverage['manual_only_requirements'],
        'automation_rate': automation_rate,
        'test_cases': execution['test_cases'],
        'executions': total_executions,
        'passed_executions': execution['passed_executions'],
        'failed_executions': execution['failed_executions'],
        'blocked_executions': execution['blocked_executions'],
        'error_executions': execution['error_executions'],
        'not_run_executions': execution['not_run_executions'],
        'manual_executions': execution['manual_executions'],
        'semi_automated_executions': execution['semi_automated_executions'],
        'execution_progress': execution['execution_progress'],
        'success_rate': execution['success_rate'],
        'executions_with_evidence': execution['executions_with_evidence'],
        'evidence_rate': evidence_rate,
        'validated_executions': execution['validated_executions'],
        'pending_review_executions': execution['pending_review_executions'],
        'rejected_executions': execution['rejected_executions'],
        'review_rate': review_rate,
        'defects': defect_metrics['defects'],
        'open_defects': defect_metrics['open_defects'],
        'in_progress_defects': defect_metrics['in_progress_defects'],
        'closed_defects': defect_metrics['closed_defects'],
        'critical_defects': defect_metrics['critical_defects'],
        'high_defects': defect_metrics['high_defects'],
        'medium_defects': defect_metrics['medium_defects'],
        'low_defects': defect_metrics['low_defects'],
        'automatic_defects': execution['automatic_defects'],
        'defect_traceability_rate': defect_traceability_rate,
        'risks': summary['risks'],
        'open_risks': summary['open_risks'],
        'high_risks': summary['high_risks'],
        'traceability_index': traceability_index,
    }


REPORT_CONTENT_BUILDERS = {
    Report.ReportType.SUMMARY: _build_summary_content,
    Report.ReportType.COVERAGE: _build_coverage_content,
    Report.ReportType.DEFECTS: _build_defects_content,
    Report.ReportType.EXECUTION: _build_execution_content,
    Report.ReportType.FINAL: _build_final_content,
}


def build_report_content(report):
    project = report.project
    builder = REPORT_CONTENT_BUILDERS.get(report.report_type, _build_summary_content)
    return builder(project)


def _content_value(report, key, default=0):
    value = report.content.get(key, default)
    return value if value is not None else default


def _chart_group(title, items):
    max_value = max([value for _label, value, _tone in items] + [1])
    return {
        'title': title,
        'items': [
            {
                'label': label,
                'value': value,
                'tone': tone,
                'percent': _percentage(value, max_value),
            }
            for label, value, tone in items
        ],
    }


def build_final_chart_groups(report):
    return [
        _chart_group(
            'Estado de requisitos segun ultima ejecucion',
            [
                ('Aprobados', _content_value(report, 'passed_requirements'), 'success'),
                ('Fallidos', _content_value(report, 'failed_requirements'), 'danger'),
                ('Bloqueados', _content_value(report, 'blocked_requirements'), 'warning'),
                ('Pendientes', _content_value(report, 'pending_requirements'), 'muted'),
            ],
        ),
        _chart_group(
            'Estado de ejecuciones',
            [
                ('PASS', _content_value(report, 'passed_executions'), 'success'),
                ('FAIL', _content_value(report, 'failed_executions'), 'danger'),
                ('BLOCKED', _content_value(report, 'blocked_executions'), 'warning'),
                ('ERROR', _content_value(report, 'error_executions'), 'danger'),
                ('No ejecutadas', _content_value(report, 'not_run_executions'), 'muted'),
            ],
        ),
        _chart_group(
            'Modo de ejecucion',
            [
                ('Manual', _content_value(report, 'manual_executions'), 'brand'),
                ('Semi-automatizada', _content_value(report, 'semi_automated_executions'), 'success'),
            ],
        ),
        _chart_group(
            'Defectos por severidad',
            [
                ('Criticos', _content_value(report, 'critical_defects'), 'danger'),
                ('Altos', _content_value(report, 'high_defects'), 'warning'),
                ('Medios', _content_value(report, 'medium_defects'), 'brand'),
                ('Bajos', _content_value(report, 'low_defects'), 'muted'),
            ],
        ),
    ]


def build_final_quality_indicators(report):
    return [
        {'label': 'Cobertura de requisitos', 'value': _content_value(report, 'coverage'), 'tone': 'success'},
        {'label': 'Avance de ejecucion', 'value': _content_value(report, 'execution_progress'), 'tone': 'brand'},
        {'label': 'Tasa de aprobacion', 'value': _content_value(report, 'success_rate'), 'tone': 'success'},
        {'label': 'Evidencia registrada', 'value': _content_value(report, 'evidence_rate'), 'tone': 'brand'},
        {'label': 'Revision docente', 'value': _content_value(report, 'review_rate'), 'tone': 'warning'},
        {'label': 'Defectos trazados', 'value': _content_value(report, 'defect_traceability_rate'), 'tone': 'success'},
        {'label': 'Cobertura automatizada', 'value': _content_value(report, 'automation_rate'), 'tone': 'brand'},
        {'label': 'Indice global de trazabilidad', 'value': _content_value(report, 'traceability_index'), 'tone': 'success'},
    ]


def build_final_pie_groups(report):
    groups = [
        {
            'title': 'Distribucion de resultados de ejecucion',
            'items': [
                {'label': 'PASS', 'value': _content_value(report, 'passed_executions'), 'color': '#24936e'},
                {'label': 'FAIL', 'value': _content_value(report, 'failed_executions'), 'color': '#d1495b'},
                {'label': 'BLOCKED', 'value': _content_value(report, 'blocked_executions'), 'color': '#d99b2b'},
                {'label': 'ERROR', 'value': _content_value(report, 'error_executions'), 'color': '#7b61a8'},
            ],
        },
        {
            'title': 'Cobertura de requisitos',
            'items': [
                {'label': 'Cubiertos', 'value': _content_value(report, 'covered_requirements'), 'color': '#2474b5'},
                {'label': 'Sin cobertura', 'value': _content_value(report, 'uncovered_requirements'), 'color': '#b8c4cf'},
            ],
        },
        {
            'title': 'Modalidad de ejecucion',
            'items': [
                {'label': 'Manual', 'value': _content_value(report, 'manual_executions'), 'color': '#2474b5'},
                {'label': 'Semi-automatizada', 'value': _content_value(report, 'semi_automated_executions'), 'color': '#24936e'},
            ],
        },
    ]
    for group in groups:
        total = sum(item['value'] for item in group['items'])
        current = 0
        stops = []
        for item in group['items']:
            item['percent'] = round((item['value'] / total) * 100) if total else 0
            start = current
            current += item['percent']
            stops.append(f"{item['color']} {start}% {current}%")
        group['total'] = total
        group['gradient'] = ', '.join(stops) if total else '#e7edf3 0% 100%'
    return groups


def build_pdf_chart_data(report):
    if report.report_type == Report.ReportType.FINAL:
        return [
            ('Req. aprobados', _content_value(report, 'passed_requirements')),
            ('Req. fallidos', _content_value(report, 'failed_requirements')),
            ('Req. bloqueados', _content_value(report, 'blocked_requirements')),
            ('Req. pendientes', _content_value(report, 'pending_requirements')),
        ]
    if report.report_type == Report.ReportType.COVERAGE:
        return [
            ('Cubiertos', _content_value(report, 'covered_requirements')),
            ('Sin cobertura', _content_value(report, 'uncovered_requirements')),
        ]
    if report.report_type == Report.ReportType.EXECUTION:
        return [
            ('Aprobadas', _content_value(report, 'passed_executions')),
            ('Fallidas', _content_value(report, 'failed_executions')),
            ('Bloqueadas', _content_value(report, 'blocked_executions')),
            ('No ejecutadas', _content_value(report, 'not_run_executions')),
            ('Confirmacion', _content_value(report, 'confirmation_executions')),
            ('Regresion', _content_value(report, 'regression_executions')),
        ]
    if report.report_type == Report.ReportType.DEFECTS:
        return [
            ('Abiertos', _content_value(report, 'open_defects')),
            ('Analisis', _content_value(report, 'analysis_defects')),
            ('Correccion', _content_value(report, 'in_progress_defects')),
            ('Pend. conf.', _content_value(report, 'pending_confirmation_defects')),
            ('Cerrados', _content_value(report, 'closed_defects')),
        ]
    return [
        ('Requisitos', _content_value(report, 'requirements')),
        ('Casos', _content_value(report, 'test_cases')),
        ('Ejecuciones', _content_value(report, 'executions')),
        ('Defectos', _content_value(report, 'defects')),
        ('Riesgos', _content_value(report, 'risks')),
    ]


def build_report_summary_text(report):
    report_type = report.report_type
    if report_type == Report.ReportType.FINAL:
        return (
            f"El proyecto registra {_content_value(report, 'requirements')} requisitos y "
            f"{_content_value(report, 'test_cases')} casos de prueba. "
            f"Se ejecutaron {_content_value(report, 'executed_requirements')} requisitos: "
            f"{_content_value(report, 'passed_requirements')} aprobados, "
            f"{_content_value(report, 'failed_requirements')} fallidos y "
            f"{_content_value(report, 'blocked_requirements')} bloqueados. "
            f"La cobertura es {_content_value(report, 'coverage')}% y el indice global de trazabilidad "
            f"es {_content_value(report, 'traceability_index')}%."
        )
    if report_type == Report.ReportType.COVERAGE:
        return (
            f"La cobertura registrada es de {_content_value(report, 'coverage')}%, con "
            f"{_content_value(report, 'covered_requirements')} requisitos cubiertos y "
            f"{_content_value(report, 'uncovered_requirements')} requisitos pendientes de cobertura."
        )
    if report_type == Report.ReportType.EXECUTION:
        return (
            f"El avance de ejecucion es de {_content_value(report, 'execution_progress')}%, con "
            f"{_content_value(report, 'passed_executions')} ejecuciones aprobadas, "
            f"{_content_value(report, 'failed_executions')} fallidas y "
            f"{_content_value(report, 'blocked_executions')} bloqueadas."
        )
    if report_type == Report.ReportType.DEFECTS:
        return (
            f"Se registran {_content_value(report, 'defects')} defectos, de los cuales "
            f"{_content_value(report, 'critical_defects')} son criticos y "
            f"{_content_value(report, 'closed_defects')} se encuentran cerrados."
        )
    return (
        f"El proyecto contiene {_content_value(report, 'requirements')} requisitos, "
        f"{_content_value(report, 'test_cases')} casos de prueba, "
        f"{_content_value(report, 'executions')} ejecuciones, "
        f"{_content_value(report, 'defects')} defectos y {_content_value(report, 'risks')} riesgos."
    )


def build_pdf_sections(report):
    generated_by = 'Sistema'
    if report.generated_by:
        generated_by = report.generated_by.get_full_name() or report.generated_by.email

    base_sections = [
        {
            'title': 'Identificacion del informe',
            'items': [
                ('Informe', report.title),
                ('Tipo', report.get_report_type_display()),
                ('Proyecto', report.project.name),
                ('Generado por', generated_by),
                ('Fecha', report.created_at.strftime('%d/%m/%Y')),
            ],
        },
        {
            'title': 'Alcance y objetivo',
            'items': [
                ('Objetivo', REPORT_OBJECTIVES.get(report.report_type, REPORT_OBJECTIVES[Report.ReportType.SUMMARY])),
                ('Alcance', REPORT_SCOPES.get(report.report_type, REPORT_SCOPES[Report.ReportType.SUMMARY])),
                ('Referencia', 'Estructura alineada a buenas practicas ISTQB e ISO/IEC/IEEE 29119-3.'),
            ],
        },
        {
            'title': 'Resumen ejecutivo',
            'paragraph': build_report_summary_text(report),
        },
    ]

    if report.report_type == Report.ReportType.FINAL:
        indicators = build_final_quality_indicators(report)
        indicator_text = ' | '.join(f"{item['label']}: {item['value']}%" for item in indicators)
        chart_sections = [
            {
                'title': group['title'],
                'chart_data': [(item['label'], item['value']) for item in group['items']],
            }
            for group in build_final_chart_groups(report)
        ]
        return base_sections + [
            {
                'title': 'Indicadores globales de calidad y trazabilidad',
                'paragraph': indicator_text,
            },
            *chart_sections,
            *[
                {
                    'title': group['title'],
                    'pie_data': [(item['label'], item['value']) for item in group['items']],
                }
                for group in build_final_pie_groups(report)
            ],
            {
                'title': 'Observaciones y cierre',
                'paragraph': (
                    'El informe general final consolida las evidencias del ciclo ISTQB y permite evaluar '
                    'cobertura, ejecucion, resultados, automatizacion, defectos y revision docente.'
                ),
            },
        ]

    return base_sections + [
        {
            'title': 'Metricas y resultados',
            'items': [
                (CONTENT_LABELS.get(key, key.replace('_', ' ').title()), value)
                for key, value in report.content.items()
            ],
        },
        {
            'title': 'Grafico automatico de metricas',
            'chart_data': build_pdf_chart_data(report),
        },
        {
            'title': 'Observaciones y cierre',
            'paragraph': (
                'Este documento fue generado por la Plataforma ISTQB como evidencia de seguimiento academico '
                'del ciclo de vida de pruebas de software. La informacion debe ser revisada por el docente tutor '
                'o responsable del proyecto antes de su presentacion formal.'
            ),
        },
    ]


def build_metric_chart(chart_data):
    labels = [label for label, _value in chart_data]
    values = [int(value or 0) for _label, value in chart_data]
    max_value = max(values + [1])

    drawing = Drawing(460, 190)
    chart = VerticalBarChart()
    chart.x = 35
    chart.y = 35
    chart.height = 105
    chart.width = 390
    chart.data = [values]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_value + max(1, max_value // 5)
    chart.valueAxis.valueStep = max(1, chart.valueAxis.valueMax // 5)
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 30
    chart.categoryAxis.labels.dy = -8
    chart.bars[0].fillColor = colors.HexColor('#0b315f')
    chart.barSpacing = 2
    drawing.add(chart)
    drawing.add(String(35, 160, 'Distribucion de metricas principales', fontSize=10, fillColor=colors.HexColor('#0b315f')))
    legend_text = ' | '.join(f'{label}: {value}' for label, value in chart_data)
    drawing.add(String(35, 12, legend_text[:100], fontSize=7, fillColor=colors.HexColor('#52667a')))
    return drawing


def build_pie_chart(chart_data):
    labels = [label for label, value in chart_data if value]
    values = [value for _label, value in chart_data if value]
    if not values:
        labels = ['Sin datos']
        values = [1]

    palette = ['#24936e', '#d1495b', '#d99b2b', '#2474b5', '#7b61a8', '#8393a5']
    drawing = Drawing(460, 190)
    pie = Pie()
    pie.x = 45
    pie.y = 30
    pie.width = 125
    pie.height = 125
    pie.data = values
    pie.labels = [str(value) for value in values]
    pie.slices.strokeWidth = 0.5
    for index, _value in enumerate(values):
        pie.slices[index].fillColor = colors.HexColor(palette[index % len(palette)])
    drawing.add(pie)

    total = sum(values)
    for index, (label, value) in enumerate(zip(labels, values)):
        percent = round((value / total) * 100) if total else 0
        y = 145 - (index * 22)
        drawing.add(String(210, y, u'\u25a0', fontSize=12, fillColor=colors.HexColor(palette[index % len(palette)])))
        drawing.add(String(228, y, f'{label}: {value} ({percent}%)', fontSize=9, fillColor=colors.HexColor('#263b50')))
    return drawing


@login_required
def report_list_view(request):
    visible_projects = visible_projects_for(request.user)
    form = ReportForm(request.POST or None)
    form.fields['project'].queryset = visible_projects.order_by('name')

    if request.method == 'POST':
        readonly_redirect = redirect_if_teacher_readonly(request, 'reports:index', 'reportes')
        if readonly_redirect:
            return readonly_redirect

    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.generated_by = request.user
        report.content = build_report_content(report)
        report.save()
        log_action(
            request.user,
            'CREATE',
            'Report',
            report.pk,
            {'project_id': report.project_id, 'report_type': report.report_type, 'title': report.title},
        )
        return redirect('reports:index')

    return render(
        request,
        'reports/index.html',
        {
            'report_cards': REPORT_CARDS,
            'reports': Report.objects.select_related('project', 'generated_by').filter(project__in=visible_projects),
            'form': form,
            'show_modal': request.method == 'POST' and form.errors,
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def report_detail_view(request, pk):
    report = get_object_or_404(
        Report.objects.select_related('project', 'generated_by'),
        pk=pk,
        project__in=visible_projects_for(request.user),
    )
    is_final = report.report_type == Report.ReportType.FINAL
    final_kpis = []
    if is_final:
        final_kpis = [
            {'label': 'Requisitos', 'value': _content_value(report, 'requirements'), 'icon': 'bi-file-earmark-text'},
            {'label': 'Requisitos ejecutados', 'value': _content_value(report, 'executed_requirements'), 'icon': 'bi-play-circle'},
            {'label': 'Requisitos aprobados', 'value': _content_value(report, 'passed_requirements'), 'icon': 'bi-check-circle'},
            {'label': 'Requisitos fallidos', 'value': _content_value(report, 'failed_requirements'), 'icon': 'bi-x-circle'},
            {'label': 'Casos de prueba', 'value': _content_value(report, 'test_cases'), 'icon': 'bi-test-tube'},
            {'label': 'Ejecuciones', 'value': _content_value(report, 'executions'), 'icon': 'bi-collection-play'},
            {'label': 'Defectos', 'value': _content_value(report, 'defects'), 'icon': 'bi-bug'},
            {'label': 'Riesgos altos', 'value': _content_value(report, 'high_risks'), 'icon': 'bi-exclamation-triangle'},
        ]

    return render(
        request,
        'reports/detail.html',
        {
            'report': report,
            'content_items': [
                (CONTENT_LABELS.get(key, key.replace('_', ' ').title()), value)
                for key, value in report.content.items()
            ],
            'is_final': is_final,
            'final_kpis': final_kpis,
            'chart_groups': build_final_chart_groups(report) if is_final else [],
            'pie_groups': build_final_pie_groups(report) if is_final else [],
            'quality_indicators': build_final_quality_indicators(report) if is_final else [],
            'summary_text': build_report_summary_text(report),
        },
    )


def build_unl_pdf(buffer, report):
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name='UNLTitle',
            parent=styles['Title'],
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0b315f'),
            fontSize=16,
            leading=20,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name='UNLSubtitle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            textColor=colors.HexColor('#24496f'),
            fontSize=10,
            leading=13,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            textColor=colors.HexColor('#0b315f'),
            fontSize=12,
            leading=16,
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name='BodySmall',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontSize=9,
            leading=12,
        )
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title=report.title,
    )

    def report_logo(filename, max_width, max_height):
        image_path = settings.BASE_DIR / 'static' / 'images' / 'reports' / filename
        image = ReportLabImage(str(image_path))
        scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        return image

    institution_copy = [
        Paragraph('UNIVERSIDAD NACIONAL DE LOJA', styles['UNLTitle']),
        Paragraph('Facultad de la Energía, las Industrias y los Recursos Naturales no Renovables', styles['UNLSubtitle']),
        Paragraph('Carrera de Computación', styles['UNLSubtitle']),
        Paragraph('Plataforma ISTQB - Gestión del Ciclo de Vida de Pruebas', styles['UNLSubtitle']),
    ]
    institutional_header = Table(
        [[
            report_logo('career-logo.png', 4.1 * cm, 1.75 * cm),
            institution_copy,
            report_logo('unl-logo.png', 4.4 * cm, 1.75 * cm),
        ]],
        colWidths=[4.3 * cm, 7.4 * cm, 4.3 * cm],
    )
    institutional_header.setStyle(
        TableStyle(
            [
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LINEBELOW', (0, 0), (-1, -1), 1.2, colors.HexColor('#0b315f')),
            ]
        )
    )

    story = [institutional_header, Spacer(1, 0.35 * cm)]

    generated_by = 'Sistema'
    if report.generated_by:
        generated_by = report.generated_by.get_full_name() or report.generated_by.email

    for index, section in enumerate(build_pdf_sections(report), start=1):
        story.append(Paragraph(f'{index}. {section["title"]}', styles['SectionTitle']))

        if 'items' in section:
            rows = [['Campo', 'Detalle']]
            rows.extend(
                [
                    [Paragraph(str(label), styles['BodySmall']), Paragraph(str(value), styles['BodySmall'])]
                    for label, value in section['items']
                ]
            )
            section_table = Table(rows, colWidths=[5.3 * cm, 10.7 * cm])
            section_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b315f')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dbe7f2')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fbfe')]),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('PADDING', (0, 0), (-1, -1), 7),
                    ]
                )
            )
            story.append(section_table)

        if 'paragraph' in section:
            story.append(Paragraph(section['paragraph'], styles['BodySmall']))

        if 'chart_data' in section:
            story.append(build_metric_chart(section['chart_data']))

        if 'pie_data' in section:
            story.append(build_pie_chart(section['pie_data']))

        story.append(Spacer(1, 0.25 * cm))

    doc.build(story)
    return

    header_table = Table(
        [
            ['Informe', report.title],
            ['Tipo', report.get_report_type_display()],
            ['Proyecto', report.project.name],
            ['Generado por', generated_by],
            ['Fecha', report.created_at.strftime('%d/%m/%Y')],
        ],
        colWidths=[4 * cm, 12 * cm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eaf4fb')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0b315f')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dbe7f2')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(header_table)
    story.append(Paragraph('Resumen del reporte', styles['SectionTitle']))

    content_rows = [['Métrica', 'Valor']]
    for key, value in report.content.items():
        content_rows.append([CONTENT_LABELS.get(key, key.replace('_', ' ').title()), str(value)])

    content_table = Table(content_rows, colWidths=[8 * cm, 8 * cm])
    content_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b315f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dbe7f2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fbfe')]),
                ('PADDING', (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(content_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph('Observación institucional', styles['SectionTitle']))
    story.append(
        Paragraph(
            'Este documento fue generado por la Plataforma ISTQB como evidencia de seguimiento académico '
            'del ciclo de vida de pruebas de software. La información debe ser revisada por el docente tutor '
            'o responsable del proyecto antes de su presentación formal.',
            styles['BodySmall'],
        )
    )

    doc.build(story)


@login_required
def report_download_view(request, pk):
    report = get_object_or_404(Report, pk=pk, project__in=visible_projects_for(request.user))
    filename = f'reporte-unl-{report.id}.pdf'
    ReportDownload.objects.create(
        report=report,
        downloaded_by=request.user,
        project=report.project,
        filename=filename,
        metadata={'report_type': report.report_type, 'title': report.title},
    )
    log_action(
        request.user,
        'DOWNLOAD',
        'Report',
        report.pk,
        {'project_id': report.project_id, 'filename': filename, 'report_type': report.report_type},
    )
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    build_unl_pdf(response, report)
    return response


@login_required
def report_delete_view(request, pk):
    readonly_redirect = redirect_if_teacher_readonly(request, 'reports:index', 'reportes')
    if readonly_redirect:
        return readonly_redirect

    report = get_object_or_404(
        Report,
        pk=pk,
        project__in=visible_projects_for(request.user),
    )

    if request.method == 'POST':
        log_action(
            request.user,
            'DELETE',
            'Report',
            report.pk,
            {'project_id': report.project_id, 'report_type': report.report_type, 'title': report.title},
        )
        report.delete()
        messages.success(request, 'Reporte eliminado correctamente.')
    else:
        messages.error(request, 'La eliminacion debe confirmarse desde el listado.')

    return redirect('reports:index')

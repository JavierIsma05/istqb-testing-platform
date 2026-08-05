import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Image as ReportLabImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.audit.services import log_action
from apps.core.permissions import can_manage_artifacts, redirect_if_teacher_readonly, visible_projects_for
from apps.incidents.models import Incident
from apps.phases.models import TestingPhase
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.traceability.models import TraceabilityLink

from .forms import ReportForm
from .models import Report, ReportDownload


PLAN_REPORT_TYPES = {
    'plan': {
        'title': 'Informe del Plan de Pruebas',
        'url_name': 'reports:plan-report-detail',
    },
    'casos': {
        'title': 'Informe de Casos de Prueba',
        'url_name': 'reports:plan-casos',
    },
    'ejecuciones': {
        'title': 'Informe de Ejecuciones',
        'url_name': 'reports:plan-ejecuciones',
    },
    'defectos': {
        'title': 'Informe de Defectos',
        'url_name': 'reports:plan-defectos',
    },
    'final': {
        'title': 'Informe Final de Pruebas',
        'url_name': 'reports:plan-final',
    },
}

REPORT_CARDS = [
    {
        'number': 1,
        'title': 'Informe del Plan de Pruebas',
        'description': 'Objetivo, alcance, estrategia, criterios, recursos y riesgos asociados del plan. 1-2 páginas.',
        'icon': 'bi-clipboard-check',
        'tone': 'brand',
        'type': 'plan',
    },
    {
        'number': 2,
        'title': 'Informe de Casos de Prueba',
        'description': 'Catálogo de casos con requisitos vinculados, prioridad, técnica y pasos de ejecución.',
        'icon': 'bi-list-check',
        'tone': 'brand',
        'type': 'casos',
    },
    {
        'number': 3,
        'title': 'Informe de Ejecuciones',
        'description': 'Resultados de ejecución, avance del ciclo, tasa de aprobación y distribución por estado.',
        'icon': 'bi-collection-play',
        'tone': 'success',
        'type': 'ejecuciones',
    },
    {
        'number': 4,
        'title': 'Informe de Defectos',
        'description': 'Defectos por severidad y estado, con detalle de cada hallazgo y su responsable.',
        'icon': 'bi-bug',
        'tone': 'danger',
        'type': 'defectos',
    },
    {
        'number': 5,
        'title': 'Informe Final de Pruebas',
        'description': 'Resumen ejecutivo con métricas consolidadas, trazabilidad, conclusiones y recomendaciones.',
        'icon': 'bi-file-earmark-bar-graph',
        'tone': 'success',
        'type': 'final',
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
    'error_executions': 'Ejecuciones con error técnico',
    'manual_executions': 'Ejecuciones manuales',
    'automated_executions': 'Ejecuciones automatizadas',
    'automated_requirements': 'Requisitos con reglas automatizadas',
    'manual_only_requirements': 'Requisitos cubiertos solo manualmente',
    'automatic_defects': 'Defectos generados por automatizacion',
    'execution_progress': 'Avance de ejecución (%)',
    'success_rate': 'Tasa de aprobacion (%)',
    'validated_executions': 'Ejecuciones validadas por docente',
    'pending_review_executions': 'Ejecuciones pendientes de revisión',
    'rejected_executions': 'Ejecuciones rechazadas',
    'executions_with_evidence': 'Ejecuciones con evidencia',
    'functional_executions': 'Ejecuciones funcionales',
    'confirmation_executions': 'Pruebas de confirmacion',
    'regression_executions': 'Pruebas de regresion',
    'defects': 'Defectos',
    'open_defects': 'Defectos abiertos',
    'in_progress_defects': 'Defectos en progreso',
    'resolved_defects': 'Defectos resueltos',
    'reopened_defects': 'Defectos reabiertos',
    'closed_defects': 'Defectos cerrados',
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
    'pending_requirements': 'Requisitos pendientes de ejecución',
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
        'Comunicar el estado de ejecución de pruebas funcionales, de confirmación y de regresión.'
    ),
    Report.ReportType.DEFECTS: (
        'Analizar el estado, severidad y trazabilidad de los defectos registrados durante las pruebas.'
    ),
}

REPORT_OBJECTIVES[Report.ReportType.FINAL] = (
    'Consolidar la calidad del proyecto mediante métricas de requisitos, cobertura, ejecución, '
    'automatización, evidencias, defectos, riesgos y revisión docente.'
)

REPORT_SCOPES = {
    Report.ReportType.SUMMARY: 'Requisitos, casos de prueba, ejecuciones, defectos y riesgos del proyecto.',
    Report.ReportType.COVERAGE: 'Requisitos, casos vinculados, casos pendientes y riesgos asociados a trazabilidad.',
    Report.ReportType.EXECUTION: 'Resultados de ejecución, evidencias, revisiones docentes y tipos de prueba.',
    Report.ReportType.DEFECTS: 'Defectos por estado, severidad y relación con ejecuciones de prueba.',
}

REPORT_SCOPES[Report.ReportType.FINAL] = (
    'Ciclo completo desde requisitos y casos hasta ejecuciones, evidencias, defectos y validación docente.'
)

PDF_SECTION_TITLES = [
    'Identificación del informe',
    'Alcance y objetivo',
    'Resumen ejecutivo',
    'Métricas y resultados',
    'Gráfico automático de métricas',
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


def _covered_requirement_ids(requirements):
    direct_ids = set(
        requirements.filter(test_cases__isnull=False).values_list('id', flat=True)
    )
    linked_ids = set(
        TraceabilityLink.objects.filter(requirement__in=requirements).values_list('requirement_id', flat=True)
    )
    return direct_ids | linked_ids


def _requirement_test_cases(requirement):
    direct_cases = list(requirement.test_cases.all())
    linked_cases = [link.test_case for link in requirement.traceability_links.all()]
    return list({test_case.id: test_case for test_case in direct_cases + linked_cases}.values())


def _high_risk_count(risks):
    return sum(1 for risk in risks if risk.risk_level == 'Alto')


def _build_summary_content(project):
    requirements, test_cases, executions, defects, risks = _project_querysets(project)
    covered_requirements = len(_covered_requirement_ids(requirements))
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
    covered_requirement_ids = _covered_requirement_ids(requirements)
    covered_requirements = len(covered_requirement_ids)
    total_requirements = requirements.count()
    automated_requirements = len(set(
        requirements.filter(test_cases__automated_rules__is_active=True).values_list('id', flat=True)
    ) | set(
        TraceabilityLink.objects.filter(
            requirement__in=requirements,
            test_case__automated_rules__is_active=True,
        ).values_list('requirement_id', flat=True)
    ))

    return {
        'project': project.name,
        'requirements': total_requirements,
        'covered_requirements': covered_requirements,
        'uncovered_requirements': total_requirements - covered_requirements,
        'coverage': _percentage(covered_requirements, total_requirements),
        'test_cases': test_cases.count(),
        'linked_test_cases': test_cases.filter(
            Q(requirement__isnull=False) | Q(traceability_links__isnull=False)
        ).distinct().count(),
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
        'resolved_defects': defects.filter(status=Defect.Status.RESOLVED).count(),
        'reopened_defects': defects.filter(status=Defect.Status.REOPENED).count(),
        'closed_defects': defects.filter(status=Defect.Status.CLOSED).count(),
        'critical_defects': defects.filter(severity=Defect.Severity.HIGH).count(),
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
        'automated_executions': executions.filter(
            execution_mode=TestExecution.ExecutionMode.AUTOMATED
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
            execution__execution_mode=TestExecution.ExecutionMode.AUTOMATED
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
    for requirement in requirements.prefetch_related(
        'test_cases__executions',
        'traceability_links__test_case__executions',
    ):
        latest_results = []
        has_execution = False
        for test_case in _requirement_test_cases(requirement):
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


def build_final_findings(report):
    findings = []
    if _content_value(report, 'coverage') < 100:
        findings.append(
            f"Existen {_content_value(report, 'uncovered_requirements')} requisitos sin cobertura de casos de prueba."
        )
    else:
        findings.append('Todos los requisitos tienen al menos un caso de prueba trazado.')

    if _content_value(report, 'failed_executions'):
        findings.append(
            f"Se registran {_content_value(report, 'failed_executions')} ejecuciones fallidas que requieren seguimiento."
        )

    if _content_value(report, 'pending_review_executions'):
        findings.append(
            f"Quedan {_content_value(report, 'pending_review_executions')} ejecuciones pendientes de revisión docente."
        )

    if _content_value(report, 'high_risks'):
        findings.append(
            f"El plan mantiene {_content_value(report, 'high_risks')} riesgos altos que deben mantenerse visibles en la priorizacion."
        )

    if not findings:
        findings.append('No se identifican brechas criticas con los datos registrados.')
    return findings


def build_final_recommendations(report):
    recommendations = []
    if _content_value(report, 'pending_review_executions'):
        recommendations.append('Validar o rechazar las ejecuciones pendientes para cerrar formalmente el ciclo de prueba.')
    if _content_value(report, 'failed_executions'):
        recommendations.append('Priorizar la corrección de defectos asociados a ejecuciones fallidas y ejecutar pruebas de confirmación.')
    if _content_value(report, 'high_risks'):
        recommendations.append('Revisar la estrategia de mitigacion de riesgos altos antes de aprobar el cierre del plan.')
    if _content_value(report, 'evidence_rate') < 100:
        recommendations.append('Adjuntar evidencia en las ejecuciones que no cuentan con soporte documental.')
    if not recommendations:
        recommendations.append('Mantener el monitoreo de regresion y conservar las evidencias como soporte de cierre.')
    return recommendations


def build_final_project_conclusion(report):
    verdict = report.content.get('final_verdict', 'Pendiente')
    coverage = _content_value(report, 'coverage')
    success_rate = _content_value(report, 'success_rate')
    traceability_index = _content_value(report, 'traceability_index')
    passed = _content_value(report, 'passed_executions')
    failed = _content_value(report, 'failed_executions')
    defects = _content_value(report, 'defects')
    open_defects = _content_value(report, 'open_defects')
    high_risks = _content_value(report, 'high_risks')
    pending_review = _content_value(report, 'pending_review_executions')
    review_rate = _content_value(report, 'review_rate')

    if verdict == 'APROBADO':
        decision = (
            'El plan de pruebas y el ciclo de vida ejecutado generan el resultado esperado, '
            'porque los criterios de salida fueron cumplidos sin observaciones criticas.'
        )
    elif verdict == 'APROBADO CON OBSERVACIONES':
        decision = (
            'El plan de pruebas y el ciclo de vida ejecutado generan parcialmente el resultado esperado: '
            'la cobertura y la ejecución permiten sustentar la calidad funcional alcanzada, '
            'pero aun existen elementos de control que deben cerrarse antes de una aprobacion final sin reservas.'
        )
    else:
        decision = (
            'El plan de pruebas y el ciclo de vida ejecutado no generan todavia el resultado esperado, '
            'porque uno o mas criterios de salida no se cumplen con la evidencia registrada.'
        )

    evidence = (
        f"Se alcanzo una cobertura de requisitos de {coverage}% y una tasa de aprobacion de {success_rate}%, "
        f"con {passed} ejecuciones aprobadas y {failed} fallidas. "
        f"El indice global de trazabilidad es {traceability_index}%, lo que muestra el grado de conexion "
        f"entre requisitos, casos, ejecuciones, defectos y riesgos."
    )
    reservations = (
        f"Como observaciones principales, permanecen {open_defects} defectos abiertos de {defects} registrados, "
        f"{high_risks} riesgos altos y {pending_review} ejecuciones pendientes de revisión docente "
        f"(revisión completada: {review_rate}%)."
    )
    closure = (
        f"Por tanto, el estado general del proyecto es: {verdict}. "
        'El resultado es util como evidencia academica y tecnica del proceso ISTQB aplicado, '
        'pero la decisión de cierre debe considerar la resolución de defectos, la mitigación de riesgos '
        'y la revisión formal de las ejecuciones restantes.'
    )
    return f'{decision} {evidence} {reservations} {closure}'


def _module_coverage(project):
    requirements = Requirement.objects.filter(project=project).prefetch_related(
        'test_cases',
        'traceability_links__test_case',
    ).order_by('title', 'code')
    modules = {}
    covered_ids = _covered_requirement_ids(requirements)
    for requirement in requirements:
        module = requirement.title or 'Sin módulo'
        modules.setdefault(module, {'module': module, 'total': 0, 'covered': 0, 'coverage': 0})
        modules[module]['total'] += 1
        if requirement.id in covered_ids:
            modules[module]['covered'] += 1
    for row in modules.values():
        row['coverage'] = _percentage(row['covered'], row['total'])
    return list(modules.values())


def _traceability_matrix_rows(project, limit=80):
    rows = []
    requirements = Requirement.objects.filter(project=project).prefetch_related(
        'test_cases__executions__defects',
        'traceability_links__test_case__executions__defects',
    ).order_by('code')
    for requirement in requirements:
        test_cases = _requirement_test_cases(requirement)
        if not test_cases:
            rows.append({
                'requirement': requirement.code,
                'test_case': '-',
                'execution': '-',
                'defect': '-',
                'status': 'SIN COBERTURA',
            })
            continue
        for test_case in test_cases:
            latest_execution = test_case.executions.first()
            defects = []
            if latest_execution:
                defects = list(latest_execution.defects.all())
            rows.append({
                'requirement': requirement.code,
                'test_case': test_case.code,
                'execution': f'EXE-{latest_execution.id:03d}' if latest_execution else '-',
                'defect': ', '.join(defect.code for defect in defects) if defects else '-',
                'status': latest_execution.result if latest_execution else 'NO EJECUTADA',
            })
            if len(rows) >= limit:
                return rows
    return rows


def _cycle_statuses(project, coverage, executed_cases, total_cases, defects_count):
    real_phases = TestingPhase.objects.filter(project=project).order_by('order')
    if real_phases.exists():
        rows = [
            {'phase': phase.name, 'status': phase.get_status_display()}
            for phase in real_phases
        ]
        progress = _percentage(
            sum(1 for phase in real_phases if phase.status == TestingPhase.Status.DONE),
            real_phases.count(),
        )
        return rows, progress

    plans = TestPlan.objects.filter(project=project)
    phases = [
        ('Requisitos', Requirement.objects.filter(project=project).exists()),
        ('Planificación', plans.exists()),
        ('Diseño de casos', total_cases > 0),
        ('Ejecución', executed_cases > 0),
        ('Gestión de defectos', defects_count > 0),
        ('Cierre', coverage == 100 and executed_cases == total_cases and total_cases > 0),
    ]
    rows = []
    for name, complete in phases:
        if complete:
            status = 'Completada'
        elif rows and rows[-1]['status'] == 'Completada':
            status = 'En progreso'
        else:
            status = 'Pendiente'
        rows.append({'phase': name, 'status': status})
    progress = _percentage(sum(1 for row in rows if row['status'] == 'Completada'), len(rows))
    return rows, progress


def _teacher_review_summary(project, requirements, executions, defects, risks):
    reviewed_executions = executions.exclude(review_status=TestExecution.ReviewStatus.PENDING).count()
    return [
        {
            'section': 'Requisitos',
            'reviewed': requirements.filter(status=Requirement.Status.APPROVED).count(),
            'total': requirements.count(),
            'pending': requirements.exclude(status=Requirement.Status.APPROVED).count(),
        },
        {
            'section': 'Ejecuciones',
            'reviewed': reviewed_executions,
            'total': executions.count(),
            'pending': executions.filter(review_status=TestExecution.ReviewStatus.PENDING).count(),
        },
        {
            'section': 'Defectos',
            'reviewed': defects.exclude(status=Defect.Status.OPEN).count(),
            'total': defects.count(),
            'pending': defects.filter(status=Defect.Status.OPEN).count(),
        },
        {
            'section': 'Riesgos',
            'reviewed': risks.exclude(status=Incident.Status.OPEN).count(),
            'total': risks.count(),
            'pending': risks.filter(status=Incident.Status.OPEN).count(),
        },
        {
            'section': 'Fases',
            'reviewed': TestingPhase.objects.filter(project=project, status=TestingPhase.Status.DONE).count(),
            'total': TestingPhase.objects.filter(project=project).count(),
            'pending': TestingPhase.objects.filter(project=project).exclude(status=TestingPhase.Status.DONE).count(),
        },
    ]


def _execution_status_distribution(executions):
    total = executions.count()
    statuses = [
        ('PASS', executions.filter(result=TestExecution.Result.PASSED).count()),
        ('FAIL', executions.filter(result=TestExecution.Result.FAILED).count()),
        ('BLOCKED', executions.filter(result=TestExecution.Result.BLOCKED).count()),
        ('ERROR', executions.filter(result=TestExecution.Result.ERROR).count()),
        ('NO EJECUTADAS', executions.filter(result=TestExecution.Result.NOT_RUN).count()),
    ]
    return [
        {'status': label, 'count': count, 'percent': _percentage(count, total)}
        for label, count in statuses
    ]


def _defect_severity_rows(defects):
    return [
        {'severity': 'Alto', 'count': defects.filter(severity=Defect.Severity.HIGH).count()},
        {'severity': 'Medio', 'count': defects.filter(severity=Defect.Severity.MEDIUM).count()},
        {'severity': 'Bajo', 'count': defects.filter(severity=Defect.Severity.LOW).count()},
    ]


def _defect_status_rows(defects):
    return [
        {'status': label, 'count': defects.filter(status=value).count()}
        for value, label in Defect.Status.choices
    ]


def _risk_matrix_rows(risks):
    probability_labels = {
        Incident.Probability.LOW: 'Baja',
        Incident.Probability.MEDIUM: 'Media',
        Incident.Probability.HIGH: 'Alta',
    }
    impact_values = [
        (Incident.Impact.LOW, 'Bajo'),
        (Incident.Impact.MEDIUM, 'Medio'),
        (Incident.Impact.HIGH, 'Alto'),
    ]
    return [
        {
            'probability': label,
            'low': risks.filter(probability=value, impact=Incident.Impact.LOW).count(),
            'medium': risks.filter(probability=value, impact=Incident.Impact.MEDIUM).count(),
            'high': risks.filter(probability=value, impact=Incident.Impact.HIGH).count(),
        }
        for value, label in probability_labels.items()
    ], [label for _value, label in impact_values]


def _execution_history_rows(project, limit=30):
    executions = TestExecution.objects.filter(
        test_case__test_plan__project=project
    ).select_related('test_case', 'executed_by').order_by('-executed_at', '-created_at')[:limit]
    return [
        {
            'date': execution.executed_at.strftime('%d/%m/%Y %H:%M') if execution.executed_at else '-',
            'test_case': execution.test_case.code,
            'result': execution.result,
            'executor': (
                execution.executed_by.get_full_name()
                or execution.executed_by.email
                if execution.executed_by
                else 'Sistema'
            ),
        }
        for execution in executions
    ]


def _exit_criteria(project, coverage, success_rate, critical_defects):
    plan = TestPlan.objects.filter(project=project).order_by('-created_at').first()
    if not plan:
        return [], False, 'NO APROBADO'
    rows = [
        {
            'criterion': 'Cobertura mínima',
            'target': f'{plan.minimum_coverage_percentage}%',
            'result': f'{coverage}%',
            'passed': coverage >= plan.minimum_coverage_percentage,
        },
        {
            'criterion': 'Aprobación mínima',
            'target': f'{plan.minimum_pass_percentage}%',
            'result': f'{success_rate}%',
            'passed': success_rate >= plan.minimum_pass_percentage,
        },
        {
            'criterion': 'Defectos críticos permitidos',
            'target': str(plan.maximum_critical_defects),
            'result': str(critical_defects),
            'passed': critical_defects <= plan.maximum_critical_defects,
        },
    ]
    all_passed = all(row['passed'] for row in rows)
    if all_passed and critical_defects == 0:
        verdict = 'APROBADO'
    elif all_passed or coverage >= plan.minimum_coverage_percentage:
        verdict = 'APROBADO CON OBSERVACIONES'
    else:
        verdict = 'NO APROBADO'
    return rows, all_passed, verdict


def _build_final_content(project):
    requirements, test_cases, executions, defects, risks = _project_querysets(project)
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
    executed_cases = executions.exclude(result=TestExecution.Result.NOT_RUN).values('test_case').distinct().count()
    detection_rate = _percentage(defect_metrics['defects'], total_executions)
    correction_rate = _percentage(defect_metrics['closed_defects'], defect_metrics['defects'])
    cycle_statuses, cycle_progress = _cycle_statuses(
        project,
        coverage['coverage'],
        executed_cases,
        test_cases.count(),
        defect_metrics['defects'],
    )
    exit_criteria, exit_criteria_passed, final_verdict = _exit_criteria(
        project,
        coverage['coverage'],
        execution['success_rate'],
        defect_metrics['critical_defects'],
    )
    if exit_criteria_passed and (
        defect_metrics['open_defects']
        or summary['high_risks']
        or execution['pending_review_executions']
    ):
        final_verdict = 'APROBADO CON OBSERVACIONES'
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
        'automated_executions': execution['automated_executions'],
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
        'module_coverage': _module_coverage(project),
        'traceability_matrix': _traceability_matrix_rows(project),
        'cycle_statuses': cycle_statuses,
        'cycle_progress': cycle_progress,
        'execution_status_distribution': _execution_status_distribution(executions),
        'defect_severity_rows': _defect_severity_rows(defects),
        'defect_status_rows': _defect_status_rows(defects),
        'risk_matrix': _risk_matrix_rows(risks)[0],
        'risk_matrix_impacts': _risk_matrix_rows(risks)[1],
        'teacher_review_summary': _teacher_review_summary(project, requirements, executions, defects, risks),
        'quality_metrics': [
            {'metric': 'Cobertura de requisitos', 'formula': 'Requisitos cubiertos / requisitos totales', 'result': f"{coverage['coverage']}%"},
            {'metric': 'Tasa de aprobacion', 'formula': 'Aprobados / ejecutados', 'result': f"{execution['success_rate']}%"},
            {'metric': 'Densidad de defectos', 'formula': 'Defectos / casos ejecutados', 'result': defect_metrics['defect_density']},
            {'metric': 'Tasa de detección', 'formula': 'Defectos encontrados / ejecuciones', 'result': f'{detection_rate}%'},
            {'metric': 'Tasa de corrección', 'formula': 'Defectos cerrados / defectos totales', 'result': f'{correction_rate}%'},
        ],
        'evidence_summary': [
            {'metric': 'Ejecuciones con evidencia', 'value': execution['executions_with_evidence']},
            {'metric': 'Ejecuciones sin evidencia', 'value': max(total_executions - execution['executions_with_evidence'], 0)},
            {'metric': 'Porcentaje de evidencia registrada', 'value': f'{evidence_rate}%'},
        ],
        'execution_history': _execution_history_rows(project),
        'exit_criteria': exit_criteria,
        'exit_criteria_passed': exit_criteria_passed,
        'final_verdict': final_verdict,
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
            'Estado de requisitos según última ejecución',
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
            'Modo de ejecución',
            [
                ('Manual', _content_value(report, 'manual_executions'), 'brand'),
                ('Automatizada', _content_value(report, 'automated_executions'), 'success'),
            ],
        ),
        _chart_group(
            'Defectos por severidad',
            [
                ('Altos', _content_value(report, 'high_defects'), 'danger'),
                ('Medios', _content_value(report, 'medium_defects'), 'warning'),
                ('Bajos', _content_value(report, 'low_defects'), 'success'),
            ],
        ),
    ]


def build_final_quality_indicators(report):
    return [
        {'label': 'Cobertura de requisitos', 'value': _content_value(report, 'coverage'), 'tone': 'success'},
        {'label': 'Avance de ejecución', 'value': _content_value(report, 'execution_progress'), 'tone': 'brand'},
        {'label': 'Tasa de aprobacion', 'value': _content_value(report, 'success_rate'), 'tone': 'success'},
        {'label': 'Evidencia registrada', 'value': _content_value(report, 'evidence_rate'), 'tone': 'brand'},
        {'label': 'Revisión docente', 'value': _content_value(report, 'review_rate'), 'tone': 'warning'},
        {'label': 'Defectos trazados', 'value': _content_value(report, 'defect_traceability_rate'), 'tone': 'success'},
        {'label': 'Cobertura automatizada', 'value': _content_value(report, 'automation_rate'), 'tone': 'brand'},
        {'label': 'Indice global de trazabilidad', 'value': _content_value(report, 'traceability_index'), 'tone': 'success'},
    ]


def build_final_pie_groups(report):
    groups = [
        {
            'title': 'Distribución de resultados de ejecución',
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
            'title': 'Modalidad de ejecución',
            'items': [
                {'label': 'Manual', 'value': _content_value(report, 'manual_executions'), 'color': '#2474b5'},
                {'label': 'Automatizada', 'value': _content_value(report, 'automated_executions'), 'color': '#24936e'},
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
            ('En progreso', _content_value(report, 'in_progress_defects')),
            ('Resueltos', _content_value(report, 'resolved_defects')),
            ('Reabiertos', _content_value(report, 'reopened_defects')),
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
            f"es {_content_value(report, 'traceability_index')}%. "
            f"Veredicto automático: {report.content.get('final_verdict', 'Pendiente')}."
        )
    if report_type == Report.ReportType.COVERAGE:
        return (
            f"La cobertura registrada es de {_content_value(report, 'coverage')}%, con "
            f"{_content_value(report, 'covered_requirements')} requisitos cubiertos y "
            f"{_content_value(report, 'uncovered_requirements')} requisitos pendientes de cobertura."
        )
    if report_type == Report.ReportType.EXECUTION:
        return (
            f"El avance de ejecución es de {_content_value(report, 'execution_progress')}%, con "
            f"{_content_value(report, 'passed_executions')} ejecuciones aprobadas, "
            f"{_content_value(report, 'failed_executions')} fallidas y "
            f"{_content_value(report, 'blocked_executions')} bloqueadas."
        )
    if report_type == Report.ReportType.DEFECTS:
        return (
            f"Se registran {_content_value(report, 'defects')} defectos, de los cuales "
            f"{_content_value(report, 'high_defects')} son de severidad alta y "
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
    generated_at = report.created_at or timezone.now()

    base_sections = [
        {
            'title': 'Identificación del informe',
            'items': [
                ('Informe', report.title),
                ('Tipo', report.get_report_type_display()),
                ('Proyecto', report.project.name),
                ('Generado por', generated_by),
                ('Fecha', generated_at.strftime('%d/%m/%Y')),
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
        findings_text = '<br/>'.join(f'- {finding}' for finding in build_final_findings(report))
        recommendations_text = '<br/>'.join(
            f'- {recommendation}' for recommendation in build_final_recommendations(report)
        )
        module_coverage = report.content.get('module_coverage', [])
        traceability_rows = report.content.get('traceability_matrix', [])
        cycle_rows = report.content.get('cycle_statuses', [])
        execution_rows = report.content.get('execution_status_distribution', [])
        severity_rows = report.content.get('defect_severity_rows', [])
        defect_status_rows = report.content.get('defect_status_rows', [])
        risk_rows = report.content.get('risk_matrix', [])
        teacher_review_rows = report.content.get('teacher_review_summary', [])
        evidence_rows = report.content.get('evidence_summary', [])
        quality_rows = report.content.get('quality_metrics', [])
        history_rows = report.content.get('execution_history', [])
        exit_rows = report.content.get('exit_criteria', [])
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
            {
                'title': 'Hallazgos principales',
                'paragraph': findings_text,
            },
            {
                'title': 'Recomendaciones de cierre',
                'paragraph': recommendations_text,
            },
            {
                'title': 'Cobertura por módulo',
                'table': {
                    'headers': ['Modulo', 'Requisitos Totales', 'Requisitos Cubiertos', 'Cobertura %'],
                    'rows': [[row['module'], row['total'], row['covered'], f"{row['coverage']}%"] for row in module_coverage],
                },
                'chart_data': [(row['module'][:18], row['coverage']) for row in module_coverage],
            },
            {
                'title': 'Matriz de trazabilidad',
                'items': [
                    ('Total requisitos cubiertos', _content_value(report, 'covered_requirements')),
                    ('Total requisitos sin cobertura', _content_value(report, 'uncovered_requirements')),
                    ('Indice de trazabilidad', f"{_content_value(report, 'traceability_index')}%"),
                ],
                'table': {
                    'headers': ['Requisito', 'Caso de prueba', 'Ejecución', 'Defecto', 'Estado'],
                    'rows': [
                        [row['requirement'], row['test_case'], row['execution'], row['defect'], row['status']]
                        for row in traceability_rows
                    ],
                },
                'chart_data': [
                    ('Cubiertos', _content_value(report, 'covered_requirements')),
                    ('Sin cobertura', _content_value(report, 'uncovered_requirements')),
                ],
            },
            {
                'title': 'Estado del ciclo de pruebas',
                'paragraph': f"Avance general del ciclo: {_content_value(report, 'cycle_progress')}%.",
                'table': {
                    'headers': ['Fase ISTQB', 'Estado'],
                    'rows': [[row['phase'], row['status']] for row in cycle_rows],
                },
            },
            {
                'title': 'Revision docente por seccion',
                'table': {
                    'headers': ['Seccion', 'Revisado', 'Total', 'Pendiente'],
                    'rows': [
                        [row['section'], row['reviewed'], row['total'], row['pending']]
                        for row in teacher_review_rows
                    ],
                },
            },
            {
                'title': 'Estado de ejecuciones',
                'table': {
                    'headers': ['Estado', 'Cantidad', 'Porcentaje'],
                    'rows': [[row['status'], row['count'], f"{row['percent']}%"] for row in execution_rows],
                },
            },
            {
                'title': 'Defectos por severidad',
                'table': {
                    'headers': ['Severidad', 'Cantidad'],
                    'rows': [[row['severity'], row['count']] for row in severity_rows],
                },
            },
            {
                'title': 'Defectos por estado',
                'table': {
                    'headers': ['Estado', 'Cantidad'],
                    'rows': [[row['status'], row['count']] for row in defect_status_rows],
                },
                'chart_data': [(row['status'][:18], row['count']) for row in defect_status_rows],
            },
            {
                'title': 'Matriz de riesgos',
                'table': {
                    'headers': ['Probabilidad', 'Impacto bajo', 'Impacto medio', 'Impacto alto'],
                    'rows': [[row['probability'], row['low'], row['medium'], row['high']] for row in risk_rows],
                },
            },
            {
                'title': 'Evidencias registradas',
                'table': {
                    'headers': ['Indicador', 'Valor'],
                    'rows': [[row['metric'], row['value']] for row in evidence_rows],
                },
            },
            {
                'title': 'Métricas de calidad',
                'table': {
                    'headers': ['Metrica', 'Formula', 'Resultado'],
                    'rows': [[row['metric'], row['formula'], row['result']] for row in quality_rows],
                },
            },
            {
                'title': 'Historial de ejecuciones',
                'table': {
                    'headers': ['Fecha', 'Caso de prueba', 'Resultado', 'Ejecutor'],
                    'rows': [[row['date'], row['test_case'], row['result'], row['executor']] for row in history_rows],
                },
            },
            {
                'title': 'Validacion de criterios de salida',
                'table': {
                    'headers': ['Criterio', 'Objetivo', 'Resultado', 'Cumple'],
                    'rows': [
                        [row['criterion'], row['target'], row['result'], 'Si' if row['passed'] else 'No']
                        for row in exit_rows
                    ],
                },
            },
            {
                'title': 'Conclusion final del proyecto',
                'paragraph': build_final_project_conclusion(report),
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
                    'cobertura, ejecución, resultados, automatización, defectos y revisión docente.'
                ),
            },
        ]

    return base_sections + [
        {
            'title': 'Métricas y resultados',
            'items': [
                (CONTENT_LABELS.get(key, key.replace('_', ' ').title()), value)
                for key, value in report.content.items()
            ],
        },
        {
            'title': 'Gráfico automático de métricas',
            'chart_data': build_pdf_chart_data(report),
        },
        {
            'title': 'Observaciones y cierre',
            'paragraph': (
                'Este documento fue generado por la Plataforma ISTQB como evidencia de seguimiento académico '
                'del ciclo de vida de pruebas de software. La información debe ser revisada por el docente tutor '
                'o responsable del proyecto antes de su presentación formal.'
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


RISK_LEVEL_TONES = {
    'Alto': 'danger',
    'Medio': 'warning',
    'Bajo': 'success',
    'Alta': 'danger',
    'Media': 'warning',
    'Baja': 'success',
}


def _plan_report_context(plan):
    risks = list(plan.risks.all())
    probability_labels = dict(Incident.Probability.choices)
    impact_labels = dict(Incident.Impact.choices)

    level_counts = {'Alto': 0, 'Medio': 0, 'Bajo': 0}
    probability_counts = {value: 0 for value, _label in Incident.Probability.choices}
    impact_counts = {value: 0 for value, _label in Incident.Impact.choices}
    matrix = {
        probability: {impact: 0 for impact, _impact_label in Incident.Impact.choices}
        for probability, _probability_label in Incident.Probability.choices
    }

    for risk in risks:
        level_counts[risk.risk_level] += 1
        probability_counts[risk.probability] += 1
        impact_counts[risk.impact] += 1
        matrix[risk.probability][risk.impact] += 1

    probability_order = [
        (Incident.Probability.HIGH, 'Alta'),
        (Incident.Probability.MEDIUM, 'Media'),
        (Incident.Probability.LOW, 'Baja'),
    ]
    impact_order = [
        (Incident.Impact.LOW, 'Bajo'),
        (Incident.Impact.MEDIUM, 'Medio'),
        (Incident.Impact.HIGH, 'Alto'),
    ]
    matrix_rows = [
        {
            'probability': probability_label,
            'low': matrix[probability_value][Incident.Impact.LOW],
            'medium': matrix[probability_value][Incident.Impact.MEDIUM],
            'high': matrix[probability_value][Incident.Impact.HIGH],
        }
        for probability_value, probability_label in probability_order
    ]
    matrix_impacts = [impact_label for _impact_value, impact_label in impact_order]

    def distribution(items):
        max_value = max([value for _label, value, _tone in items] + [1])
        return [
            {
                'label': label,
                'value': value,
                'tone': tone,
                'percent': _percentage(value, max_value),
            }
            for label, value, tone in items
        ]

    level_items = [
        ('Alto', level_counts['Alto'], RISK_LEVEL_TONES['Alto']),
        ('Medio', level_counts['Medio'], RISK_LEVEL_TONES['Medio']),
        ('Bajo', level_counts['Bajo'], RISK_LEVEL_TONES['Bajo']),
    ]
    probability_items = [
        (
            probability_label,
            probability_counts[probability_value],
            RISK_LEVEL_TONES[probability_label],
        )
        for probability_value, probability_label in probability_order
    ]
    impact_items = [
        (
            impact_label,
            impact_counts[impact_value],
            RISK_LEVEL_TONES[impact_label],
        )
        for impact_value, impact_label in impact_order
    ]

    test_type_labels = dict(TestPlan.TestType.choices)

    return {
        'risks': [
            {
                'risk': risk,
                'probability_label': probability_labels.get(risk.probability, risk.probability),
                'impact_label': impact_labels.get(risk.impact, risk.impact),
            }
            for risk in risks
        ],
        'risk_matrix': matrix_rows,
        'risk_matrix_impacts': matrix_impacts,
        'risk_summary': {
            'total': len(risks),
            'alto': level_counts['Alto'],
            'medio': level_counts['Medio'],
            'bajo': level_counts['Bajo'],
        },
        'distribution_groups': [
            {
                'title': 'Distribución de riesgos por nivel',
                'items': distribution(level_items),
            },
            {
                'title': 'Distribución por probabilidad',
                'items': distribution(probability_items),
            },
            {
                'title': 'Distribución por impacto',
                'items': distribution(impact_items),
            },
        ],
        'test_types_display': ', '.join(
            test_type_labels.get(test_type, test_type)
            for test_type in (plan.test_types or [])
        ),
    }


@login_required
def plan_report_selector_view(request):
    visible_projects = visible_projects_for(request.user).order_by('name')
    plans = TestPlan.objects.filter(project__in=visible_projects).order_by('project', 'name')
    plans_by_project = {}
    for plan in plans:
        plans_by_project.setdefault(str(plan.project_id), []).append(
            {'value': plan.pk, 'label': plan.name}
        )

    report_type = request.GET.get('type', '').strip() or 'plan'
    report_type_info = PLAN_REPORT_TYPES.get(report_type)
    if report_type_info is None:
        report_type_info = PLAN_REPORT_TYPES['plan']
        report_type = 'plan'

    plan_id = request.GET.get('plan', '').strip()
    if plan_id:
        plan = get_object_or_404(TestPlan, pk=plan_id, project__in=visible_projects)
        if report_type == 'plan':
            return redirect('reports:plan-report-detail', pk=plan.pk)
        return redirect(report_type_info['url_name'], pk=plan.pk)

    return render(
        request,
        'reports/plan_report_selector.html',
        {
            'projects': visible_projects,
            'plans_by_project_json': json.dumps(plans_by_project),
            'report_type': report_type,
            'report_type_label': report_type_info['title'],
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def plan_report_view(request, pk):
    plan = get_object_or_404(
        TestPlan.objects.select_related('project', 'created_by').prefetch_related('risks'),
        pk=pk,
        project__in=visible_projects_for(request.user),
    )
    context = _plan_report_context(plan)

    return render(
        request,
        'reports/plan_report.html',
        {
            'plan': plan,
            'generated_at': timezone.now(),
            **context,
        },
    )


def _plan_report_data(plan):
    test_cases = plan.test_cases.all()
    requirements = Requirement.objects.filter(
        Q(test_cases__test_plan=plan) | Q(traceability_links__test_case__test_plan=plan)
    ).distinct()
    total_requirements = requirements.count()
    covered_requirement_ids = _covered_requirement_ids(requirements)
    covered_requirements = len(covered_requirement_ids)
    executions = TestExecution.objects.filter(test_case__test_plan=plan)
    defects = Defect.objects.filter(test_case__test_plan=plan)
    risks = list(plan.risks.all())

    passed = executions.filter(result=TestExecution.Result.PASSED).count()
    failed = executions.filter(result=TestExecution.Result.FAILED).count()
    blocked = executions.filter(result=TestExecution.Result.BLOCKED).count()
    errors = executions.filter(result=TestExecution.Result.ERROR).count()
    not_run = executions.filter(result=TestExecution.Result.NOT_RUN).count()
    total_executions = executions.count()
    executed = total_executions - not_run
    executed_cases = executions.exclude(result=TestExecution.Result.NOT_RUN).values('test_case').distinct().count()

    passed_requirements = failed_requirements = blocked_requirements = executed_requirements = 0
    for requirement in requirements:
        plan_case_ids = set(
            requirement.test_cases.filter(test_plan=plan).values_list('id', flat=True)
        ) | set(
            requirement.traceability_links.filter(test_case__test_plan=plan).values_list('test_case_id', flat=True)
        )
        if not plan_case_ids:
            continue
        latest_results = []
        has_execution = False
        for test_case_id in plan_case_ids:
            latest_execution = executions.filter(test_case_id=test_case_id).first()
            if latest_execution:
                has_execution = True
                latest_results.append(latest_execution.result)
            else:
                latest_results.append(TestExecution.Result.NOT_RUN)
        if has_execution:
            executed_requirements += 1
        if TestExecution.Result.FAILED in latest_results:
            failed_requirements += 1
        elif any(result in {TestExecution.Result.BLOCKED, TestExecution.Result.ERROR} for result in latest_results):
            blocked_requirements += 1
        elif latest_results and all(result == TestExecution.Result.PASSED for result in latest_results):
            passed_requirements += 1

    requirement_execution_rate = _percentage(executed_requirements, total_requirements)
    defects_with_execution = defects.filter(execution__isnull=False).count()
    defect_traceability_rate = _percentage(defects_with_execution, defects.count()) if defects.count() else 100
    traceability_index = round(
        (
            _percentage(covered_requirements, total_requirements)
            + requirement_execution_rate
            + defect_traceability_rate
        ) / 3
    )

    return {
        'requirements': total_requirements,
        'covered_requirements': covered_requirements,
        'uncovered_requirements': total_requirements - covered_requirements,
        'coverage': _percentage(covered_requirements, total_requirements),
        'passed_requirements': passed_requirements,
        'failed_requirements': failed_requirements,
        'blocked_requirements': blocked_requirements,
        'pending_requirements': total_requirements - passed_requirements - failed_requirements - blocked_requirements,
        'test_cases': test_cases.count(),
        'executed_cases': executed_cases,
        'executions': total_executions,
        'passed_executions': passed,
        'failed_executions': failed,
        'blocked_executions': blocked,
        'error_executions': errors,
        'not_run_executions': not_run,
        'execution_progress': _percentage(executed_cases, test_cases.count()),
        'success_rate': _percentage(passed, executed),
        'defects': defects.count(),
        'critical_defects': defects.filter(severity=Defect.Severity.HIGH).count(),
        'high_defects': defects.filter(severity=Defect.Severity.HIGH).count(),
        'medium_defects': defects.filter(severity=Defect.Severity.MEDIUM).count(),
        'low_defects': defects.filter(severity=Defect.Severity.LOW).count(),
        'open_defects': defects.filter(status=Defect.Status.OPEN).count(),
        'closed_defects': defects.filter(status=Defect.Status.CLOSED).count(),
        'risks': len(risks),
        'high_risks': _high_risk_count(risks),
        'traceability_index': traceability_index,
        'execution_status_distribution': _execution_status_distribution(executions),
        'defect_severity_rows': _defect_severity_rows(defects),
        'defect_status_rows': _defect_status_rows(defects),
    }


def _plan_queryset(pk, user):
    return get_object_or_404(
        TestPlan.objects.select_related('project', 'created_by').prefetch_related('risks', 'test_cases'),
        pk=pk,
        project__in=visible_projects_for(user),
    )


@login_required
def plan_report_dashboard_view(request, pk):
    plan = _plan_queryset(pk, request.user)
    data = _plan_report_data(plan)
    chart = _chart_group(
        'Estado de ejecuciones',
        [
            ('Aprobadas', data['passed_executions'], 'success'),
            ('Fallidas', data['failed_executions'], 'danger'),
            ('Bloqueadas', data['blocked_executions'], 'warning'),
            ('Error', data['error_executions'], 'danger'),
            ('No ejecutadas', data['not_run_executions'], 'muted'),
        ],
    )
    severity_chart = _chart_group(
        'Defectos por severidad',
        [
            ('Altos', data['high_defects'], 'danger'),
            ('Medios', data['medium_defects'], 'warning'),
            ('Bajos', data['low_defects'], 'success'),
        ],
    )
    return render(
        request,
        'reports/plan_report_dashboard.html',
        {
            'plan': plan,
            'generated_at': timezone.now(),
            **data,
            'execution_chart': chart,
            'severity_chart': severity_chart,
        },
    )


@login_required
def plan_testcases_report_view(request, pk):
    plan = _plan_queryset(pk, request.user)
    test_cases = (
        plan.test_cases.select_related('requirement')
        .prefetch_related('executions')
        .order_by('code')
    )
    rows = []
    for test_case in test_cases:
        latest_execution = test_case.executions.exclude(result=TestExecution.Result.NOT_RUN).first()
        rows.append(
            {
                'test_case': test_case,
                'latest_result': latest_execution.get_result_display() if latest_execution else 'No ejecutado',
                'latest_actual_result': latest_execution.actual_result if latest_execution else '',
                'result_tone': {
                    TestExecution.Result.PASSED: 'success',
                    TestExecution.Result.FAILED: 'danger',
                    TestExecution.Result.BLOCKED: 'warning',
                    TestExecution.Result.ERROR: 'danger',
                    TestExecution.Result.RUNNING: 'info',
                }.get(latest_execution.result, 'muted') if latest_execution else 'muted',
            }
        )
    data = _plan_report_data(plan)
    return render(
        request,
        'reports/plan_testcases_report.html',
        {
            'plan': plan,
            'generated_at': timezone.now(),
            'test_case_rows': rows,
            'total_cases': data['test_cases'],
            'executed_cases': data['executed_cases'],
        },
    )


@login_required
def plan_executions_report_view(request, pk):
    plan = _plan_queryset(pk, request.user)
    data = _plan_report_data(plan)
    executions = (
        TestExecution.objects.filter(test_case__test_plan=plan)
        .select_related('test_case', 'executed_by')
        .order_by('-executed_at', '-created_at')
    )
    result_tones = {
        TestExecution.Result.PASSED: 'success',
        TestExecution.Result.FAILED: 'danger',
        TestExecution.Result.BLOCKED: 'warning',
        TestExecution.Result.ERROR: 'danger',
        TestExecution.Result.RUNNING: 'success',
        TestExecution.Result.NOT_RUN: 'muted',
    }
    execution_rows = [
        {
            'execution': execution,
            'executor': execution.executed_by.get_full_name() or execution.executed_by.username
            if execution.executed_by else '—',
            'result_tone': result_tones.get(execution.result, 'muted'),
        }
        for execution in executions
    ]
    chart = _chart_group(
        'Resultados de ejecución',
        [
            ('Aprobadas', data['passed_executions'], 'success'),
            ('Fallidas', data['failed_executions'], 'danger'),
            ('Bloqueadas', data['blocked_executions'], 'warning'),
            ('Error', data['error_executions'], 'danger'),
            ('No ejecutadas', data['not_run_executions'], 'muted'),
        ],
    )
    return render(
        request,
        'reports/plan_executions_report.html',
        {
            'plan': plan,
            'generated_at': timezone.now(),
            **data,
            'execution_chart': chart,
            'execution_rows': execution_rows,
        },
    )


@login_required
def plan_defects_report_view(request, pk):
    plan = _plan_queryset(pk, request.user)
    defects = (
        Defect.objects.filter(test_case__test_plan=plan)
        .select_related('execution__test_case', 'reported_by', 'assigned_to')
        .order_by('-created_at')
    )
    data = _plan_report_data(plan)
    severity_chart = _chart_group(
        'Defectos por severidad',
        [
            ('Altos', data['high_defects'], 'danger'),
            ('Medios', data['medium_defects'], 'warning'),
            ('Bajos', data['low_defects'], 'success'),
        ],
    )
    status_chart = _chart_group(
        'Defectos por estado',
        [(row['status'], row['count'], 'brand') for row in data['defect_status_rows']],
    )
    return render(
        request,
        'reports/plan_defects_report.html',
        {
            'plan': plan,
            'generated_at': timezone.now(),
            **data,
            'defects': defects,
            'severity_chart': severity_chart,
            'status_chart': status_chart,
        },
    )


def _executive_summary_blocks(plan, data):
    return [
        {
            'title': 'Alcance de la evaluación',
            'text': (
                f'El plan de pruebas "{plan.name}" (versión {plan.version}) del proyecto '
                f'"{plan.project.name}" fue evaluado considerando {data["requirements"]} requisitos, '
                f'{data["test_cases"]} casos de prueba, {data["executions"]} ejecuciones y '
                f'{data["defects"]} defectos registrados.'
            ),
        },
        {
            'title': 'Cobertura y ejecución',
            'text': (
                f'De los {data["requirements"]} requisitos, {data["covered_requirements"]} cuentan con '
                f'cobertura ({data["coverage"]}%), con {data["passed_requirements"]} aprobados, '
                f'{data["failed_requirements"]} fallidos, {data["blocked_requirements"]} bloqueados y '
                f'{data["pending_requirements"]} pendientes. Se ejecutaron {data["executed_cases"]} de '
                f'{data["test_cases"]} casos ({data["execution_progress"]}% de avance), con una tasa de '
                f'aprobación del {data["success_rate"]}%.'
            ),
        },
        {
            'title': 'Resultados de ejecución',
            'text': (
                f'De {data["executions"]} ejecuciones, {data["passed_executions"]} resultaron aprobadas, '
                f'{data["failed_executions"]} fallidas, {data["blocked_executions"]} bloqueadas, '
                f'{data["error_executions"]} con error técnico y {data["not_run_executions"]} aún no ejecutadas.'
            ),
        },
        {
            'title': 'Defectos y riesgos',
            'text': (
                f'Se registraron {data["defects"]} defectos, de los cuales {data["high_defects"]} son de '
                f'severidad alta, {data["open_defects"]} permanecen abiertos y '
                f'{data["closed_defects"]} fueron cerrados. El plan reporta {data["risks"]} riesgos, '
                f'{data["high_risks"]} de nivel alto.'
            ),
        },
        {
            'title': 'Trazabilidad',
            'text': (
                f'El índice global de trazabilidad alcanzado es del {data["traceability_index"]}%, '
                f'integrando cobertura de requisitos, ejecución y defectos vinculados.'
            ),
        },
    ]


def _final_recommendations(plan, data):
    recommendations = []
    if data['coverage'] < plan.minimum_coverage_percentage:
        recommendations.append(
            f'Aumentar la cobertura de requisitos: actualmente en {data["coverage"]}%, por debajo del mínimo '
            f'de {plan.minimum_coverage_percentage}% definido en el plan.'
        )
    if data['success_rate'] < plan.minimum_pass_percentage:
        recommendations.append(
            f'Mejorar la tasa de aprobación: actualmente en {data["success_rate"]}%, por debajo del mínimo '
            f'de {plan.minimum_pass_percentage}% establecido.'
        )
    if data['critical_defects'] > plan.maximum_critical_defects:
        recommendations.append(
            f'Resolver los defectos de severidad alta: se superaron los {plan.maximum_critical_defects} permitidos, '
            f'con {data["critical_defects"]} registrados.'
        )
    if data['open_defects'] > 0:
        recommendations.append(
            f'Dar seguimiento a los {data["open_defects"]} defectos abiertos antes de cerrar el ciclo de pruebas.'
        )
    if data['not_run_executions'] > 0:
        recommendations.append(
            f'Completar las {data["not_run_executions"]} ejecuciones pendientes para finalizar el ciclo.'
        )
    if data['traceability_index'] < 80:
        recommendations.append(
            f'Fortalecer la trazabilidad: el índice global es del {data["traceability_index"]}%.'
        )
    if len(recommendations) < 3:
        recommendations.append(
            'Revisar y validar las evidencias de las ejecuciones junto al docente tutor antes de la entrega formal.'
        )
    if len(recommendations) < 3:
        recommendations.append(
            'Mantener actualizado el registro de defectos con severidad, estado y responsable asignado.'
        )
    return recommendations


@login_required
def plan_final_report_view(request, pk):
    plan = _plan_queryset(pk, request.user)
    data = _plan_report_data(plan)
    execution_chart = _chart_group(
        'Resultados de ejecución',
        [
            ('Aprobadas', data['passed_executions'], 'success'),
            ('Fallidas', data['failed_executions'], 'danger'),
            ('Bloqueadas', data['blocked_executions'], 'warning'),
            ('Error', data['error_executions'], 'danger'),
            ('No ejecutadas', data['not_run_executions'], 'muted'),
        ],
    )
    severity_chart = _chart_group(
        'Defectos por severidad',
        [
            ('Altos', data['high_defects'], 'danger'),
            ('Medios', data['medium_defects'], 'warning'),
            ('Bajos', data['low_defects'], 'success'),
        ],
    )
    plan_context = _plan_report_context(plan)
    if data['success_rate'] >= plan.minimum_pass_percentage and data['coverage'] >= plan.minimum_coverage_percentage and data['critical_defects'] <= plan.maximum_critical_defects:
        verdict = 'APROBADO'
    else:
        verdict = 'PENDIENTE DE AJUSTES'
    return render(
        request,
        'reports/plan_final_report.html',
        {
            'plan': plan,
            'generated_at': timezone.now(),
            **data,
            'verdict': verdict,
            'executive_summary': _executive_summary_blocks(plan, data),
            'recommendations': _final_recommendations(plan, data),
            'execution_chart': execution_chart,
            'severity_chart': severity_chart,
            **plan_context,
        },
    )


def _plan_pdf_sections(plan, section, data, plan_context):
    report_title = f'Informe del Plan de Pruebas - {plan.name}'
    identification = {
        'title': 'Identificación del informe',
        'items': [
            ('Informe', report_title),
            ('Proyecto', plan.project.name),
            ('Plan de Pruebas', plan.name),
            ('Versión', plan.version),
            ('Estado', plan.get_status_display()),
            ('Fecha', timezone.now().strftime('%d/%m/%Y')),
        ],
    }
    observations = {
        'title': 'Observaciones y cierre',
        'paragraph': (
            'Este documento fue generado por la Plataforma ISTQB como evidencia de seguimiento académico '
            'del ciclo de vida de pruebas de software. La información debe ser revisada por el docente tutor '
            'o responsable del proyecto antes de su presentación formal.'
        ),
    }
    test_type_labels = dict(TestPlan.TestType.choices)

    if section == 'casos':
        def _pdf_breaklines(value):
            if not value:
                return '—'
            return escape(value).replace('\n', '<br/>').replace('\r', '')

        rows = []
        for test_case in plan.test_cases.select_related('requirement').order_by('code'):
            latest_execution = test_case.executions.exclude(result=TestExecution.Result.NOT_RUN).first()
            requirement = test_case.requirement.code if test_case.requirement else '—'
            if test_case.requirement and test_case.requirement.title:
                requirement = f"{requirement} - {test_case.requirement.title}"
            rows.append(
                [
                    f"{test_case.code} - {test_case.title}",
                    latest_execution.get_result_display() if latest_execution else 'No ejecutado',
                    requirement,
                    test_case.get_priority_display(),
                    test_case.display_technique,
                    test_case.get_level_display(),
                    test_case.version,
                    _pdf_breaklines(test_case.description),
                    _pdf_breaklines(test_case.preconditions),
                    _pdf_breaklines(test_case.test_data),
                    _pdf_breaklines(test_case.steps),
                    _pdf_breaklines(test_case.expected_result),
                    _pdf_breaklines(latest_execution.actual_result) if latest_execution else '—',
                ]
            )
        return [
            identification,
            {
                'title': 'Resumen de casos de prueba',
                'items': [
                    ('Total de casos de prueba', data['test_cases']),
                    ('Casos ejecutados', data['executed_cases']),
                    ('Progreso de ejecución', f"{data['execution_progress']}%"),
                ],
            },
            {
                'title': 'Casos de prueba del plan',
                'table': {
                    'headers': [
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
                    ],
                    'rows': rows,
                    'font_size': 7,
                },
            },
            observations,
        ]

    if section == 'ejecuciones':
        distribution_rows = data['execution_status_distribution']
        return [
            identification,
            {
                'title': 'Resumen de resultados',
                'items': [
                    ('Total de ejecuciones', data['executions']),
                    ('Aprobadas', data['passed_executions']),
                    ('Fallidas', data['failed_executions']),
                    ('Bloqueadas', data['blocked_executions']),
                    ('Error técnico', data['error_executions']),
                    ('No ejecutadas', data['not_run_executions']),
                    ('Tasa de aprobación', f"{data['success_rate']}%"),
                ],
            },
            {
                'title': 'Distribución por estado',
                'table': {
                    'headers': ['Estado', 'Cantidad', 'Porcentaje'],
                    'rows': [[row['status'], row['count'], f"{row['percent']}%"] for row in distribution_rows],
                },
                'chart_data': [(row['status'][:18], row['count']) for row in distribution_rows],
            },
            observations,
        ]

    if section == 'defectos':
        defect_rows = [
            [
                defect.code,
                defect.test_case.code if defect.test_case else '—',
                defect.title,
                defect.get_severity_display(),
                defect.get_status_display(),
            ]
            for defect in Defect.objects.filter(test_case__test_plan=plan).order_by('-created_at')
        ]
        return [
            identification,
            {
                'title': 'Resumen por severidad',
                'items': [
                    ('Altos', data['high_defects']),
                    ('Medios', data['medium_defects']),
                    ('Bajos', data['low_defects']),
                ],
            },
            {
                'title': 'Defectos por estado',
                'table': {
                    'headers': ['Estado', 'Cantidad'],
                    'rows': [[row['status'], row['count']] for row in data['defect_status_rows']],
                },
            },
            {
                'title': 'Detalle de defectos',
                'table': {
                    'headers': ['ID', 'Caso de prueba', 'Descripción', 'Severidad', 'Estado'],
                    'rows': defect_rows,
                },
            },
            observations,
        ]

    if section == 'final':
        risks_rows = [
            [
                item['risk'].code,
                item['risk'].title,
                item['probability_label'],
                item['impact_label'],
                item['risk'].risk_level,
            ]
            for item in plan_context['risks']
        ]
        return [
            identification,
            {
                'title': 'Objetivo',
                'paragraph': plan.objective,
            },
            {
                'title': 'Alcance',
                'paragraph': plan.scope or 'No definido',
            },
            {
                'title': 'Resumen del plan de pruebas',
                'items': [
                    ('Requisitos evaluados', data['requirements']),
                    ('Casos de prueba', data['test_cases']),
                    ('Ejecuciones', data['executions']),
                    ('Defectos', data['defects']),
                    ('Riesgos', data['risks']),
                ],
            },
            {
                'title': 'Requisitos evaluados',
                'items': [
                    ('Requisitos', data['requirements']),
                    ('Cobertura', f"{data['coverage']}%"),
                    ('Aprobados', data['passed_requirements']),
                    ('Fallidos', data['failed_requirements']),
                    ('Bloqueados', data['blocked_requirements']),
                    ('Pendientes', data['pending_requirements']),
                ],
            },
            {
                'title': 'Resultados de ejecución',
                'table': {
                    'headers': ['Estado', 'Cantidad', 'Porcentaje'],
                    'rows': [
                        [row['status'], row['count'], f"{row['percent']}%"]
                        for row in data['execution_status_distribution']
                    ],
                },
                'chart_data': [(row['status'][:18], row['count']) for row in data['execution_status_distribution']],
            },
            {
                'title': 'Cobertura y trazabilidad',
                'items': [
                    ('Cobertura de requisitos', f"{data['coverage']}%"),
                    ('Requisitos cubiertos', data['covered_requirements']),
                    ('Requisitos sin cobertura', data['uncovered_requirements']),
                    ('Índice de trazabilidad', f"{data['traceability_index']}%"),
                    ('Tasa de aprobación', f"{data['success_rate']}%"),
                ],
            },
            {
                'title': 'Defectos',
                'table': {
                    'headers': ['Severidad', 'Cantidad'],
                    'rows': [
                        ['Altos', data['high_defects']],
                        ['Medios', data['medium_defects']],
                        ['Bajos', data['low_defects']],
                    ],
                },
            },
            {
                'title': 'Riesgos asociados',
                'table': {
                    'headers': ['Código', 'Riesgo', 'Probabilidad', 'Impacto', 'Nivel'],
                    'rows': risks_rows,
                },
            },
            {
                'title': 'Conclusión',
                'paragraph': (
                    f"El plan {plan.name} (v{plan.version}) alcanzó una cobertura de requisitos del {data['coverage']}%, "
                    f"una tasa de aprobación del {data['success_rate']}% y un índice de trazabilidad del "
                    f"{data['traceability_index']}%. Tipo de pruebas aplicados: "
                    f"{', '.join(test_type_labels.get(t, t) for t in (plan.test_types or [])) or 'No definido'}."
                ),
            },
            observations,
        ]

    risks_rows = [
        [
            item['risk'].code,
            item['risk'].title,
            item['probability_label'],
            item['impact_label'],
            item['risk'].risk_level,
        ]
        for item in plan_context['risks']
    ]
    return [
        identification,
        {
            'title': '1. Información general',
            'items': [
                ('Proyecto', plan.project.name),
                ('Nombre del plan', plan.name),
                ('Versión', plan.version),
                ('Descripción', plan.description or '—'),
                ('Estado', plan.get_status_display()),
            ],
        },
        {
            'title': '2. Objetivos y alcance',
            'items': [
                ('Objetivo', plan.objective),
                ('Alcance', plan.scope or '—'),
            ],
        },
        {
            'title': '3. Estrategia y tipos de prueba',
            'items': [
                ('Estrategia', plan.strategy or '—'),
                (
                    'Tipos de prueba',
                    ', '.join(test_type_labels.get(test_type, test_type) for test_type in (plan.test_types or [])) or '—',
                ),
            ],
        },
        {
            'title': '4. Criterios de entrada y salida',
            'items': [
                ('Criterios de entrada', plan.entry_criteria or '—'),
                ('Criterios de salida', plan.exit_criteria or '—'),
                ('Porcentaje mínimo de aprobación', f"{plan.minimum_pass_percentage}%"),
                ('Defectos críticos máximos', plan.maximum_critical_defects),
                ('Porcentaje mínimo de cobertura', f"{plan.minimum_coverage_percentage}%"),
            ],
        },
        {
            'title': '5. Recursos y cronograma',
            'items': [
                ('Recursos', plan.resources or '—'),
                ('Entorno de pruebas', plan.environment or '—'),
                ('Responsabilidades', plan.responsibilities or '—'),
                ('Estimación', plan.estimation or '—'),
                ('Fecha de inicio', plan.start_date.strftime('%d/%m/%Y') if plan.start_date else '—'),
                ('Fecha de fin', plan.end_date.strftime('%d/%m/%Y') if plan.end_date else '—'),
            ],
        },
        {
            'title': 'Riesgos asociados al plan',
            'table': {
                'headers': ['Código', 'Riesgo', 'Probabilidad', 'Impacto', 'Nivel'],
                'rows': risks_rows,
            },
        },
        {
            'title': 'Matriz de probabilidad-impacto',
            'table': {
                'headers': ['Probabilidad', 'Impacto bajo', 'Impacto medio', 'Impacto alto'],
                'rows': [
                    [row['probability'], row['low'], row['medium'], row['high']]
                    for row in plan_context['risk_matrix']
                ],
            },
        },
        *[
            {
                'title': group['title'],
                'chart_data': [(item['label'], item['value']) for item in group['items']],
            }
            for group in plan_context['distribution_groups']
        ],
        observations,
    ]


@login_required
def plan_report_pdf_view(request, pk, section):
    plan = _plan_queryset(pk, request.user)
    sections = _plan_pdf_sections(
        plan,
        section,
        _plan_report_data(plan),
        _plan_report_context(plan),
    )
    filename = f'plan-pruebas-{section}-{plan.pk}.pdf'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    build_unl_pdf(
        response,
        plan,
        sections=sections,
        title=f'Informe del Plan de Pruebas - {plan.name}',
        use_landscape=(section == 'casos'),
    )
    return response




@login_required
def report_list_view(request):
    visible_projects = visible_projects_for(request.user, request=request)
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
        project__in=visible_projects_for(request.user, request=request),
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
            'final_findings': build_final_findings(report) if is_final else [],
            'final_recommendations': build_final_recommendations(report) if is_final else [],
            'final_project_conclusion': build_final_project_conclusion(report) if is_final else '',
            'summary_text': build_report_summary_text(report),
        },
    )


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.setFont('Helvetica', 8)
            self.setFillColor(colors.HexColor('#52667a'))
            self.drawCentredString(self._pagesize[0] / 2, 0.8 * cm, f'Página {self._pageNumber} de {num_pages}')
            super().showPage()
        super().save()


def build_unl_pdf(buffer, report, sections=None, title=None, use_landscape=False):
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
        pagesize=landscape(A4) if use_landscape else A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title=title or report.title,
        canvasmaker=NumberedCanvas,
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

    if sections is None:
        sections = build_pdf_sections(report)

    for index, section in enumerate(sections, start=1):
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

        if 'table' in section:
            table_data = section['table']
            rows = [table_data['headers']]
            rows.extend(table_data.get('rows', []))
            font_size = table_data.get('font_size', 9)
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['BodySmall'],
                fontSize=font_size,
                leading=font_size + 3,
            )
            section_table = Table(
                [
                    [
                        Paragraph(str(cell), cell_style)
                        for cell in row
                    ]
                    for row in rows
                ],
                colWidths=[doc.width / max(len(table_data['headers']), 1)] * len(table_data['headers']),
                repeatRows=1,
            )
            section_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b315f')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#dbe7f2')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fbfe')]),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('PADDING', (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(section_table)

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
    report = get_object_or_404(Report, pk=pk, project__in=visible_projects_for(request.user, request=request))
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
        project__in=visible_projects_for(request.user, request=request),
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

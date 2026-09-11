from django.db.models import Count, Q

from apps.defects.models import Defect
from apps.executions.models import TestExecution, TestStepExecution
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.traceability.models import TraceabilityLink


def percentage(value, total):
    return round((value / total) * 100, 2) if total else 0


def quality_metrics_for_project(project):
    requirements = Requirement.objects.filter(project=project)
    cases = TestCase.objects.filter(test_plan__project=project)
    executions = TestExecution.objects.filter(test_case__test_plan__project=project)
    defects = Defect.objects.filter(project=project)
    links = TraceabilityLink.objects.filter(requirement__project=project)

    requirement_ids = set(requirements.values_list('pk', flat=True))
    covered_requirement_ids = set(cases.exclude(requirement_id=None).values_list('requirement_id', flat=True))
    covered_requirement_ids.update(links.values_list('requirement_id', flat=True))
    covered_requirement_ids &= requirement_ids

    completed = executions.filter(result__in=[
        TestExecution.Result.PASSED,
        TestExecution.Result.FAILED,
        TestExecution.Result.BLOCKED,
        TestExecution.Result.ERROR,
    ])
    passed = executions.filter(result=TestExecution.Result.PASSED).count()
    failed = executions.filter(result=TestExecution.Result.FAILED).count()
    reviewed = executions.exclude(review_status=TestExecution.ReviewStatus.PENDING).count()
    step_total = TestStepExecution.objects.filter(test_execution__in=executions).count()
    step_evidence = TestStepExecution.objects.filter(test_execution__in=executions).filter(
        Q(evidence_file__isnull=False) | Q(screenshot__isnull=False)
    ).count()
    open_defects = defects.exclude(status=Defect.Status.CLOSED).count()
    critical_defects = defects.filter(priority=Defect.Priority.CRITICAL).exclude(status=Defect.Status.CLOSED).count()
    defects_with_execution = defects.filter(execution__isnull=False).count()

    return {
        'project': project,
        'requirements_total': requirements.count(),
        'requirements_approved': requirements.filter(status=Requirement.Status.APPROVED).count(),
        'requirements_covered': len(covered_requirement_ids),
        'requirements_coverage': percentage(len(covered_requirement_ids), requirements.count()),
        'cases_total': cases.count(),
        'cases_with_execution': cases.filter(executions__isnull=False).distinct().count(),
        'executions_total': executions.count(),
        'executions_completed': completed.count(),
        'executions_passed': passed,
        'executions_failed': failed,
        'pass_rate': percentage(passed, completed.count()),
        'executions_reviewed': reviewed,
        'review_rate': percentage(reviewed, executions.count()),
        'steps_total': step_total,
        'steps_with_evidence': step_evidence,
        'step_evidence_rate': percentage(step_evidence, step_total),
        'defects_total': defects.count(),
        'defects_open': open_defects,
        'critical_defects': critical_defects,
        'defects_traceable': defects_with_execution,
        'defect_traceability_rate': percentage(defects_with_execution, defects.count()),
        'traceability_index': round((
            percentage(len(covered_requirement_ids), requirements.count())
            + percentage(cases.filter(executions__isnull=False).distinct().count(), cases.count())
            + percentage(reviewed, executions.count())
            + percentage(defects_with_execution, defects.count())
        ) / 4, 2),
        'thresholds': {
            'coverage': getattr(project.test_plans.order_by('-id').first(), 'minimum_coverage_percentage', 90),
            'pass_rate': getattr(project.test_plans.order_by('-id').first(), 'minimum_pass_percentage', 80),
            'critical_defects': getattr(project.test_plans.order_by('-id').first(), 'maximum_critical_defects', 0),
        },
    }


def metric_rows(metrics):
    return [
        ('Cobertura de requisitos', f"{metrics['requirements_coverage']}%", 'Requisitos con caso directo o vínculo de trazabilidad'),
        ('Requisitos aprobados', str(metrics['requirements_approved']), 'Requisitos en estado aprobado'),
        ('Tasa de ejecución de casos', f"{percentage(metrics['cases_with_execution'], metrics['cases_total'])}%", 'Casos con al menos una ejecución'),
        ('Tasa de aprobación', f"{metrics['pass_rate']}%", 'Ejecuciones aprobadas / ejecuciones completadas'),
        ('Tasa de revisión docente', f"{metrics['review_rate']}%", 'Ejecuciones con revisión docente'),
        ('Evidencia por paso', f"{metrics['step_evidence_rate']}%", 'Pasos con archivo o captura'),
        ('Índice de trazabilidad', f"{metrics['traceability_index']}%", 'Promedio de cobertura, ejecución, revisión y defectos trazables'),
        ('Defectos abiertos', str(metrics['defects_open']), 'Defectos no cerrados'),
        ('Defectos críticos abiertos', str(metrics['critical_defects']), 'Defectos críticos no cerrados'),
    ]

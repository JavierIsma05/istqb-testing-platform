from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render

from apps.core.permissions import visible_projects_for
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase


@login_required
def traceability_matrix_view(request):
    visible_projects = visible_projects_for(request.user, request=request)
    executions_with_defects = TestExecution.objects.prefetch_related('defects')
    test_cases_with_risks = TestCase.objects.select_related('test_plan').prefetch_related(
        'test_plan__risks',
        'automated_rules',
    )
    requirements = Requirement.objects.select_related('project').prefetch_related(
        'risks',
        Prefetch('test_cases', queryset=test_cases_with_risks),
        Prefetch('test_cases__executions', queryset=executions_with_defects),
        Prefetch('traceability_links__test_case', queryset=test_cases_with_risks),
        Prefetch('traceability_links__test_case__executions', queryset=executions_with_defects),
    ).filter(project__in=visible_projects)
    total_requirements = requirements.count()
    total_test_cases = TestCase.objects.filter(test_plan__project__in=visible_projects).count()
    project_executions = TestExecution.objects.filter(test_case__test_plan__project__in=visible_projects)
    project_risks = Incident.objects.filter(project__in=visible_projects)
    total_executions = project_executions.count()
    total_risks = project_risks.count()
    high_risks = sum(1 for risk in project_risks if risk.risk_level == 'Alto')
    validated_executions = project_executions.filter(review_status=TestExecution.ReviewStatus.VALIDATED).count()
    pending_review_executions = project_executions.filter(review_status=TestExecution.ReviewStatus.PENDING).count()
    covered_requirements = 0
    rows = []

    for requirement in requirements:
        direct_cases = list(requirement.test_cases.all())
        linked_cases = [link.test_case for link in requirement.traceability_links.all()]
        test_cases_by_id = {test_case.id: test_case for test_case in direct_cases + linked_cases}
        test_cases = list(test_cases_by_id.values())

        if test_cases:
            covered_requirements += 1

        executions_by_id = {}
        automated_rules_by_id = {}
        defects_by_id = {}
        risks_by_id = {risk.id: risk for risk in requirement.risks.all()}
        for test_case in test_cases:
            for rule in test_case.automated_rules.all():
                automated_rules_by_id[rule.id] = rule
            for execution in test_case.executions.all():
                executions_by_id[execution.id] = execution
                for defect in execution.defects.all():
                    defects_by_id[defect.id] = defect

        executions = list(executions_by_id.values())
        automated_rules = list(automated_rules_by_id.values())
        defects = list(defects_by_id.values())
        risks = list(risks_by_id.values())
        validated_count = sum(
            1 for execution in executions
            if execution.review_status == TestExecution.ReviewStatus.VALIDATED
        )
        pending_review_count = sum(
            1 for execution in executions
            if execution.review_status == TestExecution.ReviewStatus.PENDING
        )

        # Coverage measures whether a requirement has at least one linked test case.
        # Execution quality and defects are reported separately and must not alter it.
        coverage = 100 if test_cases else 0

        rows.append(
            {
                'requirement': requirement,
                'test_cases': test_cases,
                'executions': executions,
                'automated_rules': automated_rules,
                'defects': defects,
                'risks': risks,
                'validated_count': validated_count,
                'pending_review_count': pending_review_count,
                'coverage': coverage,
                'coverage_tone': 'success' if coverage >= 80 else 'warning',
            }
        )

    total_coverage = round((covered_requirements / total_requirements) * 100) if total_requirements else 0

    return render(
        request,
        'traceability/index.html',
        {
            'rows': rows,
            'total_coverage': total_coverage,
            'covered_requirements': covered_requirements,
            'total_requirements': total_requirements,
            'total_test_cases': total_test_cases,
            'total_executions': total_executions,
            'total_risks': total_risks,
            'high_risks': high_risks,
            'validated_executions': validated_executions,
            'pending_review_executions': pending_review_executions,
        },
    )

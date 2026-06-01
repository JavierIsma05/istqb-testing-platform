from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core.permissions import visible_projects_for
from apps.defects.models import Defect
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase


@login_required
def traceability_matrix_view(request):
    visible_projects = visible_projects_for(request.user)
    requirements = Requirement.objects.select_related('project').prefetch_related(
        'test_cases',
        'traceability_links__test_case',
    ).filter(project__in=visible_projects)
    total_requirements = requirements.count()
    total_test_cases = TestCase.objects.filter(test_plan__project__in=visible_projects).count()
    covered_requirements = 0
    rows = []

    for requirement in requirements:
        direct_cases = list(requirement.test_cases.all())
        linked_cases = [link.test_case for link in requirement.traceability_links.all()]
        test_cases_by_id = {test_case.id: test_case for test_case in direct_cases + linked_cases}
        test_cases = list(test_cases_by_id.values())

        if test_cases:
            covered_requirements += 1

        defects = Defect.objects.filter(
            execution__test_case_id__in=[test_case.id for test_case in test_cases]
        ).distinct()

        if not defects.exists():
            defects = Defect.objects.filter(project=requirement.project).filter(
                execution__isnull=True
            )[:0]

        coverage = 100 if test_cases else 0
        if defects.exists() and coverage == 100:
            coverage = 85 if defects.count() == 1 else 60

        rows.append(
            {
                'requirement': requirement,
                'test_cases': test_cases,
                'defects': defects,
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
        },
    )

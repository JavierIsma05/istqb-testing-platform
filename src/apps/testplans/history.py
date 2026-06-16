from .models import TestPlanVersion


def test_plan_snapshot(test_plan):
    return {
        'project_id': test_plan.project_id,
        'name': test_plan.name,
        'version': test_plan.version,
        'description': test_plan.description,
        'objective': test_plan.objective,
        'scope': test_plan.scope,
        'strategy': test_plan.strategy,
        'test_types': test_plan.test_types,
        'entry_criteria': test_plan.entry_criteria,
        'exit_criteria': test_plan.exit_criteria,
        'minimum_pass_percentage': test_plan.minimum_pass_percentage,
        'maximum_critical_defects': test_plan.maximum_critical_defects,
        'minimum_coverage_percentage': test_plan.minimum_coverage_percentage,
        'resources': test_plan.resources,
        'environment': test_plan.environment,
        'responsibilities': test_plan.responsibilities,
        'estimation': test_plan.estimation,
        'status': test_plan.status,
    }


def record_test_plan_version(test_plan, changed_by=None, reason=''):
    next_number = test_plan.versions.count() + 1
    return TestPlanVersion.objects.create(
        test_plan=test_plan,
        version_number=next_number,
        version_label=test_plan.version,
        name=test_plan.name,
        objective=test_plan.objective,
        status=test_plan.status,
        changed_by=changed_by,
        change_reason=reason,
        snapshot=test_plan_snapshot(test_plan),
    )

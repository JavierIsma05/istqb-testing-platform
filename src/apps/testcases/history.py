from .models import TestCaseVersion


def test_case_snapshot(test_case):
    return {
        'test_plan_id': test_case.test_plan_id,
        'requirement_id': test_case.requirement_id,
        'code': test_case.code,
        'title': test_case.title,
        'description': test_case.description,
        'technique': test_case.technique,
        'custom_technique': test_case.custom_technique,
        'level': test_case.level,
        'preconditions': test_case.preconditions,
        'test_data': test_case.test_data,
        'steps': test_case.steps,
        'steps_data': test_case.steps_data,
        'expected_result': test_case.expected_result,
        'version': test_case.version,
        'priority': test_case.priority,
        'status': test_case.status,
        'execution_type': test_case.execution_type,
    }


def record_test_case_version(test_case, changed_by=None, reason=''):
    next_number = test_case.versions.count() + 1
    return TestCaseVersion.objects.create(
        test_case=test_case,
        version_number=next_number,
        version_label=test_case.version,
        title=test_case.title,
        status=test_case.status,
        changed_by=changed_by,
        change_reason=reason,
        snapshot=test_case_snapshot(test_case),
    )

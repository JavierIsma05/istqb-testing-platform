import pytest

from apps.executions.models import BuildArtifact, TestExecution, TestRun


@pytest.mark.django_db
def test_build_y_campana_conservan_trazabilidad(project, test_plan, test_case, user):
    build = BuildArtifact.objects.create(
        project=project,
        version='1.4.0',
        build_number='20260911.145',
        commit_sha='d757283',
        branch='main',
        environment=BuildArtifact.Environment.QA,
        created_by=user,
    )
    run = TestRun.objects.create(
        project=project,
        test_plan=test_plan,
        build=build,
        name='Regresión versión 1.4.0',
        code='RUN-001',
        environment='QA',
        created_by=user,
    )
    run.test_cases.add(test_case)
    assert run.total_cases == 1
    assert run.completion_percentage == 0
    assert run.calculate_verdict() == TestRun.Verdict.PENDING


@pytest.mark.django_db
def test_campana_completa_se_aprueba_con_todos_los_casos_pasados(project, test_plan, test_case, user):
    build = BuildArtifact.objects.create(project=project, version='1.0', build_number='1', created_by=user)
    run = TestRun.objects.create(project=project, test_plan=test_plan, build=build, name='Smoke', code='RUN-002', environment='QA', created_by=user)
    run.test_cases.add(test_case)
    TestExecution.objects.create(test_case=test_case, test_run=run, build=build, executed_by=user, result=TestExecution.Result.PASSED)
    assert run.completion_percentage == 100
    assert run.passed_cases == 1
    assert run.calculate_verdict() == TestRun.Verdict.PASSED


@pytest.mark.django_db
def test_campana_falla_si_un_caso_falla(project, test_plan, test_case, user):
    build = BuildArtifact.objects.create(project=project, version='1.0', build_number='2', created_by=user)
    run = TestRun.objects.create(project=project, test_plan=test_plan, build=build, name='Regresión', code='RUN-003', environment='QA', created_by=user)
    run.test_cases.add(test_case)
    TestExecution.objects.create(test_case=test_case, test_run=run, build=build, executed_by=user, result=TestExecution.Result.FAILED)
    assert run.calculate_verdict() == TestRun.Verdict.FAILED

import pytest

from apps.testplans.forms import TestPlanWizardForm as PlanForm
from apps.testplans.models import TestPlan as PlanModel


@pytest.mark.django_db
def test_plan_de_pruebas_se_crea_en_borrador_por_defecto(test_plan, project):
    assert test_plan.project == project
    assert test_plan.version == '1.0'
    assert test_plan.status == PlanModel.Status.DRAFT
    assert str(test_plan) == 'Plan funcional'


@pytest.mark.django_db
def test_formulario_de_plan_de_pruebas_es_valido_con_objetivo(project):
    form = PlanForm(
        data={
            'project': project.id,
            'name': 'Plan de regresion',
            'version': '1.0',
            'description': 'Validacion de regresion',
            'scope': 'Modulos principales',
            'objective': 'Detectar regresiones funcionales.',
            'entry_criteria': 'Ambiente disponible',
            'exit_criteria': 'Casos criticos ejecutados',
            'resources': 'Equipo QA',
            'status': PlanModel.Status.REVIEW,
        }
    )

    assert form.is_valid()

from dataclasses import dataclass

from django.core.exceptions import ValidationError

from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()


def requirement_can_be_approved(requirement):
    errors = []
    if not (requirement.title or '').strip():
        errors.append('El requisito debe tener un título.')
    if not (requirement.description or '').strip():
        errors.append('El requisito debe tener una descripción verificable.')
    if not requirement.priority:
        errors.append('El requisito debe tener prioridad.')
    return ValidationResult(not errors, tuple(errors))


def test_case_readiness(test_case):
    errors = []
    requirement = test_case.requirement
    if not requirement or requirement.status != Requirement.Status.APPROVED:
        errors.append('El caso requiere un requisito aprobado.')
    if not (test_case.title or '').strip():
        errors.append('El caso debe tener título.')
    if not (test_case.steps or '').strip() or not (test_case.steps_data or []):
        errors.append('El caso debe tener pasos ejecutables.')
    if not (test_case.expected_result or '').strip():
        errors.append('El caso debe tener resultado esperado.')
    if not test_case.technique:
        errors.append('El caso debe indicar la técnica de diseño utilizada.')
    return ValidationResult(not errors, tuple(errors))


def validate_test_plan_approval(plan):
    errors = []
    required_fields = {
        'objective': plan.objective,
        'scope': plan.scope,
        'strategy': plan.strategy,
        'entry_criteria': plan.entry_criteria,
        'exit_criteria': plan.exit_criteria,
        'environment': plan.environment,
        'responsibilities': plan.responsibilities,
    }
    errors.extend(f'Completa el campo {name.replace("_", " ")}.'.capitalize() for name, value in required_fields.items() if not (value or '').strip())
    requirements = plan.project.requirements.all()
    if not requirements.exists():
        errors.append('El proyecto debe tener requisitos antes de aprobar el plan.')
    elif requirements.exclude(status=Requirement.Status.APPROVED).exists():
        errors.append('Todos los requisitos del proyecto deben estar aprobados.')
    cases = plan.test_cases.all()
    if not cases.exists():
        errors.append('El plan debe tener al menos un caso de prueba antes de aprobarse.')
    for case in cases:
        readiness = test_case_readiness(case)
        errors.extend(f'{case.code}: {error}' for error in readiness.errors)
    return ValidationResult(not errors, tuple(errors))


def defect_transition_options(status):
    """Return the available defect targets from the central lifecycle definition."""
    transitions = {
        Defect.Status.OPEN: (Defect.Status.ANALYSIS, Defect.Status.IN_PROGRESS, Defect.Status.REJECTED, Defect.Status.DUPLICATED),
        Defect.Status.ANALYSIS: (Defect.Status.IN_PROGRESS, Defect.Status.OPEN),
        Defect.Status.IN_PROGRESS: (Defect.Status.RESOLVED, Defect.Status.OPEN),
        Defect.Status.RESOLVED: (Defect.Status.PENDING_CONFIRMATION, Defect.Status.IN_PROGRESS),
        Defect.Status.PENDING_CONFIRMATION: (Defect.Status.CLOSED, Defect.Status.REOPENED),
        Defect.Status.CLOSED: (Defect.Status.REOPENED,),
        Defect.Status.REOPENED: (Defect.Status.IN_PROGRESS, Defect.Status.REJECTED),
    }
    return transitions.get(status, ())


def defect_transition_allowed(defect, target):
    transitions = {
        Defect.Status.OPEN: {Defect.Status.ANALYSIS, Defect.Status.IN_PROGRESS, Defect.Status.REJECTED, Defect.Status.DUPLICATED},
        Defect.Status.ANALYSIS: {Defect.Status.IN_PROGRESS, Defect.Status.OPEN},
        Defect.Status.IN_PROGRESS: {Defect.Status.RESOLVED, Defect.Status.OPEN},
        Defect.Status.RESOLVED: {Defect.Status.PENDING_CONFIRMATION, Defect.Status.IN_PROGRESS},
        Defect.Status.PENDING_CONFIRMATION: {Defect.Status.CLOSED, Defect.Status.REOPENED},
        Defect.Status.CLOSED: {Defect.Status.REOPENED},
        Defect.Status.REOPENED: {Defect.Status.IN_PROGRESS, Defect.Status.REJECTED},
    }
    if target not in transitions.get(defect.status, set()):
        raise ValidationError('La transición solicitada no está permitida desde el estado actual.')
    if target in {Defect.Status.IN_PROGRESS, Defect.Status.RESOLVED, Defect.Status.PENDING_CONFIRMATION} and not defect.assigned_to:
        raise ValidationError('Asigna un responsable antes de avanzar el defecto.')
    if target == Defect.Status.PENDING_CONFIRMATION and not (defect.resolution or '').strip():
        raise ValidationError('Registra la resolución antes de solicitar confirmación.')
    if target == Defect.Status.CLOSED:
        if not defect.verification_execution_id:
            raise ValidationError('Un defecto solo se puede cerrar con una ejecución de confirmación aprobada.')
        if defect.verification_execution.result != 'PASSED':
            raise ValidationError('La ejecución de confirmación debe estar aprobada.')
    return True


def raise_if_invalid(result):
    if not result.ok:
        raise ValidationError(list(result.errors))
    return result


def case_changed_after_execution(instance, cleaned_data):
    if not instance.pk:
        return False
    old = TestCase.objects.get(pk=instance.pk)
    tracked = ('requirement_id', 'title', 'description', 'technique', 'level', 'preconditions', 'test_data', 'steps', 'expected_result', 'version', 'priority')
    return any(getattr(old, field) != cleaned_data.get(field, getattr(old, field)) for field in tracked)


def status_transition_for_requirement(requirement, new_status):
    allowed = {
        Requirement.Status.PENDING: {Requirement.Status.REVIEW},
        Requirement.Status.REVIEW: {Requirement.Status.APPROVED, Requirement.Status.PENDING},
        Requirement.Status.APPROVED: {Requirement.Status.REVIEW},
    }
    if new_status not in allowed.get(requirement.status, set()):
        raise ValidationError('La transición del requisito no está permitida.')
    if new_status == Requirement.Status.APPROVED:
        raise_if_invalid(requirement_can_be_approved(requirement))
    return True


def status_transition_for_plan(plan, new_status):
    allowed = {
        TestPlan.Status.DRAFT: {TestPlan.Status.REVIEW},
        TestPlan.Status.REVIEW: {TestPlan.Status.APPROVED, TestPlan.Status.DRAFT},
        TestPlan.Status.APPROVED: {TestPlan.Status.CLOSED, TestPlan.Status.REVIEW},
        TestPlan.Status.CLOSED: {TestPlan.Status.REVIEW},
    }
    if new_status not in allowed.get(plan.status, set()):
        raise ValidationError('La transición del plan no está permitida.')
    if new_status == TestPlan.Status.APPROVED:
        raise_if_invalid(validate_test_plan_approval(plan))
    return True


def status_transition_for_test_case(test_case, new_status):
    """Validate the lifecycle transitions of a test case.

    Test case execution results are not arbitrary editable states: they are
    driven by the execution workflow.
    """
    allowed = {
        TestCase.Status.PENDING: {TestCase.Status.READY},
        TestCase.Status.READY: {TestCase.Status.RUNNING, TestCase.Status.BLOCKED},
        TestCase.Status.RUNNING: {
            TestCase.Status.PASSED,
            TestCase.Status.FAILED,
            TestCase.Status.BLOCKED,
        },
        TestCase.Status.PASSED: {TestCase.Status.READY},
        TestCase.Status.FAILED: {TestCase.Status.READY},
        TestCase.Status.BLOCKED: {TestCase.Status.READY},
    }
    if new_status not in allowed.get(test_case.status, set()):
        raise ValidationError('La transición del caso de prueba no está permitida.')
    if new_status == TestCase.Status.READY:
        raise_if_invalid(test_case_readiness(test_case))
    return True



def execution_transition_allowed(execution, target):
    """Validate legal execution-result transitions."""
    allowed = {
        TestExecution.Result.NOT_RUN: {TestExecution.Result.RUNNING},
        TestExecution.Result.RUNNING: {
            TestExecution.Result.PASSED,
            TestExecution.Result.FAILED,
            TestExecution.Result.BLOCKED,
            TestExecution.Result.ERROR,
        },
    }
    if target not in allowed.get(execution.result, set()):
        raise ValidationError('La transición de la ejecución no está permitida desde el resultado actual.')
    return True


def incident_transition_allowed(incident, target):
    """Validate the lifecycle of a project risk."""
    allowed = {
        Incident.Status.OPEN: {Incident.Status.ANALYSIS, Incident.Status.MITIGATED},
        Incident.Status.ANALYSIS: {Incident.Status.MITIGATED, Incident.Status.OPEN},
        Incident.Status.MITIGATED: {Incident.Status.CLOSED, Incident.Status.ANALYSIS},
        Incident.Status.CLOSED: {Incident.Status.ANALYSIS},
    }
    if target not in allowed.get(incident.status, set()):
        raise ValidationError('La transición del riesgo no está permitida desde el estado actual.')
    if target == Incident.Status.MITIGATED and not (incident.mitigation_strategy or '').strip():
        raise ValidationError('Registra la estrategia de mitigación antes de marcar el riesgo como mitigado.')
    if target == Incident.Status.CLOSED and not (incident.mitigation_strategy or '').strip():
        raise ValidationError('Un riesgo debe tener una estrategia de mitigación antes de cerrarse.')
    return True


def validate_execution_repeat(test_case, execution_type, environment, previous_execution=None):
    if execution_type != 'NORMAL':
        return ValidationResult(True)
    qs = test_case.executions.filter(execution_type='NORMAL', result__in=['NOT_RUN', 'RUNNING', 'PASSED', 'FAILED', 'BLOCKED', 'ERROR'])
    if previous_execution:
        qs = qs.exclude(pk=previous_execution.pk)
    if environment:
        qs = qs.filter(environment=environment)
    if qs.exists():
        return ValidationResult(False, ('Ya existe una ejecución normal para este caso y ambiente. Usa confirmación o regresión, o registra un motivo de reejecución.',))
    return ValidationResult(True)


def validate_file_upload(uploaded, allowed_extensions, max_size):
    if not uploaded:
        return ValidationResult(False, ('La evidencia es obligatoria.',))
    if uploaded.size > max_size:
        return ValidationResult(False, ('La evidencia supera el tamaño máximo permitido.',))
    name = uploaded.name.lower()
    if not name.endswith(tuple(allowed_extensions)):
        return ValidationResult(False, ('El tipo de archivo no está permitido.',))
    return ValidationResult(True)


__all__ = ['case_changed_after_execution', 'defect_transition_allowed', 'execution_transition_allowed', 'incident_transition_allowed', 'raise_if_invalid', 'requirement_can_be_approved', 'status_transition_for_plan', 'status_transition_for_requirement', 'status_transition_for_test_case', 'test_case_readiness', 'validate_test_plan_approval', 'validate_execution_repeat']

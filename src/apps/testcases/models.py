from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OwnedModel
from apps.requirements.models import Requirement
from apps.testplans.models import TestPlan


class TestCase(OwnedModel):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En Redacción'
        READY = 'READY', 'Listo para Ejecutar'
        RUNNING = 'RUNNING', 'Ejecutando'
        PASSED = 'PASSED', 'Completado'
        FAILED = 'FAILED', 'Fallido'
        BLOCKED = 'BLOCKED', 'Bloqueado'

    class ExecutionType(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        AUTOMATED = 'AUTOMATED', 'Automatizada'

    class Technique(models.TextChoices):
        EQUIVALENCE = 'EQUIVALENCE', 'Partición de Equivalencia'
        BOUNDARY = 'BOUNDARY', 'Valores Límite'
        DECISION_TABLE = 'DECISION_TABLE', 'Tabla de Decisión'
        STATE_TRANSITION = 'STATE_TRANSITION', 'Transición de Estados'
        USE_CASE = 'USE_CASE', 'Casos de Uso'
        EXPERIENCE = 'EXPERIENCE', 'Basada en Experiencia'
        BLACK_BOX = 'BLACK_BOX', 'Caja Negra'
        WHITE_BOX = 'WHITE_BOX', 'Caja Blanca'
        EXPLORATORY = 'EXPLORATORY', 'Exploratoria'
        OTHER = 'OTHER', 'Otra'

    class Level(models.TextChoices):
        UNIT = 'UNIT', 'Unitaria'
        INTEGRATION = 'INTEGRATION', 'Integración'
        SYSTEM = 'SYSTEM', 'Sistema'
        ACCEPTANCE = 'ACCEPTANCE', 'Aceptación'

    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='test_cases')
    requirement = models.ForeignKey(Requirement, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_cases')
    covered_risks = models.ManyToManyField(
        'incidents.Incident',
        blank=True,
        related_name='covering_test_cases',
    )
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    technique = models.CharField(max_length=30, choices=Technique.choices, default=Technique.BLACK_BOX)
    custom_technique = models.CharField(max_length=180, blank=True)
    level = models.CharField(max_length=30, choices=Level.choices, default=Level.SYSTEM)
    preconditions = models.TextField(blank=True)
    test_data = models.TextField(blank=True)
    steps = models.TextField()
    steps_data = models.JSONField(default=list, blank=True)
    expected_result = models.TextField()
    version = models.CharField(max_length=20, default='1.0')
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    execution_type = models.CharField(
        max_length=20,
        choices=ExecutionType.choices,
        default=ExecutionType.MANUAL,
    )
    reexecution_requested = models.BooleanField(
        default=False,
        help_text='Indica que el caso fue reabierto explícitamente desde la matriz para una nueva ejecución.',
    )
    requirement_needs_revalidation = models.BooleanField(
        default=False,
        help_text='Indica si el requisito asociado necesita revalidación tras cambios.',
    )

    class Meta:
        ordering = ['test_plan', 'code']
        unique_together = ('test_plan', 'code')

    def __str__(self):
        return f'{self.code} - {self.title}'

    @property
    def display_technique(self):
        if self.technique == self.Technique.OTHER and self.custom_technique.strip():
            return self.custom_technique.strip()
        return self.get_technique_display()

    @property
    def associated_requirements(self):
        from apps.traceability.models import TraceabilityLink
        return Requirement.objects.filter(
            models.Q(pk=self.requirement_id)
            | models.Q(traceability_links__test_case=self)
        ).distinct()

    @property
    def has_approved_requirement(self):
        if not self.pk:
            return False
        return self.associated_requirements.filter(status=Requirement.Status.APPROVED).exists()

    @property
    def execution_block_reason(self):
        return 'Este caso de prueba no puede ejecutarse porque no tiene ningún requisito aprobado.'

    def clean(self):
        super().clean()
        errors = {}
        if not self.requirement_id:
            errors['requirement'] = 'Todo caso de prueba debe cubrir al menos un requisito.'
        elif self.test_plan_id and self.requirement.project_id != self.test_plan.project_id:
            errors['requirement'] = 'El requisito debe pertenecer al mismo proyecto que el plan de pruebas.'

        if self.pk and self.test_plan_id:
            previous_plan_id = type(self).objects.filter(pk=self.pk).values_list('test_plan_id', flat=True).first()
            if previous_plan_id and previous_plan_id != self.test_plan_id:
                errors['test_plan'] = 'El plan de pruebas de un caso existente no puede cambiarse; conserva su trazabilidad histórica.'

        if not (self.steps or '').strip():
            errors['steps'] = 'Registra al menos un paso de ejecucion.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)


class TestCaseVersion(models.Model):
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    version_label = models.CharField(max_length=20, default='1.0')
    title = models.CharField(max_length=180)
    status = models.CharField(max_length=20, choices=TestCase.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.CharField(max_length=180, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['test_case', '-version_number']
        unique_together = ('test_case', 'version_number')

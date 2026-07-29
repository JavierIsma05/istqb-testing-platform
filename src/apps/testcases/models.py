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
        PENDING = 'PENDING', 'Pendiente'
        PASSED = 'PASSED', 'Pasado'
        FAILED = 'FAILED', 'Fallido'
        BLOCKED = 'BLOCKED', 'Bloqueado'

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
    level = models.CharField(max_length=30, choices=Level.choices, default=Level.SYSTEM)
    preconditions = models.TextField(blank=True)
    test_data = models.TextField(blank=True)
    steps = models.TextField()
    steps_data = models.JSONField(default=list, blank=True)
    expected_result = models.TextField()
    version = models.CharField(max_length=20, default='1.0')
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['test_plan', 'code']
        unique_together = ('test_plan', 'code')

    def __str__(self):
        return f'{self.code} - {self.title}'

    def clean(self):
        super().clean()
        errors = {}
        if not self.requirement_id:
            errors['requirement'] = 'Todo caso de prueba debe cubrir al menos un requisito.'
        elif self.test_plan_id and self.requirement.project_id != self.test_plan.project_id:
            errors['requirement'] = 'El requisito debe pertenecer al mismo proyecto que el plan de pruebas.'
        if not (self.steps or '').strip():
            errors['steps'] = 'Registra al menos un paso de ejecucion.'
        if errors:
            raise ValidationError(errors)

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
        PASSED = 'PASSED', 'Passed'
        FAILED = 'FAILED', 'Failed'
        BLOCKED = 'BLOCKED', 'Bloqueado'

    class Technique(models.TextChoices):
        EQUIVALENCE = 'EQUIVALENCE', 'Partición de Equivalencia'
        BOUNDARY = 'BOUNDARY', 'Valores Límite'
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
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    technique = models.CharField(max_length=30, choices=Technique.choices, default=Technique.BLACK_BOX)
    level = models.CharField(max_length=30, choices=Level.choices, default=Level.SYSTEM)
    preconditions = models.TextField(blank=True)
    steps = models.TextField()
    expected_result = models.TextField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['test_plan', 'code']
        unique_together = ('test_plan', 'code')

    def __str__(self):
        return f'{self.code} - {self.title}'

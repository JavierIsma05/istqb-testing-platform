from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.projects.models import Project


class Incident(TimeStampedModel):
    class Probability(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'

    class Impact(models.TextChoices):
        LOW = 'LOW', 'Bajo'
        MEDIUM = 'MEDIUM', 'Medio'
        HIGH = 'HIGH', 'Alto'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Abierta'
        ANALYSIS = 'ANALYSIS', 'En análisis'
        MITIGATED = 'MITIGATED', 'Mitigada'
        CLOSED = 'CLOSED', 'Cerrado'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='incidents')
    code = models.CharField(max_length=40, default='INC-000')
    title = models.CharField(max_length=180)
    description = models.TextField()
    probability = models.CharField(max_length=20, choices=Probability.choices, default=Probability.MEDIUM)
    impact = models.CharField(max_length=20, choices=Impact.choices, default=Impact.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('project', 'code')

    def __str__(self):
        return self.title

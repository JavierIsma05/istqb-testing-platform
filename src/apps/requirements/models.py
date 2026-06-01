from django.db import models

from apps.core.models import OwnedModel
from apps.projects.models import Project


class Requirement(OwnedModel):
    class RequirementType(models.TextChoices):
        FUNCTIONAL = 'FUNCTIONAL', 'Funcional'
        NON_FUNCTIONAL = 'NON_FUNCTIONAL', 'No funcional'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        REVIEW = 'REVIEW', 'En revisión'
        APPROVED = 'APPROVED', 'Aprobado'
        CHANGED = 'CHANGED', 'Cambiado'
        RETIRED = 'RETIRED', 'Retirado'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements')
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=180)
    description = models.TextField()
    requirement_type = models.CharField(
        max_length=20,
        choices=RequirementType.choices,
        default=RequirementType.FUNCTIONAL,
    )
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['project', 'code']
        unique_together = ('project', 'code')

    def __str__(self):
        return f'{self.code} - {self.title}'

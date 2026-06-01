from django.db import models

from apps.core.models import TimeStampedModel
from apps.projects.models import Project


class TestingPhase(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        IN_PROGRESS = 'IN_PROGRESS', 'En progreso'
        DONE = 'DONE', 'Completada'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testing_phases')
    name = models.CharField(max_length=120)
    order = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.TextField(blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    completed_tasks = models.PositiveSmallIntegerField(default=0)
    pending_tasks = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['project', 'order']
        unique_together = ('project', 'order')

    def __str__(self):
        return self.name

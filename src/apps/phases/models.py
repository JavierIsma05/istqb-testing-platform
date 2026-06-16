from django.db import models
from django.conf import settings

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
    entry_criteria = models.TextField(blank=True)
    exit_criteria = models.TextField(blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    completed_tasks = models.PositiveSmallIntegerField(default=0)
    pending_tasks = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['project', 'order']
        unique_together = ('project', 'order')

    def __str__(self):
        return self.name

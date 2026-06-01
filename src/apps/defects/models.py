from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.executions.models import TestExecution
from apps.projects.models import Project


class Defect(TimeStampedModel):
    class Severity(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Fix'
        RESOLVED = 'RESOLVED', 'Resuelto'
        CLOSED = 'CLOSED', 'Closed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='defects')
    execution = models.ForeignKey(TestExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name='defects')
    code = models.CharField(max_length=40, default='DEF-000')
    title = models.CharField(max_length=180)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_defects')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_defects')

    class Meta:
        ordering = ['-created_at']
        unique_together = ('project', 'code')

    def __str__(self):
        return self.title

from django.db import models

from apps.core.models import OwnedModel
from apps.projects.models import Project


class TestPlan(OwnedModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        REVIEW = 'REVIEW', 'En revisión'
        APPROVED = 'APPROVED', 'Aprobado'
        CLOSED = 'CLOSED', 'Cerrado'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_plans')
    name = models.CharField(max_length=180)
    version = models.CharField(max_length=20, default='1.0')
    description = models.TextField(blank=True)
    objective = models.TextField()
    scope = models.TextField(blank=True)
    strategy = models.TextField(blank=True)
    entry_criteria = models.TextField(blank=True)
    exit_criteria = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ['project', 'name']

    def __str__(self):
        return self.name

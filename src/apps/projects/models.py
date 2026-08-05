from django.conf import settings
from django.db import models

from apps.core.models import OwnedModel


class Project(OwnedModel):
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planificado'
        ACTIVE = 'ACTIVE', 'Activo'
        PAUSED = 'PAUSED', 'Pausado'
        CLOSED = 'CLOSED', 'Cerrado'

    name = models.CharField(max_length=180)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tutored_projects',
    )
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='projects')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.code} - {self.name}'

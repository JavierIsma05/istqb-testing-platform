from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    entity = models.CharField(max_length=120)
    entity_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Los registros de auditoría son inmutables y no pueden modificarse.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los registros de auditoría son inmutables y no pueden eliminarse.')

    def __str__(self):
        return f'{self.action} {self.entity}'

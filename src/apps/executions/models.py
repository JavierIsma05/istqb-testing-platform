from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.testcases.models import TestCase


class TestExecution(TimeStampedModel):
    class Result(models.TextChoices):
        NOT_RUN = 'NOT_RUN', 'No ejecutado'
        PASSED = 'PASSED', 'Aprobado'
        FAILED = 'FAILED', 'Fallido'
        BLOCKED = 'BLOCKED', 'Bloqueado'

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='executions')
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.NOT_RUN)
    evidence = models.FileField(upload_to='evidence/', null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-executed_at', '-created_at']

    def __str__(self):
        return f'{self.test_case} - {self.get_result_display()}'

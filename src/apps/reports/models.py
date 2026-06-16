from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.projects.models import Project


class Report(TimeStampedModel):
    class ReportType(models.TextChoices):
        SUMMARY = 'SUMMARY', 'Resumen'
        COVERAGE = 'COVERAGE', 'Cobertura'
        DEFECTS = 'DEFECTS', 'Defectos'
        EXECUTION = 'EXECUTION', 'Ejecución'

        FINAL = 'FINAL', 'Informe general final'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=180)
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ReportDownload(TimeStampedModel):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='downloads')
    downloaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='report_downloads')
    filename = models.CharField(max_length=180)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.filename}'

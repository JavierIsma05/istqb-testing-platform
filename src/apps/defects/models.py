from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel
from apps.executions.models import TestExecution
from apps.projects.models import Project
from apps.testcases.models import TestCase


class Defect(TimeStampedModel):
    class Severity(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Abierto'
        ANALYSIS = 'ANALYSIS', 'En análisis'
        IN_PROGRESS = 'IN_PROGRESS', 'En progreso'
        RESOLVED = 'RESOLVED', 'Resuelto'
        PENDING_CONFIRMATION = 'PENDING_CONFIRMATION', 'Pendiente de confirmación'
        CLOSED = 'CLOSED', 'Cerrado'
        REOPENED = 'REOPENED', 'Reabierto'
        REJECTED = 'REJECTED', 'Rechazado'
        DUPLICATED = 'DUPLICATED', 'Duplicado'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='defects')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='defects', null=True, blank=True)
    execution = models.ForeignKey(TestExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name='defects')
    code = models.CharField(max_length=40, default='DEF-000')
    title = models.CharField(max_length=180)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_defects')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_defects')
    resolution = models.TextField(blank=True)
    verification_execution = models.ForeignKey(
        'executions.TestExecution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_defects',
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ('project', 'code')

    def clean(self):
        super().clean()
        errors = {}
        if self.test_case_id:
            case_project_id = self.test_case.test_plan.project_id
            if self.project_id != case_project_id:
                errors['project'] = 'El defecto debe pertenecer al mismo proyecto que su caso de prueba.'

        if self.execution_id and self.test_case_id:
            if self.execution.test_case_id != self.test_case_id:
                errors['execution'] = 'La ejecución relacionada debe pertenecer al caso de prueba del defecto.'
            elif self.execution.test_case.test_plan.project_id != self.project_id:
                errors['execution'] = 'La ejecución relacionada debe pertenecer al mismo proyecto del defecto.'
        elif self.execution_id and self.project_id:
            if self.execution.test_case.test_plan.project_id != self.project_id:
                errors['execution'] = 'La ejecución relacionada debe pertenecer al mismo proyecto del defecto.'

        if self.verification_execution_id and self.test_case_id:
            verification = self.verification_execution
            if verification.execution_type != TestExecution.ExecutionType.CONFIRMATION:
                errors['verification_execution'] = 'La ejecución de verificación debe ser una prueba de confirmación.'
            elif verification.test_case_id != self.test_case_id:
                errors['verification_execution'] = 'La confirmación debe pertenecer al caso de prueba del defecto.'
            elif verification.test_case.test_plan.project_id != self.project_id:
                errors['verification_execution'] = 'La confirmación debe pertenecer al mismo proyecto del defecto.'
            elif verification.related_defect_id != self.pk:
                errors['verification_execution'] = 'La confirmación debe estar vinculada al defecto actual.'
        elif self.verification_execution_id and self.project_id:
            verification = self.verification_execution
            if verification.execution_type != TestExecution.ExecutionType.CONFIRMATION:
                errors['verification_execution'] = 'La ejecución de verificación debe ser una prueba de confirmación.'
            elif verification.test_case.test_plan.project_id != self.project_id:
                errors['verification_execution'] = 'La confirmación debe pertenecer al mismo proyecto del defecto.'
            elif verification.related_defect_id != self.pk:
                errors['verification_execution'] = 'La confirmación debe estar vinculada al defecto actual.'

        if self.status == self.Status.CLOSED:
            if not self.verification_execution_id:
                errors['verification_execution'] = 'Un defecto solo puede cerrarse con una ejecución de confirmación aprobada.'
            elif self.verification_execution.result != TestExecution.Result.PASSED:
                errors['verification_execution'] = 'El cierre requiere una ejecución de confirmación con resultado aprobado.'
            elif self.verification_execution.execution_type != TestExecution.ExecutionType.CONFIRMATION:
                errors['verification_execution'] = 'El cierre requiere una ejecución de confirmación.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class DefectHistory(TimeStampedModel):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=30, choices=Defect.Status.choices)
    severity = models.CharField(max_length=20, choices=Defect.Severity.choices)
    priority = models.CharField(max_length=20, choices=Defect.Priority.choices)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_defect_history',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='defect_history_changes',
    )
    change_reason = models.CharField(max_length=180, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['defect', '-created_at']

    def __str__(self):
        return f'{self.defect.code} - {self.get_status_display()}'

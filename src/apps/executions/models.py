import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OwnedModel, TimeStampedModel
from apps.testcases.models import TestCase


class TestExecution(TimeStampedModel):
    class ExecutionMode(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual controlada'
        AUTOMATED = 'AUTOMATED', 'Automatizada'

    class ExecutionType(models.TextChoices):
        NORMAL = 'NORMAL', 'Ejecución funcional'
        CONFIRMATION = 'CONFIRMATION', 'Prueba de confirmación'
        REGRESSION = 'REGRESSION', 'Prueba de regresion'

    class Result(models.TextChoices):
        NOT_RUN = 'NOT_RUN', 'No ejecutado'
        RUNNING = 'RUNNING', 'En ejecucion'
        PASSED = 'PASSED', 'Aprobado'
        FAILED = 'FAILED', 'Fallido'
        BLOCKED = 'BLOCKED', 'Bloqueado'
        ERROR = 'ERROR', 'Error técnico'

    class ReviewStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente de revisión'
        VALIDATED = 'VALIDATED', 'Validada'
        REJECTED = 'REJECTED', 'Rechazada'
        NEEDS_FIX = 'NEEDS_FIX', 'Requiere corrección'

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='executions')
    execution_mode = models.CharField(max_length=20, choices=ExecutionMode.choices, default=ExecutionMode.MANUAL)
    execution_type = models.CharField(max_length=20, choices=ExecutionType.choices, default=ExecutionType.NORMAL)
    related_defect = models.ForeignKey('defects.Defect', on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_executions')
    planned_date = models.DateField(null=True, blank=True)
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.NOT_RUN)
    approval_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    actual_result = models.TextField(blank=True)
    test_data = models.TextField(blank=True)
    environment = models.CharField(max_length=180, blank=True)
    environment_url = models.URLField(blank=True)
    browser = models.CharField(max_length=30, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    technical_log = models.TextField(blank=True)
    step_results = models.JSONField(default=list, blank=True)
    evidence = models.FileField(upload_to='evidence/', null=True, blank=True)
    notes = models.TextField(blank=True)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_executions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-executed_at', '-created_at']

    def clean(self):
        errors = {}
        if self.test_case_id and self.related_defect_id:
            if self.related_defect.test_case_id != self.test_case_id:
                errors['related_defect'] = 'El defecto relacionado debe pertenecer al mismo caso de prueba.'
            elif self.related_defect.project_id != self.test_case.test_plan.project_id:
                errors['related_defect'] = 'El defecto relacionado debe pertenecer al mismo proyecto del caso de prueba.'
            elif self.execution_type != self.ExecutionType.CONFIRMATION:
                errors['related_defect'] = 'Un defecto relacionado solo puede asociarse mediante una prueba de confirmación.'
            elif self.related_defect.status not in {'IN_PROGRESS', 'RESOLVED', 'REOPENED', 'PENDING_CONFIRMATION'}:
                errors['related_defect'] = 'La confirmación solo puede ejecutarse sobre un defecto en corrección o pendiente de confirmación.'
        if self.execution_type == self.ExecutionType.CONFIRMATION and not self.related_defect_id:
            errors['related_defect'] = 'Una ejecución de confirmación debe estar vinculada a un defecto.'
        if self.approval_percentage is not None and self.approval_percentage > 100:
            errors['approval_percentage'] = 'El porcentaje de aprobación no puede superar 100.'
        if self.started_at and self.finished_at and self.finished_at < self.started_at:
            errors['finished_at'] = 'La fecha de finalización no puede ser anterior al inicio.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.test_case} - {self.get_result_display()}'


class TestStepExecution(TimeStampedModel):
    test_execution = models.ForeignKey(TestExecution, on_delete=models.CASCADE, related_name='step_executions')
    step_number = models.PositiveIntegerField()
    action = models.TextField()
    expected_result = models.TextField()
    obtained_result = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TestExecution.Result.choices)
    comment = models.TextField(blank=True)
    evidence_file = models.FileField(upload_to='step_evidence/', null=True, blank=True)
    screenshot = models.ImageField(upload_to='execution_screenshots/', null=True, blank=True)
    execution_log = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['step_number', 'created_at']
        constraints = [models.UniqueConstraint(fields=['test_execution', 'step_number'], name='uniq_step_execution_number')]

    def clean(self):
        errors = {}
        if self.step_number < 1:
            errors['step_number'] = 'El número de paso debe ser mayor que cero.'
        if self.test_execution_id:
            duplicate_steps = TestStepExecution.objects.filter(test_execution_id=self.test_execution_id, step_number=self.step_number)
            if self.pk:
                duplicate_steps = duplicate_steps.exclude(pk=self.pk)
            if duplicate_steps.exists():
                errors['step_number'] = 'Ya existe un resultado para este número de paso en la ejecución.'
        if self.started_at and self.finished_at and self.finished_at < self.started_at:
            errors['finished_at'] = 'La fecha de finalización no puede ser anterior al inicio.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.test_execution_id} - Paso {self.step_number}'


class TestData(OwnedModel):
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='test_data_vars')
    key = models.CharField(max_length=120)
    value = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        unique_together = ('test_case', 'key')

    def __str__(self):
        return f'{self.test_case.code} - {self.key}'


class AutomatedValidationRule(TimeStampedModel):
    class ActionType(models.TextChoices):
        OPEN_URL = 'OPEN_URL', 'Abrir URL'
        FILL_TEXT = 'FILL_TEXT', 'Escribir'
        CLICK = 'CLICK', 'Click'
        VERIFY = 'VERIFY', 'Verificar'
        WAIT = 'WAIT', 'Esperar'

    class ComparisonType(models.TextChoices):
        EXACT = 'EXACT', 'Exacto'
        CONTAINS = 'CONTAINS', 'Contiene'
        REGEX = 'REGEX', 'Expresión regular'

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='automated_rules')
    requirement = models.ForeignKey('requirements.Requirement', on_delete=models.CASCADE, related_name='automated_rules')
    step_number = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=180)
    action_type = models.CharField(max_length=30, choices=ActionType.choices, blank=True)
    is_critical = models.BooleanField(default=True)
    target_url = models.URLField(blank=True)
    selector_value = models.CharField(max_length=500, blank=True)
    input_value = models.TextField(blank=True)
    expected_value = models.CharField(max_length=500, blank=True)
    comparison_type = models.CharField(max_length=20, choices=ComparisonType.choices, default=ComparisonType.EXACT, blank=True)
    timeout_seconds = models.PositiveSmallIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['test_case', 'step_number', 'name']
        constraints = [models.UniqueConstraint(fields=['test_case', 'step_number'], name='uniq_automated_rule_step_number')]

    def clean(self):
        errors = {}
        if self.test_case_id and self.requirement_id:
            if self.requirement.project_id != self.test_case.test_plan.project_id:
                errors['requirement'] = 'El requisito debe pertenecer al mismo proyecto del caso de prueba.'
            if self.test_case.requirement_id and self.requirement_id != self.test_case.requirement_id:
                errors['requirement'] = 'La regla automatizada debe utilizar el requisito principal del caso de prueba.'
        if self.step_number < 1:
            errors['step_number'] = 'El número de paso debe ser mayor que cero.'
        if self.test_case_id:
            duplicate_steps = AutomatedValidationRule.objects.filter(test_case_id=self.test_case_id, step_number=self.step_number)
            if self.pk:
                duplicate_steps = duplicate_steps.exclude(pk=self.pk)
            if duplicate_steps.exists():
                errors['step_number'] = 'Ya existe una regla automatizada para este número de paso en el caso.'
        if not 1 <= self.timeout_seconds <= 120:
            errors['timeout_seconds'] = 'El tiempo de espera debe estar entre 1 y 120 segundos.'
        action = self.action_type
        if action == self.ActionType.OPEN_URL:
            if not self.target_url:
                errors['target_url'] = 'La acción Abrir URL requiere una dirección.'
        elif action == self.ActionType.FILL_TEXT:
            if not self.selector_value:
                errors['selector_value'] = 'La acción Escribir requiere un selector CSS.'
            if not self.input_value:
                errors['input_value'] = 'La acción Escribir requiere un dato.'
        elif action == self.ActionType.CLICK:
            if not self.selector_value:
                errors['selector_value'] = 'La acción Click requiere un selector CSS.'
        elif action == self.ActionType.VERIFY:
            if not self.selector_value:
                errors['selector_value'] = 'La acción Verificar requiere un selector CSS.'
            if not self.expected_value:
                errors['expected_value'] = 'La acción Verificar requiere un resultado esperado.'
        elif action == self.ActionType.WAIT:
            if not self.timeout_seconds:
                errors['timeout_seconds'] = 'La acción Esperar requiere una duración.'
        elif action:
            errors['action_type'] = 'La acción automatizada seleccionada no es válida.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.test_case.code} - {self.name}'


class AutomatedExecutionResult(TimeStampedModel):
    test_execution = models.ForeignKey(TestExecution, on_delete=models.CASCADE, related_name='automated_results')
    validation_rule = models.ForeignKey(AutomatedValidationRule, on_delete=models.CASCADE, related_name='execution_results')
    status = models.CharField(max_length=20, choices=TestExecution.Result.choices)
    expected_behavior = models.TextField(blank=True)
    actual_behavior = models.TextField(blank=True)
    input_used = models.TextField(blank=True)
    comparison_type = models.CharField(max_length=20, choices=AutomatedValidationRule.ComparisonType.choices, blank=True)
    technical_log = models.TextField(blank=True)
    screenshot = models.ImageField(upload_to='automation_screenshots/', null=True, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        constraints = [models.UniqueConstraint(fields=['test_execution', 'validation_rule'], name='uniq_automated_result_rule_execution')]

    def clean(self):
        errors = {}
        if self.test_execution_id and self.validation_rule_id:
            if self.test_execution.execution_mode != TestExecution.ExecutionMode.AUTOMATED:
                errors['test_execution'] = 'El resultado automatizado debe pertenecer a una ejecución automatizada.'
            if self.validation_rule.test_case_id != self.test_execution.test_case_id:
                errors['validation_rule'] = 'La regla automatizada debe pertenecer al mismo caso de prueba de la ejecución.'
            elif self.validation_rule.requirement_id != self.test_execution.test_case.requirement_id:
                errors['validation_rule'] = 'La regla automatizada debe utilizar el requisito principal del caso de prueba.'
            duplicate_results = AutomatedExecutionResult.objects.filter(test_execution_id=self.test_execution_id, validation_rule_id=self.validation_rule_id)
            if self.pk:
                duplicate_results = duplicate_results.exclude(pk=self.pk)
            if duplicate_results.exists():
                errors['validation_rule'] = 'Ya existe un resultado para esta regla en la ejecución.'
        if self.started_at and self.finished_at and self.finished_at < self.started_at:
            errors['finished_at'] = 'La fecha de finalización no puede ser anterior al inicio.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.validation_rule.name} - {self.get_status_display()}'

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.testcases.models import TestCase


class TestExecution(TimeStampedModel):
    class ExecutionMode(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual controlada'
        SEMI_AUTOMATED = 'SEMI_AUTOMATED', 'Semi-automatizada'

    class ExecutionType(models.TextChoices):
        NORMAL = 'NORMAL', 'Ejecucion funcional'
        CONFIRMATION = 'CONFIRMATION', 'Prueba de confirmacion'
        REGRESSION = 'REGRESSION', 'Prueba de regresion'

    class Result(models.TextChoices):
        NOT_RUN = 'NOT_RUN', 'No ejecutado'
        RUNNING = 'RUNNING', 'En ejecucion'
        PASSED = 'PASSED', 'Aprobado'
        FAILED = 'FAILED', 'Fallido'
        BLOCKED = 'BLOCKED', 'Bloqueado'
        ERROR = 'ERROR', 'Error tecnico'

    class ReviewStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente de revision'
        VALIDATED = 'VALIDATED', 'Validada'
        REJECTED = 'REJECTED', 'Rechazada'
        NEEDS_FIX = 'NEEDS_FIX', 'Requiere correccion'

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='executions')
    execution_mode = models.CharField(
        max_length=20,
        choices=ExecutionMode.choices,
        default=ExecutionMode.MANUAL,
    )
    execution_type = models.CharField(max_length=20, choices=ExecutionType.choices, default=ExecutionType.NORMAL)
    related_defect = models.ForeignKey(
        'defects.Defect',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_executions',
    )
    planned_date = models.DateField(null=True, blank=True)
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.NOT_RUN)
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
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_executions',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-executed_at', '-created_at']

    def __str__(self):
        return f'{self.test_case} - {self.get_result_display()}'


class TestStepExecution(TimeStampedModel):
    test_execution = models.ForeignKey(
        TestExecution,
        on_delete=models.CASCADE,
        related_name='step_executions',
    )
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

    def __str__(self):
        return f'{self.test_execution_id} - Paso {self.step_number}'


class AutomatedValidationRule(TimeStampedModel):
    class ValidationType(models.TextChoices):
        FIELD_REQUIRED = 'FIELD_REQUIRED', 'Campo obligatorio'
        EMAIL_FORMAT = 'EMAIL_FORMAT', 'Formato de correo'
        MAX_LENGTH = 'MAX_LENGTH', 'Longitud maxima'
        MIN_LENGTH = 'MIN_LENGTH', 'Longitud minima'
        TEXT_VISIBLE = 'TEXT_VISIBLE', 'Texto visible'
        ELEMENT_VISIBLE = 'ELEMENT_VISIBLE', 'Elemento visible'
        REDIRECT_URL = 'REDIRECT_URL', 'Redireccion URL'
        HTTP_STATUS = 'HTTP_STATUS', 'Estado HTTP'
        BUTTON_DISABLED = 'BUTTON_DISABLED', 'Boton deshabilitado'
        FORM_SUBMISSION_BLOCKED = 'FORM_SUBMISSION_BLOCKED', 'Envio de formulario bloqueado'

    class SelectorType(models.TextChoices):
        CSS = 'CSS', 'CSS'
        ID = 'ID', 'ID'
        NAME = 'NAME', 'Name'
        XPATH = 'XPATH', 'XPath'

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='automated_rules')
    requirement = models.ForeignKey(
        'requirements.Requirement',
        on_delete=models.PROTECT,
        related_name='automated_rules',
    )
    step_number = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=180)
    validation_type = models.CharField(max_length=40, choices=ValidationType.choices)
    target_url = models.URLField()
    selector_type = models.CharField(max_length=10, choices=SelectorType.choices, blank=True)
    selector_value = models.CharField(max_length=500, blank=True)
    secondary_selector_value = models.CharField(max_length=500, blank=True)
    input_value = models.TextField(blank=True)
    expected_value = models.CharField(max_length=500, blank=True)
    expected_text = models.CharField(max_length=500, blank=True)
    min_length = models.PositiveIntegerField(null=True, blank=True)
    max_length = models.PositiveIntegerField(null=True, blank=True)
    expected_url = models.URLField(blank=True)
    expected_http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    timeout_seconds = models.PositiveSmallIntegerField(default=10)
    browser = models.CharField(max_length=30, default='chromium')
    capture_evidence = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['test_case', 'step_number', 'name']

    def __str__(self):
        return f'{self.test_case.code} - {self.name}'


class AutomatedExecutionResult(TimeStampedModel):
    test_execution = models.ForeignKey(
        TestExecution,
        on_delete=models.CASCADE,
        related_name='automated_results',
    )
    validation_rule = models.ForeignKey(
        AutomatedValidationRule,
        on_delete=models.PROTECT,
        related_name='execution_results',
    )
    status = models.CharField(max_length=20, choices=TestExecution.Result.choices)
    expected_behavior = models.TextField(blank=True)
    actual_behavior = models.TextField(blank=True)
    input_used = models.TextField(blank=True)
    technical_log = models.TextField(blank=True)
    screenshot = models.ImageField(upload_to='automation_screenshots/', null=True, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.validation_rule.name} - {self.get_status_display()}'

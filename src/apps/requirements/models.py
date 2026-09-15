import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OwnedModel
from apps.core.models import TimeStampedModel
from apps.projects.models import Project


class Requirement(OwnedModel):
    class RequirementType(models.TextChoices):
        FUNCTIONAL = 'FUNCTIONAL', 'Funcional'
        NON_FUNCTIONAL = 'NON_FUNCTIONAL', 'No funcional'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        REVIEW = 'REVIEW', 'En revisión'
        APPROVED = 'APPROVED', 'Aprobado'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements')
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=180)
    description = models.TextField()
    acceptance_criteria = models.TextField(
        blank=True,
        help_text='Condiciones verificables que deben cumplirse para aceptar el requisito.',
    )
    requirement_type = models.CharField(
        max_length=20,
        choices=RequirementType.choices,
        default=RequirementType.FUNCTIONAL,
    )
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['project', 'code']
        unique_together = ('project', 'code')

    def clean(self):
        super().clean()
        errors = {}
        if not self.project_id:
            errors['project'] = 'El requisito debe pertenecer a un proyecto.'
        if not (self.code or '').strip():
            errors['code'] = 'El requisito debe tener un código.'
        if not (self.title or '').strip():
            errors['title'] = 'El requisito debe tener un título.'
        if not (self.description or '').strip():
            errors['description'] = 'El requisito debe tener una descripción.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} - {self.title}'

    @property
    def type_prefix(self):
        return 'RF' if self.requirement_type == self.RequirementType.FUNCTIONAL else 'RN'

    @property
    def typed_code(self):
        match = re.search(r'(\d+)$', self.code or '')
        sequence = match.group(1) if match else (self.code or '')
        return f'{self.type_prefix}-{sequence}'

    @property
    def display_label(self):
        return f'{self.typed_code} - {self.title}'


class RequirementVersion(TimeStampedModel):
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=180)
    description = models.TextField()
    acceptance_criteria = models.TextField(blank=True)
    requirement_type = models.CharField(max_length=20, choices=Requirement.RequirementType.choices)
    priority = models.CharField(max_length=20, choices=Requirement.Priority.choices)
    status = models.CharField(max_length=20, choices=Requirement.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.CharField(max_length=180, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['requirement', '-version_number']
        unique_together = ('requirement', 'version_number')

    def __str__(self):
        return f'{self.requirement.code} v{self.version_number}'

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.core.models import OwnedModel
from apps.core.models import TimeStampedModel
from apps.projects.models import Project


class TestPlan(OwnedModel):
    class TestType(models.TextChoices):
        FUNCTIONAL = 'FUNCTIONAL', 'Funcional'
        INTEGRATION = 'INTEGRATION', 'Integracion'
        SYSTEM = 'SYSTEM', 'Sistema'
        ACCEPTANCE = 'ACCEPTANCE', 'Aceptacion'

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
    test_types = models.JSONField(default=list, blank=True)
    entry_criteria = models.TextField(blank=True)
    exit_criteria = models.TextField(blank=True)
    minimum_pass_percentage = models.PositiveSmallIntegerField(default=80)
    maximum_critical_defects = models.PositiveSmallIntegerField(default=0)
    minimum_coverage_percentage = models.PositiveSmallIntegerField(default=90)
    resources = models.TextField(blank=True)
    environment = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    estimation = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ['project', 'name']

    def clean(self):
        super().clean()
        errors = {}

        if not 0 <= self.minimum_pass_percentage <= 100:
            errors['minimum_pass_percentage'] = 'El porcentaje minimo de aprobacion debe estar entre 0 y 100.'
        if not 0 <= self.minimum_coverage_percentage <= 100:
            errors['minimum_coverage_percentage'] = 'El porcentaje minimo de cobertura debe estar entre 0 y 100.'
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors['end_date'] = 'La fecha de finalizacion no puede ser anterior a la fecha de inicio.'

        project = self.project if self.project_id else None
        if project:
            if project.start_date and self.start_date and self.start_date < project.start_date:
                errors['start_date'] = 'El plan de pruebas no puede iniciar antes que el proyecto.'
            if project.end_date and self.end_date and self.end_date > project.end_date:
                errors['end_date'] = 'El plan de pruebas no puede finalizar despues que el proyecto.'
            if project.start_date and self.end_date and self.end_date < project.start_date:
                errors['end_date'] = 'El plan de pruebas debe quedar dentro del periodo del proyecto.'
            if project.end_date and self.start_date and self.start_date > project.end_date:
                errors['start_date'] = 'El plan de pruebas debe quedar dentro del periodo del proyecto.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TestPlanVersion(TimeStampedModel):
    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    version_label = models.CharField(max_length=20, default='1.0')
    name = models.CharField(max_length=180)
    objective = models.TextField()
    status = models.CharField(max_length=20, choices=TestPlan.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.CharField(max_length=180, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['test_plan', '-version_number']
        unique_together = ('test_plan', 'version_number')

    def __str__(self):
        return f'{self.test_plan.name} v{self.version_label}'

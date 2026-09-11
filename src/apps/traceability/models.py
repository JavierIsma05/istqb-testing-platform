from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase


class TraceabilityLink(TimeStampedModel):
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='traceability_links')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='traceability_links')
    rationale = models.TextField(blank=True)

    class Meta:
        unique_together = ('requirement', 'test_case')

    def clean(self):
        super().clean()
        if not self.requirement_id or not self.test_case_id:
            return
        if self.requirement.project_id != self.test_case.test_plan.project_id:
            raise ValidationError({
                'test_case': 'El caso de prueba debe pertenecer al mismo proyecto que el requisito.',
            })

    def save(self, *args, **kwargs):
        # Validate project consistency here, while leaving duplicate pairs to
        # the database unique constraint so callers receive IntegrityError.
        self.full_clean(validate_unique=False)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.requirement.code} -> {self.test_case.code}'

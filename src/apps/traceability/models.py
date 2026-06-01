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

    def __str__(self):
        return f'{self.requirement.code} -> {self.test_case.code}'

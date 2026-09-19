from django.db import transaction

from apps.incidents.models import Incident
from apps.testcases.models import TestCase


def delete_project_and_related_data(project):
    """Elimina el proyecto y todos sus datos dependientes de forma portable."""
    through_model = TestCase.covered_risks.through
    test_case_ids = list(
        TestCase.objects.filter(test_plan__project=project).values_list('pk', flat=True)
    )
    incident_ids = list(project.incidents.values_list('pk', flat=True))

    with transaction.atomic():
        if test_case_ids:
            through_model.objects.filter(testcase_id__in=test_case_ids).delete()
        if incident_ids:
            through_model.objects.filter(incident_id__in=incident_ids).delete()
            Incident.objects.filter(pk__in=incident_ids).delete()

        # Con las relaciones legacy ya retiradas, Django ejecuta el cascade
        # normal del proyecto sin SQL dependiente del motor de base de datos.
        project.delete()

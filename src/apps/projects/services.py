from django.db import connection, transaction

from apps.incidents.models import Incident
from apps.testcases.models import TestCase


def delete_project_and_related_data(project):
    """Elimina el proyecto y todos sus datos dependientes en el orden correcto."""
    through_table = TestCase.covered_risks.through._meta.db_table
    incident_table = Incident._meta.db_table
    test_case_ids = list(
        TestCase.objects.filter(test_plan__project=project).values_list('pk', flat=True)
    )
    incident_ids = list(project.incidents.values_list('pk', flat=True))

    with transaction.atomic():
        with connection.cursor() as cursor:
            conditions = []
            params = []
            if test_case_ids:
                conditions.append('testcase_id = ANY(%s)')
                params.append(test_case_ids)
            if incident_ids:
                conditions.append('incident_id = ANY(%s)')
                params.append(incident_ids)
            if conditions:
                cursor.execute(
                    f'DELETE FROM "{through_table}" WHERE ' + ' OR '.join(conditions),
                    params,
                )
            if incident_ids:
                cursor.execute(
                    f'DELETE FROM "{incident_table}" WHERE id = ANY(%s)',
                    [incident_ids],
                )

        # Con las relaciones legacy ya retiradas, Django puede ejecutar el
        # cascade normal del proyecto sin violar la FK de la tabla intermedia.
        project.delete()

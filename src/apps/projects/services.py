from django.db import connection, transaction
from django.db.models import Q

from apps.incidents.models import Incident
from apps.testcases.models import TestCase


def delete_project_and_related_data(project):
    """Elimina un proyecto y sus datos dependientes respetando el orden de las FK."""
    covered_risks_through = TestCase.covered_risks.through
    test_case_ids = list(
        TestCase.objects.filter(test_plan__project=project).values_list('pk', flat=True)
    )
    incident_ids = list(project.incidents.values_list('pk', flat=True))

    with transaction.atomic():
        # Esta tabla intermedia tiene una FK directa hacia Incident. Debe quedar
        # vacia antes de borrar los Incident, tambien en bases con datos legacy.
        filters = Q()
        has_filter = False
        if test_case_ids:
            filters |= Q(testcase_id__in=test_case_ids)
            has_filter = True
        if incident_ids:
            filters |= Q(incident_id__in=incident_ids)
            has_filter = True
        if has_filter:
            covered_risks_through.objects.filter(filters).delete()

        if incident_ids:
            Incident.objects.filter(pk__in=incident_ids).delete()

        project.delete()



def delete_project_and_related_data_raw(project):
    """Fallback de borrado para esquemas PostgreSQL con constraints legacy."""
    covered_risks_through = TestCase.covered_risks.through
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
                    f'DELETE FROM "{covered_risks_through._meta.db_table}" WHERE '
                    + ' OR '.join(conditions),
                    params,
                )
            if incident_ids:
                cursor.execute(
                    f'DELETE FROM "{Incident._meta.db_table}" WHERE id = ANY(%s)',
                    [incident_ids],
                )
        project.delete()

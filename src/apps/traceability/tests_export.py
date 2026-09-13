import csv
import io

import pytest
from django.urls import reverse

from apps.executions.models import TestExecution
from apps.projects.models import Project
from apps.testcases.models import TestCase


@pytest.mark.django_db
def test_exporta_indicadores_csv_del_proyecto_visible(client, user, project, test_case):
    TestExecution.objects.create(
        test_case=test_case,
        executed_by=user,
        result=TestExecution.Result.PASSED,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:export-indicators-csv'))

    assert response.status_code == 200
    assert response['Content-Disposition'] == 'attachment; filename="indicadores_trazabilidad.csv"'
    assert 'text/csv' in response['Content-Type']

    rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[0] == [
        'Codigo proyecto',
        'Proyecto',
        'Total requisitos',
        'Total casos de prueba',
        'Total ejecuciones',
        'Cobertura de requisitos (%)',
        'Cobertura de ejecucion (%)',
        'Casos ejecutados (%)',
    ]
    assert rows[1] == [
        project.code,
        project.name,
        '1',
        '1',
        '1',
        '100.0',
        '100.0',
        '100.0',
    ]


@pytest.mark.django_db
def test_exporta_solo_proyectos_visibles(client, user, project, requirement):
    other_user = user.__class__.objects.create_user(
        email='foreign-export@example.edu',
        password='StrongPass123',
    )
    foreign_project = Project.objects.create(
        code='PRJ-EXPORT-FOREIGN',
        name='Proyecto ajeno',
        created_by=other_user,
    )
    foreign_project.requirements.create(
        code='REQ-FOREIGN-001',
        title='Requisito ajeno',
        description='No debe exportarse.',
        created_by=other_user,
    )
    client.force_login(user)

    response = client.get(reverse('traceability:export-indicators-csv'))
    content = response.content.decode('utf-8-sig')

    assert project.code in content
    assert foreign_project.code not in content
    assert 'Proyecto ajeno' not in content
